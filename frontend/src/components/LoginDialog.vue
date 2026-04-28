<template>
  <el-dialog v-model="visible" title="需要登录" width="400px" :close-on-click-modal="false" @close="onClose">
    <p style="margin-bottom:16px;color:#909399">该操作需要管理员权限，请输入管理员账号登录。</p>
    <el-form :model="form" :rules="rules" ref="formRef" label-width="80px" @keyup.enter="doLogin">
      <el-form-item label="用户名" prop="username">
        <el-input v-model="form.username" placeholder="请输入管理员用户名" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" @click="doLogin" :loading="loading">登录</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useAppStore } from '@/stores/app'
import { login } from '@/api/authAndBackup'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'

const appStore = useAppStore()
const visible = ref(false)
const loading = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({ username: '' })

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, message: '用户名长度不能少于2位', trigger: 'blur' }
  ]
}

const doLogin = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const res = await login(form.username)
    appStore.setLoginInfo(res.data.token, res.data.user)
    const user = res.data.user
    if (user.last_product) {
      appStore.setProduct(user.last_product)
    }
    if (user.last_version) {
      appStore.setVersion(user.last_version)
    }
    ElMessage.success('登录成功')
    visible.value = false
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}

const onClose = () => {
  form.username = ''
}

const show = () => {
  form.username = ''
  visible.value = true
}

defineExpose({ show })
</script>
