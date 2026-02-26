"""宿曜道 API 路由"""
import os
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlmodel import Session

from database import get_session
from services.sukuyodo import sukuyodo_service
from services.company_search import company_search_service
from services.stats import stats_service
from services.japanese_calendar import japanese_calendar_service
from models.stats import Features

APP_PIN = os.environ.get("APP_PIN", "")


def verify_pin(request: Request):
    """驗證 PIN。APP_PIN 未設定時放行（本地開發）"""
    if not APP_PIN:
        return
    pin = request.headers.get("X-App-Pin", "")
    if pin != APP_PIN:
        raise HTTPException(status_code=401, detail="存取碼錯誤")


router = APIRouter(tags=["宿曜道"], dependencies=[Depends(verify_pin)])


class CompatibilityRequest(BaseModel):
    """相性診斷請求"""
    date1: str  # YYYY-MM-DD
    date2: str  # YYYY-MM-DD


class CompanySearchRequest(BaseModel):
    """公司自動搜尋請求"""
    keywords: str           # 搜尋關鍵字，如 "MES 智慧製造"
    area: str = "6001014000"  # 104 地區碼，預設台南善化
    birth_date: str         # 使用者生日 YYYY-MM-DD
    min_score: int = 0      # 最低分數門檻（0 表示不篩選）


class CompanyBatchItem(BaseModel):
    """批次分析用的公司資料"""
    id: str
    name: str
    founding_date: str      # YYYY-MM-DD
    memo: str = ""
    job_url: str = ""


class CompanyBatchRequest(BaseModel):
    """公司批次分析請求"""
    birth_date: str         # 使用者生日 YYYY-MM-DD
    year: int               # 分析年份
    companies: list[CompanyBatchItem]


class GcisSearchRequest(BaseModel):
    """GCIS 經濟部商工登記搜尋請求"""
    keyword: str


class CompanyUrlLookupRequest(BaseModel):
    """104 公司頁面連結查詢請求"""
    company_name: str


class LuckyDatesRequest(BaseModel):
    """吉凶日期查詢請求"""
    birth_date: str         # YYYY-MM-DD
    start_date: str = ""    # 預設 today
    days: int = 30          # 查詢天數


@router.post("/fortune/lucky-dates")
def get_lucky_dates(request: LuckyDatesRequest):
    """
    取得個人吉凶日期清單

    根據每日運勢的 career 分數篩選吉日和凶日，
    用於求職投遞/面試/談判的日期選擇。

    Args:
        request: 出生日期、起始日期、天數
    """
    try:
        birth = date.fromisoformat(request.birth_date)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="日期格式錯誤，請使用 YYYY-MM-DD"
        )

    today = date.today()
    if birth > today:
        raise HTTPException(
            status_code=400,
            detail="生日不可為未來日期"
        )

    start = None
    if request.start_date:
        try:
            start = date.fromisoformat(request.start_date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="start_date 格式錯誤，請使用 YYYY-MM-DD"
            )

    if request.days < 1 or request.days > 90:
        raise HTTPException(
            status_code=400,
            detail="days 須介於 1-90"
        )

    result = company_search_service.calculate_lucky_dates(
        birth_date=birth,
        start_date=start,
        days=request.days,
    )

    return {
        "success": True,
        "data": result,
    }


@router.get("/mansions")
async def get_all_mansions():
    """
    取得 27 宿列表

    返回所有本命宿的基本資料，包含名稱、讀音、元素等。
    用於輪盤視覺化和宿位查詢。
    """
    mansions = sukuyodo_service.get_all_mansions()

    return {
        "success": True,
        "count": len(mansions),
        "mansions": [
            {
                "index": m["index"],
                "name_jp": m["name_jp"],
                "name_zh": m.get("name_zh", m["name_jp"]),
                "reading": m["reading"],
                "element": m["element"],
                "keywords": m["keywords"],
                "personality": m.get("personality", ""),
                "personality_classic": m.get("personality_classic", ""),
                "personality_ja": m.get("personality_ja", ""),
                "classic_source": m.get("classic_source", ""),
                "nature_type": m.get("nature_type", ""),
                "day_fortune": m.get("day_fortune", {})
            }
            for m in mansions
        ]
    }


@router.get("/mansion/{date_str}")
def get_mansion_by_date(
    date_str: str,
    session: Session = Depends(get_session)
):
    """
    根據西曆生日查詢本命宿

    Args:
        date_str: 西曆生日，格式 YYYY-MM-DD

    Returns:
        本命宿完整資料，包含性格分析、感情運、事業運等
    """
    try:
        birth_date = date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="日期格式錯誤，請使用 YYYY-MM-DD"
        )

    # 驗證日期範圍
    today = date.today()
    if birth_date > today:
        raise HTTPException(
            status_code=400,
            detail="生日不可為未來日期"
        )

    if birth_date.year < 1900:
        raise HTTPException(
            status_code=400,
            detail="僅支援 1900 年後的日期"
        )

    mansion = sukuyodo_service.get_mansion(birth_date)

    # 記錄使用統計
    stats_service.log_usage(session, Features.SUKUYODO_LOOKUP)

    return {
        "success": True,
        "data": mansion
    }


@router.post("/compatibility")
def calculate_compatibility(
    request: CompatibilityRequest,
    session: Session = Depends(get_session)
):
    """
    計算雙人相性

    根據兩人的西曆生日計算宿曜道相性，
    返回關係類型、相性分數及建議。
    """
    try:
        date1 = date.fromisoformat(request.date1)
        date2 = date.fromisoformat(request.date2)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="日期格式錯誤，請使用 YYYY-MM-DD"
        )

    # 驗證日期
    today = date.today()
    for d in [date1, date2]:
        if d > today:
            raise HTTPException(
                status_code=400,
                detail="生日不可為未來日期"
            )
        if d.year < 1900:
            raise HTTPException(
                status_code=400,
                detail="僅支援 1900 年後的日期"
            )

    result = sukuyodo_service.calculate_compatibility(date1, date2)

    # 記錄使用統計
    stats_service.log_usage(session, Features.SUKUYODO_COMPATIBILITY)

    return {
        "success": True,
        "data": result
    }


@router.get("/relations")
async def get_relation_types():
    """
    取得六種關係類型說明

    返回命、業胎、栄親、友衰、安壊、危成六種關係的詳細說明。
    """
    relations = sukuyodo_service.relations_data

    return {
        "count": len(relations),
        "relations": [
            {
                "type": key,
                "name": rel["name"],
                "name_jp": rel.get("name_jp", rel["name"]),
                "reading": rel.get("reading", ""),
                "score": rel["score"],
                "description": rel["description"],
                "description_classic": rel.get("description_classic", ""),
                "description_ja": rel.get("description_ja", ""),
                "detailed": rel.get("detailed", ""),
                "advice": rel["advice"],
                "tips": rel.get("tips", []),
                "avoid": rel.get("avoid", []),
                "good_for": rel.get("good_for", [])
            }
            for key, rel in relations.items()
        ]
    }


@router.get("/elements")
async def get_elements():
    """
    取得七曜元素說明

    返回日、月、火、水、木、金、土七種元素的詳細資料。
    """
    elements = sukuyodo_service.elements_data

    return {
        "count": len(elements),
        "elements": [
            {
                "name": name,
                "reading": data.get("reading", ""),
                "planet": data.get("planet", ""),
                "traits": data.get("traits", ""),
                "energy": data.get("energy", ""),
                "description": data.get("description", ""),
                "detailed_traits": data.get("detailed_traits", ""),
                "interactions": data.get("interactions", ""),
                "life_advice": data.get("life_advice", "")
            }
            for name, data in elements.items()
        ]
    }


@router.get("/metadata")
async def get_metadata():
    """
    取得宿曜道基本資訊

    返回宿曜道的名稱、起源、創始者等元資料，含歷史沿革和讀音標註。
    """
    metadata = sukuyodo_service.metadata
    month_mansion_table = sukuyodo_service.month_mansion_table
    return {
        **metadata,
        "month_mansion_table": month_mansion_table
    }


@router.get("/compatibility-finder/{date_str}")
def find_compatible_mansions(
    date_str: str,
    session: Session = Depends(get_session)
):
    """
    尋找最佳配對與需避免的本命宿

    根據西曆生日計算本命宿，並列出：
    - 栄親（えいしん）：最適合結婚，95 分
    - 業胎（ぎょうたい）：前世之緣，90 分
    - 安壊（あんかい）：需要避免，55 分

    Args:
        date_str: 西曆生日，格式 YYYY-MM-DD
    """
    try:
        birth_date = date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="日期格式錯誤，請使用 YYYY-MM-DD"
        )

    # 驗證日期範圍
    today = date.today()
    if birth_date > today:
        raise HTTPException(
            status_code=400,
            detail="生日不可為未來日期"
        )

    if birth_date.year < 1900:
        raise HTTPException(
            status_code=400,
            detail="僅支援 1900 年後的日期"
        )

    result = sukuyodo_service.find_compatible_mansions(birth_date)

    # 記錄使用統計
    stats_service.log_usage(session, Features.SUKUYODO_LOOKUP)

    return {
        "success": True,
        "data": result
    }


@router.get("/fortune/daily/{target_date}")
def get_daily_fortune(
    target_date: str,
    birth_date: str,
    session: Session = Depends(get_session)
):
    """
    取得每日運勢

    Args:
        target_date: 要查詢的日期，格式 YYYY-MM-DD
        birth_date: 出生日期，格式 YYYY-MM-DD（Query parameter）
    """
    try:
        target = date.fromisoformat(target_date)
        birth = date.fromisoformat(birth_date)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="日期格式錯誤，請使用 YYYY-MM-DD"
        )

    result = sukuyodo_service.calculate_daily_fortune(birth, target)

    stats_service.log_usage(session, Features.SUKUYODO_LOOKUP)

    return {
        "success": True,
        "data": result
    }


@router.get("/fortune/monthly/{year}/{month}")
def get_monthly_fortune(
    year: int,
    month: int,
    birth_date: str,
    session: Session = Depends(get_session)
):
    """
    取得每月運勢

    Args:
        year: 年份
        month: 月份 (1-12)
        birth_date: 出生日期，格式 YYYY-MM-DD（Query parameter）
    """
    if month < 1 or month > 12:
        raise HTTPException(
            status_code=400,
            detail="月份必須在 1-12 之間"
        )

    try:
        birth = date.fromisoformat(birth_date)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="日期格式錯誤，請使用 YYYY-MM-DD"
        )

    result = sukuyodo_service.calculate_monthly_fortune(birth, year, month)

    stats_service.log_usage(session, Features.SUKUYODO_LOOKUP)

    return {
        "success": True,
        "data": result
    }


@router.get("/fortune/weekly/{target_date}")
def get_weekly_fortune(
    target_date: str,
    birth_date: str,
    session: Session = Depends(get_session)
):
    """
    取得週運勢（滾動視窗）

    以指定日期為中心，返回昨天 + 今天 + 未來6天 = 共8天的運勢。
    更直觀的「本週」概念，不使用 ISO 週數。

    Args:
        target_date: 中心日期，格式 YYYY-MM-DD（通常是今天）
        birth_date: 出生日期，格式 YYYY-MM-DD（Query parameter）
    """
    try:
        target = date.fromisoformat(target_date)
        birth = date.fromisoformat(birth_date)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="日期格式錯誤，請使用 YYYY-MM-DD"
        )

    result = sukuyodo_service.calculate_weekly_fortune(birth, target)

    stats_service.log_usage(session, Features.SUKUYODO_LOOKUP)

    return {
        "success": True,
        "data": result
    }


@router.get("/fortune/yearly/{year}")
def get_yearly_fortune(
    year: int,
    birth_date: str,
    session: Session = Depends(get_session)
):
    """
    取得每年運勢

    Args:
        year: 年份
        birth_date: 出生日期，格式 YYYY-MM-DD（Query parameter）
    """
    if year < 1900 or year > 2100:
        raise HTTPException(
            status_code=400,
            detail="年份必須在 1900-2100 之間"
        )

    try:
        birth = date.fromisoformat(birth_date)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="日期格式錯誤，請使用 YYYY-MM-DD"
        )

    result = sukuyodo_service.calculate_yearly_fortune(birth, year)

    stats_service.log_usage(session, Features.SUKUYODO_LOOKUP)

    return {
        "success": True,
        "data": result
    }


@router.get("/fortune/yearly-range")
def get_yearly_fortune_range(
    birth_date: str,
    start_year: int,
    end_year: int = 0,
    session: Session = Depends(get_session)
):
    """
    取得多年運勢（九曜流年法批次查詢）

    Args:
        birth_date: 出生日期，格式 YYYY-MM-DD（Query parameter）
        start_year: 起始年份
        end_year: 結束年份（預設 start_year + 9）
    """
    if end_year == 0:
        end_year = start_year + 9

    if start_year < 1900 or end_year > 2100:
        raise HTTPException(
            status_code=400,
            detail="年份必須在 1900-2100 之間"
        )

    if end_year - start_year > 9:
        raise HTTPException(
            status_code=400,
            detail="最多查詢 10 年（end_year - start_year <= 9）"
        )

    if end_year < start_year:
        raise HTTPException(
            status_code=400,
            detail="end_year 不可小於 start_year"
        )

    try:
        birth = date.fromisoformat(birth_date)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="日期格式錯誤，請使用 YYYY-MM-DD"
        )

    results = sukuyodo_service.calculate_yearly_fortune_range(birth, start_year, end_year)

    stats_service.log_usage(session, Features.SUKUYODO_LOOKUP)

    return {
        "success": True,
        "data": results
    }


@router.get("/lucky-days/categories")
def get_lucky_day_categories():
    """取得吉日分類 metadata（名稱、icon、動作清單）"""
    cats = sukuyodo_service.LUCKY_DAY_CATEGORIES
    data = []
    for key, cat in cats.items():
        actions = [
            {"key": act_key, "name": act_val["name"]}
            for act_key, act_val in cat["actions"].items()
        ]
        data.append({
            "key": key,
            "name": cat["name"],
            "icon": cat["icon"],
            "actions": actions
        })
    return {"success": True, "data": data}


@router.get("/lucky-days/summary/{date_str}")
def get_lucky_days_summary(
    date_str: str,
    categories: str = "",
    session: Session = Depends(get_session)
):
    """
    取得吉日彙整（依分類分組）

    Query params:
    - categories: 逗號分隔的分類 key，空值=全部
    """
    try:
        birth_date = date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="日期格式錯誤，請使用 YYYY-MM-DD"
        )

    today = date.today()
    if birth_date > today:
        raise HTTPException(
            status_code=400,
            detail="生日不可為未來日期"
        )

    if birth_date.year < 1900:
        raise HTTPException(
            status_code=400,
            detail="僅支援 1900 年後的日期"
        )

    all_cats = sukuyodo_service.LUCKY_DAY_CATEGORIES
    requested = [c.strip() for c in categories.split(",") if c.strip()] if categories else list(all_cats.keys())

    result_categories = []
    for cat_key in requested:
        cat_def = all_cats.get(cat_key)
        if not cat_def:
            continue
        cat_actions = []
        for act_key, act_val in cat_def["actions"].items():
            try:
                result = sukuyodo_service.get_lucky_days(
                    birth_date, cat_key, act_key, days_ahead=30
                )
                cat_actions.append({
                    "key": act_key,
                    "name": act_val["name"],
                    "lucky_days": result["lucky_days"][:5],
                })
            except Exception:
                cat_actions.append({
                    "key": act_key,
                    "name": act_val["name"],
                    "lucky_days": [],
                })
        result_categories.append({
            "key": cat_key,
            "name": cat_def["name"],
            "icon": cat_def["icon"],
            "actions": cat_actions,
        })

    stats_service.log_usage(session, Features.SUKUYODO_LOOKUP)

    return {
        "success": True,
        "data": {
            "your_mansion": sukuyodo_service.get_mansion(birth_date),
            "categories": result_categories
        }
    }


@router.get("/calendar/lucky-days/{year}/{month}")
def get_japanese_calendar_lucky_days(
    year: int,
    month: int,
    session: Session = Depends(get_session)
):
    """
    取得指定月份的日本選日曆注

    返回一粒萬倍日、天赦日、寅の日、巳の日等吉日列表，
    以及不成就日等凶日列表。

    Args:
        year: 年份
        month: 月份 (1-12)

    Returns:
        選日曆注資料
    """
    if month < 1 or month > 12:
        raise HTTPException(
            status_code=400,
            detail="月份必須在 1-12 之間"
        )

    if year < 1900 or year > 2100:
        raise HTTPException(
            status_code=400,
            detail="年份必須在 1900-2100 之間"
        )

    result = japanese_calendar_service.get_calendar_days(year, month)
    result["day_type_descriptions"] = japanese_calendar_service.get_day_type_descriptions()

    stats_service.log_usage(session, Features.SUKUYODO_LOOKUP)

    return {
        "success": True,
        "data": result
    }


@router.get("/special-days/{year}/{month}")
def get_special_days(
    year: int,
    month: int,
):
    """
    取得指定月份的宿曜特殊日（甘露日/金剛峯日/羅刹日）

    特殊日是全域的（非個人），由七曜與當日宿的組合決定。

    Args:
        year: 年份
        month: 月份 (1-12)
    """
    if month < 1 or month > 12:
        raise HTTPException(
            status_code=400,
            detail="月份必須在 1-12 之間"
        )

    if year < 1900 or year > 2100:
        raise HTTPException(
            status_code=400,
            detail="年份必須在 1900-2100 之間"
        )

    days = sukuyodo_service.get_special_days_for_month(year, month)

    return {
        "success": True,
        "data": {
            "year": year,
            "month": month,
            "days": days,
            "summary": {
                "kanro_count": sum(1 for d in days if d["type"] == "kanro"),
                "kongou_count": sum(1 for d in days if d["type"] == "kongou"),
                "rasetsu_count": sum(1 for d in days if d["type"] == "rasetsu"),
            }
        }
    }


@router.get("/calendar/monthly/{year}/{month}")
def get_calendar_month(
    year: int,
    month: int,
    birth_date: str = None,
):
    """
    取得整月統合月曆

    整合宿位、七曜、凌犯期間、甘露/金剛峯/羅刹日、日本選日。
    加入 birth_date 參數後疊加個人化資訊（三期、六害宿、運勢分數）。

    Args:
        year: 年份
        month: 月份 (1-12)
        birth_date: 出生日期（可選），格式 YYYY-MM-DD
    """
    if month < 1 or month > 12:
        raise HTTPException(
            status_code=400,
            detail="月份必須在 1-12 之間"
        )

    if year < 1900 or year > 2100:
        raise HTTPException(
            status_code=400,
            detail="年份必須在 1900-2100 之間"
        )

    birth = None
    if birth_date:
        try:
            birth = date.fromisoformat(birth_date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="日期格式錯誤，請使用 YYYY-MM-DD"
            )

    result = sukuyodo_service.get_calendar_month(year, month, birth)

    # 合併日本選日資料
    jp_calendar = japanese_calendar_service.get_calendar_days(year, month)
    jp_day_map = {}
    for jd in jp_calendar.get("days", []):
        jp_day_map[jd["date"]] = {
            "types": jd["types"],
            "labels": jd["labels"],
            "is_super_lucky": jd["is_super_lucky"],
        }
    for jd in jp_calendar.get("unlucky_days", []):
        entry = jp_day_map.get(jd["date"], {"types": [], "labels": [], "is_super_lucky": False})
        entry["types"].append(jd["type"])
        entry["labels"].append(jd["label"])
        jp_day_map[jd["date"]] = entry

    for day_entry in result["days"]:
        jp_info = jp_day_map.get(day_entry["date"])
        day_entry["japanese_calendar"] = jp_info

    # 合併日本選日統計
    result["statistics"]["tensya_count"] = jp_calendar["summary"].get("tensya_count", 0)
    result["statistics"]["ichiryumanbai_count"] = jp_calendar["summary"].get("ichiryumanbai_count", 0)

    return {
        "success": True,
        "data": result
    }


@router.get("/lucky-days/pair/{date1}/{date2}")
def get_pair_lucky_days(
    date1: str,
    date2: str,
    relation: str,
    session: Session = Depends(get_session)
):
    """
    查詢雙人吉日

    根據兩人的本命宿和關係類型，計算適合共同行動的吉日。

    Args:
        date1: 第一人（自己）的生日，格式 YYYY-MM-DD
        date2: 第二人（收藏對象）的生日，格式 YYYY-MM-DD
        relation: 關係類型（dating/spouse/parent/family/friend）
    """
    try:
        birth_date1 = date.fromisoformat(date1)
        birth_date2 = date.fromisoformat(date2)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="日期格式錯誤，請使用 YYYY-MM-DD"
        )

    # 驗證日期範圍
    today = date.today()
    for d in [birth_date1, birth_date2]:
        if d > today:
            raise HTTPException(
                status_code=400,
                detail="生日不可為未來日期"
            )
        if d.year < 1900:
            raise HTTPException(
                status_code=400,
                detail="僅支援 1900 年後的日期"
            )

    # 驗證關係類型
    valid_relations = ["dating", "spouse", "parent", "family", "friend"]
    if relation not in valid_relations:
        raise HTTPException(
            status_code=400,
            detail=f"無效的關係類型，可用值：{', '.join(valid_relations)}"
        )

    try:
        result = sukuyodo_service.get_pair_lucky_days(
            birth_date1,
            birth_date2,
            relation
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    # 記錄使用統計
    stats_service.log_usage(session, Features.SUKUYODO_COMPATIBILITY)

    return {
        "success": True,
        "data": result
    }


@router.post("/company-batch-analysis")
def company_batch_analysis(request: CompanyBatchRequest):
    """
    公司批次分析

    計算每間公司的相性、九曜流年、梯隊排名、RC 風險。
    一次呼叫取得所有已收藏公司的綜合決策資訊。

    Args:
        request: 使用者生日、年份、公司清單
    """
    try:
        birth = date.fromisoformat(request.birth_date)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="日期格式錯誤，請使用 YYYY-MM-DD"
        )

    today = date.today()
    if birth > today:
        raise HTTPException(
            status_code=400,
            detail="生日不可為未來日期"
        )

    if request.year < 1900 or request.year > 2100:
        raise HTTPException(
            status_code=400,
            detail="年份必須在 1900-2100 之間"
        )

    if len(request.companies) == 0:
        return {
            "success": True,
            "data": {"user": {}, "companies": [], "tier_summary": {}},
        }

    companies_data = [
        {
            "id": c.id,
            "name": c.name,
            "founding_date": c.founding_date,
            "memo": c.memo,
            "job_url": c.job_url,
        }
        for c in request.companies
    ]

    result = company_search_service.batch_analyze(
        birth_date=birth,
        year=request.year,
        companies=companies_data,
    )

    return {
        "success": True,
        "data": result,
    }


@router.post("/gcis/search")
async def gcis_search(req: GcisSearchRequest):
    """
    GCIS 經濟部商工登記公司搜尋

    根據關鍵字模糊搜尋公司名稱，回傳公司列表含設立日期。
    用於手動查詢時自動帶入設立日期。
    """
    if len(req.keyword.strip()) < 2:
        raise HTTPException(
            status_code=400,
            detail="關鍵字至少 2 個字"
        )
    results = await company_search_service.search_gcis(req.keyword.strip())
    return {
        "success": True,
        "data": results,
    }


@router.post("/104/company-url")
async def lookup_104_company_url(req: CompanyUrlLookupRequest):
    """
    查詢 104 公司頁面連結

    用公司名稱搜尋 104，回傳公司頁面 URL。
    找不到時回傳 null，不影響收藏流程。
    """
    if len(req.company_name.strip()) < 2:
        raise HTTPException(
            status_code=400,
            detail="公司名稱至少 2 個字"
        )
    url = await company_search_service.lookup_104_company_url(req.company_name.strip())
    return {
        "success": True,
        "data": {"job_url": url},
    }


@router.post("/company-search")
async def search_companies(request: CompanySearchRequest):
    """
    公司自動搜尋

    搜尋 104 職缺 → 查詢 twincn.com 設立日期 → 計算宿曜相性 → 排序回傳。
    整個流程需爬取外部網站，回應時間較長（約 30-60 秒）。

    Args:
        request: 搜尋條件（關鍵字、地區、使用者生日、最低分數）
    """
    try:
        birth = date.fromisoformat(request.birth_date)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="日期格式錯誤，請使用 YYYY-MM-DD"
        )

    today = date.today()
    if birth > today:
        raise HTTPException(
            status_code=400,
            detail="生日不可為未來日期"
        )

    if not request.keywords.strip():
        raise HTTPException(
            status_code=400,
            detail="搜尋關鍵字不可為空"
        )

    results = await company_search_service.search_and_calculate(
        keywords=request.keywords.strip(),
        area=request.area,
        birth_date=birth,
        min_score=request.min_score,
    )

    return {
        "success": True,
        "data": results,
        "count": len(results),
    }
