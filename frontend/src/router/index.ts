import { createRouter, createWebHistory } from 'vue-router'
import Layout from '@/components/Layout.vue'
import Dashboard from '@/views/Dashboard.vue'
import ProjectList from '@/views/ProjectList.vue'
import ProjectDetail from '@/views/ProjectDetail.vue'
import ArchiveList from '@/views/ArchiveList.vue'
import ProjectConfig from '@/views/ProjectConfig.vue'
import UserManagement from '@/views/UserManagement.vue'

const routes = [
  {
    path: '/',
    component: Layout,
    children: [
      { path: '', redirect: '/dashboard' },
      { path: 'dashboard', component: Dashboard },
      { path: 'projects', component: ProjectList },
      { path: 'projects/:id', component: ProjectDetail, props: true },
      { path: 'archive', component: ArchiveList },
      { path: 'project-config', component: ProjectConfig },
      { path: 'user-management', component: UserManagement },
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫：仅做管理员页面访问控制
router.beforeEach((to, _from, next) => {
  // 权限管理页面仅管理员可访问
  if (to.path === '/user-management') {
    const isAdmin = localStorage.getItem('isAdmin') === 'true'
    if (!isAdmin) {
      next('/dashboard')
      return
    }
  }
  next()
})

export default router
