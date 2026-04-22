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

      <el-form :inline="true" class="case-filter-form">
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
        <el-form-item label="源码问题">
          <el-select
            v-model="caseFilter.is_source_code_issue"
            placeholder="全部"
            clearable
            size="small"
            style="width: 100px"
            @change="fetchCases"
          >
            <el-option label="是" :value="true" />
            <el-option label="否" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button size="small" @click="resetCaseFilters">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="testCases" stripe v-loading="loading" class="center-table">
        <el-table-column prop="test_name" label="用例名" min-width="180" align="center" />

        <el-table-column label="状态" width="130" align="center">
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

        <el-table-column label="源码问题" width="100" align="center">
          <template #default="{ row }">
            <el-checkbox
              v-model="row.is_source_code_issue"
              @change="(val: boolean) => updateField(row, 'is_source_code_issue', val)"
            />
          </template>
        </el-table-column>

        <el-table-column label="DTS单号" width="200" align="center">
          <template #default="{ row }">
            <template v-if="row.is_source_code_issue">
              <div
                v-if="editingDtsId !== row.id"
                class="editable-cell text-center"
                @click="startEditDts(row)"
              >
                <el-link
                  v-if="row.dts_ticket && row.dts_link"
                  :href="row.dts_link"
                  target="_blank"
                  type="primary"
                  :underline="false"
                  @click.stop
                >
                  {{ row.dts_ticket }}
                </el-link>
                <span v-else-if="row.dts_ticket">{{ row.dts_ticket }}</span>
                <span v-else class="placeholder">点击添加</span>
              </div>
              <el-input
                v-else
                ref="dtsInputRef"
                v-model="dtsInputValue"
                size="small"
                @blur="saveDtsTicket(row)"
                @keyup.enter="saveDtsTicket(row)"
              />
            </template>
            <span v-else style="color: #909399">-</span>
          </template>
        </el-table-column>

        <el-table-column prop="failure_reason" label="失败原因" min-width="220" align="center">
          <template #default="{ row }">
            <div
              v-if="editingFailureReasonId !== row.id"
              class="editable-cell"
              :class="{ 'text-muted': !row.failure_reason, disabled: row.status === 'pass' }"
              @click="row.status !== 'pass' && startEditFailureReason(row)"
            >
              {{ row.failure_reason || (row.status === 'pass' ? '-' : '点击填写') }}
            </div>
            <el-input
              v-else
              ref="failureReasonInputRef"
              v-model="failureReasonInputValue"
              size="small"
              @blur="saveFailureReason(row)"
              @keyup.enter="saveFailureReason(row)"
            />
          </template>
        </el-table-column>

        <el-table-column label="责任人" width="120" align="center">
          <template #default="{ row }">
            <div
              v-if="editingOwnerId !== row.id"
              class="editable-cell"
              :class="{ 'text-muted': !row.owner }"
              @click="startEditOwner(row)"
            >
              {{ row.owner || '点击填写' }}
            </div>
            <el-input
              v-else
              ref="ownerInputRef"
              v-model="ownerInputValue"
              size="small"
              @blur="saveOwner(row)"
              @keyup.enter="saveOwner(row)"
            />
          </template>
        </el-table-column>

        <!-- 新增“详情”列，暂不绑定功能 -->
        <el-table-column label="详情" width="80" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleDetail(row)">
              详情
            </el-button>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="80" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openEditDialog(row)">
              编辑
            </el-button>
          </template>
        </el-table-column>
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

    <el-dialog v-model="editDialogVisible" title="编辑用例" width="500px">
      <el-form :model="editForm" label-width="120px">
        <el-form-item label="状态">
          <el-select v-model="editForm.status" placeholder="选择状态">
            <el-option label="通过" value="pass" />
            <el-option label="失败" value="fail" />
            <el-option label="丢失" value="lost" />
            <el-option label="处理中" value="processing" />
          </el-select>
        </el-form-item>
        <el-form-item label="失败原因">
          <el-input v-model="editForm.failure_reason" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="责任人">
          <el-input v-model="editForm.owner" />
        </el-form-item>
        <el-form-item label="是否是源码问题">
          <el-switch v-model="editForm.is_source_code_issue" />
        </el-form-item>
        <el-form-item label="关联DTS单号" v-if="editForm.is_source_code_issue">
          <el-input v-model="editForm.dts_ticket" placeholder="请输入DTS单号" />
        </el-form-item>
        <el-form-item label="DTS链接预览" v-if="editForm.is_source_code_issue && editForm.dts_ticket">
          <el-link type="primary" target="_blank" :href="generateDtsLinkPreview(editForm.dts_ticket)">
            {{ generateDtsLinkPreview(editForm.dts_ticket) }}
          </el-link>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEdit" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted, nextTick } from 'vue'
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
  test_name: '',
  status: '',
  owner: '',
  is_source_code_issue: undefined as boolean | undefined
})

const casePagination = ref({ page: 1, size: 20, total: 0 })

const editingDtsId = ref<number | null>(null)
const dtsInputValue = ref('')
const dtsInputRef = ref<HTMLInputElement>()

const editingFailureReasonId = ref<number | null>(null)
const failureReasonInputValue = ref('')
const failureReasonInputRef = ref<HTMLInputElement>()

const editingOwnerId = ref<number | null>(null)
const ownerInputValue = ref('')
const ownerInputRef = ref<HTMLInputElement>()

const editDialogVisible = ref(false)
const saving = ref(false)
const editingRow = ref<TestCaseItem | null>(null)
const editForm = reactive({
  status: '',
  failure_reason: '',
  owner: '',
  is_source_code_issue: false,
  dts_ticket: ''
})

const statusTagType = (status?: string) => {
  switch (status) {
    case 'pass': return 'success'
    case 'fail': return 'danger'
    case 'lost': return 'info'
    case 'processing': return 'warning'
    default: return 'info'
  }
}

const generateDtsLinkPreview = (ticket: string) => {
  return `https://dts.company.com/ticket/${ticket}`
}

// 详情按钮占位函数
const handleDetail = (row: TestCaseItem) => {
  // 暂时不做任何操作
  console.log('详情按钮点击，用例ID:', row.id)
}

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

const fetchCases = async () => {
  loading.value = true
  try {
    const res = await getTestCaseList({
      project_id: projectId,
      test_name: caseFilter.test_name || undefined,
      status: caseFilter.status || undefined,
      owner: caseFilter.owner || undefined,
      is_source_code_issue: caseFilter.is_source_code_issue,
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

const debouncedFetchCases = debounce(() => {
  casePagination.value.page = 1
  fetchCases()
}, 300)

const resetCaseFilters = () => {
  caseFilter.test_name = ''
  caseFilter.status = ''
  caseFilter.owner = ''
  caseFilter.is_source_code_issue = undefined
  casePagination.value.page = 1
  fetchCases()
}

const onStatusChange = async (row: TestCaseItem, newStatus: string) => {
  const updates: Partial<TestCaseUpdateData> = { status: newStatus }
  if (newStatus === 'processing' || newStatus === 'pass') {
    updates.is_analyzed = true
  }
  try {
    await updateTestCase(row.id, updates)
    row.status = newStatus
    if (updates.is_analyzed) row.is_analyzed = true
    ElMessage.success('状态已更新')
    await Promise.all([fetchDetail(), fetchCases()])
  } catch (e) {
    ElMessage.error('更新失败')
  }
}

const updateField = async (row: TestCaseItem, field: keyof TestCaseUpdateData, value: any) => {
  try {
    await updateTestCase(row.id, { [field]: value })
    ElMessage.success('更新成功')
    await Promise.all([fetchDetail(), fetchCases()])
  } catch (e) {
    ElMessage.error('更新失败')
  }
}

const startEditDts = (row: TestCaseItem) => {
  editingDtsId.value = row.id
  dtsInputValue.value = row.dts_ticket || ''
  nextTick(() => dtsInputRef.value?.focus())
}

const saveDtsTicket = async (row: TestCaseItem) => {
  const newValue = dtsInputValue.value.trim()
  editingDtsId.value = null
  if (newValue === (row.dts_ticket || '')) return
  try {
    await updateTestCase(row.id, { dts_ticket: newValue || null })
    row.dts_ticket = newValue || null
    ElMessage.success('DTS单号已更新')
    await Promise.all([fetchDetail(), fetchCases()])
  } catch (e) {
    ElMessage.error('更新失败')
  }
}

const startEditFailureReason = (row: TestCaseItem) => {
  if (row.status === 'pass') return
  editingFailureReasonId.value = row.id
  failureReasonInputValue.value = row.failure_reason || ''
  nextTick(() => failureReasonInputRef.value?.focus())
}

const saveFailureReason = async (row: TestCaseItem) => {
  const newValue = failureReasonInputValue.value.trim()
  editingFailureReasonId.value = null
  if (newValue === (row.failure_reason || '')) return
  try {
    await updateTestCase(row.id, { failure_reason: newValue || null })
    row.failure_reason = newValue || null
    ElMessage.success('失败原因已更新')
    await Promise.all([fetchDetail(), fetchCases()])
  } catch (e) {
    ElMessage.error('更新失败')
  }
}

const startEditOwner = (row: TestCaseItem) => {
  editingOwnerId.value = row.id
  ownerInputValue.value = row.owner || ''
  nextTick(() => ownerInputRef.value?.focus())
}

const saveOwner = async (row: TestCaseItem) => {
  const newValue = ownerInputValue.value.trim()
  editingOwnerId.value = null
  if (newValue === (row.owner || '')) return
  try {
    await updateTestCase(row.id, { owner: newValue || null })
    row.owner = newValue || null
    ElMessage.success('责任人已更新')
    await Promise.all([fetchDetail(), fetchCases()])
  } catch (e) {
    ElMessage.error('更新失败')
  }
}

const openEditDialog = (row: TestCaseItem) => {
  editingRow.value = row
  editForm.status = row.status
  editForm.failure_reason = row.failure_reason || ''
  editForm.owner = row.owner || ''
  editForm.is_source_code_issue = row.is_source_code_issue
  editForm.dts_ticket = row.dts_ticket || ''
  editDialogVisible.value = true
}

const saveEdit = async () => {
  if (!editingRow.value) return
  saving.value = true
  try {
    const updates: Partial<TestCaseUpdateData> = {
      status: editForm.status,
      failure_reason: editForm.failure_reason || null,
      owner: editForm.owner || null,
      is_source_code_issue: editForm.is_source_code_issue,
      dts_ticket: editForm.dts_ticket || null
    }
    if (editForm.status === 'processing' || editForm.status === 'pass') {
      updates.is_analyzed = true
    }
    await updateTestCase(editingRow.value.id, updates)
    ElMessage.success('保存成功')
    editDialogVisible.value = false
    await Promise.all([fetchDetail(), fetchCases()])
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const refresh = () => {
  casePagination.value.page = 1
  fetchDetail()
}

const goBack = () => router.push('/projects')

watch(() => [appStore.currentProduct, appStore.currentVersion], () => {
  casePagination.value.page = 1
  fetchDetail()
}, { immediate: true })

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

.center-table :deep(.el-table__header th) {
  text-align: center;
}
.center-table :deep(.el-table__body td) {
  text-align: center;
}

.editable-cell {
  min-height: 32px;
  line-height: 32px;
  padding: 0 8px;
  border-radius: 4px;
  cursor: text;
  transition: background-color 0.2s;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.editable-cell:hover {
  background-color: #f5f7fa;
}
.text-muted {
  color: #c0c4cc;
}
.placeholder {
  color: #c0c4cc;
}
.disabled {
  cursor: not-allowed;
  color: #c0c4cc;
}
.disabled:hover {
  background-color: transparent;
}

.text-center {
  text-align: center;
}

:deep(.el-table .el-input) {
  width: 100%;
}
:deep(.el-table .el-input__wrapper) {
  padding: 0 8px;
}
:deep(.el-table .el-input__inner) {
  height: 32px;
  line-height: 32px;
  text-align: center;
}
</style>