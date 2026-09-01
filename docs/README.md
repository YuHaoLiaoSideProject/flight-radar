# flight-radar 文件

## 📁 文件導覽

| 文件 | 說明 |
|------|------|
| [專案架構](./architecture.md) | 系統架構與模組關係 |
| [資料流程](./data-flow.md) | 從爬蟲到前端的完整資料流 |
| [建置部署](./build-deploy.md) | 開發環境建置與 CI/CD 流程 |
| [Code Review 流程](./code-review-flow.md) | 代碼審查執行流程與結果 |
| [Code Review 報告](../CODE-REVIEW-REPORT.md) | 代碼審查完整報告 |

## 🗺️ 快速總覽

### 📥 資料抓取層

外部資料源透過 Python 腳本抓取，儲存為日期快照。

```mermaid
graph LR
    GF["🌐 Google Flights"] -->|爬取| FRD["fetch_raw_data.py"]
    AMA["🌐 Amadeus API"] -->|REST| FRD
    RC["routes_config.json<br/>4 條航線"] --> FRD
    SH["shared.py<br/>共用工具庫"] -.->|工具函式| FRD
    FRD --> RAW["data/raw/<br/>日期快照"]
```

### 🏗️ API 建構層

從日期快照產生前端可用的靜態 API 檔案。

```mermaid
graph LR
    RAW["data/raw/<br/>日期快照"] --> BA["build_api.py"]
    BA --> API["public/api/<br/>前端 API"]
    SH["shared.py"] -.->|工具函式| BA
```

### 🎨 前端 Vue 3

前端從 API 載入資料，透過元件呈現票價資訊。

```mermaid
graph TB
    API["public/api/"] -->|fetch| APP["App.vue<br/>主控元件"]
    APP --> NAV["Navbar.vue<br/>導覽列"]
    APP --> TC["TopDeals.vue<br/>最低價推薦"]
    APP --> PC["PriceChart.vue<br/>價格走勢圖"]
    APP --> PT["PriceTable.vue<br/>週價格表"]
```

### 🚀 部署

前端建置後透過 GitHub Actions 部署到 GitHub Pages。

```mermaid
graph LR
    APP["App.vue"] -->|vite build| GH["GitHub Actions"]
    GH --> GHP["GitHub Pages"]
```
