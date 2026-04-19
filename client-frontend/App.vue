<template>
  <view />
</template>

<script>
import { resetBaseUrlToDefaultOnce } from './utils/api';

export default {
  onShow() {
    resetBaseUrlToDefaultOnce();
    this.ensureAuthRoute();
  },
  methods: {
    ensureAuthRoute() {
      const token = uni.getStorageSync('authToken');
      const pages = getCurrentPages();
      if (!pages.length) {
        return;
      }
      const route = pages[pages.length - 1].route || '';
      const isLogin = route === 'pages/auth/login';
      if (!token && !isLogin) {
        uni.reLaunch({ url: '/pages/auth/login' });
        return;
      }
      if (token && isLogin) {
        uni.switchTab({ url: '/pages/index/index' });
      }
    },
  },
};
</script>

<style>
:root {
  --wg-primary: #7b61ff;
  --wg-primary-dark: #5f46d6;
  --wg-primary-soft: #efeaff;
  --wg-primary-glow: rgba(123, 97, 255, 0.22);
  --wg-bg: #f7f3ff;
  --wg-bg-soft: #fcfaff;
  --wg-card: #ffffff;
  --wg-card-muted: #faf8ff;
  --wg-text: #2d2454;
  --wg-subtext: #8c81a7;
  --wg-border: #ece5ff;
  --wg-success: #11a36b;
  --wg-warning: #d48618;
  --wg-danger: #dd5175;
  --wg-radius-lg: 28rpx;
  --wg-radius-md: 20rpx;
  --wg-shadow: 0 14rpx 34rpx rgba(49, 30, 109, 0.08);
  --wg-shadow-soft: 0 8rpx 20rpx rgba(49, 30, 109, 0.06);
  --wg-motion-fast: 0.16s;
  --wg-motion-base: 0.28s;
  --wg-motion-slow: 0.42s;
  --wg-ease-standard: cubic-bezier(0.2, 0.7, 0.2, 1);
}

/* WXSS 不支持全局 *，用 page + 常用节点做基础盒模型 */
page {
  box-sizing: border-box;
  color: var(--wg-text);
  background:
    radial-gradient(circle at 12% -6%, rgba(123, 97, 255, 0.12) 0%, rgba(123, 97, 255, 0) 36%),
    radial-gradient(circle at 92% 10%, rgba(172, 152, 255, 0.14) 0%, rgba(172, 152, 255, 0) 32%),
    linear-gradient(180deg, var(--wg-bg) 0%, var(--wg-bg-soft) 52%, #ffffff 100%);
}
view,
text,
image,
button,
input,
textarea,
scroll-view {
  box-sizing: border-box;
}

/* 各页 button 文字垂直居中；具体高度由各页 class 控制 */
button {
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1.25;
  border-radius: var(--wg-radius-md);
  transition: transform var(--wg-motion-fast) var(--wg-ease-standard), opacity var(--wg-motion-fast) var(--wg-ease-standard), box-shadow var(--wg-motion-base) var(--wg-ease-standard), filter var(--wg-motion-base) var(--wg-ease-standard);
}

button:active {
  transform: translateY(1rpx) scale(0.98);
  opacity: 0.95;
}

input,
textarea {
  transition: border-color var(--wg-motion-base) var(--wg-ease-standard), box-shadow var(--wg-motion-base) var(--wg-ease-standard), background var(--wg-motion-base) var(--wg-ease-standard);
}

input:focus,
textarea:focus {
  border-color: rgba(123, 97, 255, 0.45);
  box-shadow: 0 0 0 6rpx rgba(123, 97, 255, 0.08);
  background: #ffffff;
}

[class$='-card'],
[class*='-card '] {
  border-radius: var(--wg-radius-lg);
  box-shadow: var(--wg-shadow);
  border: 1rpx solid rgba(123, 97, 255, 0.06);
}

[class$='-title'],
[class*='-title '] {
  color: var(--wg-text);
}

[class$='-subtitle'],
[class*='-subtitle '],
[class$='-desc'],
[class*='-desc '] {
  color: var(--wg-subtext);
}

[class$='-pill'],
[class*='-pill '],
[class$='-chip'],
[class*='-chip '] {
  border: 1rpx solid rgba(123, 97, 255, 0.12);
  box-shadow: 0 6rpx 16rpx rgba(123, 97, 255, 0.08);
}

[class$='-item'],
[class*='-item '] {
  transition: transform var(--wg-motion-fast) var(--wg-ease-standard), background var(--wg-motion-base) var(--wg-ease-standard), box-shadow var(--wg-motion-base) var(--wg-ease-standard);
}

[class$='-item']:active,
[class*='-item ']:active {
  transform: scale(0.996);
}

.section-head,
.card-head {
  position: relative;
}

.page-title {
  font-size: 42rpx;
  font-weight: 800;
  line-height: 1.2;
}

.page-subtitle {
  margin-top: 10rpx;
  font-size: 22rpx;
  line-height: 1.45;
}

[class$='-hero'],
[class*='-hero '] {
  min-height: 132rpx;
  padding: 30rpx;
  border-radius: 30rpx;
}

.section-title::after {
  content: '';
  display: block;
  width: 48rpx;
  height: 6rpx;
  margin-top: 10rpx;
  border-radius: 999rpx;
  background: linear-gradient(90deg, var(--wg-primary) 0%, rgba(123, 97, 255, 0.2) 100%);
}

.status-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 44rpx;
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  font-size: 18rpx;
  font-weight: 700;
  border: 1rpx solid transparent;
}

.status-tag.normal {
  background: rgba(17, 163, 107, 0.12);
  color: var(--wg-success);
  border-color: rgba(17, 163, 107, 0.18);
}

.status-tag.warning {
  background: rgba(212, 134, 24, 0.12);
  color: var(--wg-warning);
  border-color: rgba(212, 134, 24, 0.18);
}

.status-tag.error {
  background: rgba(221, 81, 117, 0.12);
  color: var(--wg-danger);
  border-color: rgba(221, 81, 117, 0.18);
}

@media (prefers-color-scheme: dark) {
  :root {
    --wg-bg: #171326;
    --wg-bg-soft: #1e1930;
    --wg-card: #241f38;
    --wg-card-muted: #2a2440;
    --wg-text: #f2efff;
    --wg-subtext: #b8add6;
    --wg-border: #3a3356;
    --wg-shadow: 0 14rpx 34rpx rgba(0, 0, 0, 0.28);
    --wg-shadow-soft: 0 8rpx 20rpx rgba(0, 0, 0, 0.2);
  }
}

@media (prefers-reduced-motion: reduce) {
  button,
  input,
  textarea,
  [class$='-item'],
  [class*='-item '] {
    transition: none !important;
  }
}
</style>
