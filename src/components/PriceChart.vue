<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import {
  Chart,
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  Title,
  CategoryScale,
  Tooltip,
  Legend
} from 'chart.js'
import type { RouteDetail } from '../types/flight'
import type { ScriptableContext } from 'chart.js'

Chart.register(
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  Title,
  CategoryScale,
  Tooltip,
  Legend
)

const props = defineProps<{
  routes: RouteDetail[]
  selectedRouteId: string
  compareAll: boolean
}>()

const chartCanvas = ref<HTMLCanvasElement | null>(null)
let chartInstance: Chart | null = null

const activeRoutes = computed(() => {
  if (props.compareAll) {
    return props.routes
  }
  return props.routes.filter(r => r.id === props.selectedRouteId)
})

function buildDatasets() {
  return activeRoutes.value.map(route => ({
    label: route.name,
    data: route.weeklyData.map(w => w.price),
    borderColor: route.color,
    backgroundColor: route.color,
    borderWidth: 2.5,
    tension: 0.25,
    pointRadius: (ctx: ScriptableContext<'line'>) => {
      if (ctx.dataIndex === null || ctx.dataIndex === undefined) return 2.5
      const item = route.weeklyData[ctx.dataIndex]
      return item?.isHoliday ? 5 : 2.5
    },
    pointHoverRadius: 7,
    pointBackgroundColor: (ctx: ScriptableContext<'line'>) => {
      if (ctx.dataIndex === null || ctx.dataIndex === undefined) return route.color
      const item = route.weeklyData[ctx.dataIndex]
      return item?.isHoliday ? '#EF4444' : route.color
    }
  }))
}

function renderChart() {
  if (!chartCanvas.value || !props.routes.length) return

  const baseRoute = props.routes[0]
  const labels = baseRoute.weeklyData.map(w => w.label)
  const datasets = buildDatasets()

  if (chartInstance) {
    // Update existing chart in-place to avoid destroy/recreate overhead
    chartInstance.data.labels = labels
    chartInstance.data.datasets = datasets as typeof chartInstance.data.datasets
    chartInstance.options.plugins!.legend!.display = props.compareAll
    chartInstance.update('none')
    return
  }

  chartInstance = new Chart(chartCanvas.value, {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false,
      },
      plugins: {
        legend: {
          display: props.compareAll,
          labels: {
            color: '#94A3B8',
            font: { size: 12 },
            boxWidth: 12,
            boxHeight: 12,
          }
        },
        tooltip: {
          backgroundColor: '#0F172A',
          borderColor: '#334155',
          borderWidth: 1,
          titleColor: '#F8FAFC',
          bodyColor: '#CBD5E1',
          padding: 12,
          boxPadding: 6,
          callbacks: {
            title: (items) => {
              const idx = items[0]?.dataIndex ?? 0
              const item = baseRoute.weeklyData[idx]
              return `第 ${idx + 1} 週：${item.departureDate} ~ ${item.returnDate}${item.tag ? ` (${item.tag})` : ''}`
            },
            label: (item) => {
              const val = typeof item.raw === 'number' ? item.raw : null
              return `  ${item.dataset.label}: NT$ ${val !== null ? val.toLocaleString() : 'N/A'}`
            }
          }
        }
      },
      scales: {
        x: {
          grid: {
            color: '#1E293B'
          },
          ticks: {
            color: '#64748B',
            font: { size: 11 },
            maxRotation: 45,
            minRotation: 45
          }
        },
        y: {
          grid: {
            color: '#1E293B'
          },
          ticks: {
            color: '#64748B',
            font: { size: 11 },
            callback: (val) => `NT$ ${(Number(val) / 1000).toFixed(0)}k`
          }
        }
      }
    }
  })
}

onMounted(() => {
  renderChart()
})

// 監聽航線切換、對比模式、以及每條航線的 weeklyData 長度變化
watch([() => props.selectedRouteId, () => props.compareAll], () => {
  renderChart()
})

// 用 deep watch 監聽 weeklyData 內容變化（載入更多週時觸發）
// 監聽每條航線的 weeklyData 長度變化（載入更多週時觸發）
const weeklyDataLengths = computed(() => props.routes.map(r => r.weeklyData.length).join(','))
watch(weeklyDataLengths, () => {
  renderChart()
})
</script>

<template>
  <div class="bg-slate-800/60 border border-slate-700/60 rounded-2xl p-5 mb-8 shadow-xl backdrop-blur">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
      <div>
        <h2 class="text-base font-semibold text-slate-200 flex items-center space-x-2">
          <span>📈</span>
          <span>40 週週末票價波動折線圖</span>
        </h2>
        <p class="text-xs text-slate-400 mt-0.5">
          紅色標記點為重大連假或賞花/賞楓旺季（點擊曲線可懸停查看票價）
        </p>
      </div>
      <div class="flex items-center space-x-2">
        <span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
          ● 節慶/連假標記
        </span>
      </div>
    </div>

    <div class="relative h-80 sm:h-96 w-full">
      <canvas ref="chartCanvas" role="img" :aria-label="'票價波動折線圖 - ' + (compareAll ? '全航線對比' : selectedRouteId)"></canvas>
    </div>
  </div>
</template>
