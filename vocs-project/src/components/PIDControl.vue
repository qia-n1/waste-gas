<template>
  <div class="vocs-monitor-container">
    <div class="header-section">
      <div class="header-content">
        <h1 class="main-title">VOCs智能管控与治理系统</h1>
        <div class="header-status">
          <div class="status-indicator online">
            <span class="status-dot"></span>
            <span class="status-text">系统运行中</span>
          </div>
        </div>
      </div>
    </div>

    <div class="main-layout">
      <div class="left-panel">
        <div class="panel-card monitor-card">
          <div class="card-header">
            <div class="card-title">
              <span>实时数据监控</span>
            </div>
            <div class="card-actions">
              <button class="action-btn" @click="toggleAllSections" title="展开/折叠全部">
                <span>{{ allSectionsExpanded ? '折叠全部' : '展开全部' }}</span>
              </button>
            </div>
          </div>

          <div class="data-section">
            <div class="section-header weather" @click="toggleSection('weather')">
              <span class="section-icon">{{ sections.weather ? '▼' : '▶' }}</span>
              <span class="section-title">气象数据</span>
              <span class="section-badge">3项</span>
            </div>
            <transition name="slide">
              <div v-show="sections.weather" class="data-grid">
                <div class="data-item">
                  <div class="data-content">
                    <span class="data-label">环境温度</span>
                    <span class="data-value">{{ latestSensorData.ambient_temp?.toFixed(1) || '--' }} <small>°C</small></span>
                  </div>
                </div>
                <div class="data-item">
                  <div class="data-content">
                    <span class="data-label">环境湿度</span>
                    <span class="data-value">{{ latestSensorData.ambient_humidity?.toFixed(1) || '--' }} <small>%</small></span>
                  </div>
                </div>
                <div class="data-item">
                  <div class="data-content">
                    <span class="data-label">环境压力</span>
                    <span class="data-value">{{ ((latestSensorData.ambient_pressure || 0) / 1000).toFixed(1) }} <small>kPa</small></span>
                  </div>
                </div>
              </div>
            </transition>
          </div>

          <div class="data-section">
            <div class="section-header equipment">
              <span class="section-title">设备运行参数</span>
            </div>

            <div class="data-subsection">
              <div class="subsection-header" @click="toggleSection('coating')">
                <span class="section-icon">{{ sections.coating ? '▼' : '▶' }}</span>
                <span class="subsection-title">涂布废气参数</span>
                <span class="section-badge">4项</span>
              </div>
              <transition name="slide">
                <div v-show="sections.coating" class="data-grid compact">
                  <div class="data-item small">
                    <span class="data-label">风量</span>
                    <span class="data-value">{{ ((latestSensorData.coating_flow || 0) / 1000).toFixed(1) }}k</span>
                  </div>
                  <div class="data-item small">
                    <span class="data-label">浓度</span>
                    <span class="data-value">{{ latestSensorData.coating_conc?.toFixed(2) || '--' }}</span>
                  </div>
                  <div class="data-item small">
                    <span class="data-label">温度</span>
                    <span class="data-value">{{ latestSensorData.coating_temp?.toFixed(1) || '--' }}</span>
                  </div>
                  <div class="data-item small">
                    <span class="data-label">压力</span>
                    <span class="data-value">{{ ((latestSensorData.coating_pressure || 0) / 1000).toFixed(1) }}</span>
                  </div>
                </div>
              </transition>
            </div>

            <div class="data-subsection">
              <div class="subsection-header" @click="toggleSection('rotor')">
                <span class="section-icon">{{ sections.rotor ? '▼' : '▶' }}</span>
                <span class="subsection-title">沸石转轮参数</span>
                <span class="section-badge">6项</span>
              </div>
              <transition name="slide">
                <div v-show="sections.rotor" class="data-grid compact">
                  <div class="data-item small">
                    <span class="data-label">转速</span>
                    <span class="data-value">{{ latestSensorData.rotor_speed?.toFixed(2) || '--' }}</span>
                  </div>
                  <div class="data-item small">
                    <span class="data-label">吸附功率</span>
                    <span class="data-value">{{ latestSensorData.adsorption_fan_power?.toFixed(1) || '--' }}</span>
                  </div>
                  <div class="data-item small">
                    <span class="data-label">脱附功率</span>
                    <span class="data-value">{{ latestSensorData.desorption_fan_power?.toFixed(1) || '--' }}</span>
                  </div>
                  <div class="data-item small">
                    <span class="data-label">进口温度</span>
                    <span class="data-value">{{ latestSensorData.rotor_inlet_temp?.toFixed(1) || '--' }}</span>
                  </div>
                  <div class="data-item small">
                    <span class="data-label">进口湿度</span>
                    <span class="data-value">{{ latestSensorData.rotor_inlet_humid?.toFixed(1) || '--' }}</span>
                  </div>
                  <div class="data-item small">
                    <span class="data-label">脱附温度</span>
                    <span class="data-value">{{ latestSensorData.desorption_temp?.toFixed(1) || '--' }}</span>
                  </div>
                </div>
              </transition>
            </div>

            <div class="data-subsection">
              <div class="subsection-header" @click="toggleSection('concentrated')">
                <span class="section-icon">{{ sections.concentrated ? '▼' : '▶' }}</span>
                <span class="subsection-title">浓缩废气参数</span>
                <span class="section-badge">4项</span>
              </div>
              <transition name="slide">
                <div v-show="sections.concentrated" class="data-grid compact">
                  <div class="data-item small">
                    <span class="data-label">风量</span>
                    <span class="data-value">{{ ((latestSensorData.concentrated_flow || 0) / 1000).toFixed(1) }}k</span>
                  </div>
                  <div class="data-item small">
                    <span class="data-label">浓度</span>
                    <span class="data-value">{{ latestSensorData.concentrated_conc?.toFixed(2) || '--' }}</span>
                  </div>
                  <div class="data-item small">
                    <span class="data-label">温度</span>
                    <span class="data-value">{{ latestSensorData.concentrated_temp?.toFixed(1) || '--' }}</span>
                  </div>
                  <div class="data-item small">
                    <span class="data-label">压力</span>
                    <span class="data-value">{{ ((latestSensorData.concentrated_pressure || 0) / 1000).toFixed(1) }}</span>
                  </div>
                </div>
              </transition>
            </div>

            <div class="data-subsection">
              <div class="subsection-header" @click="toggleSection('rto_in')">
                <span class="section-icon">{{ sections.rto_in ? '▼' : '▶' }}</span>
                <span class="subsection-title">RTO进口参数</span>
                <span class="section-badge">4项</span>
              </div>
              <transition name="slide">
                <div v-show="sections.rto_in" class="data-grid compact">
                  <div class="data-item small">
                    <span class="data-label">风量</span>
                    <span class="data-value">{{ ((latestSensorData.rto_in_flow || 0) / 1000).toFixed(1) }}k</span>
                  </div>
                  <div class="data-item small">
                    <span class="data-label">浓度</span>
                    <span class="data-value">{{ latestSensorData.rto_in_conc?.toFixed(2) || '--' }}</span>
                  </div>
                  <div class="data-item small">
                    <span class="data-label">温度</span>
                    <span class="data-value">{{ latestSensorData.rto_in_temp?.toFixed(1) || '--' }}</span>
                  </div>
                  <div class="data-item small">
                    <span class="data-label">压力</span>
                    <span class="data-value">{{ ((latestSensorData.rto_in_pressure || 0) / 1000).toFixed(1) }}</span>
                  </div>
                </div>
              </transition>
            </div>

            <div class="data-subsection">
              <div class="subsection-header" @click="toggleSection('rto_burn')">
                <span class="section-icon">{{ sections.rto_burn ? '▼' : '▶' }}</span>
                <span class="subsection-title">RTO燃烧参数</span>
                <span class="section-badge">2项</span>
              </div>
              <transition name="slide">
                <div v-show="sections.rto_burn" class="data-grid compact">
                  <div class="data-item small">
                    <span class="data-label">天然气流量</span>
                    <span class="data-value">{{ latestSensorData.burner_gas_flow?.toFixed(2) || '--' }}</span>
                  </div>
                  <div class="data-item small">
                    <span class="data-label">燃烧温度</span>
                    <span class="data-value">{{ latestSensorData.combustion_temp?.toFixed(1) || '--' }}</span>
                  </div>
                </div>
              </transition>
            </div>

            <div class="data-subsection">
              <div class="subsection-header" @click="toggleSection('rto_out')">
                <span class="section-icon">{{ sections.rto_out ? '▼' : '▶' }}</span>
                <span class="subsection-title">RTO出口参数</span>
                <span class="section-badge">2项</span>
              </div>
              <transition name="slide">
                <div v-show="sections.rto_out" class="data-grid compact">
                  <div class="data-item small">
                    <span class="data-label">出口浓度</span>
                    <span class="data-value">{{ latestSensorData.rto_out_conc?.toFixed(2) || '--' }}</span>
                  </div>
                  <div class="data-item small">
                    <span class="data-label">出口温度</span>
                    <span class="data-value">{{ latestSensorData.rto_out_temp?.toFixed(1) || '--' }}</span>
                  </div>
                </div>
              </transition>
            </div>
          </div>
        </div>
      </div>

      <div class="center-panel">
        <div class="panel-card chart-card">
          <div class="card-header">
            <div class="card-title">
              <span>VOCs浓度预测</span>
            </div>
            <div class="card-meta">
              <span class="meta-tag">未来6小时</span>
            </div>
          </div>

          <div class="chart-container">
            <canvas id="predictionChart"></canvas>
          </div>

          <div class="prediction-stats">
            <div class="stat-card current">
              <div class="stat-content">
                <span class="stat-label">当前值</span>
                <span class="stat-value">{{ latestSensorData.rto_out_conc?.toFixed(2) || '--' }}</span>
                <span class="stat-unit">mg/m³</span>
              </div>
            </div>
            <div class="stat-card max">
              <div class="stat-content">
                <span class="stat-label">最大值</span>
                <span class="stat-value" :class="getVOCsClass(maxPrediction)">{{ maxPrediction?.toFixed(2) || '--' }}</span>
                <span class="stat-unit">mg/m³</span>
              </div>
            </div>
            <div class="stat-card avg">
              <div class="stat-content">
                <span class="stat-label">平均值</span>
                <span class="stat-value">{{ avgPrediction?.toFixed(2) || '--' }}</span>
                <span class="stat-unit">mg/m³</span>
              </div>
            </div>
            <div class="stat-card conf">
              <div class="stat-content">
                <span class="stat-label">置信度</span>
                <span class="stat-value">{{ (latestPrediction?.confidence * 100 || 0).toFixed(1) }}</span>
                <span class="stat-unit">%</span>
              </div>
            </div>
          </div>
        </div>

        <div class="panel-card combined-card">
          <div class="card-header">
            <div class="tabs">
              <button
                :class="['tab-btn', { active: activeTab === 'history' }]"
                @click="activeTab = 'history'"
              >
                <span>预测历史</span>
              </button>
              <button
                :class="['tab-btn', { active: activeTab === 'alert' }]"
                @click="activeTab = 'alert'"
              >
                <span>预警中心</span>
                <span class="alert-count-badge" :class="getAlertCountClass()">{{ unacknowledgedCount }}</span>
              </button>
            </div>
          </div>

          <!-- 预测历史内容 -->
          <div v-show="activeTab === 'history'" class="tab-content">
            <div class="history-list">
              <div class="history-item" v-for="(pred, index) in predictionHistory.slice(0, 5)" :key="index">
                <div class="history-header">
                  <div class="history-time">{{ formatHistoryTime(pred.timestamp) }}</div>
                  <div class="history-badges">
                    <span class="history-badge alert" v-if="pred.alert_triggered">预警</span>
                  </div>
                </div>
                <div class="history-metrics">
                  <div class="metric">
                    <span class="metric-label">最大值</span>
                    <span class="metric-value">{{ getMaxValue(pred).toFixed(2) }}</span>
                  </div>
                  <div class="metric">
                    <span class="metric-label">平均值</span>
                    <span class="metric-value">{{ getAvgValue(pred).toFixed(2) }}</span>
                  </div>
                  <div class="metric">
                    <span class="metric-label">置信度</span>
                    <span class="metric-value">{{ (pred.confidence * 100).toFixed(1) }}%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 预警中心内容 -->
          <div v-show="activeTab === 'alert'" class="tab-content">
            <div class="alert-list-wrapper">
              <div class="alert-list" v-if="alerts.length > 0">
                <div
                  v-for="alert in alerts.slice(0, 10)"
                  :key="alert.alert_id"
                  :class="['alert-item', `alert-${alert.level}`, { acknowledged: alert.acknowledged }]"
                >
                  <div class="alert-indicator" :class="`indicator-${alert.level}`"></div>
                  <div class="alert-content">
                    <div class="alert-message">{{ alert.message }}</div>
                    <div class="alert-details">
                      <span class="alert-detail">当前: {{ alert.value?.toFixed(2) }} mg/m³</span>
                      <span class="alert-detail">阈值: {{ alert.threshold?.toFixed(2) }} mg/m³</span>
                    </div>
                    <div class="alert-time">{{ formatAlertTime(alert.timestamp) }}</div>
                  </div>
                  <button
                    v-if="!alert.acknowledged"
                    @click="acknowledgeAlert(alert.alert_id)"
                    class="ack-btn"
                  >
                    确认
                  </button>
                </div>
              </div>

              <!-- 无预警提示 -->
              <div class="no-alerts" v-else>
                <div class="no-alerts-icon">✓</div>
                <div class="no-alerts-text">暂无预警信息</div>
                <div class="no-alerts-hint">系统运行正常</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧面板现在为空，可以移除或用于其他功能 -->
      <div class="right-panel" style="display: none;">
      </div>
    </div>

    <!-- 通知提示 -->
    <transition name="notification">
      <div v-if="notification.show" class="notification" :class="notification.type">
        <span class="notification-indicator"></span>
        {{ notification.message }}
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue';
import axios from 'axios';
import Chart from 'chart.js/auto';

const systemStatus = ref({
  model_loaded: false,
  data_collection_interval_minutes: 15,
  prediction_interval_minutes: 15,
  prediction_horizon_minutes: 360,
  alert_threshold_mg_m3: 80,
  total_data_received: 0,
  total_predictions: 0,
  total_alerts: 0,
  buffer_size: 0,
  memory_buffer_status: '0/48',
  system_phase: '初始化期'
});

const latestSensorData = ref({
  timestamp: null,
  ambient_temp: 0,
  ambient_humidity: 0,
  ambient_pressure: 0,
  coating_flow: 0,
  coating_conc: 0,
  coating_temp: 0,
  coating_pressure: 0,
  rotor_speed: 0,
  adsorption_fan_power: 0,
  desorption_fan_power: 0,
  rotor_inlet_temp: 0,
  rotor_inlet_humid: 0,
  desorption_temp: 0,
  concentrated_flow: 0,
  concentrated_conc: 0,
  concentrated_temp: 0,
  concentrated_pressure: 0,
  rto_in_flow: 0,
  rto_in_temp: 0,
  rto_in_pressure: 0,
  burner_gas_flow: 0,
  combustion_temp: 0,
  rto_in_conc: 0,
  rto_out_conc: 0,
  rto_out_temp: 0
});

const latestPrediction = ref(null);
const predictionHistory = ref([]);
const alerts = ref([]);
const unacknowledgedCount = ref(0);
let predictionChart = null;
let eventSource = null;

const notification = ref({
  show: false,
  type: 'success',
  message: ''
});

const latestUpdateTime = computed(() => {
  return latestSensorData.value.timestamp
    ? parseLocalTimestamp(latestSensorData.value.timestamp).toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      })
    : new Date().toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      });
});

const maxPrediction = computed(() => {
  if (!latestPrediction.value || !latestPrediction.value.predicted_values) return null;
  return Math.max(...latestPrediction.value.predicted_values);
});

const avgPrediction = computed(() => {
  if (!latestPrediction.value || !latestPrediction.value.predicted_values) return null;
  const values = latestPrediction.value.predicted_values;
  return values.reduce((a, b) => a + b, 0) / values.length;
});

const sections = ref({
  weather: true,
  coating: true,
  rotor: true,
  concentrated: true,
  rto_in: true,
  rto_burn: true,
  rto_out: true
});

const activeTab = ref('history');

const allSectionsExpanded = computed(() => {
  return Object.values(sections.value).every(v => v === true);
});

function toggleSection(sectionName) {
  sections.value[sectionName] = !sections.value[sectionName];
}

function toggleAllSections() {
  const shouldExpand = !allSectionsExpanded.value;
  Object.keys(sections.value).forEach(key => {
    sections.value[key] = shouldExpand;
  });
}
function getVOCsClass(value) {
  if (!value) return 'normal';
  if (value >= 100) return 'critical';
  if (value >= 80) return 'warning';
  return 'normal';
}

function getStatusClass(value) {
  if (!value) return 'status-normal';
  if (value >= 100) return 'status-critical';
  if (value >= 80) return 'status-warning';
  return 'status-normal';
}

function getStatusText(value) {
  if (!value) return '等待数据...';
  if (value >= 100) return '严重超标';
  if (value >= 80) return '超标预警';
  return '正常';
}

// 正确解析后端发送的时间戳
function parseLocalTimestamp(timestamp) {
  if (!timestamp) return new Date();

  // 后端发送的ISO格式没有时区信息，需要当作本地时间处理
  if (timestamp.includes('T') || timestamp.includes(' ')) {
    const isoStr = timestamp.replace(' ', 'T');
    // 解析各个部分（年、月、日、时、分、秒），支持带微秒的格式
    const matches = isoStr.match(/(\d{4})-(\d{2})-(\d{2})T?(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?/);
    if (matches) {
      const [, year, month, day, hour, minute, second] = matches;
      // 使用本地时间创建Date对象
      return new Date(parseInt(year), parseInt(month) - 1, parseInt(day), parseInt(hour), parseInt(minute), parseInt(second));
    }
  }

  return new Date(timestamp);
}

function formatAlertTime(timestamp) {
  const date = parseLocalTimestamp(timestamp);
  const now = new Date();
  const diff = now - date;
  const minutes = Math.floor(diff / 60000);

  if (minutes < 1) return '刚刚';
  if (minutes < 60) return `${minutes}分钟前`;
  return date.toLocaleString('zh-CN');
}

function formatHistoryTime(timestamp) {
  const date = parseLocalTimestamp(timestamp);

  // 显示完整的时间：年/月/日 时:分:秒
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  });
}

function getAlertCountClass() {
  if (unacknowledgedCount.value === 0) return 'count-none';
  if (unacknowledgedCount.value <= 2) return 'count-low';
  if (unacknowledgedCount.value <= 5) return 'count-medium';
  return 'count-high';
}

function getMaxValue(prediction) {
  if (!prediction.predicted_values) return 0;
  return Math.max(...prediction.predicted_values);
}

function getAvgValue(prediction) {
  if (!prediction.predicted_values || prediction.predicted_values.length === 0) return 0;
  const sum = prediction.predicted_values.reduce((a, b) => a + b, 0);
  return sum / prediction.predicted_values.length;
}

function showNotification(message, type = 'success') {
  notification.value = { show: true, type, message };
  setTimeout(() => {
    notification.value.show = false;
  }, 5000);
}

// ==================== API调用 ====================
async function fetchSystemStatus() {
  try {
    const response = await axios.get('http://127.0.0.1:8001/status');
    systemStatus.value = response.data;
  } catch (error) {
    console.error('获取系统状态失败:', error);
  }
}

async function fetchLatestSensorData() {
  try {
    const response = await axios.get('http://127.0.0.1:8001/sensor-data/latest');
    latestSensorData.value = response.data;
  } catch (error) {
    console.error('获取传感器数据失败:', error);
  }
}

async function fetchLatestPrediction() {
  try {
    const response = await axios.get('http://127.0.0.1:8001/predictions/latest');
    latestPrediction.value = response.data;

    if (response.data) {
      updatePredictionChart(response.data);

      // 检查是否重复（通过timestamp比较）
      const isDuplicate = predictionHistory.value.length > 0 &&
        predictionHistory.value[0].timestamp === response.data.timestamp;

      if (!isDuplicate) {
        predictionHistory.value.unshift(response.data);
        if (predictionHistory.value.length > 20) {
          predictionHistory.value.pop();
        }
      }

      if (response.data.alert_triggered) {
        showNotification(response.data.alert_message, 'warning');
      }
    }
  } catch (error) {
    console.error('获取预测结果失败:', error);
  }
}

async function fetchAlerts() {
  try {
    const response = await axios.get('http://127.0.0.1:8001/alerts');
    alerts.value = response.data;
    unacknowledgedCount.value = alerts.value.filter(a => !a.acknowledged).length;
  } catch (error) {
    console.error('获取预警信息失败:', error);
  }
}

async function acknowledgeAlert(alertId) {
  try {
    await axios.post(`http://127.0.0.1:8001/alerts/${alertId}/acknowledge`);
    await fetchAlerts();
    showNotification('预警已确认', 'success');
  } catch (error) {
    console.error('确认预警失败:', error);
    showNotification('确认预警失败', 'error');
  }
}


function initChart() {
  const ctx = document.getElementById('predictionChart');
  if (!ctx) return;

  predictionChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [
        {
          label: 'VOCs浓度预测',
          data: [],
          borderColor: '#FF6B6B',
          backgroundColor: 'rgba(255, 107, 107, 0.1)',
          borderWidth: 3,
          pointRadius: 4,
          pointBackgroundColor: '#FF6B6B',
          tension: 0.4
        },
        {
          label: '平均值',
          data: [],
          borderColor: '#34d399',
          borderWidth: 2,
          borderDash: [10, 5],
          pointRadius: 0,
          fill: false
        },
        {
          label: '最大值',
          data: [],
          borderColor: '#f87171',
          borderWidth: 1,
          borderDash: [3, 3],
          pointRadius: 0,
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          labels: {
            color: '#e6f1ff',
            font: { size: 12 }
          }
        },
        tooltip: {
          mode: 'index',
          intersect: false,
          callbacks: {
            label: (context) => {
              return `${context.dataset.label}: ${context.parsed.y.toFixed(2)} mg/m³`;
            }
          }
        }
      },
      scales: {
        y: {
          min: 0,
          max: 100,
          title: {
            display: true,
            text: 'VOCs浓度 (mg/m³)',
            color: '#e6f1ff'
          },
          grid: { color: 'rgba(255, 255, 255, 0.1)' },
          ticks: { color: '#e6f1ff' }
        },
        x: {
          title: {
            display: true,
            text: '时间',
            color: '#e6f1ff'
          },
          grid: { color: 'rgba(255, 255, 255, 0.1)' },
          ticks: {
            color: '#e6f1ff',
            maxTicksLimit: 12
          }
        }
      }
    }
  });
}

function updatePredictionChart(prediction) {
  if (!predictionChart || !prediction) return;

  // 获取实时数据的时间戳作为起始时间（使用正确的时区解析）
  const startTime = latestSensorData.value.timestamp
    ? parseLocalTimestamp(latestSensorData.value.timestamp)
    : new Date();

  const labels = [];
  const predictedData = [];

  // 预测结果为24个值（未来6小时，每15分钟一个点）
  const predictedValues = prediction.predicted_values || [];

  // 第一个点：当前实时值（rto_out_conc 为出口VOCs浓度）
  if (latestSensorData.value.rto_out_conc !== undefined) {
    labels.push(startTime.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }));
    predictedData.push(latestSensorData.value.rto_out_conc);
  }

  // 后面24个点：预测值
  for (let i = 0; i < predictedValues.length; i++) {
    // 从下一个15分钟开始（当前时间 + (i+1) * 15分钟）
    const time = new Date(startTime.getTime() + (i + 1) * 15 * 60000);

    // 显示时间标签
    labels.push(time.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }));

    // 使用对应的预测值
    predictedData.push(predictedValues[i]);
  }

  // 动态计算y轴范围
  const dataMin = Math.min(...predictedData);
  const dataMax = Math.max(...predictedData);
  const dataRange = dataMax - dataMin;

  // 添加边距,让曲线更清晰
  let yMin, yMax;

  if (dataRange < 1) {
    // 波动很小(小于1)时,自动缩小范围以显示细节
    const margin = 0.5; // 固定边距
    yMin = Math.max(0, dataMin - margin);
    yMax = dataMax + margin;
  } else {
    // 正常情况,添加10%的边距
    const margin = dataRange * 0.1;
    yMin = Math.max(0, dataMin - margin);
    yMax = dataMax + margin;
  }

  // 确保y轴范围至少有5个单位,避免过于放大
  if (yMax - yMin < 5) {
    const center = (yMin + yMax) / 2;
    yMin = center - 2.5;
    yMax = center + 2.5;
  }

  predictionChart.data.labels = labels;
  predictionChart.data.datasets[0].data = predictedData;

  // 添加平均值线（基于预测值的平均，不包含当前值）
  const avgValue = predictedValues.reduce((a, b) => a + b, 0) / predictedValues.length;
  const avgData = new Array(labels.length).fill(avgValue);
  predictionChart.data.datasets[1].data = avgData;

  // 添加最大值线（基于预测值的最大值，不包含当前值）
  const maxValue = Math.max(...predictedValues);
  const maxData = new Array(labels.length).fill(maxValue);
  predictionChart.data.datasets[2].data = maxData;

  // 动态更新y轴范围
  predictionChart.options.scales.y.min = yMin;
  predictionChart.options.scales.y.max = yMax;

  predictionChart.update('none');
}

// ==================== SSE连接 ====================
function connectSSE() {
  eventSource = new EventSource('http://127.0.0.1:8001/events');

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);

      if (data.type === 'connected') {
        showNotification('实时连接已建立', 'success');
        fetchLatestSensorData();
        fetchAlerts();
      } else if (data.type === 'sensor_data') {
        latestSensorData.value = data.data;
      } else if (data.type === 'prediction') {
        latestPrediction.value = data.data;
        updatePredictionChart(data.data);

        // 检查是否重复（通过timestamp比较）
        const isDuplicate = predictionHistory.value.length > 0 &&
          predictionHistory.value[0].timestamp === data.data.timestamp;

        if (!isDuplicate) {
          predictionHistory.value.unshift(data.data);
          if (predictionHistory.value.length > 20) {
            predictionHistory.value.pop();
          }
        }

        if (data.data.alert_triggered) {
          showNotification(data.data.alert_message, 'warning');
          fetchAlerts();
        }
      }
    } catch (error) {
      console.error('解析SSE消息失败:', error);
    }
  };

  eventSource.onerror = (error) => {
    console.error('SSE连接错误:', error);
  };
}

// ==================== 生命周期 ====================
onMounted(() => {
  
  initChart();
  fetchSystemStatus();
  fetchLatestSensorData();
  fetchLatestPrediction();
  fetchAlerts();
  connectSSE();

  const interval = setInterval(() => {
    fetchSystemStatus();
    fetchAlerts();
  }, 30000);

  onBeforeUnmount(() => {
    clearInterval(interval);
  });
});

onBeforeUnmount(() => {
  if (eventSource) {
    eventSource.close();
  }
  if (predictionChart) {
    predictionChart.destroy();
  }
});
</script>

<style scoped>
.vocs-monitor-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 50%, #0f1419 100%);
  padding: 16px 20px 20px;
  color: #e2e8f0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', sans-serif;
  max-width: 100vw;
  overflow-x: hidden;
}

.header-section {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px 28px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  border: 1px solid rgba(139, 92, 246, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  position: relative;
}

.main-title {
  font-size: 28px;
  font-weight: 700;
  margin: 0;
  background: linear-gradient(135deg, #a78bfa 0%, #818cf8 50%, #6366f1 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: -0.5px;
  text-align: center;
}

.header-status {
  position: absolute;
  right: 28px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: 20px;
  font-size: 13px;
  color: #22c55e;
  font-weight: 500;
}

.status-dot {
  width: 8px;
  height: 8px;
  background: #22c55e;
  border-radius: 50%;
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(1.1);
  }
}

.main-layout {
  display: grid;
  grid-template-columns: 42% minmax(0, 1fr);
  gap: 20px;
  align-items: start;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}
.panel-card {
  background: linear-gradient(145deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 0;
  border: 1px solid rgba(71, 85, 105, 0.3);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
  margin-bottom: 20px;
  overflow: hidden;
  transition: all 0.3s ease;
  max-width: 100%;
  box-sizing: border-box;
}

.panel-card:hover {
  border-color: rgba(139, 92, 246, 0.3);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 22px;
  background: linear-gradient(90deg, rgba(51, 65, 85, 0.5) 0%, rgba(30, 41, 59, 0.3) 100%);
  border-bottom: 1px solid rgba(71, 85, 105, 0.3);
}

.card-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
  color: #e2e8f0;
  letter-spacing: -0.3px;
}

.card-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 6px 12px;
  background: rgba(139, 92, 246, 0.1);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 8px;
  color: #a78bfa;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover {
  background: rgba(139, 92, 246, 0.2);
  border-color: rgba(139, 92, 246, 0.5);
  transform: translateY(-1px);
}

.card-meta {
  display: flex;
  gap: 8px;
}

.meta-tag {
  padding: 4px 10px;
  background: rgba(59, 130, 246, 0.15);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
  color: #60a5fa;
}

/* ==================== 左侧监控面板 ==================== */
.left-panel {
  width: 100%;
  max-width: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.monitor-card {
  height: calc(100vh - 140px);
  max-height: calc(100vh - 140px);
  overflow-y: auto;
  width: 100%;
}

.monitor-card::-webkit-scrollbar {
  width: 6px;
}

.monitor-card::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}

.monitor-card::-webkit-scrollbar-thumb {
  background: rgba(139, 92, 246, 0.3);
  border-radius: 3px;
}

.monitor-card::-webkit-scrollbar-thumb:hover {
  background: rgba(139, 92, 246, 0.5);
}

.data-section {
  padding: 16px 20px;
  border-bottom: 1px solid rgba(71, 85, 105, 0.2);
}

.data-section:last-child {
  border-bottom: none;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  margin-bottom: 12px;
  background: linear-gradient(90deg, rgba(51, 65, 85, 0.3) 0%, transparent 100%);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.section-header:hover {
  background: linear-gradient(90deg, rgba(71, 85, 105, 0.4) 0%, transparent 100%);
}

.section-header.weather {
  background: linear-gradient(90deg, rgba(59, 130, 246, 0.15) 0%, transparent 100%);
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.section-header.equipment {
  background: transparent;
  border: none;
  cursor: default;
  padding: 12px 12px 8px;
}

.section-header.equipment:hover {
  background: transparent;
}

.section-icon {
  font-size: 10px;
  color: #94a3b8;
  transition: transform 0.2s;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #cbd5e1;
  flex: 1;
}

.section-badge {
  padding: 2px 8px;
  background: rgba(148, 163, 184, 0.1);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 10px;
  font-size: 10px;
  font-weight: 500;
  color: #94a3b8;
}

.subsection-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  margin-bottom: 8px;
  background: rgba(30, 41, 59, 0.5);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.subsection-header:hover {
  background: rgba(51, 65, 85, 0.5);
}

.subsection-title {
  font-size: 12px;
  font-weight: 500;
  color: #94a3b8;
  flex: 1;
}

.data-grid {
  display: grid;
  gap: 8px;
}

.data-grid.compact {
  grid-template-columns: repeat(2, 1fr);
}

.data-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(51, 65, 85, 0.3);
  border-radius: 10px;
  transition: all 0.2s;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  overflow: hidden;
}

.data-item:hover {
  background: rgba(30, 41, 59, 0.8);
  border-color: rgba(99, 102, 241, 0.3);
  transform: translateX(2px);
}

.data-item.small {
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
  padding: 10px 12px;
}

.data-content {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.data-label {
  font-size: 11px;
  font-weight: 500;
  color: #64748b;
  display: block;
  margin-bottom: 2px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.data-value {
  font-size: 15px;
  font-weight: 600;
  color: #e2e8f0;
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.data-value small {
  font-size: 11px;
  color: #64748b;
  font-weight: 400;
}

.data-subsection {
  margin-bottom: 12px;
}

.data-subsection:last-child {
  margin-bottom: 0;
}

.center-panel {
  width: 100%;
  max-width: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 140px);
  max-height: calc(100vh - 140px);
  gap: 16px;
}

.chart-card {
  flex: 0 0 auto;
  width: 100%;
}

.combined-card {
  flex: 1 1 auto;
  min-height: 0;
}

.chart-container {
  padding: 20px;
  height: 240px;
  background: rgba(15, 23, 42, 0.5);
  position: relative;
}

.prediction-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  padding: 20px;
  background: rgba(15, 23, 42, 0.3);
  border-top: 1px solid rgba(71, 85, 105, 0.2);
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%);
  border: 1px solid rgba(51, 65, 85, 0.3);
  border-radius: 12px;
  transition: all 0.3s;
}

.stat-card:hover {
  border-color: rgba(99, 102, 241, 0.4);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.stat-card.current {
  border-left: 3px solid #3b82f6;
}

.stat-card.max {
  border-left: 3px solid #ef4444;
}

.stat-card.avg {
  border-left: 3px solid #22c55e;
}

.stat-card.conf {
  border-left: 3px solid #a855f7;
}

.stat-content {
  flex: 1;
  min-width: 0;
}

.stat-label {
  font-size: 11px;
  font-weight: 500;
  color: #64748b;
  display: block;
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
  color: #e2e8f0;
  display: block;
  line-height: 1.2;
}

.stat-value.normal {
  color: #22c55e;
}

.stat-value.warning {
  color: #f59e0b;
}

.stat-value.critical {
  color: #ef4444;
}

.stat-unit {
  font-size: 11px;
  font-weight: 400;
  color: #64748b;
  margin-left: 2px;
}

.combined-card {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.tabs {
  display: flex;
  gap: 8px;
  width: 100%;
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: transparent;
  border: none;
  border-radius: 10px;
  color: #94a3b8;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
}

.tab-btn:hover {
  background: rgba(99, 102, 241, 0.1);
  color: #a78bfa;
}

.tab-btn.active {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(139, 92, 246, 0.2) 100%);
  color: #a78bfa;
  font-weight: 600;
}

.tab-btn.active::after {
  content: '';
  position: absolute;
  bottom: -6px;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, #818cf8 0%, #a78bfa 100%);
  border-radius: 1px;
}

.alert-count-badge {
  padding: 2px 8px;
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  border-radius: 12px;
  font-size: 11px;
  font-weight: 700;
  color: white;
  min-width: 20px;
  text-align: center;
  box-shadow: 0 2px 6px rgba(239, 68, 68, 0.3);
}

.alert-count-badge.count-none {
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  box-shadow: 0 2px 6px rgba(34, 197, 94, 0.3);
}

.alert-count-badge.count-low {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  box-shadow: 0 2px 6px rgba(245, 158, 11, 0.3);
}

.alert-count-badge.count-medium {
  background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
  box-shadow: 0 2px 6px rgba(249, 115, 22, 0.3);
}

.tab-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  min-height: 0;
}

.history-list::-webkit-scrollbar {
  width: 6px;
}

.history-list::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}

.history-list::-webkit-scrollbar-thumb {
  background: rgba(139, 92, 246, 0.3);
  border-radius: 3px;
}

.history-list::-webkit-scrollbar-thumb:hover {
  background: rgba(139, 92, 246, 0.5);
}

.history-item {
  padding: 14px;
  margin-bottom: 10px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(51, 65, 85, 0.2);
  border-radius: 10px;
  transition: all 0.2s;
}

.history-item:hover {
  background: rgba(30, 41, 59, 0.8);
  border-color: rgba(99, 102, 241, 0.3);
  transform: translateX(2px);
}

.history-item:last-child {
  margin-bottom: 0;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.history-time {
  font-size: 12px;
  font-weight: 500;
  color: #64748b;
}

.history-badges {
  display: flex;
  gap: 6px;
}

.history-badge {
  padding: 3px 8px;
  background: rgba(59, 130, 246, 0.15);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 6px;
  font-size: 10px;
  font-weight: 500;
  color: #60a5fa;
}

.history-badge.alert {
  background: rgba(245, 158, 11, 0.15);
  border-color: rgba(245, 158, 11, 0.3);
  color: #f59e0b;
}

.history-metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.metric {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 10px;
  background: rgba(30, 41, 59, 0.5);
  border-radius: 6px;
}

.metric-label {
  font-size: 11px;
  color: #64748b;
  font-weight: 500;
}

.metric-value {
  font-size: 13px;
  font-weight: 600;
  color: #e2e8f0;
}

.alert-list-wrapper {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  min-height: 0;
}

.alert-list-wrapper::-webkit-scrollbar {
  width: 6px;
}

.alert-list-wrapper::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}

.alert-list-wrapper::-webkit-scrollbar-thumb {
  background: rgba(139, 92, 246, 0.3);
  border-radius: 3px;
}

.alert-list-wrapper::-webkit-scrollbar-thumb:hover {
  background: rgba(139, 92, 246, 0.5);
}

.right-panel {
  width: 100%;
  max-width: 100%;
}

.alert-list {
  padding: 0;
}

.alert-item {
  display: flex;
  gap: 12px;
  padding: 14px;
  margin-bottom: 10px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(51, 65, 85, 0.3);
  border-radius: 12px;
  transition: all 0.2s;
  position: relative;
  overflow: hidden;
}

.alert-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: #64748b;
}

.alert-item.alert-critical::before {
  background: linear-gradient(180deg, #ef4444 0%, #dc2626 100%);
}

.alert-item.alert-warning::before {
  background: linear-gradient(180deg, #f59e0b 0%, #d97706 100%);
}

.alert-item.alert-info::before {
  background: linear-gradient(180deg, #3b82f6 0%, #2563eb 100%);
}

.alert-item:hover {
  background: rgba(30, 41, 59, 0.8);
  transform: translateX(2px);
}

.alert-item.acknowledged {
  opacity: 0.4;
  filter: grayscale(0.5);
}

.alert-indicator {
  width: 4px;
  min-width: 4px;
  height: 100%;
  border-radius: 2px;
  flex-shrink: 0;
}

.alert-indicator.indicator-critical {
  background: linear-gradient(180deg, #ef4444 0%, #dc2626 100%);
  box-shadow: 0 0 8px rgba(239, 68, 68, 0.5);
}

.alert-indicator.indicator-warning {
  background: linear-gradient(180deg, #f59e0b 0%, #d97706 100%);
  box-shadow: 0 0 8px rgba(245, 158, 11, 0.5);
}

.alert-indicator.indicator-info {
  background: linear-gradient(180deg, #3b82f6 0%, #2563eb 100%);
  box-shadow: 0 0 8px rgba(59, 130, 246, 0.5);
}

.alert-content {
  flex: 1;
  min-width: 0;
}

.alert-message {
  font-size: 13px;
  font-weight: 600;
  color: #e2e8f0;
  margin-bottom: 8px;
  line-height: 1.4;
}

.alert-details {
  display: flex;
  gap: 12px;
  margin-bottom: 6px;
}

.alert-detail {
  font-size: 11px;
  color: #94a3b8;
  font-weight: 500;
}

.alert-time {
  font-size: 11px;
  color: #64748b;
}

.ack-btn {
  padding: 6px 14px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  align-self: center;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}

.ack-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

.ack-btn:active {
  transform: translateY(0);
}

.no-alerts {
  padding: 60px 20px;
  text-align: center;
}

.no-alerts-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 16px;
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.2) 0%, rgba(16, 185, 129, 0.2) 100%);
  border: 2px solid rgba(34, 197, 94, 0.3);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  color: #22c55e;
}

.no-alerts-text {
  font-size: 15px;
  font-weight: 600;
  color: #22c55e;
  margin-bottom: 6px;
}

.no-alerts-hint {
  font-size: 13px;
  color: #64748b;
}

.notification {
  position: fixed;
  top: 24px;
  right: 24px;
  padding: 16px 20px;
  background: rgba(30, 41, 59, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 12px;
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  gap: 12px;
  z-index: 1000;
  border: 1px solid;
  animation: slideIn 0.3s ease;
  max-width: 400px;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.notification.success {
  border-color: rgba(34, 197, 94, 0.5);
  box-shadow: 0 12px 48px rgba(34, 197, 94, 0.2);
}

.notification.warning {
  border-color: rgba(245, 158, 11, 0.5);
  box-shadow: 0 12px 48px rgba(245, 158, 11, 0.2);
}

.notification.error {
  border-color: rgba(239, 68, 68, 0.5);
  box-shadow: 0 12px 48px rgba(239, 68, 68, 0.2);
}

.notification-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.notification.success .notification-indicator {
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  box-shadow: 0 0 8px rgba(34, 197, 94, 0.5);
}

.notification.warning .notification-indicator {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  box-shadow: 0 0 8px rgba(245, 158, 11, 0.5);
}

.notification.error .notification-indicator {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  box-shadow: 0 0 8px rgba(239, 68, 68, 0.5);
}

.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
  max-height: 500px;
  overflow: hidden;
}

.slide-enter-from,
.slide-leave-to {
  max-height: 0;
  opacity: 0;
  transform: translateY(-10px);
}

.notification-enter-active,
.notification-leave-active {
  transition: all 0.3s ease;
}

.notification-enter-from,
.notification-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

@media (max-width: 1600px) {
  .main-layout {
    grid-template-columns: 45% minmax(0, 1fr);
    gap: 16px;
  }

  .main-title {
    font-size: 26px;
  }

  .header-status {
    right: 20px;
  }

  .left-panel,
  .center-panel {
    height: calc(100vh - 140px);
    max-height: calc(100vh - 140px);
  }

  .data-grid.compact {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 1200px) {
  .main-layout {
    grid-template-columns: 1fr;
  }

  .header-status {
    position: static;
    transform: none;
  }

  .left-panel,
  .center-panel {
    height: auto;
    max-height: none;
  }

  .monitor-card,
  .combined-card {
    height: auto;
    max-height: 500px;
  }

  .data-grid.compact {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .vocs-monitor-container {
    padding: 12px;
  }

  .main-layout {
    grid-template-columns: 1fr;
  }

  .header-content {
    flex-direction: column;
    gap: 12px;
    padding: 16px 20px;
  }

  .header-status {
    position: static;
    transform: none;
  }

  .main-title {
    font-size: 22px;
  }

  .left-panel,
  .center-panel {
    height: auto;
    max-height: none;
    display: block;
  }

  .monitor-card,
  .combined-card {
    height: auto;
    max-height: 500px;
  }

  .prediction-stats {
    grid-template-columns: repeat(2, 1fr);
  }

  .chart-container {
    height: 220px;
  }

  .tabs {
    flex-direction: column;
  }

  .tab-btn {
    width: 100%;
    justify-content: center;
  }

  .history-list,
  .alert-list-wrapper {
    max-height: 400px;
  }
}
</style>
