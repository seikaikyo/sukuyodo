"""宿曜道 API 路由"""
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from database import get_session
from services.sukuyodo import sukuyodo_service
from services.stats import stats_service
from services.japanese_calendar import japanese_calendar_service
from models.stats import Features

router = APIRouter(tags=["宿曜道"])


class CompatibilityRequest(BaseModel):
    """相性診斷請求"""
    date1: str  # YYYY-MM-DD
    date2: str  # YYYY-MM-DD


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
                "personality": m.get("personality", "")
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

    返回命、業胎、榮親、友衰、安壞、危成六種關係的詳細說明。
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
                "energy": data.get("energy", "")
            }
            for name, data in elements.items()
        ]
    }


@router.get("/metadata")
async def get_metadata():
    """
    取得宿曜道基本資訊

    返回宿曜道的名稱、起源、創始者等元資料，含讀音標註。
    """
    return sukuyodo_service.metadata


@router.get("/compatibility-finder/{date_str}")
def find_compatible_mansions(
    date_str: str,
    session: Session = Depends(get_session)
):
    """
    尋找最佳配對與需避免的本命宿

    根據西曆生日計算本命宿，並列出：
    - 榮親（えいしん）：最適合結婚，95 分
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


@router.get("/formula")
async def get_formula_explanation():
    """
    取得計算公式說明

    返回月宿傍通曆和三九秘法的詳細計算說明。
    """
    return {
        "mansion_calculation": {
            "name": "月宿傍通曆",
            "reading": "げっしゅくぼうつうれき",
            "description": "根據農曆月份和日期計算本命宿",
            "steps": [
                "步驟 1：將西曆生日轉換為農曆",
                "步驟 2：查詢該月份的「起始宿」",
                "步驟 3：起始宿 + (日期 - 1) mod 27 = 本命宿"
            ],
            "formula": "本命宿 = (月起始宿 + 日 - 1) mod 27",
            "month_start_mansions": [
                {"month": 1, "name": "正月", "start_mansion": "危宿", "index": 11},
                {"month": 2, "name": "二月", "start_mansion": "壁宿", "index": 13},
                {"month": 3, "name": "三月", "start_mansion": "婁宿", "index": 15},
                {"month": 4, "name": "四月", "start_mansion": "昴宿", "index": 17},
                {"month": 5, "name": "五月", "start_mansion": "觜宿", "index": 19},
                {"month": 6, "name": "六月", "start_mansion": "井宿", "index": 21},
                {"month": 7, "name": "七月", "start_mansion": "星宿", "index": 24},
                {"month": 8, "name": "八月", "start_mansion": "角宿", "index": 0},
                {"month": 9, "name": "九月", "start_mansion": "氐宿", "index": 2},
                {"month": 10, "name": "十月", "start_mansion": "心宿", "index": 4},
                {"month": 11, "name": "十一月", "start_mansion": "斗宿", "index": 7},
                {"month": 12, "name": "十二月", "start_mansion": "女宿", "index": 9}
            ]
        },
        "compatibility_calculation": {
            "name": "三九秘法",
            "reading": "さんくひほう",
            "description": "根據兩人本命宿的距離判斷關係類型",
            "steps": [
                "步驟 1：計算兩人本命宿的索引差",
                "步驟 2：取絕對值作為距離（0-13 範圍）",
                "步驟 3：根據距離對照六種關係"
            ],
            "formula": "距離 = min(|宿A - 宿B|, 27 - |宿A - 宿B|)",
            "distance_relations": [
                {"distances": [0], "relation": "命", "reading": "めい"},
                {"distances": [9, 18], "relation": "業胎", "reading": "ぎょうたい"},
                {"distances": [1, 3, 10, 12, 15, 17, 24, 26], "relation": "栄親", "reading": "えいしん"},
                {"distances": [2, 5, 11, 13, 14, 16, 22, 25], "relation": "友衰", "reading": "ゆうすい"},
                {"distances": [4, 6, 21, 23], "relation": "安壊", "reading": "あんかい"},
                {"distances": [7, 8, 19, 20], "relation": "危成", "reading": "きせい"}
            ]
        },
        "element_bonus": {
            "name": "元素相性",
            "reading": "げんそそうしょう",
            "description": "根據五行相生計算額外加成",
            "rules": [
                {"condition": "同元素", "bonus": 10},
                {"condition": "相生（木→火→土→金→水→木）", "bonus": 5},
                {"condition": "其他", "bonus": 0}
            ]
        }
    }


@router.get("/career-guidance/{date_str}")
def get_career_guidance(
    date_str: str,
    session: Session = Depends(get_session)
):
    """
    取得求職離職指引

    根據西曆生日計算本命宿，提供：
    - 適合的職業類型
    - 未來 30 天的求職吉日
    - 未來 30 天的離職吉日
    - 需要避開的日期

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

    result = sukuyodo_service.get_career_guidance(birth_date)

    # 記錄使用統計
    stats_service.log_usage(session, Features.SUKUYODO_LOOKUP)

    return {
        "success": True,
        "data": result
    }


@router.get("/lucky-days/categories")
async def get_lucky_day_categories():
    """
    取得所有吉日查詢類別

    返回事業、學業、居住、婚姻、醫療、旅行等類別及其項目。
    """
    categories = sukuyodo_service.get_all_lucky_day_categories()
    return {
        "success": True,
        "categories": categories
    }


@router.get("/lucky-days/summary/{date_str}")
def get_lucky_days_summary(
    date_str: str,
    session: Session = Depends(get_session)
):
    """
    取得吉日彙整

    一次返回所有重要類別的吉日：
    - 求職面試
    - 簽約談判
    - 搬家入宅
    - 結婚登記
    - 手術開刀
    - 出遊出國
    - 重要約會
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

    # 個人吉日項目
    actions = [
        # 事業
        {"category": "career", "action": "interview", "name": "求職面試"},
        {"category": "career", "action": "contract", "name": "簽約談判"},
        # 居住
        {"category": "housing", "action": "move_in", "name": "搬家入宅"},
        # 醫療
        {"category": "medical", "action": "surgery", "name": "手術開刀"},
        # 旅行
        {"category": "travel", "action": "abroad", "name": "出遊出國"},
        # 美容
        {"category": "beauty", "action": "haircut", "name": "理髮"},
        {"category": "beauty", "action": "hair_coloring", "name": "染燙髮"},
        # 購物
        {"category": "shopping", "action": "big_purchase", "name": "大額消費"},
    ]

    summary = []
    for item in actions:
        try:
            result = sukuyodo_service.get_lucky_days(
                birth_date,
                item["category"],
                item["action"],
                days_ahead=30
            )
            summary.append({
                "name": item["name"],
                "lucky_days": result["lucky_days"][:5],  # 只取前 5 個
            })
        except Exception:
            summary.append({
                "name": item["name"],
                "lucky_days": [],
            })

    stats_service.log_usage(session, Features.SUKUYODO_LOOKUP)

    return {
        "success": True,
        "data": {
            "your_mansion": sukuyodo_service.get_mansion(birth_date),
            "summary": summary
        }
    }


@router.get("/lucky-days/{date_str}")
def get_lucky_days(
    date_str: str,
    category: str,
    action: str,
    session: Session = Depends(get_session)
):
    """
    查詢特定類別的吉日

    Args:
        date_str: 西曆生日，格式 YYYY-MM-DD
        category: 類別（career/study/housing/marriage/medical/travel/beauty/dating/shopping）
        action: 具體項目（如 interview/resign/exam 等）
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

    try:
        result = sukuyodo_service.get_lucky_days(birth_date, category, action)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    # 記錄使用統計
    stats_service.log_usage(session, Features.SUKUYODO_LOOKUP)

    return {
        "success": True,
        "data": result
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

    stats_service.log_usage(session, Features.SUKUYODO_LOOKUP)

    return {
        "success": True,
        "data": result
    }


@router.get("/calendar/day/{date_str}")
def get_japanese_calendar_day(
    date_str: str,
    session: Session = Depends(get_session)
):
    """
    取得單日的日本選日曆注資訊

    Args:
        date_str: 日期，格式 YYYY-MM-DD

    Returns:
        單日選日資訊
    """
    try:
        target_date = date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="日期格式錯誤，請使用 YYYY-MM-DD"
        )

    result = japanese_calendar_service.get_day_info(target_date)

    stats_service.log_usage(session, Features.SUKUYODO_LOOKUP)

    return {
        "success": True,
        "data": result
    }


@router.get("/calendar/upcoming")
def get_upcoming_japanese_lucky_days(
    days: int = 30,
    session: Session = Depends(get_session)
):
    """
    取得未來指定天數內的日本吉日

    Args:
        days: 查詢未來幾天（預設 30，最大 90）

    Returns:
        各類吉日列表
    """
    if days < 1 or days > 90:
        raise HTTPException(
            status_code=400,
            detail="天數必須在 1-90 之間"
        )

    result = japanese_calendar_service.get_upcoming_lucky_days(days)

    stats_service.log_usage(session, Features.SUKUYODO_LOOKUP)

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
