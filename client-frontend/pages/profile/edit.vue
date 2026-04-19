<template>
  <view class="edit-page">
    <view class="edit-hero">
      <view class="hero-text">
        <text class="page-title">编辑资料</text>
        <text class="page-subtitle">姓名、邮箱、电话与密码</text>
      </view>
      <view class="hero-chip">{{ userInfo.role || '普通用户' }}</view>
    </view>
    <view class="quick-nav">
      <button class="secondary-btn ghost" @click="goBack">返回个人中心</button>
    </view>

    <view class="edit-card">
      <view class="card-head">
        <text class="section-title">固定信息（不可修改）</text>
        <text class="section-desc">由管理员维护</text>
      </view>
      <view class="form-grid">
        <view class="form-item">
          <text class="form-label">用户名</text>
          <input class="form-input readonly" :value="userInfo.username || '-'" disabled />
        </view>
        <view class="form-item">
          <text class="form-label">所属部门</text>
          <input class="form-input readonly" :value="userInfo.department || '-'" disabled />
        </view>
        <view class="form-item">
          <text class="form-label">入职时间</text>
          <input class="form-input readonly" :value="userInfo.joinDate || '-'" disabled />
        </view>
      </view>
    </view>

    <view class="edit-card">
      <view class="card-head">
        <text class="section-title">基础信息（可修改）</text>
        <text class="section-desc">保存后会更新到当前账号资料</text>
      </view>
      <view class="form-grid">
        <view class="form-item">
          <text class="form-label">姓名</text>
          <input v-model="form.name" class="form-input" placeholder="请输入姓名" />
        </view>
        <view class="form-item">
          <text class="form-label">邮箱</text>
          <input v-model="form.email" class="form-input" placeholder="请输入邮箱" />
        </view>
        <view class="form-item">
          <text class="form-label">手机号</text>
          <input v-model="form.phone" class="form-input" placeholder="请输入手机号" />
        </view>
      </view>
      <button class="primary-btn" @click="saveProfile">保存基础信息</button>
    </view>

    <view class="edit-card">
      <view class="card-head">
        <text class="section-title">密码修改</text>
        <text class="section-desc">需填写原密码，新密码至少 6 位</text>
      </view>
      <view class="form-grid">
        <view class="form-item">
          <text class="form-label">原密码</text>
          <input v-model="passwordForm.oldPassword" class="form-input" password placeholder="请输入原密码" />
        </view>
        <view class="form-item">
          <text class="form-label">新密码</text>
          <input v-model="passwordForm.newPassword" class="form-input" password placeholder="请输入新密码" />
        </view>
        <view class="form-item">
          <text class="form-label">确认新密码</text>
          <input v-model="passwordForm.confirmPassword" class="form-input" password placeholder="请再次输入新密码" />
        </view>
      </view>
      <button class="secondary-btn" @click="changePassword">修改密码</button>
    </view>
  </view>
</template>

<script>
import { request, setAuthState } from '../../utils/api';

export default {
  data() {
    return {
      userInfo: {
        username: '',
        role: '',
        department: '',
        joinDate: '',
      },
      form: {
        name: '',
        email: '',
        phone: '',
      },
      passwordForm: {
        oldPassword: '',
        newPassword: '',
        confirmPassword: '',
      },
      loading: false,
      saving: false,
    };
  },
  onShow() {
    this.loadProfile();
  },
  methods: {
    async loadProfile() {
      this.loading = true;
      try {
        const res = await request({ url: '/profile/me' });
        if (res?.code === 200 && res.data) {
          this.userInfo = res.data;
          this.form = {
            name: res.data.name || '',
            email: res.data.email || '',
            phone: res.data.phone || '',
          };
        }
      } catch (error) {
        uni.showToast({ title: '个人信息加载失败', icon: 'none' });
      } finally {
        this.loading = false;
      }
    },
    async saveProfile() {
      const payload = {
        name: String(this.form.name || '').trim(),
        email: String(this.form.email || '').trim(),
        phone: String(this.form.phone || '').trim(),
      };

      if (!payload.name || !payload.email || !payload.phone) {
        uni.showToast({ title: '请完整填写可编辑信息', icon: 'none' });
        return;
      }

      this.saving = true;
      try {
        const res = await request({ url: '/profile/update', method: 'POST', data: payload });
        if (res?.code === 200 && res.data) {
          this.userInfo = res.data;
          setAuthState({ user: res.data });
          uni.showToast({ title: '个人信息已保存', duration: 1000 });
        }
      } catch (error) {
        uni.showToast({ title: error?.message || '保存失败', icon: 'none' });
      } finally {
        this.saving = false;
      }
    },
    async changePassword() {
      if (!this.passwordForm.oldPassword || !this.passwordForm.newPassword || !this.passwordForm.confirmPassword) {
        uni.showToast({ title: '请完整填写密码信息', icon: 'none' });
        return;
      }
      if (this.passwordForm.newPassword.length < 6) {
        uni.showToast({ title: '新密码至少 6 位', icon: 'none' });
        return;
      }
      if (this.passwordForm.newPassword !== this.passwordForm.confirmPassword) {
        uni.showToast({ title: '两次输入的新密码不一致', icon: 'none' });
        return;
      }

      try {
        await request({
          url: '/profile/change-password',
          method: 'POST',
          data: {
            old_password: this.passwordForm.oldPassword,
            new_password: this.passwordForm.newPassword,
          },
        });
        this.passwordForm = { oldPassword: '', newPassword: '', confirmPassword: '' };
        uni.showToast({ title: '密码修改成功', duration: 1000 });
      } catch (error) {
        uni.showToast({ title: error?.message || '密码修改失败', icon: 'none' });
      }
    },
    goBack() {
      uni.navigateBack({ delta: 1 });
    },
  },
};
</script>

<style>
.edit-page { min-height: 100vh; padding: 24rpx 24rpx calc(36rpx + env(safe-area-inset-bottom)); background: linear-gradient(180deg, #f7f3ff 0%, #fcfbff 52%, #ffffff 100%); }
.edit-hero,.edit-card { margin-bottom: 22rpx; padding: 26rpx; border-radius: 28rpx; background: #fff; box-shadow: 0 16rpx 36rpx rgba(49,30,109,.06); }
.quick-nav { margin-top: -6rpx; margin-bottom: 18rpx; }
.edit-hero { display:flex; justify-content:space-between; align-items:flex-start; gap:20rpx; }
.hero-text { flex:1; min-width:0; }
.page-title { display:block; font-size:42rpx; font-weight:800; color:#2b2156; line-height:1.2; word-break:break-word; }
.page-subtitle { display:block; margin-top:10rpx; font-size:22rpx; line-height:1.45; color:#8378a1; word-break:break-word; }
.hero-chip { flex-shrink:0; padding:12rpx 18rpx; border-radius:999rpx; background:#efe9ff; color:#7b61ff; font-size:21rpx; font-weight:700; }
.card-head { margin-bottom:18rpx; }
.section-title { display:block; font-size:31rpx; font-weight:800; color:#2d2454; }
.section-desc { display:block; margin-top:8rpx; font-size:20rpx; color:#8c81a7; }
.form-grid { display:flex; flex-direction:column; gap:14rpx; }
.form-item { display:flex; flex-direction:column; gap:10rpx; }
.form-label { font-size:20rpx; color:#6e6488; }
.form-input {
  width:100%;
  height:88rpx;
  line-height:88rpx;
  padding:0 20rpx;
  border-radius:20rpx;
  background:#faf8ff;
  font-size:22rpx;
  color:#2d2454;
  box-sizing:border-box;
  vertical-align:middle;
}
.form-input.readonly { color:#9a8fb6; }
.primary-btn,.secondary-btn { width:100%; height:88rpx; margin-top:18rpx; padding:0 20rpx; border-radius:22rpx; color:#fff; font-size:28rpx; font-weight:700; }
.primary-btn { background:linear-gradient(135deg,#7b61ff 0%,#947dff 100%); }
.secondary-btn { background:linear-gradient(135deg,#8b83a8 0%,#7b7397 100%); }
.secondary-btn.ghost { margin-top:0; background:#fff; color:#7b61ff; border:2rpx solid #e8e0ff; }
.primary-btn::after,.secondary-btn::after { border:none; }
</style>
