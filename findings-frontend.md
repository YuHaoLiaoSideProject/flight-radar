# Frontend Code Review Findings

## Summary
- Critical: 2
- Major: 5
- Minor: 7
- Suggestion: 5

## Findings

### [F-001] 嚴重度：Critical
- **檔案**: `src/App.vue:82-107` (`loadAllWeeks`)
- **問題**: 同時並行發出 40 個 HTTP 請求，無任何 concurrency 限制。在弱網環境或移動裝置上，瀏覽器對同一 origin 的同時連線數上限為 6（HTTP/1.1），其餘會排隊等待；若伺服器回應慢，會造成記憶體中大量 pending Promise 同時存在，以及 `detail.weeklyData.push()` 併發寫入 race condition（雖然 JS 單執行緒讓 push 本身不會 crash，但陣列順序在 `sort` 前是不確定的，且 UI 可能在 sort 前就 re-render 了中間態資料）。
- **建議**:
  1. 使用 concurrency limiter（如 p-limit 或手寫 semaphore），限制同時最多 4-6 個請求。
  2. 在每次 push 後觸發 reactive 更新前，先收集到暫存陣列，`Promise.all` 完成後再一次性賦值給 `detail.weeklyData`，避免中途 re-render。

```ts
// 改進範例
const CONCURRENT = 4
let running = 0
let queue = [...weekDates]
const results: WeekItem[] = []

await new Promise<void>((resolve) => {
  function next() {
    while (running < CONCURRENT && queue.length) {
      const dateStr = queue.shift()!
      running++
      fetch(`./${weeksBasePath}/${dateStr}.json`)
        .then(r => r.ok ? r.json() : null)
        .then(data => { if (data) results.push(data) })
        .finally(() => { running--; if (!queue.length && running === 0) resolve(); else next() })
    }
  }
  next()
})
detail.weeklyData = results.sort((a, b) => a.weekIndex - b.weekIndex)
```

---

### [F-002] 嚴重度：Critical
- **檔案**: `src/App.vue:92-95`
- **問題**: 週數硬編碼為 `40`，且以 magic date `'2026-09-05'` 作為起始日fallback。若 API 的 `meta.weeksCount` 變動，或 `topDeals` 為空陣列，邏輯會產生錯誤的日期序列（fallback 日期是任意寫死的，可能與實際資料完全不符）。
- **建議**:
  1. 直接使用 `meta.weeksCount` 作為迭代上限，而非硬編碼 40。
  2. 將 fallback 日期改為 `meta.generatedAt` 或從 API 取得的實際起始日。
  3. 若 `topDeals` 為空，應提前 return 或拋出明確錯誤，不應靜默使用 fallback。

```ts
// 改進
if (!meta.topDeals.length) {
  console.error(`航線 ${routeId} 無 topDeals 資料，無法建立週列表`)
  detail.isLoadingWeeks = false
  return
}
const startDate = new Date(meta.topDeals[0].departureDate)
const weekDates: string[] = []
for (let i = 0; i < detail.totalWeeks; i++) { ... }
```

---

### [F-003] 嚴重度：Major
- **檔案**: `src/App.vue:38` / `src/components/PriceTable.vue:13-14` / `src/components/TopDeals.vue:8-9`
- **問題**: `getGoogleFlightsUrl` 函式在 `PriceTable.vue` 和 `TopDeals.vue` 中完全重複定義（DRY 違反），且 URL 參數未經 `encodeURIComponent` 編碼。若 `origin`、`dest`、`dep`、`ret` 含有特殊字元，會產生 malformed URL。
- **建議**:
  1. 將 `getGoogleFlightsUrl` 抽取為共用工具函式（如 `src/utils/url.ts`）。
  2. 所有 URL 參數使用 `encodeURIComponent()` 編碼。

```ts
// src/utils/url.ts
export function getGoogleFlightsUrl(
  origin: string, dest: string, dep: string, ret: string
): string {
  const q = `flights from ${origin} to ${dest} on ${dep} returning ${ret}`
  return `https://www.google.com/travel/flights?q=${encodeURIComponent(q)}`
}
```

---

### [F-004] 嚴重度：Major
- **檔案**: `src/App.vue:87-96`
- **問題**: `loadAllWeeks` 直接 mutate `routeDetailsMap` 的深層屬性（`detail.weeklyData.push()`、`detail.loadedWeeks++` 等），但 `routeDetailsMap` 本身是 `ref<Record<string, RouteDetail>>`。Vue 3 的 `ref` 只對 `.value` 做深層 reactive，這裡的 `detail` 是從 `.value` 取出的別名，雖然 mutation 能被偵測到，但這種模式非常脆弱且難以維護——若之後重構為 `shallowRef` 或改用 `reactive()`，此處的 mutation 將不會觸發 reactivity。
- **建議**: 使用明確的 reactive 更新模式，例如整體賦值：

```ts
// 改進：收集完成後一次性更新
const newDetail = { ...detail, weeklyData: sortedData, isLoadingWeeks: false, loadProgress: 100 }
routeDetailsMap.value = { ...routeDetailsMap.value, [routeId]: newDetail }
```

---

### [F-005] 嚴重度：Major
- **檔案**: `src/components/PriceChart.vue:91-97`
- **問題**: `watch` 使用 `{ deep: true }` 監聽 `() => props.routes.map(r => r.weeklyData.length)`。此 watcher 函式每次都回傳新陣列（`map` 產生新引用），Vue 的 watcher 預設用 `Object.is` 比較，只要引用不同就會觸發回調。`deep: true` 會額外深層遍歷整個 `routes` 陣列的所有屬性（包含 `weeklyData` 內的每個 `history` 陣列），造成嚴重的效能浪費——每次任何 route 的任何屬性微小變動都會重建整個圖表。
- **建議**:
  1. 移除 `deep: true`，因為 watcher 函式已回傳新陣列引用，預設比較即可觸發。
  2. 若只需偵測 weeklyData 長度變化，改用 `computed` 比較數值：

```ts
const weeklyLengths = computed(() =>
  props.routes.map(r => r.weeklyData.length).join(',')
)
watch(weeklyLengths, () => renderChart())
```

---

### [F-006] 嚴重度：Major
- **檔案**: `src/components/PriceChart.vue:53-55` / `src/components/PriceChart.vue:59-61`
- **問題**: `pointRadius` 和 `pointBackgroundColor` 回調使用 `(ctx: any)`，完全繞過 TypeScript 型別檢查。Chart.js 提供了 `ScriptableLinePointOptions` 等型別，應使用正確型別。此外，回調中直接存取 `route.weeklyData[ctx.dataIndex]`，若 `weeklyData` 尚未載入完成（空陣列），`ctx.dataIndex` 可能越界，回傳 `undefined` 導致 `undefined?.isHoliday` 雖然不會 crash 但邏輯不符預期。
- **建議**:

```ts
import type { ScriptableContext } from 'chart.js'

// 使用正確型別並加上防禦
pointRadius: (ctx: ScriptableContext<'line'>) => {
  const item = route.weeklyData[ctx.dataIndex]
  return item?.isHoliday ? 5 : 2.5
},
```

---

### [F-007] 嚴重度：Major
- **檔案**: `src/App.vue:29` / `src/App.vue:35`
- **問題**: 所有 `catch` 區塊使用 `err: any`，TypeScript strict mode 下不建議使用 `any`。更重要的是，若 `fetch` 拋出的是 `TypeError`（網路斷線時），`err.message` 可能是 `"Failed to fetch"` 這類英文訊息，直接顯示給中文使用者不友善。
- **建議**:

```ts
} catch (err: unknown) {
  const message = err instanceof Error ? err.message : String(err)
  // 或者映射為友善訊息
  const friendlyMsg = message.includes('Failed to fetch')
    ? '網路連線失敗，請檢查網路設定'
    : message
  error.value = friendlyMsg
}
```

---

### [F-008] 嚴重度：Minor
- **檔案**: `src/App.vue:102`
- **問題**: `watch(compareAll, async (newVal) => { ... })` 使用 `async` callback。Vue 的 `watch` 不支援 async callback 的 awaited return（Vue 不會等待 Promise），若多個路由的 `loadRouteMeta` 同時執行，會有非預期的並行行為。雖然功能上可行，但模式不正確。
- **建議**: 改用 `watchEffect` 或在 callback 內部自行管理 async flow，不要依賴 watch 的 async 支援。

---

### [F-009] 嚴重度：Minor
- **檔案**: `src/App.vue:21-52`
- **問題**: `loadRouteMeta` 函式的回傳值 `Promise<RouteDetail | null>` 在所有呼叫點都未被使用（`await loadRouteMeta(newId)` 的回傳值被丟棄）。這是一個 side-effect-only 函式，卻設計為回傳值，造成 API 語意混淆。
- **建議**: 改為 `void` 回傳，或將回傳值用於回呼/ chaining。

---

### [F-010] 嚴重度：Minor
- **檔案**: `src/types/flight.ts:56-63`
- **問題**: `RouteDetail` 繼承 `RouteMeta` 並混入 UI 狀態屬性（`loadedWeeks`、`isLoadingWeeks`、`loadProgress`）。這是 data model 與 UI state 的混合，違反單一職責原則。若未來有多處使用 `RouteDetail`，UI 狀態會被不需要的地方污染。
- **建議**: 分離為 `RouteDetail`（純 API 資料）和 `RouteLoadingState`（UI 狀態），在 `App.vue` 中用 composite pattern 組合。

```ts
export interface RouteLoadingState {
  weeklyData: WeekItem[]
  loadedWeeks: number
  totalWeeks: number
  isLoadingWeeks: boolean
  loadProgress: number
}

export interface RouteDetail extends RouteMeta, RouteLoadingState {}
```

---

### [F-011] 嚴重度：Minor
- **檔案**: `src/components/PriceTable.vue` / `src/components/TopDeals.vue`
- **問題**: 表格缺少 `<caption>` 元素，螢幕閱讀器無法理解表格用途。`<th>` 元素未加 `scope="col"` 屬性。
- **建議**:

```html
<table class="...">
  <caption class="sr-only">未來 40 週完整票價明細表 - {{ activeRoute.name }}</caption>
  <thead>
    <tr>
      <th scope="col" class="...">週次</th>
      ...
    </tr>
  </thead>
</table>
```

---

### [F-012] 嚴重度：Minor
- **檔案**: `src/components/PriceChart.vue:113`
- **問題**: `<canvas>` 元素缺少 `aria-label` 或 `role="img"` 搭配描述文字。Chart.js 圖表對視障使用者完全不可感知。
- **建議**:

```html
<canvas ref="chartCanvas" role="img"
  :aria-label="`${activeRoutes.length === 1 ? activeRoutes[0]?.name : '全航線'}40週票價折線圖`">
</canvas>
```

---

### [F-013] 嚴重度：Minor
- **檔案**: `src/App.vue:47-49`
- **問題**: 路徑操作使用字串替換（`.replace('/index.json', '/meta.json')`、`.replace('/meta.json', '') + '/weeks'`），這種路徑拼接非常脆弱，若 API 結構稍有變動就會靜默失敗。
- **建議**: 在 `RouteSummary` 的 API schema 中直接提供 `metaPath` 和 `weeksPath` 欄位，或在前端建立 URL builder 工具，集中管理路徑邏輯。

---

### [F-014] 嚴重度：Minor
- **檔案**: `src/components/PriceChart.vue:53-61`
- **問題**: `pointRadius` 和 `pointBackgroundColor` 使用箭頭函式回調，每次 `renderChart` 都建立新的閉包。Chart.js 在每個 render frame 都會呼叫這些回調（例如 hover、resize 時），若圖表有 40 個資料點 × 多條航線，會產生大量短期物件，增加 GC 壓力。
- **建議**: 若效能成為瓶頸，可改為使用 Chart.js 的 `pointStyle` + dataset-level 設定，或在 `options` 層級用 `scriptable` options 統一處理。

---

### [F-015] 嚴重度：Suggestion
- **檔案**: `src/App.vue:6-7`
- **問題**: `selectedRouteId` 初始值為 `'TPE-NRT'` 硬編碼，但 `loadRootIndex` 中又會覆蓋為 `data.config?.defaultRoute || data.routes[0].id`。初始值 `'TPE-NRT'` 在 mount 前會短暫存在，若 `rootIndex` 尚未載入，模板中以 `selectedRouteId` 為基準的邏輯會在错误的路線上執行。
- **建議**: 將初始值設為空字串 `''`，並在模板中加 `v-if="selectedRouteId"` 保護。

---

### [F-016] 嚴重度：Suggestion
- **檔案**: `src/App.vue`
- **問題**: 缺少錯誤重試機制。若 `loadRootIndex` 失敗，使用者只能手動點「重新整理」按鈕。若 `loadAllWeeks` 中個別週載入失敗，僅 `console.warn` 且靜默略過，無重試機制。
- **建議**: 加入自動重試（如 exponential backoff）或提供「重試失敗項目」按鈕。

---

### [F-017] 嚴重度：Suggestion
- **檔案**: `src/components/PriceChart.vue:53-55` / `src/components/PriceChart.vue:59-61`
- **問題**: `pointRadius` 和 `pointBackgroundColor` 的回調使用 `route.weeklyData[ctx.dataIndex]`，但 `ctx.dataIndex` 可能為 `undefined`（如在 chart 初始化時）。雖然有 `?.` 保護，但若 `weeklyData` 載入不完整（部分缺失），可能回傳意料外的預設值。
- **建議**: 在回調開頭加入 `if (ctx.dataIndex == null) return defaultValue` 的 guard。

---

### [F-018] 嚴重度：Suggestion
- **檔案**: `src/App.vue:113-116`
- **問題**: `allLoadedRouteDetails` computed 每次呼叫都 `.map()` + `.filter()` 建立新陣列。在 `compareAll` 模式下，若 routes 數量多且 `weeklyData` 長（每條 40 週 × history），傳入 `PriceChart` 的 `routes` prop 可能導致不必要的 re-render。
- **建議**: 考慮使用 `shallowRef` 儲存 route details，或在 `PriceChart` 內部用 `computed` 做 memoization。

---

### [F-019] 嚴重度：Suggestion
- **檔案**: `src/components/PriceTable.vue:77`
- **問題**: `<a>` 連結文字為「前往查價 ↗」，對輔助技術不夠明確。`↗` 圖標對螢幕閱讀器無意義。
- **建議**: 加入 `aria-label` 提供完整描述：

```html
<a :href="..." target="_blank" rel="noopener noreferrer"
   class="..."
   :aria-label="`在 Google Flights 查詢 ${row.departureDate} 至 ${row.returnDate} 的機票`">
  前往查價 <span aria-hidden="true">↗</span>
</a>
```

---

### [F-020] 嚴重度：Suggestion
- **檔案**: `src/App.vue:141-146`
- **問題**: 錯誤狀態的「重新整理」按鈕缺少 `aria-label`，且在 loading 狀態時無 disabled 機制（連續點擊會觸發多次 fetch）。
- **建議**:

```html
<button @click="loadRootIndex"
  class="..."
  :disabled="loading"
  aria-label="重新載入 API 資料">
  重新整理
</button>
```

---

### [F-021] 嚴重度：Suggestion
- **檔案**: `src/App.vue:120-136`
- **問題**: 航線切換按鈕的 `class` 動態綁定使用三元運算式，條件為 `selectedRouteId === route.id && !compareAll`。此邏輯意味著在 `compareAll=true` 時，所有按鈕都會顯示為非選中狀態，但實際上仍有一條「selectedRouteId」被選中（只是圖表顯示全部）。這對使用者可能造成困惑——按鈕全暗但圖表有高亮航線。
- **建議**: 在 `compareAll` 模式下，應明確高亮被選中的航線按鈕（或改變按鈕群組的視覺提示），確保 UI 狀態一致。
