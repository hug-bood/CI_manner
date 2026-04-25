<template>
  <div class="user-management">
    <h2>权限管理</h2>

    <el-row :gutter="20" class="action-row">
      <el-col :span="12">
        <el-button type="primary" size="small" @click="showAddDialog">新增用户</el-button>
        <el-button type="danger" size="small" @click="doDeleteAll" :disabled="!isAdmin">删除所有用户</el-button>
      </el-col>
      <el-col :span="12" style="text-align:right">
        <el-button type="warning" size="small" @click="doBackup">数据库备份</el-button>
        <el-button type="success" size="small" @click="doExport" :disabled="!appStore.currentProduct || !appStore.currentVersion">导出版本数据</el-button>
      </el-col>
    </el-row>

    <el-table :data="users" stripe v-loading="loading" style="width: 100%">
      <el-table-column prop="username" label="用户名" min-width="150" />
      <el-table-column label="管理员" width="100" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.is_admin" type="danger">管理员</el-tag>
          <el-tag v-else type="info">普通用户</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="清理权限" width="120" align="center">
        <template #default="{ row }">
          <el-switch v-model="row.can_cleanup" @change="(val: boolean) => toggleCleanup(row, val)" :disabled="!isAdmin" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100" align="center">
        <template #default="{ row }">
          <el-button type="danger" link size="small" @click="doDelete(row)" :disabled="!isAdmin || row.is_admin">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新增用户弹窗 -->
    <el-dialog v-model="addDialogVisible" title="新增用户" width="350px">
      <el-form :model="addForm" label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="addForm.username" placeholder="请输入用户名" />
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
import { ref, reactive, computed, onMounted } from 'vue'
import { useAppStore } from '@/stores/app'
import { getUserList, createUser, updateUser, deleteUser, deleteAllUsers, getCurrentUser, exportVersionData, backupDatabase, type UserItem } from '@/api/authAndBackup'
import { ElMessage, ElMessageBox } from 'element-plus'

const appStore = useAppStore()
const loading = ref(false)
const users = ref<UserItem[]>([])
const currentUser = ref<UserItem | null>(null)
const isAdmin = computed(() => currentUser.value?.is_admin)

const addDialogVisible = ref(false)
const addForm = reactive({ username: '' })

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getUserList()
    users.value = res.data
  } catch (e) { ElMessage.error('获取用户列表失败') }
  finally { loading.value = false }
}

const fetchCurrentUser = async () => {
  try {
    const res = await getCurrentUser()
    currentUser.value = res.data
  } catch (e) { /* not logged in */ }
}

const showAddDialog = () => {
  addForm.username = ''
  addDialogVisible.value = true
}

const doAdd = async () => {
  if (!addForm.username.trim()) { ElMessage.warning('请输入用户名'); return }
  try {
    await createUser(addForm.username.trim())
    ElMessage.success('用户已创建')
    addDialogVisible.value = false
    fetchData()
  } catch (e) { ElMessage.error('创建失败') }
}

const toggleCleanup = async (row: UserItem, val: boolean) => {
  try {
    await updateUser(row.id, { can_cleanup: val })
    ElMessage.success('权限已更新')
  } catch (e) { ElMessage.error('更新失败') }
}

const doDelete = async (row: UserItem) => {
  try {
    await deleteUser(row.id)
    ElMessage.success('用户已删除')
    fetchData()
  } catch (e) { ElMessage.error('删除失败') }
}

const doDeleteAll = async () => {
  try {
    await ElMessageBox.confirm('确定要删除所有用户吗？此操作不可恢复，您也将被登出。', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteAllUsers()
    appStore.clearLoginInfo()
    ElMessage.success('所有用户已删除')
    window.location.href = '/login'
  } catch (e: any) {
    if (e !== 'cancel') { ElMessage.error('删除失败') }
  }
}

const doBackup = async () => {
  try {
    await backupDatabase()
    ElMessage.success('数据库备份完成')
  } catch (e) { ElMessage.error('备份失败') }
}

const doExport = async () => {
  if (!appStore.currentProduct || !appStore.currentVersion) return
  try {
    const res = await exportVersionData(appStore.currentProduct, appStore.currentVersion)
    const url = window.URL.createObjectURL(new Blob([res.data as any]))
    const a = document.createElement('a')
    a.href = url
    a.download = `backup_${appStore.currentProduct}_${appStore.currentVersion}.json`
    a.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e) { ElMessage.error('导出失败') }
}

onMounted(() => {
  fetchCurrentUser()
  fetchData()
})
</script>

<style scoped>
.user-management h2 { margin-bottom: 20px; }
.action-row { margin-bottom: 20px; }
</style>
