<template>
  <div class="alerts-container">
    <el-table :data="alerts" style="width: 100%" :loading="loading">
      <el-table-column prop="alert_id" label="告警 ID" width="200" />
      <el-table-column prop="trigger_time" label="触发时间" width="180" />
      <el-table-column prop="level" label="级别" width="100" />
      <el-table-column prop="status" label="状态" width="120" />
      <el-table-column prop="current_vocs" label="当前 VOCs" width="120" />
      <el-table-column prop="peak_forecast" label="预测峰值" width="120" />
      <el-table-column label="操作" width="150">
        <template #default="scope">
          <el-button type="primary" size="small" @click="viewDetails(scope.row.alert_id)">查看详情</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination
      v-model:current-page="currentPage"
      :page-size="pageSize"
      :total="total"
      @current-change="fetchAlerts"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import { alertsMockData } from '@/mock/alertsMock';

const router = useRouter();
const alerts = ref([]);
const loading = ref(false);
const currentPage = ref(1);
const pageSize = 10;
const total = ref(0);

const fetchAlerts = async (page = 1) => {
  loading.value = true;
  try {
    const response = await axios.get('/api/v1/alerts/active', {
      params: {
        limit: pageSize,
        offset: (page - 1) * pageSize
      }
    });
    alerts.value = response.data.data;
    total.value = response.data.total || 0; // Mock total count
  } catch (error) {
    console.error('获取告警列表失败', error);
  } finally {
    loading.value = false;
  }
};

const viewDetails = (alertId) => {
  router.push(`/alerts/${alertId}`);
};

onMounted(() => {
  fetchAlerts();
  // 使用模拟数据代替后端 API 数据
  alerts.value = alertsMockData;
  total.value = alertsMockData.length; // 模拟总数
  loading.value = false;
});
</script>

<style scoped>
.alerts-container {
  padding: 20px;
}
</style>