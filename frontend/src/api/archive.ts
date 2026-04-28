import client from './client'

export interface ArchiveItem {
  id: number
  product_name: string
  version: string
  project_name: string
  test_name: string
  failure_date: string
  first_failure_date: string
  consecutive_days: number
  consecutive_success_days: number
  status: string
  is_analyzed: boolean
  failure_reason: string | null
  owner: string | null
  pl: string | null
  feature_name: string | null
  is_probabilistic: boolean
}

export interface ArchiveListResponse {
  items: ArchiveItem[]
  total: number
  page: number
  size: number
}

export interface ArchiveListParams {
  product_name?: string
  version?: string
  project_name?: string
  test_name?: string
  status?: string
  owner?: string
  pl?: string
  feature_name?: string
  is_analyzed?: boolean
  is_probabilistic?: boolean
  consecutive_success_days_min?: number
  consecutive_success_days_max?: number
  page?: number
  size?: number
}

export interface ExecutionHistoryItem {
  id: number
  product_name: string
  version: string
  project_name: string
  test_name: string
  execution_date: string
  status: string
  failure_reason: string | null
}

export interface ExecutionHistoryResponse {
  items: ExecutionHistoryItem[]
  total: number
}

export const getArchiveList = (params: ArchiveListParams) => {
  return client.get<ArchiveListResponse>('/archive/failures', { params })
}

export const getProbabilisticFailures = (params: ArchiveListParams) => {
  return client.get<ArchiveListResponse>('/archive/probabilistic-failures', { params })
}

export const updateArchiveFailure = (id: number, data: {
  is_analyzed?: boolean
  failure_reason?: string | null
  is_probabilistic?: boolean
  owner?: string | null
}) => {
  return client.patch(`/archive/failures/${id}`, data)
}

export interface CleanupItem {
  id: number
  project_name: string
  test_name: string
  consecutive_success_days: number
  is_analyzed: boolean
  failure_date: string
  feature_name: string | null
}

export interface CleanupListResponse {
  items: CleanupItem[]
  retention_days: number
}

export const getCleanupList = (productName: string, version: string) => {
  return client.get<CleanupListResponse>('/archive/failures/cleanup-list', {
    params: { product_name: productName, version }
  })
}

export const cleanupArchiveFailures = (ids: number[]) => {
  return client.post<{ message: string; count: number }>('/archive/failures/cleanup', { ids })
}

export const getExecutionHistory = (params: {
  product_name: string
  version: string
  project_name?: string
  test_name: string
  page?: number
  size?: number
}) => {
  return client.get<ExecutionHistoryResponse>('/archive/execution-history', { params })
}
