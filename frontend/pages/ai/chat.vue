<template>
  <view class="ai-chat">
    <view class="page-header">
      <text class="page-title">AI 对话</text>
      <text class="page-subtitle">智能问答 · 告警辅助</text>
    </view>

    <scroll-view
      class="chat-list"
      scroll-y
      :scroll-top="scrollTop"
      :scroll-with-animation="true"
    >
      <view v-for="msg in messages" :key="msg.id" class="msg-row" :class="msg.role">
        <view class="bubble" :class="msg.role">
          <text class="bubble-text">{{ msg.text }}</text>
        </view>
      </view>
      <view class="chat-list-bottom"></view>
    </scroll-view>

    <view class="composer">
      <view class="composer-inner">
        <input
          class="composer-input"
          :value="input"
          @input="onInput"
          confirm-type="send"
          @confirm="send"
          placeholder="输入问题，例如：为什么 VOCs 会超标？"
          placeholder-style="color: var(--text-desc);"
        />
        <button class="composer-send btn-primary" :disabled="!input.trim()" @click="send">
          发送
        </button>
      </view>
      <view class="safe-bottom"></view>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      input: '',
      scrollTop: 0,
      messages: [
        { id: 1, role: 'ai', text: '你好，我是你的废气监测助手。你可以问我：告警原因、处置建议、设备排查步骤等。' },
        { id: 2, role: 'user', text: '帮我看一下 VOCs 超标可能的原因？' },
        { id: 3, role: 'ai', text: '常见原因包括：活性炭饱和/失效、吸附风量不足、密封不良泄漏、工况波动、传感器漂移。你想按“设备/工艺/传感器”哪个方向先排查？' }
      ],
      nextId: 4
    };
  },
  methods: {
    onInput(e) {
      const v = (e && e.detail && e.detail.value !== undefined)
        ? e.detail.value
        : (e && e.target ? e.target.value : '');
      this.input = v;
    },
    send() {
      const text = (this.input || '').trim();
      if (!text) return;

      this.messages.push({ id: this.nextId++, role: 'user', text });
      this.input = '';

      // 模拟 AI 回复
      setTimeout(() => {
        this.messages.push({
          id: this.nextId++,
          role: 'ai',
          text: '我已收到。你可以补充：告警点位/持续时长/当前温湿度/是否近期更换耗材，我会给更具体的排查与处置建议。'
        });
        this.$nextTick(() => this.bumpScroll());
      }, 250);

      this.$nextTick(() => this.bumpScroll());
    },
    bumpScroll() {
      // 简单触发滚动到底部：让 scrollTop 递增即可
      this.scrollTop += 9999;
    }
  }
};
</script>

<style>
.ai-chat {
  min-height: 100vh;
  background:
    radial-gradient(900rpx 520rpx at 12% 0%, rgba(123, 97, 255, 0.14) 0%, rgba(123, 97, 255, 0) 62%),
    linear-gradient(180deg, #f7f4ff 0%, #ffffff 54%, #ffffff 100%);
  display: flex;
  flex-direction: column;
}

.page-header {
  padding: 24rpx 24rpx 12rpx;
}

.page-title {
  font-size: 32rpx;
  font-weight: 800;
  color: var(--text-main);
  display: block;
}

.page-subtitle {
  margin-top: 8rpx;
  font-size: 20rpx;
  color: var(--text-second);
  display: block;
}

.chat-list {
  flex: 1;
  padding: 12rpx 24rpx 0;
}

.chat-list-bottom {
  height: 24rpx;
}

.msg-row {
  display: flex;
  margin-bottom: 16rpx;
}

.msg-row.ai {
  justify-content: flex-start;
}

.msg-row.user {
  justify-content: flex-end;
}

.bubble {
  max-width: 78%;
  padding: 16rpx 18rpx;
  border-radius: 16rpx;
  box-shadow: var(--shadow-2);
}

.bubble.ai {
  background-color: rgba(255, 255, 255, 0.95);
  color: var(--text-main);
  border-top-left-radius: 8rpx;
  border: 1rpx solid rgba(123, 97, 255, 0.1);
}

.bubble.user {
  background-color: var(--primary-ultra-light);
  color: var(--text-main);
  border-top-right-radius: 8rpx;
}

.bubble-text {
  font-size: 20rpx;
  line-height: 1.5;
  word-break: break-all;
}

.composer {
  padding: 12rpx 24rpx 0;
  background: rgba(255, 255, 255, 0.86);
  border-top: 1rpx solid var(--primary-ultra-light);
}

.composer-inner {
  display: flex;
  gap: 12rpx;
  align-items: center;
  padding: 12rpx;
  background-color: #FFFFFF;
  border-radius: 24rpx;
  box-shadow: var(--shadow-2);
}

.composer-input {
  flex: 1;
  height: 72rpx;
  padding: 0 16rpx;
  border-radius: 16rpx;
  background-color: #FFFFFF;
  border: 1rpx solid #E5E7EB;
  font-size: 20rpx;
}

.composer-send {
  height: 72rpx;
  padding: 0 22rpx;
  border-radius: 18rpx;
  font-size: 20rpx;
  min-width: 120rpx;
}

.safe-bottom {
  height: env(safe-area-inset-bottom);
}
</style>

