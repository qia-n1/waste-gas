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
          <text class="hero-kicker">ALERT DETAIL</text>
          <text class="page-title">{{ alert.title }}</text>
          <text class="page-subtitle">{{ alert.time }}</text>
        </view>
      </view>
      <view class="alert-status" :class="alert.status">
        <text v-if="alert.status === 'unresolved'">未处理</text>
        <text v-else>已处理</text>
      </view>
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
      <text class="section-title">预测曲线</text>
      <view class="prediction-list">
        <view v-for="(item, index) in alert.predictionCurve" :key="index" class="prediction-item"><text class="prediction-label">{{ item.label }}</text><text class="prediction-value">{{ item.value }}</text></view>
      </view>
    </view>

    <view class="detail-card">
      <text class="section-title">AI 诊断</text>
      <view class="ai-box"><text class="ai-title">原因分析</text><text class="ai-text">{{ alert.aiDiagnosis.reason }}</text></view>
      <view class="ai-box"><text class="ai-title">处置建议</text><text class="ai-text">{{ alert.aiDiagnosis.suggestion }}</text></view>
      <view class="ai-box"><text class="ai-title">历史相似案例</text><text v-for="(item, index) in alert.aiDiagnosis.similarCases" :key="'case' + index" class="ai-list">• {{ item }}</text></view>
      <view class="ai-box"><text class="ai-title">处置 SOP</text><text v-for="(item, index) in alert.aiDiagnosis.sop" :key="'sop' + index" class="ai-list">{{ index + 1 }}. {{ item }}</text></view>
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
        <view v-for="(record, index) in alert.processingRecords" :key="index" class="record-item"><view class="record-line"></view><view class="record-body"><text class="record-time">{{ record.time }}</text><text class="record-content">{{ record.content }}</text><text class="record-operator">{{ record.operator }}</text></view></view>
      </view>
    </view>

    <view v-if="alert.status === 'unresolved'" class="detail-card">
      <text class="section-title">一键处置</text>
      <input v-model="handleForm.result" class="form-input" placeholder="填写处置结果" />
      <textarea v-model="handleForm.notes" class="form-textarea" placeholder="填写现场说明"></textarea>
      <input v-model="handleForm.photoUrl" class="form-input" placeholder="上传照片地址（示例）" />
      <view class="action-buttons stacked">
        <button class="btn-primary" @click="submitHandle">提交闭环</button>
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
      alert: {
        id: 1,
        title: 'VOCs 浓度超标',
        time: '2026-04-13 10:00',
        description: 'VOCs 浓度达到 65.2 mg/m³，超过阈值 50 mg/m³，持续时间超过 5 分钟',
        level: 'high',
        status: 'unresolved',
        deviceId: 'DEV-001',
        location: '废气处理车间 A',
        type: '浓度超标',
        predictionCurve: [],
        aiDiagnosis: { reason: '', suggestion: '', similarCases: [], sop: [] },
        data: [{ label: 'VOCs 浓度', value: '65.2', unit: 'mg/m³', threshold: '50 mg/m³' }],
        processingRecords: [{ time: '2026-04-13 10:05', content: '系统自动检测到告警', operator: '系统' }]
      }
    };
  },
  onLoad(options) {
    this.alertId = options?.id || null;
    this.loadAlertDetail();
  },
  computed: {
    levelText() {
      if (this.alert.level === 'high') return '紧急';
      if (this.alert.level === 'medium') return '警告';
      if (this.alert.level === 'low') return '信息';
      return '未知';
    }
  },
  methods: {
    async loadAlertDetail() {
      if (!this.alertId) return;
      try {
        const res = await request({ url: `/alerts/${this.alertId}` });
        if (res && res.code === 200 && res.data) this.alert = res.data;
      } catch (error) {
        uni.showToast({ title: '详情加载失败', icon: 'none' });
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
        uni.showToast({ title: '处置记录已提交', duration: 1000 });
        this.handleForm = { result: '', notes: '', photoUrl: '' };
        await this.loadAlertDetail();
      } catch (error) {
        uni.showToast({ title: '提交失败', icon: 'none' });
      }
    }
  }
};
</script>

<style>
.alert-detail-page { min-height: 100vh; padding: 24rpx 24rpx calc(36rpx + env(safe-area-inset-bottom)); background: linear-gradient(180deg, #f7f3ff 0%, #fdfcff 52%, #ffffff 100%); }
.detail-hero,.detail-card { margin-bottom: 20rpx; padding: 26rpx; border-radius: 28rpx; background: #fff; box-shadow: 0 16rpx 36rpx rgba(49,30,109,.06); }
.detail-hero { display:flex; justify-content:space-between; align-items:flex-start; gap:18rpx; }
.hero-main { display:flex; gap:18rpx; flex:1; }
.hero-icon { width:74rpx; height:74rpx; border-radius:24rpx; display:flex; align-items:center; justify-content:center; font-size:32rpx; }
.hero-icon.high { background:#ffe9ee; } .hero-icon.medium { background:#fff5df; } .hero-icon.low { background:#e9f4ff; }
.hero-kicker { display:inline-block; font-size:18rpx; color:#7b61ff; letter-spacing:2rpx; font-weight:700; }
.page-title { display:block; margin-top:12rpx; font-size:36rpx; font-weight:800; color:#2d2454; }
.page-subtitle { display:block; margin-top:10rpx; font-size:19rpx; color:#9589af; }
.alert-status { padding:10rpx 16rpx; border-radius:999rpx; font-size:18rpx; font-weight:700; }
.alert-status.unresolved { background:#ffe9ee; color:#dd5175; } .alert-status.resolved { background:#efeaff; color:#7b61ff; }
.section-title { display:block; font-size:31rpx; font-weight:800; color:#2d2454; }
.description-content,.ai-text,.record-content { display:block; margin-top:14rpx; font-size:21rpx; line-height:1.7; color:#6f6686; }
.meta-grid,.prediction-list { display:grid; grid-template-columns:repeat(2,1fr); gap:16rpx; margin-top:18rpx; }
.meta-item,.prediction-item,.ai-box,.data-item,.record-body { padding:18rpx; border-radius:22rpx; background:#faf8ff; }
.meta-label,.data-threshold,.record-time,.info-label { font-size:18rpx; color:#9a8fb2; }
.meta-value,.prediction-value,.data-label,.data-value { display:block; margin-top:10rpx; font-size:21rpx; font-weight:700; color:#2d2454; }
.meta-value.high { color:#dd5175; } .meta-value.medium { color:#d48618; } .meta-value.low { color:#3c86c5; }
.prediction-label,.ai-title { font-size:19rpx; color:#7b61ff; font-weight:700; }
.ai-list { display:block; margin-top:10rpx; font-size:20rpx; line-height:1.6; color:#6f6686; }
.data-list,.records-list { display:flex; flex-direction:column; gap:16rpx; margin-top:18rpx; }
.data-top,.data-main { display:flex; justify-content:space-between; align-items:center; gap:12rpx; }
.data-main { justify-content:flex-start; align-items:baseline; }
.data-unit,.record-operator { font-size:18rpx; color:#8d82aa; }
.record-item { display:flex; gap:16rpx; }
.record-line { width:8rpx; border-radius:999rpx; background:linear-gradient(180deg,#7b61ff 0%,#b19cff 100%); }
.form-input,.form-textarea { width:100%; margin-top:16rpx; padding:18rpx 20rpx; border-radius:20rpx; background:#faf8ff; font-size:21rpx; }
.form-textarea { min-height:160rpx; }
.action-buttons { display:flex; gap:16rpx; margin-top:20rpx; }
.action-buttons.stacked { flex-direction:column; }
.btn-primary,.btn-secondary { width:100%; height:96rpx; border-radius:22rpx; font-size:23rpx; font-weight:700; }
.btn-primary { background:linear-gradient(135deg,#7b61ff 0%,#947dff 100%); color:#fff; }
.btn-secondary { background:#fff; color:#7b61ff; border:2rpx solid #e8e0ff; }
.btn-primary::after,.btn-secondary::after { border:none; }
</style>
