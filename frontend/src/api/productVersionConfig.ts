import client from './client'

export interface ProductVersionConfigItem {
  product_name: string
  version: string
  retention_days: number
}

export const getProductVersionConfig = (productName: string, version: string) => {
  return client.get<ProductVersionConfigItem>('/product-version-config', {
    params: { product_name: productName, version }
  })
}

export const updateProductVersionConfig = (productName: string, version: string, data: { retention_days: number }) => {
  return client.patch<ProductVersionConfigItem>('/product-version-config', data, {
    params: { product_name: productName, version }
  })
}
