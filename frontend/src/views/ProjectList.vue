<template>
  <div class="project-list">
    <h2>工程列表</h2>

    <!-- 筛选栏：输入实时搜索，无查询按钮 -->
    <el-form :inline="true" class="filter-form">
      <el-form-item label="状态">
        <el-select
          v-model="filterStatus"
          placeholder="全部"
          clearable
          style="width: 120px"
          @change="handleFilterChange"
        >
          <el-option label="全部" value="all" />
          <el-option label="成功" value="success" />
          <el-option label="失败" value="failure" />
          <el-option label="Lost" value="lost" />
        </el-select>
      </el-form-item>
      <el-form-item label="工程名">
        <el-input
          v-model="filterSearch"
          placeholder="输入工程名"
          clearable
          style="width: 180px"
          @input="handleFilterChange"
        />
      </el-form-item>
      <el-form-item label="责任人">
        <el-input
          v-model="filterOwner"
          placeholder="输入责任人"
          clearable
          style="width: 150px"
          @input="handleFilterChange"
        />
      </el-form-item>
      <el-form-item label="PL">
        <el-input
          v-model="filterPl"
          placeholder="输入PL"
          clearable
          style="width: 120px"
          @input="handleFilterChange"
        />
      </el-form-item>
      <!-- 重置按钮保留，方便清空所有筛选 -->
      <el-form-item>
        <el-button @click="resetFilters">重置</el-button>
      </el-form-item>
    </el-form>

    <!-- 工程表格 -->
    <el-table :data="projects" stripe style="width: 100%" v-loading="loading">
      <el-table-column label="工程名" min-width="180">
        <template #default="{ row }">
          <el-button type="primary" link @click="goToDetail(row.id)">
            {{ row.name }}
          </el-button>
        </template>
      </el-table-column>

      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)">
            {{ row.status || '未知' }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column prop="total_cases" label="总用例" width="100" />
      <el-table-column prop="total_failed_cases" label="失败用例" width="100" />

      <el-table-column label="失败率" width="120">
        <template #default="{ row }">
          <el-progress :percentage="row.failure_rate" :color="progressColor(row.failure_rate)" />
        </template>
      </el-table-column>

      <el-table-column label="分析进展" width="120">
        <template #default="{ row }">
          <el-progress :percentage="row.analysis_progress" :color="progressColor(row.analysis_progress)" />
        </template>
      </el-table-column>

      <el-table-column label="责任人" width="140">
        <template #default="{ row }">
          <el-input
            v-model="row.owner"
            placeholder="未分配"
            size="small"
            @blur="updateOwner(row)"
            @keyup.enter="updateOwner(row)"
          />
        </template>
      </el-table-column>

      <el-table-column label="PL" width="100">
        <template #default="{ row }">
          <el-input
            v-model="row.pl"
            placeholder="未分配"
            size="small"
            @blur="updatePl(row)"
            @keyup.enter="updatePl(row)"
          />
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <el-pagination
      v-model:current-page="pagination.page"
      v-model:page-size="pagination.size"
      :total="pagination.total"
      :page-sizes="[10, 20, 50]"
      layout="total, sizes, prev, pager, next, jumper"
      @size-change="fetchProjects"
      @current-change="fetchProjects"
      class="pagination"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { getProjectList, updateProject, type ProjectItem } from '@/api/projects'
import { ElMessage } from 'element-plus'
import { debounce } from 'lodash-es' // 需要安装 lodash-es: npm install lodash-es

const router = useRouter()
const appStore = useAppStore()

const loading = ref(false)
const projects = ref<ProjectItem[]>([])

// 筛选条件
const filterStatus = ref<string>('all')
const filterSearch = ref('')
const filterOwner = ref('')
const filterPl = ref('')

const pagination = ref({ page: 1, size: 20, total: 0 })

const statusTagType = (status: string) => {
  switch (status) {
    case 'success': return 'success'
    case 'failure': return 'danger'
    case 'lost': return 'info'
    default: return 'info'
  }
}

const progressColor = (percent: number) => {
  if (percent < 30) return '#67c23a'
  if (percent < 70) return '#e6a23c'
  return '#f56c6c'
}

// 实际请求函数
const fetchProjects = async () => {
  if (!appStore.currentProduct || !appStore.currentVersion) {
    ElMessage.warning('请先选择产品和版本')
    return
  }
  loading.value = true
  try {
    const res = await getProjectList(
      appStore.currentProduct,
      appStore.currentVersion,
      pagination.value.page,
      pagination.value.size,
      filterStatus.value === 'all' ? undefined : filterStatus.value,
      filterSearch.value || undefined,
      filterOwner.value || undefined,
      filterPl.value || undefined
    )
    projects.value = res.data.items
    pagination.value.total = res.data.total
  } finally {
    loading.value = false
  }
}

// 防抖处理，输入时触发，重置页码
const debouncedFetch = debounce(() => {
  pagination.value.page = 1
  fetchProjects()
}, 300)

// 筛选条件变化时的处理（状态变更立即触发，输入通过防抖）
const handleFilterChange = () => {
  debouncedFetch()
}

// 重置所有筛选条件
const resetFilters = () => {
  filterStatus.value = 'all'
  filterSearch.value = ''
  filterOwner.value = ''
  filterPl.value = ''
  pagination.value.page = 1
  fetchProjects()
}

const updateOwner = async (row: ProjectItem) => {
  try {
    await updateProject(row.id, { owner: row.owner })
    ElMessage.success('责任人已更新')
  } catch (e) {
    ElMessage.error('更新失败')
    fetchProjects()
  }
}

const updatePl = async (row: ProjectItem) => {
  try {
    await updateProject(row.id, { pl: row.pl })
    ElMessage.success('PL已更新')
  } catch (e) {
    ElMessage.error('更新失败')
    fetchProjects()
  }
}

const goToDetail = (id: number) => {
  router.push(`/projects/${id}`)
}

// 监听产品/版本变化，重置页码并查询
watch(() => [appStore.currentProduct, appStore.currentVersion], () => {
  pagination.value.page = 1
  fetchProjects()
}, { immediate: true })
</script>

<style scoped>
.project-list h2 {
  margin-bottom: 20px;
}
.filter-form {
  margin-bottom: 20px;
}
.pagination {
  margin-top: 20px;
  justify-content: flex-end;
}
</style>