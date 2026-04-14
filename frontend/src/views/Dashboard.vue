<template>
  <div class="dashboard">
    <h2>工程汇总仪表盘</h2>
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ summary.total_projects }}</div>
          <div class="stat-label">总工程数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ summary.failed_projects }}</div>
          <div class="stat-label">失败工程数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ summary.total_failed_cases }}</div>
          <div class="stat-label">失败用例数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ summary.average_analysis_progress.toFixed(1) }}%</div>
          <div class="stat-label">平均分析进展</div>
        </el-card>
      </el-col>
    </el-row>
    <el-row :gutter="20" class="chart-row">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>失败率分布</template>
          <div ref="failureChartRef" style="height: 300px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>分析进展趋势 (近5天)</template>
          <div ref="trendChartRef" style="height: 300px"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useAppStore } from '@/stores/app'
import { getSummary, type SummaryResponse } from '@/api/projects'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'

const appStore = useAppStore()
const summary = ref<SummaryResponse>({
  total_projects: 0,
  failed_projects: 0,
  total_failed_cases: 0,
  average_failure_rate: 0,
  average_analysis_progress: 0,
  analysis_trend: []
})

const failureChartRef = ref<HTMLElement>()
const trendChartRef = ref<HTMLElement>()
let failureChart: echarts.ECharts | null = null
let trendChart: echarts.ECharts | null = null

const fetchSummary = async () => {
  if (!appStore.currentProduct || !appStore.currentVersion) {
    ElMessage.warning('请先选择产品和版本')
    return
  }
  try {
    const res = await getSummary(appStore.currentProduct, appStore.currentVersion)
    summary.value = res.data
    updateCharts()
  } catch (e) {
    // 错误已在拦截器处理
  }
}

const updateCharts = () => {
  if (failureChart) {
    failureChart.setOption({
      tooltip: { trigger: 'item' },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        data: [
          { value: summary.value.average_failure_rate, name: '平均失败率' },
          { value: 100 - summary.value.average_failure_rate, name: '通过率' }
        ],
        label: { formatter: '{b}: {d}%' }
      }]
    })
  }
  if (trendChart) {
    trendChart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: ['4天前', '3天前', '2天前', '昨天', '今天'] },
      yAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%' } },
      series: [{
        type: 'line',
        data: summary.value.analysis_trend,
        smooth: true,
        lineStyle: { color: '#409eff', width: 3 },
        areaStyle: { color: 'rgba(64, 158, 255, 0.2)' }
      }]
    })
  }
}

const initCharts = () => {
  if (failureChartRef.value) {
    failureChart = echarts.init(failureChartRef.value)
  }
  if (trendChartRef.value) {
    trendChart = echarts.init(trendChartRef.value)
  }
  updateCharts()
}

onMounted(() => {
  initCharts()
  if (appStore.currentProduct && appStore.currentVersion) {
    fetchSummary()
  }
})

watch(() => [appStore.currentProduct, appStore.currentVersion], () => {
  fetchSummary()
}, { immediate: true })
</script>

<style scoped>
.dashboard h2 {
  margin-bottom: 20px;
}
.stats-row {
  margin-bottom: 20px;
}
.stat-card {
  text-align: center;
}
.stat-value {
  font-size: 36px;
  font-weight: bold;
  color: #409eff;
}
.stat-label {
  color: #909399;
  margin-top: 10px;
}
.chart-row {
  margin-top: 10px;
}
</style>