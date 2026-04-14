import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const currentProduct = ref<string>('')
  const currentVersion = ref<string>('')

  function setProduct(product: string) {
    currentProduct.value = product
  }

  function setVersion(version: string) {
    currentVersion.value = version
  }

  return { currentProduct, currentVersion, setProduct, setVersion }
})