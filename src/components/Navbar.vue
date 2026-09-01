<script setup lang="ts">
defineProps<{
  updatedAt: string
}>()
</script>

<template>
  <header class="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <span class="text-2xl">✈️</span>
        <div>
          <h1 class="text-lg font-bold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
            Flight Radar
          </h1>
          <p class="text-xs text-slate-400">華航日本線 · 未來 40 週六出發週末機票雷達 (9天8夜)</p>
        </div>
      </div>
      <div class="flex items-center space-x-4">
        <div class="hidden sm:flex items-center space-x-2 text-xs bg-slate-800 px-3 py-1.5 rounded-full text-slate-300 border border-slate-700">
          <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>更新時間：{{ updatedAt || '載入中...' }}</span>
        </div>
        <span class="text-xs bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2.5 py-1 rounded-md font-mono">
          40 Weeks Tracker
        </span>
      </div>
    </div>
  </header>
</template>
