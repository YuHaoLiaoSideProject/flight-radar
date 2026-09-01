<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import Navbar from './components/Navbar.vue'
import TopDeals from './components/TopDeals.vue'
import PriceChart from './components/PriceChart.vue'
import PriceTable from './components/PriceTable.vue'
import type { RootIndex, RouteDetail } from './types/flight'

const rootIndex = ref<RootIndex | null>(null)
const selectedRouteId = ref<string>('TPE-NRT')
const compareAll = ref<boolean>(false)

const routeDetailsMap = ref<Record<string, RouteDetail>>({})
const loading = ref<boolean>(true)
const routeLoading = ref<boolean>(false)
const error = ref<string | null>(null)

async function loadRootIndex() {
  try {
    loading.value = true
    const res = await fetch('./api/index.json')
    if (!res.ok) throw new Error('無法讀取頂層 api/index.json 索引檔')
    const data: RootIndex = await res.json()
    rootIndex.value = data
    
    if (data.routes && data.routes.length > 0) {
      selectedRouteId.value = data.config?.defaultRoute || data.routes[0].id
      await loadRouteDetail(selectedRouteId.value)
    }
  } catch (err: any) {
    error.value = err.message || '載入失敗'
  } finally {
    loading.value = false
  }
}

async function loadRouteDetail(routeId: string) {
  if (routeDetailsMap.value[routeId]) {
    return routeDetailsMap.value[routeId]
  }

  const routeSummary = rootIndex.value?.routes.find(r => r.id === routeId)
  if (!routeSummary) return null

  try {
    routeLoading.value = true
    const res = await fetch(`./${routeSummary.path}`)
    if (!res.ok) throw new Error(`無法讀取航線數據: ${routeSummary.path}`)
    const detail: RouteDetail = await res.json()
    routeDetailsMap.value[routeId] = detail
    return detail
  } catch (err: any) {
    console.error(err)
    return null
  } finally {
    routeLoading.value = false
  }
}

watch(compareAll, async (newVal) => {
  if (newVal && rootIndex.value) {
    for (const r of rootIndex.value.routes) {
      if (!routeDetailsMap.value[r.id]) {
        await loadRouteDetail(r.id)
      }
    }
  }
})

watch(selectedRouteId, async (newId) => {
  await loadRouteDetail(newId)
})

const currentRouteDetail = computed(() => {
  return routeDetailsMap.value[selectedRouteId.value] || null
})

const allLoadedRouteDetails = computed(() => {
  if (!rootIndex.value) return []
  return rootIndex.value.routes
    .map(r => routeDetailsMap.value[r.id])
    .filter((d): d is RouteDetail => d !== undefined)
})

onMounted(() => {
  loadRootIndex()
})
</script>

<template>
  <div class="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-blue-500 selection:text-white">
    <Navbar :updatedAt="rootIndex?.generatedAt || ''" />

    <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div v-if="loading" class="flex flex-col items-center justify-center py-24 space-y-4">
        <div class="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        <p class="text-slate-400 text-sm">正在載入 API 結構與航線數據...</p>
      </div>

      <div v-else-if="error" class="bg-rose-950/40 border border-rose-800 text-rose-200 p-6 rounded-2xl text-center my-12">
        <p class="font-semibold text-lg">⚠️ API 載入失敗</p>
        <p class="text-sm text-rose-300 mt-2">{{ error }}</p>
        <button @click="loadRootIndex" class="mt-4 px-4 py-2 bg-rose-600 hover:bg-rose-500 rounded-lg text-xs font-semibold">
          重新整理
        </button>
      </div>

      <div v-else-if="rootIndex">
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <div class="flex flex-wrap items-center gap-2 p-1.5 bg-slate-900/90 border border-slate-800 rounded-2xl w-fit">
            <button
              v-for="route in rootIndex.routes"
              :key="route.id"
              @click="selectedRouteId = route.id"
              class="px-4 py-2 rounded-xl text-xs font-medium transition-all duration-200 flex items-center space-x-2"
              :class="selectedRouteId === route.id && !compareAll
                ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'"
            >
              <span class="w-2 h-2 rounded-full" :style="{ backgroundColor: route.color }"></span>
              <span>{{ route.name }}</span>
            </button>
          </div>

          <button
            @click="compareAll = !compareAll"
            class="px-4 py-2 rounded-xl text-xs font-medium border transition-all duration-200 flex items-center space-x-2 w-fit"
            :class="compareAll
              ? 'bg-indigo-600/30 border-indigo-500 text-indigo-200'
              : 'bg-slate-900 border-slate-700 text-slate-300 hover:border-slate-600'"
          >
            <span>📊</span>
            <span>{{ compareAll ? '顯示單一航線' : '全航線疊加對比' }}</span>
          </button>
        </div>

        <div v-if="routeLoading && !currentRouteDetail" class="py-12 text-center text-slate-400 text-xs">
          載入航線詳細數據中...
        </div>

        <template v-else-if="currentRouteDetail">
          <TopDeals :activeRoute="currentRouteDetail" />
          <PriceChart
            :routes="allLoadedRouteDetails"
            :selectedRouteId="selectedRouteId"
            :compareAll="compareAll"
          />
          <PriceTable :activeRoute="currentRouteDetail" />
        </template>
      </div>
    </main>

    <footer class="border-t border-slate-900 bg-slate-950 py-6 text-center text-xs text-slate-500">
      <div class="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
        <p>Flight Radar · 分離式架構 (Raw Data ➔ Build API ➔ Static Web)</p>
        <p>原始資料已儲存於 <code>data/raw/</code> · API 自動建構於 <code>public/api/</code></p>
      </div>
    </footer>
  </div>
</template>
