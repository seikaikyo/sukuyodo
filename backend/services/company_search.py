"""公司自動搜尋服務 - 爬取 104 + GCIS 官方 API，計算宿曜相性"""
import logging
import re
from datetime import date, timedelta
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

from services.sukuyodo import sukuyodo_service

logger = logging.getLogger(__name__)

# 104 JSON API
_104_SEARCH_URL = "https://www.104.com.tw/jobs/search/api/jobs"
_104_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Referer": "https://www.104.com.tw/jobs/search/",
    "Accept": "application/json, text/plain, */*",
}

# GCIS 經濟部商工登記開放資料 API（主要）
_GCIS_API_URL = "https://data.gcis.nat.gov.tw/od/data/api/6BBA2268-1367-4B42-9CCA-BC17499EBE8C"

# findcompany 查詢設立日期（備援）
_FINDCOMPANY_BASE = "https://www.findcompany.com.tw"
_FINDCOMPANY_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}

# 104 地區碼
AREA_CODES = {
    "tainan": "6001014000",     # 台南市善化區
    "tainan_all": "6001000000", # 台南市全區
    "kaohsiung": "6003000000",  # 高雄市
    "stsp": "6001014000",       # 南科（善化區）
}


class CompanySearchService:
    """公司搜尋與相性計算服務"""

    async def search_104(
        self,
        keywords: str,
        area: str = "6001014000",
        pages: int = 2,
    ) -> list[dict]:
        """
        爬取 104 職缺搜尋結果

        Args:
            keywords: 搜尋關鍵字
            area: 104 地區碼
            pages: 搜尋頁數（每頁約 20 筆）

        Returns:
            公司名稱、職缺等資訊列表
        """
        results = []
        seen_companies = set()

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            for page in range(1, pages + 1):
                params = {
                    "keyword": keywords,
                    "area": area,
                    "page": str(page),
                }

                try:
                    headers = {
                        **_104_HEADERS,
                        "Referer": f"https://www.104.com.tw/jobs/search/?keyword={quote(keywords)}&area={area}",
                    }
                    resp = await client.get(
                        _104_SEARCH_URL,
                        params=params,
                        headers=headers,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e:
                    logger.warning("104 搜尋第 %d 頁失敗: %s", page, e)
                    continue

                job_list = data.get("data", [])
                if not job_list:
                    break

                for job in job_list:
                    cust_name = job.get("custName", "").strip()
                    if not cust_name or cust_name in seen_companies:
                        continue
                    seen_companies.add(cust_name)

                    # 取得職缺頁面 URL
                    link = job.get("link", {})
                    job_url = link.get("job", "")

                    results.append({
                        "company_name": cust_name,
                        "job_title": job.get("jobName", "") or job.get("jobNameSnippet", ""),
                        "location": job.get("jobAddrNoDesc", "") or job.get("jobAddress", ""),
                        "job_url": job_url,
                    })

        return results

    async def lookup_founding_date(
        self,
        company_name: str,
    ) -> str | None:
        """
        查詢公司設立日期（GCIS 官方 API 優先，findcompany 備援）

        Args:
            company_name: 公司名稱（全名或關鍵字）

        Returns:
            設立日期字串 (YYYY-MM-DD) 或 None
        """
        # 主要：GCIS 經濟部商工登記開放資料 API
        result = await self._lookup_gcis(company_name)
        if result:
            return result

        # 備援：findcompany.com.tw
        return await self._lookup_findcompany(company_name)

    async def lookup_104_company_url(self, company_name: str) -> str | None:
        """
        用公司名稱查詢 104 公司頁面連結

        Args:
            company_name: 公司名稱（全名或關鍵字）

        Returns:
            104 公司頁面 URL 或 None
        """
        # 去除常見後綴提高命中率
        search_name = company_name
        for suffix in ["股份有限公司", "有限公司"]:
            search_name = search_name.replace(suffix, "")
        search_name = search_name.strip()

        if not search_name:
            return None

        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            params = {
                "keyword": search_name,
                "page": "1",
            }
            headers = {
                **_104_HEADERS,
                "Referer": f"https://www.104.com.tw/jobs/search/?keyword={quote(search_name)}",
            }
            try:
                resp = await client.get(_104_SEARCH_URL, params=params, headers=headers)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                logger.warning("104 公司頁面查詢 %s 失敗: %s", company_name, e)
                return None

        job_list = data.get("data", [])
        if not job_list:
            return None

        # 找 custName 包含搜尋關鍵字的第一筆
        for job in job_list:
            cust_name = job.get("custName", "").strip()
            if search_name in cust_name:
                cust_url = job.get("link", {}).get("cust", "")
                if cust_url:
                    # 104 回傳的 URL 可能不含 protocol
                    if cust_url.startswith("//"):
                        cust_url = f"https:{cust_url}"
                    return cust_url

        return None

    async def search_gcis(self, keyword: str) -> list[dict]:
        """GCIS 公司名稱搜尋，回傳公司列表含設立日期"""
        search_name = keyword
        for suffix in ["股份有限公司", "有限公司"]:
            search_name = search_name.replace(suffix, "")

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.get(_GCIS_API_URL, params={
                    "$format": "json",
                    "$filter": f"Company_Name like {search_name} and Company_Status eq 01",
                    "$top": "10",
                })
                if resp.status_code != 200 or not resp.text.startswith("["):
                    return []
                data = resp.json()
            except Exception as e:
                logger.warning("GCIS 搜尋 %s 失敗: %s", keyword, e)
                return []

        results = []
        for company in data:
            setup_date = self._roc_to_western(company.get("Company_Setup_Date", ""))
            if not setup_date:
                continue
            results.append({
                "name": company.get("Company_Name", ""),
                "business_no": company.get("Business_Accounting_NO", ""),
                "founding_date": setup_date,
                "responsible": company.get("Responsible_Name", ""),
                "capital": company.get("Capital_Stock_Amount", "0"),
            })
        return results

    async def _lookup_gcis(self, company_name: str) -> str | None:
        """從 GCIS 官方 API 查詢設立日期"""
        # 去除常見後綴以提高模糊比對命中率
        search_name = company_name
        for suffix in ["股份有限公司", "有限公司"]:
            search_name = search_name.replace(suffix, "")

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.get(_GCIS_API_URL, params={
                    "$format": "json",
                    "$filter": f"Company_Name like {search_name} and Company_Status eq 01",
                    "$top": "5",
                })
                if resp.status_code != 200 or not resp.text.startswith("["):
                    return None
                data = resp.json()
            except Exception as e:
                logger.warning("GCIS 查詢 %s 失敗: %s", company_name, e)
                return None

        if not data:
            return None

        # 找最符合的公司（名稱包含原始關鍵字）
        for company in data:
            name = company.get("Company_Name", "")
            if search_name not in name:
                continue
            roc_date = company.get("Company_Setup_Date", "")
            return self._roc_to_western(roc_date)

        # 沒有完全符合的，用第一筆
        roc_date = data[0].get("Company_Setup_Date", "")
        return self._roc_to_western(roc_date)

    @staticmethod
    def _roc_to_western(roc_date: str) -> str | None:
        """民國 7 碼日期轉西曆 YYYY-MM-DD"""
        if not roc_date or len(roc_date) != 7:
            return None
        try:
            year = int(roc_date[:3]) + 1911
            month = roc_date[3:5]
            day = roc_date[5:7]
            result = f"{year}-{month}-{day}"
            date.fromisoformat(result)  # 驗證格式
            return result
        except (ValueError, IndexError):
            return None

    async def _lookup_findcompany(self, company_name: str) -> str | None:
        """從 findcompany.com.tw 查詢設立日期（備援）"""
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            try:
                url = f"{_FINDCOMPANY_BASE}/{company_name}"
                resp = await client.get(url, headers=_FINDCOMPANY_HEADERS)
                if resp.status_code != 200:
                    return None
                html = resp.text
            except Exception as e:
                logger.warning("findcompany 查詢 %s 失敗: %s", company_name, e)
                return None

        return self._parse_findcompany_date(html)

    def _parse_findcompany_date(self, html: str) -> str | None:
        """從 findcompany.com.tw HTML 解析設立日期"""
        soup = BeautifulSoup(html, "html.parser")

        for el in soup.find_all(["td", "span", "div"]):
            text = el.get_text(strip=True)
            if text == "設立日期":
                next_el = el.find_next_sibling()
                if next_el:
                    date_text = next_el.get_text(strip=True)
                    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", date_text)
                    if m:
                        return m.group(0)

        dates = re.findall(r"\d{4}-\d{2}-\d{2}", html)
        if dates:
            for d in dates:
                try:
                    parsed = date.fromisoformat(d)
                    if parsed.year < 2025:
                        return d
                except ValueError:
                    continue

        return None

    async def search_and_calculate(
        self,
        keywords: str,
        area: str,
        birth_date: date,
        min_score: int = 0,
    ) -> list[dict]:
        """
        搜尋 104 職缺 → 查設立日期 → 算相性 → 排序

        Args:
            keywords: 搜尋關鍵字
            area: 104 地區碼
            birth_date: 使用者生日
            min_score: 最低分數門檻（0 表示不篩選）

        Returns:
            按分數排序的公司相性結果
        """
        # 1. 搜尋 104
        companies = await self.search_104(keywords, area)
        if not companies:
            return []

        # 2. 對每間公司查設立日期 + 算相性
        results = []
        for company in companies:
            founding_date_str = await self.lookup_founding_date(company["company_name"])
            if not founding_date_str:
                continue

            try:
                founding_date = date.fromisoformat(founding_date_str)
            except ValueError:
                continue

            # 3. 計算相性
            try:
                compat = sukuyodo_service.calculate_compatibility(birth_date, founding_date)
            except Exception as e:
                logger.warning("相性計算失敗 %s: %s", company["company_name"], e)
                continue

            score = compat.get("score", 0)
            relation = compat.get("relation", {})
            relation_type = relation.get("type", "")
            direction = relation.get("direction", "")

            # 判定推薦等級
            verdict = self._get_verdict(relation_type, direction, score)

            results.append({
                "name": company["company_name"],
                "founding_date": founding_date_str,
                "score": score,
                "relation_name": relation.get("name", ""),
                "relation_type": relation_type,
                "direction": direction,
                "distance_type": relation.get("distance_type", ""),
                "distance_type_name": relation.get("distance_type_name", ""),
                "element_bonus": compat.get("element_bonus", 0),
                "verdict": verdict,
                "job_title": company["job_title"],
                "location": company["location"],
                "job_url": company["job_url"],
                "person1_mansion": compat.get("person1", {}).get("mansion", ""),
                "person1_element": compat.get("person1", {}).get("element", ""),
                "person2_mansion": compat.get("person2", {}).get("mansion", ""),
                "person2_element": compat.get("person2", {}).get("element", ""),
            })

        # 4. 篩選 + 排序
        if min_score > 0:
            results = [r for r in results if r["score"] >= min_score]

        results.sort(key=lambda r: r["score"], reverse=True)
        return results

    def batch_analyze(
        self,
        birth_date: date,
        year: int,
        companies: list[dict],
    ) -> dict:
        """
        批次分析公司：相性 + 公司流年 + 梯隊排名 + RC 風險

        Args:
            birth_date: 使用者生日
            year: 分析年份
            companies: [{id, name, founding_date, memo?, job_url?}]

        Returns:
            使用者流年 + 每間公司的綜合分析 + 梯隊統計
        """
        # 1. 計算使用者九曜流年（只做一次）
        user_yearly = sukuyodo_service.calculate_yearly_fortune(birth_date, year)

        # 2. 逐間公司計算
        results = []
        for company in companies:
            founding_date_str = company.get("founding_date", "")
            try:
                founding = date.fromisoformat(founding_date_str)
            except (ValueError, TypeError):
                continue

            # 相性
            try:
                compat = sukuyodo_service.calculate_compatibility(birth_date, founding)
            except Exception:
                continue

            score = compat.get("score", 0)
            relation = compat.get("relation", {})
            relation_type = relation.get("type", "")
            direction = relation.get("direction", "")

            # 公司九曜流年（輕量：只取 kuyou_star + overall + career）
            try:
                company_yearly = sukuyodo_service.calculate_yearly_fortune(founding, year)
                company_kuyou = company_yearly.get("kuyou_star", {})
                company_fortune = {
                    "kuyou_star": company_kuyou,
                    "overall": company_yearly.get("fortune", {}).get("overall", 50),
                    "career": company_yearly.get("fortune", {}).get("career", 50),
                }
            except Exception:
                company_kuyou = {}
                company_fortune = {"kuyou_star": {}, "overall": 50, "career": 50}

            company_level = company_kuyou.get("level", "末吉")

            # 梯隊
            tier = self._calculate_tier(score, company_level, relation_type, direction)

            # RC 風險
            memo = company.get("memo", "")
            ref_check = self._estimate_ref_check(company.get("name", ""), memo)

            # 投遞建議
            recommendation = self._build_recommendation(
                tier, ref_check, score, company_level, relation_type, direction
            )

            results.append({
                "id": company.get("id", ""),
                "name": company.get("name", ""),
                "compatibility": {
                    "score": score,
                    "relation": relation,
                    "person2": compat.get("person2", {}),
                },
                "company_fortune": company_fortune,
                "tier": tier,
                "ref_check": ref_check,
                "recommendation": recommendation,
                "memo": memo,
                "job_url": company.get("job_url", ""),
            })

        # 3. 按梯隊 + 分數排序
        results.sort(key=lambda r: (r["tier"]["rank"], -r["compatibility"]["score"]))

        # 4. 設定 priority
        for i, r in enumerate(results, 1):
            r["recommendation"]["priority"] = i

        # 5. 梯隊統計
        tier_summary = {"tier_1": 0, "tier_2": 0, "tier_3": 0, "tier_4": 0}
        for r in results:
            key = f"tier_{r['tier']['rank']}"
            tier_summary[key] = tier_summary.get(key, 0) + 1

        return {
            "user": {
                "mansion": user_yearly.get("your_mansion", {}),
                "yearly_fortune": {
                    "kuyou_star": user_yearly.get("kuyou_star", {}),
                    "overall": user_yearly.get("fortune", {}).get("overall", 50),
                    "career": user_yearly.get("fortune", {}).get("career", 50),
                },
            },
            "companies": results,
            "tier_summary": tier_summary,
        }

    def calculate_lucky_dates(
        self,
        birth_date: date,
        start_date: date | None = None,
        days: int = 30,
    ) -> dict:
        """
        計算吉凶日期清單

        根據個人每日運勢的 career 分數，篩選出吉日和凶日。
        good_dates: career >= 80 且無暗黒/凌犯
        bad_dates: career <= 48 或有安壊/暗黒/凌犯

        Args:
            birth_date: 使用者出生日期
            start_date: 起始日期（預設 today）
            days: 查詢天數

        Returns:
            { good_dates, bad_dates, dark_weeks }
        """
        if start_date is None:
            start_date = date.today()

        weekday_names = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
        good_dates = []
        bad_dates = []
        dark_ranges: list[tuple[date, date]] = []
        current_dark_start: date | None = None

        for i in range(days):
            target = start_date + timedelta(days=i)
            try:
                fortune = sukuyodo_service.calculate_daily_fortune(birth_date, target)
            except Exception:
                continue

            scores = fortune.get("fortune", {})
            career = scores.get("career", 50)
            level = scores.get("level_name", "")
            day_mansion = fortune.get("day_mansion", {})
            mansion_rel = fortune.get("mansion_relation", {})
            sanki = fortune.get("sanki", {})
            ryouhan = fortune.get("ryouhan", {})
            special = fortune.get("special_day")

            is_dark = sanki.get("is_dark_week", False) if sanki else False
            is_ryouhan = ryouhan.get("active", False) if ryouhan else False
            rel_type = mansion_rel.get("type", "") if mansion_rel else ""

            # 暗黒の一週間追蹤
            if is_dark:
                if current_dark_start is None:
                    current_dark_start = target
            else:
                if current_dark_start is not None:
                    dark_ranges.append((current_dark_start, target - timedelta(days=1)))
                    current_dark_start = None

            # 組裝 flags 和 reason
            flags = []
            reasons = []
            if special:
                flags.append(special.get("name", ""))
            if rel_type == "mei":
                flags.append("命宿日")
            if is_dark:
                flags.append("暗黒の一週間")
            if is_ryouhan:
                flags.append("凌犯期間")
            if rel_type == "ankai":
                flags.append("安壊")

            weekday = weekday_names[target.weekday()]

            entry = {
                "date": target.isoformat(),
                "weekday": weekday,
                "career": career,
                "level": level,
                "day_mansion": day_mansion.get("name_jp", ""),
                "relation": mansion_rel.get("name", "") if mansion_rel else "",
                "flags": flags,
                "reason": " + ".join(flags) if flags else level,
            }

            # 吉日: career >= 80 且無負面因素
            if career >= 80 and not is_dark and not is_ryouhan and rel_type != "ankai":
                good_dates.append(entry)
            # 凶日: career <= 48 或有安壊/暗黒/凌犯
            elif career <= 48 or is_dark or is_ryouhan or rel_type == "ankai":
                bad_dates.append(entry)

        # 結尾暗黒期間
        if current_dark_start is not None:
            dark_ranges.append((current_dark_start, start_date + timedelta(days=days - 1)))

        dark_weeks = [
            {"start": s.isoformat(), "end": e.isoformat()}
            for s, e in dark_ranges
        ]

        return {
            "good_dates": good_dates,
            "bad_dates": bad_dates,
            "dark_weeks": dark_weeks,
        }

    def _calculate_tier(
        self,
        compat_score: int,
        company_kuyou_level: str,
        relation_type: str,
        direction: str,
    ) -> dict:
        """計算梯隊排名"""
        is_good_fortune = company_kuyou_level in ("大吉", "半吉")
        is_great_fortune = company_kuyou_level == "大吉"
        is_bad_fortune = company_kuyou_level == "大凶"

        if compat_score >= 90 and is_great_fortune:
            rank = 1
        elif (compat_score >= 65 and is_good_fortune) or (compat_score >= 90 and is_good_fortune):
            rank = 2
        elif compat_score >= 90 and is_bad_fortune:
            rank = 3
        else:
            rank = 4

        # 安壊壊方向降一級
        if relation_type == "ankai" and direction == "壊" and rank < 4:
            rank += 1

        labels = {
            1: "第一梯隊",
            2: "第二梯隊",
            3: "第三梯隊",
            4: "第四梯隊",
        }
        css_classes = {
            1: "tier-1",
            2: "tier-2",
            3: "tier-3",
            4: "tier-4",
        }
        reasons = {
            1: "相性極佳且公司今年大吉",
            2: "相性良好且公司今年運勢不差",
            3: "相性佳但公司今年運勢低迷",
            4: "綜合條件需審慎評估",
        }

        return {
            "rank": rank,
            "label": labels[rank],
            "css_class": css_classes[rank],
            "reason": reasons[rank],
        }

    def _estimate_ref_check(self, company_name: str, memo: str) -> dict:
        """估算 Reference Check 風險"""
        combined = f"{company_name} {memo}".lower()

        # 高風險：上市大廠、金融業
        high_keywords = [
            "台積電", "鴻海", "聯發科", "日月光", "中華電信",
            "台達電", "廣達", "仁寶", "緯創", "和碩",
            "國泰", "富邦", "中信", "玉山", "兆豐",
            "銀行", "證券", "保險", "金控",
        ]
        for kw in high_keywords:
            if kw in combined:
                return {
                    "risk_level": "high",
                    "risk_label": "高",
                    "reason": f"大型企業/金融業，RC 流程嚴謹（含 {kw}）",
                }

        # 中風險：科技/半導體/製造業
        mid_keywords = [
            "科技", "半導體", "光電", "精密", "電子",
            "資訊", "通訊", "系統", "智慧", "自動化",
            "製造", "工業", "材料",
        ]
        for kw in mid_keywords:
            if kw in combined:
                return {
                    "risk_level": "medium",
                    "risk_label": "中",
                    "reason": f"中型科技/製造業，可能有基本 RC（含 {kw}）",
                }

        return {
            "risk_level": "low",
            "risk_label": "低",
            "reason": "一般企業，RC 機率較低",
        }

    def _build_recommendation(
        self,
        tier: dict,
        ref_check: dict,
        score: int,
        company_level: str,
        relation_type: str,
        direction: str,
    ) -> dict:
        """產生投遞建議"""
        rank = tier["rank"]
        action_items = []

        if rank == 1:
            summary = "強力推薦投遞，相性和時機都好"
            action_items.append("優先準備履歷和面試")
            action_items.append("把握今年的好運勢積極爭取")
        elif rank == 2:
            summary = "值得投遞，條件良好"
            action_items.append("正常準備即可")
        elif rank == 3:
            summary = "相性好但今年時機一般，可投但別押寶"
            action_items.append("同時準備其他選項")
            action_items.append("面試時注意公司近期狀況")
        else:
            summary = "條件一般，當備選方案"
            action_items.append("先投其他梯隊的公司")

        if ref_check["risk_level"] == "high":
            action_items.append("RC 風險高，確認前東家關係良好")
        elif ref_check["risk_level"] == "medium":
            action_items.append("可能有 RC，準備好推薦人選")

        if relation_type == "ankai" and direction == "壊":
            action_items.append("壊方關係，面試和入職後留意人際衝突")

        return {
            "priority": 0,  # 排序後再設定
            "summary": summary,
            "action_items": action_items,
        }

    def _get_verdict(self, relation_type: str, direction: str, score: int) -> str:
        """根據關係類型和方向判定推薦等級"""
        if relation_type == "eishin":
            return "推薦"
        if relation_type == "gyotai":
            return "適合"
        if relation_type == "ankai":
            if direction == "壊":
                return "避開"
            return "留意"
        if relation_type == "kisei":
            if direction == "危":
                return "留意"
            return "可考慮"
        if relation_type == "yusui":
            return "留意"
        if relation_type == "mei":
            return "中性"
        # fallback
        if score >= 80:
            return "推薦"
        if score >= 65:
            return "可考慮"
        return "留意"


company_search_service = CompanySearchService()
