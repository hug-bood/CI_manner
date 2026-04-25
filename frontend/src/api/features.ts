import client from './client'

export interface FeatureItem {
  id: number
  product_name: string
  version: string
  feature_name: string
  description: string | null
}

export interface FeatureListResponse {
  items: FeatureItem[]
  total: number
}

export const getFeatureList = (params: { product_name?: string; version?: string }) => {
  return client.get<FeatureListResponse>('/features', { params })
}

export const createFeature = (data: { product_name: string; version: string; feature_name: string; description?: string }) => {
  return client.post<FeatureItem>('/features', data)
}

export const updateFeature = (id: number, data: { feature_name?: string; description?: string }) => {
  return client.patch<FeatureItem>(`/features/${id}`, data)
}

export const deleteFeature = (id: number) => {
  return client.delete(`/features/${id}`)
}

export const bindProjectFeature = (projectId: number, featureId: number) => {
  return client.post('/features/bind', { project_id: projectId, feature_id: featureId })
}

export const unbindProjectFeature = (projectId: number, featureId: number) => {
  return client.post('/features/unbind', { project_id: projectId, feature_id: featureId })
}

export const getFeatureProjects = (featureId: number) => {
  return client.get(`/features/projects/${featureId}`)
}
