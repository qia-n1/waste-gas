<template>
  <view class="settings">
    <!-- 页面标题 -->
    <view class="page-header">
      <text class="page-title">设置</text>
    </view>

    <!-- 通知设置 -->
    <view class="setting-section">
      <text class="section-title">通知设置</text>
      <view class="setting-list">
        <view class="setting-item">
          <text class="setting-label">告警通知</text>
          <view class="setting-control">
            <switch 
              :checked="notificationSettings.alert" 
              @change="(e) => { notificationSettings.alert = e.detail.value; onNotificationChange(); }"
            />
          </view>
        </view>
        <view class="setting-item">
          <text class="setting-label">系统通知</text>
          <view class="setting-control">
            <switch 
              :checked="notificationSettings.system" 
              @change="(e) => { notificationSettings.system = e.detail.value; onNotificationChange(); }"
            />
          </view>
        </view>
        <view class="setting-item">
          <text class="setting-label">设备离线通知</text>
          <view class="setting-control">
            <switch 
              :checked="notificationSettings.offline" 
              @change="(e) => { notificationSettings.offline = e.detail.value; onNotificationChange(); }"
            />
          </view>
        </view>
      </view>
    </view>

    <!-- 数据设置 -->
    <view class="setting-section">
      <text class="section-title">数据设置</text>
      <view class="setting-list">
        <view class="setting-item" @click="clearCache">
          <text class="setting-label">清除缓存</text>
          <view class="setting-value">
            <text class="value-text">{{ cacheSize }}</text>
            <text class="setting-arrow">→</text>
          </view>
        </view>
        <view class="setting-item" @click="exportData">
          <text class="setting-label">导出数据</text>
          <view class="setting-value">
            <text class="setting-arrow">→</text>
          </view>
        </view>
        <view class="setting-item" @click="importData">
          <text class="setting-label">导入数据</text>
          <view class="setting-value">
            <text class="setting-arrow">→</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 显示设置 -->
    <view class="setting-section">
      <text class="section-title">显示设置</text>
      <view class="setting-list">
        <view class="setting-item">
          <text class="setting-label">深色模式</text>
          <view class="setting-control">
            <switch 
              :checked="displaySettings.darkMode" 
              @change="(e) => { displaySettings.darkMode = e.detail.value; onDisplayChange(); }"
            />
          </view>
        </view>
        <view class="setting-item" @click="changeLanguage">
          <text class="setting-label">语言</text>
          <view class="setting-value">
            <text class="value-text">{{ displaySettings.language }}</text>
            <text class="setting-arrow">→</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 账户设置 -->
    <view class="setting-section">
      <text class="section-title">账户设置</text>
      <view class="setting-list">
        <view class="setting-item" @click="changePassword">
          <text class="setting-label">修改密码</text>
          <view class="setting-value">
            <text class="setting-arrow">→</text>
          </view>
        </view>
        <view class="setting-item" @click="bindPhone">
          <text class="setting-label">绑定手机</text>
          <view class="setting-value">
            <text class="value-text">{{ accountSettings.phone }}</text>
            <text class="setting-arrow">→</text>
          </view>
        </view>
        <view class="setting-item" @click="bindEmail">
          <text class="setting-label">绑定邮箱</text>
          <view class="setting-value">
            <text class="value-text">{{ accountSettings.email }}</text>
            <text class="setting-arrow">→</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 关于 -->
    <view class="setting-section">
      <text class="section-title">关于</text>
      <view class="setting-list">
        <view class="setting-item" @click="showAbout">
          <text class="setting-label">关于我们</text>
          <view class="setting-value">
            <text class="setting-arrow">→</text>
          </view>
        </view>
        <view class="setting-item" @click="checkUpdate">
          <text class="setting-label">检查更新</text>
          <view class="setting-value">
            <text class="value-text">{{ appVersion }}</text>
            <text class="setting-arrow">→</text>
          </view>
        </view>
        <view class="setting-item" @click="showPrivacy">
          <text class="setting-label">隐私政策</text>
          <view class="setting-value">
            <text class="setting-arrow">→</text>
          </view>
        </view>
        <view class="setting-item" @click="showTerms">
          <text class="setting-label">服务条款</text>
          <view class="setting-value">
            <text class="setting-arrow">→</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      notificationSettings: {
        alert: true,
        system: true,
        offline: true
      },
      displaySettings: {
        darkMode: false,
        language: "简体中文"
      },
      accountSettings: {
        phone: "138****8000",
        email: "admin@example.com"
      },
      cacheSize: "12.5 MB",
      appVersion: "v1.0.0"
    };
  },
  methods: {
    onNotificationChange() {
      uni.showToast({ title: '通知设置已更新', duration: 1000 });
    },
    onDisplayChange() {
      uni.showToast({ title: '显示设置已更新', duration: 1000 });
    },
    clearCache() {
      uni.showModal({
        title: '清除缓存',
        content: '确定要清除缓存吗？',
        success: (res) => {
          if (res.confirm) {
            this.cacheSize = "0 MB";
            uni.showToast({ title: '缓存已清除', duration: 1000 });
          }
        }
      });
    },
    exportData() {
      uni.showToast({ title: '数据导出功能', duration: 1000 });
    },
    importData() {
      uni.showToast({ title: '数据导入功能', duration: 1000 });
    },
    changeLanguage() {
      uni.showToast({ title: '语言设置功能', duration: 1000 });
    },
    changePassword() {
      uni.showToast({ title: '修改密码功能', duration: 1000 });
    },
    bindPhone() {
      uni.showToast({ title: '绑定手机功能', duration: 1000 });
    },
    bindEmail() {
      uni.showToast({ title: '绑定邮箱功能', duration: 1000 });
    },
    showAbout() {
      uni.showToast({ title: '关于我们', duration: 1000 });
    },
    checkUpdate() {
      uni.showToast({ title: '当前已是最新版本', duration: 1000 });
    },
    showPrivacy() {
      uni.showToast({ title: '隐私政策', duration: 1000 });
    },
    showTerms() {
      uni.showToast({ title: '服务条款', duration: 1000 });
    }
  }
};
</script>

<style>
.settings {
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

.setting-section {
  background-color: white;
  padding: 20rpx;
  border-radius: var(--radius);
  margin-bottom: 24rpx;
  box-shadow: var(--shadow-2);
  border: 1rpx solid rgba(123, 97, 255, 0.12);
}

.section-title {
  font-size: 28rpx;
  font-weight: 700;
  margin-bottom: 16rpx;
  color: var(--text-main);
}

.setting-list {
  display: flex;
  flex-direction: column;
  gap: 1rpx;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20rpx;
  background-color: white;
  border-bottom: 1rpx solid var(--primary-ultra-light);
  border-radius: var(--radius);
  margin-bottom: 1rpx;
}

.setting-item:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.setting-label {
  font-size: 20rpx;
  color: var(--text-main);
}

.setting-control {
  display: flex;
  align-items: center;
}

.setting-value {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.value-text {
  font-size: 18rpx;
  color: var(--text-second);
}

.setting-arrow {
  font-size: 18rpx;
  color: var(--text-desc);
}
</style>