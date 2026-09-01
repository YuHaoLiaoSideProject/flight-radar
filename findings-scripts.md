# Scripts Code Review Findings

## Summary
- Critical: 1
- Major: 8
- Minor: 8
- Suggestion: 4

## Findings

### [S-001] 嚴重度：Critical
- **檔案**: fetch_flights.py:17-34 / build_api.py:8-25
- **問題**: `get_holiday_tag()` 將日期硬編碼為 2026-09 至 2027-06 的範圍。當系統運行超過此時間窗口後（例如 2027 年 7 月之後），所有日期都將回傳 `None`，導致全年無任何假期標籤，前端顯示異常且 fallback 價格邏輯失效（見 S-002）。此外 emoji 在字串比較（`"春節" in tag`）中可能導致匹配失敗。
- **建議**:
  1. 將 holiday 配置外化至 JSON/YAML 檔案，每年更新一次，或使用 `chinese-calendar` 等第三方庫動態計算。
  2. 若要維持硬編碼，至少加入年份動態計算邏輯（相對於當前年份偏移），並在腳本啟動時驗證日期範圍是否覆蓋 `weeks_ahead` 40 週。
  3. 字串匹配時忽略 emoji（如用 `tag and "春節" in tag.split(" ")[-1]` 或將 emoji 與文字分開存放）。

---

### [S-002] 嚴重度：Major
- **檔案**: fetch_flights.py:55-76 / build_api.py 未使用但 fetch_raw_data.py:31-63
- **問題**: `get_baseline_prices()` 與 `get_baseline_raw_prices()` 是近乎相同的 fallback 函式，但使用不同策略：fetch_flights.py 用 tag 字串匹配（如 `"春節" in tag`），fetch_raw_data.py 用日期字串比對（如 `"2027-02-06" in dep`）。兩者邏輯不一致，且都依賴硬編碼的年份。當 holidays 配置變更時，必須同步修改兩處，極易遺漏。
- **建議**: 抽取為共用模組（如 `scripts/shared.py`），單一實作 holiday → price multiplier 映射，所有腳本引用同一份邏輯。

---

### [S-003] 嚴重度：Major
- **檔案**: fetch_raw_data.py:7 / fetch_flights.py:47
- **問題**: `generate_weekly_dates()` 在 fetch_raw_data.py 和 fetch_flights.py 中完全複製貼上。若修改週數計算邏輯（如加入跳過特定週的功能），必須同步兩處。此外，兩個腳本使用不同的 trip_days 預設值（均為 8，但 fetch_raw_data.py 的 main 中未傳入），且與 `routes_config.json` 中的 `stayDays` 欄位各自獨立。
- **建議**: 抽取至共用模組，並考慮將 `weeks_ahead` 與 `trip_days` 統一從設定檔讀取。

---

### [S-004] 嚴重度：Major
- **檔案**: fetch_raw_data.py:90-140 / fetch_flights.py:105-158
- **問題**: `fetch_raw_flights_fast_flights()` 與 `fetch_flights_fast_flights()` 幾乎完全重複（~50 行），僅差在結果寫入的 dict 結構略有不同（raw 版多 `"currency": "TWD"`）。同樣問題也出現在 `fetch_raw_flights_amadeus()` 與 `fetch_flights_amadeus()`。
- **建議**: 抽取為共用的 fetch 函式，由呼叫端決定輸出結構。減少 ~100 行重複程式碼。

---

### [S-005] 嚴重度：Major
- **檔案**: fetch_raw_data.py:4 / fetch_flights.py:1 / build_api.py:1
- **問題**: `get_holiday_tag()` 在 fetch_flights.py 和 build_api.py 中完全複製（~25 行）。fetch_raw_data.py 則用另一套硬編碼日期比對取代之。三處重複，三套邏輯。
- **建議**: 統一為單一模組函式。

---

### [S-006] 嚴重度：Major
- **檔案**: fetch_raw_data.py:123 / fetch_flights.py:138
- **問題**: 變數 `stay_days = route.get("stayDays", trip_days)` 被賦值但從未使用。在 `FlightQuery` 建構中完全沒有用到這個值，表示 trip 天數的 config 設定形同虛設，使用者在 routes_config.json 中設定不同的 stayDays 不會有任何效果。
- **建議**: 要麼將 `stay_days` 傳入 `FlightQuery` 相關邏輯（若 fast-flights API 支援），要麼移除此無用變數避免誤導。應確認 route 的 stayDays 是否真的影響了查詢結果。

---

### [S-007] 嚴重度：Major
- **檔案**: fetch_raw_data.py:158 / fetch_flights.py:167 / build_api.py:53
- **問題**: 配置檔路徑不一致 — fetch_raw_data.py 讀取 `data/routes.json`，fetch_flights.py 讀取 `scripts/routes_config.json`，build_api.py 也讀取 `data/routes.json`。目前兩檔案內容相同（已驗證），但這意味著存在兩份必須同步的配置。若有人只修改其中一份，行為將不一致。
- **建議**: 統一使用一個路徑（建議 `scripts/routes_config.json` 或專門的 `config/routes.json`），其他腳本引用同一來源。可用符號連結或在共用模組中定義 `CONFIG_PATH`。

---

### [S-008] 嚴重度：Major
- **檔案**: fetch_raw_data.py:128-131
- **問題**: `max_errors = 5` 的中斷策略缺少 rate-limit 恢復機制。當 Google Flights 因暫時性問題（如 CAPTCHA、網路抖動）導致連續 5 次失敗時，整條航線剩餘所有 40 週都被填為 `None` 並放棄。但 1.5 秒的 rate-limit 间隔本身就可能觸發 Google 的反爬蟲機制。此外，`errors` 計數器在成功時重置，但若失敗-成功交替出現，不會觸發中斷——真正危險的「間歇性反爬蟲」模式完全不受保護。
- **建議**:
  1. 加入指數退避（exponential backoff），如在連續失敗時逐步增加 sleep 時間。
  2. 考慮加入 jitter 避免固定的 1.5 秒 pattern 被偵測。
  3. 總失敗率超過某閾值（如 30%）時也應中斷。

---

### [S-009] 嚴重度：Minor
- **檔案**: fetch_raw_data.py:80-83 / build_api.py:37-40
- **問題**: `get_latest_snapshot()` / `get_all_snapshots()` 用 `len(basename) == 15` 作為 YYYY-MM-DD.json 的過濾條件。這是脆弱的 magic number 檢查——任何其他 15 字元的 .json 檔名（如 `abc-def-gh.json`）都會被錯誤納入。此外，glob 全域掃描後再逐一過濾效率低。
- **建議**: 使用 regex `^\d{4}-\d{2}-\d{2}\.json$` 過濾，或改用 `datetime.strptime` 嘗試解析檔名，解析失敗則跳過。

---

### [S-010] 嚴重度：Minor
- **檔案**: build_api.py:37-40
- **問題**: `get_all_snapshots()` 中的 `except Exception: pass` 完全吞掉例外。若 JSON 檔損壞，不會有任何日誌輸出，使用者無法知道某個快照被跳過。
- **建議**: 至少加入 `print(f"⚠️ 讀取 {f} 失敗: {e}")` 或使用 `logging.warning()`。

---

### [S-011] 嚴重度：Minor
- **檔案**: fetch_raw_data.py:108-137, 153-160 / fetch_flights.py:123-158, 162-178
- **問題**: 所有 API 呼叫（fast-flights、Amadeus）都用裸 `except Exception` 捕獲，僅印出簡短訊息。無法區分網路錯誤、API 配額耗盡、資料格式異常等不同故障類型，也無法決定是否重試。
- **建議**: 針對不同例外類型做分類處理。至少在 fallback 到 baseline 時提醒使用者資料可能不準確。

---

### [S-012] 嚴重度：Minor
- **檔案**: 所有 .py 檔案
- **問題**: 全部腳本缺乏 type hints。函式簽章如 `def fetch_raw_flights_fast_flights(route, dates, trip_days=8)` 無法讓 IDE 或 mypy 驗證參數型別，`route` 的結構（需含 origin/destination/airline 等欄位）僅靠隱含約定。
- **建議**: 至少加入函式簽章的 type hints（如 `route: dict[str, str]`），若使用 dataclass 或 TypedDict 更佳。

---

### [S-013] 嚴重度：Minor
- **檔案**: 所有 .py 檔案
- **問題**: 大多數函式缺乏 docstring，僅 `get_baseline_raw_prices` 等少數有簡單說明。`get_holiday_tag`、`is_price_data_identical` 等核心邏輯無文件。
- **建議**: 為所有公開函式加入 docstring（至少說明參數與回傳值）。

---

### [S-014] 嚴重度：Minor
- **檔案**: build_api.py:89-95
- **問題**: `price_diff` 計算在 `cur_price` 或 `prev_price` 為 None 時回傳 0，這與「無變動」的語義相同，前端無法區分「真的沒變」和「上次沒資料」。此外若 `cur_price` 為 None 但 `prev_price` 有值（航線某週從有價變成 N/A），此異常狀態被靜默忽略。
- **建議**: 回傳 None 或特殊值（如 `"N/A"`）以區分「無資料」與「無變動」，或在 history 中加入標記。

---

### [S-015] 嚴重度：Minor
- **檔案**: fetch_flights.py:190-200 / build_api.py:140-148
- **問題**: `main()` 函式過長（fetch_flights.py ~60 行、build_api.py ~100 行），混合了配置讀取、資料抓取、統計計算、檔案寫入等多種責任，違反 Single Responsibility Principle。
- **建議**: 拆分為 `load_config()`、`process_route()`、`write_airline_index()` 等子函式。

---

### [S-016] 嚴重度：Minor
- **檔案**: fetch_raw_data.py:163-172 / fetch_flights.py:195-203
- **問題**: 硬編碼路徑 `../data/`、`../public/data/` 散布在各腳本中。若目錄結構變更（如迁移到 monorepo 或 Docker），需逐檔修改。
- **建議**: 在共用模組或設定檔中定義 `BASE_DIR`、`DATA_DIR`、`OUTPUT_DIR` 等常數。

---

### [S-017] 嚴重度：Suggestion
- **檔案**: 專案根目錄
- **問題**: 缺少 `requirements.txt` 或 `pyproject.toml`。腳本依賴 `fast_flights`、`amadeus` 等第三方庫，但新使用者無法知道該安裝什麼。
- **建議**: 建立 `requirements.txt`，至少列出 `amadeus`，並註明 `fast_flights` 為 optional（可選）依賴。

---

### [S-018] 嚴重度：Suggestion
- **檔案**: 所有 .py 檔案
- **問題**: 使用 `print()` 作為所有輸出方式，無日誌等級區分。在 CI/CD 排程執行時，無法過濾 error vs info 訊息。
- **建議**: 引入 `logging` 模組，設定適當的 log level（INFO for progress, WARNING for fallback, ERROR for failures）。

---

### [S-019] 嚴重度：Suggestion
- **檔案**: 所有 .py 檔案
- **問題**: 使用 `os.path` 進行路徑操作。Python 3.4+ 的 `pathlib.Path` 提供更語意化、更跨平台的路徑操作方式。
- **建議**: 將 `os.path.join(script_dir, "../data/routes.json")` 改為 `Path(__file__).parent.parent / "data" / "routes.json"` 等寫法，提升可讀性。

---

### [S-020] 嚴重度：Suggestion
- **檔案**: fetch_flights.py / build_api.py
- **問題**: 缺乏單元測試。`get_holiday_tag()`、`generate_weekly_dates()`、`is_price_data_identical()` 等純函式非常適合單元測試，但目前無測試覆蓋。
- **建議**: 為純邏輯函式撰寫 pytest 測試，特別是 holiday tag 的邊界日期、週數生成的起始日邏輯、價格比對的 null 處理。
