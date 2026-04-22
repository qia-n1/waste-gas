<script setup lang="ts">
import { reactive } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";

import { useAuthStore } from "@/stores/auth";

const authStore = useAuthStore();
const router = useRouter();

const form = reactive({
  username: "admin",
  password: "admin123456",
});

const submit = async () => {
  try {
    await authStore.login(form.username, form.password);
    ElMessage.success("登录成功");
    await router.push("/");
  } catch (error) {
    console.error(error);
    ElMessage.error("登录失败，请检查用户名和密码");
  }
};
</script>

<template>
  <div class="login-page">
    <section class="login-hero">
      <p class="hero-tag">VOCs Forecasting Dashboard</p>
      <h1>气盾卫士-多源化工废气智能治理系统</h1>
      <p class="hero-desc">
        面向园区管理者的监测、预测、告警与决策支持平台。当前版本优先打通实时概览与大屏监控链路。
      </p>
      <div class="hero-grid">
        <div>
          <strong>24</strong>
          <span>预测点位</span>
        </div>
        <div>
          <strong>26</strong>
          <span>重点参数</span>
        </div>
        <div>
          <strong>6h</strong>
          <span>预测窗口</span>
        </div>
      </div>
    </section>

    <section class="login-panel panel-card">
      <div class="panel-head">
        <p>管理员登录</p>
        <span>使用管理端账户进入大屏</span>
      </div>

      <el-form label-position="top" @submit.prevent="submit">
        <el-form-item label="用户名">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            placeholder="请输入密码"
            @keyup.enter="submit"
          />
        </el-form-item>
        <el-button
          class="submit-button"
          type="primary"
          :loading="authStore.loading"
          @click="submit"
        >
          进入管理大屏
        </el-button>
      </el-form>
    </section>
  </div>
</template>

<style scoped>
.login-page {
  width: 100%;
  height: 100%;
  padding: 48px;
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(380px, 460px);
  gap: 28px;
}

.login-hero,
.login-panel {
  position: relative;
  overflow: hidden;
}

.login-hero {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 42px;
  border-radius: 32px;
  background:
    radial-gradient(circle at top left, rgba(83, 209, 255, 0.18), transparent 36%),
    linear-gradient(145deg, rgba(11, 28, 57, 0.96), rgba(6, 12, 28, 0.92));
  border: 1px solid rgba(83, 209, 255, 0.2);
  box-shadow: var(--shadow-glow);
}

.hero-tag {
  color: var(--accent-cyan);
  font-size: 12px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
}

.login-hero h1 {
  margin: 12px 0 18px;
  font-size: 60px;
  line-height: 1.04;
}

.hero-desc {
  max-width: 520px;
  color: var(--text-secondary);
  font-size: 17px;
  line-height: 1.8;
}

.hero-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-top: 32px;
}

.hero-grid div {
  padding: 22px 18px;
  border-radius: 20px;
  background: rgba(7, 15, 31, 0.46);
  border: 1px solid rgba(95, 122, 191, 0.16);
}

.hero-grid strong {
  display: block;
  margin-bottom: 8px;
  font-size: 30px;
}

.hero-grid span {
  color: var(--text-secondary);
}

.login-panel {
  align-self: center;
  padding: 28px;
}

.panel-head {
  margin-bottom: 18px;
}

.panel-head p {
  margin: 0 0 4px;
  font-size: 26px;
  font-weight: 700;
}

.panel-head span {
  color: var(--text-secondary);
}

.submit-button {
  width: 100%;
  height: 48px;
  margin-top: 6px;
  background: linear-gradient(135deg, var(--accent-blue), var(--accent-cyan));
  border: none;
}

@media (max-width: 1080px) {
  .login-page {
    grid-template-columns: 1fr;
    padding: 20px;
  }

  .login-hero h1 {
    font-size: 42px;
  }
}
</style>
