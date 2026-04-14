import client from './client'

export interface StatusUpdateRequest {
  product_name: string
  version: string
  project_name: string
  suite_name: string
  test_name: string
  status: 'pass' | 'fail' | 'lost' | 'processing'
}

export interface AnalyzeRequest {
  product_name: string
  version: string
  project_name: string
  suite_name: string
  test_name: string
  failure_reason: string
}

export const updateTestCaseStatus = (data: StatusUpdateRequest) => {
  return client.patch('/test-cases/status', data)
}

export const analyzeTestCase = (data: AnalyzeRequest) => {
  return client.post('/test-cases/analyze', data)
}

export interface TestCaseUpdateData {
  owner?: string | null
  pl?: string | null
  status?: string
  failure_reason?: string | null
  is_analyzed?: boolean
}

export const updateTestCase = (testCaseId: number, data: TestCaseUpdateData) => {
  return client.patch(`/test-cases/${testCaseId}`, data)
}

export interface TestCaseListParams {
  project_id?: number
  product_name?: string
  version?: string
  project_name?: string
  suite_name?: string
  test_name?: string
  status?: string
  owner?: string
  pl?: string
  is_analyzed?: boolean
  page?: number
  size?: number
}

export interface TestCaseListResponse {
  items: TestCaseItem[]
  total: number
  page: number
  size: number
}

export const getTestCaseList = (params: TestCaseListParams) => {
  return client.get<TestCaseListResponse>('/test-cases', { params })
}