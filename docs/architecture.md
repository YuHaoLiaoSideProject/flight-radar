# 專案架構

## 🏗️ 系統架構圖

```mermaid
graph TB
    subgraph External["🌐 外部 API"]
        GF[Google Flights<br/>透過 fast-flights 套件]
        AMA[Amadeus Flight API<br/>備用資料源]
    end

    subgraph PythonLayer["🐍 Python 腳本層"]
        direction TB
        SH["shared.py<br/>共用工具庫"]
        FRD["fetch_raw_data.py<br/>原始快照抓取器"]
        FF["fetch_flights.py<br/>即時票價查詢器"]
        BA["build_api.py<br/>API 建構器"]
    end

    subgraph ConfigLayer["⚙️ 設定層"]
        RC["routes_config.json<br/>航線定義（4 條航線）"]
    end

    subgraph DataLayer["💾 資料層"]
        direction TB
        RAW["data/raw/{airline}/{route}/{date}.json<br/>日期快照（歷史記錄）"]
        ROOT["data/routes.json<br/>航線清單"]
    end

    subgraph APILayer["📡 API 層"]
        direction TB
        INDEX["public/api/index.json<br/>全站索引"]
        AIRLINE["public/api/airlines/{code}/index.json<br/>航司索引"]
        META["public/api/airlines/{code}/{route}/meta.json<br/>航線 meta"]
        WEEKS["public/api/airlines/{code}/{route}/weeks/{date}.json<br/>週資料"]
    end

    subgraph Frontend["🎨 前端 Vue 3 + TypeScript"]
        direction TB
        MT["main.ts<br/>進入點"]
        APP["App.vue<br/>主控元件"]
        NAV["Navbar.vue<br/>導覽列"]
        TC["TopDeals.vue<br/>最低價推薦"]
        PC["PriceChart.vue<br/>價格走勢圖 (Chart.js)"]
        PT["PriceTable.vue<br/>週價格表格"]
        TYPES["types/flight.ts<br/>型別定義"]
    end

    subgraph Deploy["🚀 部署"]
        CI["GitHub Actions<br/>CI/CD Pipeline"]
        GHP["GitHub Pages<br/>靜態託管"]
    end

    %% 外部到 Python
    GF -->|HTTP 爬取| FRD
    AMA -->|REST API| FF
    RC --> FRD
    RC --> FF

    %% Python 內部
    SH -.->|共用函式| FRD
    SH -.->|共用函式| FF
    SH -.->|共用函式| BA

    %% Python 到資料層
    FRD -->|JSON 快照| RAW
    ROOT --> FRD

    %% 資料層到 API 層
    RAW -->|解析 + 合併| BA
    BA -->|寫入| INDEX
    BA -->|寫入| AIRLINE
    BA -->|寫入| META
    BA -->|寫入| WEEKS

    %% API 到前端
    INDEX -->|fetch| APP
    META -->|fetch| APP
    WEEKS -->|背景載入| APP

    APP --> NAV
    APP --> TC
    APP --> PC
    APP --> PT
    TYPES -.-> APP

    %% 部署
    APP -->|vite build| CI
    CI -->|deploy| GHP
```

---

## 🎨 前端元件樹

```mermaid
graph TD
    MT["main.ts"] --> APP

    subgraph VueApp["Vue 3 應用"]
        APP["App.vue<br/>━━━━━━━━━━━━━━<br/>• rootIndex: RootIndex<br/>• selectedRouteId<br/>• routeDetailsMap<br/>• compareAll<br/>• loadingProgress"]

        APP --> NAV["Navbar.vue<br/>━━━━━━━━━━━━<br/>• 航司切換<br/>• 航線選擇"]

        APP --> TC["TopDeals.vue<br/>━━━━━━━━━━━━<br/>• topDeals[]<br/>• 最低票價排行<br/>• 假期標籤"]

        APP --> PC["PriceChart.vue<br/>━━━━━━━━━━━━<br/>• Chart.js 折線圖<br/>• 40 週價格走勢<br/>• 歷史比對線"]

        APP --> PT["PriceTable.vue<br/>━━━━━━━━━━━━<br/>• 週次表格<br/>• 價格漲跌<br/>• compareAll 模式"]
    end

    subgraph Types["TypeScript 型別"]
        T1["RootIndex"]
        T2["RouteMeta"]
        T3["RouteDetail"]
        T4["WeekItem"]
        T5["TopDealItem"]
    end

    Types -.-> APP
```

---

## 🐍 後端腳本關係圖

```mermaid
graph LR
    subgraph Shared["shared.py 共用模組"]
        GEN["generate_weekly_dates()<br/>生成 40 週日期"]
        HOL["get_holiday_tag()<br/>假期判斷"]
        BASE["get_baseline_prices()<br/>基準票價"]
        SNAP["get_latest_snapshot()<br/>最新快照"]
        ALLSNAP["get_all_snapshots()<br/>所有快照"]
    end

    subgraph Fetch["抓取腳本"]
        FRD["fetch_raw_data.py<br/>━━━━━━━━━━<br/>• 產生每日快照<br/>• 去重比對<br/>• 輸出: data/raw/"]
        FF["fetch_flights.py<br/>━━━━━━━━━━<br/>• 即時查詢<br/>• 直接輸出 API<br/>• 輸出: public/data/"]
    end

    subgraph Build["建構腳本"]
        BA["build_api.py<br/>━━━━━━━━━━<br/>• 讀取快照<br/>• 計算漲跌<br/>• 生成歷史走勢<br/>• 輸出: public/api/"]
    end

    GEN --> FRD
    GEN --> FF
    HOL --> FRD
    HOL --> FF
    BASE --> FRD
    BASE --> FF
    SNAP --> FRD
    ALLSNAP --> BA
```

---

## 🧰 技術棧清單

### 前端
| 技術 | 版本 | 用途 |
|------|------|------|
| Vue 3 | ^3.4.21 | UI 框架（Composition API + `<script setup>`） |
| TypeScript | ^5.2.2 | 型別安全 |
| Vite | ^5.1.6 | 建置工具 |
| Chart.js | ^4.4.2 | 價格走勢圖表 |
| Tailwind CSS | ^3.4.3 | 樣式系統 |
| PostCSS + Autoprefixer | ^8.4.38 / ^10.4.19 | CSS 處理 |

### 後端（Python 腳本）
| 技術 | 用途 |
|------|------|
| Python 3.x | 腳本執行環境 |
| fast-flights | Google Flights 爬蟲 |
| Amadeus API | 備用票價資料源 |
| requests + beautifulsoup4 | HTTP 請求 |

### 部署
| 技術 | 用途 |
|------|------|
| GitHub Actions | CI/CD 自動化 |
| GitHub Pages | 靜態網站託管 |

---

## 📂 目錄結構說明

```
flight-radar/
├── 📄 package.json              # Node.js 專案設定
├── 📄 vite.config.ts            # Vite 建置設定
├── 📄 tailwind.config.js        # Tailwind CSS 設定
├── 📄 tsconfig.json             # TypeScript 設定
├── 📄 CNAME                     # GitHub Pages 自訂網域
│
├── 📂 scripts/                  # Python 資料腳本
│   ├── shared.py                # 共用工具（日期、假期、價格）
│   ├── routes_config.json       # 航線定義（4 條航線）
│   ├── fetch_raw_data.py        # 原始快照抓取
│   ├── fetch_flights.py         # 即時票價查詢
│   └── build_api.py             # API 建構器
│
├── 📂 data/                     # 原始資料（不公開）
│   ├── routes.json              # 航線清單
│   └── raw/                     # 日期快照目錄
│       └── {airline}/
│           └── {route}/
│               └── YYYY-MM-DD.json
│
├── 📂 public/                   # 靜態資源（建構時複製到 dist）
│   └── api/                     # 前端 API 資料
│       ├── index.json           # 全站索引
│       └── airlines/
│           └── {code}/
│               ├── index.json   # 航司索引
│               └── {route}/
│                   ├── meta.json    # 航線 meta
│                   └── weeks/       # 週資料目錄
│                       └── YYYY-MM-DD.json
│
├── 📂 src/                      # 前端原始碼
│   ├── main.ts                  # 應用進入點
│   ├── App.vue                  # 主控元件
│   ├── style.css                # 全域樣式
│   ├── components/
│   │   ├── Navbar.vue           # 導覽列
│   │   ├── TopDeals.vue         # 最低價推薦
│   │   ├── PriceChart.vue       # 價格走勢圖
│   │   └── PriceTable.vue       # 週價格表格
│   ├── types/
│   │   └── flight.ts            # TypeScript 型別定義
│   └── utils/                   # 工具函式
│
├── 📂 docs/                     # 本文件目錄
│   ├── README.md                # 文件索引
│   ├── architecture.md          # 專案架構
│   ├── data-flow.md             # 資料流程
│   ├── build-deploy.md          # 建置部署
│   └── code-review-flow.md      # Code Review 流程
│
├── 📂 .github/workflows/
│   └── deploy.yml               # GitHub Actions 部署設定
│
└── 📄 CODE-REVIEW-REPORT.md     # 代碼審查報告
```

---

> 本文件由技術文件工程師自動產生，基於專案原始碼分析。
