# 建置部署

## 🔧 開發環境設定

```mermaid
flowchart TD
    A["📋 前置需求<br/>Node.js >= 20<br/>npm >= 10<br/>Python 3.x"] --> B["git clone repo"]

    B --> C["安裝 Node.js 依賴"]
    C --> C1["npm install"]

    B --> D["安裝 Python 依賴"]
    D --> D1["pip install requests beautifulsoup4<br/>pip install fast-flights (選用)"]

    C1 --> E["啟動開發伺服器"]
    E --> E1["npm run dev"]
    E1 --> F["🌐 localhost:5173"]

    D1 --> G["執行爬蟲腳本"]
    G --> G1["python scripts/fetch_raw_data.py"]
    G1 --> H["data/raw/ 產生快照"]

    H --> I["建構 API"]
    I --> I1["python scripts/build_api.py"]
    I1 --> J["public/api/ 產生 API 檔"]

    J --> E1

    style A fill:#F59E0B,color:#000
    style F fill:#10B981,color:#fff
```

---

## 📦 npm Scripts 說明

| 命令 | 說明 | 用途 |
|------|------|------|
| `npm run dev` | 啟動 Vite 開發伺服器 | 本地開發（localhost:5173） |
| `npm run build` | `vue-tsc -b && vite build` | 型別檢查 + 生產建置 |
| `npm run preview` | 預覽建置結果 | 確認 dist/ 產出 |
| `npm run lint` | ESLint 檢查 | 程式碼品質 |
| `npm run lint:fix` | ESLint 自動修正 | 快速修復 |
| `npm run format` | Prettier 格式化 | 程式碼風格 |
| `npm run type-check` | Vue TypeScript 型別檢查 | 型別安全 |

---

## 🐍 Python 腳本執行順序

```mermaid
flowchart LR
    subgraph Step1["步驟 1: 抓取原始資料"]
        A["fetch_raw_data.py"]
        A -->|每日執行| B["data/raw/{airline}/{route}/<br/>YYYY-MM-DD.json"]
    end

    subgraph Step2["步驟 2: 建構 API"]
        C["build_api.py"]
        C -->|讀取快照| B
        C -->|寫入| D["public/api/"]
    end

    subgraph Step3["步驟 3: 建置前端"]
        E["npm run build"]
        E -->|複製 public/| F["dist/"]
    end

    B --> C
    D --> E

    style Step1 fill:#3B82F6,color:#fff
    style Step2 fill:#8B5CF6,color:#fff
    style Step3 fill:#10B981,color:#fff
```

### 腳本參數

```bash
# fetch_raw_data.py
python scripts/fetch_raw_data.py                  # 使用 fast-flights（預設）
python scripts/fetch_raw_data.py --amadeus         # 使用 Amadeus API
python scripts/fetch_raw_data.py --no-fast-flights # 使用基準行情

# fetch_flights.py (已棄用，改用 fetch_raw_data.py)
python scripts/fetch_flights.py                    # 直接輸出到 public/data/
```

---

## 🚀 GitHub Actions CI/CD 流程

```mermaid
flowchart TD
    subgraph Trigger["觸發條件"]
        T1["git push main"]
        T2["workflow_dispatch<br/>手動觸發"]
    end

    subgraph BuildJob["🏗️ Build Job"]
        B1["Checkout code"] --> B2["Setup Node.js 22"]
        B2 --> B3["Setup Python 3.x"]
        B3 --> B4["pip install<br/>requests beautifulsoup4"]
        B4 --> B5{"skip_crawler?"}

        B5 -->|"false (預設)"| B6["python fetch_raw_data.py<br/>執行爬蟲"]
        B5 -->|"true (跳過)"| B7["跳過爬蟲"]

        B6 --> B8["python build_api.py<br/>建構 API"]
        B7 --> B8

        B8 --> B9["npm ci<br/>安裝依賴"]
        B9 --> B10["npm run build<br/>建置前端"]
        B10 --> B11["cp CNAME dist/<br/>自訂網域"]
        B11 --> B12["Upload artifact<br/>dist/ 目錄"]
    end

    subgraph DeployJob["🚀 Deploy Job"]
        D1["Deploy to GitHub Pages"]
        D2["产出部署 URL"]
    end

    Trigger --> BuildJob
    B12 --> DeployJob

    style Trigger fill:#F59E0B,color:#000
    style BuildJob fill:#3B82F6,color:#fff
    style DeployJob fill:#10B981,color:#fff
```

---

## 📤 部署到 GitHub Pages

```mermaid
sequenceDiagram
    participant Dev as 開發者
    participant GH as GitHub
    participant CI as GitHub Actions
    participant GP as GitHub Pages

    Dev->>GH: git push main
    GH->>CI: 觸發 deploy.yml

    par 平行環境設定
        CI->>CI: Setup Node.js 22
        CI->>CI: Setup Python 3.x
    end

    CI->>CI: pip install dependencies

    alt workflow_dispatch && skip_crawler=false
        CI->>CI: python fetch_raw_data.py
    end

    CI->>CI: python build_api.py
    CI->>CI: npm ci && npm run build
    CI->>CI: cp CNAME dist/

    CI->>GH: Upload artifact (dist/)
    GH->>GP: Deploy to GitHub Pages
    GP-->>Dev: 🌐 部署完成

    Note over Dev,GP: 全程約 2-3 分鐘
```

---

## 🔨 Vite 建置設定

```mermaid
flowchart LR
    subgraph Input["📦 建置輸入"]
        SRC["src/**/*.vue + .ts"]
        PUB["public/api/**/*.json"]
    end

    subgraph Vite["⚡ Vite 處理"]
        VUE["@vitejs/plugin-vue<br/>Vue SFC 編譯"]
        TS["vue-tsc<br/>TypeScript 檢查"]
        TW["Tailwind CSS<br/>樣式處理"]
        CHART["Chart.js<br/>manualChunks 分包"]
    end

    subgraph Output["📁 建置產出"]
        DIST["dist/"]
        JS["dist/assets/*.js"]
        CSS["dist/assets/*.css"]
        API["dist/api/**/*.json"]
    end

    SRC --> VUE
    SRC --> TS
    SRC --> TW
    PUB -->|直接複製| API
    VUE --> JS
    TW --> CSS
    CHART --> JS

    style Vite fill:#8B5CF6,color:#fff
```

### Vite 設定要點

| 設定 | 值 | 說明 |
|------|-----|------|
| `base` | `'./'` | 相對路徑，支援 GitHub Pages 子目錄 |
| `target` | `es2020` | 瀏覽器相容性 |
| `port` | `5173` | 開發伺服器端口 |
| `host` | `true` | 允許區域網路存取 |
| `manualChunks` | `chart-js` | Chart.js 獨立分包，減少主包大小 |

---

## 📋 完整開發流程

```mermaid
flowchart TD
    START(["開始"]) --> CLONE["git clone repo"]
    CLONE --> INSTALL["npm install + pip install"]

    INSTALL --> DEV["npm run dev<br/>啟動開發"]

    DEV --> CODE["撰寫程式碼"]
    CODE --> CHECK{"檢查"}

    CHECK -->|"TypeScript"| TC["npm run type-check"]
    CHECK -->|"ESLint"| LINT["npm run lint"]
    CHECK -->|"格式"| FMT["npm run format"]

    TC --> FIX["修正問題"]
    LINT --> FIX
    FMT --> FIX

    FIX --> CODE

    CHECK -->|"通過"| CRAWL["執行爬蟲<br/>python fetch_raw_data.py"]
    CRAWL --> BUILD_API["建構 API<br/>python build_api.py"]
    BUILD_API --> BUILD_FE["建置前端<br/>npm run build"]
    BUILD_FE --> PREVIEW["npm run preview<br/>預覽確認"]

    PREVIEW --> PUSH["git push main"]
    PUSH --> CI["GitHub Actions<br/>自動部署"]
    CI --> DEPLOY["GitHub Pages<br/>🌐 上線"]

    style START fill:#3B82F6,color:#fff
    style DEPLOY fill:#10B981,color:#fff
```

---

> 本文件由技術文件工程師自動產生，基於專案原始碼分析。
