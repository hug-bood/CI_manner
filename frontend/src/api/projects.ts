import client from './client'

export interface ProjectItem {
  id: number
  name: string
  status: 'success' | 'failure' | 'lost'
  owner: string | null
  pl: string | null
  failure_reason: string | null
  total_cases: number
  total_failed_cases: number
  analyzed_failed_cases: number
  failure_rate: number
  analysis_progress: number
  last_report_at: string | null
}

export interface ProjectListResponse {
  items: ProjectItem[]
  total: number
  page: number
  size: number
}

export interface SummaryResponse {
  total_projects: number
  failed_projects: number
  total_failed_cases: number
  average_failure_rate: number
  average_analysis_progress: number
  analysis_trend: (number | null)[]
}

export interface TestCaseItem {
  id: number
  suite_name: string
  test_name: string
  status: string
  is_analyzed: boolean
  failure_reason: string | null
  owner: string | null
  pl: string | null
  report_date: string | null
  last_report_at: string | null
}

export interface ProjectDetailResponse extends ProjectItem {
  test_cases: TestCaseItem[]
}

export const getSummary = (productName: string, version: string) => {
  const encodedVersion = encodeURIComponent(version)
  return client.get<SummaryResponse>(`/products/${productName}/versions/${encodedVersion}/summary`)
}

export const getProjectList = (
  productName: string,
  version: string,
  page: number = 1,
  size: number = 20,
  status?: string,
  search?: string,
  owner?: string,
  pl?: string
) => {
  const encodedVersion = encodeURIComponent(version)
  return client.get<ProjectListResponse>(`/products/${productName}/versions/${encodedVersion}/projects`, {
    params: { page, size, status, search, owner, pl }
  })
}

export const getProjectDetail = (projectId: number) => {
  return client.get<ProjectDetailResponse>(`/projects/${projectId}`)
}

export interface ProductVersionItem {
  product_name: string
  versions: string[]
}

export interface ProductsResponse {
  products: ProductVersionItem[]
}

export const getProducts = () => {
  return client.get<ProductsResponse>('/products')
}

export interface ProjectUpdateData {
  owner?: string | null
  pl?: string | null
  failure_reason?: string | null
}

export const updateProject = (projectId: number, data: ProjectUpdateData) => {
  return client.patch(`/projects/${projectId}`, data)
}

export const deleteProject = (projectId: number) => {
  return client.delete(`/projects/${projectId}`)
}

export interface ProjectCreateData {
  product_name: string
  version: string
  project_name: string
  owner?: string | null
  pl?: string | null
}

export const createProject = (data: ProjectCreateData) => {
  return client.post<ProjectItem>('/projects', data)
}

// ========== 统一工程查询接口 ==========

export interface UnifiedProjectItem {
  project_id: number | null       // Project 表的 id，不存在则为 null
  config_id: number | null        // ProjectConfig 表的 id，不存在则为 null
  product_name: string
  version: string
  project_name: string
  // 来自 Project
  status: string
  failure_reason: string | null
  total_cases: number
  total_failed_cases: number
  analyzed_failed_cases: number
  failure_rate: number
  analysis_progress: number
  last_report_at: string | null
  // 合并字段
  owner: string | null
  pl: string | null
}

export interface UnifiedProjectListResponse {
  items: UnifiedProjectItem[]
  total: number
  page: number
  size: number
}

export const getUnifiedProjectList = (params: {
  product_name: string
  version: string
  page?: number
  size?: number
  status?: string
  search?: string
  owner?: string
  pl?: string
}) => {
  return client.get<UnifiedProjectListResponse>('/unified-projects', { params })
}