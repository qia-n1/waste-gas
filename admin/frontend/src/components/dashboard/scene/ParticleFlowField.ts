/**
 * 2D 粒子风场流线图（受 https://blog.csdn.net/KK_bluebule/article/details/128702207 启发）
 *
 * 核心思路：
 *   1. 每帧先用 destination-out + 低 alpha 黑色整体擦除一小部分（"渐晕"），老轨迹自然褪色
 *   2. 每个污染源按浓度速率喷出新粒子；粒子带初速度（向上+风场），加重力/阻尼
 *   3. 每帧画粒子的 prev→curr 短线段，颜色由浓度比 (value/critical) 决定：
 *        浅蓝(#6fb8ff) → 橙(#ffb147) → 深红(#d43a2f)
 *   4. 粒子寿命到或飘出画布 → 回收
 *
 * 相比之前的 3D WebGL additive Points：
 *   - 不会因为多粒子叠加就过曝成白色
 *   - 浓度差异以颜色+密度双通道表达，语义更清晰
 *   - 拖尾有方向感，自然呈现"污染烟羽"的视觉
 */

export type FlowLevel = "normal" | "warning" | "critical";

export interface FlowSource {
  id: string;
  /** 屏幕像素坐标（CSS px，非设备像素） */
  screenX: number;
  screenY: number;
  /** 原始浓度值（与 warning/critical 同量纲） */
  value: number;
  warning: number;
  critical: number;
  level: FlowLevel;
}

interface Particle {
  x: number;
  y: number;
  prevX: number;
  prevY: number;
  vx: number;
  vy: number;
  life: number; // 剩余寿命（秒）
  maxLife: number;
  color: string;
  width: number;
  ownerId: string;
}

const MAX_PARTICLES = 1800;
// 渐晕清除的 alpha：越大拖尾越短、消失越快；越小拖尾越长但会"糊"
const FADE_ALPHA = 0.11;

const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v));

/** 浓度比 → HSL 颜色。0 浅蓝 / 0.5 琥珀 / 1+ 深红。 */
const colorForRatio = (ratio: number): string => {
  const r = clamp(ratio, 0, 1.15);
  // 色相从 210（蓝）平滑过渡到 0（红），中段经过琥珀
  const hue = 210 - 210 * Math.min(r, 1);
  const sat = 72 + 20 * r;
  const light = 68 - 22 * Math.min(r, 1);
  return `hsl(${hue.toFixed(0)}, ${sat.toFixed(0)}%, ${light.toFixed(0)}%)`;
};

/**
 * 单个粒子的线宽：浓度越高越粗（但最大不超过 2.2），避免画满屏粗线
 */
const widthForRatio = (ratio: number): number =>
  1 + clamp(ratio, 0, 1) * 1.2;

/**
 * 发射速率：浓度越高单位时间粒子越多。
 * 低浓度 6/s，满浓度 ~70/s，超标 critical 级再 ×1.4
 */
const emitRateForSource = (src: FlowSource): number => {
  const r = clamp(src.value / Math.max(src.critical, 1e-6), 0, 1.15);
  const base = 6 + 55 * r;
  return src.level === "critical" ? base * 1.4 : base;
};

export class ParticleFlowField {
  private readonly canvas: HTMLCanvasElement;
  private readonly ctx: CanvasRenderingContext2D;
  private cssWidth = 0;
  private cssHeight = 0;

  private particles: Particle[] = [];
  private sources = new Map<string, FlowSource>();
  private accumulators = new Map<string, number>();

  // 全局风向（2D 屏幕空间，y 向下）；默认略微向左上飘，像烟羽上升
  private windX = -0.2;
  private windY = -0.55;
  private windSpeed = 0.5;

  // 脉冲相位：critical 发射器的发射速率随相位波动
  private pulsePhase = 0;

  constructor(canvas: HTMLCanvasElement) {
    this.canvas = canvas;
    const ctx = canvas.getContext("2d");
    if (!ctx) {
      throw new Error("ParticleFlowField: 2D canvas context unavailable");
    }
    this.ctx = ctx;
    this.ctx.lineCap = "round";
    this.ctx.lineJoin = "round";
  }

  /** 画布 CSS 尺寸变化时调用。自动处理 HiDPI。 */
  resize(cssWidth: number, cssHeight: number): void {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    this.cssWidth = cssWidth;
    this.cssHeight = cssHeight;
    this.canvas.width = Math.max(1, Math.round(cssWidth * dpr));
    this.canvas.height = Math.max(1, Math.round(cssHeight * dpr));
    this.canvas.style.width = `${cssWidth}px`;
    this.canvas.style.height = `${cssHeight}px`;
    // 用 setTransform 而非 scale，避免累积缩放
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    this.ctx.lineCap = "round";
    this.ctx.lineJoin = "round";
  }

  /** 每帧把最新的污染源 2D 坐标/浓度推进来。 */
  setSources(list: FlowSource[]): void {
    this.sources.clear();
    for (const s of list) {
      this.sources.set(s.id, s);
      if (!this.accumulators.has(s.id)) this.accumulators.set(s.id, 0);
    }
    // 清理已删除源的累加器
    for (const key of Array.from(this.accumulators.keys())) {
      if (!this.sources.has(key)) this.accumulators.delete(key);
    }
  }

  /** 全局风场（屏幕空间，y 向下）。direction 不必归一，内部自动。 */
  setWind(dx: number, dy: number, speed: number): void {
    const len = Math.hypot(dx, dy) || 1;
    this.windX = dx / len;
    this.windY = dy / len;
    this.windSpeed = Math.max(0, speed);
  }

  tick(dt: number): void {
    const safeDt = Math.min(dt, 0.08);
    this.pulsePhase += safeDt * 5;

    this.fadeCanvas();
    this.spawnParticles(safeDt);
    this.updateAndDraw(safeDt);
  }

  dispose(): void {
    this.particles = [];
    this.sources.clear();
    this.accumulators.clear();
    // 擦干净
    this.ctx.setTransform(1, 0, 0, 1, 0, 0);
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
  }

  // -------------------------------------------------------------------------
  // private
  // -------------------------------------------------------------------------

  /** 用 destination-out + 半透明黑把整张画布渐晕清除，营造拖尾。 */
  private fadeCanvas(): void {
    const ctx = this.ctx;
    ctx.save();
    ctx.globalCompositeOperation = "destination-out";
    ctx.fillStyle = `rgba(0, 0, 0, ${FADE_ALPHA})`;
    ctx.fillRect(0, 0, this.cssWidth, this.cssHeight);
    ctx.restore();
  }

  private spawnParticles(dt: number): void {
    for (const src of this.sources.values()) {
      let rate = emitRateForSource(src);
      if (src.level === "critical") {
        rate *= 0.7 + 0.45 * Math.abs(Math.sin(this.pulsePhase));
      }
      const acc = (this.accumulators.get(src.id) ?? 0) + rate * dt;
      let remaining = acc;
      while (remaining >= 1 && this.particles.length < MAX_PARTICLES) {
        remaining -= 1;
        this.particles.push(this.createParticle(src));
      }
      this.accumulators.set(src.id, remaining);
    }
  }

  private createParticle(src: FlowSource): Particle {
    // 源头小范围散开，不要聚成一点
    const jitterR = 8 + Math.random() * 10;
    const jitterAngle = Math.random() * Math.PI * 2;
    const jx = Math.cos(jitterAngle) * jitterR;
    const jy = Math.sin(jitterAngle) * jitterR * 0.5; // 椭圆散开，水平更宽

    const ratio = clamp(src.value / Math.max(src.critical, 1e-6), 0, 1.15);

    // 初速度：烟羽上升 + 风场水平分量 + 随机
    const upward = -50 - Math.random() * 40; // 向上（屏幕 y 负方向）
    const drift = (Math.random() - 0.5) * 30;
    const baseSpeed = 40 + 30 * this.windSpeed;

    const x = src.screenX + jx;
    const y = src.screenY + jy;
    return {
      x,
      y,
      prevX: x,
      prevY: y,
      vx: this.windX * baseSpeed + drift,
      vy: this.windY * baseSpeed + upward * 0.45,
      life: 1.6 + Math.random() * 1.0 + ratio * 0.8,
      maxLife: 2.8,
      color: colorForRatio(ratio),
      width: widthForRatio(ratio),
      ownerId: src.id,
    };
  }

  private updateAndDraw(dt: number): void {
    const ctx = this.ctx;
    // 用 lighter 累加能让浓密区自然变亮，但我们已经靠密度表达浓度，用默认 source-over 避免过曝
    ctx.globalCompositeOperation = "source-over";

    const nextAlive: Particle[] = [];
    for (const p of this.particles) {
      // 推进物理
      p.prevX = p.x;
      p.prevY = p.y;
      // 轻微阻尼 + 风场持续推动（让老粒子继续漂散）
      p.vx = p.vx * 0.985 + this.windX * this.windSpeed * 6 * dt;
      p.vy = p.vy * 0.985 + this.windY * this.windSpeed * 6 * dt - 10 * dt; // 额外轻微上升
      p.x += p.vx * dt;
      p.y += p.vy * dt;
      p.life -= dt;

      // 超出画布或寿命到 → 回收
      if (
        p.life <= 0 ||
        p.x < -40 ||
        p.x > this.cssWidth + 40 ||
        p.y < -60 ||
        p.y > this.cssHeight + 40
      ) {
        continue;
      }

      // 末期淡出：alpha 按剩余生命比例
      const t = clamp(p.life / p.maxLife, 0, 1);
      const alpha = 0.15 + 0.7 * t;

      ctx.globalAlpha = alpha;
      ctx.strokeStyle = p.color;
      ctx.lineWidth = p.width;
      ctx.beginPath();
      ctx.moveTo(p.prevX, p.prevY);
      ctx.lineTo(p.x, p.y);
      ctx.stroke();

      nextAlive.push(p);
    }
    ctx.globalAlpha = 1;
    this.particles = nextAlive;
  }
}
