<script setup lang="ts">
import { ref, computed } from 'vue'
import type { RouteDetail } from '../types/flight'
import { getGoogleFlightsUrl } from '../utils/url'

const props = defineProps<{
  activeRoute: RouteDetail
}>()

const filterOnlyHoliday = ref(false)
const searchQuery = ref('')

const filteredData = computed(() => {
  if (!props.activeRoute) return []
  return props.activeRoute.weeklyData.filter(item => {
    if (filterOnlyHoliday.value && !item.isHoliday) return false
    if (searchQuery.value) {
      const q = searchQuery.value.toLowerCase()
      const matchDate = item.departureDate.includes(q) || item.returnDate.includes(q)
      const matchTag = item.tag ? item.tag.toLowerCase().includes(q) : false
      return matchDate || matchTag
    }
    return true
  })
})

</script>

<template>
  <div v-if="activeRoute" class="bg-slate-800/60 border border-slate-700/60 rounded-2xl p-5 shadow-xl backdrop-blur">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
      <div>
        <h2 class="text-base font-semibold text-slate-200 flex items-center space-x-2">
          <span>📋</span>
          <span>【{{ activeRoute.name }}】未來 40 週完整票價明細表</span>
        </h2>
        <p class="text-xs text-slate-400 mt-0.5">
          共 {{ filteredData.length }} 組出發週末（週六出發、隔週日返程）
        </p>
      </div>

      <div class="flex flex-wrap items-center gap-2.5">
        <label class="flex items-center space-x-2 text-xs text-slate-300 bg-slate-900/60 border border-slate-700 px-3 py-1.5 rounded-lg cursor-pointer hover:border-slate-600 transition">
          <input type="checkbox" v-model="filterOnlyHoliday" class="rounded bg-slate-800 border-slate-700 text-blue-500 focus:ring-0" />
          <span>僅顯示節慶/連假</span>
        </label>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜尋月份或節慶 (如: 04, 春節)..."
          class="text-xs bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition w-44 sm:w-56"
        />
      </div>
    </div>

    <div class="overflow-x-auto rounded-xl border border-slate-700/70">
      <table class="w-full text-left text-xs text-slate-300">
        <caption class="sr-only">{{ activeRoute.name }} 未來 40 週完整票價明細表</caption>
        <thead class="bg-slate-900/80 text-slate-400 font-semibold border-b border-slate-700">
          <tr>
            <th scope="col" class="py-3 px-4">週次</th>
            <th scope="col" class="py-3 px-4">出發日期 (週六)</th>
            <th scope="col" class="py-3 px-4">返程日期 (隔週日)</th>
            <th scope="col" class="py-3 px-4">時段 / 節慶標籤</th>
            <th scope="col" class="py-3 px-4 text-right">來回最低價</th>
            <th scope="col" class="py-3 px-4 text-center">購票連結</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-800/80">
          <tr
            v-for="row in filteredData"
            :key="row.departureDate"
            class="hover:bg-slate-750/50 transition-colors"
            :class="row.price === activeRoute.stats?.minPrice ? 'bg-emerald-950/20' : (row.isHoliday ? 'bg-rose-950/10' : '')"
          >
            <td class="py-3 px-4 font-mono text-slate-400">#{{ String(row.weekIndex).padStart(2, '0') }}</td>
            <td class="py-3 px-4 font-medium text-slate-100">{{ row.departureDate }}</td>
            <td class="py-3 px-4 text-slate-400">{{ row.returnDate }}</td>
            <td class="py-3 px-4">
              <span
                v-if="row.tag"
                class="inline-block px-2 py-0.5 rounded text-[11px] font-medium"
                :class="row.tag.includes('春節') || row.tag.includes('清明') ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' : 'bg-amber-500/15 text-amber-300'"
              >
                {{ row.tag }}
              </span>
              <span v-else-if="row.price === activeRoute.stats?.minPrice" class="inline-block px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                ✨ 最低地板價
              </span>
              <span v-else class="text-slate-500">-</span>
            </td>
            <td class="py-3 px-4 text-right font-mono text-sm font-bold" :class="row.price === activeRoute.stats?.minPrice ? 'text-emerald-400' : 'text-slate-200'">
              NT$ {{ row.price?.toLocaleString() }}
            </td>
            <td class="py-3 px-4 text-center">
              <a
                :href="getGoogleFlightsUrl(activeRoute.origin, activeRoute.destination, row.departureDate, row.returnDate)"
                target="_blank"
                rel="noopener noreferrer"
                class="inline-flex items-center text-blue-400 hover:text-blue-300 transition"
              >
                前往查價 ↗
              </a>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
