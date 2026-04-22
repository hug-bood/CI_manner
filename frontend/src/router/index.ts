import { createRouter, createWebHistory } from 'vue-router'
import Layout from '@/components/Layout.vue'
import Dashboard from '@/views/Dashboard.vue'
import ProjectList from '@/views/ProjectList.vue'
import ProjectDetail from '@/views/ProjectDetail.vue'
import ArchiveList from '@/views/ArchiveList.vue'

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
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router