<template>
  <div class="archive-list">
    <h2>历史归档</h2>

    <!-- 页签切换 -->
    <el-tabs v-model="activeTab" @tab-change="onTabChange">
      <el-tab-pane label="失败归档" name="failures" />
      <el-tab-pane label="概率失败" name="probabilistic" />
    </el-tabs>

    <!-- 筛选栏 -->
    <el-form :inline="true" class="filter-form">
      <el-form-item label="特性">
        <el-select v-model="filter.feature_name" placeholder="全部" clearable size="small" style="width:140px" @change="fetchData">
          <el-option v-for="f in features" :key="f.id" :label="f.feature_name" :value="f.feature_name" />
        </el-select>
      </el-form-item>
      <el-form-item label="工程名">
        <el-input v-model="filter.project_name" placeholder="工程名" clearable size="small" @input="debouncedFetch" />
      </el-form-item>
      <el-form-item label="用例名">
        <el-input v-model="filter.test_name" placeholder="用例名" clearable size="small" @input="debouncedFetch" />
      </el-form-item>
      <el-form-item label="PL">
        <el-input v-model="filter.pl" placeholder="PL" clearable size="small" @input="debouncedFetch" />
      </el-form-item>
      <el-form-item label="分析状态">
        <el-select v-model="filter.is_analyzed" placeholder="全部" clearable size="small" style="width:110px" @change="fetchData">
          <el-option label="已分析" :value="true" />
          <el-option label="未分析" :value="false" />
        </el-select>
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
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="未分析数" :value="unanalyzedCount" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="retention-card">
            <div class="retention-label">已修复用例保留天数</div>
            <div v-if="!editingRetention" class="retention-value" :class="{ 'retention-readonly': !isAdmin }" @click="isAdmin && startEditRetention()">
              {{ retentionDays }}天
              <el-icon v-if="isAdmin" style="margin-left:4px;cursor:pointer;color:#409eff"><Edit /></el-icon>
            </div>
            <div v-else class="retention-edit">
              <el-input-number v-model="retentionDaysInput" size="small" :min="1" :max="365" style="width:100px" />
              <el-button type="primary" size="small" @click="saveRetention" style="margin-left:4px">确定</el-button>
              <el-button size="small" @click="editingRetention = false" style="margin-left:4px">取消</el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 操作栏 -->
    <el-row class="action-row">
      <el-button type="danger" size="small" @click="showCleanupDialog" :disabled="!canCleanup">人工清理</el-button>
      <span class="action-hint" v-if="canCleanup">将清理已分析且连续成功天数 >= {{ retentionDays }}天的归档记录</span>
    </el-row>

    <!-- 数据表格 -->
    <el-table :data="items" stripe v-loading="loading" style="width: 100%">
      <el-table-column prop="feature_name" label="特性" width="120" />
      <el-table-column prop="project_name" label="工程名" width="140" />
      <el-table-column prop="test_name" label="用例名" min-width="180" />
      <el-table-column prop="pl" label="PL" width="80" />
      <el-table-column label="分析状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="row.is_analyzed ? 'success' : 'warning'" style="cursor:pointer" @click="toggleAnalyzed(row)">
            {{ row.is_analyzed ? '已分析' : '未分析' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="failure_date" label="失败日期" width="110" />
      <el-table-column prop="first_failure_date" label="起始日期" width="110" />
      <el-table-column prop="consecutive_days" label="连续失败" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="consecutiveTagType(row.consecutive_days)">{{ row.consecutive_days }}天</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="失败原因" min-width="160">
        <template #default="{ row }">
          <div v-if="editingKey !== row.id || editingField !== 'failure_reason'" class="editable-cell" :class="{ 'text-muted': !row.failure_reason }" @click="startEdit(row, 'failure_reason')">
            {{ row.failure_reason || '点击填写' }}
          </div>
          <el-input v-else v-model="editValue" size="small" @blur="saveEdit(row)" @keyup.enter="saveEdit(row)" />
        </template>
      </el-table-column>
      <el-table-column label="责任人" width="110">
        <template #default="{ row }">
          <div v-if="editingKey !== row.id || editingField !== 'owner'" class="editable-cell" :class="{ 'text-muted': !row.owner }" @click="startEdit(row, 'owner')">
            {{ row.owner || '点击填写' }}
          </div>
          <el-input v-else v-model="editValue" size="small" @blur="saveEdit(row)" @keyup.enter="saveEdit(row)" />
        </template>
      </el-table-column>
      <el-table-column label="概率失败" width="80" align="center">
        <template #default="{ row }">
          <el-checkbox v-model="row.is_probabilistic" @change="(val: boolean) => onProbabilisticChange(row, val)" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120" fixed="right" align="center">
        <template #default="{ row }">
          <el-button type="primary" link size="small" @click="showHistory(row)">历史</el-button>
          <el-button type="primary" link size="small" @click="markAnalyzed(row)" v-if="!row.is_analyzed">标记已分析</el-button>
        </template>
      </el-table-column>
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

    <!-- 人工清理弹窗 -->
    <el-dialog v-model="cleanupDialogVisible" title="人工清理归档数据" width="700px" @open="fetchCleanupList">
      <p style="margin-bottom: 12px">可清理记录（已分析且连续成功天数 >= <b>{{ cleanupRetentionDays }}</b>天）：</p>
      <div v-loading="cleanupListLoading">
        <div v-if="cleanupList.length === 0" style="color: #909399; text-align: center; padding: 20px;">暂无可清理记录</div>
        <template v-else>
          <div style="margin-bottom: 8px;">
            <el-checkbox v-model="cleanupAllChecked" @change="onCleanupCheckAll">全选</el-checkbox>
            <span style="margin-left: 12px; color: #909399; font-size: 13px;">已选 {{ cleanupSelectedIds.length }} / {{ cleanupList.length }} 条</span>
          </div>
          <el-table :data="cleanupList" stripe max-height="350" @selection-change="onCleanupSelectionChange" ref="cleanupTableRef">
            <el-table-column type="selection" width="50" />
            <el-table-column prop="feature_name" label="特性" width="120" />
            <el-table-column prop="project_name" label="工程名" width="140" />
            <el-table-column prop="test_name" label="用例名" min-width="200" />
            <el-table-column prop="consecutive_success_days" label="连续成功天数" width="120" align="center" />
            <el-table-column prop="failure_date" label="失败日期" width="110" />
          </el-table>
        </template>
      </div>
      <template #footer>
        <el-button @click="cleanupDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="doCleanup" :loading="cleanupLoading" :disabled="cleanupSelectedIds.length === 0">确认清理（{{ cleanupSelectedIds.length }}条）</el-button>
      </template>
    </el-dialog>

    <!-- 清理结果弹窗 -->
    <el-dialog v-model="cleanupResultVisible" title="清理结果" width="500px">
      <p>{{ cleanupResultMessage }}</p>
      <template #footer>
        <el-button type="primary" @click="cleanupResultVisible = false">确定</el-button>
      </template>
    </el-dialog>

    <!-- 历史执行记录弹窗 -->
    <el-dialog v-model="historyDialogVisible" :title="`执行历史 - ${historyTestName}`" width="700px">
      <el-table :data="historyItems" stripe v-loading="historyLoading" max-height="400">
        <el-table-column prop="execution_date" label="执行日期" width="120" />
        <el-table-column prop="project_name" label="工程" width="140" />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 'pass' ? 'success' : 'danger'">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="failure_reason" label="失败原因" min-width="200" show-overflow-tooltip />
      </el-table>
      <el-pagination
        v-model:current-page="historyPagination.page"
        v-model:page-size="historyPagination.size"
        :total="historyPagination.total"
        :page-sizes="[20, 50, 200]"
        layout="total, sizes, prev, pager, next"
        @size-change="fetchHistoryData"
        @current-change="fetchHistoryData"
        style="margin-top: 12px; justify-content: flex-end;"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useAppStore } from '@/stores/app'
import { getArchiveList, getProbabilisticFailures, updateArchiveFailure, cleanupArchiveFailures, getExecutionHistory, getCleanupList, type ArchiveItem, type CleanupItem } from '@/api/archive'
import { getProductVersionConfig, updateProductVersionConfig } from '@/api/productVersionConfig'
import { getFeatureList, type FeatureItem } from '@/api/features'
import { getCurrentUser, type UserItem } from '@/api/authAndBackup'
import { ElMessage } from 'element-plus'
import { Edit } from '@element-plus/icons-vue'
import { debounce } from 'lodash-es'

const appStore = useAppStore()

const loading = ref(false)
const items = ref<ArchiveItem[]>([])
const pagination = ref({ page: 1, size: 20, total: 0 })
const activeTab = ref('failures')
const features = ref<FeatureItem[]>([])
const currentUser = ref<UserItem | null>(null)

const filter = reactive({
  feature_name: '',
  project_name: '',
  test_name: '',
  pl: '',
  is_analyzed: undefined as boolean | undefined,
})

// 保留天数（产品版本级别）
const retentionDays = ref(30)
const editingRetention = ref(false)
const retentionDaysInput = ref(30)

// 清理相关
const cleanupDialogVisible = ref(false)
const cleanupLoading = ref(false)
const canCleanup = computed(() => currentUser.value?.is_admin || currentUser.value?.can_cleanup)
const isAdmin = computed(() => currentUser.value?.is_admin)
const cleanupResultVisible = ref(false)
const cleanupResultMessage = ref('')
const cleanupList = ref<CleanupItem[]>([])
const cleanupListLoading = ref(false)
const cleanupSelectedIds = ref<number[]>([])
const cleanupAllChecked = ref(true)
const cleanupRetentionDays = ref(30)
const cleanupTableRef = ref<any>(null)

// 历史记录相关
const historyDialogVisible = ref(false)
const historyLoading = ref(false)
const historyItems = ref<any[]>([])
const historyTestName = ref('')
const historyRow = ref<ArchiveItem | null>(null)
const historyPagination = ref({ page: 1, size: 50, total: 0 })

// 内联编辑
const editingKey = ref<number | null>(null)
const editingField = ref('')
const editValue = ref('')

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

const unanalyzedCount = computed(() => {
  return items.value.filter(i => !i.is_analyzed).length
})

const fetchFeatures = async () => {
  if (!appStore.currentProduct || !appStore.currentVersion) return
  try {
    const res = await getFeatureList({ product_name: appStore.currentProduct, version: appStore.currentVersion })
    features.value = res.data.items
  } catch (e) { /* ignore */ }
}

const fetchCurrentUser = async () => {
  // 未登录时不调用API，避免触发401弹窗
  if (!appStore.isLoggedIn) return
  try {
    const res = await getCurrentUser()
    currentUser.value = res.data
  } catch (e) { /* ignore */ }
}

const fetchRetentionDays = async () => {
  if (!appStore.currentProduct || !appStore.currentVersion) return
  try {
    const res = await getProductVersionConfig(appStore.currentProduct, appStore.currentVersion)
    retentionDays.value = res.data.retention_days
  } catch (e) { /* use default */ }
}

const startEditRetention = () => {
  retentionDaysInput.value = retentionDays.value
  editingRetention.value = true
}

const saveRetention = async () => {
  if (!appStore.currentProduct || !appStore.currentVersion) return
  try {
    await updateProductVersionConfig(appStore.currentProduct, appStore.currentVersion, { retention_days: retentionDaysInput.value })
    retentionDays.value = retentionDaysInput.value
    editingRetention.value = false
    ElMessage.success('保留天数已更新')
  } catch (e) {
    ElMessage.error('更新失败')
  }
}

const fetchData = async () => {
  if (!appStore.currentProduct || !appStore.currentVersion) {
    ElMessage.warning('请先选择产品和版本')
    return
  }
  loading.value = true
  try {
    const params = {
      product_name: appStore.currentProduct,
      version: appStore.currentVersion,
      project_name: filter.project_name || undefined,
      test_name: filter.test_name || undefined,
      pl: filter.pl || undefined,
      feature_name: filter.feature_name || undefined,
      is_analyzed: filter.is_analyzed,
      page: pagination.value.page,
      size: pagination.value.size
    }
    const apiFn = activeTab.value === 'probabilistic' ? getProbabilisticFailures : getArchiveList
    const res = await apiFn(params)
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

const onTabChange = () => {
  pagination.value.page = 1
  fetchData()
}

const resetFilters = () => {
  filter.feature_name = ''
  filter.project_name = ''
  filter.test_name = ''
  filter.pl = ''
  filter.is_analyzed = undefined
  pagination.value.page = 1
  fetchData()
}

const onProbabilisticChange = async (row: ArchiveItem, val: boolean) => {
  try {
    await updateArchiveFailure(row.id, { is_probabilistic: val })
    ElMessage.success('已更新')
  } catch (e) {
    ElMessage.error('更新失败')
  }
}

const markAnalyzed = async (row: ArchiveItem) => {
  try {
    await updateArchiveFailure(row.id, { is_analyzed: true })
    row.is_analyzed = true
    ElMessage.success('已标记为已分析')
  } catch (e) {
    ElMessage.error('标记失败')
  }
}

const toggleAnalyzed = async (row: ArchiveItem) => {
  const newValue = !row.is_analyzed
  try {
    await updateArchiveFailure(row.id, { is_analyzed: newValue })
    row.is_analyzed = newValue
    ElMessage.success(newValue ? '已标记为已分析' : '已标记为未分析')
  } catch (e) {
    ElMessage.error('更新失败')
  }
}

const startEdit = (row: ArchiveItem, field: string) => {
  editingKey.value = row.id
  editingField.value = field
  editValue.value = (row as any)[field] || ''
}

const saveEdit = async (row: ArchiveItem) => {
  const field = editingField.value
  const newVal = editValue.value.trim()
  editingKey.value = null
  editingField.value = ''
  if (newVal === ((row as any)[field] || '')) return
  try {
    await updateArchiveFailure(row.id, { [field]: newVal || null })
    ;(row as any)[field] = newVal || null
    ElMessage.success('已更新')
  } catch (e) {
    ElMessage.error('更新失败')
  }
}

const showCleanupDialog = () => {
  cleanupDialogVisible.value = true
}

const fetchCleanupList = async () => {
  if (!appStore.currentProduct || !appStore.currentVersion) return
  cleanupListLoading.value = true
  cleanupSelectedIds.value = []
  cleanupAllChecked.value = true
  try {
    const res = await getCleanupList(appStore.currentProduct, appStore.currentVersion)
    cleanupList.value = res.data.items
    cleanupRetentionDays.value = res.data.retention_days
    cleanupSelectedIds.value = res.data.items.map(item => item.id)
  } catch (e) {
    ElMessage.error('获取可清理列表失败')
  } finally {
    cleanupListLoading.value = false
  }
}

const onCleanupSelectionChange = (selection: CleanupItem[]) => {
  cleanupSelectedIds.value = selection.map(item => item.id)
  cleanupAllChecked.value = selection.length === cleanupList.value.length
}

const onCleanupCheckAll = (val: boolean) => {
  if (val) {
    cleanupSelectedIds.value = cleanupList.value.map(item => item.id)
    cleanupTableRef.value?.clearSelection()
    cleanupList.value.forEach(row => cleanupTableRef.value?.toggleRowSelection(row, true))
  } else {
    cleanupSelectedIds.value = []
    cleanupTableRef.value?.clearSelection()
  }
}

const doCleanup = async () => {
  if (cleanupSelectedIds.value.length === 0) {
    ElMessage.warning('请至少选择一条记录')
    return
  }
  cleanupLoading.value = true
  try {
    const res = await cleanupArchiveFailures(cleanupSelectedIds.value)
    cleanupDialogVisible.value = false
    cleanupResultMessage.value = res.data.message
    cleanupResultVisible.value = true
    fetchData()
  } catch (e) {
    ElMessage.error('清理失败')
  } finally {
    cleanupLoading.value = false
  }
}

const showHistory = async (row: ArchiveItem) => {
  historyTestName.value = row.test_name
  historyRow.value = row
  historyPagination.value = { page: 1, size: 50, total: 0 }
  historyDialogVisible.value = true
  await fetchHistoryData()
}

const fetchHistoryData = async () => {
  if (!historyRow.value) return
  const row = historyRow.value
  historyLoading.value = true
  try {
    const res = await getExecutionHistory({
      product_name: row.product_name,
      version: row.version,
      project_name: row.project_name,
      test_name: row.test_name,
      page: historyPagination.value.page,
      size: historyPagination.value.size
    })
    historyItems.value = res.data.items
    historyPagination.value.total = res.data.total
  } catch (e) {
    ElMessage.error('获取历史记录失败')
  } finally {
    historyLoading.value = false
  }
}

watch(() => [appStore.currentProduct, appStore.currentVersion], () => {
  pagination.value.page = 1
  fetchData()
  fetchFeatures()
  fetchRetentionDays()
}, { immediate: true })

onMounted(() => {
  fetchCurrentUser()
  if (appStore.currentProduct && appStore.currentVersion) {
    fetchData()
    fetchFeatures()
    fetchRetentionDays()
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
.action-row {
  margin-bottom: 16px;
}
.action-hint {
  margin-left: 12px;
  color: #909399;
  font-size: 13px;
}
.pagination {
  margin-top: 20px;
  justify-content: flex-end;
}
.retention-card {
  text-align: center;
}
.retention-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}
.retention-value {
  font-size: 20px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
}
.retention-readonly {
  cursor: default;
}
.retention-edit {
  display: inline-flex;
  align-items: center;
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
</style>
