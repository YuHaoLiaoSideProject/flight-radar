import datetime
import glob
import json
import os

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

def get_all_snapshots(route_dir):
    """讀取該航線所有依日期命名的快照檔案，並按日期排序"""
    json_files = glob.glob(os.path.join(route_dir, "*.json"))
    date_files = []
    for f in json_files:
        basename = os.path.basename(f)
        if basename.endswith(".json") and len(basename) == 15: # YYYY-MM-DD.json
            date_files.append(f)
    date_files.sort()
    
    snapshots = []
    for f in date_files:
        try:
            with open(f, "r", encoding="utf-8") as rf:
                snapshots.append((os.path.basename(f).replace(".json", ""), json.load(rf)))
        except Exception:
            pass
    return snapshots

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    routes_config_path = os.path.join(script_dir, "../data/routes.json")
    raw_data_dir = os.path.join(script_dir, "../data/raw")
    api_dir = os.path.join(script_dir, "../public/api")

    os.makedirs(api_dir, exist_ok=True)

    with open(routes_config_path, "r", encoding="utf-8") as f:
        routes_config = json.load(f)

    now_str = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S (UTC+8)")

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

        route_raw_dir = os.path.join(raw_data_dir, airline_code, route_id)
        if not os.path.exists(route_raw_dir):
            print(f"⚠️ 找不到原始資料目錄: {route_raw_dir}，跳過")
            continue

        snapshots = get_all_snapshots(route_raw_dir)
        if not snapshots:
            print(f"⚠️ 航線 {route_id} 查無任何日期快照檔案")
            continue

        latest_date_str, latest_snapshot = snapshots[-1]
        prev_snapshot = snapshots[-2][1] if len(snapshots) >= 2 else None

        # 建立前一次快照的價格表
        prev_price_map = {}
        if prev_snapshot:
            for f in prev_snapshot.get("flights", []):
                prev_price_map[f"{f['departureDate']}_{f['returnDate']}"] = f.get("price")

        # 彙整歷史價格走勢字典 (dep_ret -> list of {queryDate, price})
        history_map = {}
        for snap_date, snap_obj in snapshots:
            for f in snap_obj.get("flights", []):
                k = f"{f['departureDate']}_{f['returnDate']}"
                if k not in history_map:
                    history_map[k] = []
                p = f.get("price")
                if p is not None:
                    # 去重：若與上一個記錄相同則不重複加
                    if not history_map[k] or history_map[k][-1]["price"] != p:
                        history_map[k].append({
                            "queryDate": snap_date,
                            "price": p
                        })

        weekly_data = []
        for flight in latest_snapshot.get("flights", []):
            dep = flight["departureDate"]
            ret = flight["returnDate"]
            k = f"{dep}_{ret}"
            tag = get_holiday_tag(dep)
            dep_dt = datetime.datetime.strptime(dep, "%Y-%m-%d")
            ret_dt = datetime.datetime.strptime(ret, "%Y-%m-%d")
            
            cur_price = flight.get("price")
            prev_price = prev_price_map.get(k, cur_price)
            price_diff = (cur_price - prev_price) if (cur_price and prev_price) else 0

            flight_history = history_map.get(k, [])

            weekly_data.append({
                "weekIndex": flight["weekIndex"],
                "departureDate": dep,
                "returnDate": ret,
                "label": f"{dep_dt.strftime('%m/%d')}~{ret_dt.strftime('%m/%d')}",
                "tag": tag,
                "isHoliday": tag is not None,
                "price": cur_price,
                "previousPrice": prev_price,
                "priceDiff": price_diff,
                "history": flight_history
            })

        valid_prices = [x["price"] for x in weekly_data if x["price"] is not None]
        min_price = min(valid_prices) if valid_prices else 0
        avg_price = int(sum(valid_prices) / len(valid_prices)) if valid_prices else 0
        sorted_by_price = sorted([x for x in weekly_data if x["price"] is not None], key=lambda x: x["price"])
        top_deals = sorted_by_price[:5]

        # 產出航線 API: public/api/airlines/{airline_code}/{route_id}/
        route_api_dir = os.path.join(api_dir, "airlines", airline_code, route_id)
        weeks_dir = os.path.join(route_api_dir, "weeks")
        os.makedirs(weeks_dir, exist_ok=True)

        # 寫 meta.json (輕量)
        meta_payload = {
            "id": route["id"],
            "name": route["name"],
            "origin": route["origin"],
            "destination": route["destination"],
            "airline": airline_code,
            "airlineName": airline_name,
            "color": route["color"],
            "stayDays": route.get("stayDays", 8),
            "generatedAt": now_str,
            "latestQueryDate": latest_date_str,
            "totalSnapshotsRecorded": len(snapshots),
            "weeksCount": len(weekly_data),
            "stats": {
                "minPrice": min_price,
                "avgPrice": avg_price
            },
            "topDeals": [{
                "weekIndex": d["weekIndex"],
                "departureDate": d["departureDate"],
                "returnDate": d["returnDate"],
                "label": d["label"],
                "tag": d["tag"],
                "price": d["price"]
            } for d in top_deals]
        }

        with open(os.path.join(route_api_dir, "meta.json"), "w", encoding="utf-8") as af:
            json.dump(meta_payload, af, ensure_ascii=False, indent=2)

        # 寫每週資料 (依 departure date 命名)
        for week in weekly_data:
            week_file = os.path.join(weeks_dir, f"{week['departureDate']}.json")
            with open(week_file, "w", encoding="utf-8") as wf:
                json.dump(week, wf, ensure_ascii=False, indent=2)

        relative_route_path = f"api/airlines/{airline_code}/{route_id}/meta.json"
        airlines_map[airline_code]["routes"].append({
            "id": route["id"],
            "name": route["name"],
            "origin": route["origin"],
            "destination": route["destination"],
            "color": route["color"],
            "minPrice": min_price,
            "path": relative_route_path
        })

    # 產出各航司 API
    root_airlines_index = []
    root_all_routes = []

    for airline_code, airline_info in airlines_map.items():
        airline_api_dir = os.path.join(api_dir, "airlines", airline_code)
        os.makedirs(airline_api_dir, exist_ok=True)
        airline_api_file = os.path.join(airline_api_dir, "index.json")
        relative_airline_path = f"api/airlines/{airline_code}/index.json"

        airline_payload = {
            "code": airline_code,
            "name": airline_info["name"],
            "generatedAt": now_str,
            "routesCount": len(airline_info["routes"]),
            "routes": airline_info["routes"]
        }

        with open(airline_api_file, "w", encoding="utf-8") as aif:
            json.dump(airline_payload, aif, ensure_ascii=False, indent=2)

        root_airlines_index.append({
            "code": airline_code,
            "name": airline_info["name"],
            "routesCount": len(airline_info["routes"]),
            "path": relative_airline_path
        })

        root_all_routes.extend(airline_info["routes"])

    # 產出全站頂層 API: public/api/index.json
    root_payload = {
        "title": "Flight Radar 航班 API 索引",
        "version": "4.0.0",
        "generatedAt": now_str,
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

    root_api_path = os.path.join(api_dir, "index.json")
    with open(root_api_path, "w", encoding="utf-8") as rf:
        json.dump(root_payload, rf, ensure_ascii=False, indent=2)

    print("🚀 API 建構完成！已由日期快照目錄生成至 public/api/")

if __name__ == "__main__":
    main()
