<template>
  <el-container class="layout">
    <el-header class="header">
      <div class="title">CI 管理平台</div>
      <div class="header-right">
        <VersionSelector />
        <div class="user-info" v-if="appStore.isLoggedIn">
          <el-icon><UserIcon /></el-icon>
          <span class="username">{{ appStore.username }}</span>
          <el-tag v-if="appStore.isAdmin" type="danger" size="small" style="margin-left:6px">管理员</el-tag>
          <el-button type="text" size="small" @click="doLogout" style="color:white;margin-left:12px">登出</el-button>
        </div>
        <div class="user-info" v-else>
          <el-icon><UserIcon /></el-icon>
          <span class="username">游客</span>
          <el-button type="text" size="small" @click="showLogin" style="color:white;margin-left:12px">登录</el-button>
        </div>
      </div>
    </el-header>
    <el-container>
      <el-aside width="200px" class="aside">
        <el-menu router :default-active="$route.path" class="menu">
          <el-menu-item index="/dashboard">
            <el-icon><DataAnalysis /></el-icon>
            <span>仪表盘</span>
          </el-menu-item>
          <el-menu-item index="/projects">
            <el-icon><List /></el-icon>
            <span>工程列表</span>
          </el-menu-item>
          <el-menu-item index="/archive">
            <el-icon><Document /></el-icon>
            <span>历史归档</span>
          </el-menu-item>
          <el-menu-item index="/project-config">
            <el-icon><Setting /></el-icon>
            <span>工程配置</span>
          </el-menu-item>
          <el-menu-item index="/user-management" v-if="appStore.isAdmin">
            <el-icon><User /></el-icon>
            <span>权限管理</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      <el-main>
        <router-view />
      </el-main>
    </el-container>

    <!-- 全局登录弹窗 -->
    <LoginDialog ref="loginDialogRef" />
  </el-container>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useAppStore } from '@/stores/app'
import { logout } from '@/api/authAndBackup'
import VersionSelector from './VersionSelector.vue'
import LoginDialog from './LoginDialog.vue'
import { DataAnalysis, List, Document, Setting, User, User as UserIcon } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const appStore = useAppStore()
const loginDialogRef = ref<InstanceType<typeof LoginDialog>>()

const showLogin = () => {
  loginDialogRef.value?.show()
}

// 监听全局 401 事件，弹出登录对话框
const onAuthRequired = () => {
  loginDialogRef.value?.show()
}
onMounted(() => {
  window.addEventListener('auth-required', onAuthRequired)
})
onUnmounted(() => {
  window.removeEventListener('auth-required', onAuthRequired)
})

const doLogout = async () => {
  try {
    await logout()
  } catch (e) { /* ignore */ }
  appStore.clearLoginInfo()
  ElMessage.success('已登出')
}
</script>

<style scoped>
.layout {
  height: 100vh;
}
.header {
  background-color: #409eff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}
.title {
  font-size: 20px;
  font-weight: bold;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}
.user-info {
  display: flex;
  align-items: center;
  font-size: 14px;
}
.username {
  margin-left: 4px;
}
.aside {
  background-color: #f5f7fa;
}
.menu {
  height: 100%;
  border-right: none;
}
</style>
