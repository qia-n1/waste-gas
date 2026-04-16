<template>
  <view class="auth-page">
    <view class="bg-orb orb-left"></view>
    <view class="bg-orb orb-right"></view>
    <view class="bg-grid"></view>

    <scroll-view scroll-y class="auth-scroll" :show-scrollbar="false">
      <view class="auth-shell">
        <view class="hero-panel">
          <text class="hero-kicker">AIR GUARDIAN</text>
          <text class="hero-title">废气监测系统</text>
          <text class="hero-subtitle">用更清晰、更舒适的方式进入实时监控与告警中心。</text>
          <view class="hero-tags">
            <view class="hero-tag"><text class="tag-dot"></text><text class="tag-text">实时监控</text></view>
            <view class="hero-tag"><text class="tag-dot"></text><text class="tag-text">智能预警</text></view>
          </view>
        </view>

        <view class="auth-card">
          <view class="card-top">
            <view>
              <text class="card-title">{{ mode === 'login' ? '欢迎回来' : '创建账号' }}</text>
              <text class="card-subtitle">{{ mode === 'login' ? '登录后查看监测数据与告警信息' : '填写信息后即可自动进入系统' }}</text>
            </view>
            <view class="brand-badge">紫</view>
          </view>

          <view class="tab-row">
            <view class="tab-btn" :class="{ active: mode === 'login' }" @click="switchMode('login')">登录</view>
            <view class="tab-btn" :class="{ active: mode === 'register' }" @click="switchMode('register')">注册</view>
          </view>

          <view v-if="mode === 'login'" class="form-area">
            <view class="field-group">
              <text class="field-label">用户名</text>
              <view class="field-wrap"><text class="field-icon">账号</text><input v-model.trim="loginForm.username" class="field" placeholder="请输入用户名" /></view>
            </view>
            <view class="field-group">
              <text class="field-label">密码</text>
              <view class="field-wrap"><text class="field-icon">密码</text><input v-model="loginForm.password" class="field" type="password" placeholder="请输入密码" /></view>
            </view>
            <view class="submit-btn" @click="handleLogin">立即登录</view>
            <view class="hint-card"><text class="hint-title">快速提示</text><text class="hint-text">请输入后端真实账号，默认种子账号：admin / password</text></view>
          </view>

          <view v-else class="form-area register-area">
            <view class="field-group">
              <text class="field-label">用户名</text>
              <view class="field-wrap"><text class="field-icon">账号</text><input v-model.trim="registerForm.username" class="field" placeholder="请输入用户名" /></view>
            </view>
            <view class="field-grid">
              <view class="field-group half-field">
                <text class="field-label">姓名</text>
                <view class="field-wrap"><text class="field-icon">姓名</text><input v-model.trim="registerForm.name" class="field" placeholder="请输入真实姓名" /></view>
              </view>
              <view class="field-group half-field">
                <text class="field-label">电话</text>
                <view class="field-wrap"><text class="field-icon">电话</text><input v-model.trim="registerForm.phone" class="field" placeholder="请输入手机号" /></view>
              </view>
            </view>
            <view class="field-group">
              <text class="field-label">邮箱</text>
              <view class="field-wrap"><text class="field-icon">邮箱</text><input v-model.trim="registerForm.email" class="field" placeholder="请输入邮箱" /></view>
            </view>
            <view class="field-group">
              <text class="field-label">部门</text>
              <view class="field-wrap"><text class="field-icon">部门</text><input v-model.trim="registerForm.department" class="field" placeholder="请输入所属部门" /></view>
            </view>
            <view class="field-grid">
              <view class="field-group half-field">
                <text class="field-label">密码</text>
                <view class="field-wrap"><text class="field-icon">密码</text><input v-model="registerForm.password" class="field" type="password" placeholder="至少 6 位" /></view>
              </view>
              <view class="field-group half-field">
                <text class="field-label">确认密码</text>
                <view class="field-wrap"><text class="field-icon">确认</text><input v-model="registerForm.confirmPassword" class="field" type="password" placeholder="再次输入密码" /></view>
              </view>
            </view>
            <view class="submit-btn" @click="handleRegister">完成注册</view>
            <view class="hint-card"><text class="hint-title">注册说明</text><text class="hint-text">注册成功后将自动登录，个人中心会展示你填写的资料。</text></view>
          </view>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script>
import { getAuthToken, request, setAuthState } from '../../utils/api'
export default {
  data() {
    return {
      mode: 'login',
      loginForm: { username: '', password: '' },
      registerForm: { username: '', name: '', email: '', phone: '', department: '', password: '', confirmPassword: '' },
    }
  },
  onShow() {
    if (getAuthToken()) {
      uni.switchTab({ url: '/pages/index/index' })
    }
  },
  methods: {
    switchMode(mode) { this.mode = mode },
    completeLogin(payload) {
      setAuthState({ token: payload.access_token, user: payload.user })
      uni.showToast({ title: '登录成功', duration: 800 })
      uni.switchTab({ url: '/pages/index/index' })
    },
    async handleLogin() {
      const { username, password } = this.loginForm
      if (!username || !password) return uni.showToast({ title: '请输入用户名和密码', icon: 'none' })
      try {
        console.log('登录请求开始', { username, password })
        const res = await request({ url: '/auth/login', method: 'POST', data: { username, password } })
        console.log('登录请求响应', res)
        if (res && res.code === 200 && res.data?.access_token) return this.completeLogin(res.data)
        uni.showToast({ title: '登录失败，请检查账号密码', icon: 'none' })
      } catch (error) {
        console.error('登录请求错误', error)
        uni.showToast({ title: error?.message || '登录失败，请检查账号密码', icon: 'none' })
      }
    },
    async handleRegister() {
      console.log('handleRegister called', this.registerForm)
      const { username, name, email, phone, department, password, confirmPassword } = this.registerForm
      if (!username || !name || !email || !phone || !department || !password || !confirmPassword) {
        console.log('表单验证失败：有字段为空')
        return uni.showToast({ title: '请完整填写注册信息', icon: 'none' })
      }
      if (password.length < 6) {
        console.log('表单验证失败：密码长度不足')
        return uni.showToast({ title: '密码至少 6 位', icon: 'none' })
      }
      if (password !== confirmPassword) {
        console.log('表单验证失败：密码不一致')
        return uni.showToast({ title: '两次密码输入不一致', icon: 'none' })
      }
      try {
        console.log('开始发送注册请求')
        const res = await request({ url: '/auth/register', method: 'POST', data: { username, name, email, phone, department, role: '普通用户', password } })
        console.log('注册请求响应', res)
        if (res && res.code === 200 && res.data?.access_token) return this.completeLogin(res.data)
        uni.showToast({ title: '注册失败，请稍后重试', icon: 'none' })
      } catch (error) {
        console.error('注册请求错误', error)
        uni.showToast({ title: error?.message || '注册失败，请稍后重试', icon: 'none' })
      }
    },
  },
}
</script>

<style>
.auth-page { position: relative; min-height: 100vh; overflow: hidden; background: radial-gradient(circle at top left, rgba(255,255,255,.86) 0, rgba(255,255,255,0) 35%), linear-gradient(145deg, #f8f5ff 0%, #eee6ff 45%, #dccdfa 100%); }
.auth-scroll { min-height: 100vh; }
.auth-shell { position: relative; z-index: 2; min-height: 100vh; padding: 52rpx 28rpx calc(52rpx + env(safe-area-inset-bottom)); }
.bg-orb { position: absolute; border-radius: 50%; filter: blur(10rpx); opacity: .7; pointer-events: none; }
.orb-left { top: -120rpx; left: -80rpx; width: 360rpx; height: 360rpx; background: rgba(123,97,255,.18); }
.orb-right { top: 220rpx; right: -120rpx; width: 320rpx; height: 320rpx; background: rgba(255,255,255,.68); }
.bg-grid { position: absolute; inset: 0; opacity: .24; background-image: linear-gradient(rgba(123,97,255,.09) 1px, transparent 1px), linear-gradient(90deg, rgba(123,97,255,.09) 1px, transparent 1px); background-size: 36rpx 36rpx; pointer-events: none; }
.hero-panel { padding: 18rpx 10rpx 26rpx; }
.hero-kicker { display: inline-block; padding: 10rpx 18rpx; border-radius: 999rpx; background: rgba(255,255,255,.72); color: #7b61ff; font-size: 20rpx; font-weight: 700; letter-spacing: 2rpx; box-shadow: 0 10rpx 28rpx rgba(123,97,255,.08); }
.hero-title { display: block; margin-top: 24rpx; font-size: 54rpx; line-height: 1.15; font-weight: 800; color: #2f225d; }
.hero-subtitle { display: block; margin-top: 14rpx; max-width: 560rpx; font-size: 24rpx; line-height: 1.6; color: #6c6492; }
.hero-tags { display: flex; flex-wrap: wrap; gap: 14rpx; margin-top: 24rpx; }
.hero-tag { display: flex; align-items: center; gap: 10rpx; padding: 12rpx 18rpx; border-radius: 999rpx; background: rgba(255,255,255,.72); color: #574e82; box-shadow: 0 12rpx 32rpx rgba(123,97,255,.08); }
.tag-dot { width: 12rpx; height: 12rpx; border-radius: 50%; background: linear-gradient(135deg, #7b61ff 0%, #a78bfa 100%); }
.tag-text { font-size: 22rpx; font-weight: 600; }
.auth-card { margin-top: 18rpx; background: rgba(255,255,255,.9); border: 1rpx solid rgba(255,255,255,.7); border-radius: 32rpx; padding: 32rpx; box-shadow: 0 28rpx 70rpx rgba(90,67,178,.16); }
.card-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 20rpx; }
.card-title { display: block; font-size: 40rpx; font-weight: 800; color: #24184d; }
.card-subtitle { display: block; margin-top: 8rpx; font-size: 22rpx; line-height: 1.5; color: #73698e; }
.brand-badge { min-width: 72rpx; height: 72rpx; border-radius: 22rpx; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #7b61ff 0%, #a78bfa 100%); color: #fff; font-size: 28rpx; font-weight: 800; box-shadow: 0 14rpx 34rpx rgba(123,97,255,.24); }
.tab-row { margin-top: 30rpx; padding: 10rpx; display: grid; grid-template-columns: 1fr 1fr; gap: 12rpx; background: #f2ecff; border-radius: 22rpx; }
.tab-btn { border-radius: 16rpx; padding: 18rpx 12rpx; text-align: center; color: #766d95; font-size: 26rpx; font-weight: 700; }
.tab-btn.active { background: linear-gradient(135deg, #7b61ff 0%, #8f76ff 100%); color: #fff; box-shadow: 0 12rpx 24rpx rgba(123,97,255,.2); }
.form-area { margin-top: 28rpx; }
.field-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18rpx; }
.field-group { margin-bottom: 18rpx; }
.half-field { margin-bottom: 0; }
.field-label { display: block; margin-bottom: 10rpx; font-size: 22rpx; font-weight: 600; color: #5c5476; }
.field-wrap { display: flex; align-items: center; min-height: 96rpx; padding: 0 22rpx; background: #fff; border: 2rpx solid #ece6ff; border-radius: 20rpx; box-shadow: 0 10rpx 24rpx rgba(123,97,255,.06); }
.field-wrap:focus-within { border-color: #8d73ff; box-shadow: 0 0 0 8rpx rgba(123,97,255,.09); }
.field-icon { flex-shrink: 0; min-width: 64rpx; margin-right: 14rpx; font-size: 20rpx; font-weight: 700; color: #927dff; }
.field { width: 100%; height: 96rpx; font-size: 24rpx; color: #2c2548; }
.submit-btn { display: flex; align-items: center; justify-content: center; width: 100%; height: 96rpx; margin-top: 10rpx; border: none; border-radius: 22rpx; background: linear-gradient(135deg, #7b61ff 0%, #a78bfa 100%); color: #fff; font-size: 30rpx; font-weight: 800; letter-spacing: 2rpx; box-shadow: 0 18rpx 34rpx rgba(123,97,255,.22); position: relative; z-index: 10; }
.submit-btn::after { border: none; }
.submit-btn:active { opacity: 0.85; transform: scale(0.98); }
.hint-card { margin-top: 18rpx; padding: 20rpx 22rpx; border-radius: 20rpx; background: linear-gradient(180deg, #f8f5ff 0%, #f3eeff 100%); }
.hint-title { display: block; font-size: 20rpx; font-weight: 700; color: #6c55d9; }
.hint-text { display: block; margin-top: 8rpx; font-size: 20rpx; line-height: 1.6; color: #756b96; }
@media screen and (max-width: 640rpx) {
  .auth-shell { padding-left: 20rpx; padding-right: 20rpx; }
  .auth-card { padding: 26rpx; border-radius: 28rpx; }
  .hero-title { font-size: 48rpx; }
  .field-grid { grid-template-columns: 1fr; gap: 0; }
  .half-field { margin-bottom: 18rpx; }
}
</style>
