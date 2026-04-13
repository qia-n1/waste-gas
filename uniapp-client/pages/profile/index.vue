<template>
  <view class="profile">
    <!-- 顶部用户信息 -->
    <view class="user-info">
      <view class="user-avatar">
        <text class="avatar-text">{{ userInfo.username.charAt(0).toUpperCase() }}</text>
      </view>
      <view class="user-details">
        <text class="username">{{ userInfo.username }}</text>
        <text class="user-role">{{ userInfo.role }}</text>
      </view>
      <view class="user-actions">
        <button class="btn-edit" @click="editProfile">
          <text>编辑</text>
        </button>
      </view>
    </view>

    <!-- 系统功能 -->
    <view class="system-functions">
      <text class="section-title">系统功能</text>
      <view class="function-list">
        <view class="function-item" @click="navigateTo('/pages/monitor/realtime')">
          <view class="function-icon">📊</view>
          <text class="function-text">实时监控</text>
          <text class="function-arrow">→</text>
        </view>
        <view class="function-item" @click="navigateTo('/pages/alerts/list')">
          <view class="function-icon">⚠️</view>
          <text class="function-text">告警中心</text>
          <text class="function-arrow">→</text>
        </view>
        <view class="function-item" @click="navigateTo('/pages/settings/index')">
          <view class="function-icon">⚙️</view>
          <text class="function-text">设置</text>
          <text class="function-arrow">→</text>
        </view>
      </view>
    </view>

    <!-- 个人信息 -->
    <view class="personal-info">
      <text class="section-title">个人信息</text>
      <view class="info-list">
        <view class="info-item">
          <text class="info-label">姓名</text>
          <text class="info-value">{{ userInfo.name }}</text>
        </view>
        <view class="info-item">
          <text class="info-label">邮箱</text>
          <text class="info-value">{{ userInfo.email }}</text>
        </view>
        <view class="info-item">
          <text class="info-label">电话</text>
          <text class="info-value">{{ userInfo.phone }}</text>
        </view>
        <view class="info-item">
          <text class="info-label">所属部门</text>
          <text class="info-value">{{ userInfo.department }}</text>
        </view>
        <view class="info-item">
          <text class="info-label">入职时间</text>
          <text class="info-value">{{ userInfo.joinDate }}</text>
        </view>
      </view>
    </view>

    <!-- 其他功能 -->
    <view class="other-functions">
      <text class="section-title">其他</text>
      <view class="function-list">
        <view class="function-item" @click="showAbout">
          <view class="function-icon">ℹ️</view>
          <text class="function-text">关于我们</text>
          <text class="function-arrow">→</text>
        </view>
        <view class="function-item" @click="showHelp">
          <view class="function-icon">❓</view>
          <text class="function-text">帮助中心</text>
          <text class="function-arrow">→</text>
        </view>
        <view class="function-item" @click="showFeedback">
          <view class="function-icon">💬</view>
          <text class="function-text">意见反馈</text>
          <text class="function-arrow">→</text>
        </view>
      </view>
    </view>

    <!-- 退出登录按钮 -->
    <view class="logout-section">
      <button class="btn-logout" @click="logout">退出登录</button>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      userInfo: {
        username: "admin",
        role: "管理员",
        name: "张三",
        email: "admin@example.com",
        phone: "13800138000",
        department: "技术部",
        joinDate: "2026-01-01"
      }
    };
  },
  methods: {
    editProfile() {
      uni.showToast({ title: '编辑个人信息', duration: 1000 });
    },
    navigateTo(url) {
      uni.navigateTo({ url: url });
    },
    showAbout() {
      uni.showToast({ title: '关于我们', duration: 1000 });
    },
    showHelp() {
      uni.showToast({ title: '帮助中心', duration: 1000 });
    },
    showFeedback() {
      uni.showToast({ title: '意见反馈', duration: 1000 });
    },
    logout() {
      uni.showModal({
        title: '退出登录',
        content: '确定要退出登录吗？',
        success: (res) => {
          if (res.confirm) {
            uni.showToast({ title: '已退出登录', duration: 1000 });
            // 这里可以跳转到登录页面
          }
        }
      });
    }
  }
};
</script>

<style>
.profile {
  padding: 20rpx;
  background-color: #f5f5f5;
  min-height: 100vh;
}

.user-info {
  background-color: #4CAF50;
  color: white;
  padding: 40rpx;
  border-radius: 16rpx;
  margin-bottom: 20rpx;
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.user-avatar {
  width: 100rpx;
  height: 100rpx;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40rpx;
  font-weight: bold;
}

.avatar-text {
  color: white;
}

.user-details {
  flex: 1;
}

.username {
  font-size: 24rpx;
  font-weight: bold;
  margin-bottom: 8rpx;
  display: block;
}

.user-role {
  font-size: 18rpx;
  opacity: 0.9;
  display: block;
}

.btn-edit {
  background-color: rgba(255, 255, 255, 0.2);
  color: white;
  border: none;
  border-radius: 20rpx;
  padding: 8rpx 20rpx;
  font-size: 16rpx;
}

.system-functions {
  background-color: white;
  padding: 20rpx;
  border-radius: 16rpx;
  margin-bottom: 20rpx;
}

.section-title {
  font-size: 24rpx;
  font-weight: bold;
  margin-bottom: 16rpx;
  color: #333;
}

.function-list {
  display: flex;
  flex-direction: column;
  gap: 1rpx;
}

.function-item {
  display: flex;
  align-items: center;
  padding: 20rpx;
  background-color: #f9f9f9;
  border-bottom: 1rpx solid #f0f0f0;
}

.function-item:last-child {
  border-bottom: none;
  border-radius: 0 0 12rpx 12rpx;
}

.function-item:first-child {
  border-radius: 12rpx 12rpx 0 0;
}

.function-icon {
  font-size: 24rpx;
  margin-right: 16rpx;
  width: 32rpx;
  text-align: center;
}

.function-text {
  flex: 1;
  font-size: 18rpx;
  color: #333;
}

.function-arrow {
  font-size: 16rpx;
  color: #999;
}

.personal-info {
  background-color: white;
  padding: 20rpx;
  border-radius: 16rpx;
  margin-bottom: 20rpx;
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16rpx;
  background-color: #f9f9f9;
  border-radius: 12rpx;
}

.info-label {
  font-size: 16rpx;
  color: #666;
}

.info-value {
  font-size: 16rpx;
  color: #333;
  font-weight: 500;
}

.other-functions {
  background-color: white;
  padding: 20rpx;
  border-radius: 16rpx;
  margin-bottom: 20rpx;
}

.logout-section {
  margin-bottom: 40rpx;
}

.btn-logout {
  width: 100%;
  background-color: white;
  color: #ff4444;
  border: 1rpx solid #ff4444;
  border-radius: 12rpx;
  padding: 20rpx;
  font-size: 18rpx;
  font-weight: 500;
}
</style>