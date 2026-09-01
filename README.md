# ✈️ Flight Radar (華航週末 40 週機票雷達)

> 一個全自動化的 **Vue 3 + Vite + Tailwind CSS + GitHub Actions** 專案，自動監控並視覺化中華航空（China Airlines）未來 40 週「每週六出發、隔週日返程（9天8夜）」之日本航線來回最低票價。

---

## 🌟 核心特色

1. **0 伺服器成本 (Zero Server Cost)**：採用 GitHub Actions 定時抓取機票數據，靜態部署於 GitHub Pages。
2. **歷史價格追蹤**：每日快照儲存於 `data/raw/`，可追溯每次查詢的價格變化。
3. **直覺視覺化**：
   - 📈 **40 週趨勢折線圖**：支援歷史價格走勢對比，標註國定連假、春節與賞花旺季。
   - 🏆 **最便宜 Top 5 排行榜**：自動計算各航線最划算的 5 個週末。
   - 📋 **完整 40 週資料明細表**：支援連假篩選與漲跌標記。
4. **高擴充性**：修改 `scripts/routes_config.json` 即可新增航線（長榮、星宇、國泰等）。

---

## 🛠️ 技術棧

| 層級 | 技術 |
|------|------|
| Frontend | Vue 3 (Composition API) + TypeScript + Vite + Tailwind CSS + Chart.js |
| Backend & Crawler | Python 3 + fast-flights (Google Flights) / Amadeus API |
| CI/CD & Hosting | GitHub Actions + GitHub Pages |

---

## 🚀 快速開始 (Quick Start)

### 1. 本地開發
```bash
# 1. 複製專案
git clone https://github.com/your-username/flight-radar.git
cd flight-radar

# 2. 安裝前端依賴
npm install

# 3. 安裝 Python 依賴
pip install requests beautifulsoup4

# 4. 抓取原始資料快照
python scripts/fetch_raw_data.py

# 5. 建構 API 資料
python scripts/build_api.py

# 6. 啟動前端開發伺服器
npm run dev
```

### 2. 部署至 GitHub Pages
1. 在 GitHub 建立 Repository。
2. 推送到 `main` 分支。
3. **Settings** → **Pages** → **Source** 選擇 **GitHub Actions**。
4. （可選）設定 Amadeus API Secrets：
   - `AMADEUS_CLIENT_ID`
   - `AMADEUS_CLIENT_SECRET`
5. 每次推送或手動觸發 workflow，GitHub Actions 自動抓取並部署！

---

## 📂 專案結構

```
flight-radar/
├── scripts/                  # Python 資料腳本
│   ├── shared.py             # 共用工具（日期、假期、價格）
│   ├── routes_config.json    # 航線定義
│   ├── fetch_raw_data.py     # 原始快照抓取器
│   └── build_api.py          # API 建構器
├── data/                     # 原始資料（不公開）
│   └── raw/{airline}/{route}/YYYY-MM-DD.json
├── public/api/               # 前端 API（前端 fetch）
│   ├── index.json            # 全站索引
│   └── airlines/{code}/
│       ├── index.json        # 航司索引
│       └── {route}/
│           ├── meta.json     # 航線 meta
│           └── weeks/*.json  # 週資料
├── src/                      # 前端原始碼
│   ├── App.vue               # 主控元件
│   ├── components/           # Vue 組件
│   └── types/                # TypeScript 型別
└── docs/                     # 專案文件
```

---

## 📚 文件

- [專案架構](./docs/architecture.md) — 系統架構與模組關係
- [資料流程](./docs/data-flow.md) — 從爬蟲到前端的完整資料流
- [建置部署](./docs/build-deploy.md) — 開發環境建置與 CI/CD 流程
- [Code Review 流程](./docs/code-review-flow.md) — 代碼審查執行流程
- [Code Review 報告](./CODE-REVIEW-REPORT.md) — 代碼審查完整報告
