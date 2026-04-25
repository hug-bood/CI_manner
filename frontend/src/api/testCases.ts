import client from './client'

export interface TestCaseItem {
  id: number
  test_name: string
  status: string
  is_analyzed: boolean
  failure_reason: string | null
  owner: string | null
  pl: string | null
  report_date: string | null
  last_report_at: string | null
  is_source_code_issue: boolean
  dts_ticket: string | null
  dts_link: string | null
}

export interface TestCaseUpdateData {
  owner?: string | null
  pl?: string | null
  status?: string
  failure_reason?: string | null
  is_analyzed?: boolean
  is_source_code_issue?: boolean
  dts_ticket?: string | null
}

export interface TestCaseListParams {
  project_id?: number
  test_name?: string
  status?: string
  owner?: string
  pl?: string
  is_analyzed?: boolean
  is_source_code_issue?: boolean
  failed_only?: boolean
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

export const updateTestCase = (testCaseId: number, data: TestCaseUpdateData) => {
  return client.patch(`/test-cases/${testCaseId}`, data)
}

export interface AnalyzeRequest {
  product_name: string
  version: string
  project_name: string
  test_name: string
  failure_reason: string
}

export const analyzeTestCase = (data: AnalyzeRequest) => {
  return client.post('/test-cases/analyze', data)
}