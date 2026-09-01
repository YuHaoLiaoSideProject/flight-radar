"""
scripts/shared.py — 共用工具函式與常數
供 fetch_raw_data.py、fetch_flights.py、build_api.py 使用
"""

from __future__ import annotations

import glob
import json
import logging
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 路徑常數
# ---------------------------------------------------------------------------

CONFIG_PATH: Path = Path(__file__).parent / "routes_config.json"
DATA_DIR: Path = Path(__file__).parent.parent / "data"
PUBLIC_DIR: Path = Path(__file__).parent.parent / "public"

# ---------------------------------------------------------------------------
# 假期判斷
# ---------------------------------------------------------------------------


def get_holiday_tag(
    departure_date: str,
    return_date: str | None = None,
) -> str | None:
    """根據出發（及回程）日期判斷是否落在假期區間，回傳假期標籤或 None。

    使用相對於出發年份的動態日期，不再硬編碼跨年年份。
    只要比對區間與出發日期有交集即命中。
    """
    dep = date.fromisoformat(departure_date)
    year = dep.year

    # 如果有回程日期，用它判斷年份（跨年情境）
    ret_year = year
    if return_date is not None:
        ret_year = date.fromisoformat(return_date).year

    # 假期定義：(start, end, tag)
    # 覆蓋兩年，以防查詢跨越年份邊界
    holidays: list[tuple[str, str, str]] = []
    for y in (year, ret_year):
        holidays.extend([
            # 🧧 春節（農曆新年前後，以公曆近似）
            (f"{y}-01-26", f"{y}-02-09", "🧨 春節除夕過年"),
            # 中秋連假
            (f"{y}-09-26", f"{y}-10-04", "中秋連假前後"),
            # 國慶雙十連假
            (f"{y}-10-09", f"{y}-10-11", "國慶雙十連假"),
            # 賞楓銀杏旺季
            (f"{y}-11-07", f"{y}-11-28", "賞楓銀杏旺季"),
            # 跨年元旦假期
            (f"{y}-12-25", f"{y + 1}-01-03", "跨年元旦假期"),
            # 228 連假
            (f"{y}-02-26", f"{y}-03-01", "228 連假"),
            # 櫻花季初開
            (f"{y}-03-20", f"{y}-03-28", "🌸 櫻花季初開"),
            # 清明連假 / 櫻花滿開
            (f"{y}-04-01", f"{y}-04-11", "🌸 清明連假/櫻花滿開"),
            # 五一勞動節 / 日本黃金週
            (f"{y}-04-30", f"{y}-05-09", "五一勞動節/日本黃金週"),
            # 端午節前後
            (f"{y}-06-04", f"{y}-06-13", "端午節前後"),
        ])

    for start, end, tag in holidays:
        s = date.fromisoformat(start)
        e = date.fromisoformat(end)
        if dep <= e and (return_date is None or date.fromisoformat(return_date) >= s):
            return tag
    return None


# ---------------------------------------------------------------------------
# 日期生成
# ---------------------------------------------------------------------------


def generate_weekly_dates(
    start_date: date | str | None = None,
    weeks_ahead: int = 40,
    trip_days: int = 8,
) -> list[dict[str, Any]]:
    """從本週六起，生成连续 N 週的出發 / 回程日期列表。

    Args:
        start_date: 起始日期（預設為今天）。
        weeks_ahead: 要生成幾週的資料。
        trip_days: 每趟旅行天數（出發日 + trip_days = 回程日）。

    Returns:
        包含 weekIndex, departureDate, returnDate, label, tag, isHoliday 的字典列表。
    """
    if start_date is None:
        today = date.today()
    elif isinstance(start_date, str):
        today = date.fromisoformat(start_date)
    else:
        today = start_date

    days_until_saturday = (5 - today.weekday()) % 7
    if days_until_saturday == 0:
        days_until_saturday = 7
    first_saturday = today + timedelta(days=days_until_saturday)

    dates: list[dict[str, Any]] = []
    for i in range(weeks_ahead):
        dep = first_saturday + timedelta(weeks=i)
        ret = dep + timedelta(days=trip_days)
        dep_str = dep.strftime("%Y-%m-%d")
        ret_str = ret.strftime("%Y-%m-%d")
        tag = get_holiday_tag(dep_str, ret_str)
        dates.append({
            "weekIndex": i + 1,
            "departureDate": dep_str,
            "returnDate": ret_str,
            "label": f"{dep.strftime('%m/%d')}~{ret.strftime('%m/%d')}",
            "tag": tag,
            "isHoliday": tag is not None,
        })
    return dates


# ---------------------------------------------------------------------------
# 基準價格
# ---------------------------------------------------------------------------

_BASE_PRICES: dict[str, int] = {
    "TPE-NRT": 13652,
    "TPE-KIX": 14225,
    "TPE-FUK": 13719,
    "TSA-HND": 16440,
}


def get_baseline_prices(
    holiday_tag: str | None,
    base_price: int,
) -> int:
    """根據假期標籤回傳基準價格的倍率結果。

    Args:
        holiday_tag: 由 get_holiday_tag 回傳的標籤（可為 None）。
        base_price: 航線基準票價。

    Returns:
        套用倍率後的票價。
    """
    if holiday_tag is None:
        return int(base_price * 1.08)
    if "春節" in holiday_tag:
        return int(base_price * 2.5 + 3000)
    if "清明" in holiday_tag or "櫻花滿開" in holiday_tag:
        return int(base_price * 2.0 + 2000)
    if "櫻花季初開" in holiday_tag:
        return int(base_price * 1.4 + 1000)
    if "賞楓" in holiday_tag:
        return int(base_price * 1.3 + 1000)
    if "跨年" in holiday_tag:
        return int(base_price * 1.25 + 1000)
    if "228" in holiday_tag:
        return int(base_price * 1.15)
    if "中秋" in holiday_tag or "國慶" in holiday_tag:
        return int(base_price * 1.2)
    return int(base_price * 1.08)


def get_baseline_prices_for_route(
    route_id: str,
    week_dates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """為整條航線的所有週次生成基準價格列表。

    Args:
        route_id: 航線代碼，如 "TPE-NRT"。
        week_dates: generate_weekly_dates 的回傳結果。

    Returns:
        每週附帶 price 欄位的字典列表。
    """
    base = _BASE_PRICES.get(route_id, 14000)
    results: list[dict[str, Any]] = []
    for item in week_dates:
        price = get_baseline_prices(item.get("tag"), base)
        results.append({**item, "price": price})
    return results


# ---------------------------------------------------------------------------
# 快照檔案工具
# ---------------------------------------------------------------------------

_DATE_FILENAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.json$")


def get_latest_snapshot(route_dir: str | Path) -> tuple[str | None, dict | None]:
    """取得指定航線目錄下最新的日期快照。

    只匹配 YYYY-MM-DD.json 格式的檔名。

    Args:
        route_dir: 快照目錄路徑。

    Returns:
        (最新快照檔案路徑, 解析後的 JSON dict)，無快照時回傳 (None, None)。
    """
    route_dir = Path(route_dir)
    json_files = sorted(
        f for f in route_dir.glob("*.json")
        if _DATE_FILENAME_RE.match(f.name)
    )
    if not json_files:
        return None, None

    latest_file = json_files[-1]
    with open(latest_file, "r", encoding="utf-8") as f:
        return str(latest_file), json.load(f)


def get_all_snapshots(route_dir: str | Path) -> list[tuple[str, dict]]:
    """讀取航線目錄下所有日期快照，依日期排序。

    只匹配 YYYY-MM-DD.json 格式的檔名。

    Args:
        route_dir: 快照目錄路徑。

    Returns:
        [(日期字串, JSON dict), ...] 列表，最舊在前。
    """
    route_dir = Path(route_dir)
    json_files = sorted(
        f for f in route_dir.glob("*.json")
        if _DATE_FILENAME_RE.match(f.name)
    )

    snapshots: list[tuple[str, dict]] = []
    for f in json_files:
        try:
            with open(f, "r", encoding="utf-8") as rf:
                date_str = f.name.replace(".json", "")
                snapshots.append((date_str, json.load(rf)))
        except Exception as exc:
            logger.warning("無法讀取快照 %s: %s", f, exc)
    return snapshots
