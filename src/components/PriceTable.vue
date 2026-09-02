<script setup lang="ts">
import { ref, computed } from 'vue'
import type { RouteDetail } from '../types/flight'
import { getGoogleFlightsUrl } from '../utils/url'

const props = defineProps<{
  routes: RouteDetail[]
  destination: string
}>()

const filterOnlyHoliday = ref(false)
const searchQuery = ref('')

const destinationLabel = computed(() => {
  const labels: Record<string, string> = {
    NRT: '東京成田', KIX: '大阪關西', FUK: '福岡',
    HND: '東京羽田', OKA: '沖繩',
  }
  return labels[props.destination] || props.destination
})

// 取最長的 weeklyData 作為基準（通常是華航 40 週）
const baseRoute = computed(() =>
  props.routes.reduce((a, b) => a.weeklyData.length >= b.weeklyData.length ? a : b)
)

// 建立每週的跨航司比較資料
interface WeekRow {
  weekIndex: number
  departureDate: string
  returnDate: string
  tag: string | null
  isHoliday: boolean
  airlines: {
    routeId: string
    airlineName: string
    color: string
    price: number | null
  }[]
  lowestPrice: number | null
  lowestAirline: string
}

const weekRows = computed<WeekRow[]>(() => {
  const base = baseRoute.value
  if (!base) return []

  return base.weeklyData.map(baseWeek => {
    const airlines = props.routes.map(route => {
      const weekData = route.weeklyData.find(w => w.weekIndex === baseWeek.weekIndex)
      return {
        routeId: route.id,
        airlineName: route.airlineName,
        color: route.color,
        price: weekData?.price ?? null,
      }
    })

    const validPrices = airlines.filter(a => a.price != null)
    const lowest = validPrices.length > 0
      ? validPrices.reduce((a, b) => a.price! < b.price! ? a : b)
      : null

    return {
      weekIndex: baseWeek.weekIndex,
      departureDate: baseWeek.departureDate,
      returnDate: baseWeek.returnDate,
      tag: baseWeek.tag,
      isHoliday: baseWeek.isHoliday,
      airlines,
      lowestPrice: lowest?.price ?? null,
      lowestAirline: lowest?.airlineName ?? '',
    }
  })
})

const filteredData = computed(() => {
  return weekRows.value.filter(row => {
    if (filterOnlyHoliday.value && !row.isHoliday) return false
    if (searchQuery.value) {
      const q = searchQuery.value.toLowerCase()
      const matchDate = row.departureDate.includes(q) || row.returnDate.includes(q)
      const matchTag = row.tag ? row.tag.toLowerCase().includes(q) : false
      return matchDate || matchTag
    }
    return true
  })
})

// 全局最低價
const globalMinPrice = computed(() => {
  const all = weekRows.value.map(r => r.lowestPrice).filter((p): p is number => p != null)
  return all.length > 0 ? Math.min(...all) : null
})

function getAirlinePrice(row: WeekRow, routeId: string) {
  return row.airlines.find(a => a.routeId === routeId)
}
</script>

<template>
  <div v-if="routes.length" class="bg-slate-800/60 border border-slate-700/60 rounded-2xl p-5 shadow-xl backdrop-blur">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
      <div>
        <h2 class="text-base font-semibold text-slate-200 flex items-center space-x-2">
          <span>📋</span>
          <span>{{ destinationLabel }} 未來 40 週完整票價明細</span>
        </h2>
        <p class="text-xs text-slate-400 mt-0.5">
          共 {{ filteredData.length }} 週 ·
          <span v-for="(r, idx) in routes" :key="r.id">
            <span class="w-2 h-2 rounded-full inline-block" :style="{ backgroundColor: r.color }"></span>
            {{ r.airlineName }}<span v-if="idx < routes.length - 1"> vs </span>
          </span>
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
        <caption class="sr-only">{{ destinationLabel }} 未來 40 週完整票價明細表</caption>
        <thead class="bg-slate-900/80 text-slate-400 font-semibold border-b border-slate-700">
          <tr>
            <th scope="col" class="py-3 px-3">週次</th>
            <th scope="col" class="py-3 px-3">出發 (週六)</th>
            <th scope="col" class="py-3 px-3">返程 (隔週日)</th>
            <th scope="col" class="py-3 px-3">節慶標籤</th>
            <th
              v-for="route in routes"
              :key="route.id"
              scope="col"
              class="py-3 px-3 text-right"
            >
              <div class="flex items-center justify-end gap-1.5">
                <span class="w-2 h-2 rounded-full" :style="{ backgroundColor: route.color }"></span>
                <span>{{ route.airlineName }}</span>
              </div>
            </th>
            <th scope="col" class="py-3 px-3 text-center">購票</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-800/80">
          <tr
            v-for="row in filteredData"
            :key="row.departureDate"
            class="hover:bg-slate-750/50 transition-colors"
            :class="row.lowestPrice === globalMinPrice ? 'bg-emerald-950/20' : (row.isHoliday ? 'bg-rose-950/10' : '')"
          >
            <td class="py-3 px-3 font-mono text-slate-400">#{{ String(row.weekIndex).padStart(2, '0') }}</td>
            <td class="py-3 px-3 font-medium text-slate-100">{{ row.departureDate }}</td>
            <td class="py-3 px-3 text-slate-400">{{ row.returnDate }}</td>
            <td class="py-3 px-3">
              <span
                v-if="row.tag"
                class="inline-block px-2 py-0.5 rounded text-[11px] font-medium"
                :class="row.tag.includes('春節') || row.tag.includes('清明') ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' : 'bg-amber-500/15 text-amber-300'"
              >
                {{ row.tag }}
              </span>
              <span v-else-if="row.lowestPrice === globalMinPrice" class="inline-block px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                ✨ 全航司最低
              </span>
              <span v-else class="text-slate-500">-</span>
            </td>
            <td
              v-for="route in routes"
              :key="route.id"
              class="py-3 px-3 text-right font-mono text-sm"
            >
              <template v-if="getAirlinePrice(row, route.id)?.price != null">
                <span
                  class="font-bold"
                  :class="getAirlinePrice(row, route.id)?.price === row.lowestPrice
                    ? 'text-emerald-400'
                    : 'text-slate-200'"
                >
                  NT$ {{ getAirlinePrice(row, route.id)?.price?.toLocaleString() }}
                </span>
              </template>
              <span v-else class="text-slate-600 text-[11px]">未開賣</span>
            </td>
            <td class="py-3 px-3 text-center">
              <a
                :href="getGoogleFlightsUrl('TPE', destination, row.departureDate, row.returnDate)"
                target="_blank"
                rel="noopener noreferrer"
                class="inline-flex items-center text-blue-400 hover:text-blue-300 transition"
              >
                查價 ↗
              </a>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
