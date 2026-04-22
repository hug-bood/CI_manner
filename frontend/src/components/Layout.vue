<template>
  <el-container class="layout">
    <el-header class="header">
      <div class="title">CI 管理平台</div>
      <VersionSelector />
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
        </el-menu>
      </el-aside>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import VersionSelector from './VersionSelector.vue'
import { DataAnalysis, List, Document } from '@element-plus/icons-vue'
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
.aside {
  background-color: #f5f7fa;
}
.menu {
  height: 100%;
  border-right: none;
}
</style>