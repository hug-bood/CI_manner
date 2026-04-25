<template>
  <div class="project-list">
    <h2>工程列表</h2>

    <!-- 筛选栏 -->
    <el-form :inline="true" class="filter-form">
      <el-form-item>
        <el-button type="primary" size="small" @click="showAddDialog">新增工程</el-button>
      </el-form-item>
      <el-form-item label="特性">
        <el-select v-model="filterFeature" placeholder="全部" clearable style="width: 140px" @change="onFeatureChange">
          <el-option v-for="f in features" :key="f.id" :label="f.feature_name" :value="f.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="filterStatus" placeholder="全部" clearable style="width: 120px" @change="fetchProjects">
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
          style="width: 170px"
          @input="debouncedFetchProjects"
        />
      </el-form-item>
      <el-form-item label="责任人">
        <el-input
          v-model="filterOwner"
          placeholder="输入责任人"
          clearable
          style="width: 150px"
          @input="debouncedFetchProjects"
        />
      </el-form-item>
      <el-form-item label="PL">
        <el-input
          v-model="filterPl"
          placeholder="输入PL"
          clearable
          style="width: 120px"
          @input="debouncedFetchProjects"
        />
      </el-form-item>
      <el-form-item>
        <el-button @click="resetFilters">重置</el-button>
      </el-form-item>
    </el-form>

    <!-- 工程表格 -->
    <el-table :data="projects" stripe style="width: 100%" v-loading="loading">
      <el-table-column label="工程名" min-width="160">
        <template #default="{ row }">
          <el-button type="primary" link @click="goToDetail(row)">
            {{ row.project_name }}
          </el-button>
        </template>
      </el-table-column>

      <el-table-column prop="status" label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)">
            {{ row.status || '未知' }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column prop="total_failed_cases" label="失败用例数" width="110" align="center" />

      <el-table-column label="分析进展" width="130" align="center">
        <template #default="{ row }">
          <el-progress :percentage="row.analysis_progress" :color="progressColor(row.analysis_progress)" :stroke-width="16" :text-inside="true" />
        </template>
      </el-table-column>

      <el-table-column label="失败原因" min-width="180">
        <template #default="{ row }">
          <div
            v-if="editingFailureReasonKey !== rowKey(row)"
            class="editable-cell"
            :class="{ 'text-muted': !row.failure_reason }"
            @click="startEditFailureReason(row)"
          >
            {{ row.failure_reason || '点击填写' }}
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

      <el-table-column label="推送时间" width="170" align="center">
        <template #default="{ row }">
          {{ row.last_report_at ? formatTime(row.last_report_at) : '-' }}
        </template>
      </el-table-column>

      <!-- 责任人：点击激活编辑 -->
      <el-table-column label="责任人" width="120">
        <template #default="{ row }">
          <div
            v-if="editingOwnerKey !== rowKey(row)"
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

      <!-- PL：点击激活编辑 -->
      <el-table-column label="PL" width="100">
        <template #default="{ row }">
          <div
            v-if="editingPlKey !== rowKey(row)"
            class="editable-cell"
            :class="{ 'text-muted': !row.pl }"
            @click="startEditPl(row)"
          >
            {{ row.pl || '点击填写' }}
          </div>
          <el-input
            v-else
            ref="plInputRef"
            v-model="plInputValue"
            size="small"
            @blur="savePl(row)"
            @keyup.enter="savePl(row)"
          />
        </template>
      </el-table-column>

      <el-table-column label="提单" width="80" align="center">
        <template #default>
          <el-button type="primary" link size="small" disabled>提单</el-button>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="80" fixed="right" align="center">
        <template #default="{ row }">
          <el-button type="danger" link size="small" @click="doDelete(row)">删除</el-button>
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

    <!-- 新增弹窗 -->
    <el-dialog v-model="addDialogVisible" title="新增工程" width="400px">
      <el-form :model="addForm" label-width="80px">
        <el-form-item label="工程名">
          <el-input v-model="addForm.project_name" />
        </el-form-item>
        <el-form-item label="PL">
          <el-input v-model="addForm.pl" />
        </el-form-item>
        <el-form-item label="责任人">
          <el-input v-model="addForm.owner" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="doAdd">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { getUnifiedProjectList, updateProject, deleteProject, createProject, type UnifiedProjectItem } from '@/api/projects'
import { updateProjectConfig, deleteProjectConfig } from '@/api/projectConfigs'
import { getFeatureList, getFeatureProjects, type FeatureItem } from '@/api/features'
import { ElMessage, ElMessageBox } from 'element-plus'
import { debounce } from 'lodash-es'

const router = useRouter()
const appStore = useAppStore()

const loading = ref(false)
const projects = ref<UnifiedProjectItem[]>([])
const features = ref<FeatureItem[]>([])

// 筛选条件
const filterFeature = ref<number | undefined>(undefined)
const filterStatus = ref<string>('all')
const filterSearch = ref('')
const filterOwner = ref('')
const filterPl = ref('')

const pagination = ref({ page: 1, size: 20, total: 0 })

// 用 project_name 作为行唯一标识（因为 project_id 可能为 null）
const rowKey = (row: UnifiedProjectItem) => row.project_name

// 内联编辑状态 - 责任人
const editingOwnerKey = ref<string | null>(null)
const ownerInputValue = ref('')
const ownerInputRef = ref<HTMLInputElement>()

// 内联编辑状态 - PL
const editingPlKey = ref<string | null>(null)
const plInputValue = ref('')
const plInputRef = ref<HTMLInputElement>()

// 内联编辑状态 - 失败原因
const editingFailureReasonKey = ref<string | null>(null)
const failureReasonInputValue = ref('')
const failureReasonInputRef = ref<HTMLInputElement>()

const statusTagType = (status: string) => {
  switch (status) {
    case 'success': return 'success'
    case 'failure': return 'danger'
    case 'lost': return 'info'
    default: return 'info'
  }
}

const progressColor = (percent: number) => {
  if (percent >= 100) return '#67c23a'
  if (percent >= 50) return '#e6a23c'
  return '#f56c6c'
}

const formatTime = (time: string) => {
  const d = new Date(time)
  return d.toLocaleString('zh-CN', { hour12: false })
}

const fetchProjects = async () => {
  if (!appStore.currentProduct || !appStore.currentVersion) {
    ElMessage.warning('请先选择产品和版本')
    return
  }
  loading.value = true
  try {
    const res = await getUnifiedProjectList({
      product_name: appStore.currentProduct,
      version: appStore.currentVersion,
      page: pagination.value.page,
      size: pagination.value.size,
      status: (!filterStatus.value || filterStatus.value === 'all') ? undefined : filterStatus.value,
      search: filterSearch.value || undefined,
      owner: filterOwner.value || undefined,
      pl: filterPl.value || undefined
    })
    projects.value = res.data.items
    pagination.value.total = res.data.total
  } finally {
    loading.value = false
  }
}

const debouncedFetchProjects = debounce(() => {
  pagination.value.page = 1
  fetchProjects()
}, 300)

const resetFilters = () => {
  filterFeature.value = undefined
  filterStatus.value = 'all'
  filterSearch.value = ''
  filterOwner.value = ''
  filterPl.value = ''
  pagination.value.page = 1
  fetchProjects()
}

const fetchFeatures = async () => {
  if (!appStore.currentProduct || !appStore.currentVersion) return
  try {
    const res = await getFeatureList({ product_name: appStore.currentProduct, version: appStore.currentVersion })
    features.value = res.data.items
  } catch (e) { /* ignore */ }
}

const onFeatureChange = async (featureId: number | undefined) => {
  if (featureId) {
    try {
      const res = await getFeatureProjects(featureId)
      const featureProjectIds = new Set(res.data.items.map((p: any) => p.id))
      projects.value = projects.value.filter(p => p.project_id && featureProjectIds.has(p.project_id))
    } catch (e) { /* ignore */ }
  } else {
    fetchProjects()
  }
}

// 责任人编辑
const startEditOwner = (row: UnifiedProjectItem) => {
  editingOwnerKey.value = rowKey(row)
  ownerInputValue.value = row.owner || ''
  nextTick(() => ownerInputRef.value?.focus())
}

const saveOwner = async (row: UnifiedProjectItem) => {
  const newValue = ownerInputValue.value.trim()
  editingOwnerKey.value = null
  if (newValue === (row.owner || '')) return
  try {
    // 优先更新 Project，如果不存在则更新 ProjectConfig
    if (row.project_id) {
      await updateProject(row.project_id, { owner: newValue || null })
    }
    if (row.config_id) {
      await updateProjectConfig(row.config_id, { owner: newValue || null })
    }
    row.owner = newValue || null
    appStore.bumpProjectDataVersion()
    ElMessage.success('责任人已更新')
  } catch (e) {
    ElMessage.error('更新失败')
    await fetchProjects()
  }
}

// PL 编辑
const startEditPl = (row: UnifiedProjectItem) => {
  editingPlKey.value = rowKey(row)
  plInputValue.value = row.pl || ''
  nextTick(() => plInputRef.value?.focus())
}

const savePl = async (row: UnifiedProjectItem) => {
  const newValue = plInputValue.value.trim()
  editingPlKey.value = null
  if (newValue === (row.pl || '')) return
  try {
    if (row.project_id) {
      await updateProject(row.project_id, { pl: newValue || null })
    }
    if (row.config_id) {
      await updateProjectConfig(row.config_id, { pl: newValue || null })
    }
    row.pl = newValue || null
    appStore.bumpProjectDataVersion()
    ElMessage.success('PL已更新')
  } catch (e) {
    ElMessage.error('更新失败')
    await fetchProjects()
  }
}

// 失败原因编辑
const startEditFailureReason = (row: UnifiedProjectItem) => {
  editingFailureReasonKey.value = rowKey(row)
  failureReasonInputValue.value = row.failure_reason || ''
  nextTick(() => failureReasonInputRef.value?.focus())
}

const saveFailureReason = async (row: UnifiedProjectItem) => {
  const newValue = failureReasonInputValue.value.trim()
  editingFailureReasonKey.value = null
  if (newValue === (row.failure_reason || '')) return
  if (!row.project_id) {
    ElMessage.warning('该工程尚未有CI上报数据，无法编辑失败原因')
    return
  }
  try {
    await updateProject(row.project_id, { failure_reason: newValue || null })
    row.failure_reason = newValue || null
    appStore.bumpProjectDataVersion()
    ElMessage.success('失败原因已更新')
  } catch (e) {
    ElMessage.error('更新失败')
    await fetchProjects()
  }
}

const goToDetail = (row: UnifiedProjectItem) => {
  if (!row.project_id) {
    ElMessage.warning('该工程尚未有CI上报数据，无法查看详情')
    return
  }
  router.push(`/projects/${row.project_id}`)
}

// 新增弹窗
const addDialogVisible = ref(false)
const addForm = reactive({ project_name: '', pl: '', owner: '' })

const showAddDialog = () => {
  addForm.project_name = ''
  addForm.pl = ''
  addForm.owner = ''
  addDialogVisible.value = true
}

const doAdd = async () => {
  if (!appStore.currentProduct || !appStore.currentVersion) return
  if (!addForm.project_name) { ElMessage.warning('请输入工程名'); return }
  try {
    await createProject({
      product_name: appStore.currentProduct,
      version: appStore.currentVersion,
      project_name: addForm.project_name,
      pl: addForm.pl || undefined,
      owner: addForm.owner || undefined
    })
    ElMessage.success('新增成功')
    addDialogVisible.value = false
    appStore.bumpProjectDataVersion()
    fetchProjects()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '新增失败')
  }
}

// 删除工程
const doDelete = async (row: UnifiedProjectItem) => {
  try {
    await ElMessageBox.confirm(`确定删除工程"${row.project_name}"吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    // 同时删除两表中的记录
    if (row.project_id) {
      await deleteProject(row.project_id)
    }
    if (row.config_id) {
      await deleteProjectConfig(row.config_id)
    }
    ElMessage.success('已删除')
    appStore.bumpProjectDataVersion()
    fetchProjects()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

watch(() => [appStore.currentProduct, appStore.currentVersion], () => {
  pagination.value.page = 1
  fetchProjects()
  fetchFeatures()
}, { immediate: true })

// 监听工程数据版本号变化，跨页面同步刷新
watch(() => appStore.projectDataVersion, () => {
  fetchProjects()
})
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

/* 可编辑单元格样式 */
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

:deep(.el-table .el-input) {
  width: 100%;
}
:deep(.el-table .el-input__wrapper) {
  padding: 0 8px;
}
:deep(.el-table .el-input__inner) {
  height: 32px;
  line-height: 32px;
}
</style>
