import client from './client'

export interface ArchiveItem {
  id: number
  product_name: string
  version: string
  project_name: string
  suite_name: string
  test_name: string
  failure_date: string
  first_failure_date: string
  consecutive_days: number
  status: string
  failure_reason: string | null
  owner: string | null
  pl: string | null
}

export interface ArchiveListResponse {
  items: ArchiveItem[]
  total: number
  page: number
  size: number
}

export const getArchiveList = (params: {
  product_name?: string
  version?: string
  project_name?: string
  suite_name?: string
  test_name?: string
  status?: string
  owner?: string
  pl?: string
  page?: number
  size?: number
}) => {
  return client.get<ArchiveListResponse>('/archive/failures', { params })
}