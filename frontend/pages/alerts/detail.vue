<template>
  <view class="alert-detail">
    <!-- 页面标题 -->
    <view class="page-header">
      <text class="page-title">告警详情</text>
    </view>

    <!-- 告警基本信息 -->
    <view class="alert-info">
      <view class="alert-header">
        <view class="alert-icon" :class="alert.level">
          <text class="icon" v-if="alert.level === 'high'">高</text>
          <text class="icon" v-else-if="alert.level === 'medium'">中</text>
          <text class="icon" v-else>低</text>
        </view>
        <view class="alert-title-container">
          <text class="alert-title">{{ alert.title }}</text>
          <text class="alert-time">{{ alert.time }}</text>
        </view>
        <view class="alert-status" :class="alert.status">
          <text v-if="alert.status === 'unresolved'">未处理</text>
          <text v-else>已处理</text>
        </view>
      </view>

      <view class="divider-light"></view>

      <view class="alert-description">
        <text class="description-label">告警描述</text>
        <text class="description-content">{{ alert.description }}</text>
      </view>

      <view class="divider-light"></view>

      <view class="alert-meta">
        <view class="meta-item">
          <text class="meta-label">告警等级</text>
          <text class="meta-value" :class="alert.level">
            {{ levelText }}
          </text>
        </view>
        <view class="meta-item">
          <text class="meta-label">告警设备</text>
          <text class="meta-value">{{ alert.deviceId }}</text>
        </view>
        <view class="meta-item">
          <text class="meta-label">告警位置</text>
          <text class="meta-value">{{ alert.location }}</text>
        </view>
        <view class="meta-item">
          <text class="meta-label">告警类型</text>
          <text class="meta-value">{{ alert.type }}</text>
        </view>
      </view>
    </view>

    <!-- 告警数据 -->
    <view class="alert-data">
      <text class="section-title">告警数据</text>
      <view class="data-list">
        <view v-for="(data, index) in alert.data" :key="index" class="data-item">
          <text class="data-label">{{ data.label }}</text>
          <text class="data-value">{{ data.value }}</text>
          <text class="data-unit">{{ data.unit }}</text>
          <text class="data-threshold">阈值: {{ data.threshold }}</text>
        </view>
      </view>
    </view>

    <!-- 处理记录 -->
    <view class="processing-records">
      <text class="section-title">处理记录</text>
      <view class="records-list">
        <view v-for="(record, index) in alert.processingRecords" :key="index" class="record-item">
          <text class="record-time">{{ record.time }}</text>
          <text class="record-content">{{ record.content }}</text>
          <text class="record-operator">{{ record.operator }}</text>
        </view>
      </view>
    </view>

    <!-- 操作按钮 -->
    <view class="action-buttons" v-if="alert.status === 'unresolved'">
      <button class="btn-primary" @click="resolveAlert">标记为已处理</button>
      <button class="btn-secondary" @click="ignoreAlert">忽略告警</button>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      alert: {
        id: 1,
        title: "VOCs 浓度超标",
        time: "2026-04-13 10:00",
        description: "VOCs 浓度达到 65.2 mg/m³，超过阈值 50 mg/m³，持续时间超过 5 分钟",
        level: "high",
        status: "unresolved",
        deviceId: "DEV-001",
        location: "废气处理车间 A",
        type: "浓度超标",
        data: [
          {
            label: "VOCs 浓度",
            value: "65.2",
            unit: "mg/m³",
            threshold: "50 mg/m³"
          },
          {
            label: "温度",
            value: "25.3",
            unit: "℃",
            threshold: "40 ℃"
          },
          {
            label: "湿度",
            value: "45",
            unit: "%",
            threshold: "80%"
          }
        ],
        processingRecords: [
          {
            time: "2026-04-13 10:05",
            content: "系统自动检测到告警",
            operator: "系统"
          }
        ]
      }
    };
  },
  onLoad(options) {
    // 兼容性保护：options 可能为 undefined
    if (!options || typeof options !== 'object') {
      return;
    }

    // 从参数中获取告警 ID（如存在则可根据 ID 拉取详情）
    const alertId = options.id;
    if (alertId) {
      // TODO: 根据 alertId 请求后端获取真实数据并替换模拟数据
      // this.fetchAlert(alertId)
    }
  },
  computed: {
    levelText() {
      switch (this.alert.level) {
        case 'high': return '紧急';
        case 'medium': return '警告';
        case 'low': return '信息';
        default: return '未知';
      }
    }
  },
  methods: {
    resolveAlert() {
      // 标记告警为已处理
      this.alert.status = 'resolved';
      // 添加处理记录
      this.alert.processingRecords.push({
        time: new Date().toLocaleString(),
        content: "告警已处理",
        operator: "当前用户"
      });
      uni.showToast({ title: '告警已标记为已处理', duration: 1000 });
    },
    ignoreAlert() {
      uni.showToast({ title: '告警已忽略', duration: 1000 });
    }
  }
};
</script>

<style>
.alert-detail {
  min-height: 100vh;
  padding: 24rpx;
  padding-bottom: calc(24rpx + env(safe-area-inset-bottom));
  background:
    radial-gradient(860rpx 460rpx at 8% 0%, rgba(123, 97, 255, 0.12) 0%, rgba(123, 97, 255, 0) 60%),
    linear-gradient(180deg, #f8f5ff 0%, #ffffff 48%, #ffffff 100%);
}

.page-header {
  margin-bottom: 20rpx;
}

.page-title {
  font-size: 32rpx;
  font-weight: 700;
  color: var(--primary);
}

.alert-info {
  background-color: white;
  padding: 20rpx;
  border-radius: var(--radius);
  margin-bottom: 20rpx;
  box-shadow: var(--shadow-2);
  border: 1rpx solid rgba(123, 97, 255, 0.12);
}

.alert-header {
  display: flex;
  align-items: flex-start;
  gap: 16rpx;
  margin-bottom: 20rpx;
}

.alert-icon {
  width: 48rpx;
  height: 48rpx;
  border-radius: 14rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20rpx;
  flex-shrink: 0;
  font-weight: 700;
  color: #FFFFFF;
  border: 1rpx solid rgba(255, 255, 255, 0.9);
}

.alert-icon.high {
  background: linear-gradient(135deg, #EF4444 0%, #F87171 100%);
}

.alert-icon.medium {
  background: linear-gradient(135deg, #F59E0B 0%, #FBBF24 100%);
}

.alert-icon.low {
  background: linear-gradient(135deg, #7B61FF 0%, #A78BFA 100%);
}

.alert-title-container {
  flex: 1;
}

.alert-title {
  font-size: 20rpx;
  font-weight: 600;
  color: var(--text-main);
  margin-bottom: 8rpx;
  display: block;
}

.alert-time {
  font-size: 18rpx;
  color: var(--text-second);
  display: block;
}

.alert-status {
  padding: 4rpx 12rpx;
  border-radius: 12rpx;
  font-size: 18rpx;
  flex-shrink: 0;
}

.alert-status.unresolved {
  background-color: #FFF6F6;
  color: var(--danger);
}

.alert-status.resolved {
  background-color: var(--primary-ultra-light);
  color: var(--primary);
}

.alert-description {
  margin: 20rpx 0;
}

.description-label {
  font-size: 16rpx;
  color: var(--text-second);
  margin-bottom: 8rpx;
  display: block;
}

.description-content {
  font-size: 18rpx;
  color: var(--text-main);
  line-height: 1.4;
}

.alert-meta {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16rpx;
  margin-top: 20rpx;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.meta-label {
  font-size: 18rpx;
  color: var(--text-desc);
}

.meta-value {
  font-size: 20rpx;
  color: var(--text-main);
  font-weight: 500;
}

.meta-value.high {
  color: var(--danger);
}

.meta-value.medium {
  color: var(--warning);
}

.meta-value.low {
  color: var(--primary-light);
}

.alert-data {
  background-color: white;
  padding: 20rpx;
  border-radius: var(--radius);
  margin-bottom: 20rpx;
  box-shadow: var(--shadow-2);
  border: 1rpx solid rgba(123, 97, 255, 0.12);
}

.section-title {
  font-size: 24rpx;
  font-weight: 700;
  margin-bottom: 16rpx;
  color: var(--text-main);
}

.data-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.data-item {
  display: flex;
  flex-direction: column;
  gap: 4rpx;
  padding: 16rpx;
  background-color: var(--primary-ultra-light);
  border-radius: var(--radius);
}

.data-label {
  font-size: 18rpx;
  color: var(--text-second);
}

.data-value {
  font-size: 24rpx;
  font-weight: 700;
  color: var(--text-main);
}

.data-unit {
  font-size: 18rpx;
  color: var(--text-desc);
}

.data-threshold {
  font-size: 18rpx;
  color: var(--text-second);
}

.processing-records {
  background-color: white;
  padding: 20rpx;
  border-radius: var(--radius);
  margin-bottom: 20rpx;
  box-shadow: var(--shadow-2);
  border: 1rpx solid rgba(123, 97, 255, 0.12);
}

.records-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.record-item {
  display: flex;
  flex-direction: column;
  gap: 4rpx;
  padding: 16rpx;
  background-color: var(--primary-ultra-light);
  border-radius: var(--radius);
}

.record-time {
  font-size: 18rpx;
  color: var(--text-desc);
}

.record-content {
  font-size: 20rpx;
  color: var(--text-main);
  line-height: 1.4;
}

.record-operator {
  font-size: 18rpx;
  color: var(--text-second);
  align-self: flex-end;
}

.action-buttons {
  display: flex;
  gap: 16rpx;
  margin-bottom: 20rpx;
}
</style>