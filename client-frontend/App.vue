<template>
  <view class="app-container">
    <router-view />
  </view>
</template>

<script>
export default {
  name: 'App',
  onLaunch() {
    console.log('App Launch');
  },
  onShow() {
    console.log('App Show');
  },
  onHide() {
    console.log('App Hide');
  }
};
</script>

<style>
/* 全局样式 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.app-container {
  min-height: 100vh;
  background-color: #f5f5f5;
}

/* 通用样式 */
.section-title {
  font-size: 24rpx;
  font-weight: bold;
  margin-bottom: 16rpx;
  color: #333;
}

/* 按钮样式 */
.btn-primary {
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 12rpx;
  padding: 16rpx;
  font-size: 18rpx;
  font-weight: 500;
}

.btn-secondary {
  background-color: white;
  color: #4CAF50;
  border: 1rpx solid #4CAF50;
  border-radius: 12rpx;
  padding: 16rpx;
  font-size: 18rpx;
  font-weight: 500;
}

/* 卡片样式 */
.card {
  background-color: white;
  border-radius: 16rpx;
  padding: 20rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);
}

/* 列表项样式 */
.list-item {
  display: flex;
  align-items: center;
  padding: 20rpx;
  border-bottom: 1rpx solid #f0f0f0;
}

.list-item:last-child {
  border-bottom: none;
}

/* 状态标签 */
.status-tag {
  padding: 4rpx 12rpx;
  border-radius: 12rpx;
  font-size: 14rpx;
}

.status-tag.normal {
  background-color: #e8f5e8;
  color: #4CAF50;
}

.status-tag.warning {
  background-color: #fff3cd;
  color: #ff9800;
}

.status-tag.error {
  background-color: #f8d7da;
  color: #ff4444;
}

/* 加载动画 */
.loading {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40rpx;
}

/* 空状态 */
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60rpx 20rpx;
  text-align: center;
}

.empty-text {
  font-size: 18rpx;
  color: #999;
  margin-top: 16rpx;
}
</style>