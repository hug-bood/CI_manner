<template>
  <div class="project-detail">
    <el-page-header @back="goBack" :title="project?.name">
      <template #content>
        <el-tag :type="statusTagType(project?.status)">{{ project?.status || '未知' }}</el-tag>
        <span style="margin-left: 10px">责任人: {{ project?.owner || '未分配' }}</span>
        <span style="margin-left: 10px">PL: {{ project?.pl || '未分配' }}</span>
      </template>
    </el-page-header>

    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-statistic title="总用例" :value="project?.total_cases || 0" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="失败用例" :value="project?.total_failed_cases || 0" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="失败率" :value="project?.failure_rate || 0" suffix="%" :precision="2" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="分析进展" :value="project?.analysis_progress || 0" suffix="%" :precision="1" />
      </el-col>
    </el-row>

    <el-card class="table-card">
      <template #header>
        <span>用例列表</span>
        <el-button type="primary" size="small" style="float: right" @click="refresh">刷新</el-button>
      </template>

      <!-- 筛选栏 -->
      <el-form :inline="true" class="case-filter-form">
        <el-form-item label="套件名">
          <el-input
            v-model="caseFilter.suite_name"
            placeholder="输入套件名"
            clearable
            size="small"
            @input="debouncedFetchCases"
          />
        </el-form-item>
        <el-form-item label="用例名">
          <el-input
            v-model="caseFilter.test_name"
            placeholder="输入用例名"
            clearable
            size="small"
            @input="debouncedFetchCases"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select
            v-model="caseFilter.status"
            placeholder="全部"
            clearable
            size="small"
            style="width: 110px"
            @change="fetchCases"
          >
            <el-option label="通过" value="pass" />
            <el-option label="失败" value="fail" />
            <el-option label="丢失" value="lost" />
            <el-option label="处理中" value="processing" />
          </el-select>
        </el-form-item>
        <el-form-item label="责任人">
          <el-input
            v-model="caseFilter.owner"
            placeholder="责任人"
            clearable
            size="small"
            style="width: 120px"
            @input="debouncedFetchCases"
          />
        </el-form-item>
        <el-form-item label="PL">
          <el-input
            v-model="caseFilter.pl"
            placeholder="PL"
            clearable
            size="small"
            style="width: 100px"
            @input="debouncedFetchCases"
          />
        </el-form-item>
        <el-form-item>
          <el-button size="small" @click="resetCaseFilters">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="testCases" stripe v-loading="loading">
        <el-table-column prop="suite_name" label="套件名" width="200" />
        <el-table-column prop="test_name" label="用例名" min-width="200" />

        <el-table-column label="状态" width="130">
          <template #default="{ row }">
            <el-select
              v-model="row.status"
              size="small"
              style="width: 100%"
              @change="(val: string) => onStatusChange(row, val)"
            >
              <el-option label="通过" value="pass" />
              <el-option label="失败" value="fail" />
              <el-option label="丢失" value="lost" />
              <el-option label="处理中" value="processing" />
            </el-select>
          </template>
        </el-table-column>

        <el-table-column prop="failure_reason" label="失败原因" min-width="180">
          <template #default="{ row }">
            <el-input
              v-model="row.failure_reason"
              placeholder="未填写"
              size="small"
              :disabled="row.status === 'pass'"
              @blur="updateField(row, 'failure_reason', row.failure_reason)"
              @keyup.enter="updateField(row, 'failure_reason', row.failure_reason)"
            />
          </template>
        </el-table-column>

        <el-table-column label="责任人" width="120">
          <template #default="{ row }">
            <el-input
              v-model="row.owner"
              placeholder="未分配"
              size="small"
              @blur="updateField(row, 'owner', row.owner)"
              @keyup.enter="updateField(row, 'owner', row.owner)"
            />
          </template>
        </el-table-column>

        <el-table-column label="PL" width="100">
          <template #default="{ row }">
            <el-input
              v-model="row.pl"
              placeholder="未分配"
              size="small"
              @blur="updateField(row, 'pl', row.pl)"
              @keyup.enter="updateField(row, 'pl', row.pl)"
            />
          </template>
        </el-table-column>

        <el-table-column prop="report_date" label="报告日期" width="120" />
      </el-table>

      <el-pagination
        v-model:current-page="casePagination.page"
        v-model:page-size="casePagination.size"
        :total="casePagination.total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchCases"
        @current-change="fetchCases"
        class="pagination"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { getProjectDetail, type ProjectDetailResponse } from '@/api/projects'
import { getTestCaseList, updateTestCase, type TestCaseItem, type TestCaseUpdateData } from '@/api/testCases'
import { ElMessage } from 'element-plus'
import { debounce } from 'lodash-es'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()

const projectId = Number(route.params.id)
const loading = ref(false)
const project = ref<ProjectDetailResponse | null>(null)
const testCases = ref<TestCaseItem[]>([])

const caseFilter = reactive({
  suite_name: '',
  test_name: '',
  status: '',
  owner: '',
  pl: ''
})

const casePagination = ref({ page: 1, size: 20, total: 0 })

const statusTagType = (status?: string) => {
  switch (status) {
    case 'pass': return 'success'
    case 'fail': return 'danger'
    case 'lost': return 'info'
    case 'processing': return 'warning'
    default: return 'info'
  }
}

// 获取工程基本信息
const fetchDetail = async () => {
  loading.value = true
  try {
    const res = await getProjectDetail(projectId)
    project.value = res.data
    await fetchCases()
  } finally {
    loading.value = false
  }
}

// 获取用例列表（带筛选）
const fetchCases = async () => {
  loading.value = true
  try {
    const res = await getTestCaseList({
      project_id: projectId,
      suite_name: caseFilter.suite_name || undefined,
      test_name: caseFilter.test_name || undefined,
      status: caseFilter.status || undefined,
      owner: caseFilter.owner || undefined,
      pl: caseFilter.pl || undefined,
      page: casePagination.value.page,
      size: casePagination.value.size
    })
    testCases.value = res.data.items
    casePagination.value.total = res.data.total
  } catch (e) {
    ElMessage.error('获取用例列表失败')
  } finally {
    loading.value = false
  }
}

// 防抖搜索
const debouncedFetchCases = debounce(() => {
  casePagination.value.page = 1
  fetchCases()
}, 300)

// 重置筛选
const resetCaseFilters = () => {
  caseFilter.suite_name = ''
  caseFilter.test_name = ''
  caseFilter.status = ''
  caseFilter.owner = ''
  caseFilter.pl = ''
  casePagination.value.page = 1
  fetchCases()
}

// 状态变更逻辑：processing / pass 自动标记已分析
const onStatusChange = async (row: TestCaseItem, newStatus: string) => {
  const updates: Partial<TestCaseUpdateData> = { status: newStatus }
  if (newStatus === 'processing' || newStatus === 'pass') {
    updates.is_analyzed = true
  }
  try {
    await updateTestCase(row.id, updates)
    ElMessage.success('状态已更新')
    // 关键修复：并行刷新工程详情和用例列表，确保分析进展即时更新
    await Promise.all([fetchDetail(), fetchCases()])
  } catch (e) {
    ElMessage.error('更新失败')
  }
}

// 通用字段更新（责任人、PL、失败原因等）
const updateField = async (row: TestCaseItem, field: keyof TestCaseUpdateData, value: any) => {
  try {
    await updateTestCase(row.id, { [field]: value })
    ElMessage.success('更新成功')
    // 同样并行刷新，保持数据一致
    await Promise.all([fetchDetail(), fetchCases()])
  } catch (e) {
    ElMessage.error('更新失败')
  }
}

const refresh = () => {
  casePagination.value.page = 1
  fetchDetail()
}

const goBack = () => router.push('/projects')

onMounted(() => {
  if (!appStore.currentProduct || !appStore.currentVersion) {
    ElMessage.warning('请先选择产品和版本')
    router.push('/dashboard')
    return
  }
  fetchDetail()
})
</script>

<style scoped>
.project-detail {
  padding: 0 10px;
}
.stats-row {
  margin: 20px 0;
}
.table-card {
  margin-top: 10px;
}
.case-filter-form {
  margin-bottom: 15px;
  padding: 10px 0;
  border-bottom: 1px solid #ebeef5;
}
.pagination {
  margin-top: 15px;
  justify-content: flex-end;
}
</style>