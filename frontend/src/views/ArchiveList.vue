<template>
  <div class="archive-list">
    <h2>历史失败归档</h2>

    <!-- 筛选栏 -->
    <el-form :inline="true" class="filter-form">
      <el-form-item label="工程名">
        <el-input
          v-model="filter.project_name"
          placeholder="工程名"
          clearable
          size="small"
          @input="debouncedFetch"
        />
      </el-form-item>
      <el-form-item label="套件名">
        <el-input
          v-model="filter.suite_name"
          placeholder="套件名"
          clearable
          size="small"
          @input="debouncedFetch"
        />
      </el-form-item>
      <el-form-item label="用例名">
        <el-input
          v-model="filter.test_name"
          placeholder="用例名"
          clearable
          size="small"
          @input="debouncedFetch"
        />
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="filter.status" placeholder="全部" clearable size="small" @change="fetchData">
          <el-option label="失败" value="fail" />
          <el-option label="丢失" value="lost" />
          <el-option label="处理中" value="processing" />
        </el-select>
      </el-form-item>
      <el-form-item label="责任人">
        <el-input
          v-model="filter.owner"
          placeholder="责任人"
          clearable
          size="small"
          @input="debouncedFetch"
        />
      </el-form-item>
      <el-form-item label="PL">
        <el-input
          v-model="filter.pl"
          placeholder="PL"
          clearable
          size="small"
          @input="debouncedFetch"
        />
      </el-form-item>
      <el-form-item>
        <el-button size="small" @click="resetFilters">重置</el-button>
      </el-form-item>
    </el-form>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="总归档记录" :value="pagination.total" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="平均连续失败天数" :value="avgConsecutiveDays" :precision="1" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 数据表格 -->
    <el-table :data="items" stripe v-loading="loading" style="width: 100%">
      <el-table-column prop="project_name" label="工程名" width="150" />
      <el-table-column prop="suite_name" label="套件名" width="180" />
      <el-table-column prop="test_name" label="用例名" min-width="200" />
      <el-table-column prop="status" label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="failure_date" label="失败日期" width="120" />
      <el-table-column prop="first_failure_date" label="起始日期" width="120" />
      <el-table-column prop="consecutive_days" label="连续天数" width="100">
        <template #default="{ row }">
          <el-tag :type="consecutiveTagType(row.consecutive_days)">{{ row.consecutive_days }} 天</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="failure_reason" label="失败原因" min-width="180" show-overflow-tooltip />
      <el-table-column prop="owner" label="责任人" width="100" />
      <el-table-column prop="pl" label="PL" width="80" />
    </el-table>

    <el-pagination
      v-model:current-page="pagination.page"
      v-model:page-size="pagination.size"
      :total="pagination.total"
      :page-sizes="[10, 20, 50]"
      layout="total, sizes, prev, pager, next, jumper"
      @size-change="fetchData"
      @current-change="fetchData"
      class="pagination"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useAppStore } from '@/stores/app'
import { getArchiveList, type ArchiveItem } from '@/api/archive'
import { ElMessage } from 'element-plus'
import { debounce } from 'lodash-es'

const appStore = useAppStore()

const loading = ref(false)
const items = ref<ArchiveItem[]>([])
const pagination = ref({ page: 1, size: 20, total: 0 })

const filter = reactive({
  project_name: '',
  suite_name: '',
  test_name: '',
  status: '',
  owner: '',
  pl: ''
})

const statusTagType = (status: string) => {
  switch (status) {
    case 'fail': return 'danger'
    case 'lost': return 'info'
    case 'processing': return 'warning'
    default: return ''
  }
}

const consecutiveTagType = (days: number) => {
  if (days >= 7) return 'danger'
  if (days >= 3) return 'warning'
  return 'success'
}

const avgConsecutiveDays = computed(() => {
  if (items.value.length === 0) return 0
  const sum = items.value.reduce((acc, cur) => acc + cur.consecutive_days, 0)
  return sum / items.value.length
})

const fetchData = async () => {
  if (!appStore.currentProduct || !appStore.currentVersion) {
    ElMessage.warning('请先选择产品和版本')
    return
  }
  loading.value = true
  try {
    const res = await getArchiveList({
      product_name: appStore.currentProduct,
      version: appStore.currentVersion,
      project_name: filter.project_name || undefined,
      suite_name: filter.suite_name || undefined,
      test_name: filter.test_name || undefined,
      status: filter.status || undefined,
      owner: filter.owner || undefined,
      pl: filter.pl || undefined,
      page: pagination.value.page,
      size: pagination.value.size
    })
    items.value = res.data.items
    pagination.value.total = res.data.total
  } catch (e) {
    ElMessage.error('获取归档数据失败')
  } finally {
    loading.value = false
  }
}

const debouncedFetch = debounce(() => {
  pagination.value.page = 1
  fetchData()
}, 300)

const resetFilters = () => {
  filter.project_name = ''
  filter.suite_name = ''
  filter.test_name = ''
  filter.status = ''
  filter.owner = ''
  filter.pl = ''
  pagination.value.page = 1
  fetchData()
}

watch(() => [appStore.currentProduct, appStore.currentVersion], () => {
  pagination.value.page = 1
  fetchData()
}, { immediate: true })

onMounted(() => {
  if (appStore.currentProduct && appStore.currentVersion) {
    fetchData()
  }
})
</script>

<style scoped>
.archive-list h2 {
  margin-bottom: 20px;
}
.filter-form {
  margin-bottom: 20px;
}
.stats-row {
  margin-bottom: 20px;
}
.pagination {
  margin-top: 20px;
  justify-content: flex-end;
}
</style>