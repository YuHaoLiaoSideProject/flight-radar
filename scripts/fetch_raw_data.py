"""
fetch_raw_data.py — 從 Google Flights / Amadeus 抓取原始日期快照
資料寫入 data/raw/{airline}/{route_id}/{YYYY-MM-DD}.json
後續由 build_api.py 讀取並產出 public/api/
"""

from __future__ import annotations

import datetime
import json
import os
import sys
from pathlib import Path

# 確保 scripts/ 在 import path 中
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from shared import (
    DATA_DIR,
    fetch_flights_amadeus,
    fetch_flights_fast_flights,
    generate_weekly_dates,
    get_latest_snapshot,
    is_price_data_identical,
)


def main() -> None:
    routes_file = DATA_DIR / "routes.json"
    raw_base_dir = DATA_DIR / "raw"

    with open(routes_file, "r", encoding="utf-8") as f:
        routes = json.load(f)

    dates = generate_weekly_dates(weeks_ahead=40, trip_days=8)
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    now_str = datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=8))
    ).strftime("%Y-%m-%d %H:%M:%S (UTC+8)")

    # Determine data source priority
    use_fast_flights = "--no-fast-flights" not in sys.argv
    use_amadeus = "--amadeus" in sys.argv

    print(
        f"📊 資料來源: "
        f"{'fast-flights (Google Flights)' if use_fast_flights else 'Amadeus' if use_amadeus else 'N/A (all sources disabled)'}"
    )
    print(f"📅 查詢 {len(dates)} 週, {len(routes)} 條航線\n")

    for route in routes:
        airline = route["airline"]
        route_id = route["id"]
        # Directory structure: data/raw/{airline}/{route_id}/
        route_dir = raw_base_dir / airline / route_id
        route_dir.mkdir(parents=True, exist_ok=True)
        today_snapshot_path = route_dir / f"{today_str}.json"

        print(f"📥 抓取快照: [{airline}] {route['name']} (查詢日: {today_str})...")

        # 1. Fetch today's 40-week prices
        today_flights: list[dict] | None = None

        if use_fast_flights and not use_amadeus:
            print("  📡 使用 fast-flights 查詢 Google Flights...")
            today_flights = fetch_flights_fast_flights(route, dates, script_name="fetch_raw_data")

        if today_flights is None and use_amadeus:
            today_flights = fetch_flights_amadeus(route, dates, script_name="fetch_raw_data")

        if today_flights is None:
            print("  ⚠️ 所有資料來源皆失敗，設為無資料")
            today_flights = [{**item, "price": None, "currency": "TWD"} for item in dates]

        # 2. Get previous snapshot for comparison
        latest_file_path, latest_snapshot = get_latest_snapshot(route_dir)

        if latest_snapshot and is_price_data_identical(
            today_flights, latest_snapshot.get("flights", [])
        ):
            print(f"  └─ ⚖️ 與上次快照 ({os.path.basename(latest_file_path)}) 價格完全相同，略過重複寫入！")
            continue

        # 3. Write new snapshot
        snapshot_payload = {
            "routeId": route_id,
            "airline": airline,
            "origin": route["origin"],
            "destination": route["destination"],
            "queryDate": today_str,
            "capturedAt": now_str,
            "dataSource": "fast-flights" if use_fast_flights else "amadeus" if use_amadeus else "unknown",
            "weeksCount": len(today_flights),
            "flights": today_flights,
        }

        with open(today_snapshot_path, "w", encoding="utf-8") as sf:
            json.dump(snapshot_payload, sf, ensure_ascii=False, indent=2)

        print(f"  └─ 💾 已儲存新快照檔案: data/raw/{airline}/{route_id}/{today_str}.json")

    print("\n🎉 原始日期快照已更新至 data/raw/ (按日期獨立分檔)")


if __name__ == "__main__":
    main()
