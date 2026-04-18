<template>
  <view class="alert-detail-page">
    <view class="detail-hero">
      <view class="hero-main">
        <view class="hero-icon" :class="alert.level">
          <text v-if="alert.level === 'high'">🔥</text>
          <text v-else-if="alert.level === 'medium'">⚠️</text>
          <text v-else>ℹ️</text>
        </view>
        <view class="hero-copy">
          <text class="page-title">{{ alert.title }}</text>
          <text class="page-subtitle">{{ alert.time }}</text>
        </view>
      </view>
      <view class="alert-status" :class="alert.status">
        <text>{{ statusLabel }}</text>
      </view>
    </view>
    <view class="quick-nav">
      <button class="btn-secondary mini" @click="backToList">返回告警列表</button>
      <button class="btn-secondary mini" @click="gotoRecords">查看处置记录</button>
    </view>

    <view v-if="alert.status === 'unresolved'" class="accept-banner">
      <text class="accept-text">接单后开始现场处置</text>
      <button class="accept-btn" @click="acceptOrder">接单</button>
    </view>

    <view class="detail-card">
      <text class="section-title">告警描述</text>
      <text class="description-content">{{ alert.description }}</text>
      <view class="meta-grid">
        <view class="meta-item"><text class="meta-label">告警等级</text><text class="meta-value" :class="alert.level">{{ levelText }}</text></view>
        <view class="meta-item"><text class="meta-label">告警设备</text><text class="meta-value">{{ alert.deviceId }}</text></view>
        <view class="meta-item"><text class="meta-label">告警位置</text><text class="meta-value">{{ alert.location }}</text></view>
        <view class="meta-item"><text class="meta-label">告警类型</text><text class="meta-value">{{ alert.type }}</text></view>
      </view>
    </view>

    <view class="detail-card">
      <text class="section-title">短时浓度预测</text>
      <view class="prediction-list">
        <view v-for="(item, index) in alert.predictionCurve" :key="index" class="prediction-item"><text class="prediction-label">{{ item.label }}</text><text class="prediction-value">{{ item.value }}</text></view>
      </view>
    </view>

    <view class="detail-card">
      <text class="section-title">智能诊断</text>
      <view class="ai-box"><text class="ai-title">原因分析</text><text class="ai-text">{{ alert.aiDiagnosis.reason }}</text></view>
      <view class="ai-box"><text class="ai-title">处置建议</text><text class="ai-text">{{ alert.aiDiagnosis.suggestion }}</text></view>
      <view class="ai-box"><text class="ai-title">历史相似案例</text><text v-for="(item, index) in alert.aiDiagnosis.similarCases" :key="index" class="ai-list">• {{ item }}</text></view>
      <view class="ai-box"><text class="ai-title">处置 SOP</text><text v-for="(item, index) in alert.aiDiagnosis.sop" :key="index" class="ai-list">{{ index + 1 }}. {{ item }}</text></view>
    </view>

    <view v-if="alert.status === 'unresolved' && alert.aiPlan" class="detail-card">
      <text class="section-title">AI 方案与问答</text>
      <view class="ai-box">
        <text class="ai-title">{{ alert.aiPlan.title }}</text>
        <text class="ai-text">{{ alert.aiPlan.summary }}</text>
        <text v-for="(s, i) in alert.aiPlan.steps" :key="i" class="ai-list">{{ i + 1 }}. {{ s }}</text>
        <text v-if="alert.aiPlan.qaHint" class="ai-hint">{{ alert.aiPlan.qaHint }}</text>
      </view>

      <view class="ai-box">
        <text class="ai-title">方案下追问</text>
        <scroll-view scroll-y class="ai-chat-list">
          <view v-for="(item, index) in aiHistory" :key="index" class="ai-chat-item" :class="item.role">
            <text class="ai-chat-role">{{ item.role === 'assistant' ? 'AI' : '我' }}</text>
            <text class="ai-chat-content">{{ item.content }}</text>
            <text class="ai-chat-time">{{ item.createdAt || '刚刚' }}</text>
          </view>
          <view v-if="!aiHistory.length" class="ai-chat-empty">
            <text class="ai-chat-empty-text">可在此针对方案继续提问</text>
          </view>
        </scroll-view>
        <textarea v-model="aiQuestion" class="ai-chat-input" placeholder="输入问题，例如：压差升高怎么判断是取压管堵塞？"></textarea>
        <view class="action-buttons">
          <button class="btn-secondary" @click="loadAiHistory">刷新对话</button>
          <button class="btn-primary" @click="sendAiQuestion">发送</button>
        </view>
      </view>
    </view>

    <view class="detail-card">
      <text class="section-title">告警数据</text>
      <view class="data-list">
        <view v-for="(data, index) in alert.data" :key="index" class="data-item">
          <view class="data-top"><text class="data-label">{{ data.label }}</text><text class="data-threshold">阈值: {{ data.threshold }}</text></view>
          <view class="data-main"><text class="data-value">{{ data.value }}</text><text class="data-unit">{{ data.unit }}</text></view>
        </view>
      </view>
    </view>

    <view class="detail-card">
      <text class="section-title">处理记录</text>
      <view class="records-list">
        <view v-for="(record, index) in pagedProcessingRecords" :key="index" class="record-item"><view class="record-line"></view><view class="record-body"><text class="record-time">{{ record.time }}</text><text class="record-content">{{ record.content }}</text><text class="record-operator">{{ record.operator }}</text></view></view>
      </view>
      <view v-if="alert.processingRecords && alert.processingRecords.length" class="pager-row">
        <button class="pager-btn" :disabled="recordPage <= 1" @click="changeRecordPage(-1)">上一页</button>
        <text class="pager-text">{{ recordPage }}/{{ recordTotalPages }}</text>
        <button class="pager-btn" :disabled="recordPage >= recordTotalPages" @click="changeRecordPage(1)">下一页</button>
      </view>
    </view>

    <view v-if="alert.status === 'tracking'" class="detail-card tracking-card">
      <text class="section-title">持续跟踪</text>
      <text class="tracking-desc">处置已提交，须持续跟踪满 48 小时且无异常反复后方可结案。</text>
      <text v-if="alert.handledAt" class="tracking-meta">处置完成时间：{{ alert.handledAt }}</text>
      <text class="tracking-meta">最早可结案：{{ alert.resolveEarliestAt || '—' }}</text>
      <button
        class="btn-primary"
        :disabled="!alert.canResolve"
        @click="submitResolve"
      >结案</button>
      <text v-if="!alert.canResolve" class="tracking-warn">未满 48 小时，请稍后再试</text>
    </view>

    <view v-if="alert.status === 'unresolved' || alert.status === 'accepted'" class="detail-card">
      <text class="section-title">处置反馈</text>
      <input v-model="handleForm.result" class="form-input" placeholder="处置结果" />
      <textarea v-model="handleForm.notes" class="form-textarea" placeholder="现场说明（选填）" />
      <input v-model="handleForm.photoUrl" class="form-input" placeholder="照片链接（选填）" />
      <view class="action-buttons stacked">
        <button class="btn-primary" @click="submitHandle">提交处置（进入 48h 跟踪）</button>
        <button class="btn-secondary" @click="markMisreport">标记误报</button>
        <button class="btn-secondary" @click="ignoreAlert">忽略告警</button>
      </view>
    </view>
  </view>
</template>

<script>
import { request } from '../../utils/api';

export default {
  data() {
    return {
      alertId: null,
      handleForm: { result: '', notes: '', photoUrl: '' },
      aiSessionId: '',
      aiHistory: [],
      aiQuestion: '',
      recordPage: 1,
      recordPageSize: 5,
      alert: {
        id: 1,
        title: 'VOCs 浓度超标',
        time: '2026-04-13 10:00',
        description: 'VOCs 浓度达到 65.2 mg/m³，超过阈值 50 mg/m³，持续时间超过 5 分钟',
        level: 'high',
        status: 'unresolved',
        handledAt: null,
        resolveEarliestAt: null,
        canResolve: false,
        deviceId: 'DEV-001',
        location: '废气处理车间 A',
        type: '浓度超标',
        predictionCurve: [],
        aiDiagnosis: { reason: '', suggestion: '', similarCases: [], sop: [] },
        aiPlan: null,
        data: [{ label: 'VOCs 浓度', value: '65.2', unit: 'mg/m³', threshold: '50 mg/m³' }],
        processingRecords: [{ time: '2026-04-13 10:05', content: '系统自动检测到告警', operator: '系统' }]
      }
    };
  },
  onLoad(options) {
    this.alertId = options && options.id ? options.id : null;
    this.aiSessionId = this.alertId ? `alert-${this.alertId}` : '';
    this.loadAlertDetail();
    this.loadAiHistory();
  },
  computed: {
    levelText() {
      if (this.alert.level === 'high') return '紧急';
      if (this.alert.level === 'medium') return '警告';
      if (this.alert.level === 'low') return '信息';
      return '未知';
    },
    statusLabel() {
      if (this.alert.status === 'unresolved') return '待接单';
      if (this.alert.status === 'accepted') return '处理中';
      if (this.alert.status === 'tracking') return '持续跟踪';
      if (this.alert.status === 'resolved') return '已结案';
      return '—';
    },
    recordTotalPages() {
      const total = Array.isArray(this.alert.processingRecords) ? this.alert.processingRecords.length : 0;
      return Math.max(1, Math.ceil(total / this.recordPageSize));
    },
    pagedProcessingRecords() {
      const records = Array.isArray(this.alert.processingRecords) ? this.alert.processingRecords : [];
      const start = (this.recordPage - 1) * this.recordPageSize;
      return records.slice(start, start + this.recordPageSize);
    },
  },
  methods: {
    backToList() {
      uni.switchTab({ url: '/pages/alerts/list' });
    },
    gotoRecords() {
      uni.navigateTo({ url: '/pages/records/index?tab=disposal' });
    },
    async loadAlertDetail() {
      if (!this.alertId) return;
      try {
        const res = await request({ url: `/alerts/${this.alertId}` });
        if (res && res.code === 200 && res.data) {
          this.alert = res.data;
          this.recordPage = 1;
        }
      } catch (error) {
        uni.showToast({ title: '详情加载失败', icon: 'none' });
      }
    },
    changeRecordPage(step) {
      const next = this.recordPage + step;
      this.recordPage = Math.min(this.recordTotalPages, Math.max(1, next));
    },
    async loadAiHistory() {
      if (!this.aiSessionId) return;
      try {
        const res = await request({ url: `/rag/history?sessionId=${this.aiSessionId}` });
        if (res?.code === 200) this.aiHistory = res.data || [];
      } catch (error) {
        // 静默失败：不影响主流程
      }
    },
    async sendAiQuestion() {
      const q = String(this.aiQuestion || '').trim();
      if (!q) return uni.showToast({ title: '请输入问题', icon: 'none' });
      if (!this.aiSessionId) return;
      try {
        const prompt = this.alert?.aiPlan?.summary ? `【方案摘要】${this.alert.aiPlan.summary}\n【问题】${q}` : q;
        const res = await request({ url: '/rag/diagnose', method: 'POST', data: { question: prompt, sessionId: this.aiSessionId } });
        if (res?.code === 200) {
          this.aiQuestion = '';
          await this.loadAiHistory();
        }
      } catch (error) {
        uni.showToast({ title: 'AI 请求失败', icon: 'none' });
      }
    },
    async acceptOrder() {
      if (!this.alertId) return;
      try {
        await request({ url: `/alerts/${this.alertId}/accept`, method: 'POST' });
        uni.showToast({ title: '接单成功', icon: 'success' });
        await this.loadAlertDetail();
      } catch (e) {
        uni.showToast({ title: '接单失败', icon: 'none' });
      }
    },
    async ignoreAlert() {
      if (!this.alertId) return;
      try {
        await request({ url: `/alerts/${this.alertId}/ignore`, method: 'POST' });
        await this.loadAlertDetail();
        uni.showToast({ title: '告警已忽略', duration: 1000 });
      } catch (error) {
        uni.showToast({ title: '操作失败', icon: 'none' });
      }
    },
    async markMisreport() {
      if (!this.alertId) return;
      try {
        await request({ url: `/alerts/${this.alertId}/misreport`, method: 'POST' });
        await this.loadAlertDetail();
        uni.showToast({ title: '已标记为误报', duration: 1000 });
      } catch (error) {
        uni.showToast({ title: '标记失败', icon: 'none' });
      }
    },
    async submitHandle() {
      if (!this.handleForm.result) return uni.showToast({ title: '请填写处置结果', icon: 'none' });
      try {
        await request({ url: `/alerts/${this.alertId}/handle`, method: 'POST', data: this.handleForm });
        uni.showToast({ title: '已进入持续跟踪，期满后可结案', duration: 1600 });
        this.handleForm = { result: '', notes: '', photoUrl: '' };
        await this.loadAlertDetail();
      } catch (error) {
        uni.showToast({ title: '提交失败', icon: 'none' });
      }
    },
    async submitResolve() {
      if (!this.alertId || !this.alert.canResolve) return;
      try {
        await request({ url: `/alerts/${this.alertId}/resolve`, method: 'POST' });
        uni.showToast({ title: '已结案', duration: 1000 });
        await this.loadAlertDetail();
      } catch (error) {
        const msg = (error && error.message) || '结案失败';
        uni.showToast({ title: msg.length > 40 ? '未满跟踪期或状态不允许' : msg, icon: 'none' });
      }
    }
  }
};
</script>

<style>
.alert-detail-page { min-height: 100vh; padding: 24rpx 24rpx calc(36rpx + env(safe-area-inset-bottom)); background: linear-gradient(180deg, #f7f3ff 0%, #fdfcff 52%, #ffffff 100%); }
.detail-hero,.detail-card { margin-bottom: 20rpx; padding: 26rpx; border-radius: 28rpx; background: #fff; box-shadow: 0 16rpx 36rpx rgba(49,30,109,.06); }
.quick-nav { display:flex; gap:12rpx; margin: 2rpx 0 20rpx; }
.detail-hero { display:flex; justify-content:space-between; align-items:flex-start; gap:18rpx; }
.hero-main { display:flex; gap:18rpx; flex:1; min-width:0; }
.hero-copy { flex:1; min-width:0; }
.hero-icon { width:74rpx; height:74rpx; border-radius:24rpx; display:flex; align-items:center; justify-content:center; font-size:32rpx; }
.hero-icon.high { background:#ffe9ee; } .hero-icon.medium { background:#fff5df; } .hero-icon.low { background:#e9f4ff; }
.page-title { display:block; font-size:34rpx; font-weight:800; color:#2d2454; line-height:1.25; word-break:break-word; }
.page-subtitle { display:block; margin-top:10rpx; font-size:20rpx; color:#9589af; line-height:1.4; word-break:break-word; }
.alert-status { flex-shrink:0; padding:10rpx 14rpx; border-radius:999rpx; font-size:17rpx; font-weight:700; max-width:36%; text-align:center; line-height:1.2; word-break:break-word; }
.alert-status.unresolved { background:#ffe9ee; color:#dd5175; } .alert-status.accepted { background:#fff5df; color:#c97812; } .alert-status.tracking { background:#e8f4ff; color:#2f6f9f; } .alert-status.resolved { background:#efeaff; color:#7b61ff; }
.tracking-card .tracking-desc { display:block; margin-top:14rpx; font-size:21rpx; line-height:1.55; color:#6f6686; }
.tracking-card .tracking-meta { display:block; margin-top:10rpx; font-size:20rpx; color:#8d82aa; }
.tracking-card .tracking-warn { display:block; margin-top:12rpx; font-size:20rpx; color:#c97812; }
.tracking-card .btn-primary { width:100%; margin-top:18rpx; }
.tracking-card .btn-primary[disabled] { opacity:0.45; }
.accept-banner { margin-bottom:20rpx; padding:22rpx; border-radius:24rpx; background:linear-gradient(135deg,#f4efff 0%,#fff 100%); border:2rpx solid #e8e0ff; display:flex; flex-direction:column; gap:16rpx; }
.accept-text { font-size:21rpx; color:#5d5478; line-height:1.55; }
.accept-btn { height:88rpx; padding:0 24rpx; border-radius:22rpx; background:linear-gradient(135deg,#7b61ff 0%,#947dff 100%); color:#fff; font-size:28rpx; font-weight:700; }
.accept-btn::after { border:none; }
.section-title { display:block; font-size:31rpx; font-weight:800; color:#2d2454; line-height:1.25; word-break:break-word; }
.description-content,.ai-text,.record-content { display:block; margin-top:14rpx; font-size:21rpx; line-height:1.55; color:#6f6686; word-break:break-word; }
.meta-grid,.prediction-list { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:16rpx; margin-top:18rpx; }
.meta-item,.prediction-item,.ai-box,.data-item,.record-body { padding:18rpx; border-radius:22rpx; background:#faf8ff; }
.meta-label,.data-threshold,.record-time,.info-label { font-size:18rpx; color:#9a8fb2; }
.meta-value,.prediction-value,.data-label,.data-value { display:block; margin-top:10rpx; font-size:21rpx; font-weight:700; color:#2d2454; word-break:break-word; line-height:1.3; }
.meta-value.high { color:#dd5175; } .meta-value.medium { color:#d48618; } .meta-value.low { color:#3c86c5; }
.prediction-label,.ai-title { font-size:19rpx; color:#7b61ff; font-weight:700; }
.ai-list { display:block; margin-top:10rpx; font-size:20rpx; line-height:1.6; color:#6f6686; }
.ai-hint { display:block; margin-top:12rpx; font-size:20rpx; color:#8d82aa; line-height:1.55; }
.ai-chat-list { max-height: 520rpx; margin-top: 14rpx; }
.ai-chat-item { margin-bottom: 16rpx; padding: 18rpx; border-radius: 20rpx; background:#faf8ff; }
.ai-chat-item.assistant { background:#f2ecff; }
.ai-chat-role,.ai-chat-time { display:block; font-size:18rpx; color:#8f84ab; }
.ai-chat-content { display:block; margin-top:8rpx; font-size:21rpx; line-height:1.55; color:#2d2454; word-break:break-word; }
.ai-chat-empty { padding: 20rpx; text-align:center; }
.ai-chat-empty-text { font-size: 21rpx; color:#9a8fb2; line-height:1.6; }
.ai-chat-input { width:100%; min-height:160rpx; margin-top:12rpx; padding:20rpx; border-radius:20rpx; background:#faf8ff; font-size:22rpx; line-height:1.45; box-sizing:border-box; }
.data-list,.records-list { display:flex; flex-direction:column; gap:16rpx; margin-top:18rpx; }
.data-top,.data-main { display:flex; justify-content:space-between; align-items:center; gap:12rpx; }
.data-main { justify-content:flex-start; align-items:baseline; }
.data-unit,.record-operator { font-size:18rpx; color:#8d82aa; }
.record-item { display:flex; gap:16rpx; }
.record-line { width:8rpx; border-radius:999rpx; background:linear-gradient(180deg,#7b61ff 0%,#b19cff 100%); }
.pager-row { margin-top:14rpx; display:flex; align-items:center; justify-content:flex-end; gap:12rpx; }
.pager-btn { min-width:112rpx; height:62rpx; padding:0 16rpx; border-radius:16rpx; background:#efeaff; color:#7b61ff; font-size:20rpx; font-weight:700; }
.pager-btn::after { border:none; }
.pager-btn[disabled] { opacity:.45; }
.pager-text { font-size:20rpx; color:#8f84ab; min-width:72rpx; text-align:center; }
.form-input {
  width:100%;
  margin-top:16rpx;
  height:88rpx;
  line-height:88rpx;
  padding:0 20rpx;
  border-radius:20rpx;
  background:#faf8ff;
  font-size:22rpx;
  box-sizing:border-box;
  vertical-align:middle;
}
.form-textarea {
  width:100%;
  margin-top:16rpx;
  min-height:160rpx;
  padding:20rpx;
  border-radius:20rpx;
  background:#faf8ff;
  font-size:22rpx;
  line-height:1.45;
  box-sizing:border-box;
}
.action-buttons { display:flex; gap:16rpx; margin-top:20rpx; }
.action-buttons.stacked { flex-direction:column; }
.btn-primary,.btn-secondary { width:100%; height:88rpx; padding:0 20rpx; border-radius:22rpx; font-size:28rpx; font-weight:700; }
.btn-secondary.mini { height:72rpx; font-size:22rpx; }
.btn-primary { background:linear-gradient(135deg,#7b61ff 0%,#947dff 100%); color:#fff; }
.btn-secondary { background:#fff; color:#7b61ff; border:2rpx solid #e8e0ff; }
.btn-primary::after,.btn-secondary::after { border:none; }
</style>
