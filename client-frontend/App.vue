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
:root {
  --primary: #7B61FF;
  --primary-light: #A78BFA;
  --bg: #ffffff;
  --bg-soft: #f8f5ff;
  --text-main: #1f2937;
  --text-second: #6b7280;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

/* 通用样式 */
.section-title {
  font-size: 31rpx;
  font-weight: bold;
  margin-bottom: 16rpx;
  color: var(--text-main);
}

/* 按钮样式 */
.btn-primary {
  background-color: var(--primary);
  color: white;
  border: none;
  border-radius: 12rpx;
  padding: 16rpx;
  font-size: 23rpx;
  font-weight: 500;
}

.btn-secondary {
  background-color: white;
  color: var(--primary);
  border: 1rpx solid var(--primary);
  border-radius: 12rpx;
  padding: 16rpx;
  font-size: 23rpx;
  font-weight: 500;
}

/* 卡片样式 */
.card {
  background-color: white;
  border-radius: 16rpx;
  padding: 20rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 8rpx 24rpx rgba(123, 97, 255, 0.08);
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
  font-size: 18rpx;
}

.status-tag.normal {
  background-color: #f3f0ff;
  color: var(--primary);
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
  font-size: 23rpx;
  color: #999;
  margin-top: 16rpx;
}
</style>