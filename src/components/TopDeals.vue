<script setup lang="ts">
import type { RouteDetail } from '../types/flight'

const props = defineProps<{
  activeRoute: RouteDetail
}>()

function getGoogleFlightsUrl(origin: string, dest: string, dep: string, ret: string) {
  return `https://www.google.com/travel/flights?q=flights%20from%20${origin}%20to%20${dest}%20on%20${dep}%20returning%20${ret}`
}
</script>

<template>
  <div v-if="activeRoute" class="bg-slate-800/60 border border-slate-700/60 rounded-2xl p-5 mb-8 shadow-xl backdrop-blur">
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center space-x-2">
        <span class="text-amber-400 text-lg">🏆</span>
        <h2 class="text-base font-semibold text-slate-200">
          【{{ activeRoute.name }}】最便宜 Top 5 週末推薦
        </h2>
      </div>
      <span class="text-xs text-slate-400">
        常態地板價：<strong class="text-emerald-400 font-bold">NT$ {{ activeRoute.stats?.minPrice?.toLocaleString() }}</strong>
      </span>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
      <div
        v-for="(deal, idx) in activeRoute.topDeals"
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
            {{ deal.returnDate }} ({{ activeRoute.stayDays + 1 }}天{{ activeRoute.stayDays }}夜)
          </div>
        </div>

        <div class="mt-3 pt-2 border-t border-slate-800 flex items-center justify-between">
          <div>
            <div class="text-[10px] text-slate-400">來回含稅</div>
            <div class="text-base font-extrabold text-emerald-400">
              NT$ {{ deal.price?.toLocaleString() }}
            </div>
          </div>
          <a
            :href="getGoogleFlightsUrl(activeRoute.origin, activeRoute.destination, deal.departureDate, deal.returnDate)"
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
</template>
