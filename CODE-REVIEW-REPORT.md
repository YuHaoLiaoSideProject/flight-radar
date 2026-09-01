# Code Review Report — flight-radar

**日期**：2025-07-26  
**審查者**：資深工程師標準 Code Review  
**專案**：華航週末 40 週機票雷達  
**審查範圍**：前端 (Vue/TS)、Python 腳本、設定檔  

---

## Executive Summary

本專案整體架構合理，CI/CD 流程（GitHub Actions + Pages）設計正確，README 文件完整度高。主要風險在於**缺乏自動化品質管控工具鏈**、**多處嚴重的程式碼重複**、以及**硬編碼日期即將過期**。

### 嚴重度分佈

| 嚴重度 | 前端 | 腳本 | 設定 | **合計** |
|--------|------|------|------|----------|
| 🔴 Critical | 2 | 1 | 1 | **4** |
| 🟠 Major | 5 | 8 | 5 | **18** |
| 🟡 Minor | 7 | 8 | 5 | **20** |
| 💡 Suggestion | 5 | 4 | 4 | **13** |
| **合計** | 19 | 21 | 15 | **55** |

---

## 🔴 Critical Issues（必須立即修復）

### 1. 年份硬編碼即將過期 — `[S-001]`
- **檔案**：`fetch_flights.py:17-34` / `build_api.py:8-25`
- **問題**：`get_holiday_tag()` 硬編碼 2026-09 至 2027-06 日期範圍。**2027 年 7 月後所有日期無假期標籤**，fallback 價格系統失效。
- **建議**：改用 `chinese-calendar` 第三方庫動態計算，或將 holiday 配置外化至 JSON 檔案。

### 2. 40 個 HTTP 請求同時並發 — `[F-001]`
- **檔案**：`src/App.vue:82-107`
- **問題**：`loadAllWeeks` 同時發出 40 個 fetch 請求，無 concurrency 限制。瀏覽器同源並發上限為 6（HTTP/1.1），多餘請求排隊等待；記憶體中大量 pending Promise 同時存在，`weeklyData.push()` 有併發 race condition。
- **建議**：使用 concurrency limiter（如 p-limit），限制同時最多 4-6 個請求；收集完成後一次性賦值。

### 3. 週數硬編碼 + fallback 日期 — `[F-002]`
- **檔案**：`src/App.vue:92-95`
- **問題**：週數硬編碼為 `40`，以 magic date `'2026-09-05'` 作 fallback。若 API `meta.weeksCount` 變動或 `topDeals` 為空，會產生錯誤的日期序列。
- **建議**：直接使用 `meta.weeksCount` 作為迭代上限；若 `topDeals` 為空應提前 return。

### 4. 缺乏自動化品質管控工具鏈 — `[C-001]`
- **檔案**：`package.json`
- **問題**：無 ESLint、Prettier、pre-commit hook 配置。品質管控完全依賴人工 review，風險極高。
- **建議**：安裝 `eslint` + `@vue/eslint-config-typescript` + `eslint-plugin-vue`、`prettier`、`husky` + `lint-staged`。

---

## 🟠 Major Issues（強烈建議修復）

| # | 來源 | 檔案 | 問題摘要 |
|---|------|------|----------|
| M1 | 前端 | `App.vue:38` / `PriceTable.vue:13` / `TopDeals.vue:8` | `getGoogleFlightsUrl` 在 3 處重複定義（DRY 違反），且 URL 參數未 `encodeURIComponent` |
| M2 | 前端 | `App.vue:87-96` | 直接 mutate `ref` 深層屬性（`detail.weeklyData.push()`），模式脆弱，重構為 `shallowRef` 時會壞掉 |
| M3 | 前端 | `PriceChart.vue:91-97` | `watch` 使用 `deep: true` 監聽 routes 陣列，每次任何屬性微小變動都重建整個圖表 |
| M4 | 前端 | `PriceChart.vue:53-61` | 使用 `(ctx: any)` 繞過 TypeScript 型別檢查，Chart.js 提供了完整型別定義 |
| M5 | 前端 | `App.vue:29,35` | 所有 `catch` 使用 `err: any`，型別不安全；fetch 錯誤訊息直接顯示給中文使用者不友善 |
| M6 | 腳本 | 多處 | 三支腳本間大量程式碼重複：`generate_weekly_dates` ×2、`holiday_tag` ×3、fetch functions ×2（~100 行重複） |
| M7 | 腳本 | `fetch_raw_data.py:123` / `fetch_flights.py:138` | `stay_days` 變數被賦值但從未使用，`routes_config.json` 的 `stayDays` 設定形同虛設 |
| M8 | 腳本 | 多處 | 配置檔路徑不一致：`data/routes.json` vs `scripts/routes.json`，兩份必須同步 |
| M9 | 腳本 | `fetch_raw_data.py:128-131` | 缺乏 rate-limit 恢復機制，反爬蟲策略脆弱（固定 1.5s interval + 5 次中斷） |
| M10 | 設定 | `vite.config.ts` | 無 `manualChunks`（chart.js ~200KB 捆綁在主 chunk）、無 `resolve.alias`、無 sourcemap 設定 |
| M11 | 設定 | `tsconfig.json` | 缺少 `forceConsistentCasingInFileNames`、無 `paths` 別名與 Vite 不同步 |
| M12 | 設定 | `.gitignore` | 缺少 `.env*`、`.venv/`、`.DS_Store`、`__pycache__/` |
| M13 | 設定 | `package.json` | 所有依賴使用 `^` 版本範圍，無 engines 欄位鎖定 Node 版本 |

---

## 🟡 Minor Issues

| # | 來源 | 檔案 | 問題摘要 |
|---|------|------|----------|
| m1 | 前端 | `App.vue:102` | `watch` 使用 `async` callback，Vue 不支援 awaited return |
| m2 | 前端 | `App.vue:21-52` | `loadRouteMeta` 回傳值未被使用，語義混淆 |
| m3 | 前端 | `types/flight.ts:56-63` | `RouteDetail` 混合 UI state 與 API 資料，違反 SRP |
| m4 | 前端 | `PriceTable.vue` / `TopDeals.vue` | 表格缺 `<caption>`、`<th>` 缺 `scope="col"` |
| m5 | 前端 | `PriceChart.vue:113` | `<canvas>` 缺 `aria-label`，視障使用者無法感知圖表 |
| m6 | 前端 | `App.vue:47-49` | 路徑操作使用字串替換，脆弱易壞 |
| m7 | 前端 | `PriceChart.vue:53-61` | 高頻閉包增加 GC 壓力 |
| m8 | 腳本 | `build_api.py:37-40` | `except Exception: pass` 完全吞掉例外 |
| m9 | 腳本 | 多處 | 全部腳本缺乏 type hints |
| m10 | 腳本 | 多處 | 大多數函式缺乏 docstring |
| m11 | 腳本 | `build_api.py:89-95` | `price_diff` 無法區分「無變動」與「無資料」 |
| m12 | 腳本 | 多處 | `main()` 函式過長（60~100 行），混合多種責任 |
| m13 | 腳本 | 多處 | 硬編碼路徑 `../data/`、`../public/data/` 散布各腳本 |
| m14 | 腳本 | 多處 | 裸 `except Exception` 捕獲所有例外，無法區分錯誤類型 |
| m15 | 腳本 | 多處 | `len(basename) == 15` 用 magic number 過濾檔名 |
| m16 | 設定 | `tailwind.config.js` | `brand` 色階不完整（缺 200-400, 800-900） |
| m17 | 設定 | `vite.config.ts` | 缺 dev server `host: true` 設定（手機測試需手動加 `--host`） |
| m18 | 設定 | `index.html` | 缺 `<noscript>` fallback |
| m19 | 設定 | `postcss.config.js` | 缺 `cssnano` CSS 壓縮 |
| m20 | 設定 | `README.md` | GitHub URL 使用 `your-username` 佔位符 |

---

## 💡 Suggestions

| # | 來源 | 建議 |
|---|------|------|
| S1 | 前端 | 硬編碼初始 route ID `'TPE-NRT'` 改為空字串 |
| S2 | 前端 | 加入自動重試機制（exponential backoff） |
| S3 | 前端 | `pointRadius` 回調加 `ctx.dataIndex == null` guard |
| S4 | 前端 | `allLoadedRouteDetails` computed 加 memoization |
| S5 | 前端 | 錯誤狀態按鈕加 `aria-label` + loading 時 disabled |
| S6 | 前端 | `compareAll` 模式下按鈕視覺提示不一致 |
| S7 | 腳本 | 建立 `requirements.txt` |
| S8 | 腳本 | 用 `logging` 取代 `print()` |
| S9 | 腳本 | 用 `pathlib.Path` 取代 `os.path` |
| S10 | 腳本 | 為純函式補單元測試（pytest） |
| S11 | 設定 | 補齊 npm scripts（lint、lint:fix、format、type-check） |
| S12 | 設定 | `build.target` 與 `tsconfig.json` 對齊 |
| S13 | 設定 | 預先加入 `"darkMode": "class"` |

---

## 🎯 優先修復建議（按 ROI 排序）

### Phase 1：立即修復（1-2 天）
1. **`get_holiday_tag` 重構**（Critical S-001）— 過期後整個 fallback 系統失效
2. **加入 ESLint + Prettier + lint-staged**（Critical C-001）— 投入低、收益高
3. **`.gitignore` 完善**（Major M-005）— 防止 `.env` 被 commit
4. **fetch concurrency 限制**（Critical F-001）— 防止 race condition

### Phase 2：重構（3-5 天）
1. **抽出 `scripts/shared.py`**（Major M6-M9）— 解決腳本間大量重複
2. **抽出 `src/utils/url.ts`**（Major M1）— 解決前端工具函式重複
3. **Vite build 優化**（Major M10）— chart.js 獨立 chunk + alias 設定
4. **TypeScript 型別安全**（Major M4, M5）— 移除 `any`，使用正確型別

### Phase 3：體驗優化（1 週）
1. **Accessibility 補強**（Minor m4-m5）— ARIA 標籤、canvas 描述
2. **錯誤處理改善**（Minor m8, m14）— 分類例外、提供友善訊息
3. **測試覆蓋**（Suggestion S10）— 為核心邏輯補單元測試

---

## 📁 詳細 Findings

完整 review 詳見：
- [`findings-frontend.md`](./findings-frontend.md) — 前端 21 個 issues
- [`findings-scripts.md`](./findings-scripts.md) — 腳本 20 個 issues
- [`findings-config.md`](./findings-config.md) — 設定 15 個 issues

---

*Report generated by Senior Engineer Code Review*
