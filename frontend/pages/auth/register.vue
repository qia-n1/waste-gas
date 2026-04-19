<template>
  <view class="auth-page">
    <view class="auth-bg">
      <view class="auth-blob blob-1"></view>
      <view class="auth-blob blob-2"></view>
      <view class="auth-blob blob-3"></view>
    </view>

    <!-- 注册表单（使用 scroll-view 避免小屏/键盘遮挡） -->
    <scroll-view class="auth-content" scroll-y :show-scrollbar="false">
      <!-- 顶部 logo 和标题 -->
      <view class="register-header">
        <view class="logo-container">
          <text class="logo-text">废气监测系统</text>
        </view>
        <text class="register-title">用户注册</text>
        <text class="register-subtitle">请填写您的注册信息</text>
      </view>

      <view class="auth-card register-form">
        <view class="form-item">
          <text class="form-label">账号</text>
          <input
            class="form-input"
            :value="form.username"
            @input="(e) => { form.username = (e && e.detail && e.detail.value !== undefined) ? e.detail.value : (e && e.target ? e.target.value : '') }"
            placeholder="请输入账号"
            placeholder-style="color: var(--text-desc);"
          />
        </view>
        <view class="form-item">
          <text class="form-label">密码</text>
          <input
            class="form-input"
            :value="form.password"
            @input="(e) => { form.password = (e && e.detail && e.detail.value !== undefined) ? e.detail.value : (e && e.target ? e.target.value : '') }"
            type="password"
            placeholder="请输入密码"
            placeholder-style="color: var(--text-desc);"
          />
        </view>
        <view class="form-item">
          <text class="form-label">确认密码</text>
          <input
            class="form-input"
            :value="form.confirmPassword"
            @input="(e) => { form.confirmPassword = (e && e.detail && e.detail.value !== undefined) ? e.detail.value : (e && e.target ? e.target.value : '') }"
            type="password"
            placeholder="请再次输入密码"
            placeholder-style="color: var(--text-desc);"
          />
        </view>
        <view class="form-item">
          <text class="form-label">姓名</text>
          <input
            class="form-input"
            :value="form.name"
            @input="(e) => { form.name = (e && e.detail && e.detail.value !== undefined) ? e.detail.value : (e && e.target ? e.target.value : '') }"
            placeholder="请输入姓名"
            placeholder-style="color: var(--text-desc);"
          />
        </view>
        <view class="form-item">
          <text class="form-label">电话</text>
          <input
            class="form-input"
            :value="form.phone"
            @input="(e) => { form.phone = (e && e.detail && e.detail.value !== undefined) ? e.detail.value : (e && e.target ? e.target.value : '') }"
            placeholder="请输入电话号码"
            placeholder-style="color: var(--text-desc);"
          />
        </view>
        <view class="form-item">
          <text class="form-label">邮箱</text>
          <input
            class="form-input"
            :value="form.email"
            @input="(e) => { form.email = (e && e.detail && e.detail.value !== undefined) ? e.detail.value : (e && e.target ? e.target.value : '') }"
            placeholder="请输入邮箱地址"
            placeholder-style="color: var(--text-desc);"
          />
        </view>
        <button class="btn-primary btn-block register-btn" @click="register">注册</button>
        <view class="login-link">
          <text>已有账号？</text>
          <text class="login-text" @click="navigateToLogin">立即登录</text>
        </view>
      </view>

      <view class="content-bottom-safe"></view>
    </scroll-view>
  </view>
</template>

<script>
import { request } from '@/utils/request';

export default {
  data() {
    return {
      form: {
        username: '',
        password: '',
        confirmPassword: '',
        name: '',
        phone: '',
        email: ''
      },
      submitting: false
    };
  },
  methods: {
    async register() {
      if (!this.form.username) {
        uni.showToast({ title: '请输入账号', icon: 'none' });
        return;
      }
      if (!this.form.password) {
        uni.showToast({ title: '请输入密码', icon: 'none' });
        return;
      }
      if (this.form.password !== this.form.confirmPassword) {
        uni.showToast({ title: '两次输入的密码不一致', icon: 'none' });
        return;
      }
      if (!this.form.name) {
        uni.showToast({ title: '请输入姓名', icon: 'none' });
        return;
      }
      if (!this.form.phone) {
        uni.showToast({ title: '请输入电话号码', icon: 'none' });
        return;
      }
      if (!this.form.email) {
        uni.showToast({ title: '请输入邮箱地址', icon: 'none' });
        return;
      }
      if (this.submitting) return;
      this.submitting = true;
      uni.showLoading({ title: '注册中...' });
      try {
        await request({
          url: '/api/auth/register',
          method: 'POST',
          data: {
            username: this.form.username,
            password: this.form.password,
            name: this.form.name,
            phone: this.form.phone,
            email: this.form.email
          }
        });
        uni.showToast({ title: '注册成功', icon: 'success' });
        setTimeout(() => {
          uni.navigateTo({ url: '/pages/auth/login' });
        }, 600);
      } catch (err) {
        uni.showToast({ title: err.message || '注册失败', icon: 'none' });
      } finally {
        uni.hideLoading();
        this.submitting = false;
      }
    },
    navigateToLogin() {
      uni.navigateTo({ url: '/pages/auth/login' });
    }
  }
};
</script>

<style>
.auth-page {
  min-height: 100vh;
  padding: 40rpx 24rpx;
  padding-bottom: calc(40rpx + env(safe-area-inset-bottom));
  background-color: var(--bg);
  position: relative;
  overflow: hidden;
}

.auth-bg {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(900rpx 520rpx at 20% 10%, rgba(123, 97, 255, 0.22) 0%, rgba(123, 97, 255, 0) 60%),
    radial-gradient(800rpx 480rpx at 85% 22%, rgba(167, 139, 250, 0.20) 0%, rgba(167, 139, 250, 0) 60%),
    linear-gradient(180deg, rgba(243, 240, 255, 0.88) 0%, rgba(255, 255, 255, 0.95) 55%, rgba(255, 255, 255, 1) 100%);
}

.auth-blob {
  position: absolute;
  border-radius: 9999rpx;
  filter: blur(2rpx);
  opacity: 0.9;
}

.blob-1 {
  width: 520rpx;
  height: 520rpx;
  left: -220rpx;
  top: -200rpx;
  background: radial-gradient(circle at 30% 30%, rgba(123, 97, 255, 0.35), rgba(123, 97, 255, 0));
}

.blob-2 {
  width: 460rpx;
  height: 460rpx;
  right: -220rpx;
  top: 40rpx;
  background: radial-gradient(circle at 30% 30%, rgba(167, 139, 250, 0.35), rgba(167, 139, 250, 0));
}

.blob-3 {
  width: 640rpx;
  height: 640rpx;
  left: 120rpx;
  bottom: -380rpx;
  background: radial-gradient(circle at 30% 30%, rgba(243, 240, 255, 1), rgba(243, 240, 255, 0));
}

.auth-content {
  position: relative;
  z-index: 1;
  height: calc(100vh - 80rpx);
}

.auth-card {
  background-color: rgba(255, 255, 255, 0.92);
  border-radius: var(--radius);
  padding: 28rpx;
  box-shadow: 0 18rpx 60rpx rgba(31, 41, 55, 0.08);
  border: 1rpx solid rgba(243, 240, 255, 0.9);
  backdrop-filter: blur(6rpx);
  width: 100%;
}

.content-bottom-safe {
  height: calc(24rpx + env(safe-area-inset-bottom));
}

.register-header {
  text-align: center;
  margin-bottom: 24rpx;
  margin-top: 70rpx;
}

.logo-container {
  width: 120rpx;
  height: 120rpx;
  background: linear-gradient(180deg, var(--primary), var(--primary-light));
  border-radius: 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 32rpx;
  box-shadow: 0 18rpx 60rpx rgba(123, 97, 255, 0.22);
}

.logo-text {
  font-size: 24rpx;
  font-weight: 700;
  color: white;
}

.register-title {
  font-size: 32rpx;
  font-weight: 700;
  color: var(--text-main);
  margin-bottom: 12rpx;
}

.register-subtitle {
  font-size: 20rpx;
  color: var(--text-second);
}

.register-form {
  flex: 1;
}

.form-item {
  margin-bottom: 24rpx;
  width: 100%;
}

.form-label {
  display: block;
  font-size: 20rpx;
  font-weight: 600;
  color: var(--text-main);
  margin-bottom: 12rpx;
}

.form-input {
  background-color: white;
  border: 1rpx solid #E5E7EB;
  border-radius: var(--radius);
  height: 88rpx;
  padding: 0 20rpx;
  font-size: 18rpx;
  color: var(--text-main);
  box-shadow: 0 8rpx 20rpx rgba(31, 41, 55, 0.04);
  width: 100%;
  display: block;
  line-height: 88rpx;
}

.register-btn {
  width: 100%;
  height: 96rpx;
  line-height: 96rpx;
  display: block;
  border: none;
  border-radius: var(--radius);
  background: linear-gradient(135deg, #7B61FF 0%, #8F79FF 100%);
  color: #FFFFFF;
  font-size: 30rpx;
  font-weight: 600;
  text-align: center;
  box-shadow: 0 12rpx 30rpx rgba(123, 97, 255, 0.24);
  margin-bottom: 24rpx;
}

.login-link {
  text-align: center;
  font-size: 18rpx;
  color: var(--text-second);
}

.login-text {
  color: var(--primary);
  margin-left: 8rpx;
}
</style>