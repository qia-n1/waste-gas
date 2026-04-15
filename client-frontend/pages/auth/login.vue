<template>
  <view class="auth-page">
    <view class="auth-card">
      <text class="brand">废气监测系统</text>
      <text class="subtitle">实时监控 · 智能预警</text>

      <view class="tab-row">
        <button
          type="button"
          class="tab-btn"
          :class="{ active: mode === 'login' }"
          @click="mode = 'login'"
        >
          登录
        </button>
        <button
          type="button"
          class="tab-btn"
          :class="{ active: mode === 'register' }"
          @click="mode = 'register'"
        >
          注册
        </button>
      </view>

      <view v-if="mode === 'login'" class="form-area">
        <label class="field-label">用户名</label>
        <input v-model.trim="loginForm.username" class="field" placeholder="请输入用户名" />

        <label class="field-label">密码</label>
        <input
          v-model="loginForm.password"
          class="field"
          type="password"
          placeholder="请输入密码"
        />

        <button type="button" class="submit-btn" @click="handleLogin">登录</button>

        <view class="hint">
          <text>输入后端真实账号登录，默认种子账号：admin / password</text>
        </view>
      </view>

      <view v-else class="form-area">
        <label class="field-label">用户名</label>
        <input v-model.trim="registerForm.username" class="field" placeholder="请输入用户名" />

        <label class="field-label">姓名</label>
        <input v-model.trim="registerForm.name" class="field" placeholder="请输入真实姓名" />

        <label class="field-label">邮箱</label>
        <input v-model.trim="registerForm.email" class="field" placeholder="请输入邮箱" />

        <label class="field-label">电话</label>
        <input v-model.trim="registerForm.phone" class="field" placeholder="请输入手机号" />

        <label class="field-label">部门</label>
        <input v-model.trim="registerForm.department" class="field" placeholder="请输入所属部门" />

        <label class="field-label">密码</label>
        <input
          v-model="registerForm.password"
          class="field"
          type="password"
          placeholder="请输入密码（至少6位）"
        />

        <label class="field-label">确认密码</label>
        <input
          v-model="registerForm.confirmPassword"
          class="field"
          type="password"
          placeholder="请再次输入密码"
        />

        <button type="button" class="submit-btn" @click="handleRegister">注册</button>

        <view class="hint">
          <text>注册信息会写入后端，个人中心显示的就是这份资料。</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { request, setAuthState } from '../../utils/api'

export default {
  data() {
    return {
      mode: 'login',
      loginForm: {
        username: '',
        password: '',
      },
      registerForm: {
        username: '',
        name: '',
        email: '',
        phone: '',
        department: '',
        password: '',
        confirmPassword: '',
      },
    }
  },
  methods: {
    completeLogin(payload) {
      setAuthState({
        token: payload.access_token,
        user: payload.user,
      })
      uni.showToast({ title: '登录成功', duration: 800 })
      uni.redirectTo({ url: '/pages/index/index' })
    },

    async handleLogin() {
      const username = this.loginForm.username
      const password = this.loginForm.password

      if (!username || !password) {
        uni.showToast({ title: '请输入用户名和密码', icon: 'none' })
        return
      }

      try {
        const res = await request({
          url: '/auth/login',
          method: 'POST',
          data: { username, password },
        })

        if (res && res.code === 200 && res.data?.access_token) {
          this.completeLogin(res.data)
          return
        }

        uni.showToast({ title: '登录失败，请检查账号密码', icon: 'none' })
      } catch (error) {
        uni.showToast({ title: error?.message || '登录失败，请检查账号密码', icon: 'none' })
      }
    },

    async handleRegister() {
      const username = this.registerForm.username
      const name = this.registerForm.name
      const email = this.registerForm.email
      const phone = this.registerForm.phone
      const department = this.registerForm.department
      const password = this.registerForm.password
      const confirmPassword = this.registerForm.confirmPassword

      if (!username || !name || !email || !phone || !department || !password || !confirmPassword) {
        uni.showToast({ title: '请完整填写注册信息', icon: 'none' })
        return
      }

      if (password.length < 6) {
        uni.showToast({ title: '密码至少 6 位', icon: 'none' })
        return
      }

      if (password !== confirmPassword) {
        uni.showToast({ title: '两次密码输入不一致', icon: 'none' })
        return
      }

      try {
        const res = await request({
          url: '/auth/register',
          method: 'POST',
          data: {
            username,
            name,
            email,
            phone,
            department,
            password,
          },
        })

        if (res && res.code === 200 && res.data?.access_token) {
          this.completeLogin(res.data)
          return
        }

        uni.showToast({ title: '注册失败，请稍后重试', icon: 'none' })
      } catch (error) {
        const message = error?.message || '注册失败，请稍后重试'
        uni.showToast({ title: message, icon: 'none' })
      }
    },
  },
}
</script>

<style>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24rpx;
  background: linear-gradient(145deg, #f3f8f4 0%, #dcefe0 50%, #c7e4cf 100%);
}

.auth-card {
  width: 100%;
  max-width: 760rpx;
  background: #ffffff;
  border-radius: 24rpx;
  padding: 36rpx;
  box-shadow: 0 20rpx 60rpx rgba(39, 93, 53, 0.15);
}

.brand {
  display: block;
  text-align: center;
  font-size: 42rpx;
  font-weight: 700;
  color: #1f6b34;
}

.subtitle {
  display: block;
  text-align: center;
  margin-top: 10rpx;
  font-size: 22rpx;
  color: #6c7f72;
}

.tab-row {
  margin-top: 28rpx;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14rpx;
}

.tab-btn {
  border: none;
  border-radius: 14rpx;
  padding: 16rpx 12rpx;
  background: #eef5f0;
  color: #55705f;
  font-size: 26rpx;
  font-weight: 600;
  cursor: pointer;
}

.tab-btn.active {
  background: #2f8f4a;
  color: #ffffff;
}

.form-area {
  margin-top: 24rpx;
}

.field-label {
  display: block;
  font-size: 22rpx;
  color: #4d6254;
  margin-bottom: 10rpx;
}

.field {
  width: 100%;
  border: 1px solid #cfe0d4;
  border-radius: 12rpx;
  padding: 16rpx;
  margin-bottom: 18rpx;
  font-size: 24rpx;
  outline: none;
}

.field:focus {
  border-color: #2f8f4a;
  box-shadow: 0 0 0 3px rgba(47, 143, 74, 0.12);
}

.submit-btn {
  width: 100%;
  border: none;
  border-radius: 12rpx;
  padding: 18rpx;
  font-size: 28rpx;
  font-weight: 700;
  color: #fff;
  background: #2f8f4a;
  cursor: pointer;
}

.submit-btn:hover {
  background: #25763c;
}

.hint {
  margin-top: 16rpx;
  text-align: center;
  color: #6c7f72;
  font-size: 20rpx;
}
</style>
