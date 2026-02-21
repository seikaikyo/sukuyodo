"""公司自動搜尋服務 - 爬取 104 + findcompany.com.tw，計算宿曜相性"""
import logging
import re
from datetime import date
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

# findcompany 查詢設立日期
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
        從 findcompany.com.tw 查詢公司設立日期

        Args:
            company_name: 公司全名

        Returns:
            設立日期字串 (YYYY-MM-DD) 或 None
        """
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

        # findcompany 頁面結構: "設立日期" 標籤旁邊有 YYYY-MM-DD 格式日期
        for el in soup.find_all(["td", "span", "div"]):
            text = el.get_text(strip=True)
            if text == "設立日期":
                # 找下一個兄弟元素
                next_el = el.find_next_sibling()
                if next_el:
                    date_text = next_el.get_text(strip=True)
                    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", date_text)
                    if m:
                        return m.group(0)

        # 備用: 直接搜尋 HTML 中的西曆日期模式
        # findcompany 回傳的日期通常是 YYYY-MM-DD 格式
        dates = re.findall(r"\d{4}-\d{2}-\d{2}", html)
        if dates:
            # 第一個日期通常是設立日期（頁面結構穩定）
            for d in dates:
                try:
                    parsed = date.fromisoformat(d)
                    # 排除太近的日期（可能是最後變更日期等）
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
