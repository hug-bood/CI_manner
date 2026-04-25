import client from './client'

export interface ProjectConfigItem {
  id: number
  product_name: string
  version: string
  project_name: string
  pl: string | null
  owner: string | null
  retention_days: number
}

export interface ProjectConfigListResponse {
  items: ProjectConfigItem[]
  total: number
  page: number
  size: number
}

export const getProjectConfigList = (params: {
  product_name?: string
  version?: string
  project_name?: string
  page?: number
  size?: number
}) => {
  return client.get<ProjectConfigListResponse>('/project-configs', { params })
}

export const createProjectConfig = (data: {
  product_name: string
  version: string
  project_name: string
  pl?: string
  owner?: string
  retention_days?: number
}) => {
  return client.post<ProjectConfigItem>('/project-configs', data)
}

export const updateProjectConfig = (id: number, data: {
  pl?: string | null
  owner?: string | null
  retention_days?: number
}) => {
  return client.patch<ProjectConfigItem>(`/project-configs/${id}`, data)
}

export const deleteProjectConfig = (id: number) => {
  return client.delete(`/project-configs/${id}`)
}

export const uploadProjectConfigs = (productName: string, version: string, file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return client.post('/project-configs/upload', formData, {
    params: { product_name: productName, version },
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const downloadProjectConfigs = (productName: string, version: string) => {
  return client.get('/project-configs/download', {
    params: { product_name: productName, version },
    responseType: 'blob'
  })
}
