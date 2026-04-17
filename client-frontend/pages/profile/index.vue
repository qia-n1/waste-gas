<template>
  <view class="profile-page">
    <view class="profile-hero">
      <view class="hero-left">
        <view class="user-avatar"><text class="avatar-text">{{ userAvatar }}</text></view>
        <view class="user-details">
          <text class="username">{{ userInfo.username || '未登录用户' }}</text>
          <text class="user-role">{{ userInfo.role || '普通用户' }}</text>
          <text class="user-area">负责区域：{{ areaText }}</text>
        </view>
      </view>
      <button class="btn-edit" @click="editProfile">编辑</button>
    </view>

    <view class="profile-card">
      <view class="section-head"><view><text class="section-title">我的告警与处置</text><text class="section-desc">查看近期处置记录与巡检情况</text></view></view>
      <view class="summary-grid">
        <view class="summary-box"><text class="summary-label">我的处置</text><text class="summary-value">{{ disposals.length }}</text></view>
        <view class="summary-box"><text class="summary-label">巡检记录</text><text class="summary-value">{{ inspections.length }}</text></view>
      </view>
      <view class="summary-actions">
        <view class="action-pill" @click="navigateTo('/pages/records/index')">处置记录</view>
        <view class="action-pill" @click="navigateTo('/pages/area/index')">我的区域</view>
        <view class="action-pill" @click="navigateTo('/pages/ai/chat')">AI 助手</view>
      </view>
    </view>

    <view class="profile-card">
      <view class="section-head"><view><text class="section-title">个人信息</text><text class="section-desc">账号资料与组织信息</text></view></view>
      <view class="info-list">
        <view class="info-item"><text class="info-label">姓名</text><text class="info-value">{{ userInfo.name || '-' }}</text></view>
        <view class="info-item"><text class="info-label">邮箱</text><text class="info-value">{{ userInfo.email || '-' }}</text></view>
        <view class="info-item"><text class="info-label">电话</text><text class="info-value">{{ userInfo.phone || '-' }}</text></view>
        <view class="info-item"><text class="info-label">所属部门</text><text class="info-value">{{ userInfo.department || '-' }}</text></view>
        <view class="info-item"><text class="info-label">入职时间</text><text class="info-value">{{ userInfo.joinDate || '-' }}</text></view>
      </view>
    </view>

    <view class="profile-card">
      <view class="section-head"><view><text class="section-title">我的处置记录</text><text class="section-desc">支持导出 CSV</text></view><text class="action-link" @click="exportDisposals">导出</text></view>
      <view class="record-list">
        <view v-for="item in disposals" :key="item.id" class="record-item"><text class="record-title">{{ item.result }}</text><text class="record-meta">{{ item.status }} · {{ item.createdAt }}</text></view>
      </view>
    </view>

    <view class="profile-card">
      <view class="section-head"><view><text class="section-title">个人巡检记录</text><text class="section-desc">最近巡检摘要</text></view></view>
      <view class="record-list">
        <view v-for="item in inspections" :key="item.id" class="record-item"><text class="record-title">{{ item.areaName }}</text><text class="record-meta">{{ item.summary }}</text><text class="record-meta">{{ item.createdAt }}</text></view>
      </view>
    </view>

    <view class="logout-section"><button class="btn-logout" @click="logout">退出登录</button></view>
  </view>
</template>

<script>
import { clearAuthState, request } from '../../utils/api';

export default {
  data() {
    return {
      userInfo: { username: '', role: '', name: '', email: '', phone: '', department: '', joinDate: '', areas: [] },
      disposals: [],
      inspections: [],
      loading: false,
    };
  },
  computed: {
    userAvatar() { return this.userInfo.username ? this.userInfo.username.charAt(0).toUpperCase() : 'U'; },
    areaText() { return Array.isArray(this.userInfo.areas) && this.userInfo.areas.length ? this.userInfo.areas.join('、') : '未分配'; }
  },
  onShow() { this.loadProfile(); },
  methods: {
    async loadProfile() {
      this.loading = true;
      try {
        const [profileRes, disposalRes, inspectionRes] = await Promise.all([
          request({ url: '/profile/me' }),
          request({ url: '/profile/disposals' }),
          request({ url: '/profile/inspections' })
        ]);
        if (profileRes?.code === 200) this.userInfo = profileRes.data;
        if (disposalRes?.code === 200) this.disposals = disposalRes.data;
        if (inspectionRes?.code === 200) this.inspections = inspectionRes.data;
      } catch (error) {
        if (String(error?.message || '').includes('Unauthorized')) return;
        uni.showToast({ title: '用户信息加载失败', icon: 'none' });
      } finally {
        this.loading = false;
      }
    },
    editProfile() { uni.navigateTo({ url: '/pages/profile/edit' }); },
    async exportDisposals() {
      try {
        const res = await request({ url: '/alerts/exports/disposals' });
        if (res?.code === 200) uni.showModal({ title: '导出内容', content: res.data.content.slice(0, 200) + '...' , showCancel: false });
      } catch (error) {
        uni.showToast({ title: '导出失败', icon: 'none' });
      }
    },
    navigateTo(url) {
      uni.navigateTo({ url });
    },
    logout() {
      uni.showModal({ title: '退出登录', content: '确定要退出登录吗？', success: (res) => {
        if (res.confirm) {
          clearAuthState();
          uni.showToast({ title: '已退出登录', duration: 1000 });
          uni.reLaunch({ url: '/pages/auth/login' });
        }
      }});
    }
  }
};
</script>

<style>
.profile-page { min-height: 100vh; padding: 24rpx 24rpx calc(36rpx + env(safe-area-inset-bottom)); background: linear-gradient(180deg, #f7f3ff 0%, #fcfbff 52%, #ffffff 100%); }
.profile-hero,.profile-card { margin-bottom: 22rpx; padding: 26rpx; border-radius: 28rpx; background: #fff; box-shadow: 0 16rpx 36rpx rgba(49,30,109,.06); }
.profile-hero { display:flex; justify-content:space-between; align-items:center; gap:18rpx; background:linear-gradient(135deg,#7b61ff 0%,#8d74ff 50%,#b39cff 100%); }
.hero-left { display:flex; align-items:center; gap:18rpx; flex:1; }
.user-avatar { width:112rpx; height:112rpx; border-radius:34rpx; background:rgba(255,255,255,.18); display:flex; align-items:center; justify-content:center; font-size:42rpx; font-weight:800; }
.avatar-text,.username,.user-role,.user-area,.btn-edit { color:#fff; }
.username { display:block; font-size:31rpx; font-weight:800; }
.user-role,.user-area { display:block; margin-top:8rpx; font-size:20rpx; opacity:.92; }
.btn-edit { height:78rpx; padding:0 26rpx; border-radius:22rpx; background:rgba(255,255,255,.18); font-size:21rpx; }
.btn-edit::after { border:none; }
.section-head { display:flex; justify-content:space-between; align-items:center; gap:12rpx; margin-bottom:18rpx; }
.section-title { display:block; font-size:31rpx; font-weight:800; color:#2d2454; }
.section-desc { display:block; margin-top:8rpx; font-size:20rpx; color:#8c81a7; }
.action-link { color:#7b61ff; font-size:20rpx; font-weight:700; }
.summary-grid { display:grid; grid-template-columns:repeat(2,1fr); gap:14rpx; }
.summary-box,.info-item,.record-item { padding:20rpx; border-radius:22rpx; background:#faf8ff; }
.summary-actions { display:flex; gap:12rpx; margin-top:14rpx; }
.action-pill { flex:1; text-align:center; padding:16rpx 12rpx; border-radius:18rpx; background:#efeaff; color:#7b61ff; font-size:20rpx; font-weight:700; }
.summary-label,.info-label,.record-meta { display:block; font-size:18rpx; color:#9388ae; }
.summary-value,.info-value,.record-title { display:block; margin-top:10rpx; font-size:23rpx; color:#2d2454; font-weight:700; }
.info-list,.record-list { display:flex; flex-direction:column; gap:14rpx; }
.info-item { display:flex; justify-content:space-between; align-items:center; gap:16rpx; }
.info-value { text-align:right; }
.record-title { margin-top:0; }
.record-meta { margin-top:8rpx; line-height:1.6; }
.logout-section { margin-top:24rpx; }
.btn-logout { width:100%; height:96rpx; border-radius:22rpx; background:linear-gradient(135deg,#7b61ff 0%,#947dff 100%); color:#fff; font-size:23rpx; font-weight:700; }
.btn-logout::after { border:none; }
</style>
