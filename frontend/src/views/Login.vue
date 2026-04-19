<template>
  <div class="login-container">
    <el-form :model="loginForm" @submit.prevent="onSubmit">
      <el-form-item label="用户名">
        <el-input v-model="loginForm.username" placeholder="请输入用户名" />
      </el-form-item>
      <el-form-item label="密码">
        <el-input v-model="loginForm.password" type="password" placeholder="请输入密码" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="onSubmit">登录</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { reactive } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

const router = useRouter();
const loginForm = reactive({
  username: '',
  password: ''
});

const onSubmit = async () => {
  try {
    const response = await axios.post('/api/v1/auth/login', loginForm);
    const { access_token } = response.data;
    localStorage.setItem('token', access_token);
    router.push('/dashboard');
  } catch (error) {
    console.error('登录失败', error);
  }
};
</script>

<style scoped>
.login-container {
  max-width: 400px;
  margin: 100px auto;
  padding: 20px;
  border: 1px solid #ccc;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
</style>