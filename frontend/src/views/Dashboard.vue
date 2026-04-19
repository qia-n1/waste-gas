<template>
  <div class="dashboard-container">
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card>
          <h3>当前 VOCs</h3>
          <p>{{ currentVOCs }} mg/m³</p>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <h3>6 小时预测峰值</h3>
          <p>{{ peakForecast }} mg/m³</p>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <h3>活动告警</h3>
          <p>{{ activeAlerts }} 条</p>
        </el-card>
      </el-col>
    </el-row>
    <el-row>
      <el-card>
        <v-chart :options="chartOptions" style="height: 400px;" />
      </el-card>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import VChart from 'vue-echarts';
import { dashboardMockData } from '@/mock/dashboardMock';

const currentVOCs = ref(0);
const peakForecast = ref(0);
const activeAlerts = ref(0);
const chartOptions = ref({});

onMounted(async () => {
  try {
    // 使用模拟数据代替后端 API 数据
    const data = dashboardMockData;
    currentVOCs.value = data.actual_series[data.actual_series.length - 1].vocs;
    peakForecast.value = data.forecast_series[0].vocs;
    activeAlerts.value = 1; // 模拟告警数量

    chartOptions.value = {
      xAxis: {
        type: 'category',
        data: data.actual_series.map(item => item.time)
      },
      yAxis: {
        type: 'value'
      },
      series: [
        {
          name: '实际值',
          type: 'line',
          data: data.actual_series.map(item => item.vocs)
        },
        {
          name: '预测值',
          type: 'line',
          data: data.forecast_series.map(item => item.vocs)
        }
      ]
    };
  } catch (error) {
    console.error('获取数据失败', error);
  }
});
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
}
</style>