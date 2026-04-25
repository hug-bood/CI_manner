<template>
  <div class="project-config">
    <h2>工程配置</h2>

    <el-row :gutter="20" class="action-row">
      <el-col :span="12">
        <el-button type="primary" size="small" @click="showAddDialog">新增配置</el-button>
        <el-button size="small" @click="triggerUpload">上传表格</el-button>
        <el-button size="small" @click="doDownload">下载表格</el-button>
        <input ref="fileInputRef" type="file" accept=".csv" style="display:none" @change="onFileChange" />
      </el-col>
    </el-row>

    <el-table :data="configs" stripe v-loading="loading" style="width: 100%">
      <el-table-column prop="project_name" label="工程" min-width="180" />
      <el-table-column label="PL" width="140">
        <template #default="{ row }">
          <div v-if="editingKey !== rowKey(row) || editingField !== 'pl'" class="editable-cell" :class="{ 'text-muted': !row.pl }" @click="startEdit(row, 'pl')">
            {{ row.pl || '点击填写' }}
          </div>
          <el-input v-else ref="editInputRef" v-model="editValue" size="small" @blur="saveEdit(row)" @keyup.enter="saveEdit(row)" />
        </template>
      </el-table-column>
      <el-table-column label="责任人" width="140">
        <template #default="{ row }">
          <div v-if="editingKey !== rowKey(row) || editingField !== 'owner'" class="editable-cell" :class="{ 'text-muted': !row.owner }" @click="startEdit(row, 'owner')">
            {{ row.owner || '点击填写' }}
          </div>
          <el-input v-else ref="editInputRef" v-model="editValue" size="small" @blur="saveEdit(row)" @keyup.enter="saveEdit(row)" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="80" fixed="right" align="center">
        <template #default="{ row }">
          <el-button type="danger" link size="small" @click="doDelete(row)">删除</el-button>
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

    <!-- 新增弹窗 -->
    <el-dialog v-model="addDialogVisible" title="新增工程配置" width="400px">
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
import { ref, reactive, watch, nextTick, onMounted } from 'vue'
import { useAppStore } from '@/stores/app'
import { getUnifiedProjectList, type UnifiedProjectItem } from '@/api/projects'
import { createProjectConfig, updateProjectConfig, deleteProjectConfig, uploadProjectConfigs, downloadProjectConfigs } from '@/api/projectConfigs'
import { updateProject, deleteProject } from '@/api/projects'
import { ElMessage, ElMessageBox } from 'element-plus'

const appStore = useAppStore()
const loading = ref(false)
const configs = ref<UnifiedProjectItem[]>([])
const pagination = ref({ page: 1, size: 20, total: 0 })
const fileInputRef = ref<HTMLInputElement>()

// 用 project_name 作为行唯一标识
const rowKey = (row: UnifiedProjectItem) => row.project_name

// 内联编辑
const editingKey = ref<string | null>(null)
const editingField = ref('')
const editValue = ref('')
const editInputRef = ref<HTMLInputElement>()

// 新增弹窗
const addDialogVisible = ref(false)
const addForm = reactive({ project_name: '', pl: '', owner: '' })

const fetchData = async () => {
  if (!appStore.currentProduct || !appStore.currentVersion) return
  loading.value = true
  try {
    const res = await getUnifiedProjectList({
      product_name: appStore.currentProduct,
      version: appStore.currentVersion,
      page: pagination.value.page,
      size: pagination.value.size
    })
    configs.value = res.data.items
    pagination.value.total = res.data.total
  } finally {
    loading.value = false
  }
}

const startEdit = (row: UnifiedProjectItem, field: string) => {
  editingKey.value = rowKey(row)
  editingField.value = field
  editValue.value = (row as any)[field] || ''
  nextTick(() => editInputRef.value?.focus())
}

const saveEdit = async (row: UnifiedProjectItem) => {
  const field = editingField.value
  editingKey.value = null
  editingField.value = ''

  const newVal = editValue.value.trim()
  if (newVal === ((row as any)[field] || '')) return
  try {
    // 同时更新两表
    if (row.project_id) {
      await updateProject(row.project_id, { [field]: newVal || null })
    }
    if (row.config_id) {
      await updateProjectConfig(row.config_id, { [field]: newVal || null })
    }
    ;(row as any)[field] = newVal || null
    appStore.bumpProjectDataVersion()
    ElMessage.success('已更新')
  } catch (e) { ElMessage.error('更新失败') }
}

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
    await createProjectConfig({
      product_name: appStore.currentProduct,
      version: appStore.currentVersion,
      project_name: addForm.project_name,
      pl: addForm.pl || undefined,
      owner: addForm.owner || undefined
    })
    ElMessage.success('新增成功')
    addDialogVisible.value = false
    appStore.bumpProjectDataVersion()
    fetchData()
  } catch (e) { ElMessage.error('新增失败') }
}

const doDelete = async (row: UnifiedProjectItem) => {
  try {
    await ElMessageBox.confirm(`确定删除工程"${row.project_name}"的配置吗？`, '提示', {
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
    fetchData()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const triggerUpload = () => {
  fileInputRef.value?.click()
}

const onFileChange = async (e: Event) => {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file || !appStore.currentProduct || !appStore.currentVersion) return
  try {
    const res = await uploadProjectConfigs(appStore.currentProduct, appStore.currentVersion, file)
    ElMessage.success(`导入${res.data.imported}条，更新${res.data.updated}条`)
    appStore.bumpProjectDataVersion()
    fetchData()
  } catch (e) { ElMessage.error('上传失败') }
  target.value = ''
}

const doDownload = async () => {
  if (!appStore.currentProduct || !appStore.currentVersion) return
  try {
    const res = await downloadProjectConfigs(appStore.currentProduct, appStore.currentVersion)
    const url = window.URL.createObjectURL(new Blob([res.data as any]))
    const a = document.createElement('a')
    a.href = url
    a.download = `project_config_${appStore.currentProduct}_${appStore.currentVersion}.csv`
    a.click()
    window.URL.revokeObjectURL(url)
  } catch (e) { ElMessage.error('下载失败') }
}

watch(() => [appStore.currentProduct, appStore.currentVersion], () => {
  pagination.value.page = 1
  fetchData()
}, { immediate: true })

// 监听工程数据版本号变化，跨页面同步刷新
watch(() => appStore.projectDataVersion, () => {
  fetchData()
})

onMounted(() => { if (appStore.currentProduct && appStore.currentVersion) fetchData() })
</script>

<style scoped>
.project-config h2 { margin-bottom: 20px; }
.action-row { margin-bottom: 20px; }
.pagination { margin-top: 20px; justify-content: flex-end; }
.editable-cell {
  min-height: 32px; line-height: 32px; padding: 0 8px; border-radius: 4px;
  cursor: text; transition: background-color 0.2s; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.editable-cell:hover { background-color: #f5f7fa; }
.text-muted { color: #c0c4cc; }
</style>
