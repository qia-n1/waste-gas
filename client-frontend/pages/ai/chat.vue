<template>
  <view class="ai-page">
    <view class="ai-hero">
      <view>
        <text class="hero-kicker">AI ASSISTANT</text>
        <text class="page-title">AI 多轮对话助手</text>
        <text class="page-subtitle">支持原因分析、处置建议、历史相似案例和 SOP 查询。</text>
      </view>
      <text class="hero-chip">{{ history.length }} 条</text>
    </view>

    <view class="chat-card">
      <scroll-view scroll-y class="chat-list">
        <view v-for="(item, index) in history" :key="index" class="chat-item" :class="item.role">
          <text class="chat-role">{{ item.role === 'assistant' ? 'AI' : '我' }}</text>
          <text class="chat-content">{{ item.content }}</text>
          <text class="chat-time">{{ item.createdAt || '刚刚' }}</text>
        </view>
      </scroll-view>
      <textarea v-model="question" class="chat-input" placeholder="请输入告警原因分析、SOP 或历史案例查询问题"></textarea>
      <view class="action-row">
        <button class="secondary-btn" @click="exportDialog">导出记录</button>
        <button class="primary-btn" @click="sendQuestion">发送</button>
      </view>
    </view>

    <view v-if="reply.answer" class="result-card">
      <text class="section-title">AI 回复</text>
      <text class="result-text">{{ reply.answer }}</text>
      <view class="tag-block">
        <text class="block-title">相似案例</text>
        <text v-for="(item, index) in reply.similarCases" :key="index" class="tag-item">• {{ item }}</text>
      </view>
      <view class="tag-block">
        <text class="block-title">处置 SOP</text>
        <text v-for="(item, index) in reply.sop" :key="index" class="tag-item">{{ index + 1 }}. {{ item }}</text>
      </view>
    </view>
  </view>
</template>

<script>
import { request } from '../../utils/api';

export default {
  data() {
    return {
      sessionId: 'default',
      history: [],
      question: '',
      reply: { answer: '', similarCases: [], sop: [] }
    };
  },
  onShow() {
    this.loadHistory();
  },
  methods: {
    async loadHistory() {
      try {
        const res = await request({ url: `/rag/history?sessionId=${this.sessionId}` });
        if (res?.code === 200) this.history = res.data;
      } catch (error) {
        uni.showToast({ title: '历史记录加载失败', icon: 'none' });
      }
    },
    async sendQuestion() {
      if (!this.question) return uni.showToast({ title: '请输入问题', icon: 'none' });
      try {
        const res = await request({ url: '/rag/diagnose', method: 'POST', data: { question: this.question, sessionId: this.sessionId } });
        if (res?.code === 200) {
          this.reply = res.data;
          await this.loadHistory();
          this.question = '';
        }
      } catch (error) {
        uni.showToast({ title: 'AI 请求失败', icon: 'none' });
      }
    },
    async exportDialog() {
      try {
        const res = await request({ url: `/rag/export?sessionId=${this.sessionId}` });
        if (res?.code === 200) uni.showModal({ title: '导出内容', content: res.data.content.slice(0, 200) + '...', showCancel: false });
      } catch (error) {
        uni.showToast({ title: '导出失败', icon: 'none' });
      }
    }
  }
};
</script>

<style>
.ai-page { min-height: 100vh; padding: 24rpx 24rpx calc(36rpx + env(safe-area-inset-bottom)); background: linear-gradient(180deg, #f7f3ff 0%, #fcfbff 52%, #ffffff 100%); }
.ai-hero,.chat-card,.result-card { margin-bottom: 22rpx; padding: 26rpx; border-radius: 28rpx; background: #fff; box-shadow: 0 16rpx 36rpx rgba(49,30,109,.06); }
.ai-hero { display:flex; justify-content:space-between; align-items:flex-end; gap:16rpx; }
.hero-kicker { display:inline-block; font-size:18rpx; color:#7b61ff; letter-spacing:2rpx; font-weight:700; }
.page-title { display:block; margin-top:14rpx; font-size:42rpx; font-weight:800; color:#2b2156; }
.page-subtitle { display:block; margin-top:10rpx; font-size:21rpx; line-height:1.6; color:#8378a1; }
.hero-chip { padding:12rpx 18rpx; border-radius:999rpx; background:#efe9ff; color:#7b61ff; font-size:21rpx; font-weight:700; }
.chat-list { max-height: 520rpx; }
.chat-item { margin-bottom: 16rpx; padding: 18rpx; border-radius: 20rpx; background:#faf8ff; }
.chat-item.assistant { background:#f2ecff; }
.chat-role,.chat-time { display:block; font-size:18rpx; color:#8f84ab; }
.chat-content { display:block; margin-top:8rpx; font-size:21rpx; line-height:1.7; color:#2d2454; }
.chat-input { width:100%; min-height:160rpx; margin-top:12rpx; padding:18rpx 20rpx; border-radius:20rpx; background:#faf8ff; font-size:21rpx; }
.action-row { display:flex; gap:14rpx; margin-top:16rpx; }
.primary-btn,.secondary-btn { flex:1; height:92rpx; border-radius:22rpx; font-size:22rpx; font-weight:700; }
.primary-btn { background:linear-gradient(135deg,#7b61ff 0%,#947dff 100%); color:#fff; }
.secondary-btn { background:#fff; color:#7b61ff; border:2rpx solid #e8e0ff; }
.primary-btn::after,.secondary-btn::after { border:none; }
.section-title,.block-title { display:block; font-size:28rpx; font-weight:800; color:#2d2454; }
.result-text,.tag-item { display:block; margin-top:12rpx; font-size:21rpx; line-height:1.7; color:#6f6686; }
.tag-block { margin-top:16rpx; }
</style>
