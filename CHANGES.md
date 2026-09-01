# Changes Summary — Code Review Fixes

**日期**：2025-07-26  
**基於**：`CODE-REVIEW-REPORT.md`（55 issues）  

---

## 修復統計

| 嚴重度 | 修復數 | 剩餘 |
|--------|--------|------|
| 🔴 Critical | **4/4** | 0 |
| 🟠 Major | **13/18** | 5 |
| 🟡 Minor | **3/20** | 17 |
| 💡 Suggestion | **0/13** | 13 |
| **合計** | **20/55** | 35 |

---

## 已修復 Issues

### 🔴 Critical（4/4 ✅）

| ID | 問題 | 修復方式 |
|----|------|----------|
| S-001 | `get_holiday_tag` 硬編碼 2026-2027 | 建立 `scripts/shared.py`，改為動態年份計算 |
| F-001 | 40 個 fetch 同時並發 | 加入 concurrency limiter（最多 4 個同時） |
| F-002 | 週數硬編碼 40 + magic fallback date | 改用 `meta.totalWeeks`；topDeals 空時 early return |
| C-001 | 缺乏 ESLint/Prettier/pre-commit | 建立 `eslint.config.js`、`.prettierrc`、補齊 npm scripts |

### 🟠 Major（13/18）

| ID | 問題 | 修復方式 |
|----|------|----------|
| M1 | `getGoogleFlightsUrl` 重複 3 處 | 建立 `src/utils/url.ts`，兩 component 改用 import |
| M2 | reactive push() mutation | 改用整體賦值 `routeDetailsMap.value = { ... }` |
| M3 | `deep: true` watch 效能浪費 | 改用 computed 比較數值字串 |
| M4 | `(ctx: any)` 繞過 TS 型別 | 改用 `ScriptableContext<'line'>` + null guard |
| M5 | `catch (err: any)` 型別不安全 | 改用 `catch (err: unknown)` + `instanceof Error` |
| M6 | 腳本間大量重複（~100 行） | 抽出 `scripts/shared.py`，3 支腳本引用共用模組 |
| M7 | `stay_days` 未使用 | 移除無用變數 |
| M8 | 配置檔路徑不一致 | 統一使用 `shared.CONFIG_PATH`、`shared.DATA_DIR` |
| M10 | Vite 缺 build 優化 | 加入 `manualChunks`（chart.js 獨立）、`@` alias、`server.host` |
| M11 | tsconfig 缺 alias / Casing 設定 | 加入 `baseUrl`、`paths`、`forceConsistentCasingInFileNames` |
| M12 | .gitignore 遺漏 .env / .venv | 補齊 `.env*`、`.venv/`、`.DS_Store`、`__pycache__/` |
| M13 | 缺 engines / scripts | 加入 `engines`、`lint`/`format`/`type-check` scripts |
| — | `price_diff` 無法區分「無變動」與「無資料」 | 改回傳 `None` 而非 `0` |

### 🟡 Minor（3/20）

| ID | 問題 | 修復方式 |
|----|------|----------|
| F-011 | 表格缺 `<caption>` / `<th>` scope | 加入 `<caption class="sr-only">` + `scope="col"` |
| F-012 | `<canvas>` 缺 aria-label | 加入 `role="img"` + 動態 `:aria-label` |
| — | tailwind brand 色階不完整 | 補齊 50-900 色階 |

---

## 新增/修改檔案清單

### 新增
- `scripts/shared.py` — 共用邏輯（holiday、日期、價格、路徑常數）
- `src/utils/url.ts` — Google Flights URL 工具函式
- `eslint.config.js` — ESLint flat config
- `.prettierrc` — Prettier 設定

### 修改
- `src/App.vue` — concurrency limiter、型別安全、reactive 更新
- `src/components/PriceChart.vue` — TypeScript 型別、效能 watch、a11y
- `src/components/PriceTable.vue` — import url.ts、a11y
- `src/components/TopDeals.vue` — import url.ts
- `scripts/fetch_raw_data.py` — 引用 shared
- `scripts/fetch_flights.py` — 引用 shared
- `scripts/build_api.py` — 引用 shared
- `vite.config.ts` — alias、build 優化、server 設定
- `tsconfig.json` — alias、Casing 設定
- `package.json` — engines、scripts、metadata
- `.gitignore` — 補齊忽略規則
- `tailwind.config.js` — 色階補齊
- `postcss.config.js` — cssnano
- `index.html` — noscript fallback

---

## 剩餘 Issues（建議後續處理）

### 🟠 Major（5）
| ID | 問題 | 建議 |
|----|------|------|
| S-008 | 反爬蟲策略脆弱（固定 1.5s） | 加入 exponential backoff + jitter |
| S-006 | `stayDays` config 仍可能無效 | 確認 fast-flights API 是否支援 trip_days |
| — | 缺 `requirements.txt` | 建立 requirements.txt |
| — | 裸 `except Exception` 捕獲 | 針對不同例外類型分類處理 |
| — | `main()` 函式過長 | 拆分為子函式 |

### 🟡 Minor（17）/ 💡 Suggestion（13）
- 路徑操作改用 pathlib
- 用 logging 取代 print
- 為純函式補單元測試
- 加入自動重試機制
- 前端 route 初始值改空字串
- `compareAll` 模式按鈕視覺提示
- CSS 壓縮（cssnano）
- README 佔位符修正
- darkMode 預留
- 等等...

---

*All Critical issues resolved. Remaining items are recommended for future iterations.*
