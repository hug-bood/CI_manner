import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getCurrentUser } from '@/api/authAndBackup'

export const useAppStore = defineStore('app', () => {
  const currentProduct = ref<string>('')
  const currentVersion = ref<string>('')

  // 工程数据版本号：每次增/改/删操作后递增，用于跨页面同步刷新
  const projectDataVersion = ref(0)

  // 登录状态
  const token = ref<string>(localStorage.getItem('token') || '')
  const username = ref<string>(localStorage.getItem('username') || '')
  const isAdmin = ref<boolean>(localStorage.getItem('isAdmin') === 'true')
  const canCleanup = ref<boolean>(localStorage.getItem('canCleanup') === 'true')

  const isLoggedIn = computed(() => !!token.value)

  // 偏好是否已从后端加载（避免重复请求）
  const preferencesLoaded = ref(false)

  function setProduct(product: string) {
    currentProduct.value = product
  }

  function setVersion(version: string) {
    currentVersion.value = version
  }

  function setLoginInfo(newToken: string, newUser: { username: string; is_admin: boolean; can_cleanup: boolean }) {
    token.value = newToken
    username.value = newUser.username
    isAdmin.value = newUser.is_admin
    canCleanup.value = newUser.can_cleanup
    localStorage.setItem('token', newToken)
    localStorage.setItem('username', newUser.username)
    localStorage.setItem('isAdmin', String(newUser.is_admin))
    localStorage.setItem('canCleanup', String(newUser.can_cleanup))
  }

  function clearLoginInfo() {
    token.value = ''
    username.value = ''
    isAdmin.value = false
    canCleanup.value = false
    preferencesLoaded.value = false
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('isAdmin')
    localStorage.removeItem('canCleanup')
  }

  function bumpProjectDataVersion() {
    projectDataVersion.value++
  }

  async function loadPreferencesFromBackend() {
    if (preferencesLoaded.value || !token.value) return
    try {
      const res = await getCurrentUser()
      const user = res.data
      if (user.last_product) {
        currentProduct.value = user.last_product
      }
      if (user.last_version) {
        currentVersion.value = user.last_version
      }
      preferencesLoaded.value = true
    } catch (e) {
      // 未登录或请求失败，忽略
    }
  }

  return {
    currentProduct, currentVersion, setProduct, setVersion,
    projectDataVersion, bumpProjectDataVersion,
    token, username, isAdmin, canCleanup, isLoggedIn,
    setLoginInfo, clearLoginInfo,
    preferencesLoaded, loadPreferencesFromBackend
  }
})
