import datetime
import json
import os
import time
import sys

from shared import (
    CONFIG_PATH,
    PUBLIC_DIR,
    generate_weekly_dates,
    get_baseline_prices_for_route,
)


def fetch_flights_fast_flights(route, week_dates):
    """Use fast-flights (Google Flights scraper) to get real prices"""
    try:
        from fast_flights import FlightQuery, Passengers, create_query, get_flights
    except ImportError:
        print("  ⚠️ fast-flights 未安裝，跳過")
        return None

    origin = route["origin"]
    destination = route["destination"]
    airline_code = route["airline"]
    route_id = route["id"]

    weekly_data = []
    errors = 0
    max_errors = 5  # Allow up to 5 consecutive errors before aborting route

    for i, item in enumerate(week_dates):
        dep_date = item["departureDate"]
        ret_date = item["returnDate"]
        try:
            # Create round-trip query with airline filter
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

            # Find cheapest flight for this airline only
            price = None
            for flight in results:
                flight_airlines = [a.upper() for a in flight.airlines]
                # Check if this flight matches our target airline
                if any(airline_code.upper() in a for a in flight_airlines):
                    price = flight.price
                    break

            # No fallback — leave as null if CI not found
            if price is not None:
                weekly_data.append({**item, "price": int(price)})
                errors = 0  # Reset consecutive error counter
                status = "✅"
            else:
                weekly_data.append({**item, "price": None})
                status = "⚠️"

            print(f"  [{i+1}/{len(week_dates)}] {dep_date} → {ret_date}: {status} {price if price else 'N/A'} TWD")

        except Exception as e:
            print(f"  [{i+1}/{len(week_dates)}] {dep_date} → {ret_date}: ❌ Error: {e}")
            weekly_data.append({**item, "price": None})
            errors += 1

            if errors >= max_errors:
                print(f"  ⚠️ 連續 {max_errors} 次錯誤，中斷此航線查詢")
                # Fill remaining weeks with None
                for remaining in week_dates[i+1:]:
                    weekly_data.append({**remaining, "price": None})
                break

        # Rate limiting: 1.5 seconds between requests
        if i < len(week_dates) - 1:
            time.sleep(1.5)

    return weekly_data


def fetch_flights_amadeus(route, week_dates):
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

    weekly_data = []
    for item in week_dates:
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
            if res.data:
                price = float(res.data[0]['price']['total'])
                weekly_data.append({**item, "price": int(price)})
            else:
                weekly_data.append({**item, "price": None})
            time.sleep(0.3)
        except Exception as err:
            print(f"  API Error for {item['departureDate']}: {err}")
            weekly_data.append({**item, "price": None})

    return weekly_data


def main():
    base_data_dir = PUBLIC_DIR / "data"
    os.makedirs(base_data_dir, exist_ok=True)

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        routes_config = json.load(f)

    week_dates = generate_weekly_dates(weeks_ahead=40, trip_days=8)
    now_str = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S (UTC+8)")

    # Determine data source priority: fast-flights > Amadeus > baseline
    use_fast_flights = "--no-fast-flights" not in sys.argv
    use_amadeus = "--amadeus" in sys.argv

    print(f"📊 資料來源: {'fast-flights (Google Flights)' if use_fast_flights else 'Amadeus' if use_amadeus else 'Baseline'}")
    print(f"📅 查詢 {len(week_dates)} 週, {len(routes_config)} 條航線\n")

    # Group by airline
    airlines_map = {}

    for route in routes_config:
        airline_code = route["airline"]
        airline_name = route.get("airlineName", airline_code)
        route_id = route["id"]

        if airline_code not in airlines_map:
            airlines_map[airline_code] = {
                "code": airline_code,
                "name": airline_name,
                "routes": []
            }

        print(f"處理 [{airline_code}] 航線: {route['name']} ({route_id})...")

        weekly_data = None

        # Try fast-flights first
        if use_fast_flights and not use_amadeus:
            print(f"  📡 使用 fast-flights 查詢 Google Flights...")
            weekly_data = fetch_flights_fast_flights(route, week_dates)

        # Fallback to Amadeus
        if weekly_data is None and use_amadeus:
            weekly_data = fetch_flights_amadeus(route, week_dates)

        # Final fallback: baseline prices
        if weekly_data is None:
            print(f"  📋 使用基準行情資料 (fallback)")
            weekly_data = get_baseline_prices_for_route(route_id, week_dates)

        valid_prices = [x["price"] for x in weekly_data if x["price"] is not None]
        min_price = min(valid_prices) if valid_prices else 0
        avg_price = int(sum(valid_prices) / len(valid_prices)) if valid_prices else 0
        sorted_by_price = sorted([x for x in weekly_data if x["price"] is not None], key=lambda x: x["price"])
        top_deals = sorted_by_price[:5]

        # Output path: public/data/airlines/{airline_code}/{route_id}/
        route_dir = os.path.join(base_data_dir, "airlines", airline_code, route_id)
        os.makedirs(route_dir, exist_ok=True)
        route_index_file = os.path.join(route_dir, "index.json")

        route_payload = {
            "id": route["id"],
            "name": route["name"],
            "origin": route["origin"],
            "destination": route["destination"],
            "airline": airline_code,
            "airlineName": airline_name,
            "color": route["color"],
            "stayDays": route.get("stayDays", 8),
            "updatedAt": now_str,
            "weeksCount": len(weekly_data),
            "dataSource": "fast-flights" if (use_fast_flights and weekly_data and weekly_data[0].get("price") is not None and "--no-fast-flights" not in sys.argv) else "amadeus" if use_amadeus else "baseline",
            "stats": {
                "minPrice": min_price,
                "avgPrice": avg_price
            },
            "topDeals": top_deals,
            "weeklyData": weekly_data
        }

        with open(route_index_file, "w", encoding="utf-8") as rf:
            json.dump(route_payload, rf, ensure_ascii=False, indent=2)

        # Register in airline list
        relative_route_path = f"data/airlines/{airline_code}/{route_id}/index.json"
        airlines_map[airline_code]["routes"].append({
            "id": route["id"],
            "name": route["name"],
            "origin": route["origin"],
            "destination": route["destination"],
            "color": route["color"],
            "minPrice": min_price,
            "path": relative_route_path
        })

        print(f"  ✅ 完成 ({len(valid_prices)}/{len(weekly_data)} 週有價格)\n")

    # Output airline indices
    root_airlines_index = []
    root_all_routes = []

    for airline_code, airline_info in airlines_map.items():
        airline_dir = os.path.join(base_data_dir, "airlines", airline_code)
        airline_index_file = os.path.join(airline_dir, "index.json")
        relative_airline_path = f"data/airlines/{airline_code}/index.json"

        airline_payload = {
            "code": airline_code,
            "name": airline_info["name"],
            "updatedAt": now_str,
            "routesCount": len(airline_info["routes"]),
            "routes": airline_info["routes"]
        }

        with open(airline_index_file, "w", encoding="utf-8") as af:
            json.dump(airline_payload, af, ensure_ascii=False, indent=2)

        root_airlines_index.append({
            "code": airline_code,
            "name": airline_info["name"],
            "routesCount": len(airline_info["routes"]),
            "path": relative_airline_path
        })

        root_all_routes.extend(airline_info["routes"])

    # Output root index
    root_payload = {
        "title": "Flight Radar 航班票價索引",
        "version": "3.0.0",
        "updatedAt": now_str,
        "weeksCount": 40,
        "config": {
            "defaultAirline": "CI",
            "defaultRoute": "TPE-NRT",
            "tripDays": 8,
            "currency": "TWD"
        },
        "airlines": root_airlines_index,
        "routes": root_all_routes
    }

    root_index_path = os.path.join(base_data_dir, "index.json")
    with open(root_index_path, "w", encoding="utf-8") as mf:
        json.dump(root_payload, mf, ensure_ascii=False, indent=2)

    print("🎉 成功建立分層索引與航線資料檔！")
    print(f"  - 頂層索引: {root_index_path}")


if __name__ == "__main__":
    main()
