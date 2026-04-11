<template>
  <div class="alert-details-container">
    <el-card v-if="alertDetails" class="box-card">
      <h3>告警详情</h3>
      <p><strong>告警 ID:</strong> {{ alertDetails.alert_id }}</p>
      <p><strong>触发时间:</strong> {{ alertDetails.trigger_time }}</p>
      <p><strong>级别:</strong> {{ alertDetails.level }}</p>
      <p><strong>当前 VOCs:</strong> {{ alertDetails.current_vocs }} mg/m³</p>
      <p><strong>预测峰值:</strong> {{ alertDetails.peak_forecast }} mg/m³</p>
      <p><strong>诊断:</strong> {{ alertDetails.diagnosis }}</p>
      <h4>特征贡献:</h4>
      <el-table :data="alertDetails.feature_contributions" style="width: 100%">
        <el-table-column prop="feature" label="特征" />
        <el-table-column prop="label" label="描述" />
        <el-table-column prop="delta" label="变化" />
        <el-table-column prop="weight" label="权重" />
      </el-table>
      <h4>建议:</h4>
      <ul>
        <li v-for="(suggestion, index) in alertDetails.suggestions" :key="index">
          {{ suggestion }}
        </li>
      </ul>
    </el-card>
    <el-empty v-else description="未找到告警详情" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';
import { alertDetailsMockData } from '@/mock/alertsMock';

const route = useRoute();
const alertDetails = ref(null);

const fetchAlertDetails = async () => {
  const alertId = route.params.id;
  try {
    const response = await axios.get(`/api/v1/alerts/${alertId}/diagnosis`);
    alertDetails.value = response.data.data;
  } catch (error) {
    console.error('获取告警详情失败', error);
  }
};

onMounted(() => {
  fetchAlertDetails();
  // 使用模拟数据代替后端 API 数据
  alertDetails.value = alertDetailsMockData;
});
</script>

<style scoped>
.alert-details-container {
  padding: 20px;
}
</style>