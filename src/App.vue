<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import Navbar from './components/Navbar.vue'
import TopDeals from './components/TopDeals.vue'
import PriceChart from './components/PriceChart.vue'
import PriceTable from './components/PriceTable.vue'
import type { RootIndex, RouteMeta, RouteDetail, WeekItem } from './types/flight'

const rootIndex = ref<RootIndex | null>(null)
const selectedRouteId = ref<string>('TPE-NRT')
const compareAll = ref<boolean>(false)

const routeDetailsMap = ref<Record<string, RouteDetail>>({})
const loading = ref<boolean>(true)
const error = ref<string | null>(null)

// 用來追蹤每條航線的週載入狀態
const loadingProgress = ref<Record<string, { loaded: number; total: number }>>({})

async function loadRootIndex() {
  try {
    loading.value = true
    const res = await fetch('./api/index.json')
    if (!res.ok) throw new Error('無法讀取頂層 api/index.json 索引檔')
    const data: RootIndex = await res.json()
    rootIndex.value = data
    
    if (data.routes && data.routes.length > 0) {
      selectedRouteId.value = data.config?.defaultRoute || data.routes[0].id
      await loadRouteMeta(selectedRouteId.value)
    }
  } catch (err: any) {
    error.value = err.message || '載入失敗'
  } finally {
    loading.value = false
  }
}

async function loadRouteMeta(routeId: string): Promise<RouteDetail | null> {
  // 如果已載入完整資料，直接回傳
  if (routeDetailsMap.value[routeId]) {
    return routeDetailsMap.value[routeId]
  }

  const routeSummary = rootIndex.value?.routes.find(r => r.id === routeId)
  if (!routeSummary) return null

  try {
    // 載入 meta.json
    const metaPath = routeSummary.path.replace('/index.json', '/meta.json')
    const res = await fetch(`./${metaPath}`)
    if (!res.ok) throw new Error(`無法讀取航線 meta: ${metaPath}`)
    const meta: RouteMeta = await res.json()

    // 建立初始 RouteDetail
    const detail: RouteDetail = {
      ...meta,
      weeklyData: [],
      loadedWeeks: 0,
      totalWeeks: meta.weeksCount,
      isLoadingWeeks: false,
      loadProgress: 0
    }
    routeDetailsMap.value[routeId] = detail
    
    // 開始背景載入所有週資料
    loadAllWeeks(routeId)
    
    return detail
  } catch (err: any) {
    console.error(err)
    return null
  }
}

async function loadAllWeeks(routeId: string) {
  const detail = routeDetailsMap.value[routeId]
  if (!detail || detail.isLoadingWeeks) return

  const routeSummary = rootIndex.value?.routes.find(r => r.id === routeId)
  if (!routeSummary) return

  detail.isLoadingWeeks = true
  loadingProgress.value[routeId] = { loaded: 0, total: detail.totalWeeks }

  const weeksBasePath = routeSummary.path.replace('/index.json', '/weeks')
  
  // 從 topDeals 取得所有 departure date 作為週列表
  // 這裡我們需要知道所有週的 departure date
  // 先建立一個簡單的日期序列 (每週五出發)
  const meta = detail
  const startDate = new Date(meta.topDeals[0]?.departureDate || '2026-09-05')
  
  // 產生 40 週的日期列表
  const weekDates: string[] = []
  for (let i = 0; i < 40; i++) {
    const d = new Date(startDate)
    d.setDate(d.getDate() + i * 7)
    weekDates.push(d.toISOString().split('T')[0])
  }

  // 並行載入所有週
  const loadPromises = weekDates.map(async (dateStr) => {
    try {
      const res = await fetch(`./${weeksBasePath}/${dateStr}.json`)
      if (res.ok) {
        const weekData: WeekItem = await res.json()
        detail.weeklyData.push(weekData)
        detail.loadedWeeks++
        detail.loadProgress = Math.round((detail.loadedWeeks / detail.totalWeeks) * 100)
        loadingProgress.value[routeId].loaded = detail.loadedWeeks
      }
    } catch (err) {
      console.warn(`載入週資料失敗: ${dateStr}`, err)
    }
  })

  await Promise.all(loadPromises)
  
  // 按 weekIndex 排序
  detail.weeklyData.sort((a, b) => a.weekIndex - b.weekIndex)
  detail.isLoadingWeeks = false
  detail.loadProgress = 100
}

watch(compareAll, async (newVal) => {
  if (newVal && rootIndex.value) {
    for (const r of rootIndex.value.routes) {
      if (!routeDetailsMap.value[r.id]) {
        await loadRouteMeta(r.id)
      }
    }
  }
})

watch(selectedRouteId, async (newId) => {
  await loadRouteMeta(newId)
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
        <p class="text-slate-400 text-sm">正在載入 API 結構...</p>
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

        <!-- 載入進度條 -->
        <div v-if="currentRouteDetail?.isLoadingWeeks" class="mb-6">
          <div class="flex items-center justify-between text-xs text-slate-400 mb-2">
            <span>載入週資料中...</span>
            <span>{{ currentRouteDetail.loadedWeeks }} / {{ currentRouteDetail.totalWeeks }} ({{ currentRouteDetail.loadProgress }}%)</span>
          </div>
          <div class="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
            <div 
              class="h-full bg-gradient-to-r from-blue-500 to-cyan-400 transition-all duration-300 ease-out"
              :style="{ width: `${currentRouteDetail.loadProgress}%` }"
            ></div>
          </div>
        </div>

        <template v-if="currentRouteDetail">
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
