import datetime
import json
import os
import time
import sys
from pathlib import Path

from shared import (
    DATA_DIR,
    generate_weekly_dates,
    get_baseline_prices_for_route,
    get_latest_snapshot,
)


def fetch_raw_flights_fast_flights(route, dates):
    """Use fast-flights (Google Flights scraper) to get raw prices"""
    try:
        from fast_flights import FlightQuery, Passengers, create_query, get_flights
    except ImportError:
        print("  ⚠️ fast-flights 未安裝，跳過")
        return None

    origin = route["origin"]
    destination = route["destination"]
    airline_code = route["airline"]

    flights = []
    errors = 0
    max_errors = 5

    for i, item in enumerate(dates):
        dep_date = item["departureDate"]
        ret_date = item["returnDate"]
        try:
            query = create_query(
                flights=[
                    FlightQuery(date=dep_date, from_airport=origin, to_airport=destination, airlines=[airline_code]),
                    FlightQuery(date=ret_date, from_airport=destination, to_airport=origin, airlines=[airline_code])
                ],
                trip="round-trip",
                passengers=Passengers(adults=1),
                currency="TWD",
                language="zh-TW"
            )

            results = get_flights(query)

            price = None
            for flight in results:
                flight_airlines = [a.upper() for a in flight.airlines]
                if any(airline_code.upper() in a for a in flight_airlines):
                    price = flight.price
                    break

            # No fallback — leave as null if airline not found
            flights.append({
                **item,
                "price": int(price) if price else None,
                "currency": "TWD"
            })

            if price is not None:
                errors = 0
                print(f"  [{i+1}/{len(dates)}] {dep_date} → {ret_date}: ✅ {price} TWD")
            else:
                print(f"  [{i+1}/{len(dates)}] {dep_date} → {ret_date}: ⚠️ N/A")

        except Exception as e:
            print(f"  [{i+1}/{len(dates)}] {dep_date} → {ret_date}: ❌ Error: {e}")
            flights.append({**item, "price": None, "currency": "TWD"})
            errors += 1

            if errors >= max_errors:
                print(f"  ⚠️ 連續 {max_errors} 次錯誤，中斷此航線查詢")
                for remaining in dates[i+1:]:
                    flights.append({**remaining, "price": None, "currency": "TWD"})
                break

        # Rate limiting: 1.5 seconds between requests
        if i < len(dates) - 1:
            time.sleep(1.5)

    return flights


def fetch_raw_flights_amadeus(route, dates):
    """Fallback: use Amadeus API if credentials available"""
    amadeus_id = os.getenv("AMADEUS_CLIENT_ID")
    amadeus_secret = os.getenv("AMADEUS_CLIENT_SECRET")

    if not amadeus_id or not amadeus_secret:
        return None

    try:
        from amadeus import Client
        amadeus_client = Client(client_id=amadeus_id, client_secret=amadeus_secret)
        print("  ✅ 使用 Amadeus API")
    except Exception as e:
        print(f"  ⚠️ Amadeus 初始化失敗: {e}")
        return None

    flights = []
    for item in dates:
        try:
            res = amadeus_client.shopping.flight_offers_search.get(
                originLocationCode=route["origin"],
                destinationLocationCode=route["destination"],
                departureDate=item["departureDate"],
                returnDate=item["returnDate"],
                adults=1,
                includedAirlineCodes=route["airline"],
                currencyCode="TWD",
                max=3
            )
            price = float(res.data[0]['price']['total']) if res.data else None
            flights.append({**item, "price": int(price) if price else None, "currency": "TWD"})
            time.sleep(0.3)
        except Exception:
            flights.append({**item, "price": None, "currency": "TWD"})

    return flights


def is_price_data_identical(new_flights, previous_flights):
    """Compare two 40-week snapshots to see if all prices are identical"""
    if not previous_flights or len(new_flights) != len(previous_flights):
        return False
    prev_map = {f"{x['departureDate']}_{x['returnDate']}": x.get("price") for x in previous_flights}
    for item in new_flights:
        k = f"{item['departureDate']}_{item['returnDate']}"
        if prev_map.get(k) != item.get("price"):
            return False
    return True


def main():
    routes_file = DATA_DIR / "routes.json"
    raw_base_dir = DATA_DIR / "raw"

    with open(routes_file, "r", encoding="utf-8") as f:
        routes = json.load(f)

    dates = generate_weekly_dates(weeks_ahead=40, trip_days=8)
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    now_str = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S (UTC+8)")

    # Determine data source priority
    use_fast_flights = "--no-fast-flights" not in sys.argv
    use_amadeus = "--amadeus" in sys.argv

    print(f"📊 資料來源: {'fast-flights (Google Flights)' if use_fast_flights else 'Amadeus' if use_amadeus else 'Baseline'}")
    print(f"📅 查詢 {len(dates)} 週, {len(routes)} 條航線\n")

    for route in routes:
        airline = route["airline"]
        route_id = route["id"]
        # Directory structure: data/raw/{airline}/{route_id}/
        route_dir = os.path.join(raw_base_dir, airline, route_id)
        os.makedirs(route_dir, exist_ok=True)
        today_snapshot_path = os.path.join(route_dir, f"{today_str}.json")

        print(f"📥 抓取快照: [{airline}] {route['name']} (查詢日: {today_str})...")

        # 1. Fetch today's 40-week prices
        today_flights = None

        if use_fast_flights and not use_amadeus:
            print(f"  📡 使用 fast-flights 查詢 Google Flights...")
            today_flights = fetch_raw_flights_fast_flights(route, dates)

        if today_flights is None and use_amadeus:
            today_flights = fetch_raw_flights_amadeus(route, dates)

        if today_flights is None:
            print(f"  📋 使用基準行情資料 (fallback)")
            today_flights = get_baseline_prices_for_route(route_id, dates)
            for f in today_flights:
                f["currency"] = "TWD"

        # 2. Get previous snapshot for comparison
        latest_file_path, latest_snapshot = get_latest_snapshot(route_dir)

        # If prices haven't changed, skip writing new file
        if latest_snapshot and is_price_data_identical(today_flights, latest_snapshot.get("flights", [])):
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
            "dataSource": "fast-flights" if use_fast_flights else "amadeus" if use_amadeus else "baseline",
            "weeksCount": len(today_flights),
            "flights": today_flights
        }

        with open(today_snapshot_path, "w", encoding="utf-8") as sf:
            json.dump(snapshot_payload, sf, ensure_ascii=False, indent=2)

        print(f"  └─ 💾 已儲存新快照檔案: data/raw/{airline}/{route_id}/{today_str}.json")

    print("\n🎉 原始日期快照已更新至 data/raw/ (按日期獨立分檔)")


if __name__ == "__main__":
    main()
