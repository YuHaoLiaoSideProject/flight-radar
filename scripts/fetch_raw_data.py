import datetime
import glob
import json
import os
import time

def generate_weekly_dates(weeks_ahead=40, trip_days=8):
    today = datetime.date.today()
    days_until_saturday = (5 - today.weekday()) % 7
    if days_until_saturday == 0:
        days_until_saturday = 7
    first_saturday = today + datetime.timedelta(days=days_until_saturday)

    dates = []
    for i in range(weeks_ahead):
        dep = first_saturday + datetime.timedelta(weeks=i)
        ret = dep + datetime.timedelta(days=trip_days)
        dates.append({
            "weekIndex": i + 1,
            "departureDate": dep.strftime("%Y-%m-%d"),
            "returnDate": ret.strftime("%Y-%m-%d")
        })
    return dates

def get_baseline_raw_prices(route_id, dates):
    base_map = {
        "TPE-NRT": 13652,
        "TPE-KIX": 14225,
        "TPE-FUK": 13719,
        "TSA-HND": 16440
    }
    base = base_map.get(route_id, 14000)
    flights = []
    
    for item in dates:
        dep = item["departureDate"]
        price = base
        if "2027-02-06" in dep: # 春節
            price = int(base * 2.5 + 3000)
        elif "2027-04-03" in dep: # 清明
            price = int(base * 2.0 + 2000)
        elif "2027-03-27" in dep: # 櫻花
            price = int(base * 1.4 + 1000)
        elif "2026-11" in dep: # 賞楓
            price = int(base * 1.3 + (2000 if route_id in ["TPE-KIX", "TPE-FUK"] else 1000))
        elif "2026-12-26" in dep: # 跨年
            price = int(base * 1.25 + 1000)
        elif "2027-02-27" in dep: # 228
            price = int(base * 1.15)
        elif "2026-09-26" in dep or "2026-10-10" in dep:
            price = int(base * 1.2)
        elif "2027-05" in dep and route_id == "TPE-FUK":
            price = base
        elif "2027-01" in dep or "2026-09" in dep:
            price = base
        else:
            price = int(base * 1.08)

        flights.append({
            **item,
            "price": price,
            "currency": "TWD"
        })
    return flights

def get_latest_snapshot(route_dir):
    """獲取該航線最新的一份日期快照檔案"""
    json_files = glob.glob(os.path.join(route_dir, "*.json"))
    # 過濾出符合 YYYY-MM-DD.json 的檔案並排序
    date_files = []
    for f in json_files:
        basename = os.path.basename(f)
        if basename.endswith(".json") and len(basename) == 15: # 2026-09-01.json
            date_files.append(f)
    date_files.sort()
    if not date_files:
        return None, None
    latest_file = date_files[-1]
    with open(latest_file, "r", encoding="utf-8") as f:
        return latest_file, json.load(f)

def is_price_data_identical(new_flights, previous_flights):
    """比對兩次 40 週快照的所有價格是否完全相同"""
    if not previous_flights or len(new_flights) != len(previous_flights):
        return False
    prev_map = {f"{x['departureDate']}_{x['returnDate']}": x.get("price") for x in previous_flights}
    for item in new_flights:
        k = f"{item['departureDate']}_{item['returnDate']}"
        if prev_map.get(k) != item.get("price"):
            return False
    return True

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    routes_file = os.path.join(script_dir, "../data/routes.json")
    raw_base_dir = os.path.join(script_dir, "../data/raw")

    with open(routes_file, "r", encoding="utf-8") as f:
        routes = json.load(f)

    dates = generate_weekly_dates(weeks_ahead=40, trip_days=8)
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    now_str = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S (UTC+8)")

    amadeus_id = os.getenv("AMADEUS_CLIENT_ID")
    amadeus_secret = os.getenv("AMADEUS_CLIENT_SECRET")
    amadeus_client = None
    if amadeus_id and amadeus_secret:
        try:
            from amadeus import Client
            amadeus_client = Client(client_id=amadeus_id, client_secret=amadeus_secret)
            print("✅ 成功連接 Amadeus 機票 API")
        except Exception as e:
            print(f"⚠️ Amadeus 初始化異常: {e}")

    for route in routes:
        airline = route["airline"]
        route_id = route["id"]
        # 目錄結構: data/raw/{airline}/{route_id}/
        route_dir = os.path.join(raw_base_dir, airline, route_id)
        os.makedirs(route_dir, exist_ok=True)
        today_snapshot_path = os.path.join(route_dir, f"{today_str}.json")

        print(f"📥 抓取快照: [{airline}] {route['name']} (查詢日: {today_str})...")

        # 1. 抓取今日 40 週票價
        today_flights = []
        if amadeus_client:
            for item in dates:
                try:
                    res = amadeus_client.shopping.flight_offers_search.get(
                        originLocationCode=route["origin"],
                        destinationLocationCode=route["destination"],
                        departureDate=item["departureDate"],
                        returnDate=item["returnDate"],
                        adults=1,
                        includedAirlineCodes=airline,
                        currencyCode="TWD",
                        max=3
                    )
                    price = float(res.data[0]['price']['total']) if res.data else None
                    today_flights.append({**item, "price": int(price) if price else None, "currency": "TWD"})
                    time.sleep(0.3)
                except Exception:
                    today_flights.append({**item, "price": None, "currency": "TWD"})
        else:
            today_flights = get_baseline_raw_prices(route_id, dates)

        # 2. 獲取前次快照進行差異比對
        latest_file_path, latest_snapshot = get_latest_snapshot(route_dir)

        # 如果已有前次快照，且比對發現所有價格完全相同，則不重複寫入新檔案
        if latest_snapshot and is_price_data_identical(today_flights, latest_snapshot.get("flights", [])):
            print(f"  └─ ⚖️ 與上次快照 ({os.path.basename(latest_file_path)}) 價格完全相同，略過重複寫入！")
            continue

        # 3. 價格有變動或為首次抓取，寫入獨立日期快照檔案
        snapshot_payload = {
            "routeId": route_id,
            "airline": airline,
            "origin": route["origin"],
            "destination": route["destination"],
            "queryDate": today_str,
            "capturedAt": now_str,
            "weeksCount": len(today_flights),
            "flights": today_flights
        }

        with open(today_snapshot_path, "w", encoding="utf-8") as sf:
            json.dump(snapshot_payload, sf, ensure_ascii=False, indent=2)

        print(f"  └─ 💾 已儲存新快照檔案: data/raw/{airline}/{route_id}/{today_str}.json")

    print("🎉 原始日期快照已更新至 data/raw/ (按日期獨立分檔，已簽入 Git)")

if __name__ == "__main__":
    main()
