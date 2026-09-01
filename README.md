# ✈️ Flight Radar (華航週末 40 週機票雷達)

> 一個全自動化的 **Vue 3 + Vite + Tailwind CSS + GitHub Actions** 專案，自動監控並視覺化中華航空（China Airlines）未來 40 週「每週六出發、隔週日返程（9天8夜）」之日本航線來回最低票價。

---

## 🌟 核心特色
1. **0 伺服器成本 (Zero Server Cost)**：採用 GitHub Actions 每日定時抓取機票數據並更新靜態 `public/data/flights.json`，部署於 GitHub Pages。
2. **直覺視覺化**：
   - 📈 **40 週趨勢折線圖**：支援單一航線或全航線疊加對比，標註國定連假、春節與賞花旺季。
   - 🏆 **最便宜 Top 5 排行榜**：自動計算各航線最划算的 5 個週末，附帶一鍵 Google Flights 購票搜尋連結。
   - 📋 **完整 40 週資料明細表**：支援快速關鍵字搜尋、連假篩選與最低地板價標記。
3. **高擴充性**：只需修改 `scripts/routes_config.json` 即可自由新增長榮、星宇、國泰或其他全球航線。

---

## 🛠️ 技術棧
- **Frontend**：Vue 3 (Composition API) + TypeScript + Vite + Tailwind CSS + Chart.js
- **Backend & Crawler**：Python 3 + Amadeus API / Google Flights Scraper
- **CI/CD & Hosting**：GitHub Actions + GitHub Pages

---

## 🚀 快速開始 (Quick Start)

### 1. 本地開發
```bash
# 1. 複製專案
git clone https://github.com/your-username/flight-radar.git
cd flight-radar

# 2. 安裝前端依賴
npm install

# 3. 測試執行 Python 數據更新腳本
python scripts/fetch_flights.py

# 4. 啟動前端開發伺服器
npm run dev
```

### 2. 部署至 GitHub Pages
1. 在 GitHub 建立一個名為 `flight-radar` 的 Repository。
2. 將本專案程式碼推送到 `main` 分支。
3. 進入 GitHub Repository 的 **Settings** -> **Pages**：
   - **Build and deployment** -> **Source** 選擇 **GitHub Actions**。
4. （可選）若有申請 Amadeus API，進入 **Settings** -> **Secrets and variables** -> **Actions**，新增：
   - `AMADEUS_CLIENT_ID`
   - `AMADEUS_CLIENT_SECRET`
5. 每次推送或每天早上 08:00 (UTC 00:00)，GitHub Actions 都會自動抓取最新票價並自動發布更新！
