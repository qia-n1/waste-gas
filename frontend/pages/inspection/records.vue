<template>
  <view class="inspection-records">
    <view class="page-header">
      <text class="page-title">个人巡检记录</text>
      <text class="page-subtitle">按时间查看你的巡检结果</text>
    </view>

    <view class="filter-bar">
      <view class="chip" :class="{ active: filter === 'all' }" @click="filter = 'all'">全部</view>
      <view class="chip" :class="{ active: filter === 'ok' }" @click="filter = 'ok'">正常</view>
      <view class="chip" :class="{ active: filter === 'warn' }" @click="filter = 'warn'">异常</view>
    </view>

    <view class="list">
      <view
        v-for="item in filtered"
        :key="item.id"
        class="card record"
        @click="openDetail(item)"
      >
        <view class="record-top">
          <view class="left">
            <text class="record-title nowrap">{{ item.title }}</text>
            <text class="record-meta">{{ item.time }} · {{ item.area }}</text>
          </view>
          <view class="tag" :class="item.status">
            <text>{{ item.status === 'ok' ? '正常' : '异常' }}</text>
          </view>
        </view>
        <view class="divider-light"></view>
        <view class="record-bottom">
          <view class="kv">
            <text class="k">巡检点</text>
            <text class="v">{{ item.point }}</text>
          </view>
          <view class="kv">
            <text class="k">备注</text>
            <text class="v nowrap">{{ item.note }}</text>
          </view>
        </view>
      </view>

      <view v-if="filtered.length === 0" class="empty">
        <text class="empty-icon">巡</text>
        <text class="empty-text">暂无巡检记录</text>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      filter: 'all',
      records: [
        { id: 1, title: '日常巡检', time: '2026-04-13 09:20', area: 'A区', point: '废气处理车间 A-01', status: 'ok', note: '风机运行正常，仪表读数稳定' },
        { id: 2, title: '专项巡检', time: '2026-04-12 16:40', area: 'B区', point: '吸附装置 B-03', status: 'warn', note: '压差偏高，建议检查滤材与管路' },
        { id: 3, title: '日常巡检', time: '2026-04-11 10:05', area: 'C区', point: '在线监测 C-02', status: 'ok', note: '无异常' }
      ]
    };
  },
  computed: {
    filtered() {
      if (this.filter === 'all') return this.records;
      return this.records.filter(r => r.status === this.filter);
    }
  },
  methods: {
    openDetail(item) {
      uni.showToast({ title: `打开记录：${item.id}`, icon: 'none' });
    }
  }
};
</script>

<style>
.inspection-records {
  min-height: 100vh;
  padding: 24rpx;
  padding-bottom: calc(24rpx + env(safe-area-inset-bottom));
  background:
    radial-gradient(860rpx 460rpx at 8% 0%, rgba(123, 97, 255, 0.12) 0%, rgba(123, 97, 255, 0) 60%),
    linear-gradient(180deg, #f8f5ff 0%, #ffffff 48%, #ffffff 100%);
}

.page-header {
  margin-bottom: 16rpx;
}

.page-title {
  font-size: 32rpx;
  font-weight: 800;
  color: var(--text-main);
  display: block;
}

.page-subtitle {
  margin-top: 8rpx;
  font-size: 20rpx;
  color: var(--text-second);
  display: block;
}

.filter-bar {
  display: flex;
  gap: 12rpx;
  margin: 16rpx 0 20rpx;
}

.chip {
  padding: 12rpx 18rpx;
  border-radius: 999rpx;
  border: 1rpx solid #E5E7EB;
  background-color: #FFFFFF;
  color: var(--text-second);
  font-size: 20rpx;
}

.chip.active {
  border-color: var(--primary);
  background-color: var(--primary-ultra-light);
  color: var(--primary);
}

.list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.record {
  margin-bottom: 0;
}

.record-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.record-title {
  font-size: 22rpx;
  font-weight: 700;
  color: var(--text-main);
  display: block;
  max-width: 420rpx;
}

.record-meta {
  margin-top: 8rpx;
  font-size: 18rpx;
  color: var(--text-second);
  display: block;
}

.tag {
  padding: 6rpx 14rpx;
  border-radius: 999rpx;
  font-size: 18rpx;
  flex-shrink: 0;
}

.tag.ok {
  background-color: #ECFDF5;
  color: var(--success);
}

.tag.warn {
  background-color: #FEF3C7;
  color: var(--warning);
}

.record-bottom {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.kv {
  display: flex;
  gap: 12rpx;
}

.k {
  width: 96rpx;
  color: var(--text-desc);
  font-size: 18rpx;
  flex-shrink: 0;
}

.v {
  color: var(--text-main);
  font-size: 18rpx;
  flex: 1;
}

.empty-icon {
  width: 72rpx;
  height: 72rpx;
  border-radius: 18rpx;
  background: linear-gradient(135deg, #7B61FF 0%, #A78BFA 100%);
  color: #FFFFFF;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
  font-weight: 700;
}
</style>

