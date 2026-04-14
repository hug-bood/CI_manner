import axios from 'axios'
import { ElMessage } from 'element-plus'

const client = axios.create({
  baseURL: 'http://127.0.0.1:8000/api/v1',
  timeout: 10000,
})

client.interceptors.response.use(
  (response) => response,
  (error) => {
    ElMessage.error(error.response?.data?.detail || '请求失败')
    return Promise.reject(error)
  }
)

export default client