<template>
  <view class="settings-page">
    <view class="settings-hero">
      <view>
        <text class="hero-kicker">SETTINGS</text>
        <text class="page-title">系统设置</text>
        <text class="page-subtitle">统一管理接口、通知、账户与缓存相关配置。</text>
      </view>
      <view class="hero-chip">{{ appVersion }}</view>
    </view>

    <view class="setting-card">
      <view class="card-head"><text class="section-title">消息推送</text><text class="section-desc">告警、系统、设备离线提醒开关</text></view>
      <view class="setting-list">
        <view class="setting-item"><text class="setting-label">告警通知</text><view class="setting-control"><input type="checkbox" class="setting-switch" :checked="notificationSettings.alert" @change="onNotificationChange('alert', $event)" /></view></view>
        <view class="setting-item"><text class="setting-label">系统通知</text><view class="setting-control"><input type="checkbox" class="setting-switch" :checked="notificationSettings.system" @change="onNotificationChange('system', $event)" /></view></view>
        <view class="setting-item"><text class="setting-label">设备离线通知</text><view class="setting-control"><input type="checkbox" class="setting-switch" :checked="notificationSettings.offline" @change="onNotificationChange('offline', $event)" /></view></view>
      </view>
    </view>

    <view class="setting-card">
      <view class="card-head"><text class="section-title">接口与缓存</text><text class="section-desc">管理后端地址与缓存空间</text></view>
      <view class="setting-list">
        <view class="setting-item" @click="changeApiBaseUrl"><text class="setting-label">后端地址</text><view class="setting-value"><text class="value-text">{{ apiBaseUrl }}</text><text class="setting-arrow">→</text></view></view>
        <view class="setting-item" @click="clearCache"><text class="setting-label">清除缓存</text><view class="setting-value"><text class="value-text">{{ cacheSize }}</text><text class="setting-arrow">→</text></view></view>
      </view>
    </view>

    <view class="setting-card">
      <view class="card-head"><text class="section-title">账户安全</text><text class="section-desc">支持修改密码</text></view>
      <input v-model="passwordForm.oldPassword" class="form-input" password placeholder="请输入原密码" />
      <input v-model="passwordForm.newPassword" class="form-input" password placeholder="请输入新密码（至少 6 位）" />
      <button class="primary-btn" @click="submitPasswordChange">修改密码</button>
    </view>

    <view class="setting-card">
      <view class="card-head"><text class="section-title">消息记录</text><text class="section-desc">最近收到的实时提醒</text></view>
      <view class="message-list">
        <view v-for="item in notifications" :key="item.id" class="message-item"><text class="message-title">{{ item.title }}</text><text class="message-content">{{ item.content }}</text><text class="message-meta">{{ item.createdAt }}</text></view>
      </view>
    </view>
  </view>
</template>

<script>
import { getBaseUrl, request, setBaseUrl } from '../../utils/api';

export default {
  data() {
    return {
      notificationSettings: { alert: true, system: true, offline: true },
      displaySettings: { darkMode: false, language: '简体中文' },
      apiBaseUrl: '',
      cacheSize: '12.5 MB',
      appVersion: 'v1.0.0',
      notifications: [],
      passwordForm: { oldPassword: '', newPassword: '' }
    };
  },
  onShow() {
    this.apiBaseUrl = getBaseUrl();
    this.loadSettings();
    this.loadNotifications();
  },
  methods: {
    async loadSettings() {
      try {
        const res = await request({ url: '/settings' });
        if (res?.code === 200 && res.data) {
          this.notificationSettings = res.data.notificationSettings;
          this.displaySettings = res.data.displaySettings;
          this.cacheSize = res.data.cacheSize;
          this.appVersion = res.data.appVersion;
        }
      } catch (error) {
        uni.showToast({ title: '设置加载失败', icon: 'none' });
      }
    },
    async loadNotifications() {
      try {
        const res = await request({ url: '/profile/notifications' });
        if (res?.code === 200) this.notifications = res.data;
      } catch (error) {
        uni.showToast({ title: '消息加载失败', icon: 'none' });
      }
    },
    async saveSettings() {
      try {
        await request({ url: '/settings', method: 'PUT', data: { alert: this.notificationSettings.alert, system: this.notificationSettings.system, offline: this.notificationSettings.offline, darkMode: this.displaySettings.darkMode, language: this.displaySettings.language } });
      } catch (error) {
        uni.showToast({ title: '设置保存失败', icon: 'none' });
      }
    },
    async onNotificationChange(field, event) {
      this.notificationSettings[field] = Boolean(event?.target?.checked);
      await this.saveSettings();
      uni.showToast({ title: '通知设置已更新', duration: 1000 });
    },
    changeApiBaseUrl() {
      uni.showModal({ title: '设置后端地址', editable: true, placeholderText: '例如 http://127.0.0.1:8002/api/v1', content: this.apiBaseUrl, success: (res) => {
        if (res.confirm && res.content) {
          const value = res.content.trim().replace(/\/$/, '');
          setBaseUrl(value);
          this.apiBaseUrl = value;
          uni.showToast({ title: '后端地址已保存', duration: 1000 });
        }
      }});
    },
    clearCache() {
      this.cacheSize = '0 MB';
      uni.showToast({ title: '缓存已清除', duration: 1000 });
    },
    async submitPasswordChange() {
      if (!this.passwordForm.oldPassword || !this.passwordForm.newPassword) return uni.showToast({ title: '请填写完整密码', icon: 'none' });
      try {
        await request({ url: '/profile/change-password', method: 'POST', data: this.passwordForm });
        this.passwordForm = { oldPassword: '', newPassword: '' };
        uni.showToast({ title: '密码修改成功', duration: 1000 });
      } catch (error) {
        uni.showToast({ title: error?.message || '修改失败', icon: 'none' });
      }
    }
  }
};
</script>

<style>
.settings-page { min-height: 100vh; padding: 24rpx 24rpx calc(36rpx + env(safe-area-inset-bottom)); background: linear-gradient(180deg, #f7f3ff 0%, #fcfbff 52%, #ffffff 100%); }
.settings-hero,.setting-card { margin-bottom: 22rpx; padding: 26rpx; border-radius: 28rpx; background: #fff; box-shadow: 0 16rpx 36rpx rgba(49,30,109,.06); }
.settings-hero { display:flex; justify-content:space-between; align-items:flex-end; gap:20rpx; }
.hero-kicker { display:inline-block; font-size:18rpx; color:#7b61ff; letter-spacing:2rpx; font-weight:700; }
.page-title { display:block; margin-top:14rpx; font-size:42rpx; font-weight:800; color:#2b2156; }
.page-subtitle { display:block; margin-top:10rpx; font-size:21rpx; line-height:1.6; color:#8378a1; }
.hero-chip { padding:12rpx 18rpx; border-radius:999rpx; background:#efe9ff; color:#7b61ff; font-size:21rpx; font-weight:700; }
.card-head { margin-bottom:18rpx; }
.section-title { display:block; font-size:31rpx; font-weight:800; color:#2d2454; }
.section-desc { display:block; margin-top:8rpx; font-size:20rpx; color:#8c81a7; }
.setting-list,.message-list { display:flex; flex-direction:column; gap:14rpx; }
.setting-item,.message-item { display:flex; justify-content:space-between; align-items:center; gap:16rpx; padding:20rpx; border-radius:22rpx; background:#faf8ff; }
.setting-label,.message-title { font-size:23rpx; color:#2d2454; font-weight:700; }
.setting-value { display:flex; align-items:center; gap:12rpx; max-width:56%; }
.value-text,.message-content,.message-meta { font-size:19rpx; color:#9388ae; }
.setting-arrow { font-size:21rpx; color:#9b90b3; }
.setting-control { display:flex; align-items:center; }
.setting-switch { width:44px; height:24px; accent-color:#7B61FF; }
.form-input { width:100%; margin-top:14rpx; padding:18rpx 20rpx; border-radius:20rpx; background:#faf8ff; font-size:21rpx; }
.primary-btn { width:100%; height:96rpx; margin-top:18rpx; border-radius:22rpx; background:linear-gradient(135deg,#7b61ff 0%,#947dff 100%); color:#fff; font-size:23rpx; font-weight:700; }
.primary-btn::after { border:none; }
.message-item { display:block; }
.message-content,.message-meta { display:block; margin-top:8rpx; line-height:1.6; }
</style>
