import datetime
import json
import os
import time

def get_holiday_tag(dep_date_str):
    dep = datetime.datetime.strptime(dep_date_str, "%Y-%m-%d").date()
    if dep >= datetime.date(2026, 9, 26) and dep <= datetime.date(2026, 10, 4):
        return "中秋連假前後"
    elif dep >= datetime.date(2026, 10, 9) and dep <= datetime.date(2026, 10, 11):
        return "國慶雙十連假"
    elif dep >= datetime.date(2026, 11, 7) and dep <= datetime.date(2026, 11, 28):
        return "賞楓銀杏旺季"
    elif dep >= datetime.date(2026, 12, 25) and dep <= datetime.date(2027, 1, 3):
        return "跨年元旦假期"
    elif dep >= datetime.date(2027, 2, 5) and dep <= datetime.date(2027, 2, 14):
        return "🧨 春節除夕過年"
    elif dep >= datetime.date(2027, 2, 26) and dep <= datetime.date(2027, 3, 1):
        return "228 連假"
    elif dep >= datetime.date(2027, 3, 20) and dep <= datetime.date(2027, 3, 28):
        return "🌸 櫻花季初開"
    elif dep >= datetime.date(2027, 4, 1) and dep <= datetime.date(2027, 4, 11):
        return "🌸 清明連假/櫻花滿開"
    elif dep >= datetime.date(2027, 4, 30) and dep <= datetime.date(2027, 5, 9):
        return "五一勞動節/日本黃金週"
    elif dep >= datetime.date(2027, 6, 4) and dep <= datetime.date(2027, 6, 13):
        return "端午節前後"
    return None

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
        dep_str = dep.strftime("%Y-%m-%d")
        ret_str = ret.strftime("%Y-%m-%d")
        tag = get_holiday_tag(dep_str)
        dates.append({
            "weekIndex": i + 1,
            "departureDate": dep_str,
            "returnDate": ret_str,
            "label": f"{dep.strftime('%m/%d')}~{ret.strftime('%m/%d')}",
            "tag": tag,
            "isHoliday": tag is not None
        })
    return dates

def get_baseline_prices(route_id, week_dates):
    base_map = {
        "TPE-NRT": 13652,
        "TPE-KIX": 14225,
        "TPE-FUK": 13719,
        "TSA-HND": 16440
    }
    base = base_map.get(route_id, 14000)
    weekly_records = []
    
    for item in week_dates:
        dep = item["departureDate"]
        tag = item["tag"]
        price = base
        
        if "春節" in (tag or ""):
            price = int(base * 2.5 + 3000)
        elif "清明" in (tag or "") or "櫻花滿開" in (tag or ""):
            price = int(base * 2.0 + 2000)
        elif "櫻花季初開" in (tag or ""):
            price = int(base * 1.4 + 1000)
        elif "賞楓" in (tag or ""):
            price = int(base * 1.3 + (2000 if route_id in ["TPE-KIX", "TPE-FUK"] else 1000))
        elif "跨年" in (tag or ""):
            price = int(base * 1.25 + 1000)
        elif "228" in (tag or ""):
            price = int(base * 1.15)
        elif "中秋" in (tag or "") or "國慶" in (tag or ""):
            price = int(base * 1.2)
        elif "2027-05" in dep and route_id == "TPE-FUK":
            price = base
        elif "2027-01" in dep or "2026-09" in dep:
            price = base
        else:
            price = int(base * 1.08)

        weekly_records.append({
            **item,
            "price": price
        })
    return weekly_records

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "routes_config.json")
    base_data_dir = os.path.join(script_dir, "../public/data")
    os.makedirs(base_data_dir, exist_ok=True)

    with open(config_path, "r", encoding="utf-8") as f:
        routes_config = json.load(f)

    week_dates = generate_weekly_dates(weeks_ahead=40, trip_days=8)
    now_str = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S (UTC+8)")

    # 檢查是否有 Amadeus API 憑證
    amadeus_id = os.getenv("AMADEUS_CLIENT_ID")
    amadeus_secret = os.getenv("AMADEUS_CLIENT_SECRET")
    amadeus_client = None
    if amadeus_id and amadeus_secret:
        try:
            from amadeus import Client
            amadeus_client = Client(client_id=amadeus_id, client_secret=amadeus_secret)
            print("✅ 成功初始化 Amadeus API")
        except Exception as e:
            print(f"⚠️ 初始化 Amadeus 失敗: {e}，將使用基準行情資料")

    # 按航空公司分組
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
        
        weekly_data = []
        if amadeus_client:
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
                    print(f"API Error for {item['departureDate']}: {err}")
                    weekly_data.append({**item, "price": None})
        else:
            weekly_data = get_baseline_prices(route_id, week_dates)

        valid_prices = [x["price"] for x in weekly_data if x["price"] is not None]
        min_price = min(valid_prices) if valid_prices else 0
        avg_price = int(sum(valid_prices) / len(valid_prices)) if valid_prices else 0
        sorted_by_price = sorted([x for x in weekly_data if x["price"] is not None], key=lambda x: x["price"])
        top_deals = sorted_by_price[:5]

        # 航線專屬目錄: public/data/airlines/{airline_code}/{route_id}/
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
            "stats": {
                "minPrice": min_price,
                "avgPrice": avg_price
            },
            "topDeals": top_deals,
            "weeklyData": weekly_data
        }

        with open(route_index_file, "w", encoding="utf-8") as rf:
            json.dump(route_payload, rf, ensure_ascii=False, indent=2)

        # 登記在該航空清單中
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

    # 產出各航空公司的 index.json: public/data/airlines/{airline_code}/index.json
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

    # 產出全站頂層 index.json: public/data/index.json
    root_payload = {
        "title": "Flight Radar 航班票價索引",
        "version": "2.0.0",
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
