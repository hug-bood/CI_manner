<template>
  <div class="login-page">
    <div class="login-card">
      <h2>CI 管理平台</h2>
      
      <!-- 初始化模式：创建首个管理员 -->
      <div v-if="!hasUsers" class="init-mode">
        <p class="hint">首次使用，请创建管理员账号</p>
        <el-form :model="form" :rules="usernameRules" ref="formRef" label-width="80px">
          <el-form-item label="用户名" prop="username">
            <el-input v-model="form.username" placeholder="请输入用户名" @keyup.enter="doInit" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="doInit" :loading="loading" style="width:100%">创建管理员并登录</el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 登录/注册模式 -->
      <div v-else>
        <!-- 登录表单 -->
        <div v-if="mode === 'login'">
          <el-form :model="form" :rules="usernameRules" ref="formRef" label-width="80px">
            <el-form-item label="用户名" prop="username">
              <el-input v-model="form.username" placeholder="请输入用户名" @keyup.enter="doLogin" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="doLogin" :loading="loading" style="width:100%">登录</el-button>
            </el-form-item>
          </el-form>
          <div class="switch-link">
            还没有账号？<el-link type="primary" @click="switchToRegister">立即注册</el-link>
          </div>
        </div>

        <!-- 注册表单 -->
        <div v-else>
          <el-form :model="form" :rules="usernameRules" ref="formRef" label-width="80px">
            <el-form-item label="用户名" prop="username">
              <el-input v-model="form.username" placeholder="请输入用户名" @keyup.enter="doRegister" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="doRegister" :loading="loading" style="width:100%">注册</el-button>
            </el-form-item>
          </el-form>
          <div class="switch-link">
            已有账号？<el-link type="primary" @click="switchToLogin">返回登录</el-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { login, register, checkAuth, createUser } from '@/api/authAndBackup'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'

const router = useRouter()
const appStore = useAppStore()
const loading = ref(false)
const hasUsers = ref(true)
const mode = ref<'login' | 'register'>('login')
const formRef = ref<FormInstance>()

const form = reactive({
  username: ''
})

const usernameRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, message: '用户名长度不能少于2位', trigger: 'blur' }
  ]
}

const switchToRegister = () => {
  mode.value = 'register'
  form.username = ''
}

const switchToLogin = () => {
  mode.value = 'login'
  form.username = ''
}

onMounted(async () => {
  if (appStore.isLoggedIn) {
    router.push('/dashboard')
    return
  }
  try {
    const res = await checkAuth()
    hasUsers.value = res.data.has_users
  } catch (e) {
    hasUsers.value = true
  }
})

const doInit = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await createUser(form.username)
    const loginRes = await login(form.username)
    appStore.setLoginInfo(loginRes.data.token, loginRes.data.user)
    ElMessage.success('管理员创建成功，已自动登录')
    router.push('/dashboard')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '初始化失败')
  } finally {
    loading.value = false
  }
}

const doLogin = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const res = await login(form.username)
    appStore.setLoginInfo(res.data.token, res.data.user)
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}

const doRegister = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const res = await register(form.username)
    appStore.setLoginInfo(res.data.token, res.data.user)
    ElMessage.success('注册成功，已自动登录')
    router.push('/dashboard')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.login-card {
  width: 420px;
  padding: 40px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
}
.login-card h2 {
  text-align: center;
  margin-bottom: 30px;
  color: #303133;
}
.hint {
  text-align: center;
  color: #e6a23c;
  margin-bottom: 20px;
  font-size: 14px;
}
.switch-link {
  text-align: center;
  margin-top: 16px;
  font-size: 14px;
  color: #909399;
}
</style>
