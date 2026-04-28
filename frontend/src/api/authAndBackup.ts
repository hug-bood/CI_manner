import client from './client'

export interface UserItem {
  id: number
  username: string
  is_admin: boolean
  can_cleanup: boolean
  last_product: string | null
  last_version: string | null
}

export interface LoginResponse {
  token: string
  user: UserItem
}

export const login = (username: string) => {
  return client.post<LoginResponse>('/auth/login', { username })
}

export const register = (username: string) => {
  return client.post<LoginResponse>('/auth/register', { username })
}

export const logout = () => {
  return client.post('/auth/logout')
}

export const checkAuth = () => {
  return client.get<{ has_users: boolean }>('/auth/check')
}

export const getUserList = () => {
  return client.get<UserItem[]>('/auth/users')
}

export const createUser = (username: string) => {
  return client.post<UserItem>('/auth/users', { username })
}

export const updateUser = (userId: number, data: { can_cleanup?: boolean }) => {
  return client.patch<UserItem>(`/auth/users/${userId}`, data)
}

export const deleteUser = (userId: number) => {
  return client.delete(`/auth/users/${userId}`)
}

export const deleteAllUsers = () => {
  return client.delete('/auth/users')
}

export const getCurrentUser = () => {
  return client.get<UserItem>('/auth/me')
}

export const saveUserPreferences = (data: { last_product?: string | null; last_version?: string | null }) => {
  return client.patch<UserItem>('/auth/me/preferences', data)
}

export const getBackupInfo = (productName?: string, version?: string) => {
  return client.get('/backup/info', { params: { product_name: productName, version } })
}

export const exportVersionData = (productName: string, version: string) => {
  return client.post('/backup/export', null, {
    params: { product_name: productName, version },
    responseType: 'blob'
  })
}

export const backupDatabase = () => {
  return client.post('/backup/db-backup')
}
