<template>
  <div class="version-selector">
    <el-select
      v-model="selectedProduct"
      placeholder="选择产品"
      style="width: 180px; margin-right: 10px"
      filterable
    >
      <el-option
        v-for="item in products"
        :key="item.product_name"
        :label="item.product_name"
        :value="item.product_name"
      />
    </el-select>
    <el-select
      v-model="selectedVersion"
      placeholder="选择版本"
      style="width: 240px"
      filterable
      :disabled="!selectedProduct"
    >
      <el-option
        v-for="ver in currentVersions"
        :key="ver"
        :label="ver"
        :value="ver"
      />
    </el-select>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useAppStore } from '@/stores/app'
import { getProducts, type ProductVersionItem } from '@/api/projects'
import { saveUserPreferences } from '@/api/authAndBackup'
import { ElMessage } from 'element-plus'

const appStore = useAppStore()

const products = ref<ProductVersionItem[]>([])
const selectedProduct = ref<string>('')
const selectedVersion = ref<string>('')

const currentVersions = computed(() => {
  const product = products.value.find(p => p.product_name === selectedProduct.value)
  return product?.versions || []
})

const fetchProducts = async () => {
  if (appStore.isLoggedIn && !appStore.preferencesLoaded) {
    await appStore.loadPreferencesFromBackend()
  }
  try {
    const res = await getProducts()
    products.value = res.data.products

    if (appStore.currentProduct) {
      selectedProduct.value = appStore.currentProduct
    } else if (products.value.length > 0) {
      selectedProduct.value = products.value[0].product_name
    }
  } catch (e) {
    ElMessage.error('获取产品列表失败')
  }
}

watch(selectedProduct, (newProduct) => {
  if (!newProduct) {
    selectedVersion.value = ''
    return
  }

  const versions = currentVersions.value
  if (versions.length > 0) {
    if (appStore.currentProduct === newProduct && appStore.currentVersion) {
      selectedVersion.value = appStore.currentVersion
    } else {
      selectedVersion.value = versions[0]
    }
  } else {
    selectedVersion.value = ''
  }
}, { immediate: true })

watch([selectedProduct, selectedVersion], ([product, version]) => {
  if (product && version) {
    if (appStore.currentProduct !== product || appStore.currentVersion !== version) {
      appStore.setProduct(product)
      appStore.setVersion(version)
      if (appStore.isLoggedIn) {
        saveUserPreferences({ last_product: product, last_version: version }).catch(() => {})
      }
    }
  }
})

onMounted(() => {
  fetchProducts()
})
</script>

<style scoped>
.version-selector {
  display: flex;
  align-items: center;
}
</style>