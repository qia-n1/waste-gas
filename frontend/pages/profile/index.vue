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
          <view class="function-icon text-icon">监</view>
          <text class="function-text">实时监控</text>
          <text class="function-arrow">→</text>
        </view>
        <view class="function-item" @click="navigateTo('/pages/alerts/list')">
          <view class="function-icon text-icon">警</view>
          <text class="function-text">告警中心</text>
          <text class="function-arrow">→</text>
        </view>
        <view class="function-item" @click="navigateTo('/pages/inspection/records')">
          <view class="function-icon text-icon">巡</view>
          <text class="function-text">个人巡检记录</text>
          <text class="function-arrow">→</text>
        </view>
        <view class="function-item" @click="navigateTo('/pages/settings/index')">
          <view class="function-icon text-icon">设</view>
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
          <view class="function-icon text-icon">关</view>
          <text class="function-text">关于我们</text>
          <text class="function-arrow">→</text>
        </view>
        <view class="function-item" @click="showHelp">
          <view class="function-icon text-icon">助</view>
          <text class="function-text">帮助中心</text>
          <text class="function-arrow">→</text>
        </view>
        <view class="function-item" @click="showFeedback">
          <view class="function-icon text-icon">反</view>
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
      const tabPages = ['/pages/index/index', '/pages/monitor/realtime', '/pages/alerts/list', '/pages/profile/index'];
      const path = url.split('?')[0];
      if (tabPages.includes(path)) {
        uni.switchTab({ url: path });
      } else {
        uni.navigateTo({ url: url });
      }
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
  min-height: 100vh;
  padding: 24rpx;
  padding-bottom: calc(24rpx + env(safe-area-inset-bottom));
  background:
    radial-gradient(860rpx 460rpx at 8% 0%, rgba(123, 97, 255, 0.12) 0%, rgba(123, 97, 255, 0) 60%),
    linear-gradient(180deg, #f8f5ff 0%, #ffffff 48%, #ffffff 100%);
}

.user-info {
  background-color: var(--primary-ultra-light);
  color: var(--text-main);
  padding: 40rpx;
  border-radius: var(--radius);
  margin-bottom: 24rpx;
  display: flex;
  align-items: center;
  gap: 20rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);
}

.user-avatar {
  width: 100rpx;
  height: 100rpx;
  border-radius: 50%;
  background-color: white;
  border: 4rpx solid var(--primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40rpx;
  font-weight: 700;
  color: var(--primary);
}

.avatar-text {
  color: var(--primary);
}

.user-details {
  flex: 1;
}

.username {
  font-size: 32rpx;
  font-weight: 700;
  margin-bottom: 8rpx;
  display: block;
  color: var(--text-main);
}

.user-role {
  font-size: 22rpx;
  opacity: 0.9;
  display: block;
  color: var(--text-second);
}

.btn-edit {
  background-color: var(--primary);
  color: white;
  border: none;
  border-radius: 20rpx;
  padding: 8rpx 20rpx;
  font-size: 22rpx;
  font-weight: 500;
}

.system-functions {
  background-color: white;
  padding: 20rpx;
  border-radius: var(--radius);
  margin-bottom: 24rpx;
  box-shadow: var(--shadow-2);
  border: 1rpx solid rgba(123, 97, 255, 0.12);
}

.section-title {
  font-size: 32rpx;
  font-weight: 700;
  margin-bottom: 16rpx;
  color: var(--text-main);
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
  background-color: white;
  border-bottom: 1rpx solid var(--primary-ultra-light);
  border-radius: var(--radius);
  margin-bottom: 1rpx;
}

.function-item:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.function-icon {
  margin-right: 16rpx;
  width: 44rpx;
  height: 44rpx;
  border-radius: 12rpx;
  text-align: center;
  color: #FFFFFF;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18rpx;
  font-weight: 700;
  background: linear-gradient(135deg, #7B61FF 0%, #A78BFA 100%);
  box-shadow: 0 8rpx 20rpx rgba(123, 97, 255, 0.2);
}

.function-text {
  flex: 1;
  font-size: 22rpx;
  color: var(--text-main);
}

.function-arrow {
  font-size: 22rpx;
  color: var(--text-desc);
}

.personal-info {
  background-color: white;
  padding: 20rpx;
  border-radius: var(--radius);
  margin-bottom: 24rpx;
  box-shadow: var(--shadow-2);
  border: 1rpx solid rgba(123, 97, 255, 0.12);
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16rpx;
  background-color: var(--primary-ultra-light);
  border-radius: var(--radius);
}

.info-label {
  font-size: 22rpx;
  color: var(--text-second);
}

.info-value {
  font-size: 22rpx;
  color: var(--text-main);
  font-weight: 500;
}

.other-functions {
  background-color: white;
  padding: 20rpx;
  border-radius: var(--radius);
  margin-bottom: 24rpx;
  box-shadow: var(--shadow-2);
  border: 1rpx solid rgba(123, 97, 255, 0.12);
}

.logout-section {
  margin-bottom: 40rpx;
}

.btn-logout {
  width: 100%;
  background-color: var(--primary);
  color: white;
  border: none;
  border-radius: var(--radius);
  height: var(--btn-height);
  font-size: 22rpx;
  font-weight: 600;
  box-shadow: 0 6rpx 22rpx rgba(123, 97, 255, 0.15);
}
</style>