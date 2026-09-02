<script setup lang="ts">
import { computed } from 'vue'
import type { RouteDetail, TopDealItem } from '../types/flight'
import { getGoogleFlightsUrl } from '../utils/url'

const props = defineProps<{
  routes: RouteDetail[]
  destination: string
}>()

// 把所有航司的 topDeals 合併，取最低價的 Top 5
interface EnrichedDeal extends TopDealItem {
  airlineName: string
  airlineColor: string
  routeId: string
}

const mergedTopDeals = computed<EnrichedDeal[]>(() => {
  const all: EnrichedDeal[] = []
  for (const route of props.routes) {
    for (const deal of route.topDeals) {
      all.push({
        ...deal,
        airlineName: route.airlineName,
        airlineColor: route.color,
        routeId: route.id,
      })
    }
  }
  // 按出發日 + 價格排序，取最低 5
  const sorted = all
    .filter(d => d.price != null)
    .sort((a, b) => (a.price ?? Infinity) - (b.price ?? Infinity))
  // 去重：同一天只保留最低價
  const seen = new Set<string>()
  const unique: EnrichedDeal[] = []
  for (const d of sorted) {
    if (!seen.has(d.departureDate)) {
      seen.add(d.departureDate)
      unique.push(d)
    }
  }
  return unique.slice(0, 5)
})

const destinationLabel = computed(() => {
  const labels: Record<string, string> = {
    NRT: '東京成田', KIX: '大阪關西', FUK: '福岡',
    HND: '東京羽田', OKA: '沖繩',
  }
  return labels[props.destination] || props.destination
})

// 找出各航司的地板價
const floorPrices = computed(() =>
  props.routes.map(r => ({
    airlineName: r.airlineName,
    color: r.color,
    minPrice: r.stats?.minPrice,
  }))
)
</script>

<template>
  <div v-if="mergedTopDeals.length" class="bg-slate-800/60 border border-slate-700/60 rounded-2xl p-5 mb-8 shadow-xl backdrop-blur">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between mb-4 gap-2">
      <div class="flex items-center space-x-2">
        <span class="text-amber-400 text-lg">🏆</span>
        <h2 class="text-base font-semibold text-slate-200">
          {{ destinationLabel }} 最便宜 Top 5（跨航司）
        </h2>
      </div>
      <div class="flex items-center gap-3">
        <div
          v-for="fp in floorPrices"
          :key="fp.airlineName"
          class="text-[11px] flex items-center gap-1"
        >
          <span class="w-2 h-2 rounded-full" :style="{ backgroundColor: fp.color }"></span>
          <span class="text-slate-400">{{ fp.airlineName }}：</span>
          <strong class="text-emerald-400 font-bold">NT$ {{ fp.minPrice?.toLocaleString() }}</strong>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
      <div
        v-for="(deal, idx) in mergedTopDeals"
        :key="deal.departureDate"
        class="relative bg-slate-900/90 border border-slate-700/80 rounded-xl p-4 flex flex-col justify-between hover:border-blue-500/50 hover:shadow-lg hover:shadow-blue-500/10 transition-all duration-200"
      >
        <div class="flex items-center justify-between mb-2">
          <span
            class="text-[11px] font-bold px-2 py-0.5 rounded-full"
            :class="idx === 0 ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' : 'bg-slate-800 text-slate-400'"
          >
            Top {{ idx + 1 }}
          </span>
          <span v-if="deal.tag" class="text-[10px] bg-rose-500/20 text-rose-300 px-2 py-0.5 rounded-full">
            {{ deal.tag }}
          </span>
        </div>

        <div class="my-2">
          <div class="text-sm font-semibold text-slate-100 flex items-center space-x-1">
            <span>{{ deal.departureDate }}</span>
            <span class="text-slate-500 text-xs">➔</span>
          </div>
          <div class="text-xs text-slate-400 mt-0.5">
            {{ deal.returnDate }}
          </div>
        </div>

        <div class="mt-3 pt-2 border-t border-slate-800">
          <div class="flex items-center justify-between">
            <div>
              <div class="flex items-center gap-1.5 mb-0.5">
                <span class="w-2 h-2 rounded-full" :style="{ backgroundColor: deal.airlineColor }"></span>
                <span class="text-[10px] text-slate-400">{{ deal.airlineName }}</span>
              </div>
              <div class="text-base font-extrabold text-emerald-400">
                NT$ {{ deal.price?.toLocaleString() }}
              </div>
            </div>
            <a
              :href="getGoogleFlightsUrl('TPE', destination, deal.departureDate, deal.returnDate)"
              target="_blank"
              rel="noopener noreferrer"
              class="text-xs bg-blue-600 hover:bg-blue-500 text-white px-2.5 py-1.5 rounded-lg font-medium transition shadow-sm"
            >
              搜尋 ↗
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
