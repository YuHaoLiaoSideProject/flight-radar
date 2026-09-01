# 資料流程

## 🔄 端到端資料流總覽

資料從外部 API 抓取，經 API 建構，最終在前端視覺化呈現。以下是各階段的詳細流程：

### 1️⃣ 資料抓取（每日快照）

從 Google Flights 或 Amadeus API 抓取票價，儲存為日期快照。

```mermaid
flowchart LR
    GF1["Google Flights"] -->|HTTP| FRD["fetch_raw_data.py"]
    AMA1["Amadeus API"] -->|REST| FRD
    RC["routes_config.json"] --> FRD
    FRD -->|JSON| RAW["data/raw/{airline}/{route}/<br/>YYYY-MM-DD.json"]
```

### 2️⃣ API 建構

從快照產生靜態 JSON API，供前端使用。

```mermaid
flowchart LR
    RAW["data/raw/ 快照"] -->|讀取| BA["build_api.py"]
    BA --> IDX["index.json"]
    BA --> AIR["airlines/{code}/index.json"]
    BA --> META["meta.json"]
    BA --> WK["weeks/*.json"]
```

### 3️⃣ 前端載入

前端從 API 載入資料，並行載入週資料。

```mermaid
flowchart LR
    IDX["index.json"] -->|fetch| APP["App.vue"]
    META["meta.json"] -->|fetch| APP
    WK["weeks/*.json"] -->|背景載入| APP
```

### 4️⃣ 視覺化

前端元件將資料轉換為圖表、卡片、表格。

```mermaid
flowchart LR
    APP["App.vue"] -->|weeklyData| PC["PriceChart.vue"]
    APP -->|topDeals| TC["TopDeals.vue"]
    APP -->|allWeeks| PT["PriceTable.vue"]
```

---

## 📥 階段一：資料抓取

```mermaid
flowchart TD
    START(["開始: fetch_raw_data.py"]) --> LOAD["讀取 routes_config.json<br/>載入 4 條航線"]

    LOAD --> GEN["generate_weekly_dates()<br/>從本週六起生成 40 週日期<br/>trip_days = 8"]

    GEN --> LOOP{遍歷每條航線}

    LOOP --> CHECK{"資料源選擇"}

    CHECK -->|"fast-flights<br/>(預設)"| FF["fast_flights.get_flights()<br/>Google Flights 爬取"]
    CHECK -->|"--amadeus"| AMA["amadeus.shopping.flight_offers_search()"]
    CHECK -->|"--no-fast-flights"| BASE["get_baseline_prices_for_route()<br/>基準行情"]

    FF --> COMPARE{"比對上次快照"}
    AMA --> COMPARE
    BASE --> COMPARE

    COMPARE -->|"價格不同"| WRITE["寫入新快照<br/>data/raw/{airline}/{route}/<br/>YYYY-MM-DD.json"]
    COMPARE -->|"價格相同"| SKIP["跳過（去重）"]

    WRITE --> NEXT{"還有下一條航線?"}
    SKIP --> NEXT

    NEXT -->|"是"| LOOP
    NEXT -->|"否"| DONE(["完成"])

    style START fill:#3B82F6,color:#fff
    style DONE fill:#10B981,color:#fff
    style WRITE fill:#F59E0B,color:#000
    style SKIP fill:#9CA3AF,color:#000
```

### 快照資料結構

```json
{
  "routeId": "TPE-NRT",
  "airline": "CI",
  "origin": "TPE",
  "destination": "NRT",
  "queryDate": "2025-09-01",
  "capturedAt": "2025-09-01 14:30:00 (UTC+8)",
  "dataSource": "fast-flights",
  "weeksCount": 40,
  "flights": [
    {
      "weekIndex": 1,
      "departureDate": "2025-09-06",
      "returnDate": "2025-09-14",
      "label": "09/06~09/14",
      "tag": null,
      "isHoliday": false,
      "price": 14744,
      "currency": "TWD"
    }
  ]
}
```

---

## 🏗️ 階段二：API 建構

```mermaid
flowchart TD
    START(["開始: build_api.py"]) --> LOAD["讀取 data/routes.json<br/>航線設定"]

    LOAD --> LOOP{遍歷每條航線}

    LOOP --> SNAP["讀取快照<br/>data/raw/{airline}/{route}/"]

    SNAP --> LATEST["取最新快照<br/>get_all_snapshots()"]

    LATEST --> PREV["取前一次快照<br/>（若有）"]

    PREV --> CALCHIST["計算歷史價格走勢<br/>history_map[dep_ret]<br/>→ [{queryDate, price}]"]

    CALCHIST --> CALCPRICE["計算每週資料<br/>• price: 當前價格<br/>• previousPrice: 前次價格<br/>• priceDiff: 漲跌幅<br/>• tag: 假期標籤"]

    CALCPRICE --> TOP5["計算統計<br/>• minPrice: 最低價<br/>• avgPrice: 平均價<br/>• topDeals: 前 5 低"]

    TOP5 --> WRTMETA["寫入 meta.json<br/>（輕量：含 topDeals）"]

    WRTMETA --> WRTWEEKS["寫入 weeks/{date}.json<br/>（每週詳細資料 + history）"]

    WRTWEEKS --> NEXT{"還有下一條?"}

    NEXT -->|"是"| LOOP
    NEXT -->|"否"| IDX

    IDX["生成各航司 index.json"] --> ROOT["生成全站 index.json<br/>• airlines[]<br/>• routes[]<br/>• config"]

    ROOT --> DONE(["完成"])

    style START fill:#3B82F6,color:#fff
    style DONE fill:#10B981,color:#fff
```

### meta.json 結構

```json
{
  "id": "TPE-NRT",
  "name": "台北桃園 ⇄ 東京成田",
  "airline": "CI",
  "airlineName": "中華航空",
  "weeksCount": 40,
  "latestQueryDate": "2025-09-01",
  "totalSnapshotsRecorded": 15,
  "stats": {
    "minPrice": 13106,
    "avgPrice": 16500
  },
  "topDeals": [
    {
      "weekIndex": 12,
      "departureDate": "2025-11-22",
      "returnDate": "2025-11-30",
      "label": "11/22~11/30",
      "tag": "賞楓銀杏旺季",
      "price": 13106
    }
  ]
}
```

### 週資料結構（含歷史）

```json
{
  "weekIndex": 12,
  "departureDate": "2025-11-22",
  "returnDate": "2025-11-30",
  "label": "11/22~11/30",
  "tag": "賞楓銀杏旺季",
  "isHoliday": true,
  "price": 13106,
  "previousPrice": 13450,
  "priceDiff": -344,
  "history": [
    { "queryDate": "2025-08-15", "price": 14200 },
    { "queryDate": "2025-08-22", "price": 13800 },
    { "queryDate": "2025-08-29", "price": 13450 },
    { "queryDate": "2025-09-01", "price": 13106 }
  ]
}
```

---

## 🎨 階段三：前端載入流程

```mermaid
sequenceDiagram
    participant U as 使用者
    participant APP as App.vue
    participant API as public/api/

    U->>APP: 開啟頁面
    APP->>API: fetch(index.json)
    API-->>APP: RootIndex（航線列表 + config）
    APP->>APP: selectedRouteId = config.defaultRoute

    APP->>API: fetch(meta.json)
    API-->>APP: RouteMeta（topDeals + stats）
    APP->>APP: 建立 RouteDetail

    par 並行背景載入（CONCURRENT=4）
        APP->>API: fetch(weeks/2025-09-06.json)
        API-->>APP: WeekItem (含 history)
        APP->>API: fetch(weeks/2025-09-13.json)
        API-->>APP: WeekItem (含 history)
        APP->>API: fetch(weeks/2025-09-20.json)
        API-->>APP: WeekItem (含 history)
        APP->>API: fetch(weeks/2025-09-27.json)
        API-->>APP: WeekItem (含 history)
    end

    APP->>APP: 計算 loadingProgress
    APP->>APP: 更新 weeklyData[]
    APP->>U: 顯示圖表 + 表格
```

### 前端資料流轉換

```mermaid
flowchart LR
    subgraph Input["📥 資料輸入"]
        A["index.json<br/>航線列表"]
        B["meta.json<br/>topDeals + stats"]
        C["weeks/*.json<br/>週票價 + history"]
    end

    subgraph Transform["🔄 轉換處理"]
        D["App.vue<br/>合併 RouteDetail"]
        E["computed: weeklyData<br/>排序 + 過濾"]
        F["computed: topDeals<br/>前 5 低價"]
        G["computed: allWeeks<br/>完整週列表"]
    end

    subgraph Output["📤 視覺化輸出"]
        H["PriceChart.vue<br/>Chart.js 折線圖"]
        I["TopDeals.vue<br/>最低價卡片"]
        J["PriceTable.vue<br/>可排序表格"]
    end

    A --> D
    B --> D
    C --> D
    D --> E
    D --> F
    D --> G
    E --> H
    F --> I
    G --> J
```

---

## 📊 價格歷史比對邏輯

### 計算當前 vs 前次價格

比較最新快照與前一次快照的價格，計算漲跌幅。

```mermaid
flowchart TD
    A["latest_snapshot.flights[i]"] -->|cur_price| COMP["priceDiff = cur_price - prev_price"]
    B["prev_snapshot.flights[i]"] -->|prev_price| COMP
    COMP -->|正數| UP["⬆️ 漲價"]
    COMP -->|負數| DOWN["⬇️ 降價"]
    COMP -->|零| SAME["➡️ 持平"]
```

### 歷史走勢聚合

將多次快照的價格依日期聚合，產生歷史走勢資料。

```mermaid
flowchart TD
    H1["snapshot 1<br/>2025-08-15"] -->|dep_ret key| HM["history_map"]
    H2["snapshot 2<br/>2025-08-22"] -->|dep_ret key| HM
    H3["snapshot 3<br/>2025-08-29"] -->|dep_ret key| HM
    H4["snapshot 4<br/>2025-09-01"] -->|dep_ret key| HM
    HM -->|"去重：連續相同價格不重複"| HIST["history[]<br/>依日期排序"]
```

### 假期標籤乘數

假期標籤會影響票價顯示的倍數與加成。

```mermaid
flowchart LR
    T1["春節"] -->|2.5x + 3000| P1[" NT$37,130"]
    T2["櫻花滿開"] -->|2.0x + 2000| P2[" NT$30,450"]
    T3["賞楓"] -->|1.3x + 1000| P3[" NT$18,747"]
    T4["跨年"] -->|1.25x + 1000| P4[" NT$18,065"]
    T5["一般"] -->|1.08x| P5[" NT$14,744"]
```

---

## 📁 目錄結構對應

```
資料流向圖:

data/raw/                          public/api/
├── CI/                            ├── index.json
│   ├── TPE-NRT/                   │   (全站索引)
│   │   ├── 2025-08-15.json ──┐    │
│   │   ├── 2025-08-22.json ──┤    ├── airlines/
│   │   ├── 2025-08-29.json ──┤    │   └── CI/
│   │   └── 2025-09-01.json ──┤    │       ├── index.json
│   ├── TPE-KIX/    build_api.py   │       ├── TPE-NRT/
│   ├── TPE-FUK/    ────────────→  │       │   ├── meta.json
│   └── TSA-HND/                   │       │   └── weeks/
│                                   │       │       ├── 2025-09-06.json
                                   │       │       ├── 2025-09-13.json
                                   │       │       └── ... (40 files)
                                   │       ├── TPE-KIX/
                                   │       └── ...
                                   └── (前端 fetch)
```

---

> 本文件由技術文件工程師自動產生，基於專案原始碼分析。
