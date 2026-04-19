<template>
  <view class="auth-page">
    <view class="auth-bg">
      <view class="auth-blob blob-1"></view>
      <view class="auth-blob blob-2"></view>
      <view class="auth-blob blob-3"></view>
    </view>

    <view class="auth-content">
      <!-- 顶部 logo 和标题 -->
      <view class="login-header">
        <view class="logo-container">
          <text class="logo-text">废气监测系统</text>
        </view>
        <text class="login-title">用户登录</text>
        <text class="login-subtitle">请输入您的账号和密码</text>
      </view>

      <!-- 登录表单 -->
      <view class="auth-card login-form">
        <view class="form-item">
          <text class="form-label">账号</text>
          <input
            class="form-input"
            :value="form.username"
            @input="(e) => { form.username = (e && e.detail && e.detail.value !== undefined) ? e.detail.value : (e && e.target ? e.target.value : '') }
            "
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
        <view class="form-options">
          <view class="checkbox-group">
            <checkbox 
              :checked="form.remember" 
              @change="(e) => { form.remember = e.detail.value; }"
              class="checkbox"
            />
            <text class="checkbox-label">记住密码</text>
          </view>
          <text class="forgot-password" @click="forgotPassword">忘记密码？</text>
        </view>
        <button class="btn-primary btn-block login-btn" @click="login">登录</button>
        <view class="register-link">
          <text>还没有账号？</text>
          <text class="register-text" @click="navigateToRegister">立即注册</text>
        </view>
      </view>
    </view>
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
        remember: false
      },
      submitting: false
    };
  },
  methods: {
    async login() {
      if (!this.form.username) {
        uni.showToast({ title: '请输入账号', icon: 'none' });
        return;
      }
      if (!this.form.password) {
        uni.showToast({ title: '请输入密码', icon: 'none' });
        return;
      }

      if (this.submitting) return;
      this.submitting = true;
      uni.showLoading({ title: '登录中...' });
      try {
        const res = await request({
          url: '/api/auth/login',
          method: 'POST',
          data: {
            username: this.form.username,
            password: this.form.password
          }
        });
        uni.setStorageSync('token', res.token || '');
        uni.setStorageSync('userInfo', res.user || {});

        uni.showToast({ title: '登录成功', icon: 'success' });
        setTimeout(() => {
          uni.switchTab({ url: '/pages/index/index' });
        }, 600);
      } catch (err) {
        uni.showToast({ title: err.message || '登录失败', icon: 'none' });
      } finally {
        uni.hideLoading();
        this.submitting = false;
      }
    },
    forgotPassword() {
      uni.showToast({ title: '忘记密码功能', icon: 'none' });
    },
    navigateToRegister() {
      uni.navigateTo({ url: '/pages/auth/register' });
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
  display: flex;
  flex-direction: column;
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

.login-header {
  text-align: center;
  margin-bottom: 28rpx;
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

.login-title {
  font-size: 32rpx;
  font-weight: 700;
  color: var(--text-main);
  margin-bottom: 12rpx;
}

.login-subtitle {
  font-size: 20rpx;
  color: var(--text-second);
}

.login-form {
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

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 40rpx;
}

.checkbox-group {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.checkbox {
  transform: scale(0.9);
}

.checkbox-label {
  font-size: 18rpx;
  color: var(--text-second);
}

.forgot-password {
  font-size: 18rpx;
  color: var(--primary);
  padding: 8rpx 0;
}

.login-btn {
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

.register-link {
  text-align: center;
  font-size: 18rpx;
  color: var(--text-second);
}

.register-text {
  color: var(--primary);
  margin-left: 8rpx;
}
</style>