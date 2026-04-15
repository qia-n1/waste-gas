<template>
  <view class="settings">
    <!-- 页面标题 -->
    <view class="page-header">
      <text class="page-title">设置</text>
    </view>

    <!-- 接口设置 -->
    <view class="setting-section">
      <text class="section-title">接口设置</text>
      <view class="setting-list">
        <view class="setting-item" @click="changeApiBaseUrl">
          <text class="setting-label">后端地址</text>
          <view class="setting-value">
            <text class="value-text">{{ apiBaseUrl }}</text>
            <text class="setting-arrow">→</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 通知设置 -->
    <view class="setting-section">
      <text class="section-title">通知设置</text>
      <view class="setting-list">
        <view class="setting-item">
          <text class="setting-label">告警通知</text>
          <view class="setting-control">
            <switch 
              v-model="notificationSettings.alert" 
              @change="onNotificationChange"
            />
          </view>
        </view>
        <view class="setting-item">
          <text class="setting-label">系统通知</text>
          <view class="setting-control">
            <switch 
              v-model="notificationSettings.system" 
              @change="onNotificationChange"
            />
          </view>
        </view>
        <view class="setting-item">
          <text class="setting-label">设备离线通知</text>
          <view class="setting-control">
            <switch 
              v-model="notificationSettings.offline" 
              @change="onNotificationChange"
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
              v-model="displaySettings.darkMode" 
              @change="onDisplayChange"
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
import { getBaseUrl, request, setBaseUrl } from '../../utils/api';

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
      apiBaseUrl: '',
      cacheSize: "12.5 MB",
      appVersion: "v1.0.0"
    };
  },
  onShow() {
    this.apiBaseUrl = getBaseUrl();
    this.loadSettings();
  },
  methods: {
    async loadSettings() {
      try {
        const res = await request({ url: '/settings' });
        if (res && res.code === 200 && res.data) {
          this.notificationSettings = res.data.notificationSettings;
          this.displaySettings = res.data.displaySettings;
          this.cacheSize = res.data.cacheSize;
          this.appVersion = res.data.appVersion;
        }
      } catch (error) {
        uni.showToast({ title: '设置加载失败', icon: 'none' });
      }
    },
    async saveSettings() {
      try {
        await request({
          url: '/settings',
          method: 'PUT',
          data: {
            alert: this.notificationSettings.alert,
            system: this.notificationSettings.system,
            offline: this.notificationSettings.offline,
            darkMode: this.displaySettings.darkMode,
            language: this.displaySettings.language
          }
        });
      } catch (error) {
        uni.showToast({ title: '设置保存失败', icon: 'none' });
      }
    },
    async onNotificationChange() {
      await this.saveSettings();
      uni.showToast({ title: '通知设置已更新', duration: 1000 });
    },
    async onDisplayChange() {
      await this.saveSettings();
      uni.showToast({ title: '显示设置已更新', duration: 1000 });
    },
    changeApiBaseUrl() {
      uni.showModal({
        title: '设置后端地址',
        editable: true,
        placeholderText: '例如 http://127.0.0.1:8002/api/v1',
        content: this.apiBaseUrl,
        success: (res) => {
          if (res.confirm && res.content) {
            const value = res.content.trim().replace(/\/$/, '');
            setBaseUrl(value);
            this.apiBaseUrl = value;
            uni.showToast({ title: '后端地址已保存', duration: 1000 });
          }
        }
      });
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
  padding: 20rpx;
  background-color: #f5f5f5;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 20rpx;
}

.page-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
}

.setting-section {
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
  background-color: #f9f9f9;
  border-bottom: 1rpx solid #f0f0f0;
}

.setting-item:last-child {
  border-bottom: none;
  border-radius: 0 0 12rpx 12rpx;
}

.setting-item:first-child {
  border-radius: 12rpx 12rpx 0 0;
}

.setting-label {
  font-size: 18rpx;
  color: #333;
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
  font-size: 16rpx;
  color: #999;
}

.setting-arrow {
  font-size: 16rpx;
  color: #999;
}
</style>