"""日本選日曆注服務 - 傳統擇日系統"""
from datetime import date, timedelta
from typing import Literal


class JapaneseCalendarService:
    """
    日本選日曆注服務

    實作日本傳統的選日系統，包含：
    - 一粒萬倍日（いちりゅうまんばいび）
    - 天赦日（てんしゃにち/てんしゃび）
    - 寅の日（とらのひ）
    - 巳の日（みのひ）
    - 不成就日（ふじょうじゅび）
    - 六曜（ろくよう）
    """

    # 天干（十干）
    STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    STEMS_READING = ["きのえ", "きのと", "ひのえ", "ひのと", "つちのえ",
                     "つちのと", "かのえ", "かのと", "みずのえ", "みずのと"]

    # 地支（十二支）
    BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    BRANCHES_READING = ["ね", "うし", "とら", "う", "たつ", "み",
                        "うま", "ひつじ", "さる", "とり", "いぬ", "い"]
    BRANCHES_ANIMAL = ["鼠", "牛", "虎", "兔", "龍", "蛇", "馬", "羊", "猴", "雞", "狗", "豬"]

    # 六曜順序
    ROKUYO = ["先勝", "友引", "先負", "仏滅", "大安", "赤口"]
    ROKUYO_READING = ["せんしょう", "ともびき", "せんぶ", "ぶつめつ", "たいあん", "しゃっこう"]
    ROKUYO_MEANING = [
        "午前吉、午後凶",
        "朝夕吉、正午凶",
        "午前凶、午後吉",
        "終日凶、慶事避ける",
        "終日吉、万事大吉",
        "正午前後一時吉、他凶"
    ]

    # 一粒萬倍日：每月對應的地支
    # 格式：{月份: [地支索引列表]}
    ICHIRYUMANBAI_MAP = {
        1: [1, 6],    # 丑、午
        2: [8, 2],    # 酉、寅（注：日本曆法中二月為酉、寅）
        3: [0, 3],    # 子、卯
        4: [3, 8],    # 卯、酉（注：日本曆法中四月為卯、酉）
        5: [4, 9],    # 辰、酉
        6: [5, 8],    # 巳、酉（注：日本曆法中六月為巳、酉）
        7: [6, 11],   # 午、亥
        8: [0, 7],    # 子、未
        9: [3, 8],    # 卯、酉（注：日本曆法中九月為卯、酉）
        10: [1, 6],   # 丑、午
        11: [2, 7],   # 寅、未
        12: [0, 3],   # 子、卯
    }

    # 天赦日：季節對應的干支組合
    # 春(2-4月)=戊寅, 夏(5-7月)=甲午, 秋(8-10月)=戊申, 冬(11-1月)=甲子
    TENSYA_MAP = {
        "spring": (4, 2),   # 戊寅 (stem=4, branch=2)
        "summer": (0, 6),   # 甲午 (stem=0, branch=6)
        "autumn": (4, 8),   # 戊申 (stem=4, branch=8)
        "winter": (0, 0),   # 甲子 (stem=0, branch=0)
    }

    # 不成就日：每月的特定日期
    # 日本不成就日每月有固定的日期模式
    FUJOUBYOU_PATTERN = {
        1: [3, 11, 19, 27],
        2: [2, 10, 18, 26],
        3: [1, 9, 17, 25],
        4: [4, 12, 20, 28],
        5: [5, 13, 21, 29],
        6: [6, 14, 22, 30],
        7: [3, 11, 19, 27],
        8: [8, 16, 24],
        9: [1, 9, 17, 25],
        10: [4, 12, 20, 28],
        11: [5, 13, 21, 29],
        12: [6, 14, 22, 30],
    }

    def __init__(self):
        pass

    def get_stem_branch(self, target_date: date) -> tuple[int, int]:
        """
        計算日干支

        使用 1900-01-01 為甲子日 (0, 0) 作為基準

        Args:
            target_date: 目標日期

        Returns:
            (天干索引, 地支索引)
        """
        # 1900-01-01 是甲子日
        base = date(1900, 1, 1)
        days = (target_date - base).days
        stem = days % 10
        branch = days % 12
        return stem, branch

    def get_stem_branch_name(self, target_date: date) -> dict:
        """
        取得日干支的完整資訊

        Args:
            target_date: 目標日期

        Returns:
            包含干支名稱、讀音的字典
        """
        stem, branch = self.get_stem_branch(target_date)
        return {
            "stem": self.STEMS[stem],
            "stem_reading": self.STEMS_READING[stem],
            "branch": self.BRANCHES[branch],
            "branch_reading": self.BRANCHES_READING[branch],
            "animal": self.BRANCHES_ANIMAL[branch],
            "full": f"{self.STEMS[stem]}{self.BRANCHES[branch]}",
            "stem_index": stem,
            "branch_index": branch
        }

    def get_season(self, target_date: date) -> Literal["spring", "summer", "autumn", "winter"]:
        """
        根據月份判定季節

        日本傳統曆法的季節劃分：
        - 春：2月、3月、4月
        - 夏：5月、6月、7月
        - 秋：8月、9月、10月
        - 冬：11月、12月、1月

        Args:
            target_date: 目標日期

        Returns:
            季節名稱
        """
        month = target_date.month
        if month in [2, 3, 4]:
            return "spring"
        elif month in [5, 6, 7]:
            return "summer"
        elif month in [8, 9, 10]:
            return "autumn"
        else:
            return "winter"

    def is_ichiryumanbai(self, target_date: date) -> bool:
        """
        判定是否為一粒萬倍日

        一粒萬倍日意為「一粒種子可收穫萬倍」，
        適合開業、投資、求財等開始新事物的日子。

        Args:
            target_date: 目標日期

        Returns:
            是否為一粒萬倍日
        """
        _, branch = self.get_stem_branch(target_date)
        valid_branches = self.ICHIRYUMANBAI_MAP.get(target_date.month, [])
        return branch in valid_branches

    def is_tensya(self, target_date: date) -> bool:
        """
        判定是否為天赦日

        天赦日是一年中最吉祥的日子，
        「天が万物の罪を赦す日」（天赦萬物之罪的日子）。
        一年約有 5-6 天。

        Args:
            target_date: 目標日期

        Returns:
            是否為天赦日
        """
        stem, branch = self.get_stem_branch(target_date)
        season = self.get_season(target_date)
        required = self.TENSYA_MAP[season]
        return (stem, branch) == required

    def is_tora_no_hi(self, target_date: date) -> bool:
        """
        判定是否為寅の日

        寅（虎）被視為財運之神毘沙門天的使者，
        適合求財、開運、旅行出發。
        每 12 天一次。

        Args:
            target_date: 目標日期

        Returns:
            是否為寅の日
        """
        _, branch = self.get_stem_branch(target_date)
        return branch == 2  # 寅

    def is_mi_no_hi(self, target_date: date) -> bool:
        """
        判定是否為巳の日

        巳（蛇）被視為弁財天的使者，
        適合財運、藝術、才能相關的祈願。
        每 12 天一次。

        Args:
            target_date: 目標日期

        Returns:
            是否為巳の日
        """
        _, branch = self.get_stem_branch(target_date)
        return branch == 5  # 巳

    def is_tsuchinoto_mi(self, target_date: date) -> bool:
        """
        判定是否為己巳の日（つちのとみのひ）

        己巳之日是巳の日中特別吉祥的日子，
        被認為是最強的金運日。
        每 60 天一次。

        Args:
            target_date: 目標日期

        Returns:
            是否為己巳の日
        """
        stem, branch = self.get_stem_branch(target_date)
        return stem == 5 and branch == 5  # 己巳

    def is_fujoubyou(self, target_date: date) -> bool:
        """
        判定是否為不成就日

        不成就日意為「何事も成就しない日」（萬事不成之日），
        應避免開始新事物、簽約、結婚等重要事項。

        Args:
            target_date: 目標日期

        Returns:
            是否為不成就日
        """
        month = target_date.month
        day = target_date.day
        pattern = self.FUJOUBYOU_PATTERN.get(month, [])
        return day in pattern

    def get_rokuyo(self, target_date: date) -> dict:
        """
        計算六曜

        六曜是日本最常用的曆注之一，
        依序為：先勝、友引、先負、仏滅、大安、赤口

        計算方式：(農曆月 + 農曆日) mod 6

        Args:
            target_date: 目標日期

        Returns:
            六曜資訊
        """
        # 簡化計算：使用西曆日期的近似算法
        # 實際上應該使用農曆，但這裡採用常見的近似方法
        # (月 + 日) mod 6
        idx = (target_date.month + target_date.day) % 6
        return {
            "name": self.ROKUYO[idx],
            "reading": self.ROKUYO_READING[idx],
            "meaning": self.ROKUYO_MEANING[idx],
            "index": idx
        }

    def get_day_info(self, target_date: date) -> dict:
        """
        取得單日的完整選日資訊

        Args:
            target_date: 目標日期

        Returns:
            包含所有選日資訊的字典
        """
        # 計算各種吉日
        is_ichiryu = self.is_ichiryumanbai(target_date)
        is_ten = self.is_tensya(target_date)
        is_tora = self.is_tora_no_hi(target_date)
        is_mi = self.is_mi_no_hi(target_date)
        is_tsuchi_mi = self.is_tsuchinoto_mi(target_date)
        is_fujo = self.is_fujoubyou(target_date)

        # 收集類型和標籤
        types = []
        labels = []

        if is_ten:
            types.append("tensya")
            labels.append("天赦日")
        if is_ichiryu:
            types.append("ichiryumanbai")
            labels.append("一粒萬倍日")
        if is_tsuchi_mi:
            types.append("tsuchinoto_mi")
            labels.append("己巳の日")
        elif is_mi:
            types.append("mi_no_hi")
            labels.append("巳の日")
        if is_tora:
            types.append("tora_no_hi")
            labels.append("寅の日")

        # 判斷是否為超吉日（多重吉日重疊）
        lucky_count = len(types)
        is_super_lucky = lucky_count >= 2

        # 取得干支和六曜
        stem_branch = self.get_stem_branch_name(target_date)
        rokuyo = self.get_rokuyo(target_date)

        # 星期幾
        weekday_names = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
        weekday = weekday_names[target_date.weekday()]

        return {
            "date": target_date.isoformat(),
            "weekday": weekday,
            "stem_branch": stem_branch,
            "rokuyo": rokuyo,
            "types": types,
            "labels": labels,
            "is_super_lucky": is_super_lucky,
            "is_fujoubyou": is_fujo
        }

    def get_calendar_days(self, year: int, month: int) -> dict:
        """
        取得整月的選日資訊

        Args:
            year: 年份
            month: 月份 (1-12)

        Returns:
            包含吉日列表和凶日列表的字典
        """
        # 計算該月有多少天
        if month == 12:
            next_month = date(year + 1, 1, 1)
        else:
            next_month = date(year, month + 1, 1)
        first_day = date(year, month, 1)
        days_in_month = (next_month - first_day).days

        lucky_days = []
        unlucky_days = []

        for day in range(1, days_in_month + 1):
            target_date = date(year, month, day)
            day_info = self.get_day_info(target_date)

            # 有吉日類型的加入 lucky_days
            if day_info["types"]:
                lucky_days.append({
                    "date": day_info["date"],
                    "weekday": day_info["weekday"],
                    "types": day_info["types"],
                    "labels": day_info["labels"],
                    "is_super_lucky": day_info["is_super_lucky"],
                    "stem_branch": day_info["stem_branch"]["full"],
                    "rokuyo": day_info["rokuyo"]["name"]
                })

            # 不成就日加入 unlucky_days
            if day_info["is_fujoubyou"]:
                unlucky_days.append({
                    "date": day_info["date"],
                    "weekday": day_info["weekday"],
                    "type": "fujoubyou",
                    "label": "不成就日",
                    "stem_branch": day_info["stem_branch"]["full"],
                    "rokuyo": day_info["rokuyo"]["name"]
                })

        return {
            "year": year,
            "month": month,
            "days": lucky_days,
            "unlucky_days": unlucky_days,
            "summary": {
                "tensya_count": sum(1 for d in lucky_days if "tensya" in d["types"]),
                "ichiryumanbai_count": sum(1 for d in lucky_days if "ichiryumanbai" in d["types"]),
                "tora_count": sum(1 for d in lucky_days if "tora_no_hi" in d["types"]),
                "mi_count": sum(1 for d in lucky_days if "mi_no_hi" in d["types"] or "tsuchinoto_mi" in d["types"]),
                "super_lucky_count": sum(1 for d in lucky_days if d["is_super_lucky"]),
                "fujoubyou_count": len(unlucky_days)
            }
        }

    def get_upcoming_lucky_days(self, days_ahead: int = 30) -> dict:
        """
        取得未來指定天數內的吉日

        Args:
            days_ahead: 查詢未來幾天（預設 30）

        Returns:
            包含各類吉日列表的字典
        """
        today = date.today()
        result = {
            "tensya": [],
            "ichiryumanbai": [],
            "tora_no_hi": [],
            "mi_no_hi": [],
            "tsuchinoto_mi": [],
            "super_lucky": [],
            "fujoubyou": []
        }

        for i in range(days_ahead):
            target_date = today + timedelta(days=i)
            day_info = self.get_day_info(target_date)

            base_info = {
                "date": day_info["date"],
                "weekday": day_info["weekday"],
                "stem_branch": day_info["stem_branch"]["full"]
            }

            if "tensya" in day_info["types"]:
                result["tensya"].append(base_info)
            if "ichiryumanbai" in day_info["types"]:
                result["ichiryumanbai"].append(base_info)
            if "tora_no_hi" in day_info["types"]:
                result["tora_no_hi"].append(base_info)
            if "mi_no_hi" in day_info["types"]:
                result["mi_no_hi"].append(base_info)
            if "tsuchinoto_mi" in day_info["types"]:
                result["tsuchinoto_mi"].append(base_info)
            if day_info["is_super_lucky"]:
                result["super_lucky"].append({
                    **base_info,
                    "types": day_info["types"],
                    "labels": day_info["labels"]
                })
            if day_info["is_fujoubyou"]:
                result["fujoubyou"].append(base_info)

        return result


# 全域實例
japanese_calendar_service = JapaneseCalendarService()
