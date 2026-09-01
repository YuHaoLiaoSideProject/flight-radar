# Config Code Review Findings

## Summary
- Critical: 1
- Major: 5
- Minor: 5
- Suggestion: 4

---

## Findings

### [C-001] 嚴重度：Critical
- **檔案**: `package.json`
- **問題**: 專案無任何 linting（ESLint）、程式碼格式化（Prettier）或 pre-commit hook（husky + lint-staged）配置。在無人值守的 CI/CD 流程中，無 lint 代表品質管控完全依賴人工 code review，風險極高。
- **建議**:
  1. 安裝 `eslint` + `@vue/eslint-config-typescript` + `eslint-plugin-vue`，建立 `eslint.config.js`。
  2. 安裝 `prettier` + `eslint-config-prettier`，確保格式化一致。
  3. 安裝 `husky` + `lint-staged`，在 pre-commit 階段自動執行 `eslint --fix` 和 `prettier --write`。
  4. 在 `package.json` 中加入 scripts：`"lint": "eslint src/"`、`"format": "prettier --write src/"`。

---

### [M-001] 嚴重度：Major
- **檔案**: `vite.config.ts:3-5`
- **問題**: Vite 配置過於精簡，缺少重要的 build 優化設定：
  - 無 `build.rollupOptions.output.manualChunks`：`chart.js`（~200KB）會與 Vue 捆綁在同一 chunk，影響首屏載入。
  - 無 `build.sourcemap` 設定：生產環境無 sourcemap 有利安全性，但開發除錯建議開啟。
  - 無 `resolve.alias`：專案未設定路徑別名（如 `@/` → `src/`），大型專案會造成 `../../` 深層 import。
- **建議**:
  ```ts
  export default defineConfig({
    plugins: [vue()],
    base: './',
    resolve: {
      alias: { '@': path.resolve(__dirname, 'src') }
    },
    build: {
      rollupOptions: {
        output: {
          manualChunks: { 'chart-js': ['chart.js'] }
        }
      }
    }
  })
  ```

---

### [M-002] 嚴重度：Major
- **檔案**: `package.json:10-16`
- **問題**: 所有依賴使用 `^`（caret）版本範圍，無 lockfile 策略保障。雖然 `package-lock.json` 存在，但在不同環境 `npm install` 可能拉到不同次版本，造成「在我機器上能跑」的問題。
- **建議**:
  1. CI/CD 中已使用 `npm ci`（✓ 正確），但本地開發應也建議使用 `npm ci` 或加 `"engines"` 欄位锁定 Node 版本。
  2. 在 `package.json` 加入：
     ```json
     "engines": { "node": ">=20", "npm": ">=10" }
     ```
  3. 考慮對關鍵依賴（vue、vite）改用精確版本或 `~` 範圍。

---

### [M-003] 嚴重度：Major
- **檔案**: `index.html:5`
- **問題**: Favicon 使用 `data:image/svg+xml` 內嵌 SVG，其中包含未經 URL 編碼的 emoji（`✈️`）。部分舊版瀏覽器或嚴格 CSP 環境可能解析失敗。此外 `<html>` 缺少 `lang` 屬性以外的安全 headers。
- **建議**:
  1. 將 emoji 改為 URL 編碼格式或使用純文字 SVG 路徑。
  2. 建議在 `<head>` 加入基本 CSP meta tag（即使 GitHub Pages 有限制）：
     ```html
     <meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'">
     ```
  3. 考慮將 favicon 改為獨立 `/public/favicon.svg` 檔案，避免 data URI 編碼問題。

---

### [M-004] 嚴重度：Major
- **檔案**: `tsconfig.json:1-23`
- **問題**: TypeScript 配置缺少幾個重要選項：
  - 無 `baseUrl` / `paths`：無法使用路徑別名，與 Vite alias 不同步。
  - 無 `forceConsistentCasingInFileNames`：跨平台（Windows vs macOS）大小寫不一致問題。
  - `include` 未包含 `env.d.ts` 或 `src/**/*.d.ts` 以外的類型定義檔。
- **建議**:
  ```json
  {
    "compilerOptions": {
      "baseUrl": ".",
      "paths": { "@/*": ["src/*"] },
      "forceConsistentCasingInFileNames": true
    }
  }
  ```

---

### [M-005] 嚴重度：Major
- **檔案**: `.gitignore`
- **問題**: `.gitignore` 缺少多個應忽略的檔案/目錄：
  - `.env*`（環境變數檔案，含 API keys）
  - `.venv/`（Python virtual environment，目錄存在但未忽略）
  - `*.local`（Vite 本地配置覆蓋檔）
  - `.DS_Store`（macOS 系統檔）
  - `dist/` 已忽略（✓），但 `public/` 被忽略可能導致靜態資源丟失（需確認意圖）。
- **建議**:
  ```
  # Environment files
  .env
  .env.*
  *.local

  # OS files
  .DS_Store
  Thumbs.db

  # Python
  .venv/
  __pycache__/
  *.pyc
  ```

---

### [m-001] 嚴重度：Minor
- **檔案**: `tailwind.config.js:8-15`
- **問題**: `brand` 色彩只定義了 50、100、500、600、700 五個色階，缺少 200、300、400、800、900。使用 `bg-brand-200` 等會產生未定義的 class，Tailwind 會 fallback 到透明或報錯。
- **建議**: 補齊完整色階（至少 50-900），或使用 Tailwind 內建色系（如 `blue`）並透過 `theme.extend.colors.brand` 映射。

---

### [m-002] 嚴重度：Minor
- **檔案**: `vite.config.ts`
- **問題**: 缺少 `server` 設定，開發伺服器預設监听 `localhost:5173`，若需從外部設備（手機測試 RWD）存取，需手動加 `--host`。
- **建議**:
  ```ts
  server: {
    host: true,  // 允許外部存取
    port: 5173
  }
  ```

---

### [m-003] 嚴重度：Minor
- **檔案**: `index.html:8-10`
- **問題**: `<body>` 直接使用 Tailwind utility classes（`bg-slate-900 text-slate-100 min-h-screen`），但 `index.html` 不是 Tailwind 掃描的模板（`tailwind.config.js` 的 `content` 已包含 `./index.html`，✓ 正確）。然而 `<div id="app">` 後無 loading 狀態或 noscript fallback。
- **建議**: 加入基本的 loading indicator 或 `<noscript>` 提示：
  ```html
  <div id="app">
    <noscript>請啟用 JavaScript 以使用本應用程式。</noscript>
  </div>
  ```

---

### [m-004] 嚴重度：Minor
- **檔案**: `postcss.config.js`
- **問題**: PostCSS 配置正確但可加入 `cssnano` 進行 CSS 壓縮優化。
- **建議**:
  ```js
  export default {
    plugins: {
      tailwindcss: {},
      autoprefixer: {},
      ...(process.env.NODE_ENV === 'production' ? { cssnano: { preset: 'default' } } : {})
    }
  }
  ```
  並安裝 `cssnano` 作為 devDependency。

---

### [m-005] 嚴重度：Minor
- **檔案**: `README.md:52`
- **問題**: README 中的 GitHub URL 使用 `your-username` 佔位符，應替換為實際 repo URL（`YuHaoLiaoSideProject/flight-radar`）。
- **建議**: 將 `https://github.com/your-username/flight-radar.git` 改為 `https://github.com/YuHaoLiaoSideProject/flight-radar.git`。

---

### [S-001] 嚴重度：Suggestion
- **檔案**: `package.json`
- **問題**: `scripts` 中缺少常用開發便利指令。
- **建議**:
  ```json
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc -b && vite build",
    "preview": "vite preview",
    "lint": "eslint src/",
    "lint:fix": "eslint src/ --fix",
    "format": "prettier --write src/",
    "type-check": "vue-tsc --noEmit"
  }
  ```

---

### [S-002] 嚴重度：Suggestion
- **檔案**: `vite.config.ts`
- **問題**: 未設定 `build.target`，預設為 `modules`（ES2015+），但 `tsconfig.json` target 為 `ES2020`，兩者不一致可能造成最終 bundle 與預期不符。
- **建議**: 明確指定 `build.target: 'es2020'`，與 TypeScript 配置對齊。

---

### [S-003] 嚴重度：Suggestion
- **檔案**: `package.json`
- **問題**: 缺少 `description`、`author`、`license` 等 metadata 欄位，不利於 npm registry 發布（雖然專案為 `private: true`）。
- **建議**: 補充基本 metadata：
  ```json
  "description": "華航週末 40 週機票雷達 - 自動監控並視覺化中華航空日本航線票價",
  "author": "YuHaoLiao",
  "license": "MIT"
  ```

---

### [S-004] 嚴重度：Suggestion
- **檔案**: `tailwind.config.js`
- **問題**: 未使用 Tailwind 的 `darkMode` 設定，若未來需支援深色/淺色主題切換，需再修改。
- **建議**: 預先加入 `"darkMode": "class"` 以利未來擴充：
  ```js
  export default {
    darkMode: 'class',
    content: [...],
    ...
  }
  ```

---

## 總結

本專案整體架構合理，`tsconfig.json` 的 strict mode 設定良好，README 文件完整度高，CI/CD 流程（GitHub Actions + Pages）設計正確。主要風險在於**缺乏自動化品質管控工具鏈**（Critical），以及多項可預防的配置遺漏（Major）。建議優先處理 C-001（加入 ESLint + Prettier）和 M-005（.gitignore 完善），再逐步優化 build 設定與 DX 工具。
