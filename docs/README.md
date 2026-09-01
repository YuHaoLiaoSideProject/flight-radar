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

```mermaid
graph TB
    subgraph External["🌐 外部資料源"]
        GF[Google Flights]
        AMA[Amadeus API]
    end

    subgraph Python["🐍 Python 腳本層"]
        FRD[fetch_raw_data.py<br/>原始快照抓取]
        FF[fetch_flights.py<br/>即時票價查詢]
        BA[build_api.py<br/>API 建構器]
        SH[shared.py<br/>共用工具庫]
    end

    subgraph Storage["💾 資料儲存"]
        RAW[data/raw/<br/>日期快照]
        RC[routes_config.json<br/>航線設定]
        API[public/api/<br/>前端 API]
    end

    subgraph Frontend["🎨 前端 Vue 3"]
        APP[App.vue<br/>主控元件]
        NAV[Navbar.vue<br/>導覽列]
        TC[TopDeals.vue<br/>最低價推薦]
        PC[PriceChart.vue<br/>價格走勢圖]
        PT[PriceTable.vue<br/>週價格表]
    end

    subgraph Deploy["🚀 部署"]
        GH[GitHub Actions]
        GHP[GitHub Pages]
    end

    GF --> FRD
    AMA --> FRD
    GF --> FF
    AMA --> FF
    SH --> FRD
    SH --> FF
    SH --> BA
    RC --> FRD
    RC --> FF

    FRD --> RAW
    RAW --> BA
    BA --> API

    API --> APP
    APP --> NAV
    APP --> TC
    APP --> PC
    APP --> PT

    GH --> GHP
    API -.->|建構時複製| GH
```

---

> 本文件由技術文件工程師自動產生，基於專案原始碼分析。
