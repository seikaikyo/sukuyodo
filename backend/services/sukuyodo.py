"""宿曜道計算服務 - 日本真言宗占星術"""
import json
import random
from datetime import date
from pathlib import Path
from typing import Optional


class SukuyodoService:
    """
    宿曜道（真言宗宿曜占星術）計算服務

    基於空海《宿曜經》，使用農曆生日計算本命宿（27宿之一），
    並提供雙人相性診斷（六種關係）。
    """

    # 月宿傍通曆：農曆月份對應的起始宿
    # 每月初一從這個宿開始，之後每天進一宿
    MONTH_START_MANSION = {
        1: 11,   # 正月：室宿
        2: 13,   # 二月：奎宿
        3: 15,   # 三月：胃宿
        4: 17,   # 四月：畢宿
        5: 19,   # 五月：参宿
        6: 21,   # 六月：鬼宿
        7: 24,   # 七月：張宿
        8: 0,    # 八月：角宿
        9: 2,    # 九月：氐宿
        10: 4,   # 十月：心宿
        11: 7,   # 十一月：斗宿
        12: 9,   # 十二月：虛宿
    }

    # 距離類型對照表：用於判斷近距離/中距離/遠距離及方向性
    # 依據 yakumoin.net（八雲院）絕對距離分類：
    #   近距離 = abs_dist 0-4（含業/胎）→ d=0,1,2,3,4,9,18,23,24,25,26
    #   中距離 = abs_dist 5-8           → d=5,6,7,8,19,20,21,22
    #   遠距離 = abs_dist 10-13         → d=10,11,12,13,14,15,16,17
    # direction_map: 從 person1 角度看，該距離代表的方向（如 1 = 栄，26 = 親）
    DISTANCE_TYPE_MAP = {
        "eishin": {
            "near": {"distances": [1, 26], "direction_map": {1: "栄", 26: "親"}},
            "mid": {"distances": [8, 19], "direction_map": {8: "親", 19: "栄"}},
            "far": {"distances": [10, 17], "direction_map": {10: "栄", 17: "親"}}
        },
        "yusui": {
            "near": {"distances": [2, 25], "direction_map": {2: "衰", 25: "友"}},
            "mid": {"distances": [7, 20], "direction_map": {7: "友", 20: "衰"}},
            "far": {"distances": [11, 16], "direction_map": {11: "衰", 16: "友"}}
        },
        "ankai": {
            "near": {"distances": [3, 24], "direction_map": {3: "安", 24: "壊"}},
            "mid": {"distances": [6, 21], "direction_map": {6: "壊", 21: "安"}},
            "far": {"distances": [12, 15], "direction_map": {12: "安", 15: "壊"}}
        },
        "kisei": {
            "near": {"distances": [4, 23], "direction_map": {4: "危", 23: "成"}},
            "mid": {"distances": [5, 22], "direction_map": {5: "成", 22: "危"}},
            "far": {"distances": [13, 14], "direction_map": {13: "危", 14: "成"}}
        },
        "mei": {"near": {"distances": [0], "direction_map": {0: "命"}}},
        "gyotai": {
            "near": {"distances": [9, 18], "direction_map": {9: "業", 18: "胎"}}
        }
    }

    # === 原典三九秘法：位名對照 ===
    # distance 0-8 = 一九（命行）, 9-17 = 二九（業行）, 18-26 = 三九（胎行）
    # 各九的起始位不同（命/業/胎），後續 8 位（栄→衰→安→危→成→壊→友→親）共通
    SANKU_POSITION_NAMES = [
        "命", "栄", "衰", "安", "危", "成", "壊", "友", "親",  # 一九
        "業", "栄", "衰", "安", "危", "成", "壊", "友", "親",  # 二九
        "胎", "栄", "衰", "安", "危", "成", "壊", "友", "親",  # 三九
    ]

    SANKU_GROUP_NAMES = {
        1: {"name": "一九（命行）", "reading": "いっく（めいぎょう）", "head": "命"},
        2: {"name": "二九（業行）", "reading": "にく（ごうぎょう）", "head": "業"},
        3: {"name": "三九（胎行）", "reading": "さんく（たいぎょう）", "head": "胎"},
    }

    # 原典經文對照（T21n1299 卷下 各日吉凶詳述 p.397c-398a）
    CLASSICAL_POSITION_TEXTS = {
        "命": {
            "sutra": "命宿日、胎宿日，不宜舉動百事。",
            "ref": "T21, p.397c",
            "interpretation": "命宿是本命位置，對方落在此處代表你們如鏡相照，根源相同。經文說命日不宜妄動，暗示這段關係中雙方容易彼此牽制，需以觀照取代衝動。",
        },
        "業": {
            "sutra": "值業宿日，所作善惡亦不成就，甚衰。",
            "ref": "T21, p.397c",
            "interpretation": "業宿代表過去累積的因果。對方落在此位，彼此有深厚的業力牽連。經文直言業日做事難成，提醒這段關係中不宜急躁推進，順其自然比強求更好。",
        },
        "胎": {
            "sutra": "命宿日、胎宿日，不宜舉動百事。",
            "ref": "T21, p.397c",
            "interpretation": "胎宿代表未來的可能性，帶有來世延續的因緣。與命宿同樣不宜妄動，但胎含孕育之意，靜待時機成熟方可行動。",
        },
        "栄": {
            "sutra": "若榮宿日，即宜入官拜職、對見大人、上書表進獻君王、興營買賣、裁著新衣、沐浴及諸吉事並大吉。",
            "ref": "T21, p.397c",
            "interpretation": "栄宿是繁榮興旺之位。對方落在你的栄位，代表此人帶給你好運和提升的能量。經文列舉入官拜職、買賣等諸多吉事，是最適合積極行動的位置。",
        },
        "衰": {
            "sutra": "若衰日，唯宜解除諸惡、療病。",
            "ref": "T21, p.398a",
            "interpretation": "衰宿主療癒與消退。對方落在你的衰位，此人在你的生命中扮演療癒者的角色——幫你排除負面、治療傷痛。但經文用「唯宜」二字限定，代表這段關係的作用僅止於療傷，無法帶來進一步的提升或發展。",
        },
        "安": {
            "sutra": "若安宿日，移徙吉，遠行人入宅、造作園宅、安坐臥床帳、作壇場並吉。",
            "ref": "T21, p.397c-398a",
            "interpretation": "安宿主穩定和安居。對方落在你的安位，代表此人帶給你安定感。經文提到遷居、造宅等安頓之事皆吉，這段關係有穩固根基的作用。",
        },
        "危": {
            "sutra": "若危壞日，並不宜遠行出、入移徙、買賣、婚姻、裁衣、剃頭、沐浴並凶。",
            "ref": "T21, p.398a",
            "interpretation": "危宿主變動和風險。對方落在你的危位，代表此人會為你帶來挑戰和不確定性。經文警告諸事不宜，你與此人互動時需特別謹慎，避免做重大決定。",
        },
        "成": {
            "sutra": "若成宿日，宜修道學問、合和長年藥法，作諸成就法並吉。",
            "ref": "T21, p.398a",
            "interpretation": "成宿主成就和學習。對方落在你的成位，代表此人是你借力成事的對象。經文提到修道學問、合藥成就，這段關係適合在專業領域互相切磋、共同精進。",
        },
        "壊": {
            "sutra": "若壞日，宜作鎮壓、降伏怨讎及討伐阻壞奸惡之謀，餘並不堪。",
            "ref": "T21, p.398a",
            "interpretation": "壊宿主破壞和降伏。對方落在你的壊位，代表此人會打破你的既有模式。經文指出壊日只適合鎮壓降伏，「餘並不堪」四字表明這股力量是一次性的，衝擊過後便歸於平靜。",
        },
        "友": {
            "sutra": "若友宿日、親宿日，宜結交、定婚姻，歡宴聚會並吉。",
            "ref": "T21, p.398a",
            "interpretation": "友宿主交誼和給予。對方落在你的友位，你是這段關係中主動付出的一方。經文明確指出友日適合結交和婚姻，是社交吉位。",
        },
        "親": {
            "sutra": "若友宿日、親宿日，宜結交、定婚姻，歡宴聚會並吉。",
            "ref": "T21, p.398a",
            "interpretation": "親宿主親近和吸引。對方落在你的親位，代表此人自然被你吸引。與友宿共用經文，同為社交吉位，差別在於親是接受方、友是給予方。",
        },
    }

    # 三九秘法位置 → 現代行動建議（職場/人際實用化）
    PRACTICAL_ACTION_MAP = {
        "命": {
            "do": ["深入自我觀察", "與對方互相映照優缺點"],
            "avoid": ["衝動行事", "在關係中強求主導"],
            "career": "適合做長期夥伴或合夥人，但需要明確分工避免互相牽制",
        },
        "栄": {
            "do": ["積極爭取合作機會", "借力拓展事業版圖", "把握對方帶來的資源"],
            "avoid": ["錯過黃金時機", "對好運視而不見"],
            "career": "對方能提升你的職場運勢，適合主動投遞、爭取面試",
        },
        "衰": {
            "do": ["放慢節奏", "借助對方反省自身不足", "處理累積的問題"],
            "avoid": ["期待對方帶來直接好處", "在此關係中投入過多資源"],
            "career": "對方在你的生命中扮演療癒者角色，適合短期合作而非長期依賴",
        },
        "安": {
            "do": ["建立穩定的合作基礎", "推進安頓性質的事務", "長期佈局"],
            "avoid": ["急於求成", "忽略細節和根基"],
            "career": "此公司環境穩定踏實，適合需要安定感的職場發展",
        },
        "危": {
            "do": ["保持警覺", "做好風險評估", "設定停損點"],
            "avoid": ["做重大決定", "忽視不安的直覺"],
            "career": "此關係帶有變動性，互動時需特別謹慎",
        },
        "成": {
            "do": ["在專業領域深入合作", "共同學習精進", "推動專案落地"],
            "avoid": ["只談不做", "忽略成果驗收"],
            "career": "適合在技術或專業領域借力成事，共同精進",
        },
        "壊": {
            "do": ["利用衝擊力打破僵局", "在必要時果斷行動"],
            "avoid": ["長期消耗", "期望維持現狀不變"],
            "career": "此關係的衝擊是一次性的，適合短期突破而非長期合作",
        },
        "友": {
            "do": ["主動付出和照顧", "建立社交連結", "分享資源"],
            "avoid": ["只付出不設界限", "忽略自身需求"],
            "career": "你是關係中的給予方，投入的心力會轉化為人脈和信任",
        },
        "親": {
            "do": ["接受對方的善意", "順勢發展關係", "擴大交友圈"],
            "avoid": ["被動等待", "不回應對方的好意"],
            "career": "對方自然被你吸引，合作意願高，抓住這份緣分",
        },
        "業": {
            "do": ["順應因果自然發展", "理解前世今生的牽連"],
            "avoid": ["強行改變關係走向", "急躁推進"],
            "career": "有深厚的因果牽連，業力推動下事情會自然成形",
        },
        "胎": {
            "do": ["耐心等待時機成熟", "播種未來的可能性"],
            "avoid": ["揠苗助長", "否定長期潛力"],
            "career": "潛力型關係，短期未必見效，但長遠有發展空間",
        },
    }

    # 方向在職場情境的深度解讀（雙視角）
    DIRECTION_CAREER_MEANINGS = {
        "栄": {
            "energy_flow": "對方給予你正面能量",
            "as_person1": "你是被提升方，此公司環境有利你的發展",
            "as_person2": "你是提升者，你能帶給對方正面影響",
            "career_tip": "主動爭取，這是你的貴人位",
        },
        "親": {
            "energy_flow": "對方自然親近你",
            "as_person1": "你被對方吸引，合作意願自然高",
            "as_person2": "你是被親近的一方，對方會主動靠過來",
            "career_tip": "順勢發展，不需要刻意經營",
        },
        "衰": {
            "energy_flow": "對方消耗你的能量",
            "as_person1": "你是能量流失方，長期互動需注意消耗",
            "as_person2": "你是療癒者角色，幫助對方排除負面",
            "career_tip": "短期合作可，長期需要評估投入產出比",
        },
        "友": {
            "energy_flow": "你主動給予對方",
            "as_person1": "你是付出方，會自然想照顧對方",
            "as_person2": "你是接受方，對方會為你付出",
            "career_tip": "你的投入會轉化為人脈和信任",
        },
        "安": {
            "energy_flow": "對方給予你穩定感",
            "as_person1": "你從對方身上獲得安定的力量",
            "as_person2": "你是對方的安定錨，提供穩固支持",
            "career_tip": "適合長期穩定的合作關係",
        },
        "壊": {
            "energy_flow": "對方打破你的既有模式",
            "as_person1": "你是被衝擊方，現狀會被打破",
            "as_person2": "你是衝擊者，能幫對方突破僵局",
            "career_tip": "做好心理準備，變動是成長的機會",
        },
        "危": {
            "energy_flow": "對方帶給你風險和挑戰",
            "as_person1": "你處於被動承受風險的位置",
            "as_person2": "你是挑戰的來源，能推動對方成長",
            "career_tip": "謹慎評估，設好停損點再行動",
        },
        "成": {
            "energy_flow": "對方幫助你成就目標",
            "as_person1": "你是借力方，對方能助你成事",
            "as_person2": "你是成就者，能幫對方完成目標",
            "career_tip": "適合在專業領域深度合作",
        },
        "命": {
            "energy_flow": "雙方互為鏡像",
            "as_person1": "你與對方本質相同，互相映照",
            "as_person2": "對方與你本質相同，互相映照",
            "career_tip": "適合做夥伴，但需明確分工",
        },
        "業": {
            "energy_flow": "過去因果的牽引力",
            "as_person1": "你感受到深厚的業力牽連",
            "as_person2": "對方受到你過去累積的影響",
            "career_tip": "順應因果，不強求不抗拒",
        },
        "胎": {
            "energy_flow": "未來可能性的萌發",
            "as_person1": "你感受到未來的潛力和可能",
            "as_person2": "對方在你身上看到未來的希望",
            "career_tip": "長期投資型關係，耐心等待收穫",
        },
    }

    def __init__(self):
        self._mansions_data = None
        self._relations_data = None
        self._elements_data = None
        self._metadata = None
        self._month_mansion_table = None

    @staticmethod
    def _seeded_choice(seed_key: str, pool: list):
        """獨立 seed 的 random.choice，不影響外部 seed 狀態"""
        random.seed(seed_key)
        return random.choice(pool)

    def _load_data(self):
        """載入所有資料"""
        if self._mansions_data is None:
            data_path = Path(__file__).parent.parent / "data" / "sukuyodo_mansions.json"
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._mansions_data = data["mansions"]
                self._relations_data = data["relations"]
                self._elements_data = data.get("elements", {})
                self._metadata = data.get("metadata", {})
                self._month_mansion_table = data.get("month_mansion_table", {})

    @property
    def mansions_data(self) -> list[dict]:
        """載入 27 宿資料"""
        self._load_data()
        return self._mansions_data

    @property
    def relations_data(self) -> dict:
        """載入關係資料"""
        self._load_data()
        return self._relations_data

    @property
    def elements_data(self) -> dict:
        """載入元素資料"""
        self._load_data()
        return self._elements_data

    @property
    def metadata(self) -> dict:
        """載入元資料"""
        self._load_data()
        return self._metadata

    @property
    def month_mansion_table(self) -> dict:
        """載入傍通曆資料"""
        self._load_data()
        return self._month_mansion_table

    def solar_to_lunar(self, solar_date: date) -> tuple[int, int, int, bool]:
        """
        西曆轉農曆

        Args:
            solar_date: 西曆日期

        Returns:
            (年, 月, 日, 是否閏月)

        Raises:
            RuntimeError: 當 lunarcalendar 套件未安裝時
        """
        try:
            from lunarcalendar import Converter, Solar
            solar = Solar(solar_date.year, solar_date.month, solar_date.day)
            lunar = Converter.Solar2Lunar(solar)
            return (lunar.year, lunar.month, lunar.day, lunar.isleap)
        except ImportError:
            raise RuntimeError(
                "lunarcalendar 套件未安裝。"
                "請執行 'pip install lunarcalendar' 安裝。"
                "宿曜道計算需要精確的農曆轉換，不接受近似值。"
            )

    def lunar_to_solar(self, lunar_year: int, lunar_month: int, lunar_day: int) -> Optional[date]:
        """
        農曆轉西曆

        Args:
            lunar_year: 農曆年
            lunar_month: 農曆月 (1-12)
            lunar_day: 農曆日 (1-30)

        Returns:
            對應的西曆日期，若無效則返回 None
        """
        try:
            from lunarcalendar import Converter, Lunar
            lunar = Lunar(lunar_year, lunar_month, lunar_day, isleap=False)
            solar = Converter.Lunar2Solar(lunar)
            return date(solar.year, solar.month, solar.day)
        except (ImportError, ValueError, Exception):
            # 無法轉換（可能是無效日期）
            return None

    def get_solar_dates_for_lunar(
        self,
        lunar_month: int,
        lunar_day: int,
        year_range: int = 20,
        center_year: Optional[int] = None
    ) -> list[dict]:
        """
        將農曆月日轉換為多年的西曆日期

        Args:
            lunar_month: 農曆月 (1-12)
            lunar_day: 農曆日 (1-30)
            year_range: 年份範圍（±N 年）
            center_year: 中心年份（預設為當前年份）

        Returns:
            西曆日期列表
        """
        from datetime import date as dt
        center = center_year or dt.today().year
        start_year = center - year_range
        end_year = center + year_range

        results = []
        for year in range(start_year, end_year + 1):
            solar_date = self.lunar_to_solar(year, lunar_month, lunar_day)
            if solar_date:
                results.append({
                    "lunar_year": year,
                    "solar_date": solar_date.isoformat(),
                    "display": f"{solar_date.year}/{solar_date.month}/{solar_date.day}"
                })

        return results

    def get_mansion_index(self, lunar_month: int, lunar_day: int) -> int:
        """
        根據農曆月日計算本命宿索引

        使用月宿傍通曆：每月初一有固定的起始宿，
        之後每天進一宿（27宿循環）

        Args:
            lunar_month: 農曆月份 (1-12)
            lunar_day: 農曆日期 (1-30)

        Returns:
            本命宿索引 (0-26)
        """
        # 處理閏月：使用對應的月份
        month = lunar_month if 1 <= lunar_month <= 12 else 1

        # 取得該月起始宿
        start = self.MONTH_START_MANSION.get(month, 0)

        # 每天進一宿
        return (start + lunar_day - 1) % 27

    # 全域參考點：農曆2026年正月初一 = 2026-02-17 = 室宿(11)
    # 用於日運連續宿位計算，確保每日恰好前進一宿
    _MANSION_REF_DATE = date(2026, 2, 17)
    _MANSION_REF_INDEX = 11  # 室宿

    def _get_corrected_mansion_index(self, solar_date: date) -> int:
        """日運用的修正後宿位（全域連續遞進，每日+1）

        以農曆2026年正月初一=室宿(11)為參考點，
        根據日數差計算任意日期的宿位。每日恰好前進一宿，
        不受月邊界 gap 或年邊界重置影響。

        本命宿仍使用 get_mansion_index（靜態表）。
        """
        days_diff = (solar_date - self._MANSION_REF_DATE).days
        return (self._MANSION_REF_INDEX + days_diff) % 27

    def get_mansion(self, solar_date: date) -> dict:
        """
        根據西曆生日取得本命宿資料

        Args:
            solar_date: 西曆生日

        Returns:
            包含本命宿完整資料的字典
        """
        lunar_year, lunar_month, lunar_day, is_leap = self.solar_to_lunar(solar_date)
        mansion_index = self.get_mansion_index(lunar_month, lunar_day)
        mansion = self.mansions_data[mansion_index]

        return {
            **mansion,
            "solar_date": solar_date.isoformat(),
            "lunar_date": {
                "year": lunar_year,
                "month": lunar_month,
                "day": lunar_day,
                "is_leap": is_leap,
                "display": f"農曆 {lunar_month} 月 {lunar_day} 日"
            }
        }

    def get_relation_type(self, index1: int, index2: int) -> dict:
        """
        計算兩個宿位之間的關係

        三九秘法：根據兩宿之間的距離判斷關係類型

        Args:
            index1: 第一個宿的索引 (0-26)
            index2: 第二個宿的索引 (0-26)

        Returns:
            關係資料（包含 distance_type 和 direction）
        """
        # 計算有向距離：從 index1 到 index2
        # forward_distance: index1 往前數幾格到 index2
        forward_distance = (index2 - index1) % 27

        # 檢查各種關係
        for rel_key, rel_data in self.relations_data.items():
            distances = rel_data["distances"]
            if forward_distance in distances:
                # 找到匹配的關係，計算距離類型和方向
                distance_type, direction = self._get_distance_info(rel_key, forward_distance)
                return {
                    "type": rel_key,
                    "distance_type": distance_type,
                    "distance_type_name": self._get_distance_type_name(distance_type),
                    "distance_type_reading": self._get_distance_type_reading(distance_type),
                    "direction": direction,
                    **rel_data
                }

        # 預設：未知關係（不應該發生）
        return {
            "type": "unknown",
            "name": "未知",
            "score": 50,
            "description": "無法判斷關係類型",
            "advice": "",
            "distance_type": None,
            "distance_type_name": "",
            "distance_type_reading": "",
            "direction": None
        }

    def _get_distance_info(self, rel_type: str, distance: int) -> tuple[Optional[str], Optional[str]]:
        """
        根據關係類型和距離，取得距離類型和方向

        Args:
            rel_type: 關係類型 (eishin, yusui, etc.)
            distance: 有向距離 (0-26)

        Returns:
            (distance_type, direction) - 如 ("near", "栄")
        """
        type_map = self.DISTANCE_TYPE_MAP.get(rel_type)
        if not type_map:
            return (None, None)

        for dist_type, config in type_map.items():
            if distance in config["distances"]:
                direction = config["direction_map"].get(distance)
                return (dist_type, direction)

        return (None, None)

    def _get_distance_type_name(self, distance_type: Optional[str]) -> str:
        """將距離類型轉換為中文名稱"""
        return {"near": "近距離", "mid": "中距離", "far": "遠距離"}.get(distance_type or "", "")

    def _get_distance_type_reading(self, distance_type: Optional[str]) -> str:
        """將距離類型轉換為假名讀音"""
        return {"near": "きんきょり", "mid": "ちゅうきょり", "far": "えんきょり"}.get(distance_type or "", "")

    def calculate_compatibility(
        self,
        date1: date,
        date2: date
    ) -> dict:
        """
        計算兩人的相性

        Args:
            date1: 第一個人的西曆生日
            date2: 第二個人的西曆生日

        Returns:
            相性分析結果
        """
        mansion1 = self.get_mansion(date1)
        mansion2 = self.get_mansion(date2)

        relation = self.get_relation_type(mansion1["index"], mansion2["index"])

        # 計算距離
        distance = abs(mansion2["index"] - mansion1["index"])
        if distance > 13:
            distance = 27 - distance

        # 計算元素相性加成
        element_bonus = self._calculate_element_bonus(
            mansion1["element"],
            mansion2["element"]
        )

        # 取得元素資料
        elem1_data = self.elements_data.get(mansion1["element"], {})
        elem2_data = self.elements_data.get(mansion2["element"], {})

        # 綜合分數（等級映射 + 元素加成）
        rel_level = self.RELATION_LEVEL_MAP.get(relation["type"], "chukichi")
        final_score = min(100, self.LEVEL_DISPLAY_SCORE[rel_level] + element_bonus)

        # 取得距離化描述（如果有）
        dist_type = relation.get("distance_type")
        by_distance = relation.get("by_distance", {})
        distance_detail = by_distance.get(dist_type, {}) if dist_type else {}

        # 使用距離化描述覆蓋通用描述（如果有的話）
        rel_description = distance_detail.get("description") or relation["description"]
        rel_advice = distance_detail.get("advice") or relation["advice"]
        rel_tips = distance_detail.get("tips") or relation.get("tips", [])
        rel_avoid = distance_detail.get("avoid") or relation.get("avoid", [])

        return {
            "person1": {
                "date": date1.isoformat(),
                "mansion": mansion1["name_jp"],
                "reading": mansion1["reading"],
                "element": mansion1["element"],
                "element_reading": elem1_data.get("reading", ""),
                "element_traits": elem1_data.get("traits", ""),
                "keywords": mansion1["keywords"],
                "index": mansion1["index"]
            },
            "person2": {
                "date": date2.isoformat(),
                "mansion": mansion2["name_jp"],
                "reading": mansion2["reading"],
                "element": mansion2["element"],
                "element_reading": elem2_data.get("reading", ""),
                "element_traits": elem2_data.get("traits", ""),
                "keywords": mansion2["keywords"],
                "index": mansion2["index"]
            },
            "relation": {
                "type": relation["type"],
                "name": relation["name"],
                "name_jp": relation.get("name_jp", relation["name"]),
                "reading": relation.get("reading", ""),
                "description": rel_description,
                "detailed": relation.get("detailed", ""),
                "advice": rel_advice,
                "tips": rel_tips,
                "avoid": rel_avoid,
                "good_for": relation.get("good_for", []),
                "distance_type": relation.get("distance_type"),
                "distance_type_name": relation.get("distance_type_name", ""),
                "distance_type_reading": relation.get("distance_type_reading", ""),
                "direction": relation.get("direction"),
                "love": distance_detail.get("love", ""),
                "career": distance_detail.get("career", ""),
                "roles": self.ROLE_DESCRIPTIONS.get(relation["type"], {})
            },
            "calculation": {
                "distance": distance,
                "formula": f"|{mansion1['index']} - {mansion2['index']}| = {abs(mansion2['index'] - mansion1['index'])} → 距離 {distance}",
                "element_relation": self._get_element_relation(mansion1["element"], mansion2["element"])
            },
            "score": final_score,
            "element_bonus": element_bonus,
            "summary": self._generate_summary(mansion1, mansion2, relation, final_score),
            "classical_analysis": self.get_classical_analysis(mansion1["index"], mansion2["index"]),
            "direction_analysis": self.get_direction_analysis(relation.get("direction", "命")),
            "practical_guidance": self.get_practical_guidance(mansion1["index"], mansion2["index"]),
        }

    def get_classical_analysis(self, index1: int, index2: int) -> dict:
        """取得原典三九秘法分析

        根據 T21n1299《宿曜經》卷下的三九秘法，計算雙方在對方三九法中的位置，
        引用對應經文並提供白話解讀。

        Args:
            index1: person1 的宿曜 index (0-26)
            index2: person2 的宿曜 index (0-26)

        Returns:
            雙向原典分析結果
        """
        def _build_direction_view(source_idx: int, target_idx: int) -> dict:
            distance = (target_idx - source_idx) % 27
            position_name = self.SANKU_POSITION_NAMES[distance]
            group_number = (distance // 9) + 1
            group_info = self.SANKU_GROUP_NAMES[group_number]
            position_text = self.CLASSICAL_POSITION_TEXTS[position_name]

            source_mansion = self.mansions_data[source_idx]
            target_mansion = self.mansions_data[target_idx]
            src = source_mansion["name_jp"]
            tgt = target_mansion["name_jp"]

            # 將白話解讀中的「你/對方/此人」替換為實際宿名
            interp = position_text["interpretation"]
            interp = interp.replace("你們", f"{src}與{tgt}")
            interp = interp.replace("你的", f"{src}的")
            interp = interp.replace("此人", tgt)
            interp = interp.replace("對方", tgt)
            interp = interp.replace("你", src)

            return {
                "source_mansion": src,
                "target_mansion": tgt,
                "distance": distance,
                "group": {
                    "number": group_number,
                    "name": group_info["name"],
                    "reading": group_info["reading"],
                    "head": group_info["head"],
                },
                "position": {
                    "name": position_name,
                    "index_in_group": distance % 9,
                    "full_name": f"{group_info['name']}之{position_name}",
                },
                "sutra": {
                    "text": position_text["sutra"],
                    "ref": position_text["ref"],
                },
                "interpretation": interp,
            }

        return {
            "source": "T21n1299 宿曜經 卷下",
            "person1_to_person2": _build_direction_view(index1, index2),
            "person2_to_person1": _build_direction_view(index2, index1),
        }

    def get_direction_analysis(self, direction: str) -> dict:
        """方向性深度分析：能量流動 + 職場意涵

        Args:
            direction: 方向標籤（栄/衰/安/危/成/壊/友/親/命/業/胎）

        Returns:
            能量流動、雙方視角、職場建議、反方向資訊
        """
        direction_pairs = {
            "栄": "親", "親": "栄",
            "友": "衰", "衰": "友",
            "安": "壊", "壊": "安",
            "危": "成", "成": "危",
            "命": "命", "業": "胎", "胎": "業",
        }

        meaning = self.DIRECTION_CAREER_MEANINGS.get(direction, {})
        inverse = direction_pairs.get(direction, direction)
        inverse_meaning = self.DIRECTION_CAREER_MEANINGS.get(inverse, {})

        return {
            "direction": direction,
            "energy_flow": meaning.get("energy_flow", ""),
            "person1_perspective": meaning.get("as_person1", ""),
            "person2_perspective": meaning.get("as_person2", ""),
            "career_tip": meaning.get("career_tip", ""),
            "inverse_direction": inverse,
            "inverse_meaning": inverse_meaning.get("energy_flow", ""),
        }

    def get_practical_guidance(self, index1: int, index2: int) -> dict:
        """根據三九秘法位置產出現代行動建議

        Args:
            index1: person1 的宿曜 index (0-26)
            index2: person2 的宿曜 index (0-26)

        Returns:
            雙向實用行動建議（宜做/忌做/職場建議）
        """
        def _build_guidance(source_idx: int, target_idx: int) -> dict:
            distance = (target_idx - source_idx) % 27
            position_name = self.SANKU_POSITION_NAMES[distance]
            actions = self.PRACTICAL_ACTION_MAP.get(position_name, {})
            return {
                "position": position_name,
                "do": actions.get("do", []),
                "avoid": actions.get("avoid", []),
                "career_advice": actions.get("career", ""),
            }

        return {
            "person1_to_person2": _build_guidance(index1, index2),
            "person2_to_person1": _build_guidance(index2, index1),
        }

    def _get_element_relation(self, elem1: str, elem2: str) -> str:
        """取得元素關係說明"""
        GENERATING = {
            ("木", "火"): "木生火",
            ("火", "土"): "火生土",
            ("土", "金"): "土生金",
            ("金", "水"): "金生水",
            ("水", "木"): "水生木",
            ("日", "火"): "日生火",
            ("月", "水"): "月生水"
        }

        if elem1 == elem2:
            return f"同元素（{elem1}）+10 分"

        pair = (elem1, elem2)
        reverse_pair = (elem2, elem1)

        if pair in GENERATING:
            return f"{GENERATING[pair]} +5 分"
        if reverse_pair in GENERATING:
            return f"{GENERATING[reverse_pair]} +5 分"

        return "無特殊加成"

    def _calculate_element_bonus(self, elem1: str, elem2: str) -> int:
        """計算元素相性加成"""
        # 五行相生：木生火、火生土、土生金、金生水、水生木
        # 日月特殊：日生火、月生水
        GENERATING = [
            ("木", "火"),
            ("火", "土"),
            ("土", "金"),
            ("金", "水"),
            ("水", "木"),
            ("日", "火"),
            ("月", "水")
        ]

        if elem1 == elem2:
            return 10  # 同元素加分

        pair = (elem1, elem2)
        reverse_pair = (elem2, elem1)

        if pair in GENERATING or reverse_pair in GENERATING:
            return 5  # 相生加分

        return 0

    def _generate_summary(
        self,
        mansion1: dict,
        mansion2: dict,
        relation: dict,
        calculated_score: int
    ) -> str:
        """生成相性總結"""
        rel_name = relation["name"]
        name1 = mansion1["name_jp"]
        name2 = mansion2["name_jp"]

        if calculated_score >= 90:
            level = "非常合拍"
        elif calculated_score >= 75:
            level = "相當不錯"
        elif calculated_score >= 60:
            level = "需要磨合"
        else:
            level = "要多小心"

        return (
            f"{name1}與{name2}的關係是「{rel_name}」，整體評價：{level}。\n"
            f"{relation['description']}\n"
            f"建議：{relation['advice']}"
        )

    def get_all_mansions(self) -> list[dict]:
        """取得所有 27 宿資料"""
        return self.mansions_data

    def get_mansion_lunar_dates(self, mansion_index: int) -> list[dict]:
        """
        取得某個宿位對應的農曆生日範圍

        Args:
            mansion_index: 宿位索引 (0-26)

        Returns:
            對應的農曆月日列表
        """
        results = []

        # 每個月檢查哪些日期會對應到這個宿位
        for month, start_mansion in self.MONTH_START_MANSION.items():
            # 計算這個月的哪一天對應到目標宿位
            # mansion_index = (start_mansion + day - 1) % 27
            # day = (mansion_index - start_mansion + 1) % 27
            # 如果結果 <= 0，加 27

            day = (mansion_index - start_mansion + 1) % 27
            if day <= 0:
                day += 27

            # 農曆每月最多 30 天，只取有效日期
            if 1 <= day <= 30:
                month_names = {
                    1: "正月", 2: "二月", 3: "三月", 4: "四月",
                    5: "五月", 6: "六月", 7: "七月", 8: "八月",
                    9: "九月", 10: "十月", 11: "十一月", 12: "十二月"
                }
                results.append({
                    "lunar_month": month,
                    "lunar_month_name": month_names[month],
                    "lunar_day": day,
                    "display": f"{month_names[month]}{day}日"
                })

        return results

    def find_compatible_mansions(self, solar_date: date) -> dict:
        """
        根據生日找出最佳配對與需要避免的本命宿

        Args:
            solar_date: 西曆生日

        Returns:
            包含栄親、業胎、安壊三類配對宿位的資料
        """
        mansion = self.get_mansion(solar_date)
        user_index = mansion["index"]

        # 各關係類型的距離定義（完整六種關係）
        COMPATIBILITY_TYPES = {
            "mei": {
                "relation": "命",
                "reading": "めい",
                "distances": [0],
                "score": 85,
                "description": "如同鏡子般的存在，彼此理解但優缺點皆被放大",
                "detailed": "命宿之人擁有相同的宿星，等於遇見另一個自己。你們不需要多餘的解釋就能理解對方在想什麼，默契好到讓旁人羨慕。但這面鏡子也會毫不留情地映照出你不想面對的缺點——你身上那些讓自己煩躁的特質，對方也會有。相處的關鍵在於把對方當成自我成長的參照，而不是互相放大弱點。能做到這點的話，這是一段可以走很遠的關係。"
            },
            "gyotai": {
                "relation": "業胎",
                "reading": "ぎょうたい",
                "distances": [9, 18],
                "score": 90,
                "description": "前世因緣深厚，常有似曾相識之感",
                "detailed": "業胎是宿曜道中最神秘的關係。初次見面就覺得對方好像認識了很久，聊起天來完全沒有陌生感。宿曜道認為這是前世累積的緣分在今生延續。這段關係的特點是自然、不費力，你們不需要刻意經營就能維持默契。但也正因如此，容易把對方的存在視為理所當然。記得偶爾表達感謝，讓這份難得的緣分持續發酵。"
            },
            "eishin": {
                "relation": "栄親",
                "reading": "えいしん",
                "distances": [1, 8, 10, 17, 19, 26],
                "score": 95,
                "description": "最適合結婚的對象，互相提攜成長的良緣",
                "detailed": "栄親在宿曜道中被視為最理想的結合。你們的能量場互相加持，一方有光芒時另一方也會跟著閃耀。不是那種激烈的來電，而是越相處越覺得「跟這個人在一起什麼都會變好」的踏實感。在職場上你們是天然的好搭檔，在感情中是能共同成長的伴侶。維持這段關係的秘訣是讓彼此都有發光的舞台，不要只有一方在付出。"
            },
            "yusui": {
                "relation": "友衰",
                "reading": "ゆうすい",
                "distances": [2, 7, 11, 16, 20, 25],
                "score": 70,
                "description": "相處舒適自在，但需注意不要一起停滯不前",
                "detailed": "友衰的友方會覺得跟對方在一起很舒服，衰方則可能不自覺地消耗精力。這種關係初期很迷人——你們聊得來、價值觀接近、在一起總是很開心。但長期下來，如果沒有刻意地互相激勵，容易變成一起追劇一起抱怨但都不行動的狀態。經營這段關係的方法是設定共同目標，用正向的壓力推著彼此前進。"
            },
            "ankai": {
                "relation": "安壊",
                "reading": "あんかい",
                "distances": [3, 6, 12, 15, 21, 24],
                "score": 50,
                "description": "強烈吸引力但權力不對等，需謹慎經營",
                "detailed": "安壊是宿曜道中最有戲劇性的關係。安方會被壊方強烈吸引，壊方則不自覺地對安方施加壓力。這種不對等的能量讓關係充滿張力和刺激感。如果雙方都能意識到這種動態並刻意平衡，反而能碰撞出驚人的火花。這段關係需要比其他關係更用心地維護——建立明確的界線、養成坦誠溝通的習慣、在張力出現時主動踩煞車。用對方法，安壊關係能成為推動彼此成長的強大力量。"
            },
            "kisei": {
                "relation": "危成",
                "reading": "きせい",
                "distances": [4, 5, 13, 14, 22, 23],
                "score": 75,
                "description": "互補的關係，需要磨合但能促進彼此成長",
                "detailed": "危成是一段「不磨合就無法前進，但磨合之後特別堅固」的關係。成方帶來穩定和規劃能力，危方帶來突破和冒險精神。初期你們可能對對方的做事方式感到困惑甚至不耐煩，但這種差異正是讓你們各自補足盲點的機會。經歷過幾次衝突和理解之後，你們會變成一個攻守兼備的組合。耐心是這段關係的必要投資。"
            }
        }

        result = {
            "your_mansion": {
                "name_jp": mansion["name_jp"],
                "name_zh": mansion["name_zh"],
                "reading": mansion["reading"],
                "index": user_index,
                "element": mansion["element"],
                "lunar_date": mansion["lunar_date"]
            }
        }

        # 計算各類型的配對宿位
        for key, config in COMPATIBILITY_TYPES.items():
            indices = set()
            for d in config["distances"]:
                indices.add((user_index + d) % 27)
                indices.add((user_index - d + 27) % 27)

            # 取得這些宿位的詳細資料
            mansions = []
            for idx in sorted(indices):
                m = self.mansions_data[idx]
                elem_data = self.elements_data.get(m["element"], {})
                lunar_dates = self.get_mansion_lunar_dates(idx)

                # 為每個農曆日期加上西曆對照
                for ld in lunar_dates:
                    ld["solar_dates"] = self.get_solar_dates_for_lunar(
                        ld["lunar_month"],
                        ld["lunar_day"],
                        year_range=25,
                        center_year=solar_date.year
                    )

                mansions.append({
                    "name_jp": m["name_jp"],
                    "name_zh": m["name_zh"],
                    "reading": m["reading"],
                    "index": idx,
                    "element": m["element"],
                    "element_reading": elem_data.get("reading", ""),
                    "keywords": m["keywords"],
                    "personality": m["personality"],
                    "lunar_dates": lunar_dates
                })

            result[key] = {
                "relation": config["relation"],
                "reading": config["reading"],
                "score": config["score"],
                "description": config["description"],
                "detailed": config.get("detailed", ""),
                "mansions": mansions
            }

        return result

    # ==================== 運勢計算 ====================

    def _load_fortune_data(self):
        """載入運勢資料"""
        if not hasattr(self, '_fortune_data') or self._fortune_data is None:
            data_path = Path(__file__).parent.parent / "data" / "sukuyodo_fortune.json"
            with open(data_path, "r", encoding="utf-8") as f:
                self._fortune_data = json.load(f)
        return self._fortune_data

    def _calc_fortune_element_relation(self, elem1: str, elem2: str) -> tuple[str, int]:
        """
        計算運勢用的元素關係

        Returns:
            (關係類型, 加成分數)
        """
        fortune_data = self._load_fortune_data()

        if elem1 == elem2:
            return ("same", fortune_data["element_relations"]["same"]["bonus"])

        # 相生（有方向性）：環境元素(elem2)生用戶元素(elem1) → 有利
        for pair in fortune_data["generating_pairs"]:
            if elem2 == pair[0] and elem1 == pair[1]:
                return ("generating", fortune_data["element_relations"]["generating"]["bonus"])

        # 相洩（有方向性）：用戶元素(elem1)生環境元素(elem2) → 能量被消耗
        for pair in fortune_data["generating_pairs"]:
            if elem1 == pair[0] and elem2 == pair[1]:
                return ("weakening", fortune_data["element_relations"]["weakening"]["bonus"])

        # 相剋（維持雙向）
        for pair in fortune_data["conflicting_pairs"]:
            if (elem1 == pair[0] and elem2 == pair[1]) or \
               (elem1 == pair[1] and elem2 == pair[0]):
                return ("conflicting", fortune_data["element_relations"]["conflicting"]["bonus"])

        # 日/月特殊處理：使用 special_elements 資料
        # 日生火、月生水，需區分方向性
        special = fortune_data.get("special_elements", {})
        for special_elem in ["日", "月"]:
            if elem1 == special_elem or elem2 == special_elem:
                other = elem2 if elem1 == special_elem else elem1
                spec = special.get(special_elem, {})
                if other in spec.get("generates", []):
                    if elem1 == special_elem:
                        # 用戶元素是日/月，生出環境元素 → 能量被消耗
                        return ("weakening", fortune_data["element_relations"]["weakening"]["bonus"])
                    else:
                        # 環境元素是日/月，生出用戶元素 → 用戶被生
                        return ("generating", fortune_data["element_relations"]["generating"]["bonus"])
                return ("neutral", fortune_data["element_relations"]["neutral"]["bonus"])

        return ("neutral", fortune_data["element_relations"]["neutral"]["bonus"])

    # 三九秘法：關係類型對應的基礎分數範圍
    # key 使用羅馬拼音，與 relations 資料一致
    RELATION_SCORE_RANGES = {
        "eishin": (85, 95),   # 栄親 - 大吉 - 最佳配對日
        "gyotai": (78, 88),   # 業胎 - 吉 - 前世因緣日
        "mei": (72, 82),      # 命 - 中吉 - 同宿日
        "yusui": (60, 72),    # 友衰 - 中吉偏低 - 舒適但易懈怠
        "kisei": (45, 58),    # 危成 - 小吉 - 需謹慎
        "ankai": (32, 48),    # 安壊 - 凶 - 權力不對等日
    }

    # === 等級優先制常數（原典依據） ===

    # 日運勢五等級（三九秘法）：index 0 = 最佳, index 4 = 最差
    FORTUNE_LEVELS = ["daikichi", "kichi", "chukichi", "shokyo", "kyo"]

    # 關係類型 → 等級映射
    RELATION_LEVEL_MAP = {
        "eishin": "daikichi",  # 栄親 → 大吉
        "gyotai": "kichi",     # 業胎 → 吉
        "mei": "kichi",        # 命 → 吉
        "yusui": "chukichi",   # 友衰 → 中吉
        "kisei": "shokyo",     # 危成 → 小凶
        "ankai": "kyo",        # 安壊 → 凶
    }

    # 凌犯翻轉（對稱鏡射）
    RYOUHAN_LEVEL_FLIP = {
        "daikichi": "kyo",
        "kichi": "shokyo",
        "chukichi": "chukichi",  # 中吉不變
        "shokyo": "kichi",
        "kyo": "daikichi",
    }

    # 等級 → 顯示分數（UI 進度條用）
    LEVEL_DISPLAY_SCORE = {
        "daikichi": 90,
        "kichi": 75,
        "chukichi": 60,
        "shokyo": 45,
        "kyo": 35,
    }

    # 年運月趨勢用映射（宏觀概覽，差距較日運勢小）
    # 注意：不得超過日運勢的 LEVEL_DISPLAY_SCORE，月趨勢是宏觀參考
    YEARLY_TREND_SCORE = {
        "daikichi": 80,
        "kichi": 70,
        "chukichi": 60,
        "shokyo": 50,
        "kyo": 40,
    }

    # 等級 → 中日文名稱
    LEVEL_NAMES = {
        "daikichi": {"zh": "大吉", "ja": "大吉", "reading": "だいきち"},
        "kichi": {"zh": "吉", "ja": "吉", "reading": "きち"},
        "chukichi": {"zh": "中吉", "ja": "中吉", "reading": "ちゅうきち"},
        "shokyo": {"zh": "小凶", "ja": "小凶", "reading": "しょうきょう"},
        "kyo": {"zh": "凶", "ja": "凶", "reading": "きょう"},
    }

    # 等級 → effective_interpretation
    LEVEL_INTERPRETATION = {
        "daikichi": "excellent",
        "kichi": "good",
        "chukichi": "neutral",
        "shokyo": "challenging",
        "kyo": "caution",
    }

    # 等級 → advice key
    LEVEL_ADVICE_KEY = {
        "daikichi": "excellent",
        "kichi": "good",
        "chukichi": "neutral",
        "shokyo": "caution",
        "kyo": "challenging",
    }

    # 等級 → 描述選擇 key
    LEVEL_DESC_KEY = {
        "daikichi": "excellent",
        "kichi": "good",
        "chukichi": "fair",
        "shokyo": "caution",
        "kyo": "warning",
    }

    # 凌犯中等級 → 描述選擇 key
    RYOUHAN_DESC_KEY = {
        "daikichi": "high_reversal",
        "kichi": "high_reversal",
        "chukichi": "mid_reversal",
        "shokyo": "low_reversal",
        "kyo": "low_reversal",
    }

    # 九曜四等級 → 顯示分數（獨立體系）
    KUYOU_LEVEL_MAP = {
        "大吉": 85,
        "半吉": 65,
        "末吉": 50,
        "大凶": 35,
    }

    # 每日運勢專用描述（區別於雙人配對描述）
    DAILY_FORTUNE_DESCRIPTIONS = {
        "eishin": [
            "大吉之日，天時地利人和，貴人運旺盛。適合積極行動、開展新事物、重要會議或面試。把握機會，事半功倍。",
            "今天的能量場對你非常有利，無論是提案、談判還是開啟新合作，成功率都比平時高出許多。主動出擊會有好結果。",
            "各方面條件都在向你靠攏的一天。人際關係中容易遇到幫助你的人，工作上的努力也會得到相應的回報。放手去做吧。",
            "今天如果有需要別人幫忙的事情，開口就對了，對方答應的機率很高。社交場合也容易認識到未來能長期合作的對象。",
            "你今天的判斷力和行動力都在高峰，拿來處理懸而未決的重要事項最合適。拖越久越難處理的事，趁今天一口氣搞定。"
        ],
        "gyotai": [
            "吉日，直覺特別敏銳，靈感泉湧。適合創意發想、深度思考、學習新知。內心的聲音值得傾聽。",
            "今天你的感知力比平時更強，可能會突然想通一件困擾已久的事情。適合做需要創造力的工作，或者學習一項新技能。",
            "與過去的經驗產生共鳴的一天。你可能會從舊回憶或過往的學習中找到解決當前問題的線索。靜下心來感受，答案就在那裡。",
            "今天特別適合做筆記或寫東西，腦中的想法會比平時更容易組織成清晰的脈絡。如果你有寫作、企劃或設計的工作，效率會不錯。",
            "你對周遭人事物的觀察力今天特別銳利，能察覺到平常忽略的訊號。這種敏感度拿來分析問題或理解他人的立場都很管用。"
        ],
        "mei": [
            "中吉，能量回歸平穩，與自我對話的好日子。適合自我反省、整理思緒、規劃未來。靜心內觀，收穫更多。",
            "今天適合面對真實的自己。不管是檢視最近的生活狀態，還是重新思考未來的方向，你會比平時更清楚自己要什麼。",
            "內在能量充沛的一天，適合做決定和確認方向。你對自己的了解會特別深刻，趁這個時候把模糊的想法整理清楚。",
            "今天的你特別能聽見自己內心的真實想法。那些平時被工作和雜事蓋住的聲音，今天會浮上來，認真聽一聽對你有好處。",
            "很適合獨處充電的一天。泡杯茶、散個步、或找一個安靜的角落想想最近的生活，你會發現一些之前沒注意到的盲點。"
        ],
        "yusui": [
            "平穩之日，一切按部就班即可。適合處理例行事務、維持現狀。不宜冒進或做重大改變，穩中求進為佳。",
            "今天的節奏偏慢，不適合趕進度或做激進的決策。把手邊的事情處理好，整理一下桌面和待辦清單，會讓你感到踏實。",
            "能量處於休養狀態的一天。不需要刻意追求突破，做好份內的事、維持穩定的生活節奏就是最好的安排。",
            "今天的步調就像週末下午，不急不趕剛剛好。拿來回覆拖欠的訊息、整理檔案、更新行事曆這類零碎事務很合適。",
            "如果你最近一直在衝刺，今天正好可以喘口氣。做一些不太需要動腦的事情，讓自己的電池充一充，明天再繼續。"
        ],
        "kisei": [
            "需謹慎之日，行事宜三思而後行。注意細節、避免粗心大意。遇事多請教他人意見，可化險為夷。",
            "今天容易在小地方出差錯，出門前多檢查一次、重要文件多看幾遍。如果遇到猶豫的事情，聽聽身邊人的看法。",
            "外在環境有些不穩定的跡象，做任何決定前多留一點緩衝時間。避免在情緒激動時做出承諾或回應。",
            "今天的溝通上容易產生誤會，講話和寫訊息都多確認一次再送出。特別是跟上司或客戶的對話，措辭要比平時更謹慎。",
            "如果今天有重要的東西要交出去，提前完成比卡在最後一刻好。這種日子趕 deadline 特別容易出包，留多一點餘裕給自己。"
        ],
        "ankai": [
            "挑戰之日，外在環境較為不順。重大決定建議延後，保持低調、韜光養晦。靜待時機，不宜強求。",
            "今天可能會遇到意料之外的阻礙或延誤，不要和它硬碰硬。暫時退一步，把精力放在不需要外界配合的事情上。",
            "運勢處於低點的一天，但不代表什麼都不能做。處理簡單的日常事務沒問題，只是要避開涉及大筆金錢或重要合約的事項。",
            "今天不太適合發起請求或爭取什麼，容易碰壁。做好自己的本分就好，需要交涉的事情留到明後天再處理會順利很多。",
            "如果今天遇到不順心的事，提醒自己這只是暫時的低潮。不要因為一時的挫折就做出衝動的決定，過幾天回頭看會慶幸自己忍住了。"
        ]
    }

    # 每日運勢關係名稱（更適合每日運勢語境）
    DAILY_FORTUNE_RELATION_NAMES = {
        "eishin": "大吉",
        "gyotai": "吉",
        "mei": "中吉",
        "yusui": "平",
        "kisei": "小凶",
        "ankai": "凶"
    }

    # 每日運勢各項描述（根據分數區間 × 三九秘法關係）
    # 5 個區間：excellent(85+), good(70-84), fair(55-69), caution(40-54), warning(<40)
    DAILY_CATEGORY_DESCRIPTIONS = {
        "career": {
            "excellent": [
                "今天事業運勢極佳。三九秘法顯示你的本命宿與當日宿形成強力共振，工作上的企劃、提案、面試都容易被接受。把握這天推動關鍵事項。",
                "職場上你今天的存在感特別強，上司和同事對你的表現會留下深刻印象。適合爭取曝光機會、主導會議、或提出新的工作方向。",
                "你的判斷力和執行力今天都在高峰。需要做重大工作決策的話，今天的直覺值得信任。團隊合作也特別順暢。",
            ],
            "good": [
                "事業運穩中向好。宿曜關係顯示今天適合推進已在進行中的專案，執行力不錯，處理複雜任務的效率比平時高。",
                "工作上的溝通順暢，跟客戶或同事的互動容易達成共識。適合安排需要協調多方的工作，或處理需要細心的行政事務。",
                "今天在職場上不太會踩雷，按照計畫進行就好。如果有想爭取的加薪或升遷機會，可以開始做準備。",
            ],
            "fair": [
                "事業運平穩，沒有特別的助力也沒有阻礙。按部就班處理日常工作即可，不需要刻意求表現。",
                "今天適合做不需要太多創意的例行工作。整理檔案、回覆郵件、更新報告這類事務做起來很順手。",
                "工作上遇到的問題不大不小，花點時間就能解決。不用急著做大決定，觀望一下再行動比較穩妥。",
            ],
            "caution": [
                "事業運需要留意。宿曜關係提示今天職場上容易遇到小摩擦，與上司或客戶的互動要比平時更謹慎。確認再確認是今天的工作原則。",
                "今天不太適合提出新企劃或爭取新專案，時機不對。把精力放在完善手邊已有的工作上比較有成果。",
                "工作中的細節今天要特別注意，數字、日期、名稱這些容易出錯的地方多檢查幾遍。避免在壓力下做倉促決定。",
            ],
            "warning": [
                "事業運低迷，宿曜關係顯示外在環境不利於積極行動。今天做好本分就好，不要主動挑起衝突或爭取什麼。需要談判或簽約的事延後處理。",
                "職場上可能遇到意料外的阻礙或延遲，保持冷靜不要焦躁。這只是暫時的能量低谷，硬撐著做大事反而容易出差錯。",
            ]
        },
        "love": {
            "excellent": [
                "今天感情運極佳。宿曜能量有利於人際連結，不管是伴侶間的交流還是新的邂逅，都特別容易產生深度共鳴。適合表白、約會、深入對話。",
                "你今天散發的氣場特別有魅力，身邊的人會不自覺地被你吸引。有伴侶的人適合安排特別的約會，單身者出門社交可能有驚喜。",
                "感情上的溝通今天特別順暢，平時說不出口的話今天說出來效果特別好。適合處理關係中懸而未決的問題。",
            ],
            "good": [
                "感情運不錯。人際互動中容易感受到溫暖和善意。與伴侶的日常相處會特別和諧，小確幸的一天。",
                "今天適合和重要的人一起做些日常但舒服的事情：一起吃飯、散步、或只是聊天。不需要大陣仗，自然的互動就很美好。",
                "社交場合中你今天的親和力不錯，別人願意主動跟你分享或聊天。如果想拓展人際圈，今天跨出第一步會比較自在。",
            ],
            "fair": [
                "感情運平穩，沒有波瀾也沒有驚喜。與身邊人的相處維持常態，不需要刻意經營也不會出問題。",
                "今天的人際互動中規中矩。如果有什麼想對重要的人說的話，找個輕鬆的時機自然地表達就好。",
                "感情方面保持現狀即可。不需要刻意製造浪漫，做好日常的關心和陪伴就是最好的。",
            ],
            "caution": [
                "感情運需留意。今天容易因為小事和身邊人產生摩擦，特別是語氣和措辭上。說話前先想一想，很多衝突其實只是溝通方式的問題。",
                "人際關係中今天可能會出現誤解，不要急著解釋或反駁。給對方和自己一點空間冷靜，過一陣子自然會理清。",
                "今天不太適合討論敏感話題或做關係中的重大決定。如果覺得情緒上來了，先離開現場冷靜再回來處理。",
            ],
            "warning": [
                "感情運低落。宿曜能量提示今天容易在人際關係中踩雷，避免翻舊帳或做出衝動的承諾。獨處比強迫自己社交更好。",
                "今天如果和伴侶或朋友發生不愉快，忍一忍，不要在氣頭上說出讓自己後悔的話。低潮會過去，但傷人的話收不回來。",
            ]
        },
        "health": {
            "excellent": [
                "今天健康運極佳。身體能量充沛，精力旺盛。適合安排高強度的運動或戶外活動，體能表現會比平時好。",
                "身心狀態都在最佳水準。如果平時有在運動，今天可以試著挑戰一下自己的極限。睡眠品質也預計會不錯。",
                "你的免疫力和恢復力今天都很好。如果最近有什麼小毛病，今天可能會感覺明顯好轉。適合安排健康檢查。",
            ],
            "good": [
                "健康運不錯。身體沒什麼大問題，精神狀態也清醒。做一些輕鬆的運動（散步、瑜伽、伸展）會讓你感覺更好。",
                "今天的體能和精神都在及格線以上。維持正常的作息就好，如果天氣不錯，出門走走對身心都有幫助。",
                "身體狀況穩定。注意補充水分和均衡飲食，讓好的狀態延續下去。今天開始培養新的健康習慣是個好時機。",
            ],
            "fair": [
                "健康運普通。身體沒什麼特別需要擔心的，維持日常的保健習慣就好。注意不要久坐，定時起來活動一下。",
                "體能和精神都在一般水準，不會覺得特別有活力也不會太疲倦。按照平時的作息過就好。",
                "健康面保持現狀。如果之前有在做的運動或保健計畫，今天繼續執行就好，不需要加量也不需要減量。",
            ],
            "caution": [
                "健康運需注意。宿曜能量提示今天身體比較容易感到疲勞，不要硬撐。如果覺得累就休息，不要逞強。",
                "今天要特別注意肩頸和腰背，長時間維持同一個姿勢容易造成不適。每隔一小時起來活動一下筋骨。",
                "精神上可能會有些低落或焦慮，這是暫時的能量波動。做幾次深呼吸，或聽一些讓自己放鬆的音樂。",
            ],
            "warning": [
                "健康運低落，今天最需要留意的就是身體訊號。覺得不舒服就不要硬撐，該看醫生就去看。避免高強度運動和熬夜。",
                "身體處於需要休養的狀態。今天最好的健康策略是早睡、多喝水、減少刺激性食物。給身體一個恢復的機會。",
            ]
        },
        "wealth": {
            "excellent": [
                "今天財運極佳。宿曜關係顯示金錢方面的決策特別準確，適合處理投資、簽約、談薪資等與錢相關的重要事項。",
                "財運旺盛的一天。如果有想購入的資產或想投資的項目，今天的判斷力值得信賴。意外之財也有可能出現。",
                "金錢運上你今天的直覺特別準，看到好的機會不要猶豫太久。不過也不是叫你衝動消費，有理性分析支撐的決定才值得行動。",
            ],
            "good": [
                "財運不錯。日常的收支管理今天做起來特別順手，可能會發現省錢的好方法或意外的折扣。適合整理帳務。",
                "金錢方面今天不太會踩雷。正常的消費沒問題，如果有在比價的東西，今天做決定通常不會後悔。",
                "財運穩中向好。今天適合規劃理財方向或檢視目前的收支平衡。做一些未來會讓你的錢包感謝你的準備工作。",
            ],
            "fair": [
                "財運平穩，不會有大的進帳也不會有意外支出。維持平時的消費習慣即可，不需要刻意節省也不要衝動消費。",
                "金錢方面中規中矩。該花的花、該省的省，不需要特別擔心。大額支出的話可以再觀望一下。",
                "財運沒有特別的波動。處理日常帳單、繳費這類事務沒問題，但不建議今天做重大的財務決策。",
            ],
            "caution": [
                "財運需留意。今天容易出現預期外的支出，出門前確認一下錢包和手機的付款額度。避免借錢給別人或做財務擔保。",
                "金錢方面今天要保守一些。看到打折促銷先不要衝動，回家想一想真的需要再買。投資決策也建議延後。",
                "今天不太適合談錢。無論是談薪資、議價還是追討欠款，效果都不會太好。等個幾天再處理，條件會更有利。",
            ],
            "warning": [
                "財運低迷。今天盡量減少不必要的支出，避免涉及大額金錢的決定。簽合約、投資、借貸這些事情延後處理最安全。",
                "金錢方面要格外小心，容易因為疏忽而造成損失。出門帶的現金和卡片夠用就好，不要帶太多。線上付款也多確認金額。",
            ]
        }
    }

    # 凌犯期間專用描述（吉凶逆轉時使用）
    # score >= 70: high_reversal（表吉實險）
    # 50-69: mid_reversal（局勢不明）
    # < 50: low_reversal（表凶有轉機）
    RYOUHAN_CATEGORY_DESCRIPTIONS = {
        "career": {
            "high_reversal": [
                {"zh": "表面上工作順利，但凌犯期間中的順遂往往藏著陷阱。今天做的決定可能在幾天後出現意想不到的後果，重要決策建議延後。",
                 "ja": "表面上は仕事が順調だが、凌犯期間中の順調さには罠が潜む。今日の決定が数日後に思わぬ結果を招く可能性あり。重要な決断は延期を推奨。"},
                {"zh": "看起來是推進事業的好時機，但凌犯的影響讓判斷力打折扣。尤其是涉及人事異動或合約簽署，等凌犯結束再處理更穩妥。",
                 "ja": "事業を進める好機に見えるが、凌犯の影響で判断力が鈍る。人事異動や契約締結は凌犯終了後に処理するのが堅実。"},
                {"zh": "職場氣氛不錯，但別被表象迷惑。凌犯期間的「好機會」常常是包裝過的風險，多觀察幾天再行動。",
                 "ja": "職場の雰囲気は良好だが、表面に惑わされないように。凌犯期間の「好機」は往々にしてリスクを孕む。数日様子を見てから行動すべし。"},
            ],
            "mid_reversal": [
                {"zh": "工作上的局勢不太明朗，凌犯期間增添了變數。維持現有進度就好，不要主動發起新計畫或改變方向。",
                 "ja": "仕事の局面が不透明で、凌犯期間が変数を加える。現状維持に努め、新規計画や方針転換は控えるべし。"},
                {"zh": "凌犯的影響讓工作節奏變得不穩定，同事間容易產生誤解。今天的溝通多確認一次，避免假設對方理解你的意思。",
                 "ja": "凌犯の影響で仕事のリズムが不安定に。同僚間で誤解が生じやすい。今日のコミュニケーションは確認を怠らないこと。"},
            ],
            "low_reversal": [
                {"zh": "雖然整體運勢偏低，但凌犯的逆轉效應反而提供了喘息的空間。原本預期的阻礙可能沒那麼嚴重，靜待觀察。",
                 "ja": "全体の運勢は低調だが、凌犯の逆転効果がかえって猶予を与える。予想された障害はそれほど深刻でない可能性あり。静観を。"},
                {"zh": "凌犯期間表凶反吉，看似困難的工作處境可能暗藏轉機。不要急著放棄，先把手邊的事情做好。",
                 "ja": "凌犯期間は表凶反吉。困難に見える仕事の状況に転機が潜む可能性あり。諦めず手元の仕事をこなすべし。"},
            ]
        },
        "love": {
            "high_reversal": [
                {"zh": "感情方面看起來甜蜜，但凌犯期間容易產生認知偏差。今天的浪漫承諾和衝動告白，過幾天可能會覺得太冒進。",
                 "ja": "恋愛面は甘美に見えるが、凌犯期間は認知の偏りが生じやすい。今日のロマンチックな約束や衝動的な告白は数日後に後悔する恐れあり。"},
                {"zh": "跟伴侶的互動表面和諧，但凌犯的暗流可能讓小問題在之後放大。有什麼心裡的話想說，等凌犯過後再談比較好。",
                 "ja": "パートナーとの関係は表面上穏やかだが、凌犯の暗流が小さな問題を後で拡大させる恐れあり。本音の話し合いは凌犯後に。"},
            ],
            "mid_reversal": [
                {"zh": "感情上的判斷力受凌犯影響而模糊。對方的言行可能不是你理解的那個意思，不要過度解讀，也不要在今天做關係的重大決定。",
                 "ja": "恋愛の判断力が凌犯の影響でぼやける。相手の言動を深読みせず、今日は関係の重大な決断を避けるべし。"},
                {"zh": "凌犯期間的感情互動容易失準。今天適合維持日常相處就好，不適合深入討論關係問題或未來規劃。",
                 "ja": "凌犯期間の感情的やり取りはズレが生じやすい。日常の付き合いに留め、関係の深い話し合いや将来の計画は控えるべし。"},
            ],
            "low_reversal": [
                {"zh": "感情運勢雖低，但凌犯的逆轉可能帶來意外的溫暖。之前冷淡的關係有回溫的跡象，把握但不強求。",
                 "ja": "恋愛運は低調だが、凌犯の逆転が意外な温もりをもたらす可能性あり。冷えた関係に回復の兆し。掴みつつも無理はしないこと。"},
                {"zh": "看起來不太順利的感情狀態，在凌犯影響下反而有緩和的可能。保持平常心，不要因為暫時的低潮就做出分手的決定。",
                 "ja": "不調に見える恋愛状態だが、凌犯の影響でかえって緩和される可能性あり。平常心を保ち、一時の低迷で別れを決断しないこと。"},
            ]
        },
        "health": {
            "high_reversal": [
                {"zh": "身體感覺還行，但凌犯期間容易忽視身體的微弱警訊。今天不要做太激烈的運動，也不要因為「覺得沒事」就忽略不舒服。",
                 "ja": "体調は悪くないが、凌犯期間は体の微かな警告を見落としやすい。激しい運動は避け、不調を感じたら軽視しないこと。"},
                {"zh": "凌犯期間身體的感知會有偏差，自覺良好不代表真的沒問題。飲食清淡一些，早點休息，讓身體有恢復的餘裕。",
                 "ja": "凌犯期間は体の感覚にズレが生じ、自覚が良好でも実際は違う場合がある。食事は控えめに、早めの休息で体に回復の余裕を。"},
            ],
            "mid_reversal": [
                {"zh": "健康狀態受凌犯影響而不穩定，注意力和反應速度都會下降。開車、操作機具要比平常更小心。",
                 "ja": "健康状態が凌犯の影響で不安定に。注意力や反応速度が低下するため、運転や機械操作には普段以上の注意を。"},
                {"zh": "凌犯期間的健康運勢搖擺不定。不要臨時改變飲食習慣或運動計畫，維持穩定的作息就是最好的養生。",
                 "ja": "凌犯期間の健康運は揺れ動く。食習慣や運動計画の急な変更は避け、安定した生活リズムの維持が最良の養生。"},
            ],
            "low_reversal": [
                {"zh": "身體狀況雖然偏弱，但凌犯的逆轉效應可能讓慢性不適有所緩解。這是調養身體的好時機，順勢而為。",
                 "ja": "体調は弱めだが、凌犯の逆転効果で慢性的な不調が緩和される可能性あり。体を養う好機、流れに任せるべし。"},
                {"zh": "健康運勢低檔，但凌犯期間的「表凶實緩」效應讓惡化的風險降低。靜養休息、避免過勞即可。",
                 "ja": "健康運は低調だが、凌犯期間の「表凶実緩」効果で悪化のリスクは軽減。静養・休息に努め、過労を避けるべし。"},
            ]
        },
        "wealth": {
            "high_reversal": [
                {"zh": "財運看起來不錯，但凌犯期間的「好運」經常是錢來得快去得也快。今天收到的獲利或好消息，可能有後續的隱藏成本。",
                 "ja": "金運は良さそうに見えるが、凌犯期間の「好運」は入りも出も速い。今日の利益や良い知らせには隠れたコストがある可能性。"},
                {"zh": "表面的財運順遂在凌犯影響下需要打折看待。投資、借貸、大額消費都建議暫緩，等凌犯結束後再評估。",
                 "ja": "表面的な金運の順調さは凌犯の影響で割り引いて見るべき。投資・借入・大きな支出は凌犯終了後に再評価を。"},
            ],
            "mid_reversal": [
                {"zh": "財務狀況在凌犯期間變得不透明，收支可能出現預期外的波動。今天適合整理帳目，不適合做財務決策。",
                 "ja": "凌犯期間中は財務状況が不透明になり、収支に予想外の変動が生じる可能性。帳簿の整理には適すが、財務的な決断には不向き。"},
                {"zh": "凌犯的影響讓金錢判斷力下降。看起來划算的東西可能有你沒注意到的問題，購物前多比較幾家。",
                 "ja": "凌犯の影響で金銭面の判断力が低下。お得に見えるものに気づかない問題が潜む可能性あり。購入前に複数比較すべし。"},
            ],
            "low_reversal": [
                {"zh": "財運偏弱，但凌犯的逆轉讓預期的損失可能不會發生。之前擔心的財務問題有緩解的跡象，不必過度焦慮。",
                 "ja": "金運は弱めだが、凌犯の逆転で予想された損失は回避できる可能性。心配していた財務問題に緩和の兆しあり。過度な不安は不要。"},
                {"zh": "表面的財運低迷在凌犯效應下可能只是虛驚一場。守住現有資產，不要恐慌性地做出調整。",
                 "ja": "表面的な金運の低迷は凌犯効果で杞憂に終わる可能性。現有資産を守り、パニック的な調整は控えるべし。"},
            ]
        }
    }

    # 甘露日/金剛峯日/羅刹日（宿曜經卷五）
    # key: (jp_weekday, day_mansion_index) → special_day_type
    # jp_weekday: 0=日, 1=月, 2=火, 3=水, 4=木, 5=金, 6=土
    SPECIAL_DAY_MAP = {
        # 甘露日（大吉）
        (0, 26): "kanro",   # 日曜 + 軫宿
        (1, 17): "kanro",   # 月曜 + 畢宿
        (2, 5): "kanro",    # 火曜 + 尾宿
        (3, 22): "kanro",   # 水曜 + 柳宿
        (4, 21): "kanro",   # 木曜 + 鬼宿
        (5, 3): "kanro",    # 金曜 + 房宿
        (6, 23): "kanro",   # 土曜 + 星宿
        # 金剛峯日（吉）
        (0, 5): "kongou",   # 日曜 + 尾宿
        (1, 4): "kongou",   # 月曜 + 心宿（大正藏底本，明版作女宿）
        (2, 12): "kongou",  # 火曜 + 壁宿
        (3, 16): "kongou",  # 水曜 + 昴宿
        (4, 20): "kongou",  # 木曜 + 井宿
        (5, 24): "kongou",  # 金曜 + 張宿
        (6, 1): "kongou",   # 土曜 + 亢宿
        # 羅刹日（凶）
        (0, 15): "rasetsu",  # 日曜 + 胃宿
        (1, 21): "rasetsu",  # 月曜 + 鬼宿
        (2, 25): "rasetsu",  # 火曜 + 翼宿
        (3, 19): "rasetsu",  # 水曜 + 参宿
        (4, 2): "rasetsu",   # 木曜 + 氐宿
        (5, 13): "rasetsu",  # 金曜 + 奎宿
        (6, 22): "rasetsu",  # 土曜 + 柳宿
    }

    SPECIAL_DAY_INFO = {
        "kanro": {
            "name": "甘露日",
            "reading": "かんろび",
            "level": "大吉",
            "description": "宿曜經記載的大吉日。七曜與當日宿的能量完全調和，萬事順遂。適合護摩供、灌頂傳法、開眼供養、入佛開光、結婚、簽約、搬遷、開業等重要行動。",
            "description_classic": "甘露者，天降甘美之法雨也。七曜與宿値相應調和，萬事成就，百福莊嚴。此日行事，如沐法雨，所願皆遂。",
            "description_ja": "甘露日は七曜と当日の宿が最も調和する大吉日なり。「甘露」とは仏教における不死の霊薬（アムリタ）を指し、天の恵みが降り注ぐ日とされる。真言宗では護摩供・灌頂伝法・開眼供養など最重要の仏事をこの日に行うことを旨とす。"
        },
        "kongou": {
            "name": "金剛峯日",
            "reading": "こんごうぶび",
            "level": "吉",
            "description": "宿曜經記載的吉日。七曜與當日宿形成堅固的守護能量。原典記載「宜作一切降伏法，誦日天子呪及作護摩，並諸猛利等事」。適合護摩修法、降伏法、寫經、授戒、出家受戒、面試、考試等需要毅力與持續力的行動。",
            "description_classic": "金剛峯者，金剛界之堅固守護也。宜作一切降伏法，誦日天子呪及作護摩，並諸猛利等事。此日所作，堅牢不退，久長成就。",
            "description_ja": "金剛峯日は七曜と当日の宿が堅固な守護の力を形成する吉日なり。原典に「一切の降伏法を作し、日天子呪を誦し、及び護摩を作すに宜し」とある。密教の金剛界に由来し、護摩修法・降伏法・写経・授戒など猛利の行に最適なり。"
        },
        "rasetsu": {
            "name": "羅刹日",
            "reading": "らせつび",
            "level": "凶",
            "description": "宿曜經記載的凶日。七曜與當日宿的能量產生衝突，容易遇到阻礙。避免護摩、灌頂、簽約、遠行。適合靜坐禪修、誦經迴向、閉關自修、整理反省。",
            "description_classic": "羅刹者，障礙破壞之鬼神也。七曜與宿値相沖，諸事不順，多遇阻滯。此日宜靜守，不宜遠行興作。",
            "description_ja": "羅刹日は七曜と当日の宿が衝突し、障碍が生じやすい凶日なり。「羅刹」は仏教における悪鬼の名で、妨げと破壊を象徴する。この日は護摩・灌頂など重要な仏事を避け、静坐禅修・誦経回向・閑居自省に充てるべし。"
        }
    }

    # 因素優先級定義：當多因素同時存在時的判讀優先順序
    # 數值越大優先度越高，凌犯逆轉一切吉凶
    FACTOR_PRIORITY = {
        "ryouhan": 6,       # 凌犯期間（最高）— 逆轉所有吉凶
        "special_day": 5,   # 特殊日（甘露/金剛峯/羅刹）— 七曜與宿的特殊共鳴
        "rokugai": 4,       # 六害宿 — 人際層面的干擾
        "dark_week": 3,     # 暗黒の一週間 — 27 日循環的低潮期
        "relation": 2,      # 宿關係（栄親/安壊等）— 每日基本盤
        "sanki_day": 1,     # 三期サイクル日類型 — 最細緻的日常節奏
    }

    # 凌犯期間（七曜陵逼）查表
    # key: (農曆月, 朔日七曜) → (開始日, 結束日)
    # 農曆月: 1-12, 七曜: 0=日,1=月,2=火,3=水,4=木,5=金,6=土
    # 根據 nakshatra.tokyo 及宿曜經卷五
    RYOUHAN_MAP = {
        (1, 6): (1, 16),    # 正月 土曜 → 1-16日
        (1, 0): (17, 30),   # 正月 日曜 → 17-30日
        (2, 1): (1, 14),    # 二月 月曜 → 1-14日
        (2, 2): (15, 30),   # 二月 火曜 → 15-30日
        (3, 3): (1, 12),    # 三月 水曜 → 1-12日
        (3, 4): (13, 30),   # 三月 木曜 → 13-30日
        (4, 5): (1, 10),    # 四月 金曜 → 1-10日
        (4, 6): (11, 30),   # 四月 土曜 → 11-30日
        (5, 0): (1, 8),     # 五月 日曜 → 1-8日
        (5, 1): (9, 30),    # 五月 月曜 → 9-30日
        (6, 2): (1, 6),     # 六月 火曜 → 1-6日
        (6, 3): (7, 30),    # 六月 水曜 → 7-30日
        (7, 5): (1, 3),     # 七月 金曜 → 1-3日
        (7, 6): (4, 30),    # 七月 土曜 → 4-30日
        (8, 2): (1, 27),    # 八月 火曜 → 1-27日
        (9, 4): (1, 25),    # 九月 木曜 → 1-25日
        (9, 5): (26, 30),   # 九月 金曜 → 26-30日
        (10, 6): (1, 23),   # 十月 土曜 → 1-23日
        (10, 0): (24, 30),  # 十月 日曜 → 24-30日
        (11, 2): (1, 20),   # 十一月 火曜 → 1-20日
        (11, 3): (21, 30),  # 十一月 水曜 → 21-30日
        (12, 4): (1, 18),   # 十二月 木曜 → 1-18日
        (12, 5): (19, 30),  # 十二月 金曜 → 19-30日
    }

    # 凌犯期間三語描述（宿曜經卷五「七曜陵逼」+ nakshatra.tokyo 交叉驗證）
    RYOUHAN_DESCRIPTIONS = {
        1: {
            "classic": "正月土曜朔，初一至十六日陵逼。日曜朔，十七至三十日陵逼。",
            "ja": "正月の朔日が土曜なら1日〜16日、日曜なら17日〜30日が凌犯期間となる。",
            "zh": "正月朔日為土曜時，初一至十六為凌犯期間；朔日為日曜時，十七至三十為凌犯期間。"
        },
        2: {
            "classic": "二月月曜朔，初一至十四日陵逼。火曜朔，十五至三十日陵逼。",
            "ja": "二月の朔日が月曜なら1日〜14日、火曜なら15日〜30日が凌犯期間となる。",
            "zh": "二月朔日為月曜時，初一至十四為凌犯期間；朔日為火曜時，十五至三十為凌犯期間。"
        },
        3: {
            "classic": "三月水曜朔，初一至十二日陵逼。木曜朔，十三至三十日陵逼。",
            "ja": "三月の朔日が水曜なら1日〜12日、木曜なら13日〜30日が凌犯期間となる。",
            "zh": "三月朔日為水曜時，初一至十二為凌犯期間；朔日為木曜時，十三至三十為凌犯期間。"
        },
        4: {
            "classic": "四月金曜朔，初一至十日陵逼。土曜朔，十一至三十日陵逼。",
            "ja": "四月の朔日が金曜なら1日〜10日、土曜なら11日〜30日が凌犯期間となる。",
            "zh": "四月朔日為金曜時，初一至十為凌犯期間；朔日為土曜時，十一至三十為凌犯期間。"
        },
        5: {
            "classic": "五月日曜朔，初一至八日陵逼。月曜朔，九至三十日陵逼。",
            "ja": "五月の朔日が日曜なら1日〜8日、月曜なら9日〜30日が凌犯期間となる。",
            "zh": "五月朔日為日曜時，初一至八為凌犯期間；朔日為月曜時，九至三十為凌犯期間。"
        },
        6: {
            "classic": "六月火曜朔，初一至六日陵逼。水曜朔，七至三十日陵逼。",
            "ja": "六月の朔日が火曜なら1日〜6日、水曜なら7日〜30日が凌犯期間となる。",
            "zh": "六月朔日為火曜時，初一至六為凌犯期間；朔日為水曜時，七至三十為凌犯期間。"
        },
        7: {
            "classic": "七月金曜朔，初一至三日陵逼。土曜朔，四至三十日陵逼。",
            "ja": "七月の朔日が金曜なら1日〜3日、土曜なら4日〜30日が凌犯期間となる。",
            "zh": "七月朔日為金曜時，初一至三為凌犯期間；朔日為土曜時，四至三十為凌犯期間。"
        },
        8: {
            "classic": "八月火曜朔，初一至二十七日陵逼。",
            "ja": "八月の朔日が火曜なら1日〜27日が凌犯期間となる。",
            "zh": "八月朔日為火曜時，初一至二十七為凌犯期間。"
        },
        9: {
            "classic": "九月木曜朔，初一至二十五日陵逼。金曜朔，二十六至三十日陵逼。",
            "ja": "九月の朔日が木曜なら1日〜25日、金曜なら26日〜30日が凌犯期間となる。",
            "zh": "九月朔日為木曜時，初一至二十五為凌犯期間；朔日為金曜時，二十六至三十為凌犯期間。"
        },
        10: {
            "classic": "十月土曜朔，初一至二十三日陵逼。日曜朔，二十四至三十日陵逼。",
            "ja": "十月の朔日が土曜なら1日〜23日、日曜なら24日〜30日が凌犯期間となる。",
            "zh": "十月朔日為土曜時，初一至二十三為凌犯期間；朔日為日曜時，二十四至三十為凌犯期間。"
        },
        11: {
            "classic": "十一月火曜朔，初一至二十日陵逼。水曜朔，二十一至三十日陵逼。",
            "ja": "十一月の朔日が火曜なら1日〜20日、水曜なら21日〜30日が凌犯期間となる。",
            "zh": "十一月朔日為火曜時，初一至二十為凌犯期間；朔日為水曜時，二十一至三十為凌犯期間。"
        },
        12: {
            "classic": "十二月木曜朔，初一至十八日陵逼。金曜朔，十九至三十日陵逼。",
            "ja": "十二月の朔日が木曜なら1日〜18日、金曜なら19日〜30日が凌犯期間となる。",
            "zh": "十二月朔日為木曜時，初一至十八為凌犯期間；朔日為金曜時，十九至三十為凌犯期間。"
        },
    }

    # 六害宿：凌犯期間中以本命宿為基準的 6 個大凶日宿
    # 順時計方向（宿曜盤上順行）偏移量
    # 來源：yakumoin.net, kosei-do.co.jp, sukuyou.divination.page 三方交叉驗證
    # 凶度排序：命宿 > 事宿 > 意宿 > 聚宿 > 同宿 > 克宿
    ROKUGAI_OFFSETS = {
        "命宿": {"offset": 0, "severity": 1, "reading": "めいしゅく"},   # 本命宿
        "意宿": {"offset": 3, "severity": 3, "reading": "いしゅく"},   # 一九の安（第 4 番目）
        "事宿": {"offset": 9, "severity": 2, "reading": "じしゅく"},   # 業（第 10 番目）
        "克宿": {"offset": 12, "severity": 6, "reading": "こくしゅく"},  # 二九の安（第 13 番目）
        "聚宿": {"offset": 15, "severity": 4, "reading": "じゅしゅく"},  # 二九の壊（第 16 番目）
        "同宿": {"offset": 19, "severity": 5, "reading": "どうしゅく"},  # 三九の栄（第 20 番目）
    }

    # 三期サイクル：27 日為一循環，分三期各 9 天
    # 每期的起始關係和名稱
    SANKI_CYCLE = [
        {"name": "躍動の週", "reading": "やくどうのしゅう", "start_relation": "命",
         "description": "活動期。27日循環的第一期（一九），從命宿開始。能量充沛，適合積極行動、開展新事。",
         "description_classic": "一九者，命宿起行之期也。氣勢充盈，所作多成。宜積極進取，興造百事。",
         "description_ja": "一九（いっく）は命宿から始まる活動期なり。27日循環の最初の9日間にして、エネルギーが最も充実する時期。新たな計画の発起、重要な約束、積極的な行動に適す。"},
        {"name": "破壊の週", "reading": "はかいのしゅう", "start_relation": "業",
         "description": "衰退期。27日循環的第二期（二九），從業宿開始。前期積累的問題浮現，宜收斂整理。",
         "description_classic": "二九者，業宿起行之期也。前期所積之疲困顯現，氣勢轉衰。宜收斂謹慎，不宜妄動。",
         "description_ja": "二九（にく）は業宿から始まる衰退期なり。前期に蓄積した疲労や問題が表面化し、エネルギーが収斂に向かう。新規の着手を避け、手元の整理と反省に努めるべき時期。"},
        {"name": "再生の週", "reading": "さいせいのしゅう", "start_relation": "胎",
         "description": "轉換期。27日循環的第三期（三九），從胎宿開始。舊的結束、新的萌芽，適合反省與準備。",
         "description_classic": "三九者，胎宿起行之期也。舊事終而新事萌。宜靜養整理，以備來期。",
         "description_ja": "三九（さんく）は胎宿から始まる転換期なり。27日循環の最終段階にして、古きものの終わりと新しきものの萌芽が同時に起こる。静養・整理・準備に充て、次の循環に向けた蓄力の時期とす。"},
    ]

    # 三期サイクル各日型（每期 9 天：起始日 + 栄→衰→安→危→成→壊→友→親）
    # 起始日因期而異：一九=命、二九=業、三九=胎
    SANKI_DAY_TYPES = {
        # 各期的第 1 天（起始日）
        "period_start": {
            1: {"name": "命の日", "reading": "めいのひ",
                "description": "27 日循環的起點，本命宿回歸之日。原典記載「不宜舉動百事」，應靜守本分，不宜開展新事或做重大決定。適合反省與沉澱。",
                "description_ja": "27 日循環の起点にして本命宿回帰の日。原典に「百事を挙動するに宜しからず」とあり、新規の着手や重大な決断を避け、静かに自省するのが良い。"},
            2: {"name": "業の日", "reading": "ごうのひ",
                # 校勘注：品三(p.391b)記載「業宿直日，所作皆吉祥」，卷下(p.397c)記載「所作善惡亦不成就，甚衰」。
                # 兩處記載矛盾，系統採用卷下版本（三九秘要法的詳細展開，更具體可操作）。
                "description": "前世因緣顯現的業之位置。原典卷下記載「所作善惡亦不成就，甚衰」（注：品三另記「所作皆吉祥」，兩說不同，系統從卷下）。做什麼都難有結果，應低調收斂，不宜妄動。破壊の週的入口。",
                "description_ja": "前世からの因縁を示す業の位置。原典巻下に「善悪ともに成就せず、甚だ衰なり」とある（注：品三には「所作皆吉祥」とあり記載が異なる。本システムは巻下に従う）。何をしても結果に繋がりにくい。控えめに過ごし、破壊の週の入口として心構えを整える日。"},
            3: {"name": "胎の日", "reading": "たいのひ",
                "description": "再生的開始，對應胎之位置。原典記載「不宜舉動百事」，與命日同為靜守之日。適合靜心內省，為下一個循環做準備。",
                "description_ja": "再生の始まりにして胎の位置。原典に「百事を挙動するに宜しからず」とあり、命の日と同じく静守の日。内省を深め、次の循環に備える時。"},
        },
        # 第 2-9 天（全期共通）
        "day": {
            2: {"name": "栄の日", "reading": "えいのひ",
                "description": "原典記載「諸吉事並大吉」。入官拜職、對見大人、上書表進獻君王、興營買賣、裁著新衣、沐浴皆吉。出家人剃髮、割爪甲、沐浴、承事師主、啟請法要亦吉。積極行動的好日子。",
                "description_ja": "原典に「諸の吉事並びに大吉なり」とある。官職拝命・大人への拝謁・上書表の進献・売買経営・裁縫・沐浴すべて吉。出家者の剃髪・爪切り・沐浴・師事・法要請願にも好適。積極的に動いて吉。"},
            3: {"name": "衰の日", "reading": "すいのひ",
                "description": "原典記載「唯宜解除諸惡、療病」，另記「不宜遠行、出入遷移、買賣裁衣、剃頭剪甲」。氣勢減弱，適合除障、破邪、療病等淨化性質的行為，其餘不宜勉強。",
                "description_ja": "原典に「唯だ諸悪を解除し、病を療するに宜し」とあり、「遠行・出入遷移・売買・裁衣・剃頭剪甲並びに不吉」とも。気勢は弱まるが、浄化の行には向く。それ以外は無理をしないこと。"},
            4: {"name": "安の日", "reading": "あんのひ",
                "description": "原典記載「移徙吉，遠行人入宅、造作園宅、安坐臥床帳、作壇場並吉」。穩定安寧之日，搬遷、遠行歸宅、造宅、設壇修法皆吉。踏實前行的好時機。",
                "description_ja": "原典に「移徙吉、遠行人の入宅、園宅を造作し、坐臥の床帳を安んじ、壇場を作るに並びに吉」とある。安定の気が流れ、引越し・遠方からの帰宅・建築・寝具の設え・壇場設営に好適。着実に進めるのが吉。"},
            5: {"name": "危の日", "reading": "きのひ",
                "description": "原典記載「宜結交、定婚姻、歡宴聚會吉」，但另記「危壊日不宜遠行、移徙、買賣、婚姻、裁衣、剃頭、沐浴並凶」（注：婚姻在兩處記載吉凶不同）。社交聚會吉，遠行買賣則宜避開。",
                "description_ja": "原典に「結交を宜し、婚姻を定め、歓宴聚会に吉」とある一方、「危壊日は遠行・移徙・売買・婚姻・裁衣・剃頭・沐浴並びに凶」とも（注：婚姻の吉凶が箇所により異なる）。社交は吉、遠行・売買は避けるのが良い。"},
            6: {"name": "成の日", "reading": "せいのひ",
                "description": "原典記載「宜修道學問、合和長年藥法、作諸成就法並吉」。修法、學問、成就法皆吉。努力的成果開花結果，適合修行精進和完成重要事項。",
                "description_ja": "原典に「修道学問に宜し、長年の薬法を合和し、諸の成就法を作すに並びに吉」とある。修法・学問・合薬・成就法すべてに好適。努力が実を結び、修行精進と重要事項の完遂に最適。"},
            7: {"name": "壊の日", "reading": "かいのひ",
                "description": "原典記載「宜作鎮壓、降伏怨讎及討伐阻壞奸惡之謀，餘並不堪」。降伏法和鎮壓可行，但其他事務不宜。具有破邪顯正的力量。",
                "description_ja": "原典に「鎮圧を作し、怨讐を降伏し、阻壞奸悪の謀を討伐するに宜し、余は並びに堪えず」とある。降伏法・鎮圧・討伐は可能だが、他の事には不向き。破邪顕正の力がある日。"},
            8: {"name": "友の日", "reading": "ゆうのひ",
                "description": "原典品三記載「宜結交朋友大吉」，卷下記載「宜結交、定婚姻，歡宴聚會並吉」。人際關係圓滑，適合社交、宴會和協作。",
                "description_ja": "原典品三に「朋友と結交するに大吉」、巻下に「結交を宜し、婚姻を定め、歓宴聚会に並びに吉」とある。人間関係が円滑に進み、社交・宴席・共同作業に好適。"},
            9: {"name": "親の日", "reading": "しんのひ",
                "description": "原典記載「宜結交、定婚姻，歡宴聚會並吉」（與友日記載相同）。適合與家人、伴侶、至交相聚，社交宴會吉。",
                "description_ja": "原典に「結交を宜し、婚姻を定め、歓宴聚会に並びに吉」とある（友日と同じ記載）。家族・恋人・親しい友人との集まりに好適。社交・宴席に吉。"},
        }
    }

    # 月運勢專用描述
    MONTHLY_FORTUNE_DESCRIPTIONS = {
        "eishin": [
            "本月運勢極佳，天時地利皆站在你這邊。適合推動重要計畫、拓展人脈、爭取機會。積極主動，必有所獲。",
            "這個月你做什麼都比平時順手，特別是需要和人互動的事情。面試、提案、拓展業務都是好時機。",
            "貴人運集中出現的月份。你可能會遇到對職涯或人生有幫助的人，別猶豫，主動建立連結。",
            "想轉職、談加薪、或者爭取一個新職位的話，這個月是動手的好時機。你的表現會被看見，結果通常不會讓你失望。",
            "這個月你在團隊裡的影響力會明顯提升，適合主導專案或帶領新方向。別怕站出來，周圍的人會樂意配合你。"
        ],
        "gyotai": [
            "本月靈感充沛，創造力旺盛。適合學習進修、開發新專案、探索未知領域。相信直覺，勇於嘗試。",
            "這個月你的腦袋特別活躍，很適合研究新東西或啟動一個放在心裡很久的計畫。行動力配合靈感，效果加倍。",
            "你在本月對事情的判斷力比平時更準確。如果心裡有一個方向一直在呼喚你，這個月就是去嘗試的好時機。",
            "本月很適合進行深度學習或取得認證，你的專注力和理解力比平時好，看書和上課的效率會讓你自己驚訝。",
            "如果你從事創意相關的工作，這個月的產出品質會特別高。靈感來的時候馬上記下來，過了這個月可能就抓不住了。"
        ],
        "mei": [
            "本月能量穩定，適合沉澱反思。整理過去的經驗，規劃未來的方向。內省的功夫，將為下個階段打好基礎。",
            "這個月適合慢下來看看自己走到了哪裡。不需要急著做大事，花時間整理思緒和環境，會讓你接下來更有方向。",
            "安靜蓄力的一個月。表面上看起來沒什麼大動作，但你在內心做的規劃和調整，會在之後的月份發揮作用。",
            "這個月你對自己的優缺點看得特別清楚。趁這個機會補強弱項，或決定要把強項發揮到什麼程度，都很適合。",
            "本月適合檢視你的人際關係和生活重心。哪些人值得花更多時間相處、哪些習慣該改掉，現在想會比較客觀。"
        ],
        "yusui": [
            "本月步調平緩，維持現狀即可。專注於日常工作與生活品質，不宜大動作。穩紮穩打，細水長流。",
            "這個月不需要追求突破，把手邊的事情做扎實比開闢新戰場更重要。享受穩定的生活節奏。",
            "一個適合休養和充電的月份。不要給自己太大壓力，該休息就休息，等精力回復了再衝刺也不遲。",
            "這個月拿來還技術債、清待辦事項、或處理那些一直拖著沒做的行政雜務最適合。做完之後會輕鬆很多。",
            "不要跟別人比進度，每個人的節奏不一樣。這個月你需要的是紮實的積累，不是華麗的成績單。"
        ],
        "kisei": [
            "本月需多加留意，做事宜謹慎細心。重要決定多方考量，遇到困難尋求協助。小心駛得萬年船。",
            "這個月在工作和財務上要多留心細節，特別是合約條款和金額計算。遇到拿不準的事情，多問一個人的意見。",
            "外在環境可能出現一些變數，提前做好備案比事後補救容易得多。這個月的耐心和細心會為你擋掉不少麻煩。",
            "本月人際互動上容易有摩擦，特別是跟合作夥伴或家人之間。說話之前先想一想，很多衝突其實只是表達方式的問題。",
            "健康方面這個月要多注意，作息和飲食盡量規律。身體發出的小警訊不要忽略，早點處理比拖到嚴重好得多。"
        ],
        "ankai": [
            "本月運勢較為低迷，宜守不宜攻。重大事項建議延後，保守理財，避免衝動決策。韜光養晦，等待時機。",
            "這個月適合處理已經在進行的事情，不適合開啟新的大計畫。如果有重大簽約或投資，能延到下個月更好。",
            "暫時進入蟄伏期，但這不代表浪費時間。趁這段時間整理資源、補充知識、修復關係，下個月就能重新出發。",
            "這個月可能會覺得做什麼都使不上力，別焦慮，這是正常的週期波動。把能做好的小事做好，大事等下個月再說。",
            "本月最忌跟風或被別人帶著走。看到別人在衝，不代表你也要跟。守好自己的節奏，等時機對了你會跑得比誰都快。"
        ]
    }

    # 月運勢建議
    MONTHLY_FORTUNE_ADVICE = {
        "eishin": [
            "把握良機，積極行動，本月的努力將會有豐碩的回報。",
            "趁運勢好的時候多做幾件一直想做的事，現在開始的成功率最高。",
            "這個月你的存在感特別強，適合爭取曝光、發表意見、展現自己的能力。",
            "有想認識的人就大膽去搭話，有想合作的對象就主動聯繫。這個月你開口的成功率比你想的高很多。",
            "把最重要的事排在這個月處理，效率和結果都會比其他時間點好。順風的時候就全力衝刺，不要客氣。"
        ],
        "gyotai": [
            "傾聽內心的聲音，本月的靈感可能帶來意想不到的突破。",
            "如果有什麼念頭反覆出現在腦海裡，認真對待它——那可能就是你的突破口。",
            "本月適合報名課程、閱讀新書、參加工作坊，任何形式的學習都會有收穫。",
            "試著用新的角度看待老問題，你這個月的思維彈性很好，可能會找到之前怎麼想都想不到的解法。",
            "跟不同領域的人聊聊天，你會發現很多跨界的點子在腦袋裡自動連接起來。這個月的你吸收力特別強。"
        ],
        "mei": [
            "給自己一些獨處的時間，好好整理思緒，為未來做準備。",
            "寫日記、做心智圖、或跟信任的朋友深聊一次，這個月的自我梳理會很有價值。",
            "回顧一下過去三個月做的事情，哪些值得繼續、哪些該調整，趁現在想清楚。",
            "這個月適合定下來想想你真正在乎的事情是什麼。工作、生活、關係，排個優先順序，之後行動會更有方向。",
            "找一天把手機放下，花半天時間跟自己獨處。不管是散步、泡澡還是發呆，都會比滑手機有收穫。"
        ],
        "yusui": [
            "享受平穩的節奏，專注於提升生活品質，不必急於求成。",
            "趁這個月沒什麼大事的時候，處理拖延已久的小事和雜務，清爽迎接下個階段。",
            "把注意力放在吃好、睡好、運動這些基本功上，身體狀態好了，做什麼都會更順。",
            "這個月適合經營你的日常小確幸。整理房間、學做一道新菜、或者固定去運動，建立好習慣比追求大目標更實際。",
            "不要因為沒有大進展就覺得焦慮。每一天把該做的事做好，累積下來的成果比你以為的更扎實。"
        ],
        "kisei": [
            "遇事多想幾步，謹慎行事，小心能避開大部分的麻煩。",
            "這個月做決定前多留一天冷靜期，急著回覆的衝動往往會帶來後悔。",
            "備份重要檔案、確認截止日期、提前處理行政事務，這些小動作能幫你避開大問題。",
            "跟人合作的時候把責任歸屬講清楚，白紙黑字比口頭約定可靠。這個月模糊地帶最容易出問題。",
            "錢的事情這個月要特別小心，不管是借出去還是投資。看不懂的東西不要碰，已經答應的承諾要確實履行。"
        ],
        "ankai": [
            "保持低調，養精蓄銳，等待更好的時機再出擊。",
            "這個月先把體力和精力養好，下個月運勢回升時你就有本錢衝刺了。",
            "不需要和困難硬碰硬，暫時繞路走也是一種策略。保存實力比消耗自己更聰明。",
            "這個月少做承諾、少接新任務，把現有的事情收好收滿就夠了。等運勢轉好再擴張版圖也來得及。",
            "如果周圍有人想拉你進一個看起來很好的機會，先冷靜觀察。這個月你容易因為急著翻身而做出判斷失誤。"
        ]
    }

    # 週運焦點：根據元素關係類型提供本週關注方向
    WEEKLY_FORTUNE_FOCUS = {
        "same": [
            "本週的七曜能量與你的本命元素相同，內在能量充沛，做事的手感特別好。適合推進需要個人專注力的工作，你的判斷力和執行力都處於高峰。把重要的決策和關鍵會議安排在這幾天，效率會讓你自己驚訝。",
            "同元素週意味著你和環境的頻率完全對上了。平時覺得吃力的事情這週會變得輕鬆，與人溝通的理解力也比平時好。拿來處理需要深度思考的任務，或者跟重要的人談一件你一直想談的事。",
            "你的本命元素在這週被強化，個人特質會更鮮明。擅長的領域表現突出，但也要注意別太執著於自己的想法，聽聽不同聲音能讓你的計畫更全面。",
            "同頻共振的一週。你的表達力和感染力都處在高位，適合做簡報、帶領團隊、或者處理需要說服別人的事情。這週做出的決定通常經得起時間考驗，因為你的判斷力特別穩。",
            "本週你的存在感比平時強。不管是職場上的發言還是生活中的互動，別人會更加關注你的想法。利用這份影響力去推動你在意的事情，效果事半功倍。"
        ],
        "generating": [
            "本週外在能量正在滋養你的本命元素，環境條件對你特別有利。別人的支持和配合會比平時更容易到位，適合處理需要外部資源的事情。開口求助、提出合作邀請、爭取預算，這週的成功率值得你積極嘗試。",
            "相生週帶來的是一種「什麼都比較順」的感覺。人際互動中你會發現貴人不請自來，工作上的阻力也比預期小。把握這段好時機，把拖延已久的重要事項排進行程。",
            "能量場向你傾斜的一週。學新東西的吸收力強，推動計畫的執行力好，連運氣都比平時好一些。不需要刻意做什麼特別的事，但也別浪費了這份順勢。",
            "外部資源向你匯聚的一週。無論是同事的主動協助、朋友的有用資訊、還是工作中意外發現的捷徑，你會覺得身邊的人和事都在幫你。這時候放大你的行動範圍，多跨出一步，回報會超出預期。",
            "這週的學習效率特別高。不管是讀書、上課、還是在工作中邊做邊學，你能比平時更快地把新知識轉化為可用的能力。如果有一直想研究的題目，這週正好可以花幾個晚上好好鑽研。"
        ],
        "weakening": [
            "本週你的能量有向外流失的跡象，做事可能需要比平時多花一點力氣。不必焦慮，調整好節奏最重要：減少不必要的社交、推掉能推的應酬、把精力集中在少數幾件真正重要的事上。做得少但做得好，比什麼都碰一點但都做不完更有價值。",
            "能量被消耗的一週，你可能會覺得動力不如上週。這是正常的週期變化，對策是降低同時處理的事情數量。把待辦清單砍掉一半，專心把剩下的做好。同時注意飲食和睡眠，身體的補給比任何策略都管用。",
            "本週適合用效率取代時間。不要用加班來補進度，而是想辦法優化流程。能自動化的就自動化、能委託的就委託、能簡化的就簡化。省下來的精力留給需要你親自處理的關鍵環節。",
            "消耗感比較明顯的一週。你的身體和大腦都在暗示你放慢速度，不要硬撐。中午如果能小睡十五分鐘就小睡，晚上能早一小時上床就早一小時。體力的恢復直接影響你下週的表現。",
            "本週不適合同時處理太多事。列出待辦事項之後，把重要程度排在前三名以外的全部延到下週。你的精力有限，與其十件事都做到五十分，不如三件事做到九十分。"
        ],
        "conflicting": [
            "本週外在能量與你有些摩擦，計畫可能遇到預期之外的變數。不要把這當成壞事——阻力往往是在提醒你哪個環節還沒準備好。遇到卡關的時候先退一步看全局，找到問題的真正原因再處理，比硬推有效。這週的耐心比能力更重要。",
            "這週的挑戰在於控制節奏。外在環境會製造一些干擾，讓你很想加快速度把事情搞定，但越急越容易出錯。每天完成最重要的三件事就好，其他的留到下週。穩住不急躁，比什麼都重要。",
            "溝通方面本週需要多花心思。別人的反應可能不如你預期，不是你說錯了什麼，而是雙方的頻率暫時沒對上。重要的訊息用文字確認、口頭協議留下紀錄，減少誤會的空間。",
            "這週可能會出現一兩個讓你措手不及的狀況。提前把重要任務的截止日往前拉兩天，給自己留緩衝空間。萬一真的遇到突發狀況，你還有時間應對而不至於手忙腳亂。",
            "張力帶來的不全是壓力，偶爾也是突破的契機。如果你一直卡在某個問題上，這週的摩擦力反而可能逼你想出一個全新的解法。換個角度看問題，阻力也能變成推力。"
        ],
        "neutral": [
            "本週能量平穩，沒有特別好也沒有特別差的外力影響。這種時候你的主動作為比什麼都重要——想推什麼就去推、想學什麼就去學，不會有意外的阻礙，也不會有天上掉下來的好運。踏實做事，結果不會讓你失望。",
            "中性能量的一週，適合處理需要穩定輸出的工作。寫報告、整理資料、複習進度，這些不太刺激但很重要的事情在這週做最恰當。把基礎打好，下週如果有好機會就能馬上接住。",
            "既然外在環境不會主動推你或拉你，那就自己決定這週的重點。挑一件你最想完成的事情，集中火力去做。沒有干擾的時候，專注力是你最強的武器。",
            "平穩的一週適合做規劃。不管是下個月的工作計畫、週末的安排、還是年度目標的進度檢查，在沒有外力干擾的時候做規劃，頭腦最清楚、判斷最準確。花一個小時靜下來想清楚方向，值得。",
            "本週不會有什麼意外打亂你的節奏。利用這段穩定期把一些雜事清一清——回覆積壓的訊息、整理桌面和電腦資料夾、確認保險和帳單。把這些小石頭搬開，後面跑起來才不會絆倒。"
        ]
    }

    # 週運各項提示：事業/感情/健康的週度短提示
    WEEKLY_CATEGORY_TIPS = {
        "career": {
            "same": [
                "事業上你的判斷力本週特別準，適合做重要決策。推進需要個人擔當的專案、主動爭取新的機會，你的表現會讓人印象深刻。",
                "工作效率高峰期。把最燒腦的任務排在這幾天，你的專注力和產出品質都在最佳狀態。順手清掉那些拖了好幾週的待辦事項。"
            ],
            "generating": [
                "職場上這週特別容易獲得支援。有什麼需要協調的資源、需要主管點頭的提案，趁這幾天提出來，通過率比平時高。",
                "跨部門合作或團隊協作的效率本週特別好。你的提案容易被接受，別人配合度也高。把需要多方溝通的任務排在這週處理。"
            ],
            "weakening": [
                "事業上這週以守為主。不是擴張的好時機，但適合把現有的工作做到更好。優化流程、整理文件、復盤上週的成果。",
                "工作量可能比預期大，優先處理有截止日的任務。能推遲的非緊急事項留到下週，這週的精力有限，用在刀口上。"
            ],
            "conflicting": [
                "職場溝通本週需要格外注意措辭。重要的指示和協議用文字留底，避免口頭約定事後各說各話。",
                "工作中可能會遇到計畫外的變動。保持彈性，準備好備案。與其抱怨變化，不如把它視為展現應變能力的機會。"
            ],
            "neutral": [
                "事業穩定推進的一週。沒有特別的順風或阻力，靠自己的節奏穩步前進即可。適合處理需要耐心和細心的工作。",
                "本週適合做工作上的長期規劃。趁環境平靜的時候想清楚下個月甚至下一季的重點方向。"
            ]
        },
        "love": {
            "same": [
                "感情上你的魅力值本週偏高，跟人互動時從容自信的態度很加分。有伴的人適合安排一次質感好的約會，單身的人可以主動出擊。",
                "情感表達力本週特別好。平時不太會說的話，這週說出來反而很自然。如果有什麼想對重要的人說的，別再拖了。"
            ],
            "generating": [
                "感情上被支持的感覺很強。另一半比平時更體貼，朋友也可能主動幫你牽線。好的感情能量要珍惜，也要記得回饋。",
                "社交運佳，適合參加聚會或約會。你這週散發的親和力讓人想靠近，這是拓展新關係的好時機。"
            ],
            "weakening": [
                "感情上這週可能因為疲倦而顯得冷淡。不是你不在乎，只是精力有限。跟另一半或朋友解釋一下你的狀態，別讓對方誤解。",
                "本週的情緒波動比較大，別在心情不好的時候做關於感情的重大決定。先調整好自己的狀態再說。"
            ],
            "conflicting": [
                "人際互動本週可能有些小摩擦。不是大事，但如果處理不好可能留下心結。有誤會就當場說清楚，別讓小問題發酵。",
                "跟另一半的溝通本週需要多一點耐心。你們可能在某些小事上看法不同，不用爭出勝負，互相理解比贏了辯論重要。"
            ],
            "neutral": [
                "感情生活本週平淡穩定。沒有浪漫的驚喜，但也沒有什麼煩心事。利用這段平靜好好陪伴在意的人，日常的相處才是感情的根基。",
                "社交節奏隨意調整即可。想約人就約，想獨處就獨處。不用強迫自己去社交，也不用刻意迴避。順其自然的互動最舒服。"
            ]
        },
        "health": {
            "same": [
                "身體狀態本週穩定。適合維持或加強運動習慣，你的體能和精神狀態都在正常範圍。不要因為感覺好就過度操勞。",
                "健康方面本週沒有特別的問題。保持正常的作息和飲食即可。如果可以的話，多喝水、少喝含糖飲料。"
            ],
            "generating": [
                "精力充沛的一週。適合增加運動強度或嘗試新的運動方式。身體恢復力好，即使稍微累一點也能很快復原。",
                "身體的代謝效率本週偏高，是調整飲食或開始新的健康計畫的好時機。做出的改變比較容易看到效果。"
            ],
            "weakening": [
                "本週容易感到疲累。晚上盡量在十一點前上床，減少咖啡因的攝取。如果覺得肩頸很緊，花十分鐘做伸展操。",
                "免疫力本週可能稍微下降。注意保暖、避免吃太涼的食物。如果身體有不舒服的感覺，別硬撐，早點休息。"
            ],
            "conflicting": [
                "壓力可能反映在身體上。留意頭痛、肩頸僵硬、失眠等訊號。每天花十分鐘做深呼吸或簡單伸展，讓身體釋放緊繃。",
                "健康方面本週要特別注意情緒對身體的影響。煩躁的時候用運動代替久坐，散步二十分鐘比滑手機兩小時有效得多。"
            ],
            "neutral": [
                "身體狀態平穩，適合維持現有的健康習慣。如果你已經有固定運動的習慣，繼續保持。如果還沒有，從每天走路三十分鐘開始。",
                "本週的健康管理以「維持」為主。不需要特別加強什麼，保持穩定的作息和飲食就是對身體最好的照顧。"
            ]
        }
    }

    # 月運主題描述：根據本命宿與月宿的關係描述整體氣氛
    MONTHLY_THEME_DESCRIPTIONS = {
        "eishin": [
            "這個月的宇宙能量全力支持你，像是站在順風處的弓箭手，射出去的每一支箭都會比平時飛得更遠。你在人群中的影響力會自然提升，別人比較願意聽你的想法、接受你的提議。好好利用這股勢頭，把那些需要說服別人、爭取資源的事情排在這個月處理。",
            "月宿與你的本命宿形成最佳互動角度，做事的時候你會感覺一切都在配合你。靈感會在日常中自然浮現，人際關係的摩擦也比平時少。建議把最重要、最想做好的事情排在這個月，因為你的成功率明顯高於其他時段。",
            "本月的關係場域特別有利。不管是職場合作還是私人交往，你釋放出來的能量讓別人想要靠近你、幫助你。這不是運氣，是你的本命宿和這個月的能量場高度契合的結果。主動出擊，收穫會超乎預期。"
        ],
        "gyotai": [
            "這個月你和宇宙之間有一條看不見的線在共振，直覺特別準、靈感特別多。平時想破頭的問題，可能在散步或洗澡的時候突然有了答案。別急著用邏輯否定那些閃過腦海的念頭，先記下來再慢慢驗證。這個月的第六感值得信任。",
            "月宿與本命宿的共鳴讓你這個月的感知力變得更敏銳。你能比平時更準確地判斷一件事該不該做、一個人值不值得信任。把這份敏銳度用在決策上，可以省掉很多走彎路的時間。學習新東西的效率也比平時好，好好把握。",
            "本月的能量場有利於深度思考和創意發想。如果你的工作需要寫方案、做設計、或者構思策略，這個月的產出品質會讓你自己驚訝。找幾個安靜的下午專心工作，不要讓瑣事把靈感打斷了。"
        ],
        "mei": [
            "這個月的能量像一面清澈的湖水，適合停下腳步看清楚自己的倒影。你會比平時更了解自己真正想要什麼、不想要什麼。利用這份清明做一些重要的自我對話：職涯方向對不對？生活重心需不需要調整？現在想得清楚，後面才不會後悔。",
            "月宿和本命宿形成的角度讓你暫時抽離了日常的忙碌，退一步看全局。這不是消極或怠惰，而是戰略性的暫停。花時間做復盤、整理資訊、重新規劃優先順序，這些看似不產出的行為，其實是在為下一波行動蓄力。",
            "本月適合做減法。那些占用你時間但沒有實質回報的活動、半途而廢的計畫、消耗你能量的關係，趁這個月的清醒做出取捨。留下來的才是真正重要的，之後你的精力會更集中、更有效率。"
        ],
        "yusui": [
            "這個月的能量平緩穩定，沒有大起大落。表面上看似平淡，但這正是打地基的好時機。那些需要耐心、需要重複練習的事情，在這個月做最合適。每天進步一點點，累積下來的成果會在之後的月份爆發出來。",
            "月宿能量與你的本命宿保持適度距離，你不會被外力推著走，也不會被拖住腳步。利用這份自在去做那些被你拖延的事情：整理收納、更新履歷、檢查保單、清理硬碟。做完之後那種清爽的感覺值得你花一個週末。",
            "本月的關鍵是不要跟別人比進度。每個人的能量週期不一樣，別人在衝刺的時候你正好在蓄力，這完全正常。把注意力放回自己身上，紮紮實實地把手邊的事做好，不用擔心落後。"
        ],
        "kisei": [
            "這個月的能量帶有一些摩擦感，做事可能會遇到預期之外的阻力。不要因此焦躁，阻力也是一種資訊——它在告訴你哪些環節需要多花心思。提前做好備案、重要文件多檢查一遍、跟人溝通的時候把話說清楚，就能把大部分風險擋在門外。",
            "月宿和本命宿之間存在一些張力，你可能會發現這個月需要花比較多力氣去處理突發狀況。放慢節奏、降低對自己的期望值不是認輸，而是聰明的策略。用八成的力量做事，留兩成應對意外，反而能走得更穩。",
            "這個月的人際互動需要多一份耐心。別人可能無意間踩到你的地雷，你也可能因為壓力大而對身邊的人不夠溫柔。意識到這一點就好了——遇到不舒服的時候先深呼吸三次再回應，能省掉事後道歉的麻煩。"
        ],
        "ankai": [
            "這個月的能量場偏低，你可能會覺得動力不足、做事使不上力。這是本命宿和月宿之間的自然週期，不是你的問題。最好的應對方式是順勢而為：減少社交應酬、推遲重大決定、把精力集中在維持現狀上。等下個月能量回升了再重新出發。",
            "月宿能量與你的本命宿處於最不協調的位置，這個月不適合冒險和擴張。守住手上已有的成果，把做到一半的事情收尾，比開始新的計畫更有價值。如果可以的話，這個月多留一些時間給自己，充足的休息是恢復能量最有效的方式。",
            "本月最忌急躁和衝動。看到好機會先按住想伸手的衝動，等觀察幾天確認沒問題再行動。這個月你的判斷力會比平時稍微遲鈍一些，多聽信任的朋友怎麼說，用別人的視角補充自己看不到的盲點。"
        ]
    }

    # 年運建議：根據天干元素與本命元素的關係生成差異化建議
    YEARLY_FORTUNE_ADVICE = {
        "same": [
            "今年的干支能量與你的本命元素相同，如同照鏡子般的一年。你對自身的長處和短處會看得異常清楚，適合藉此機會重新定位自己的發展方向。同類能量共振雖然穩定，但要注意避免思維固化，主動接觸不同領域的人會為你帶來新的視野。",
            "本命元素與年度能量一致，你的個人特質在今年會被放大。擅長的事情做起來得心應手，但缺點也可能更明顯。建議把精力集中在你最有優勢的領域，用深耕取代廣撒。同時安排固定的自我檢視時間，確保不會在舒適圈裡停滯不前。",
            "同元素年份是鞏固根基的好時機。過去累積的技能和人脈在今年會自然發酵，不需要刻意推銷自己，該來的機會會自己找上門。重點是把基本功做紮實，讓你的專業能力經得起時間考驗。"
        ],
        "generating": [
            "今年的干支能量對你的本命元素形成相生關係，外在環境自然而然地在支持你。這是積極擴張的好年份，不管是換工作、拓展業務、還是嘗試新技能，成功率都比平時高。唯一要注意的是不要因為順利就鬆懈了品質管控，根基穩固才能走得長遠。",
            "年度能量正在滋養你的本命元素，就像植物遇到了適合的土壤和氣候。你會發現做事的阻力變小了，過去推不動的案子今年可能出現轉機。趁勢把握，但記得分配好精力，不要什麼都想抓，聚焦在兩三個最重要的目標上效果最好。",
            "相生年份帶來的不只是運氣好，更是學習和成長的加速期。你的吸收力和理解力在今年特別強，報名課程、考取證照、或者深入研究一個新領域都很適合。投資在自己身上的時間和金錢，回報率會超出你的預期。"
        ],
        "weakening": [
            "今年你的本命元素正在滋養干支能量，代表你的付出會比較多。工作上可能扛起更多責任，或者花大量時間幫助身邊的人。這不是壞事，但你必須學會管理自己的能量，定期休息和充電。每個月留出幾天完全放空的時間，不要讓自己燃燒殆盡。",
            "能量被消耗的年份，你會感覺做同樣的事需要比以前更多的力氣。這時候效率比努力更重要——學會說不、設定界線、把不必要的社交和雜務砍掉。把省下來的精力用在真正重要的事情上，少做但做好，反而能取得更扎實的成果。",
            "今年的關鍵字是「精簡」。你的能量有限，沒辦法什麼都顧到。列出今年最想完成的三件事，其他全部放到候補清單。同時注意身體健康，飲食均衡和充足睡眠不是建議，是今年必須遵守的底線。"
        ],
        "conflicting": [
            "今年的干支能量與你的本命元素存在張力，外在環境可能帶來一些挑戰和壓力。但張力也是成長的催化劑——那些讓你不舒服的狀況，往往是在推你離開舒適圈。面對困難不要硬撐，善用團隊和外部資源，這一年適合學習借力使力的智慧。",
            "相剋能量的年份不代表運氣差，而是需要用不同的策略。直線前進受阻時，換個角度繞路反而更快。今年適合培養耐性和彈性，遇到阻礙先停下來觀察全局，找到對的切入點再行動。急躁是今年最大的敵人，穩住節奏才能化險為夷。",
            "這是一個需要「磨」的年份。工作中的摩擦、人際上的衝突、計畫的延遲，都是在磨掉你身上不需要的稜角。撐過去之後你會發現自己變得更成熟、更有韌性。控制好情緒，不要在壓力下做重大決定，等風頭過了再定奪。"
        ],
        "kyo": [
            "九曜循環走到低谷，今年的外在環境會比較嚴苛。這是九年一次的能量低潮，不是針對你，而是循環走到了這裡。最務實的策略是縮小戰線：把手上的事情分成「必須做」和「可以等」，只留必須做的，其他全部暫緩。不要在這一年啟動新計畫、跳槽、或做任何需要大量資源投入的事。守住現有的，等低谷過去再說。遇到重大決定先擱七天，讓自己有足夠的時間從不同角度看事情。",
            "今年會比較辛苦，這是事實，不需要粉飾。但辛苦不等於毀滅，九曜的循環每九年一輪，低谷之後就是回升。你現在要做的只有一件事：安全度過。減少不必要的社交應酬、推掉高風險的邀約、避免借貸和大額投資。人際方面，話到嘴邊停三秒再說，今年特別容易因為一句氣話毀掉多年經營的關係。身邊有讓你安心的人，多跟他們待在一起。",
            "低潮年有一個被忽略的好處：它會幫你看清什麼才是真正重要的。順風順水的時候你分不清什麼是實力、什麼是運氣；逆境來了，還留在身邊的人、還能穩住的事情，那才是你的底牌。今年不追求成長，追求穩定。把生活作息固定下來、把身體照顧好、把最核心的幾段關係維護住。年底你回頭看會發現：你沒有少什麼，反而知道自己真正擁有什麼。"
        ],
        "neutral": [
            "今年的干支能量與你的本命元素沒有明顯的衝突或加持，意味著你有更大的自主空間。命運的影響力退到背景裡，你的主動作為才是決定年度成績的關鍵。想衝刺就衝刺、想休息就休息，沒有特別好或特別壞的外力推著你走。自律的人在這種年份最容易拉開差距。",
            "中性能量的年份就像一塊空白畫布，最終畫出什麼完全取決於你自己。不會有太多意外驚喜，但也不會有無法預見的災難。這是最適合制定長期計畫並穩定推進的時期，因為外在變數少，你可以專心把手上的事做到最好。",
            "今年沒有明顯的順風或逆風，比較適合做那些需要長時間持續投入的事情——學一門語言、養成運動習慣、系統性地整理財務、或者經營一段穩定的關係。急不得也懶不得，用日拱一卒的心態，年底回頭看會很有成就感。"
        ]
    }

    # 年度主題敘事：根據天干元素與本命元素的關係描述整體走向
    YEARLY_THEME_DESCRIPTIONS = {
        "same": [
            "今年你和年度能量的頻率完全一致。這種同頻共振會放大你的核心特質，讓你在擅長的領域格外得心應手。你的直覺更準、決策更果斷、表達更有說服力。但同頻也意味著盲點會被放大，你可能過度自信而忽略旁人的提醒。找一兩個信任的朋友定期交換想法，用外部視角修正你看不到的死角。這一年適合做深耕，把已經有基礎的技能或關係往上推一個層次，而不是四處開新戰場。",
            "同元素的年份像是一面放大鏡。你最自豪的能力會更突出，但暗處的短板也會因為光線充足而無處躲藏。好消息是，看見問題才有機會處理。年初花一個月做自我盤點，列出三項想強化的優勢和兩項需要正視的不足，然後用剩下的十一個月紮實推進。你不需要追求全面進步，把最重要的幾件事做到位就足夠了。穩定輸出的一年，結果取決於你的紀律。",
            "今年的外在環境像是你內在能量的映射。你擅長什麼，機會就往哪邊靠攏。過去累積的人脈、技能、聲譽會在今年自然轉化為實際報酬。做你最擅長的事，不要被「應該多嘗試」的聲音分散注意力。你的存在感比任何時候都強，該展現的時候不必謙虛。穩住節奏，避免在舒適圈裡待太久卻以為自己在進步。"
        ],
        "generating": [
            "今年外在能量正在主動支持你，就像風從背後吹來，走起來比平時輕鬆。你申請的東西更容易通過、合作的提案更容易被接受、學新技能的速度也快了不少。這不是虛假的泡沫，而是你本命元素被大環境滋養的結果。把握這股順風，把一直想做但沒勇氣開始的事排進今年的計畫裡。唯一需要注意的是，順利的時候人容易膨脹。定期停下來檢查方向是否正確，比一直跑更有價值。",
            "相生年份帶來的最大禮物是「吸引力」——你會自然吸引到對你有幫助的資源、人脈和機會。這不是玄學，而是你的狀態好的時候，別人更願意跟你合作。充分利用這個優勢去建立長期關係：多參加行業活動、主動約見想合作的人、把那些放在備忘錄裡的計畫拿出來執行。今年種下的種子，會在未來兩三年持續結果。但別什麼都想抓，集中在兩三個核心目標上的效果最好。",
            "今年你的學習能力和適應力都在高峰。不管是轉換跑道、學一門新技術、還是進入一個陌生的社交圈，你的上手速度會比預期快很多。年初勇敢跨出舒適圈，年底回頭看會慶幸自己沒有猶豫。環境在幫你，但你需要先邁出那一步。建議在上半年就把最重要的新嘗試啟動，下半年用來鞏固和深化。"
        ],
        "weakening": [
            "今年你的能量會向外流出比較多，直白說就是付出大於回收。你可能要扛起更多責任、花更多時間處理別人的事、或者面對超出預期的工作量。既然如此，能量管理就是今年最重要的課題。把時間和精力視為有限的預算來分配，每週留至少一天完全放空，不處理任何需要用腦的事。當你覺得「再多做一點應該沒關係」的時候，通常就是該停下來的時候。做得少但做得好，比什麼都沾一點但全部做到六十分好得多。",
            "能量消耗型的年份不代表注定辛苦，而是需要換一種打法。直覺反應是「加倍努力」，但正確的策略是「精準投入」。砍掉對你沒有實質幫助的社交、推掉沒有回報的額外工作、把時間留給真正重要的少數事情。同時，這一年你在幫助別人的過程中反而會學到東西。那些看似在消耗你的付出，可能在幾年後以意想不到的方式回報你。",
            "今年最需要的兩個字是「設界」——設定界線。你的本命元素正在滋養外界，如果不主動控制輸出量，到年底你會覺得被掏空。學會在適當的時候說「這個我做不了」或「這個時間我不方便」。你的健康是今年的底線，飲食、睡眠和運動不是加分題，是必答題。保護好自己，你才能持續為身邊的人帶來價值。"
        ],
        "conflicting": [
            "今年的能量場有不少摩擦和張力。計畫可能被打斷、人際互動可能出現衝突、你以為很穩的事情可能冒出變數。這些不順不是針對你，而是你的本命元素和年度能量之間需要一段磨合期。面對挑戰時，退一步想清楚再行動比硬撐有效。今年培養出來的耐性和應變力會成為你未來幾年最重要的資產。避免在壓力大的時候做重大決定，那些讓你覺得「必須現在決定」的事情，十之八九可以等幾天。",
            "張力也是轉化的契機。今年你會被迫面對一些你一直在逃避的問題——可能是工作方向、人際關係、或者自我認知。過程不舒服，但解決之後你會脫一層皮、變一個人。把這一年當成密集訓練營：你不會喜歡過程，但會感謝結果。保持彈性、控制情緒、遇到卡關就換個方式試。最糟的做法是停在原地生悶氣。",
            "今年的關鍵策略是「繞路前進」。直線走不通的時候，換個角度切入反而更快。你會發現原本的計畫A行不通，但計畫B和C可能帶來更好的結果。放下對既定方案的執著，用變通取代固執。這一年你和某些人的關係可能會變得緊張，不是誰對誰錯，而是頻率暫時不同步。給彼此多一點空間，等風頭過了自然會恢復。"
        ],
        "kyo": [
            "今年是九曜循環中的低谷段，外在環境的支持力降到最低。你會覺得做什麼都比平時費勁，本來順手的事情冒出一堆小狀況，人際關係也可能莫名其妙變得緊繃。這些不是你的問題，是年運的節奏走到了這裡。最聰明的做法是承認現實，然後調整打法：把目標從「往前衝」改成「不後退」。守住工作、守住健康、守住重要的人，其他都可以放一放。這一年你不需要證明什麼，只需要穩穩地走過去。九曜循環不會停在這裡，低谷的另一邊就是回升。",
            "接下來這一年，事情的發展可能不會照你的劇本走。你安排好的計畫會被打斷、你信任的人可能讓你失望、你努力的方向未必有即時回報。聽起來很糟，但低潮年有一個特性：它不會永遠持續下去。你現在的任務不是逆轉局面，而是保存實力。把精力集中在三件事上——睡好、吃好、和讓你安心的人保持聯繫。大的決定能拖就拖，等狀態回來再做。你以前撐過的難關比這個多，這次也一樣。",
            "九曜低谷年的特徵是「什麼都慢半拍」。申請的東西晚批、約好的事情改期、預期的收入延遲入帳。你可能因此焦躁，覺得自己被困住了。但「慢」不是「停」。你可以趁這段強制減速的時間做一些平常沒空做的事：整理那堆拖了半年的文件、把斷聯的老朋友約出來吃頓飯、認真想一想接下來三年你到底想過什麼樣的日子。這一年不會給你舞台，但會給你思考的空間。用好這段時間，等下一波上升期到來時你會比別人準備得更充分。"
        ],
        "neutral": [
            "今年的外在環境不會主動推你，也不會拉你後腿。你有最大的自主權來決定這一年要過成什麼樣子。對自律的人來說這是最好的年份——你做什麼就得什麼，付出多少就回收多少，公平透明。但缺乏自律的人會覺得這一年「好像什麼也沒發生」。差別在於你有沒有主動設定目標並且持續推進。年初花兩週時間認真規劃全年，然後用季度為單位檢核進度。這一年沒有驚喜也沒有意外，最終結果完全是你行動的總和。",
            "中性能量年份像一張白紙——你可以畫出任何你想要的圖案。沒有順風不代表逆境，只是環境退到背景裡，把舞台完全留給你。適合做那些需要長期穩定投入的事情：學語言、寫書、建立被動收入、經營深度關係。急躁是這一年最大的浪費，因為沒有外力干擾的時期最適合專注，而你把它浪費在焦慮上就太可惜了。",
            "今年的座右銘是「日拱一卒」。不需要大爆發、不需要抓住什麼轉瞬即逝的機會、不需要跟任何人競爭。每天做好手邊的事，每週完成一個小目標，每月檢視一次方向。年底你會驚訝地發現，不知不覺間已經走了很遠。穩定的一年，成果取決於你的持續性而非爆發力。"
        ]
    }

    # 年度各項分述：事業/感情/健康/財運的年度走勢描述
    YEARLY_CATEGORY_DESCRIPTIONS = {
        "career": {
            "same": [
                "事業方面，同元素年份讓你的專業能力被放大。你在自己的領域裡如魚得水，同事和主管會更加信任你的判斷。適合深耕現有崗位、爭取更大的責任範圍。但要注意不要因為太熟練而失去創新的動力。",
                "今年的職場表現穩定而扎實。你的工作風格和環境需求完全匹配，推進專案的效率比往年高。如果有升遷機會，主動爭取的成功率不低。別在舒適圈裡待太久，偶爾接一些有挑戰的任務來維持成長。"
            ],
            "generating": [
                "事業運勢旺盛，外部環境在推你向上。今年很適合換工作、創業、或者在公司內部爭取新的職位。你提出的想法比較容易被採納，跨部門合作也比較順利。年初就鎖定目標，用上半年衝刺，下半年穩固成果。",
                "今年職場上的貴人特別多。有人會主動拉你一把、介紹你認識關鍵人物、或者給你一個意想不到的機會。保持開放心態，別急著說不。同時提升自己的可見度——不是張揚，而是讓你的專業成果被需要看到的人看到。"
            ],
            "weakening": [
                "事業上今年需要多花一些力氣。你可能被分配到更多的工作量，或者需要處理別人留下的爛攤子。這不是你能力不夠，而是能量消耗型年份的正常現象。把精力集中在最能展現價值的兩三件事上，其他的用最低限度的標準過關即可。",
                "今年職場上的主旋律是「守成」。不是擴張的好時機，但很適合把手上的事情做到極致。把流程優化、把關係經營好、把基礎打牢。等能量恢復的年份到來時，你現在的積累會成為衝刺的資本。"
            ],
            "conflicting": [
                "事業上今年會遇到一些意外的挑戰。計畫被打亂、合作對象臨時變卦、市場風向突然轉彎。這些變數不一定是壞事，因為有些更好的機會藏在變化裡。保持彈性，不要死抱著原來的計畫不放。讓自己有空間嘗試計畫B和C。",
                "職場人際需要額外經營。你和同事或主管之間可能出現理解上的落差，多確認、多溝通能避免大部分問題。不要用情緒去處理工作上的衝突，冷靜幾天再回應，結果往往比當下反應好得多。"
            ],
            "kyo": [
                "今年的職場不適合主動出擊。不要在這一年跳槽、要求大幅加薪、或者跟主管正面衝突。先穩住現有位置，把手上的工作做到不出錯就好。如果被裁員或被迫轉換，不要急著做決定，給自己至少兩週的冷靜期再行動。低潮年做的職涯決定很容易後悔。",
                "工作上遇到不公平的事情，今年不是正面交鋒的時機，但可以把它當成觀察和學習的素材。記錄下來，想清楚你真正在意的是什麼、你希望怎麼被對待。同時，趁這段時間補強自己的技能、整理作品集、維護關鍵人脈。低谷年做的準備工作，會在下一波機會來臨時直接變現。"
            ],
            "neutral": [
                "事業表現取決於你自己的投入程度。今年不會有天上掉下來的好機會，但也不會有無法預見的絆腳石。制定清晰的季度目標，踏實推進即可。最適合用來累積技能、建立長期競爭力、深化專業領域的知識。",
                "今年的職場環境穩定，沒有太多外力干擾。利用這段平靜期做一些需要專注的事情：考證照、寫專業文章、整理作品集。這些短期看不到回報的投入，會在未來的某個時刻突然派上用場。"
            ]
        },
        "love": {
            "same": [
                "感情方面，同頻年份讓你對自己想要什麼更清楚。不管是單身還是有伴，你都會更誠實地面對內心需求。單身者今年容易遇到價值觀相近的人，不用急著找，但要讓自己出現在對的場合。有伴侶的人關係穩定中帶著一點舒適感，安排一些共同的新體驗來增添火花。",
                "感情裡的你今年特別有魅力，因為同元素加持讓你更自信、更從容。這種由內而外的吸引力是最持久的。單身者如果遇到喜歡的人，主動出擊的成功率高。有伴的人雙方默契增加，適合討論一些關於未來的規劃。"
            ],
            "generating": [
                "感情運勢很好，桃花旺但不亂。今年遇到的人品質比較高，能讓你有「終於遇到對的人」的感覺。不過別因為太順利就省略了解對方的過程，好的感情需要時間來確認。有伴的人適合規劃婚事或者一起完成一件有意義的事。",
                "今年在感情中你會感覺被支持和理解。另一半比平時更願意配合你，朋友也會主動幫你介紹對象。善用這股好運，但也要記得付出。感情是雙向的，你接收到的善意需要以另一種形式回饋。"
            ],
            "weakening": [
                "感情上今年需要多花心思經營。你可能因為工作忙碌而忽略了另一半，或者因為精力有限而對社交失去興趣。但感情不是你忙就能暫停的東西，每週至少留出一段不被打擾的時間給重要的人。單身者不用急著找對象，先把自己的狀態調整好再說。",
                "有伴的人今年要注意溝通品質。你可能因為累而說話比較直接，對方不一定能理解你只是疲倦而不是不在乎。有話好好說，用文字表達不了的東西就當面談。關係裡偶爾示弱不是認輸，是讓對方知道你需要他。"
            ],
            "conflicting": [
                "感情方面今年有些波折。可能遇到價值觀衝突、生活節奏不合拍、或者對未來的期待不同。這些問題藏在水面下很久了，今年它們浮上來反而是好事。正面處理比假裝沒看到好。不管結果如何，誠實面對是唯一的出路。",
                "單身的人今年的桃花帶有一點試煉的意味。你遇到的人可能讓你心動但又讓你猶豫，那種矛盾感其實是在幫你釐清你真正需要的是什麼類型。不急著確定關係，多觀察、多了解，等張力過去之後再做決定。"
            ],
            "kyo": [
                "感情上今年最好的策略是「不折騰」。盡量不要在這一年做感情裡的重大決定——低潮期的情緒容易影響你看待關係的方式，等心境穩定之後再回頭評估會更客觀。有伴的人就好好相處，吵架的時候先離開現場，冷靜之後再談。單身的人不用急，把注意力放在照顧自己上面，狀態好了自然會吸引對的人。",
                "今年感情裡最需要的是一個讓你安心的存在。不一定是戀人，可以是家人、摯友、任何讓你在身邊就覺得世界沒那麼糟的人。主動跟這些人保持聯繫，累的時候打個電話、週末約出來吃頓飯。不要自己扛，也不要覺得麻煩別人丟臉。有伴的人今年把另一半當隊友而不是觀眾，一起面對比各自承擔有效得多。"
            ],
            "neutral": [
                "感情上今年不溫不火，適合穩定經營。不會有戲劇化的轉折，但會有日常相處裡的小確幸。有伴的人適合把注意力放回基本功——好好吃飯、好好聊天、好好休息。單身者不用焦慮，但也別把自己封閉起來，保持正常的社交頻率即可。",
                "今年感情的主題是「品質大於數量」。深度的交流比頻繁的約會有價值，了解一個人的內在比外在條件更重要。如果你想要一段長久的關係，今年的穩定環境非常適合慢慢培養。"
            ]
        },
        "health": {
            "same": [
                "健康方面，同元素年份讓你的身體狀況基本穩定。你的體質和今年的能量頻率合拍，不容易出大問題。但「穩定」不等於「不用管」，正因為今年沒什麼警訊，很容易忽略那些緩慢累積的隱患。維持規律的運動、均衡的飲食，安排一次全面的健康檢查。預防永遠比治療便宜。",
                "今年身體底子好，適合建立長期的健康習慣。不管是開始跑步、學游泳、還是調整飲食結構，今年養成的好習慣比較容易堅持下去。不要等到身體發出警告才行動，趁狀態好的時候投資健康。"
            ],
            "generating": [
                "健康運佳，今年是改善體質的好時機。如果你想減重、增肌、或者改善某個長期的小毛病，今年的效果會比較明顯。身體的恢復力也比較好，即使偶爾熬夜或作息不正常，也能比較快恢復。但別因此就糟蹋自己。",
                "今年的精力充沛，做什麼都不太容易累。但這股好狀態需要用正確的方式運用——規律運動把多餘的能量消耗掉，而不是用加班來填滿。適合嘗試一項新的運動，或者把運動頻率從一週三次提高到四五次。"
            ],
            "weakening": [
                "健康是今年最需要關注的項目。能量外流讓你比平時更容易疲勞，免疫力可能也稍微下降。感冒、過敏、腸胃不適這些小問題可能比往年頻繁。強烈建議每天保證七到八小時的睡眠，減少咖啡因和酒精的攝取。不要硬撐，身體的信號比你的意志力準確得多。",
                "今年你的身體在提醒你欠的債。過去幾年高強度運轉累積的疲勞可能在今年集中爆發。不要害怕，這是身體在自我修復。配合身體的需求，該休息就休息、該看醫生就看醫生。養好今年，未來才有本錢衝刺。"
            ],
            "conflicting": [
                "健康上今年要多留心壓力對身體的影響。張力年份帶來的焦慮可能導致失眠、頭痛、肌肉緊繃、或者消化不良。找到適合你的紓壓方式是今年的必修課——不管是運動、冥想、還是單純找人聊天。不要讓壓力在體內累積到爆炸才處理。",
                "今年容易因為趕時間而忽略身體警訊。養成每天用五分鐘掃描身體狀態的習慣：哪裡痠、哪裡緊、睡得夠不夠、吃得好不好。小問題及時處理，就不會演變成大問題。安排上半年做一次健檢，及早發現及早處理。"
            ],
            "kyo": [
                "健康是今年需要比平時更主動關注的項目。低潮年的身體恢復速度會比較慢，所以預防比治療更重要。每天睡滿七小時、三餐正常吃、每週至少走路三十分鐘——這些基本功就是你最好的護身符。如果出現不舒服的症狀，早點去看醫生，不要拖。今年安排一次完整健檢，有問題及早處理，沒問題就安心。把身體照顧好，其他事情才有底氣去面對。",
                "今年的壓力會直接反映在身體上。失眠、偏頭痛、腸胃不適、莫名的疲倦感，這些都是身體在幫你喊停。不要硬撐，累了就休息、扛不住就求助。減少咖啡因和酒精的攝取，它們短期提神但長期消耗你的修復能力。找到一個能讓你放鬆的固定儀式：泡澡、散步、聽音樂、什麼都好，每天給自己半小時完全不用想事情的時間。身體撐住了，其他的才有談的餘地。"
            ],
            "neutral": [
                "健康狀態平穩，今年適合做體質管理。沒有特別需要擔心的大問題，但也不要因此就放縱生活作息。把健康管理視為一種長期投資，今年投入的每一分努力都會在未來幾年得到回報。建立固定的運動時間、改善飲食結構、保持充足的睡眠。",
                "今年的身體不會給你太多警告，所以你需要主動去關心它。定期量體重、記錄睡眠品質、觀察皮膚和精神狀態的變化。這些日常的微調比一年做一次健檢更能即時反映你的健康狀況。"
            ]
        },
        "wealth": {
            "same": [
                "財運方面，同元素年份你對金錢的感知力更強。你能比平時更精準地判斷哪些錢該花、哪些錢該存、哪些投資值得跟。適合重新審視你的財務結構——保險夠不夠、緊急預備金有沒有三到六個月的生活費、投資組合是否需要調整。用你今年特別敏銳的財務直覺，做一些長期有利的理財決策。",
                "今年的財務狀態穩定，沒有太大的起伏。收入和支出都在預期範圍內，不會有突如其來的大額開支或意外之財。這種穩定期最適合打好理財基礎：清掉小額負債、建立自動存款機制、學一點基礎的投資知識。"
            ],
            "generating": [
                "財運旺盛，今年有不錯的增加收入的機會。可能是加薪、獎金、副業收入、或者投資回報。但「有機會」不等於「自動到手」，你需要主動爭取——該談薪資就談、該爭取專案獎金就爭取。同時控制花費，別因為賺得多就花得多，把多出來的收入存下來或者投入增值資產。",
                "今年的錢會從意想不到的管道流進來。保持開放心態，不要拒絕看起來不太傳統的賺錢機會。當然，天上不會掉餡餅，如果一個機會好到不真實，花時間確認清楚再行動。正當管道的機會今年確實比較多。"
            ],
            "weakening": [
                "財務方面今年要做好「花多存少」的心理準備。不是你會虧錢，而是你需要花錢的地方比預期多——可能是維修費、醫療費、人情費、或者不得不做的升級投資。提前留出一筆預備金，遇到必要開支時才不會手忙腳亂。能省的地方省，不能省的地方不要省。",
                "今年不適合做高風險的投資或大額的衝動消費。把注意力放在「不虧」上面，穩穩地守住已有的資產比追求高報酬更重要。如果必須做財務決策，找專業的人諮詢，不要靠感覺。"
            ],
            "conflicting": [
                "財務上可能有一些意外的波動。你以為穩賺的投資可能出現回檔、預期的收入可能延遲入帳、突然冒出一筆計畫外的開支。應對的方式是：不要把所有雞蛋放在一個籃子裡，保持財務的靈活性。手邊永遠留一筆三到六個月的生活費，讓自己有餘裕應對變化。",
                "今年在花錢之前多想三秒。衝動消費和衝動投資是張力年份最容易犯的錯。看到好東西先放進購物車等兩天、聽到好機會先記下來研究一週。過了冷靜期還覺得值得的，再花錢也不遲。"
            ],
            "kyo": [
                "財務上今年的核心策略是「穩健」。盡量不借錢、不做沒有把握的投資、遇到重大財務決定先多方確認再行動。低潮年的環境干擾比較多，容易讓人做出衝動的金錢決定，多給自己一點思考時間不會吃虧。手邊的現金留越多越好，至少準備六個月的生活費當安全墊。如果已經有投資部位，不要加碼也不要恐慌賣出，維持現狀就好。今年的目標不是賺錢，是穩穩守住。",
                "今年可能會遇到一些意料之外的開支：車子壞了、家電要換、身體需要治療、朋友開口借錢。提前把預備金準備好，遇到的時候才不慌。能不花的錢就不花，能晚付的帳就晚付。如果有人跟你推銷保險、基金、或任何理財商品，一律說「我再想想」然後放到明年再決定。低谷年守住荷包比什麼都重要。"
            ],
            "neutral": [
                "財務狀態平穩，沒有大起大落。這種環境最適合做長期理財規劃——定期定額投資、重新配置資產比例、或者開始研究一個你一直想了解的投資工具。不要期待今年有爆發性的財務增長，但持續穩定的累積到年底也是一筆可觀的數目。",
                "今年的財運中規中矩，收入跟付出成正比。想多賺就得多做，沒有捷徑。把注意力放在提升自己的賺錢能力上面——技能升級帶來的加薪、作品集帶來的副業機會——這些投入的回報比任何理財技巧都可靠。"
            ]
        }
    }

    # 角色別相處建議：根據關係類型提供不同身份的互動指南
    ROLE_DESCRIPTIONS = {
        "eishin": {
            "colleague": "栄親在職場上是最強的搭檔組合。你們天然地互相加持，一個人的提案被另一個人補充之後總是變得更完整。分工的時候各自負責擅長的部分，彙整時反而比一個人全做更快更好。如果有機會合作專案，不要猶豫直接組隊。唯一要注意的是功勞的歸屬——因為你們太容易合作成功，有時候會忘了釐清各自的貢獻，事先講清楚比事後爭論好。",
            "friend": "栄親的友誼有一種自然而然的滋養感，跟對方聊完天之後你會覺得被充電了。你們適合一起做有建設性的事——一起運動、一起學東西、一起參加活動。這種朋友不會讓你越來越懶，反而是在對方身邊你會不自覺地想變得更好。遇到人生重大決定的時候，聽聽對方的想法，栄親朋友給的建議通常特別有參考價值。",
            "lover": "栄親在感情中是越相處越舒服的類型。初識時可能不是一見鍾情的驚天動地，但日子一長你會發現這個人讓你的生活全面升級。彼此的價值觀契合度高，生活習慣也容易磨合。重點是兩個人都要有各自的舞台——如果只有一方在成長，另一方容易產生不安全感。安排定期的共同活動和各自的獨處時間，維持健康的距離。",
            "family": "栄親關係的家人相處起來最輕鬆。你們之間的理解是天然的，很多事不需要解釋對方就能體會。作為親子關係，父母和孩子之間很少有真正的衝突，因為雙方都願意替對方著想。作為兄弟姐妹，你們是對方最強的後盾。家庭中如果有重大決策需要討論，你們之間的溝通效率最高。"
        },
        "gyotai": {
            "colleague": "業胎關係的同事之間有一種說不出的默契，有時候對方還沒開口你就知道他想表達什麼。合作的時候可以省掉很多溝通成本，工作節奏也容易對上。不過要注意一點：你們太熟悉彼此的思考模式，有可能陷入同溫層效應。遇到需要創新的時候，主動引入第三方的觀點來打破慣性思維。",
            "friend": "業胎的朋友像是認識了很多年的老友，即使很久沒聯絡，見面之後馬上回到上次離開的地方。你們之間不需要客套，可以直接說真話而不擔心傷感情。這種朋友不多，珍惜這份默契。但也因為太舒服了，有時候會忽略主動關心對方的近況，定期聯繫不要讓距離把默契消磨掉。",
            "lover": "業胎在感情中有一種宿命般的吸引力，認識的時候常有「這個人我好像在哪裡見過」的感覺。交往之後會發現很多價值觀、生活習慣甚至小癖好都相似。這種相似讓你們相處起來極度自在，但長期來說需要刻意製造一些新鮮感。一起嘗試新的興趣、去沒去過的地方旅行、突破日常的模式，讓這段關係保持活力。",
            "family": "業胎關係的家人之間有種深層的連結感，家庭聚會的時候你會發現跟這位家人特別聊得來。即使生活方式不同，你們對事情的看法往往出奇一致。如果需要一個能真正理解你的家人傾訴心事，這位業胎家人是首選。他們的建議通常最切合你的實際狀況，因為他們本能地懂你在想什麼。"
        },
        "mei": {
            "colleague": "命宿關係的同事就像照鏡子，你們的工作風格和思維方式極為相似。這有好有壞——好處是溝通零障礙，壞處是盲點也一模一樣。合作的時候要特別注意互相提醒對方看不到的地方，不要以為對方想到了就等於自己也不用擔心。分工的時候盡量負責不同的環節，避免重複勞動。",
            "friend": "命宿的朋友是最了解你的人，因為他們本質上跟你是同一類人。這意味著你最好的時候他們看得到，你最差的時候他們也瞞不過。這種友誼需要高度的自我接納——能接受對方身上那些跟自己一樣的缺點，才能真正享受這段關係。你們適合互相當對方的鏡子，坦誠地交換對彼此的觀察。",
            "lover": "命宿之間的感情帶有強烈的「終於被完全理解」的感受，對方的一個眼神你就知道他的情緒。但這份理解有時候是把雙面刃——因為太了解對方，吵架的時候也知道怎麼說最傷人。感情經營的重點是學會在衝突中控制情緒，不要利用對對方的了解來攻擊。你們需要約定好底線，有些話知道也不能說出口。",
            "family": "命宿的家人之間像是同一個模子刻出來的，性格、脾氣、甚至生活習慣都驚人地相似。相處起來很自在但也容易針鋒相對，因為對方身上你最看不慣的特質其實就是你自己的翻版。學會在這面鏡子前保持幽默感，笑著承認「你看，我們果然一樣」比互相指責有效得多。"
        },
        "yusui": {
            "colleague": "友衰在工作上需要注意能量的流向。友方在合作中通常主導節奏，衰方則容易被帶著走。如果你是友方，記得適時詢問對方的意見而不是一個人做決定。如果你是衰方，該表達的立場不要忍著不說。兩個人的能力其實差不多，只是互動模式容易形成固定角色，刻意打破這個慣性會讓合作更均衡。",
            "friend": "友衰的友誼通常很舒服，在一起時間過得特別快。但長期下來要注意是不是總在做一樣的事——一起吃飯、一起追劇、一起抱怨卻都不行動。好朋友應該互相推一把，偶爾提議做點新的事情，或者約對方一起報名課程。讓這段友誼不只是安慰劑，也是成長的觸媒。",
            "lover": "友衰的感情初期非常甜蜜，因為相處的舒適度很高。但進入穩定期之後，如果兩個人都不主動製造變化，容易陷入「哪裡都好但好像少了點什麼」的狀態。解方是設定共同目標：一起存錢旅行、一起健身、一起學新技能。有目標在前面拉著，你們會走得更有方向感。",
            "family": "友衰關係的家人相處融洽但容易形成依賴。如果你是友方的角色，家中的決定很多會由你主導，但記得這不代表衰方沒有想法，而是他們習慣讓你先說。主動問對方的意見，讓每個家人都有表達的空間。家庭中的能量越均衡，所有人的狀態都會越好。"
        },
        "ankai": {
            "colleague": "安壊在職場上的互動帶有競爭性的張力。壊方可能不自覺地表現得比較強勢，安方則會感受到壓力。如果能把這種張力引導到正面的競爭上，反而能激發出雙方最好的表現。關鍵是保持專業距離，把注意力放在工作成果上。私下建立信任也很重要——找機會在輕鬆的場合增加了解，減少不必要的防備心。",
            "friend": "安壊的友誼刺激但消耗能量。你們在一起的時候不無聊，但結束之後其中一方可能會覺得累。維持這段友誼的方法是控制強度和頻率——不需要天天見面，每隔一段時間聚一次反而每次都很精彩。也要留意權力動態有沒有失衡，健康的友誼不應該讓任何一方長期覺得委屈。",
            "lover": "安壊的愛情充滿激情和戲劇性。壊方的強勢在戀愛初期會讓安方覺得很有安全感，但時間一長如果壊方不學會收斂，安方會累積不滿。雙方必須在感情中建立對等的溝通機制：定期討論彼此的感受、設定不可逾越的底線、在衝突時給對方冷靜的空間。這段感情的天花板很高，但維護成本也不低。",
            "family": "安壊的家庭關係最需要有意識地管理。壊方在家中往往比較有主導權，安方容易委曲求全。如果是親子關係，壊方的家長要特別注意不要過度控制，安方的孩子需要更多被肯定和被聽到。營造一個每個人都能安全表達的家庭氛圍，比什麼都重要。衝突不可避免，但衝突後的修復才是維繫關係的關鍵。"
        },
        "kisei": {
            "colleague": "危成在工作上是互補型的組合。成方負責規劃和執行，危方負責創意和突破。初期你們可能對彼此的工作方式感到困惑：「為什麼他要這樣做？」但磨合之後會發現這種差異其實是最大的資產。給彼此足夠的空間用各自的方式做事，在結果上對齊就好。過程中的差異不是問題，是互補。",
            "friend": "危成的友誼需要時間發酵。一開始你們可能覺得聊不到一起去，但某次深入的對話之後你會突然理解對方的世界觀——原來他看事情的角度跟你完全不同，卻同樣有道理。這種朋友的價值在於拓寬你的視野，跟你不一樣的觀點才能讓你看到盲點。比起聊天，一起做事更能加深你們的情誼。",
            "lover": "危成的感情前期需要比較多耐心，因為你們的生活節奏、溝通方式甚至審美偏好都不太一樣。但熬過磨合期之後，你們會成為非常穩固的伴侶。關鍵是接受對方跟你不同不代表他是錯的。學會欣賞差異而不是試圖改變對方，你們的感情會越磨越亮。定期安排約會夜，回到初識時那種好奇地探索對方的狀態。",
            "family": "危成的家庭關係需要雙方多練習理解力。你們看待事情的方式不同，容易因為觀念差異產生摩擦。但這種差異也讓家庭的視角更全面——做重大決定的時候，聽完所有人的意見通常能得到最平衡的結論。家庭聚會中不要急著否定對方的看法，先聽完再表達自己的想法，溝通品質會提升很多。"
        }
    }

    def _shift_level(self, level: str, direction: int) -> str:
        """
        等級位移

        Args:
            level: 當前等級 key (daikichi/kichi/chukichi/shokyo/kyo)
            direction: +1 = 提升一級, -1 = 降低一級

        Returns:
            位移後的等級 key（到頂/到底不再移）
        """
        idx = self.FORTUNE_LEVELS.index(level)
        # FORTUNE_LEVELS index 0 = 最佳(daikichi), 4 = 最差(kyo)
        # direction +1 表示提升（往 index 小的方向）
        new_idx = max(0, min(len(self.FORTUNE_LEVELS) - 1, idx - direction))
        return self.FORTUNE_LEVELS[new_idx]

    def _determine_daily_level(
        self, relation_type: str, ryouhan: Optional[dict],
        special_day_type: Optional[str]
    ) -> tuple[str, str, int]:
        """
        核心等級判定流程（原典邏輯）

        1. 本命宿 x 當日宿 → RELATION_LEVEL_MAP → base_level
        2. 凌犯判定 → RYOUHAN_LEVEL_FLIP
        3. 特殊日 → _shift_level(±1)
        4. 六害宿 → 不影響等級（warning only）

        Args:
            relation_type: 宿曜關係 (eishin/yusui/ankai/...)
            ryouhan: 凌犯資料（None = 不在凌犯期間）
            special_day_type: 特殊日類型 (kanro/rasetsu/kongou/None)

        Returns:
            (final_level, base_level, overflow_bonus) — 最終等級、原始等級、
            溢出加分（等級已在極值但特殊日仍有加持時的額外分數）
        """
        # Step 1: 基礎等級
        base_level = self.RELATION_LEVEL_MAP.get(relation_type, "chukichi")
        level = base_level

        # Step 2: 凌犯翻轉
        if ryouhan:
            level = self.RYOUHAN_LEVEL_FLIP[level]

        # Step 3: 特殊日位移
        overflow_bonus = 0
        if special_day_type:
            prev_level = level
            if special_day_type == "kanro":
                if ryouhan:
                    level = self._shift_level(level, -1)  # 凌犯中甘露 → 降級
                else:
                    level = self._shift_level(level, +1)  # 正常甘露 → 升級
            elif special_day_type == "rasetsu":
                if ryouhan:
                    level = self._shift_level(level, +1)  # 凌犯中羅刹 → 升級
                else:
                    level = self._shift_level(level, -1)  # 正常羅刹 → 降級
            elif special_day_type == "kongou":
                # 金剛峯日「宜作一切降伏法」(T21 p.398b-c)
                # 原典凌犯規則(p.391b-c)概括性適用所有日，金剛峯日亦遵循吉凶逆轉
                if ryouhan:
                    level = self._shift_level(level, -1)  # 凌犯中金剛峯 → 降級
                else:
                    level = self._shift_level(level, +1)  # 正常金剛峯 → 升級

            # 等級已在極值無法位移時，特殊日加持轉為分數溢出
            # 凌犯中不設溢出（凌犯已是極端情況，特殊日逆轉後不再疊加溢出）
            if level == prev_level and special_day_type in ("kanro", "kongou") and not ryouhan:
                overflow_bonus = 10  # 甘露/金剛峯在大吉日的額外加持
            elif level == prev_level and special_day_type == "rasetsu" and not ryouhan:
                overflow_bonus = -10  # 羅刹在凶日的額外壓制

        return level, base_level, overflow_bonus

    def calculate_daily_fortune(self, birth_date: date, target_date: date) -> dict:
        """
        計算每日運勢

        使用三九秘法：根據「本命宿」與「當日宿」的關係決定運勢基調

        Args:
            birth_date: 出生日期
            target_date: 要查詢的日期

        Returns:
            每日運勢資料
        """
        import random

        fortune_data = self._load_fortune_data()
        mansion = self.get_mansion(birth_date)
        user_element = mansion["element"]
        user_index = mansion["index"]

        # === 核心修正：計算「當日宿」===
        # 使用修正後宿位，避免大月邊界重複
        lunar_y, lunar_m, lunar_d, _ = self.solar_to_lunar(target_date)
        day_mansion_index = self._get_corrected_mansion_index(target_date)
        day_mansion = self.mansions_data[day_mansion_index]

        # === 三九秘法：計算本命宿與當日宿的關係 ===
        mansion_relation = self.get_relation_type(user_index, day_mansion_index)
        mansion_relation_type = mansion_relation["type"]

        # === 七曜資訊 ===
        weekday = target_date.weekday()
        jp_weekday = (weekday + 1) % 7
        day_info = fortune_data["weekday_elements"][str(jp_weekday)]
        day_element = day_info["element"]

        # === 元素相性（次要因素，用於分類微調） ===
        element_relation_type, element_bonus = self._calc_fortune_element_relation(
            user_element, day_element
        )
        element_adjustment = int(element_bonus / 2)  # ±20→±10, ±10→±5, ±5→±2
        element_desc = fortune_data["element_relations"].get(
            element_relation_type,
            fortune_data["element_relations"]["neutral"]
        )["description"]

        # === 甘露日/金剛峯日/羅刹日判定 ===
        special_day_key = (jp_weekday, day_mansion_index)
        special_day_type = self.SPECIAL_DAY_MAP.get(special_day_key)

        # === 凌犯期間判定 ===
        ryouhan = self.check_ryouhan_period(target_date)

        # === 等級優先制：核心判定 ===
        final_level, base_level, overflow_bonus = self._determine_daily_level(
            mansion_relation_type, ryouhan, special_day_type
        )

        # 等級 → 顯示分數（含特殊日溢出加分）
        level_score = self.LEVEL_DISPLAY_SCORE[final_level]
        overall_score = max(30, min(100, level_score + element_adjustment + overflow_bonus))

        # === 計算各項運勢（從等級分數衍生 + 分類親和微調） ===
        def calc_category_score(category: str) -> int:
            cat_data = fortune_data["fortune_categories"][category]
            cat_bonus = 3 if user_element in cat_data["favorable_elements"] else 0
            day_bonus = 2 if day_element in cat_data["favorable_elements"] else 0
            return max(30, min(100, overall_score + cat_bonus + day_bonus))

        career_score = calc_category_score("career")
        love_score = calc_category_score("love")
        health_score = calc_category_score("health")
        wealth_score = calc_category_score("wealth")

        # === 六害宿判定（凌犯期間中才生效，warning flag 不影響等級） ===
        rokugai = None
        if ryouhan:
            rokugai_list = self.get_rokugai_suku(user_index)
            for rg in rokugai_list:
                if rg["mansion_index"] == day_mansion_index:
                    rokugai = {
                        "active": True,
                        "name": rg["name"],
                        "name_reading": rg["name_reading"],
                        "severity": rg["severity"],
                        "description": f"凌犯期間中の六害宿「{rg['name']}」に当たります。本命宿との関係で特に注意が必要な日です。"
                    }
                    break

        # === 特殊日資料組裝 ===
        special_day = None
        if special_day_type:
            special_day = dict(self.SPECIAL_DAY_INFO[special_day_type])
            special_day["type"] = special_day_type
            if ryouhan:
                if special_day_type in ("kanro", "kongou"):
                    special_day["ryouhan_reversed"] = True
                    special_day["original_level"] = special_day["level"]
                    special_day["level"] = "凶（凌犯逆轉）"
                elif special_day_type == "rasetsu":
                    special_day["ryouhan_reversed"] = True
                    special_day["original_level"] = special_day["level"]
                    special_day["level"] = "吉（凌犯逆轉）"
                else:
                    special_day["ryouhan_reversed"] = False
            else:
                special_day["ryouhan_reversed"] = False

        # === 三期サイクル ===
        sanki = self.get_sanki_cycle(user_index, day_mansion_index)

        # === 各項描述（根據等級選擇，非分數門檻） ===
        def get_category_desc(category: str, ryouhan_active: bool = False) -> dict:
            """回傳 {"zh": "...", "ja": "..."} 或 {"zh": "..."}"""
            random.seed(f"{birth_date.isoformat()}{target_date.isoformat()}cat_{category}")
            if ryouhan_active:
                descs = self.RYOUHAN_CATEGORY_DESCRIPTIONS.get(category, {})
                desc_key = self.RYOUHAN_DESC_KEY.get(final_level, "mid_reversal")
                pool = descs.get(desc_key, [{"zh": ""}])
                return random.choice(pool)
            else:
                descs = self.DAILY_CATEGORY_DESCRIPTIONS.get(category, {})
                desc_key = self.LEVEL_DESC_KEY.get(final_level, "fair")
                pool = descs.get(desc_key, [""])
                return {"zh": random.choice(pool)}

        is_ryouhan_active = ryouhan is not None
        career_descs = get_category_desc("career", is_ryouhan_active)
        love_descs = get_category_desc("love", is_ryouhan_active)
        health_descs = get_category_desc("health", is_ryouhan_active)
        wealth_descs = get_category_desc("wealth", is_ryouhan_active)
        career_desc = career_descs["zh"]
        love_desc = love_descs["zh"]
        health_desc = health_descs["zh"]
        wealth_desc = wealth_descs["zh"]
        career_desc_ja = career_descs.get("ja", "")
        love_desc_ja = love_descs.get("ja", "")
        health_desc_ja = health_descs.get("ja", "")
        wealth_desc_ja = wealth_descs.get("ja", "")

        # === 選擇建議（根據等級） ===
        random.seed(f"{birth_date.isoformat()}{target_date.isoformat()}advice")
        advice_key = self.LEVEL_ADVICE_KEY.get(final_level, "neutral")
        advice_list = fortune_data["daily_advice"].get(advice_key, fortune_data["daily_advice"]["neutral"])
        advice = random.choice(advice_list)

        # === 多因素交叉分析 ===
        compound_analysis = self._analyze_compound_factors(
            ryouhan, special_day_type, mansion_relation_type, sanki, rokugai
        )

        # === 幸運物品（每日動態計算） ===
        lucky = fortune_data["lucky_items"]

        # 方位：以當日宿元素為主，大吉日回歸本命方位
        if mansion_relation_type in ("eishin", "gyotai", "mei"):
            lucky_direction = lucky["directions"].get(user_element, lucky["directions"]["土"])
        else:
            lucky_direction = lucky["directions"].get(day_mansion["element"], lucky["directions"]["土"])

        # 顏色：以七曜元素為主，同元素日使用本命色
        if element_relation_type == "same":
            lucky_color = lucky["colors"].get(user_element, lucky["colors"]["土"])
        else:
            lucky_color = lucky["colors"].get(day_element, lucky["colors"]["土"])

        # 數字：當日宿 index + 農曆日推導，每天不同
        num1 = (day_mansion_index % 9) + 1
        num2 = ((day_mansion_index + lunar_d) % 9) + 1
        if num2 == num1:
            num2 = (num2 % 9) + 1
        lucky_numbers = [num1, num2]

        return {
            "date": target_date.isoformat(),
            "weekday": {
                "name": day_info["name"],
                "reading": day_info["reading"],
                "element": day_element,
                "planet": day_info["planet"]
            },
            "day_mansion": {
                "name_jp": day_mansion["name_jp"],
                "reading": day_mansion["reading"],
                "element": day_mansion["element"],
                "index": day_mansion_index,
                "day_fortune": day_mansion.get("day_fortune", {})
            },
            "your_mansion": {
                "name_jp": mansion["name_jp"],
                "reading": mansion["reading"],
                "element": user_element,
                "index": mansion["index"],
                "personality_classic": mansion.get("personality_classic", ""),
                "career_classic": mansion.get("career_classic", "")
            },
            "mansion_relation": {
                "type": mansion_relation_type,
                "name": self.DAILY_FORTUNE_RELATION_NAMES.get(mansion_relation_type, mansion_relation["name"]),
                "name_jp": mansion_relation.get("name_jp", mansion_relation["name"]),
                "reading": mansion_relation.get("reading", ""),
                "description": self._seeded_choice(f"{birth_date.isoformat()}{target_date.isoformat()}rel_desc", self.DAILY_FORTUNE_DESCRIPTIONS.get(mansion_relation_type, [mansion_relation["description"]])),
                "description_classic": mansion_relation.get("description_classic", ""),
                "description_ja": mansion_relation.get("description_ja", "")
            },
            "element_relation": {
                "type": element_relation_type,
                "description": element_desc
            },
            "fortune": {
                "level": final_level,
                "level_name": self.LEVEL_NAMES[final_level]["zh"],
                "level_name_ja": self.LEVEL_NAMES[final_level]["ja"],
                "level_reading": self.LEVEL_NAMES[final_level]["reading"],
                "base_level": base_level,
                "overall": overall_score,
                "career": career_score,
                "love": love_score,
                "health": health_score,
                "wealth": wealth_score,
                "career_desc": career_desc,
                "love_desc": love_desc,
                "health_desc": health_desc,
                "wealth_desc": wealth_desc,
                "career_desc_ja": career_desc_ja,
                "love_desc_ja": love_desc_ja,
                "health_desc_ja": health_desc_ja,
                "wealth_desc_ja": wealth_desc_ja,
                "ryouhan_active": ryouhan is not None,
                "ryouhan_warning": "凌犯期間中，吉凶判斷可能與平時相反。表面順遂之事暗藏風險，表面困難之事反有轉機。重大決策宜延後。原典記載化解之法為「入灌頂及護摩，並修諸功德」。" if ryouhan else None,
                "ryouhan_warning_ja": "凌犯期間中のため、吉凶の判断が通常と逆転する可能性があります。原典には「灌頂に入り護摩を作し、並びに諸の功徳を修す」が禳いの法と記されています。重要な決断は延期をお勧めします。" if ryouhan else None,
                "effective_interpretation": self.LEVEL_INTERPRETATION.get(final_level, "neutral")
            },
            "advice": advice,
            "lucky": {
                "direction": lucky_direction["direction"],
                "direction_reading": lucky_direction["reading"],
                "color": lucky_color["color"],
                "color_reading": lucky_color["reading"],
                "color_hex": lucky_color["hex"],
                "numbers": lucky_numbers
            },
            "special_day": special_day,
            "ryouhan": ryouhan,
            "rokugai": rokugai,
            "sanki": sanki,
            "compound_analysis": compound_analysis
        }

    def calculate_monthly_fortune(self, birth_date: date, year: int, month: int) -> dict:
        """
        計算每月運勢

        Args:
            birth_date: 出生日期
            year: 年份
            month: 月份 (1-12)

        Returns:
            每月運勢資料
        """
        import random
        from datetime import timedelta

        fortune_data = self._load_fortune_data()
        mansion = self.get_mansion(birth_date)
        user_index = mansion["index"]
        user_element = mansion["element"]

        # 取得該月的月宿（使用月宿傍通曆）
        mid_date = date(year, month, 15)
        _, lunar_month_for_mansion, _, _ = self.solar_to_lunar(mid_date)
        month_mansion_index = self.MONTH_START_MANSION.get(lunar_month_for_mansion, 0)
        month_mansion = self.mansions_data[month_mansion_index]
        month_mansion_elem = month_mansion["element"]

        # 本命宿 vs 月宿關係 → 等級映射
        relation = self.get_relation_type(user_index, month_mansion_index)
        month_level = self.RELATION_LEVEL_MAP.get(relation["type"], "chukichi")
        base_score = self.LEVEL_DISPLAY_SCORE[month_level]

        # 月份主題加成
        month_theme = fortune_data["monthly_themes"].get(str(month), {})
        theme_element = month_theme.get("element_boost", "土")
        if user_element == theme_element:
            base_score = min(100, base_score + 5)

        # 計算該月天數
        first_day = date(year, month, 1)
        if month == 12:
            next_month_first = date(year + 1, 1, 1)
        else:
            next_month_first = date(year, month + 1, 1)
        days_in_month = (next_month_first - first_day).days

        # 收集所有日運資料（凌犯/特殊日/暗黒統計）
        all_daily = []
        ryouhan_count = 0
        special_days_in_month = []
        dark_week_count = 0

        for d in range(days_in_month):
            day_date = first_day + timedelta(days=d)
            daily_fortune = self.calculate_daily_fortune(birth_date, day_date)

            is_ryouhan = daily_fortune.get("ryouhan") is not None
            special_day = daily_fortune.get("special_day")
            is_dark = daily_fortune.get("sanki", {}).get("is_dark_week", False)

            if is_ryouhan:
                ryouhan_count += 1
            if special_day:
                special_days_in_month.append({
                    "date": day_date.isoformat(),
                    "type": special_day.get("type", ""),
                    "name": special_day.get("name", "")
                })
            if is_dark:
                dark_week_count += 1

            sanki = daily_fortune.get("sanki", {})
            all_daily.append({
                "date": day_date.isoformat(),
                "weekday": daily_fortune["weekday"]["name"],
                "score": daily_fortune["fortune"]["overall"],
                "special_day": special_day.get("name") if special_day else None,
                "ryouhan_active": is_ryouhan,
                "is_dark_week": is_dark,
                "sanki_period_index": sanki.get("period_index", 1),
                "sanki_period": sanki.get("period", "躍動の週"),
                "sanki_day_in_period": sanki.get("day_in_period", 1),
                "sanki_day_type": sanki.get("day_type", ""),
            })

        # 月整體分數 = 每日分數平均（與週分數算法一致）
        ryouhan_ratio = ryouhan_count / days_in_month if days_in_month > 0 else 0
        daily_avg = round(sum(d["score"] for d in all_daily) / len(all_daily)) if all_daily else 60
        base_score = max(35, min(100, daily_avg))

        # 從平均分數反推月等級
        if base_score >= 90:
            month_level = "daikichi"
        elif base_score >= 75:
            month_level = "kichi"
        elif base_score >= 60:
            month_level = "chukichi"
        elif base_score >= 45:
            month_level = "shokyo"
        else:
            month_level = "kyo"

        # 各項運勢（基於元素親和，非隨機數）
        def calc_monthly_category(category: str) -> int:
            cat_data = fortune_data["fortune_categories"][category]
            cat_bonus = 8 if user_element in cat_data["favorable_elements"] else 0
            month_elem_bonus = 5 if month_mansion_elem in cat_data["favorable_elements"] else 0
            return max(30, min(100, base_score + cat_bonus + month_elem_bonus))

        # 按三期サイクル分組（取代固定 7 天分週）
        periods: list[dict] = []
        current_group: dict | None = None

        for d in all_daily:
            period_idx = d["sanki_period_index"]
            if current_group is None or current_group["period_index"] != period_idx:
                if current_group is not None:
                    periods.append(current_group)
                current_group = {
                    "period_index": period_idx,
                    "period_name": d["sanki_period"],
                    "days": [d]
                }
            else:
                current_group["days"].append(d)

        if current_group is not None:
            periods.append(current_group)

        # 組裝 weekly（欄位名保留 weekly 以減少前端改動量）
        weekly = []
        for seq, group in enumerate(periods, 1):
            days = group["days"]
            score = round(sum(d["score"] for d in days) / len(days))
            score = max(40, min(100, score))

            # focus 用該區段首日七曜元素決定
            start_date = date.fromisoformat(days[0]["date"])
            jp_weekday = (start_date.weekday() + 1) % 7
            week_element = fortune_data["weekday_elements"].get(str(jp_weekday), {}).get("element", "土")
            best_focus = "career"
            for cat in ["career", "love", "health", "wealth"]:
                if week_element in fortune_data["fortune_categories"][cat]["favorable_elements"]:
                    best_focus = cat
                    break

            # 警告彙整
            warnings = []
            ryouhan_days = sum(1 for d in days if d["ryouhan_active"])
            dark_days = sum(1 for d in days if d["is_dark_week"])
            specials = [d for d in days if d["special_day"]]
            if ryouhan_days > 0:
                warnings.append(f"凌犯期間 {ryouhan_days} 日")
            if dark_days > 0:
                warnings.append(f"暗黒の一週間 {dark_days} 日")
            for sp in specials:
                warnings.append(f"{sp['date'][-5:]} {sp['special_day']}")

            weekly.append({
                "week": seq,
                "period_index": group["period_index"],
                "period_name": group["period_name"],
                "period_reading": self.SANKI_CYCLE[group["period_index"] - 1]["reading"],
                "week_start": days[0]["date"],
                "week_end": days[-1]["date"],
                "days_count": len(days),
                "score": score,
                "focus": fortune_data["fortune_categories"][best_focus]["name"],
                "has_dark_week": dark_days > 0,
                "daily_overview": days,
                "warnings": warnings,
            })

        # 月警告彙整
        month_warnings = []
        if ryouhan_count > 0:
            month_warnings.append(f"本月有 {ryouhan_count} 天處於凌犯期間，吉凶逆轉需特別留意")
        if dark_week_count > 0:
            month_warnings.append(f"本月有 {dark_week_count} 天處於暗黒の一週間，判斷力下降宜保守行事")
        kanro_count = sum(1 for s in special_days_in_month if s["type"] == "kanro")
        rasetsu_count = sum(1 for s in special_days_in_month if s["type"] == "rasetsu")
        kongou_count = sum(1 for s in special_days_in_month if s["type"] == "kongou")
        if kanro_count > 0:
            month_warnings.append(f"甘露日 {kanro_count} 天")
        if rasetsu_count > 0:
            month_warnings.append(f"羅刹日 {rasetsu_count} 天")
        if kongou_count > 0:
            month_warnings.append(f"金剛峯日 {kongou_count} 天")

        # 月度策略分析
        monthly_strategy = self._generate_monthly_strategy(weekly, all_daily, ryouhan_count, days_in_month)

        return {
            "year": year,
            "month": month,
            "lunar_month": lunar_month_for_mansion,
            "month_mansion": {
                "name_jp": month_mansion["name_jp"],
                "reading": month_mansion["reading"],
                "index": month_mansion_index,
                "element": month_mansion["element"]
            },
            "your_mansion": {
                "name_jp": mansion["name_jp"],
                "reading": mansion["reading"],
                "element": user_element,
                "index": user_index
            },
            "relation": {
                "type": relation["type"],
                "name": self.DAILY_FORTUNE_RELATION_NAMES.get(relation["type"], relation["name"]),
                "name_jp": relation.get("name_jp", relation["name"]),
                "reading": relation.get("reading", ""),
                "description": self._seeded_choice(f"{birth_date.isoformat()}{year}{month}rel_desc", self.MONTHLY_FORTUNE_DESCRIPTIONS.get(relation["type"], [relation["description"]]))
            },
            "theme": {
                "title": month_theme.get("theme", ""),
                "focus": month_theme.get("focus", ""),
                "element_boost": theme_element,
                "description": self._seeded_choice(f"{birth_date.isoformat()}{year}{month}theme_desc", self.MONTHLY_THEME_DESCRIPTIONS.get(relation["type"], ["本月能量平穩，按照自己的步調前進即可。"]))
            },
            "fortune": {
                "level": month_level,
                "level_name": self.LEVEL_NAMES[month_level]["zh"],
                "level_name_ja": self.LEVEL_NAMES[month_level]["ja"],
                "level_reading": self.LEVEL_NAMES[month_level]["reading"],
                "overall": base_score,
                "career": calc_monthly_category("career"),
                "love": calc_monthly_category("love"),
                "health": calc_monthly_category("health"),
                "wealth": calc_monthly_category("wealth")
            },
            "ryouhan_info": {
                "affected_days": ryouhan_count,
                "total_days": days_in_month,
                "ratio": round(ryouhan_ratio, 2)
            } if ryouhan_count > 0 else None,
            "month_warnings": month_warnings,
            "special_days": special_days_in_month,
            "weekly": weekly,
            "strategy": monthly_strategy,
            "advice": self._seeded_choice(f"{birth_date.isoformat()}{year}{month}advice", self.MONTHLY_FORTUNE_ADVICE.get(relation["type"], [f"本月運勢{self.DAILY_FORTUNE_RELATION_NAMES.get(relation['type'], '平穩')}，順其自然即可。"]))
        }

    def calculate_weekly_fortune(self, birth_date: date, target_date: date) -> dict:
        """
        計算週運勢（滾動視窗）

        以 target_date 為中心，返回：
        - 昨天（1天）
        - 今天（target_date）
        - 未來 6 天
        共 8 天的運勢，更直觀的「本週」概念

        Args:
            birth_date: 出生日期
            target_date: 中心日期（通常是今天）

        Returns:
            週運勢資料
        """
        import random
        from datetime import timedelta

        fortune_data = self._load_fortune_data()
        mansion = self.get_mansion(birth_date)
        user_index = mansion["index"]
        user_element = mansion["element"]

        # 滾動視窗：昨天 + 今天 + 未來6天 = 8天
        yesterday = target_date - timedelta(days=1)
        week_end = target_date + timedelta(days=6)

        # 取得 target_date 的七曜元素
        weekday = target_date.weekday()
        jp_weekday = (weekday + 1) % 7
        day_info = fortune_data["weekday_elements"].get(str(jp_weekday), {
            "name": "月曜日", "reading": "げつようび", "element": "月", "planet": "月"
        })
        center_element = day_info["element"]

        # 計算元素關係
        relation_type, base_bonus = self._calc_fortune_element_relation(user_element, center_element)
        relation_desc = fortune_data["element_relations"].get(
            relation_type,
            fortune_data["element_relations"]["neutral"]
        )["description"]

        # 收集每日運勢（8天）+ 特殊日/凌犯/暗黒統計
        daily_overview = []
        week_warnings = []
        ryouhan_count = 0
        dark_week_count = 0
        special_day_entries = []

        for day_offset in range(-1, 7):
            day_date = target_date + timedelta(days=day_offset)
            daily_fortune = self.calculate_daily_fortune(birth_date, day_date)

            is_ryouhan = daily_fortune.get("ryouhan") is not None
            special_day = daily_fortune.get("special_day")
            is_dark = daily_fortune.get("sanki", {}).get("is_dark_week", False)

            if is_ryouhan:
                ryouhan_count += 1
            if special_day:
                special_day_entries.append({
                    "date": day_date.isoformat(),
                    "name": special_day.get("name", "")
                })
            if is_dark:
                dark_week_count += 1

            daily_overview.append({
                "date": day_date.isoformat(),
                "weekday": daily_fortune["weekday"]["name"],
                "score": daily_fortune["fortune"]["overall"],
                "level": daily_fortune["fortune"].get("level", ""),
                "is_today": day_offset == 0,
                "is_yesterday": day_offset == -1,
                "special_day": special_day.get("name") if special_day else None,
                "ryouhan_active": is_ryouhan,
                "is_dark_week": is_dark
            })

        # 週整體分數 = 8 天每日分數平均（日分數已從等級映射，自然傳遞）
        overall_score = round(sum(d["score"] for d in daily_overview) / len(daily_overview))
        overall_score = max(30, min(100, overall_score))

        # 各項運勢（以日運平均為基礎，與月運算法一致）
        def calc_weekly_category(category: str) -> int:
            cat_data = fortune_data["fortune_categories"][category]
            cat_bonus = 6 if user_element in cat_data["favorable_elements"] else 0
            day_bonus = 4 if center_element in cat_data["favorable_elements"] else 0
            return max(30, min(100, overall_score + cat_bonus + day_bonus))

        career_score = calc_weekly_category("career")
        love_score = calc_weekly_category("love")
        health_score = calc_weekly_category("health")
        wealth_score = calc_weekly_category("wealth")

        # 週警告彙整
        if ryouhan_count > 0:
            week_warnings.append(f"凌犯期間 {ryouhan_count} 日")
        if dark_week_count > 0:
            week_warnings.append(f"暗黒の一週間 {dark_week_count} 日")
        for sp in special_day_entries:
            week_warnings.append(f"{sp['date'][-5:]} {sp['name']}")

        # 選擇建議（根據平均分數反推等級）
        random.seed(f"{birth_date.isoformat()}{target_date.isoformat()}weekly_advice")
        if overall_score >= 83:
            advice_list = fortune_data["daily_advice"]["excellent"]
        elif overall_score >= 68:
            advice_list = fortune_data["daily_advice"]["good"]
        elif overall_score >= 53:
            advice_list = fortune_data["daily_advice"]["neutral"]
        elif overall_score >= 40:
            advice_list = fortune_data["daily_advice"]["caution"]
        else:
            advice_list = fortune_data["daily_advice"]["challenging"]

        advice = random.choice(advice_list)

        # 幸運物品
        lucky = fortune_data["lucky_items"]
        lucky_direction = lucky["directions"].get(center_element, lucky["directions"]["土"])
        lucky_color = lucky["colors"].get(center_element, lucky["colors"]["土"])

        # 各項提示
        category_tips = {}
        for cat in ["career", "love", "health"]:
            cat_tips = self.WEEKLY_CATEGORY_TIPS.get(cat, {})
            tip_key = relation_type if relation_type in cat_tips else "neutral"
            random.seed(f"{birth_date.isoformat()}{target_date.isoformat()}tip_{cat}")
            category_tips[cat] = random.choice(cat_tips.get(tip_key, [""]))

        return {
            "center_date": target_date.isoformat(),
            "week_start": yesterday.isoformat(),
            "week_end": week_end.isoformat(),
            "today_element": {
                "name": day_info["name"],
                "reading": day_info["reading"],
                "element": center_element,
                "planet": day_info["planet"]
            },
            "your_mansion": {
                "name_jp": mansion["name_jp"],
                "reading": mansion["reading"],
                "element": user_element,
                "index": user_index
            },
            "element_relation": {
                "type": relation_type,
                "description": relation_desc
            },
            "fortune": {
                "overall": overall_score,
                "career": career_score,
                "love": love_score,
                "health": health_score,
                "wealth": wealth_score
            },
            "daily_overview": daily_overview,
            "week_warnings": week_warnings,
            "advice": advice,
            "focus": self._seeded_choice(f"{birth_date.isoformat()}{target_date.isoformat()}weekly_focus", self.WEEKLY_FORTUNE_FOCUS.get(relation_type, self.WEEKLY_FORTUNE_FOCUS["neutral"])),
            "category_tips": category_tips,
            "lucky": {
                "direction": lucky_direction["direction"],
                "direction_reading": lucky_direction["reading"],
                "color": lucky_color["color"],
                "color_reading": lucky_color["reading"],
                "color_hex": lucky_color["hex"]
            }
        }

    # 九曜流年法（宿曜經）：9 年循環
    # 數え年 1 歲 = 羅喉星，每年順推
    KUYOU_STARS = [
        {
            "name": "羅喉星", "reading": "らごうせい",
            "level": "大凶", "fortune_name": "潜運",
            "element": None, "base_score": 48,
            "buddha": "不動明王",
            "description": "八方受阻的一年。氣力旺盛、想挑戰新事物的衝動很強，但運氣不站在你這邊。衝動行事容易招來失敗，越急越容易出差錯。這一年的功課是學會「等待」。把想做的事寫下來但先不動手，用這段時間觀察局勢、蒐集情報、養好體力。忍住不出手反而比亂出手更需要實力。"
        },
        {
            "name": "土曜星", "reading": "どようせい",
            "level": "半吉", "fortune_name": "開運",
            "element": "土", "base_score": 62,
            "buddha": "聖觀音",
            "description": "從低谷緩慢爬升的一年。身體容易出小狀況，心情也不太爽快，但整體趨勢是往上走的。夏秋之間注意健康管理，土地和不動產相關的事情要謹慎處理。不是大展拳腳的時機，但可以開始規劃下一步。穩紮穩打比什麼都重要。"
        },
        {
            "name": "水曜星", "reading": "すいようせい",
            "level": "末吉", "fortune_name": "喜運",
            "element": "水", "base_score": 58,
            "buddha": "彌勒菩薩",
            "description": "表面平靜、暗流湧動的一年。運勢不算差，但你的心思會比實際狀況更紛亂，容易自己嚇自己。春夏低調行事、減少不必要的社交和承諾，秋冬之後才會明顯好轉。貴人和長輩的建議今年格外受用，遇到拿不定主意的事不要自己悶著想，找有經驗的人聊一聊。"
        },
        {
            "name": "金曜星", "reading": "きんようせい",
            "level": "半吉", "fortune_name": "平運",
            "element": "金", "base_score": 63,
            "buddha": "阿彌陀如來",
            "description": "吉凶參半、好壞交織的一年。人際關係是今年最需要花心思的課題，工作上也可能出現讓你措手不及的變化。但壞事裡藏著好事，困難的處境反而能讓你遇到真正幫你的人。聽從專業人士的建議，不要只靠自己的判斷。"
        },
        {
            "name": "日曜星", "reading": "にちようせい",
            "level": "大吉", "fortune_name": "盛運",
            "element": "日", "base_score": 82,
            "buddha": "千手觀音",
            "description": "如順風滿帆的一年。財運旺、做事有利、地位和聲望都在上升。積極行動會帶來超出預期的回報。但越是順利越要保持謙虛，驕傲自滿的瞬間就是運勢反轉的起點。把今年的成果轉化為長期資產，別揮霍在虛榮上。"
        },
        {
            "name": "火曜星", "reading": "かようせい",
            "level": "大凶", "fortune_name": "休運",
            "element": "火", "base_score": 42,
            "buddha": "虛空藏菩薩",
            "description": "需要格外謹慎的一年。人際和事業上容易遇到挑戰，家庭和工作中的關係也可能因為溝通不順而出現考驗。這些考驗不是來打倒你的，是在提醒你哪些關係需要更用心經營。控制情緒是今年最重要的課題——遇到讓你想發火的事情，先離開現場冷靜十分鐘再回應。撐過這一年，你的耐性和應變力會提升一個層次。"
        },
        {
            "name": "計都星", "reading": "けいとせい",
            "level": "大凶", "fortune_name": "滞運",
            "element": None, "base_score": 45,
            "buddha": "釋迦如來",
            "description": "事情的進展比預期慢、付出和回報不成正比的一年。春季三個月特別需要耐心，到秋天會逐漸好轉。這不是你的能力問題，是時運的節奏走到了這裡。你能做的是調整期望、減少冒險、把精力集中在守住現有的成果上。同時，趁這段減速期整理思緒、盤點資源，為下一波回升做好準備。低谷年是最好的反思期。"
        },
        {
            "name": "月曜星", "reading": "げつようせい",
            "level": "大吉", "fortune_name": "進運",
            "element": "月", "base_score": 80,
            "buddha": "勢至菩薩",
            "description": "如龍得水、萬事亨通的一年。人脈和機運同時到來，工作上有貴人拉拔、生活中喜事接連不斷。信仰虔誠者今年的修行功德加倍，適合發願、拓展格局、承擔更大的責任。好運會持續整年，但越順利越要保持感恩和謙遜，把這一年的成果轉化為長期的根基。"
        },
        {
            "name": "木曜星", "reading": "もくようせい",
            "level": "大吉", "fortune_name": "吉運",
            "element": "木", "base_score": 80,
            "buddha": "藥師如來",
            "description": "如春天發芽般，做什麼都容易成長的一年。婚姻運好、家庭安泰、私人生活充實。不管是開始一段新關係、搬家、還是轉換跑道，今年的選擇都容易帶來好結果。但好運不等於不用努力，鬆懈是吉年最大的浪費。"
        }
    ]

    # 真言宗修行對照資料（空海大師《宿曜經》修行者視角）
    SHINGON_KUYOU_DATA = {
        "羅喉星": {
            "practice_name": "閉關沉潛期",
            "practice_level": "精進",
            "description": (
                "修行者的羅喉星年，是密法精進的絕佳時機。世俗觀點視此年為大凶，但在空海大師的教導中，"
                "外在障礙正是內在修行的催化劑。當世間的門一扇扇關上，禪房的門正為你敞開。"
                "這一年適合減少外緣、專注於持咒與觀想。不動明王的忿怒相並非憤怒，而是斬斷煩惱的決心。"
                "以不動明王為本尊，每日持誦真言，將八方受阻的困境轉化為八識清淨的修行。"
                "歷代高僧往往在最艱難的歲月中獲得突破，因為逆境讓心無處可逃，只能向內觀照。"
                "閉關不一定要入山，日常生活中減少不必要的應酬、關掉社群媒體、每天固定時間靜坐，"
                "就是在家居士的閉關。這一年你會發現，少即是多，靜中有動。"
            ),
            "description_classic": "羅喉者，日月之蝕神也。梵名 Rahu，隱覆光明，百事阻滯。然修行者於此年閉關精進，反能破暗見明，轉障為道。",
            "description_ja": "羅喉星は日蝕・月蝕を司る暗黒の星なり。世俗においては万事阻滞の大凶年とされるが、真言宗では逆に閉関精進の好機と捉える。外縁を断ち内観に徹すれば、不動明王の智慧火が業障を焼き尽くし、暗闇の中にこそ悟りの光が見出される。",
            "core_teaching": "空海大師云：「即身成佛，不離此處。」逆境不是阻礙，是照見自心的明鏡。",
            "practice_focus": "持咒精進、減少外緣、深入密法修行",
            "recommended_practices": ["不動明王法", "護摩修法", "百日加行"],
            "mantra": {
                "buddha": "不動明王",
                "name": "不動明王真言",
                "text": "ノウマク サンマンダ バザラダン センダ マカロシャダ ソワタヤ ウンタラタ カンマン",
                "reading": "のうまく さんまんだ ばざらだん せんだ まかろしゃだ そわたや うんたらた かんまん",
                "siddham_bija": "カーン",
                "siddham_roman": "k\u0101\u1e43",
                "siddham_unicode": "\U0001158E\U000115AF\U000115BD"
            },
            "homa_type": "息災護摩",
            "homa_description": "以息災護摩消除業障，迴向障礙消除、修行順遂",
            "theme": {
                "title": "閉關沉潛之年",
                "description": (
                    "羅喉星的暗影籠罩，世俗事務處處受阻——但這正是密教行者入深定的最佳契機。"
                    "外在的不順遂，是宇宙在提醒你：向外追求的路暫時封閉了，請轉向內在。"
                    "不動明王的火焰燒盡障礙，護摩的薪火淨化業障。"
                    "這一年的修行成果，會在未來的順境中綻放。種子在黑暗的土壤中發芽，修行在困境中紮根。"
                )
            },
            "category_practice": {
                "career": "以利他為發心，在職場中修行忍辱波羅蜜。不順遂的工作環境是修煉心性的道場，每一個困難的同事都是你的善知識。放下對結果的執著，專注於當下的每一件事做到最好。",
                "love": "以慈悲心看待所有關係中的摩擦。人際困難不是懲罰，是觀照自己習氣的機會。練習在對方讓你不舒服的時候，先觀察自己的反應，再做回應。這就是日常中的觀心法門。",
                "health": "每日固定時段靜坐，從十五分鐘開始。配合腹式呼吸，讓身心回到安定。飲食清淡，減少刺激性食物。身體是修行的道器，照顧好它才能走更遠的修行路。",
                "wealth": "布施是最好的理財。不一定要捐大錢，每天一個小小的善行就是在累積福德資糧。供養三寶、幫助有需要的人、甚至只是給人一個真誠的微笑，都是在為自己的福德帳戶存款。"
            },
            "advice": "這一年的關鍵字是「轉化」。把世俗的困境轉化為修行的動力，把外在的阻礙轉化為內在的力量。不動明王的真言是你的護身符，每日持誦至少 108 遍。記住：最深的黑暗之後，就是最亮的黎明。",
            "monthly_tips": {
                "1": "正月發願：設定年度修行目標，發大願心。「為利眾生願成佛」——從利他的發心開始這一年。",
                "2": "涅槃會（2/15）：觀修無常。佛陀的入滅提醒我們：一切有為法如夢幻泡影。趁此月深化對無常的體悟。",
                "3": "春季彼岸會：迴向功德給一切有情眾生。精進持咒，將修行的力量分享出去。彼岸不遠，就在一念之間。",
                "4": "灌佛會（4/8）：慶祝佛誕，重新發起菩提心。回想自己為什麼開始修行，讓初心成為繼續前進的動力。",
                "5": "持戒精進月：檢視自己的身口意，有沒有偏離正道。持戒不是束縛，是保護自己不被習氣拖著走。",
                "6": "夏安居開始：密集修行期。即使在家，也安排每天固定一小時的修法時間，持續不間斷。",
                "7": "盂蘭盆：施餓鬼、供養先祖。觀想六道眾生的苦，生起大悲心。修不動明王法迴向冤親債主。",
                "8": "夏安居結束：回顧這兩個月的修行成果，鞏固所得。不要鬆懈，修行是馬拉松，不是短跑。",
                "9": "秋季彼岸會：再次迴向功德。秋天的收斂之氣適合向內觀照，深化禪定功夫。",
                "10": "深化修行月：觀照內心的微細煩惱，用不動明王的智慧火焰一一照破。",
                "11": "報恩講：感恩上師、感恩佛法、感恩一切善緣。供養是修行的重要一環，心存感恩本身就是修行。",
                "12": "成道會（12/8）：年末省思，發大願。佛陀在菩提樹下成道，你在日常中修行。寫下明年的修行計畫。"
            },
            "warnings": ["避免衝動行事，每個重大決定前先靜坐觀照", "減少不必要的社交應酬，保護修行的能量"],
            "opportunities": ["閉關修行的最佳年份", "深入密法、突破修行瓶頸的契機"]
        },
        "土曜星": {
            "practice_name": "穩固根基期",
            "practice_level": "調和",
            "description": (
                "土曜星年如同建築打地基——表面看不到進展，但一切穩固都從這裡開始。"
                "聖觀音菩薩的慈悲之眼觀照著你，提醒你修行不必求快，根基穩了自然向上生長。"
                "這一年適合回歸基本功：端正坐姿、調整呼吸、重新學習最基礎的觀想法門。"
                "很多修行者急著追求高深的法門，卻忽略了基礎功夫。土曜星年就是宇宙給你的提醒："
                "回到原點，把根基打穩。一棵大樹的高度取決於根的深度。"
                "身體可能出現小狀況，這是在提醒你照顧好修行的道器。適度運動、規律作息，"
                "讓身心都處於穩定的狀態，修行自然事半功倍。"
            ),
            "description_classic": "土曜者，鎮星也。梵名 Śani，主穩重遲緩。此年宜固根基，不宜急進。如大地承載萬物，厚德載物之時也。",
            "description_ja": "土曜星は鎮星とも呼ばれ、安定と遅滞を司る星なり。此の年は地固めの時期にして、表面上の進展は乏しくとも、修行の根基を堅固にする好機。聖観音の慈悲に護られ、基本功を磨き直すことで、後年の飛躍に備える。",
            "core_teaching": "觀音菩薩「尋聲救苦」的精神，提醒我們修行的根基在於對眾生苦的真實感受。",
            "practice_focus": "回歸基本功、調整身心、穩固修行根基",
            "recommended_practices": ["聖觀音法", "大悲心陀羅尼", "阿字觀"],
            "mantra": {
                "buddha": "聖觀音",
                "name": "聖觀音真言",
                "text": "オン アロリキャ ソワカ",
                "reading": "おん あろりきゃ そわか",
                "siddham_bija": "サ",
                "siddham_roman": "sa",
                "siddham_unicode": "\U000115AD"
            },
            "homa_type": "息災護摩",
            "homa_description": "以息災護摩培固根基，迴向福德增長、道心堅固",
            "theme": {
                "title": "穩固根基之年",
                "description": (
                    "土的能量沉穩厚重，這一年的節奏會比你期待的慢。但慢不是停滯，是在紮根。"
                    "聖觀音的慈悲如大地般承載一切。你不需要飛得多高，只需要站得更穩。"
                    "回歸修行的基本功，重新審視自己的發心是否純正，持戒是否清淨。"
                    "地基打得好，未來的修行才能蓋得高。這是平凡卻不可或缺的一年。"
                )
            },
            "category_practice": {
                "career": "穩健經營，不求突破但求穩固。在工作中修「不急不躁」的功夫。每一件小事都認真做，把日常工作當作修行的一部分。腳踏實地比好高騖遠更能走到終點。",
                "love": "用觀音的慈悲眼看待身邊的人。關係中的問題往往來自期待過高。放下「對方應該怎樣」的執念，接受真實的彼此，愛自然會流動。",
                "health": "身體是修行的道器，這一年特別需要保養。規律作息、適度運動、清淡飲食。每天散步三十分鐘，邊走邊持誦聖觀音真言，身心同修。",
                "wealth": "土性主穩，理財也該穩健。不適合冒險投資，適合儲蓄和長期規劃。供養三寶、布施助人是真正的「穩賺不賠」。"
            },
            "advice": "這一年修行的關鍵在「穩」字。不追求神通感應，不羨慕他人的快速進展，專注於自己腳下的每一步。聖觀音的真言簡短卻深遠，每日持誦時觀想觀音菩薩的慈悲光明照耀自己和一切眾生。",
            "monthly_tips": {
                "1": "正月：設定務實的年度修行計畫。不要貪多，選一個主修法門持續一整年。",
                "2": "涅槃會（2/15）：觀修大地承載萬物的功德。土之德在於承載與包容。",
                "3": "春季彼岸會：檢視修行根基，哪裡不穩就補哪裡。基礎功夫永遠不嫌多。",
                "4": "灌佛會（4/8）：以清淨心灌沐佛像，同時洗滌自己心中的塵垢。",
                "5": "調身月：注意飲食作息，安排健康檢查。道器不穩，修行難成。",
                "6": "夏安居開始：安住當下，不被外境牽著走。每天固定時間持誦聖觀音真言。",
                "7": "盂蘭盆：以觀音的大悲心迴向一切有情。供養先祖，感恩生命的根源。",
                "8": "鞏固月：回顧上半年的修行，穩固所得成果。不進則退，持續用功。",
                "9": "秋季彼岸會：秋天的收斂之氣助你向內紮根。深化基本功的修持。",
                "10": "沉澱月：減少外出，在家精進。把心安住在法上，不隨境轉。",
                "11": "報恩講：感恩大地的承載，感恩根基的穩固。供養是最好的培福方式。",
                "12": "成道會（12/8）：年末總結，看看根基是否比年初更穩了。發願明年更上一層。"
            },
            "warnings": ["注意身體健康，定期檢查", "不宜急躁冒進，穩步前行"],
            "opportunities": ["打穩修行根基的好年份", "適合回歸基本功、重新出發"]
        },
        "水曜星": {
            "practice_name": "智慧開展期",
            "practice_level": "增上",
            "description": (
                "水曜星年是智慧之水流淌的一年。彌勒菩薩的未來佛智慧照亮前路，"
                "適合研讀經典、修文殊法、廣學多聞。水的特性是柔軟而無處不達，"
                "你的理解力和洞察力在這一年會特別敏銳。"
                "但水也有暗流——想太多、煩惱多、心思過於活躍。"
                "修行者的功課是讓智慧之水澄清而非混濁。靜坐觀心，讓念頭如水面的漣漪自然平息。"
                "彌勒菩薩代表未來的希望和大慈之心，這一年學到的法門和智慧，"
                "會成為你未來弘法利生的資糧。不要急著把學到的東西說出去，先消化、再分享。"
            ),
            "description_classic": "水曜者，辰星也。梵名 Budha，主智慧流通。此年智慧如水潤澤，宜研讀經典、廣學多聞。然水亦有暗流，宜靜心澄慮。",
            "description_ja": "水曜星は辰星とも呼ばれ、智慧と学問を司る星なり。此の年は理解力・洞察力が冴え渡り、経典研鑽や法門修学に最適。弥勒菩薩の大慈の智慧に導かれ、学んだ法が未来の弘法利生の資糧となる。",
            "core_teaching": "彌勒菩薩的「大慈」心——以智慧觀照一切眾生，給予真正需要的幫助。",
            "practice_focus": "研讀經典、修文殊法、廣學多聞",
            "recommended_practices": ["彌勒菩薩法", "理趣經讀誦", "寫經修行"],
            "mantra": {
                "buddha": "彌勒菩薩",
                "name": "彌勒菩薩真言",
                "text": "オン マイタレイヤ ソワカ",
                "reading": "おん まいたれいや そわか",
                "siddham_bija": "ユ",
                "siddham_roman": "yu",
                "siddham_unicode": "\U000115A7\U000115B2"
            },
            "homa_type": "息災護摩",
            "homa_description": "以息災護摩淨除無明，迴向智慧開顯、正見增長",
            "theme": {
                "title": "智慧開展之年",
                "description": (
                    "水的流動帶來智慧的滋潤。經典中過去讀不懂的段落，今年可能豁然開朗。"
                    "彌勒菩薩的慈心與智慧並重。學法不只是增長知識，更是培養觀照實相的能力。"
                    "用清淨的心閱讀每一部經典，讓法水洗去見解上的塵垢。"
                    "這一年的學習成果會在未來的弘法中派上用場。"
                )
            },
            "category_practice": {
                "career": "以智慧處理工作中的複雜局面。水的柔軟能繞過障礙。不硬碰硬，用圓融的方式解決問題。遇到猶豫不決的事，靜下心來觀照，答案自然浮現。",
                "love": "以彌勒菩薩的慈心對待每一段關係。不用想太多「為什麼」，用心感受對方的需要。真正的智慧不是分析對錯，是能夠同理他人的處境。",
                "health": "水主腎，注意泌尿系統和腰部保養。靜坐時觀想清涼的智慧之水流遍全身，洗淨身心的疲憊。保持充足的水分攝取，身體的水和智慧的水同樣重要。",
                "wealth": "智慧是最好的投資。這一年花在學習上的錢不會白費。供養法師、請購經典、參加法會，這些都是在為智慧帳戶儲值。"
            },
            "advice": "水曜星年的修行重點是「學」。但學不是填鴨，是讓法水自然滲透。每天留半小時讀經，不求量多，求真正理解。彌勒菩薩的真言雖短，持誦時觀想未來佛的智慧光明照耀自己，讓心中的疑惑一一消解。",
            "monthly_tips": {
                "1": "正月：選定今年要深入研讀的一部經典，制定閱讀計畫。",
                "2": "涅槃會（2/15）：讀《涅槃經》選段，體會佛陀最後的教誨。",
                "3": "春季彼岸會：以智慧迴向，願一切眾生開啟般若之眼。",
                "4": "灌佛會（4/8）：佛陀誕生帶來智慧的光明。重新發起求法的決心。",
                "5": "深入月：專注研讀，減少分心。把手機放遠一點，書本拿近一點。",
                "6": "夏安居開始：結合靜坐與經典研讀，定慧雙修。",
                "7": "盂蘭盆：以智慧觀照六道苦，發起大悲心。",
                "8": "實踐月：把學到的道理在日常中實踐。知行合一才是真正的智慧。",
                "9": "秋季彼岸會：智慧的收穫期。整理上半年的學習心得。",
                "10": "融會月：把學到的不同法門串聯起來，尋找共通的核心。",
                "11": "報恩講：以法供養回報師恩。把學到的法分享給有緣人。",
                "12": "成道會（12/8）：佛陀的覺悟始於智慧。總結今年的學法成果，發願明年繼續精進。"
            },
            "warnings": ["避免想太多而行動太少，知行要合一", "學法不宜貪多，深入一門勝過淺嘗百門"],
            "opportunities": ["研讀經典、開啟智慧的最佳年份", "適合參加講座、進修佛學"]
        },
        "金曜星": {
            "practice_name": "福德累積期",
            "practice_level": "調和",
            "description": (
                "金曜星年是累積福德資糧的一年。阿彌陀如來的無量光明照耀，"
                "提醒我們修行不只是為自己，更是為了利益一切眾生。"
                "金的特性是收斂、純淨，這一年適合提煉修行的品質而非追求數量。"
                "人際關係可能出現變動，有人離去也有人到來——這是在提煉你的善緣。"
                "阿彌陀如來的「無量壽」代表超越時間的修行視野。不要只看眼前的得失，"
                "把目光放遠到生生世世的修行大業。今年的每一個善行，都在密嚴佛國中種下種子。"
            ),
            "description_classic": "金曜者，太白星也。梵名 Śukra，主收斂純淨。此年宜累積福德、莊嚴身儀。人事有變動，乃提煉善緣之時。",
            "description_ja": "金曜星は太白星とも呼ばれ、収斂と浄化を司る星なり。此の年は福徳資糧を蓄える時期にして、阿弥陀如来の無量光に照らされ、修行の質を高める好機。人間関係の変動は善縁を精錬する作用あり。",
            "core_teaching": "阿彌陀如來「無量光壽」的教導——修行的價值不在當下的感應，在於生生世世的累積。",
            "practice_focus": "累積福德資糧、淨化身口意、光明真言修法",
            "recommended_practices": ["阿彌陀如來法", "光明真言持誦", "施食供養"],
            "mantra": {
                "buddha": "阿彌陀如來",
                "name": "阿彌陀如來真言",
                "text": "オン アミリタ テイセイ カラ ウン",
                "reading": "おん あみりた ていせい から うん",
                "siddham_bija": "キリーク",
                "siddham_roman": "hr\u012b\u1e25",
                "siddham_unicode": "\U000115AE\U000115BF\U000115A8\U000115B1\U000115BE"
            },
            "homa_type": "息災護摩",
            "homa_description": "以息災護摩除障延命，迴向福壽增長、資糧圓滿",
            "theme": {
                "title": "福德累積之年",
                "description": (
                    "金的能量收斂提煉，阿彌陀如來的光明指引方向。"
                    "這一年不求外在的擴張，而是內在品質的提升。"
                    "每一個善念、每一次持咒、每一回布施，都是在累積成佛的資糧。"
                    "福德看不見摸不著，卻是修行路上最實在的財富。"
                )
            },
            "category_practice": {
                "career": "在工作中修布施波羅蜜。不只是金錢的布施，更重要的是時間、能力和善意的布施。主動幫助同事、分享經驗、承擔責任——這些都是在職場中累積福德。",
                "love": "以阿彌陀如來的無量慈悲看待關係的變動。有人離去是緣盡，有人到來是緣起。不執著、不排斥，以平等心對待每一段關係。",
                "health": "金主肺，注意呼吸系統保養。練習阿息觀（吐納配合阿字觀想），每一口呼吸都是與本尊相應的機會。秋天特別注意保暖，預防感冒。",
                "wealth": "真正的財富是福德。今年適合增加布施供養的比例，不一定要大量金額，重要的是持續而真誠。隨喜他人的善行也是在累積自己的福德。"
            },
            "advice": "金曜星年的修行心法是「提煉」。像冶金一樣，去除雜質留下純金。檢視自己的修行中有哪些流於形式、缺乏真心。阿彌陀如來的真言持誦時，觀想無量光明從佛的心中流出，淨化自己和一切眾生的業障。",
            "monthly_tips": {
                "1": "正月：發願今年要累積的福德目標，具體可行。",
                "2": "涅槃會（2/15）：以無常觀提醒自己，累積福德要趁早。",
                "3": "春季彼岸會：以布施迴向功德，願一切眾生同證菩提。",
                "4": "灌佛會（4/8）：佛誕日是大供養的好時機。以清淨心供花供水。",
                "5": "護生月：供養施食、護持道場，以實際行動累積福德。日常中愛護一切有情即是修行。",
                "6": "夏安居開始：密集持誦阿彌陀如來真言，每日千遍以上。",
                "7": "盂蘭盆：供養僧眾、迴向先祖。這是大布施的月份。",
                "8": "淨化月：檢視身口意三業，有不清淨的地方要懺悔改正。",
                "9": "秋季彼岸會：金氣收斂，適合向內提煉修行品質。",
                "10": "隨喜月：隨喜讚歎他人的善行，這是最輕鬆的累積福德方式。",
                "11": "報恩講：供養上師三寶，回報法乳之恩。",
                "12": "成道會（12/8）：回顧一年的福德累積，以歡喜心收尾。"
            },
            "warnings": ["人際關係變動期，以平常心面對", "不宜執著於修行的感應和體驗"],
            "opportunities": ["累積福德資糧的大好年份", "適合增加布施供養的頻率"]
        },
        "日曜星": {
            "practice_name": "弘法利生期",
            "practice_level": "弘法",
            "description": (
                "日曜星年是光明照耀的一年。千手觀音的千手千眼代表無限的救度方便，"
                "這一年你的影響力和感召力特別強，正是弘法利生的最佳時機。"
                "世俗觀點視此年為大吉，但修行者看到的不是「享受好運」，而是「承擔責任」。"
                "能量充沛、貴人相助、機會頻現——這些不是讓你享樂的，是讓你有更大的力量去幫助別人。"
                "千手觀音的每一隻手都代表一種度化眾生的方法。你今年能做的不只是修自己，"
                "更重要的是把修行的利益傳遞出去。分享你的經驗、帶領初學者、護持道場，"
                "讓好運變成好的業力，讓順境成為利他的資本。"
            ),
            "description_classic": "日曜者，太陽也。梵名 Sūrya，主光明盛大。此年萬事亨通，福慧增長。宜積極行事，弘法利生。最上吉年也。",
            "description_ja": "日曜星は太陽そのものにして、光明と繁栄を司る最上の吉星なり。此の年はエネルギーが最も充実し、修行も世俗も順風満帆。千手観音の無量の慈悲力に護られ、積極的に行動し衆生利益に励むべき時期。",
            "core_teaching": "千手觀音「度一切苦厄」——順境中的修行者，責任是用自己的力量去幫助還在苦中的眾生。",
            "practice_focus": "弘法利生、護持道場、分享修行經驗",
            "recommended_practices": ["千手觀音法", "大悲心陀羅尼法", "利他行"],
            "mantra": {
                "buddha": "千手觀音",
                "name": "千手觀音真言",
                "text": "オン バザラ タラマ キリク",
                "reading": "おん ばざら たらま きりく",
                "siddham_bija": "キリーク",
                "siddham_roman": "hr\u012b\u1e25",
                "siddham_unicode": "\U000115AE\U000115BF\U000115A8\U000115B1\U000115BE"
            },
            "homa_type": "息災護摩",
            "homa_description": "以息災護摩消除眾障，迴向弘法順利、眾緣和合",
            "theme": {
                "title": "弘法利生之年",
                "description": (
                    "日的光明能量充沛，千手觀音的加持護佑。"
                    "這不只是運勢好的一年，是你回饋眾生的一年。"
                    "把修行的成果化為實際的利他行動。"
                    "好運是用來幫助別人的資本，不是用來享受的特權。"
                )
            },
            "category_practice": {
                "career": "把職場當作弘法的道場。用你的專業能力去幫助更多人，帶領團隊不是為了權力，是為了讓更多人成長。順境中保持謙虛，才能讓好運延續。",
                "love": "千手觀音的慈悲是無差別的。在關係中付出，不求回報。今年你有能力給予更多——給予時間、理解、支持和愛。讓身邊的人因為你的存在而感到溫暖。",
                "health": "能量充沛的一年，但不要因此透支。適度運動、充足睡眠，保持身心的平衡。健康的身體才能持續利他。",
                "wealth": "財運佳的年份，正是大力布施的時候。收入增加的部分拿出一定比例供養三寶、幫助弱勢。讓財富流動起來，不要只進不出。"
            },
            "advice": "大吉之年的修行者，最需要警惕的是「順境中的懈怠」。一切順利時人容易鬆懈，忘記修行的初衷。千手觀音的真言提醒你：每一隻手都在為眾生工作，你的好運也該如此。這一年要比往年更加精進，因為你有更多的能量可以利用。",
            "monthly_tips": {
                "1": "正月：發起弘法利生的大願。列出今年能為他人做的具體事項。",
                "2": "涅槃會（2/15）：以佛陀的遺教為鑑，繼承弘法的使命。",
                "3": "春季彼岸會：帶領身邊的人一起修行迴向。",
                "4": "灌佛會（4/8）：組織或參與慶祝活動，讓更多人認識佛法。",
                "5": "利他月：主動幫助正在困難中的人。你一個小小的善行可能改變別人的一天。",
                "6": "夏安居開始：在精進修行的同時，護持道場的運作。",
                "7": "盂蘭盆：以大悲心迴向六道眾生。組織法會或帶領共修。",
                "8": "分享月：分享自己的修行經驗，但要謙虛，不要說教。",
                "9": "秋季彼岸會：回顧弘法利生的成果，不執著於功德。",
                "10": "護持月：支持道場、護持法師、幫助初學者。",
                "11": "報恩講：以弘法的行動回報師恩。最好的報恩是讓更多人受益。",
                "12": "成道會（12/8）：年末回顧，這一年有多少人因為你而接觸佛法？"
            },
            "warnings": ["順境中保持警覺，不要被好運沖昏頭", "弘法要隨緣，不要強迫他人接受"],
            "opportunities": ["弘法利生的最佳年份", "影響力和感召力最強的時期"]
        },
        "火曜星": {
            "practice_name": "降魔淨障期",
            "practice_level": "精進",
            "description": (
                "火曜星年是修行者面對內心魔障的一年。虛空藏菩薩的智慧如虛空般廣大無邊，"
                "這一年的衝突和挫折，都是在燒煉你的我執和習氣。"
                "世俗觀點視此年為大凶，但密教行者知道：火能燒毀一切不淨之物，"
                "包括你心中那些隱藏很深的貪嗔癡。"
                "情緒容易波動、人際容易衝突——這些不是外在的困境，是內在業障顯現的徵兆。"
                "虛空藏菩薩修法是對治之道。觀想無邊虛空容納一切，"
                "你的心也能如虛空般包容所有順逆境界。"
                "降伏護摩的火焰象徵以智慧之火焚燒煩惱。修行的敵人不在外面，在自己心裡。"
            ),
            "description_classic": "火曜者，熒惑星也。梵名 Maṅgala，主急躁衝動。此年多災厄變動，宜忍辱精進。以慈悲心化瞋恚火，轉煩惱為菩提。",
            "description_ja": "火曜星は熒惑星とも呼ばれ、急躁と変動を司る星なり。九曜中最も凶意が強く、衝動的な行動が災いを招きやすい年。虚空蔵菩薩の広大な智慧に帰依し、忍辱波羅蜜の修行を以て瞋恚の炎を鎮めるべし。",
            "core_teaching": "虛空藏菩薩的「虛空」——心量大到如虛空，一切煩惱都裝得下，也放得下。",
            "practice_focus": "降魔淨障、觀照習氣、修忍辱行",
            "recommended_practices": ["虛空藏菩薩法", "降伏護摩", "懺悔行"],
            "mantra": {
                "buddha": "虛空藏菩薩",
                "name": "虛空藏菩薩真言",
                "text": "ノウボウ アキャシャ ギャラバヤ オン アリ キャマリ ボリ ソワカ",
                "reading": "のうぼう あきゃしゃ ぎゃらばや おん あり きゃまり ぼり そわか",
                "siddham_bija": "タラーク",
                "siddham_roman": "tr\u0101\u1e25",
                "siddham_unicode": "\U0001159D\U000115BF\U000115A8\U000115AF\U000115BE"
            },
            "homa_type": "息災護摩",
            "homa_description": "以息災護摩淨除魔障，迴向煩惱消滅、內心清淨",
            "theme": {
                "title": "降魔淨障之年",
                "description": (
                    "火的能量猛烈直接，衝突在所難免。但修行者不怕火，因為火能煉金。"
                    "虛空藏菩薩的智慧提醒你：衝突的本質是自己心中的不安。"
                    "當你能在怒火中保持觀照，你就已經在降魔了。"
                    "這一年的修行比順境中更有價值，因為逆境才是真正的考試。"
                )
            },
            "category_practice": {
                "career": "職場的衝突是修忍辱的道場。有人批評你、否定你、為難你——把每一次不舒服都當作修行的機會。在心裡默念虛空藏菩薩真言，讓情緒的火焰在智慧的觀照下自然熄滅。",
                "love": "關係中的摩擦是照見自己的鏡子。對方讓你生氣的點，往往是你自己沒有處理好的問題。在想要反擊之前，先問自己：「我為什麼這麼在意？」這一問就是修行。",
                "health": "火主心，注意心血管和情緒健康。學會在情緒升起時做三次深呼吸，讓火氣降下來。避免刺激性食物，多吃清涼降火的食材。",
                "wealth": "不宜冒險投資或重大財務決定。這一年的財運考驗是「控制」——控制衝動消費、控制投機心理。守住現有的就是最好的理財。"
            },
            "advice": "火曜星年的修行核心是「觀照」。每次情緒升起時，不要急著反應，先觀察它：這個憤怒從哪裡來？它停留多久？它是怎麼消失的？虛空藏菩薩的真言是你的滅火器。記住：能降伏自心的人，才是真正的勇者。",
            "monthly_tips": {
                "1": "正月：發願今年修忍辱行。把「不急著反應」當作年度功課。",
                "2": "涅槃會（2/15）：佛陀在面對魔軍時安坐不動。學習佛陀的定力。",
                "3": "春季彼岸會：懺悔過去的瞋心業。真心懺悔是淨障的最快方法。",
                "4": "灌佛會（4/8）：以清淨心沐浴佛像，同時沐浴自己的心。",
                "5": "觀照月：每天記錄一次情緒的升起和消退，培養自我覺察力。",
                "6": "夏安居開始：精進修虛空藏菩薩法，以廣大心包容一切。",
                "7": "盂蘭盆：以懺悔心迴向冤親債主。化解宿怨是淨障的重要一環。",
                "8": "忍辱月：遇到不如意的事，練習先停十秒再回應。",
                "9": "秋季彼岸會：秋天的肅殺之氣助你斬斷煩惱。精進降伏護摩修法。",
                "10": "轉化月：把上半年的困難經驗轉化為修行的養分。",
                "11": "報恩講：感恩逆緣的教導。沒有困難，就沒有成長。",
                "12": "成道會（12/8）：回顧這一年降伏了哪些心魔。發願繼續精進。"
            },
            "warnings": ["控制情緒是首要功課，衝動行事後果嚴重", "注意心血管健康，避免過度操勞"],
            "opportunities": ["破除我執習氣的絕佳時機", "修忍辱行、提升定力的最佳年份"]
        },
        "計都星": {
            "practice_name": "業障清淨期",
            "practice_level": "精進",
            "description": (
                "計都星年是業障浮現、等待清淨的一年。釋迦如來親自示範了在菩提樹下降魔成道的歷程——"
                "最深的業障浮現之時，正是最接近覺悟的時刻。"
                "努力得不到回報、計畫被迫中斷——世俗觀點認為這是壞事，修行者知道這是業障在消融。"
                "過去世的業力在今年集中顯現，正是因為你的修行力量夠了，才有能力承受和轉化它。"
                "釋迦如來是歷史上真實存在的覺悟者，他的教法不是理論而是親身實踐的結果。"
                "跟隨佛陀的腳步，在困境中保持正念，在挫折中保持精進，業障終將消盡。"
            ),
            "description_classic": "計都者，月之降交點也。梵名 Ketu，主停滯隱晦。此年事多遲滯，進退不明。宜潛修蓄力，以待時機。釋迦如來之智慧光明，照破無明。",
            "description_ja": "計都星は月の降交点にして、停滞と隠晦を司る星なり。物事の進展が見えにくく、方向感を失いやすい年。釈迦如来の根本智に帰依し、焦らず着実に内なる修行を積むことで、やがて無明の霧が晴れる時を待つ。",
            "core_teaching": "釋迦如來「四聖諦」——苦的存在不是為了折磨你，是為了讓你找到離苦的道路。",
            "practice_focus": "懺悔消業、抄經禮佛、精進不懈",
            "recommended_practices": ["釋迦如來法", "光明真言法", "寫經"],
            "mantra": {
                "buddha": "釋迦如來",
                "name": "釋迦如來真言",
                "text": "ノウマク サンマンダ ボダナン バク",
                "reading": "のうまく さんまんだ ぼだなん ばく",
                "siddham_bija": "バク",
                "siddham_roman": "bha\u1e25",
                "siddham_unicode": "\U000115A5\U000115BE"
            },
            "homa_type": "息災護摩",
            "homa_description": "以息災護摩淨化宿業，迴向罪障消滅、身心清淨",
            "theme": {
                "title": "業障清淨之年",
                "description": (
                    "計都星的暗影中，業障如同積雪融化般顯現。不舒服是正常的——毒素排出時本來就會不適。"
                    "釋迦如來在成道前也經歷了最猛烈的魔障考驗。"
                    "你正在經歷的，就是修行路上的「排毒反應」。忍過去，前方就是清淨的道路。"
                    "懺悔是最有力的淨障法門。真心面對自己的過錯，業障才能真正消融。"
                )
            },
            "category_practice": {
                "career": "工作上的阻滯是業障的顯現。不要怨天尤人，以「逆來順受」的態度面對。同時積極懺悔，在心裡對過去世可能傷害過的眾生真誠道歉。業障消了，路自然就通了。",
                "love": "關係中的困難可能是宿世因緣。以平等心面對每一個進入你生命的人。對於造成你痛苦的人，試著感恩他們幫你消業。這不是逃避，是修行者的智慧。",
                "health": "注意身體的警訊，業障有時會透過身體來顯現。定期檢查、適當休息。每天抄寫《心經》一遍，安定身心。",
                "wealth": "不宜重大投資，守成為主。業障消融的過程中財運不穩定是正常的。把注意力放在內在的富足上，外在的匱乏只是暫時的。"
            },
            "advice": "計都星年要有「消業了業」的覺悟。不順遂的事不是在懲罰你，是在幫你清除前進路上的障礙。釋迦如來的真言是你的定心丸。每天早晚各持誦 108 遍，觀想佛陀的金光照耀全身，業障如烏雲般漸漸散去。抄寫《心經》也是非常有效的淨障方法。",
            "monthly_tips": {
                "1": "正月：發起懺悔的決心。列出今年要修的懺法。",
                "2": "涅槃會（2/15）：佛陀的涅槃是業盡果圓。觀修業障終有消盡的一天。",
                "3": "春季彼岸會：精進懺悔，迴向冤親債主。春天的生機助你重新開始。",
                "4": "灌佛會（4/8）：佛誕日的清淨能量助你淨化業障。",
                "5": "忍耐月：這段期間可能特別辛苦。咬牙忍過去，夏天會好轉。",
                "6": "夏安居開始：密集抄經、禮佛、懺悔。把夏安居當作淨障閉關。",
                "7": "盂蘭盆：以大懺悔心迴向一切冤親債主。這是化解宿怨的最佳月份。",
                "8": "漸入佳境月：業障開始鬆動，心會感覺比較輕了。繼續用功，不要鬆懈。",
                "9": "秋季彼岸會：秋風掃落葉，業障也在逐漸清落。",
                "10": "持續月：保持修行的節奏，不急不緩，穩步前行。",
                "11": "報恩講：感恩業障的教導。沒有障礙，你不會修得這麼深。",
                "12": "成道會（12/8）：佛陀成道前降魔成功。回顧這一年你降伏了多少業障。"
            },
            "warnings": ["春季三個月特別注意身心狀態", "不宜冒險或做重大改變"],
            "opportunities": ["消除宿業、淨化心靈的難得機會", "修懺悔法門的最佳年份"]
        },
        "月曜星": {
            "practice_name": "慈悲增長期",
            "practice_level": "增上",
            "description": (
                "月曜星年是慈悲心自然增長的一年。勢至菩薩以智慧之光接引眾生，"
                "這一年你的同理心和感受力特別敏銳，能夠真切地體會他人的苦樂。"
                "月的能量柔和而深遠，像月光灑滿大地般，你的慈悲也會照亮身邊的人。"
                "穩步前進、漸入佳境——這是修行累積到一定程度後自然出現的狀態。"
                "勢至菩薩代表「大勢」的智慧力量，看似柔和卻無比堅定。"
                "這一年適合拓展利他的範圍、建立修行的同參道友、參加共修。"
                "獨修是根基，共修是力量。月光下的修行者不再孤獨。"
            ),
            "description_classic": "月曜者，太陰也。梵名 Candra，主柔和慈愛。此年人緣殊勝，感受力增強。宜慈悲行善、護持眾生。大吉之年也。",
            "description_ja": "月曜星は太陰にして、柔和と慈愛を司る吉星なり。此の年は感受性が高まり人間関係に恵まれる。勢至菩薩の智慧光に導かれ、慈悲の実践と衆生護持に励むべき時期。直感力が冴え、修行にも深みが増す。",
            "core_teaching": "勢至菩薩「都攝六根，淨念相繼」——以專注和持續的力量，讓慈悲成為自然的習慣。",
            "practice_focus": "培養慈悲心、建立修行社群、參加共修",
            "recommended_practices": ["勢至菩薩法", "慈心觀", "共修法會"],
            "mantra": {
                "buddha": "勢至菩薩",
                "name": "勢至菩薩真言",
                "text": "オン サンザンザン サク ソワカ",
                "reading": "おん さんざんざん さく そわか",
                "siddham_bija": "サク",
                "siddham_roman": "sa\u1e25",
                "siddham_unicode": "\U000115AD\U000115BE"
            },
            "homa_type": "息災護摩",
            "homa_description": "以息災護摩消除隔閡，迴向慈悲增長、善緣具足",
            "theme": {
                "title": "慈悲增長之年",
                "description": (
                    "月光柔和地灑下來，你的慈悲心也在不知不覺中成長。"
                    "勢至菩薩的智慧光明指引你：慈悲不是軟弱，是真正的力量。"
                    "這一年會遇到很多讓你感動的人和事。珍惜每一次心被觸動的瞬間。"
                    "獨修的根基加上共修的力量，修行會進入一個新的階段。"
                )
            },
            "category_practice": {
                "career": "用慈悲心帶領團隊、服務客戶。今年的人脈會特別好，因為你的善意能被感受到。不要把工作只當作賺錢的手段，每一次服務都是修行的機會。",
                "love": "慈悲增長的一年，感情生活會比較順遂。但慈悲不是討好，是真正地為對方的幸福著想。有時候說真話比說好聽的話更慈悲。",
                "health": "月主水液，注意體內水分平衡和淋巴循環。慈心觀修持對身心健康有直接的幫助——研究顯示，慈悲心可以降低壓力荷爾蒙、增強免疫力。",
                "wealth": "善緣帶來善財。今年的財運跟人際關係直接相關。真誠地幫助他人，財富會以你意想不到的方式回流。"
            },
            "advice": "月曜星年的修行關鍵是「連結」。連結自己的慈悲心、連結修行的同參道友、連結需要幫助的眾生。勢至菩薩的真言持誦時，觀想柔和的月光從菩薩的寶冠中流出，照耀自己和一切眾生。找一個固定的共修團體加入，修行的路上有同伴會走得更遠。",
            "monthly_tips": {
                "1": "正月：發起慈悲心的大願。找到一個可以定期參加的共修團體。",
                "2": "涅槃會（2/15）：以慈悲心緬懷佛陀。佛陀一生都在為眾生付出。",
                "3": "春季彼岸會：以慈悲迴向，願一切眾生離苦得樂。",
                "4": "灌佛會（4/8）：佛陀誕生是慈悲的降臨。以歡喜心參加慶祝。",
                "5": "慈心月：每天修慈心觀，從自己開始，擴展到所有眾生。",
                "6": "夏安居開始：參加共修精進。跟同參道友一起用功，力量加倍。",
                "7": "盂蘭盆：以慈悲心供養、迴向。這個月的慈悲能量特別強。",
                "8": "拓展月：擴大慈悲的範圍，不只對親近的人慈悲，也對陌生人慈悲。",
                "9": "秋季彼岸會：秋月清明，適合深化慈心觀的修持。",
                "10": "分享月：把修行中獲得的安定和喜悅分享出去。",
                "11": "報恩講：以慈悲的行動回報一切善緣。",
                "12": "成道會（12/8）：佛陀的覺悟源自對眾生苦的深切體會。以慈悲心收尾。"
            },
            "warnings": ["慈悲要有智慧，不要變成濫好人", "注意不要因為過度同理而耗盡自己的能量"],
            "opportunities": ["培養慈悲心的最佳年份", "建立修行社群、結交善知識的好時機"]
        },
        "木曜星": {
            "practice_name": "法運亨通期",
            "practice_level": "弘法",
            "description": (
                "木曜星年如春天萬物生長，修行和世俗都在開花結果。藥師如來的琉璃光明照耀，"
                "身心健康、法緣殊勝，是修行者承擔更大責任的時候。"
                "世俗觀點的「大吉」在修行者眼中是「法運亨通」——不是個人的幸運，"
                "是佛法因緣成熟的表現。"
                "木的能量生長擴展，你的修行會自然地影響到更多人。"
                "藥師如來能治癒身心的一切疾病，你今年也能成為他人的「藥」——"
                "用你的修行、你的言行、你的存在，療癒身邊需要幫助的人。"
                "法運亨通不是終點，是另一個起點。更大的能量帶來更大的責任。"
            ),
            "description_classic": "木曜者，歲星也。梵名 Bṛhaspati，主發展繁榮。此年福德圓滿，百事成就。宜發大願、弘法利生。最上吉年也。",
            "description_ja": "木曜星は歳星とも呼ばれ、発展と繁栄を司る最上の吉星なり。此の年は福徳智慧ともに円満し、修行も世事も大いに成就する。薬師如来の瑠璃光に護られ、大願を発し弘法利生に邁進すべき時期。",
            "core_teaching": "藥師如來「琉璃光」——透明清淨如琉璃，修行者的心也應如此澄澈無染。",
            "practice_focus": "弘法度眾、承擔責任、修菩薩行",
            "recommended_practices": ["藥師如來法", "菩提心修持", "利他行願"],
            "mantra": {
                "buddha": "藥師如來",
                "name": "藥師如來真言",
                "text": "オン コロコロ センダリ マトウギ ソワカ",
                "reading": "おん ころころ せんだり まとうぎ そわか",
                "siddham_bija": "ベイ",
                "siddham_roman": "bhai",
                "siddham_unicode": "\U000115A5\U000115B9"
            },
            "homa_type": "息災護摩",
            "homa_description": "以息災護摩除障增福，迴向法運亨通、弘法事業圓滿",
            "theme": {
                "title": "法運亨通之年",
                "description": (
                    "木的生長力與藥師如來的加持結合，修行和生活都在蓬勃發展。"
                    "好的因緣如春筍般冒出來——新的法門、新的老師、新的同修。"
                    "但成長也意味著責任。你的一舉一動都在影響他人對佛法的印象。"
                    "以身作則比說一千遍道理更有力量。讓修行的成果自然流露。"
                )
            },
            "category_practice": {
                "career": "法運亨通帶動事業順利，但不要忘記初心。用修行者的心態經營事業：正命、正業、正精進。讓事業成為修行的延伸，而不是修行的障礙。",
                "love": "感情生活充實的一年。藥師如來的光明照亮關係中的每一個角落。以真誠和關懷建立深厚的連結。好的關係是修行最好的助緣。",
                "health": "藥師如來是身心健康的守護者。今年健康運佳，但要趁這個時候建立長期的養生習慣。每天持誦藥師咒七遍，觀想琉璃光淨化全身。",
                "wealth": "法運帶動財運，適合規劃長期的福報投資。在財務穩定的基礎上增加供養和布施的比例。真正的富足是內外兼備。"
            },
            "advice": "木曜星年是修行者「出關展翅」的時候。前幾年的沉潛、根基、學習、累積，在這一年開花結果。藥師如來的真言是你的護身光明。但最重要的提醒是：不要因為順利就忘記精進。春天的花開得越盛，夏天的果結得越飽滿——前提是你持續照料。",
            "monthly_tips": {
                "1": "正月：以藥師如來的十二大願為範本，設定今年的弘法願景。",
                "2": "涅槃會（2/15）：佛陀的教法如藥，要讓更多人服用這帖良藥。",
                "3": "春季彼岸會：春天的生長力最強。把修行的能量傳遞出去。",
                "4": "灌佛會（4/8）：慶祝佛誕，感恩佛法的滋養。組織或參與弘法活動。",
                "5": "生長月：修行和事業都在快速成長。保持節奏，不要失衡。",
                "6": "夏安居開始：在弘法的同時不忘自修。利他和自利雙軌並進。",
                "7": "盂蘭盆：以藥師如來的大願迴向一切眾生，願眾生身心安樂。",
                "8": "成果月：回顧上半年的成果，調整下半年的方向。",
                "9": "秋季彼岸會：秋天是收穫的季節，也是感恩的季節。",
                "10": "深化月：在廣度之外追求深度。選一個法門深入修持。",
                "11": "報恩講：以弘法利生的成果回報師恩和佛恩。",
                "12": "成道會（12/8）：這一年你離覺悟更近了嗎？誠實面對，發願繼續前行。"
            },
            "warnings": ["順境中更要保持精進，成功容易帶來懈怠", "弘法以身教為主，不要只說不做"],
            "opportunities": ["弘法度眾的絕佳時機", "修行和事業同時開花結果的年份"]
        }
    }

    def calculate_yearly_fortune(self, birth_date: date, year: int) -> dict:
        """
        計算每年運勢（九曜流年法）

        根據數え年計算當年的九曜星，結合本命宿元素推導年運。

        Args:
            birth_date: 出生日期
            year: 年份

        Returns:
            每年運勢資料
        """
        import random

        fortune_data = self._load_fortune_data()
        mansion = self.get_mansion(birth_date)
        user_index = mansion["index"]
        user_element = mansion["element"]

        # === 九曜流年法 ===
        kazoe_age = year - birth_date.year + 1
        star_index = (kazoe_age - 1) % 9
        star = self.KUYOU_STARS[star_index]
        star_element = star["element"]

        # 九曜等級 → 顯示分數（KUYOU_LEVEL_MAP）
        kuyou_level_score = self.KUYOU_LEVEL_MAP.get(star["level"], 50)

        # 九曜星與本命元素的關係（僅影響分類，不影響整體等級）
        if star_element:
            star_relation, star_bonus = self._calc_fortune_element_relation(user_element, star_element)
        else:
            # 羅喉星/計都星無元素，使用 conflicting 作為預設
            star_relation = "conflicting"
            star_bonus = -10

        base_score = kuyou_level_score

        warnings = []

        # 九曜年運對月趨勢的加持（大吉年底氣高，大凶年全面壓低）
        KUYOU_MONTHLY_MODIFIER = {
            "大吉": 8,
            "半吉": 3,
            "末吉": 0,
            "大凶": -8,
        }
        kuyou_modifier = KUYOU_MONTHLY_MODIFIER.get(star["level"], 0)

        # 計算每月趨勢（月宿關係 + 九曜年運加持）
        monthly_trend = []
        for m in range(1, 13):
            # 取得該月月宿（農曆月份）
            mid_date = date(year, m, 15)
            _, lunar_month_for_trend, _, _ = self.solar_to_lunar(mid_date)
            month_mansion_idx = self.MONTH_START_MANSION.get(lunar_month_for_trend, 0)
            month_mansion_elem = self.mansions_data[month_mansion_idx]["element"]

            # 本命宿 vs 月宿關係 → 等級
            month_relation = self.get_relation_type(user_index, month_mansion_idx)
            month_rel_level = self.RELATION_LEVEL_MAP.get(month_relation["type"], "chukichi")

            # 凌犯期間抽樣（每月 7 個取樣日）
            ryouhan_days = 0
            if m == 12:
                days_in_m = (date(year + 1, 1, 1) - date(year, m, 1)).days
            else:
                days_in_m = (date(year, m + 1, 1) - date(year, m, 1)).days
            sample_days = [1, 5, 10, 15, 20, 25, 30]
            sample_count = 0
            for sd in sample_days:
                if sd <= days_in_m:
                    sample_count += 1
                    ryouhan = self.check_ryouhan_period(date(year, m, sd))
                    if ryouhan:
                        ryouhan_days += 1

            ryouhan_ratio = ryouhan_days / sample_count if sample_count > 0 else 0
            if ryouhan_ratio > 0.5:
                month_rel_level = self._shift_level(month_rel_level, -2)
            elif ryouhan_ratio > 0:
                month_rel_level = self._shift_level(month_rel_level, -1)

            # 月宿等級分數 + 九曜年運加持 + 元素微調
            month_base = self.YEARLY_TREND_SCORE[month_rel_level] + kuyou_modifier

            _, user_month_bonus = self._calc_fortune_element_relation(user_element, month_mansion_elem)
            month_base += user_month_bonus // 2

            if star_element:
                _, star_month_bonus = self._calc_fortune_element_relation(month_mansion_elem, star_element)
                month_base += star_month_bonus // 4

            month_score = max(35, min(100, month_base))

            # 統計每月特殊日數量（甘露/金剛峯/羅刹）
            sd_counts = {"kanro": 0, "kongou": 0, "rasetsu": 0}
            for d in range(1, days_in_m + 1):
                try:
                    check_date = date(year, m, d)
                    wd = check_date.weekday()
                    jp_wd = (wd + 1) % 7
                    mansion_idx = self._get_corrected_mansion_index(check_date)
                    sd_type = self.SPECIAL_DAY_MAP.get((jp_wd, mansion_idx))
                    if sd_type in sd_counts:
                        sd_counts[sd_type] += 1
                except Exception:
                    pass

            monthly_trend.append({
                "month": m,
                "score": month_score,
                "relation_type": month_relation["type"],
                "ryouhan_ratio": round(ryouhan_ratio, 2),
                "special_day_counts": sd_counts
            })

        # 找出機會月份（分數最高的 3 個月）
        sorted_months = sorted(monthly_trend, key=lambda x: x["score"], reverse=True)
        opportunities = []
        opportunity_details = {
            "規劃": "制定年度目標、整理思緒、規劃未來方向。把大目標拆成每月可執行的小步驟，寫下來比放在腦袋裡有效得多。",
            "執行": "落實計畫、按部就班推進、將想法化為行動。這個月的執行力特別強，拖延已久的待辦事項趁現在一口氣清掉。",
            "人際": "拓展人脈、參加社交活動，可能遇到對你有幫助的人。主動約見三個你欣賞但久未聯繫的朋友，好的連結會帶來意想不到的機會。",
            "學習": "進修充電的好時機，考取證照、閱讀學習新技能。你的理解力和記憶力在這段期間會比平時好，報名那個一直想上的課程吧。",
            "事業": "積極爭取升遷機會、展現專業能力、建立職場影響力。主動向上管理，讓你的成果被看見，該談薪資就談，別不好意思。",
            "健康": "調養身心、建立運動習慣、關注身體警訊。每天至少 30 分鐘的有氧運動，搭配飲食調整，這個月投資健康的回報率最高。",
            "社交": "參加聚會活動、結交新朋友、維繫重要關係。跨出同溫層去認識不同領域的人，多元的交流會激發你的新想法。",
            "財運": "投資理財好時機、開拓收入來源、把握賺錢機會。不只是省錢，更要想辦法增加收入管道，副業或投資都值得認真研究。",
            "專業": "深耕專業領域、累積實力、建立個人品牌。選一個你最擅長的方向持續鑽研，寫文章或做分享，讓專業被更多人認識。",
            "家庭": "陪伴家人、處理家務事、增進家庭和諧。放下手機跟家人好好吃一頓飯、聊一次天，關係的品質比相處的時間更重要。",
            "內省": "沉澱反思、調整心態、重新審視人生方向。找一天獨處，把這一年做對了什麼、做錯了什麼寫下來，誠實面對自己才能真正進步。",
            "總結": "回顧年度成果、整理資源、為明年做準備。盤點今年的收穫和不足，把經驗變成明年可以直接套用的方法論。"
        }
        for m in sorted_months[:3]:
            month_name = f"{m['month']}月"
            theme = fortune_data["monthly_themes"].get(str(m["month"]), {})
            focus = theme.get("focus", "發展")
            detail = opportunity_details.get(focus, "把握機會積極行動")
            opportunities.append(f"{month_name}（運勢分數 {m['score']}）：{detail}")

        # 找出需注意的月份（分數最低的）
        worst_months = sorted(monthly_trend, key=lambda x: x["score"])[:2]
        for wm in worst_months:
            if wm["score"] < 55:
                warnings.append(f"{wm['month']}月運勢較低（{wm['score']}分），避免重大投資或簽約")

        base_score = max(35, min(95, base_score))

        # 各項運勢（等級分數 + 元素親和微調）
        star_element_for_cat = star_element if star_element else "土"

        def calc_yearly_category(category: str) -> int:
            cat_data = fortune_data["fortune_categories"][category]
            cat_bonus = 10 if user_element in cat_data["favorable_elements"] else 0
            year_boost = 5 if star_element_for_cat in cat_data["favorable_elements"] else 0
            star_adj = star_bonus // 4 if star_element else 0  # 九曜元素微調
            return max(35, min(100, base_score + cat_bonus + year_boost + star_adj))

        # 描述用的元素關係 key（九曜吉凶等級優先於元素關係）
        # 大凶：一律使用專屬 kyo 描述（務實安撫導向，非元素摩擦）
        # 末吉：正面元素降為 weakening
        # 大吉：負面/中性元素強制升為 generating
        # 半吉：衝突元素緩和為 weakening
        desc_relation = star_relation
        if star["level"] == "大凶":
            desc_relation = "kyo"
        elif star["level"] == "末吉":
            if star_relation in ("same", "generating"):
                desc_relation = "weakening"
        elif star["level"] == "大吉":
            if star_relation in ("neutral", "conflicting", "weakening"):
                desc_relation = "generating"
        elif star["level"] == "半吉":
            if star_relation == "conflicting":
                desc_relation = "weakening"

        # 年度建議
        advice_key = desc_relation if desc_relation in self.YEARLY_FORTUNE_ADVICE else "neutral"
        random.seed(f"{birth_date.isoformat()}{year}advice")
        advice = random.choice(self.YEARLY_FORTUNE_ADVICE[advice_key])

        # 年度主題：使用九曜星的 fortune_name 作為標題
        theme_key = desc_relation if desc_relation in self.YEARLY_THEME_DESCRIPTIONS else "neutral"
        random.seed(f"{birth_date.isoformat()}{year}theme")
        theme_description = random.choice(self.YEARLY_THEME_DESCRIPTIONS[theme_key])

        # 各項分述
        category_descriptions = {}
        for cat in ["career", "love", "health", "wealth"]:
            cat_key = desc_relation if desc_relation in self.YEARLY_CATEGORY_DESCRIPTIONS.get(cat, {}) else "neutral"
            random.seed(f"{birth_date.isoformat()}{year}catdesc_{cat}")
            cat_descs = self.YEARLY_CATEGORY_DESCRIPTIONS.get(cat, {}).get(cat_key, [""])
            category_descriptions[cat] = random.choice(cat_descs)

        # 年度策略分析
        strategy = self._generate_yearly_strategy(monthly_trend, star["level"], birth_date, year)

        # 月趨勢加入動態提示（取代固定 tip）
        for item in monthly_trend:
            item["tip"] = strategy["dynamic_tips"].get(item["month"], "")

        return {
            "year": year,
            "kuyou_star": {
                "name": star["name"],
                "reading": star["reading"],
                "level": star["level"],
                "fortune_name": star["fortune_name"],
                "element": star_element,
                "buddha": star["buddha"],
                "description": star["description"],
                "kazoe_age": kazoe_age
            },
            "your_mansion": {
                "name_jp": mansion["name_jp"],
                "reading": mansion["reading"],
                "element": user_element,
                "index": user_index
            },
            "fortune": {
                "overall": base_score,
                "career": calc_yearly_category("career"),
                "love": calc_yearly_category("love"),
                "health": calc_yearly_category("health"),
                "wealth": calc_yearly_category("wealth")
            },
            "theme": {
                "title": f"{star['fortune_name']}之年",
                "description": theme_description
            },
            "category_descriptions": category_descriptions,
            "monthly_trend": monthly_trend,
            "opportunities": opportunities,
            "warnings": warnings,
            "advice": advice,
            "shingon": self._build_shingon_data(star["name"]),
            "strategy": strategy
        }

    def _build_shingon_data(self, star_name: str) -> dict:
        """從 SHINGON_KUYOU_DATA 提取該九曜星的真言宗修行資料"""
        data = self.SHINGON_KUYOU_DATA.get(star_name, {})
        if not data:
            return {}
        return {
            "practice_name": data.get("practice_name", ""),
            "practice_level": data.get("practice_level", ""),
            "description": data.get("description", ""),
            "description_classic": data.get("description_classic", ""),
            "description_ja": data.get("description_ja", ""),
            "core_teaching": data.get("core_teaching", ""),
            "practice_focus": data.get("practice_focus", ""),
            "recommended_practices": data.get("recommended_practices", []),
            "mantra": data.get("mantra", {}),
            "homa_type": data.get("homa_type", ""),
            "homa_description": data.get("homa_description", ""),
            "theme": data.get("theme", {}),
            "category_practice": data.get("category_practice", {}),
            "category_labels": {
                "career": "法務", "love": "慈悲",
                "health": "身心", "wealth": "福德"
            },
            "advice": data.get("advice", ""),
            "monthly_tips": data.get("monthly_tips", {}),
            "warnings": data.get("warnings", []),
            "opportunities": data.get("opportunities", [])
        }

    def _generate_yearly_strategy(self, monthly_trend: list, kuyou_level: str, birth_date: date, year: int) -> dict:
        """
        年度趨吉避凶策略分析

        基於 monthly_trend 資料（score, relation_type, ryouhan_ratio）生成
        結構化的可行動建議。

        Args:
            monthly_trend: 12 個月的趨勢資料
            kuyou_level: 九曜等級（大吉/半吉/末吉/大凶）
            birth_date: 出生日期
            year: 年份

        Returns:
            策略分析 dict
        """
        # === 1. safe_havens：連續 2+ 個月 score >= 65 的區段 ===
        safe_havens = []
        streak_start = None
        for m in monthly_trend:
            if m["score"] >= 65:
                if streak_start is None:
                    streak_start = m["month"]
            else:
                if streak_start is not None:
                    streak_end = monthly_trend[monthly_trend.index(m) - 1]["month"]
                    if streak_end - streak_start + 1 >= 2:
                        # 判斷是否為栄親或業胎集群
                        cluster_months = [x for x in monthly_trend if streak_start <= x["month"] <= streak_end]
                        eishin_count = sum(1 for x in cluster_months if x["relation_type"] == "eishin")
                        gyotai_count = sum(1 for x in cluster_months if x["relation_type"] == "gyotai")
                        cluster_type = None
                        if eishin_count >= len(cluster_months) // 2:
                            cluster_type = "eishin_cluster"
                        elif gyotai_count >= len(cluster_months) // 2:
                            cluster_type = "gyotai_cluster"
                        safe_havens.append({
                            "start_month": streak_start,
                            "end_month": streak_end,
                            "avg_score": round(sum(x["score"] for x in cluster_months) / len(cluster_months)),
                            "cluster_type": cluster_type,
                            "description": self._safe_haven_description(streak_start, streak_end, cluster_type)
                        })
                    streak_start = None
        # 收尾：年末仍在連續高分
        if streak_start is not None:
            streak_end = monthly_trend[-1]["month"]
            if streak_end - streak_start + 1 >= 2:
                cluster_months = [x for x in monthly_trend if streak_start <= x["month"] <= streak_end]
                eishin_count = sum(1 for x in cluster_months if x["relation_type"] == "eishin")
                gyotai_count = sum(1 for x in cluster_months if x["relation_type"] == "gyotai")
                cluster_type = None
                if eishin_count >= len(cluster_months) // 2:
                    cluster_type = "eishin_cluster"
                elif gyotai_count >= len(cluster_months) // 2:
                    cluster_type = "gyotai_cluster"
                safe_havens.append({
                    "start_month": streak_start,
                    "end_month": streak_end,
                    "avg_score": round(sum(x["score"] for x in cluster_months) / len(cluster_months)),
                    "cluster_type": cluster_type,
                    "description": self._safe_haven_description(streak_start, streak_end, cluster_type)
                })

        # === 2. best_months：score top 3 且無凌犯 ===
        candidates = [m for m in monthly_trend if m["ryouhan_ratio"] == 0]
        if len(candidates) < 3:
            candidates = sorted(monthly_trend, key=lambda x: (-x["score"], x["ryouhan_ratio"]))
        else:
            candidates = sorted(candidates, key=lambda x: -x["score"])
        best_months = []
        for m in candidates[:3]:
            rel_name = self.DAILY_FORTUNE_RELATION_NAMES.get(m["relation_type"], "平")
            best_months.append({
                "month": m["month"],
                "score": m["score"],
                "relation_type": m["relation_type"],
                "description": self._best_month_description(m)
            })

        # === 3. caution_months：ryouhan >= 0.5 或安壊且 score < 45 ===
        caution_months = []
        for m in monthly_trend:
            reasons = []
            if m["ryouhan_ratio"] >= 0.5:
                pct = int(m["ryouhan_ratio"] * 100)
                reasons.append(f"凌犯佔比 {pct}%")
            if m["relation_type"] == "ankai" and m["score"] < 45:
                reasons.append("安壊低分")
            if m["score"] < 45:
                reasons.append(f"分數偏低（{m['score']}）")
            if reasons:
                caution_months.append({
                    "month": m["month"],
                    "score": m["score"],
                    "reasons": reasons,
                    "description": self._caution_month_description(m, reasons)
                })

        # === 4. ryouhan_outlook：全年凌犯概覽 ===
        ryouhan_months = [m for m in monthly_trend if m["ryouhan_ratio"] > 0]
        total_ryouhan_ratio = sum(m["ryouhan_ratio"] for m in monthly_trend) / 12
        ryouhan_month_nums = [m["month"] for m in ryouhan_months]

        # 找連續凌犯群
        consecutive_groups = []
        if ryouhan_month_nums:
            group = [ryouhan_month_nums[0]]
            for i in range(1, len(ryouhan_month_nums)):
                if ryouhan_month_nums[i] == ryouhan_month_nums[i - 1] + 1:
                    group.append(ryouhan_month_nums[i])
                else:
                    if len(group) >= 2:
                        consecutive_groups.append(group)
                    group = [ryouhan_month_nums[i]]
            if len(group) >= 2:
                consecutive_groups.append(group)

        ryouhan_outlook = {
            "affected_months": ryouhan_month_nums,
            "total_ratio": round(total_ryouhan_ratio, 2),
            "consecutive_groups": consecutive_groups,
            "description": self._ryouhan_outlook_description(ryouhan_month_nums, consecutive_groups, total_ryouhan_ratio)
        }

        # === 5. yearly_rhythm：年度節奏 ===
        first_half = [m["score"] for m in monthly_trend if m["month"] <= 6]
        second_half = [m["score"] for m in monthly_trend if m["month"] > 6]
        avg_first = sum(first_half) / len(first_half) if first_half else 60
        avg_second = sum(second_half) / len(second_half) if second_half else 60

        # 找最低點位置來判斷 V 型
        scores = [m["score"] for m in monthly_trend]
        min_month_idx = scores.index(min(scores))
        max_month_idx = scores.index(max(scores))

        diff = avg_first - avg_second
        if diff >= 10:
            rhythm_type = "front_heavy"
        elif diff <= -10:
            rhythm_type = "back_heavy"
        elif min_month_idx in range(3, 9) and avg_first > min(scores) + 10 and avg_second > min(scores) + 10:
            rhythm_type = "v_shape"
        elif max_month_idx in range(3, 9) and avg_first < max(scores) - 10 and avg_second < max(scores) - 10:
            rhythm_type = "inv_v_shape"
        else:
            rhythm_type = "stable"

        rhythm_descriptions = {
            "front_heavy": "上半年氣勢較強，建議把重要決策和行動集中在前六個月，下半年轉為守成鞏固。",
            "back_heavy": "下半年運勢漸入佳境，上半年先做好準備和累積，等時機成熟再全力推進。",
            "v_shape": f"年中（{min_month_idx + 1}月前後）是低谷期，前後兩端相對穩定。低谷期專注內省和調整，不急著做決定。",
            "inv_v_shape": f"年中（{max_month_idx + 1}月前後）是全年高峰，把握中段黃金期集中火力，年頭年尾則放慢步調。",
            "stable": "全年節奏平穩，沒有太大起伏，適合持續穩定地推進長期目標。"
        }

        yearly_rhythm = {
            "type": rhythm_type,
            "first_half_avg": round(avg_first),
            "second_half_avg": round(avg_second),
            "description": rhythm_descriptions[rhythm_type]
        }

        # === 6. dynamic_tips：取代固定月度提示 ===
        dynamic_tips = {}
        for m in monthly_trend:
            dynamic_tips[m["month"]] = self._generate_dynamic_tip(m)

        return {
            "safe_havens": safe_havens,
            "best_months": best_months,
            "caution_months": caution_months,
            "ryouhan_outlook": ryouhan_outlook,
            "yearly_rhythm": yearly_rhythm,
            "dynamic_tips": dynamic_tips
        }

    def _safe_haven_description(self, start: int, end: int, cluster_type: str | None) -> str:
        """避風港區段的描述文字"""
        period = f"{start}-{end}月"
        if cluster_type == "eishin_cluster":
            return f"{period}連續栄親高分，這段期間是全年最穩固的避風港，適合推進重要事項。"
        elif cluster_type == "gyotai_cluster":
            return f"{period}連續業胎月，前世因緣深厚的時期，人際合作和共同事業特別順利。"
        return f"{period}連續高分段，運勢穩定向好，適合積極行動和做出重要決定。"

    def _best_month_description(self, m: dict) -> str:
        """最佳月份的建議文字"""
        rel = m["relation_type"]
        score = m["score"]
        month = m["month"]

        if rel == "eishin":
            return f"{month}月栄親月（{score}分），全年最佳行動期之一，大膽推進計畫。"
        elif rel == "gyotai":
            return f"{month}月業胎月（{score}分），適合合作、簽約、建立夥伴關係。"
        elif rel == "mei":
            return f"{month}月命月（{score}分），本命能量強化，適合開創性的行動。"
        elif score >= 75:
            return f"{month}月高分（{score}分），運勢良好，把握機會積極行動。"
        return f"{month}月（{score}分），相對穩定的時期，可安排重要事務。"

    def _caution_month_description(self, m: dict, reasons: list) -> str:
        """警戒月的描述文字"""
        month = m["month"]
        if m["ryouhan_ratio"] >= 0.5:
            return f"{month}月凌犯嚴重，吉凶逆轉機率高，避免重大決策和簽約。守勢為主，等待時機。"
        elif m["relation_type"] == "ankai":
            return f"{month}月安壊月，關係容易破裂，避免衝突和冒險，低調行事。"
        return f"{month}月運勢偏低（{m['score']}分），保守行事，不宜冒進。"

    def _ryouhan_outlook_description(self, months: list, groups: list, ratio: float) -> str:
        """全年凌犯概覽描述"""
        if not months:
            return "今年沒有凌犯月份，全年運勢走向清晰可預測。"

        parts = []
        if groups:
            for g in groups:
                parts.append(f"{g[0]}-{g[-1]}月連續{len(g)}個月凌犯")
        scattered = [m for m in months if not any(m in g for g in groups)]
        if scattered:
            parts.append(f"{', '.join(str(m) for m in scattered)}月零星凌犯")

        advice = ""
        if ratio >= 0.3:
            advice = "凌犯佔比偏高，今年整體需謹慎行事，重要決策盡量安排在非凌犯月。"
        elif groups:
            longest = max(groups, key=len)
            advice = f"留意{longest[0]}-{longest[-1]}月連續凌犯期，這段期間盡量避開重大行動。"
        else:
            advice = "凌犯零星分布，影響有限，留意個別月份即可。"

        return "。".join(parts) + "。" + advice

    def _generate_dynamic_tip(self, m: dict) -> str:
        """根據月份數據動態生成月度提示"""
        score = m["score"]
        rel = m["relation_type"]
        ryouhan = m["ryouhan_ratio"]

        # 高分 + 栄親
        if score >= 80 and rel == "eishin":
            return "栄親高分月，放手去做想做的事，成功率高。"
        # 高分 + 業胎
        if score >= 80 and rel == "gyotai":
            return "業胎高分月，人際合作會帶來好結果，主動出擊。"
        # 高分 + 凌犯
        if score >= 70 and ryouhan > 0.3:
            return "分數不錯但有凌犯干擾，好事多磨，耐心處理意外狀況。"
        # 高分一般
        if score >= 75:
            return "運勢穩定偏高，適合推進計畫和做決定。"
        # 中等 + 無凌犯
        if 60 <= score < 75 and ryouhan == 0:
            return "中等穩定，按部就班推進，不急不緩。"
        # 中等 + 凌犯
        if 60 <= score < 75 and ryouhan > 0:
            return "運勢中等偏有凌犯波動，遇到反覆屬正常，穩住心態。"
        # 低分 + 重凌犯
        if score < 50 and ryouhan >= 0.5:
            return "凌犯嚴重加上低分，守勢為主，避免冒險和重大決策。"
        # 低分 + 安壊
        if score < 50 and rel == "ankai":
            return "安壊低分月，人際關係容易緊張，低調行事、遠離是非。"
        # 低分一般
        if score < 50:
            return "運勢偏低，養精蓄銳，為下個高峰期做準備。"
        # 中偏低
        return "運勢平穩，做好手邊的事，不需要太大動作。"

    def _generate_monthly_strategy(self, weekly_data: list, all_daily: list, ryouhan_count: int, days_in_month: int) -> dict:
        """
        月度趨吉避凶策略分析

        基於每日運勢資料生成 best_days、avoid_days、action_windows。

        Args:
            weekly_data: 週次資料列表
            all_daily: 每日概覽資料列表
            ryouhan_count: 凌犯天數
            days_in_month: 該月天數

        Returns:
            月度策略 dict
        """
        # === 1. best_days：top 3 高分日（score >= 70，無凌犯/羅刹/命/胎/業/壊） ===
        # 注意：不再整體排除 is_dark_week，原典各日吉凶不同
        # 但命/胎/業/壊日即使高分也不應推薦（原典禁忌）
        _excluded_day_types = ("命の日", "胎の日", "業の日", "壊の日")
        clean_high = [d for d in all_daily
                      if d["score"] >= 70
                      and not d.get("ryouhan_active", False)
                      and not (d.get("special_day") and "羅刹" in (d.get("special_day") or ""))
                      and d.get("sanki_day_type", "") not in _excluded_day_types]
        clean_high.sort(key=lambda x: -x["score"])
        best_days = []
        for d in clean_high[:3]:
            best_days.append({
                "date": d["date"],
                "weekday": d["weekday"],
                "score": d["score"],
                "reason": self._best_day_reason(d)
            })

        # === 2. avoid_days：安壊+凌犯、暗黒+羅刹等危險組合 ===
        avoid_days = []
        for d in all_daily:
            dangers = []
            if d.get("ryouhan_active") and d.get("is_dark_week"):
                dangers.append("凌犯+暗黒の一週間")
            elif d.get("ryouhan_active") and d.get("special_day") and "羅刹" in (d.get("special_day") or ""):
                dangers.append("凌犯+羅刹日")
            elif d.get("is_dark_week") and d.get("special_day") and "羅刹" in (d.get("special_day") or ""):
                dangers.append("暗黒+羅刹日")
            elif d["score"] < 40 and d.get("ryouhan_active"):
                dangers.append("凌犯低分")

            if dangers:
                avoid_days.append({
                    "date": d["date"],
                    "weekday": d["weekday"],
                    "score": d["score"],
                    "reasons": dangers
                })

        # === 3. action_windows：連續 3+ 天 score >= 60 的最佳行動區間 ===
        action_windows = []
        window_start = None
        window_days = []
        for d in all_daily:
            if d["score"] >= 60 and not d.get("ryouhan_active", False):
                if window_start is None:
                    window_start = d["date"]
                window_days.append(d)
            else:
                if window_start is not None and len(window_days) >= 3:
                    avg = round(sum(x["score"] for x in window_days) / len(window_days))
                    action_windows.append({
                        "start_date": window_start,
                        "end_date": window_days[-1]["date"],
                        "days": len(window_days),
                        "avg_score": avg,
                        "description": f"連續 {len(window_days)} 天穩定期（均分 {avg}），適合安排重要事務。"
                    })
                window_start = None
                window_days = []
        # 收尾
        if window_start is not None and len(window_days) >= 3:
            avg = round(sum(x["score"] for x in window_days) / len(window_days))
            action_windows.append({
                "start_date": window_start,
                "end_date": window_days[-1]["date"],
                "days": len(window_days),
                "avg_score": avg,
                "description": f"連續 {len(window_days)} 天穩定期（均分 {avg}），適合安排重要事務。"
            })

        return {
            "best_days": best_days,
            "avoid_days": avoid_days,
            "action_windows": action_windows
        }

    def _best_day_reason(self, d: dict) -> str:
        """最佳日的理由文字"""
        parts = [f"運勢 {d['score']} 分"]
        if d.get("special_day"):
            if "甘露" in d["special_day"]:
                parts.append("甘露日加持")
            elif "金剛" in d["special_day"]:
                parts.append("金剛峯日加持")
        return "，".join(parts)

    def calculate_yearly_fortune_range(self, birth_date: date, start_year: int, end_year: int) -> list:
        """
        批次計算多年運勢（九曜流年法）

        復用既有 calculate_yearly_fortune，逐年計算後彙整。

        Args:
            birth_date: 出生日期
            start_year: 起始年份
            end_year: 結束年份（含）

        Returns:
            多年運勢資料列表
        """
        results = []
        for year in range(start_year, end_year + 1):
            results.append(self.calculate_yearly_fortune(birth_date, year))
        return results

    # ==================== 通用吉日查詢 ====================

    # 吉日查詢類別定義
    # 關係類型對照：mei(命), gyotai(業胎), eishin(栄親), yusui(友衰), ankai(安壊), kisei(危成)
    LUCKY_DAY_CATEGORIES = {
        "career": {
            "name": "事業",
            "icon": "briefcase",
            "actions": {
                "interview": {"name": "求職面試", "favor_relations": ["eishin", "gyotai"], "favor_score": 75},
                "resign": {"name": "離職提出", "favor_relations": ["yusui"], "month_day_range": [1, 5, 25, 31], "favor_score": 65},
                "opening": {"name": "開業", "favor_relations": ["eishin", "mei"], "favor_score": 80},
                "contract": {"name": "簽約", "favor_relations": ["eishin", "gyotai"], "favor_score": 70}
            }
        },
        "study": {
            "name": "學業",
            "icon": "book",
            "actions": {
                "enrollment": {"name": "入學報到", "favor_relations": ["eishin", "gyotai"], "favor_score": 70},
                "exam": {"name": "考試", "favor_relations": ["eishin", "mei"], "favor_weekdays": [1, 3], "favor_score": 75},
                "tutor": {"name": "補習報名", "favor_relations": ["gyotai", "yusui"], "favor_score": 65}
            }
        },
        "housing": {
            "name": "居住",
            "icon": "house",
            "actions": {
                "move_in": {"name": "搬家入宅", "favor_relations": ["eishin", "mei"], "favor_score": 75},
                "renovation": {"name": "裝潢開工", "favor_relations": ["eishin"], "favor_weekdays": [0, 3], "favor_score": 70},
                "purchase": {"name": "購屋簽約", "favor_relations": ["eishin", "gyotai"], "favor_score": 80}
            }
        },
        "marriage": {
            "name": "婚姻",
            "icon": "heart",
            "actions": {
                "register": {"name": "結婚登記", "favor_relations": ["eishin", "mei", "gyotai", "yusui"], "favor_score": 70},
                "wedding": {"name": "婚禮", "favor_relations": ["eishin", "gyotai", "mei", "yusui"], "favor_score": 70},
                "engagement": {"name": "訂婚", "favor_relations": ["eishin", "gyotai", "yusui"], "favor_score": 70}
            }
        },
        "medical": {
            "name": "醫療",
            "icon": "heart-pulse",
            "actions": {
                "surgery": {"name": "手術", "favor_relations": ["eishin"], "avoid_relations": ["ankai", "kisei"], "favor_score": 80},
                "checkup": {"name": "健康檢查", "favor_relations": ["yusui", "eishin"], "favor_score": 65},
                "visit": {"name": "看診", "favor_relations": ["yusui"], "favor_score": 60}
            }
        },
        "travel": {
            "name": "旅行",
            "icon": "airplane",
            "actions": {
                "abroad": {"name": "出國", "favor_relations": ["eishin", "gyotai"], "favor_score": 75},
                "trip": {"name": "旅遊出發", "favor_relations": ["eishin", "yusui"], "favor_score": 70}
            }
        },
        "grooming": {
            "name": "剃髮",
            "icon": "brightness-high",
            "actions": {
                "teihatsu": {
                    "name": "剃髮",
                    "favor_relations": ["eishin", "mei", "gyotai"],
                    "avoid_relations": ["ankai"],
                    "favor_weekdays": [2, 4],
                    "avoid_weekdays": [1],
                    "avoid_birth_mansion": True,
                    "favor_mansions": [11, 8, 21],
                    "favor_score": 70
                }
            }
        },
        "beauty": {
            "name": "美容造型",
            "icon": "scissors",
            "actions": {
                "hair_coloring": {"name": "染髮", "favor_relations": ["eishin"], "favor_score": 65},
                "perm": {"name": "燙髮", "favor_relations": ["eishin", "gyotai"], "favor_score": 65},
                "nail": {"name": "美甲", "favor_relations": ["eishin", "yusui"], "favor_score": 60},
                "skincare": {"name": "護膚美容", "favor_relations": ["eishin", "mei"], "favor_score": 65},
                "tattoo": {"name": "紋繡/刺青", "favor_relations": ["eishin"], "avoid_relations": ["ankai"], "favor_score": 70}
            }
        },
        "dating": {
            "name": "感情",
            "icon": "chat-heart",
            "actions": {
                "first_date": {"name": "第一次約會", "favor_relations": ["eishin", "gyotai", "yusui"], "favor_weekdays": [4, 5], "favor_score": 70},
                "confession": {"name": "告白", "favor_relations": ["eishin", "mei", "yusui"], "favor_score": 70},
                "matchmaking": {"name": "相親", "favor_relations": ["eishin", "gyotai", "yusui"], "favor_score": 70},
                "breakup": {"name": "分手", "favor_relations": ["yusui", "ankai"], "avoid_relations": ["kisei"], "favor_score": 60}
            }
        },
        "shopping": {
            "name": "購物",
            "icon": "bag",
            "actions": {
                "clothing": {"name": "買衣服", "favor_relations": ["eishin", "yusui"], "favor_weekdays": [4, 5, 6], "favor_score": 65},
                "jewelry": {"name": "買首飾", "favor_relations": ["eishin", "mei"], "favor_score": 70},
                "big_purchase": {"name": "大額消費", "favor_relations": ["eishin", "gyotai"], "favor_score": 75}
            }
        }
    }

    def get_lucky_days(
        self,
        birth_date: date,
        category: str,
        action: str,
        days_ahead: int = 30
    ) -> dict:
        """
        通用吉日查詢

        Args:
            birth_date: 西曆生日
            category: 類別（career/study/housing/marriage/medical/travel/beauty/dating/shopping）
            action: 具體項目
            days_ahead: 查詢未來幾天（預設 30）

        Returns:
            吉日列表和建議
        """
        from datetime import timedelta

        # 驗證類別和項目
        if category not in self.LUCKY_DAY_CATEGORIES:
            raise ValueError(f"無效的類別: {category}")

        cat_config = self.LUCKY_DAY_CATEGORIES[category]
        if action not in cat_config["actions"]:
            raise ValueError(f"無效的項目: {action}")

        action_config = cat_config["actions"][action]

        mansion = self.get_mansion(birth_date)
        user_element = mansion["element"]
        user_index = mansion["index"]

        today = date.today()
        lucky_days = []
        avoid_days = []

        fortune_data = self._load_fortune_data()

        # 取得項目配置
        favor_relations = action_config.get("favor_relations", ["eishin"])
        avoid_relations = action_config.get("avoid_relations", ["ankai", "kisei"])
        favor_score = action_config.get("favor_score", 70)
        favor_weekdays = action_config.get("favor_weekdays", None)
        favor_mansions = action_config.get("favor_mansions", None)
        month_day_range = action_config.get("month_day_range", None)

        # 吉宿名稱對照（用於顯示）
        mansion_names = {11: "室宿", 8: "女宿", 21: "鬼宿"}

        for i in range(days_ahead):
            check_date = today + timedelta(days=i)

            # 計算當日運勢（含等級）
            daily_fortune = self.calculate_daily_fortune(birth_date, check_date)
            score = daily_fortune["fortune"]["overall"]
            day_level = daily_fortune["fortune"].get("level", "chukichi")

            # 取得當日資訊
            weekday = check_date.weekday()
            jp_weekday = (weekday + 1) % 7
            day_element = fortune_data["weekday_elements"][str(jp_weekday)]["element"]
            day_name = fortune_data["weekday_elements"][str(jp_weekday)]["name"]

            # 計算當日宿（修正後宿位）
            day_mansion_index = self._get_corrected_mansion_index(check_date)

            # 計算與本命宿的關係
            relation = self.get_relation_type(user_index, day_mansion_index)
            relation_type = relation["type"]

            # 判斷是否吉日
            is_lucky = False
            lucky_reason = ""

            # 統一品質評估（凌犯/壊の日/羅刹日/暗黒の一週間/甘露日/金剛峯日等）
            quality = self._evaluate_day_quality(daily_fortune, action)
            if quality["excluded"]:
                if len(avoid_days) < 5:
                    avoid_days.append({
                        "date": check_date.isoformat(),
                        "weekday": day_name,
                        "score": score,
                        "level": day_level,
                        "reason": quality["exclude_reason"]
                    })
                continue

            # 檢查避開的關係
            if relation_type in avoid_relations:
                if len(avoid_days) < 5:
                    avoid_days.append({
                        "date": check_date.isoformat(),
                        "weekday": day_name,
                        "score": score,
                        "level": day_level,
                        "reason": f"{relation['name']}日，不宜{action_config['name']}"
                    })
                continue

            # 檢查避開的星期（如火曜日忌剃髮）
            avoid_weekdays = action_config.get("avoid_weekdays", None)
            if avoid_weekdays and weekday in avoid_weekdays:
                if len(avoid_days) < 5:
                    avoid_days.append({
                        "date": check_date.isoformat(),
                        "weekday": day_name,
                        "score": score,
                        "level": day_level,
                        "reason": f"{day_name}不宜{action_config['name']}"
                    })
                continue

            # 檢查本命宿日（剃髮忌本命宿日）
            if action_config.get("avoid_birth_mansion") and day_mansion_index == user_index:
                if len(avoid_days) < 5:
                    avoid_days.append({
                        "date": check_date.isoformat(),
                        "weekday": day_name,
                        "score": score,
                        "level": day_level,
                        "reason": "本命宿日，不宜剃髮"
                    })
                continue

            # 檢查等級過低（小凶/凶 = 避開）
            if day_level in ("shokyo", "kyo"):
                if len(avoid_days) < 5:
                    avoid_days.append({
                        "date": check_date.isoformat(),
                        "weekday": day_name,
                        "score": score,
                        "level": day_level,
                        "reason": f"運勢{self.LEVEL_NAMES[day_level]['zh']}，建議避開"
                    })
                continue

            # 檢查特定月日範圍（如離職適合月初月底）
            if month_day_range:
                day_of_month = check_date.day
                in_range = any(
                    day_of_month <= month_day_range[1] or day_of_month >= month_day_range[2]
                    for _ in [1]
                )
                if not in_range:
                    continue

            # 判斷吉日條件
            if relation_type in favor_relations:
                is_lucky = True
                lucky_reason = f"{relation['name']}日，{self._get_relation_benefit(relation_type, action)}"
            elif favor_mansions and day_mansion_index in favor_mansions:
                is_lucky = True
                m_name = mansion_names.get(day_mansion_index, f"index {day_mansion_index}")
                lucky_reason = f"當日宿為{m_name}，傳統上特別適合{action_config['name']}。{m_name}之日淨身修儀，事半功倍"
            elif day_element == user_element and score >= favor_score:
                is_lucky = True
                lucky_reason = f"{day_name}（{day_element}曜）與你的本命元素相同，能量共振特別強烈。這天你的狀態比平時穩定，做需要專注和耐心的事情效率最高"
            elif self._is_generating(day_element, user_element) and score >= favor_score:
                is_lucky = True
                lucky_reason = f"{day_name}的{day_element}曜能量正在滋養你的本命元素，形成相生的良性循環。這天你會感覺做事順手，外在環境彷彿在配合你的節奏"
            elif score >= favor_score + 5:
                # 特定星期加分
                if favor_weekdays and weekday in favor_weekdays:
                    is_lucky = True
                    lucky_reason = f"整體運勢{score}分，加上{day_name}本身就適合{action_config['name']}，天時地利兼具"
                elif score >= favor_score + 10:
                    is_lucky = True
                    lucky_reason = f"整體運勢高達{score}分，各方面能量都處於高峰期，適合處理重要事務"

            if is_lucky and len(lucky_days) < 8:
                # 評級直接取等級名稱，再根據品質評估調整
                rating = self.LEVEL_NAMES.get(day_level, {"zh": "中吉"})["zh"]
                if quality["rating_shift"] != 0:
                    rating = self._shift_rating_name(rating, quality["rating_shift"])

                # 時段建議
                time_tip = self._get_personal_time_tip(day_element, user_element, action)

                day_entry: dict = {
                    "date": check_date.isoformat(),
                    "weekday": day_name,
                    "score": score,
                    "level": day_level,
                    "rating": rating,
                    "reason": lucky_reason,
                    "best_time": time_tip["best_time"],
                    "avoid_time": time_tip["avoid_time"]
                }
                if quality["conflicts"]:
                    day_entry["conflicts"] = quality["conflicts"]
                if quality["boosts"]:
                    day_entry["boosts"] = quality["boosts"]

                lucky_days.append(day_entry)

        return {
            "category": category,
            "category_name": cat_config["name"],
            "action": action,
            "action_name": action_config["name"],
            "your_mansion": {
                "name_jp": mansion["name_jp"],
                "reading": mansion["reading"],
                "element": user_element
            },
            "lucky_days": lucky_days,
            "avoid_days": avoid_days,
            "advice": self._get_action_advice(category, action, user_element)
        }

    # 吉日理由：按類別 + 關係類型提供差異化的好處描述
    LUCKY_DAY_BENEFITS = {
        "career": {
            "eishin": "貴人運極強，面試官、主管、合作方都對你有好印象。今天做出的職場決策成功率特別高，簽約、談判、提案都適合排在這天",
            "gyotai": "直覺特別準，能敏銳地判斷出哪個選擇對你的職涯最有利。如果有兩個 offer 在猶豫，今天的第一反應通常是對的",
            "mei": "你的存在感和說服力在今天達到高峰。面試展現的自信、開業的儀式感、簽約時的氣場，都會讓對方留下深刻印象",
            "yusui": "能量平穩順暢，適合處理需要冷靜判斷的事務。今天做的決定比較理性、不容易受情緒影響，是簽約和談合作的好時機"
        },
        "study": {
            "eishin": "學習運極佳。今天遇到的老師或同學可能成為長期的學習夥伴，報名的課程或考試也容易取得好結果",
            "gyotai": "理解力和記憶力處於高峰。考試時平時想不起來的知識今天會自然浮現，入學或報名的選擇也會是對的方向",
            "mei": "表達力強，適合口試或需要上台的考試。你的思路清晰、回答有條理，考官容易被你的自信吸引",
            "yusui": "心態穩定不緊張，適合需要持久專注力的考試。不會因為粗心或焦慮而失常，正常發揮就能拿到好成績"
        },
        "housing": {
            "eishin": "搬家和入宅的能量場極佳。新環境的氣場和你高度契合，住進去之後的生活品質會比預期好。購屋簽約也容易談到理想條件",
            "gyotai": "對房屋的直覺特別準。看房子的時候你能感受到哪些地方「對」、哪些地方「不對」。跟著感覺走，選到的房子通常不會讓你後悔",
            "mei": "你的氣場和新空間容易產生共鳴。搬家入宅之後，你會很快適應新環境。裝潢開工也容易順利推進",
            "yusui": "穩定的能量適合需要冷靜判斷的購屋決策。不容易被銷售話術影響，能夠理性分析條件再做決定"
        },
        "marriage": {
            "eishin": "婚姻能量最佳日。兩人的默契會被放大，登記或婚禮都充滿祝福的氛圍。這天互相許下的承諾特別有重量",
            "gyotai": "感情的直覺力在今天最強。訂婚或登記時你會確認「對，就是這個人」的感覺。緣分的共鳴在這天特別明顯",
            "mei": "今天的你散發著幸福的光環。婚禮的氛圍會特別好，到場的賓客也能感受到你們的喜悅。適合拍婚紗或舉辦儀式",
            "yusui": "穩定和諧的日子，適合想要安靜溫馨的登記或訂婚。沒有戲劇化的起伏，但充滿踏實的幸福感"
        },
        "medical": {
            "eishin": "醫療運佳。今天遇到的醫生比較能準確判斷你的狀況，手術和治療的順利度也比較高。醫病溝通特別順暢",
            "gyotai": "身體的自癒力今天比較強。健康檢查的結果也比較能如實反映你的狀況，不容易有假陽性或假陰性干擾判斷",
            "mei": "你能比平時更清楚地描述自己的症狀。醫生因此更容易做出準確的診斷。看診的效率和品質都比較好",
            "yusui": "心態平穩不焦慮，適合做需要放鬆心情的檢查項目。手術前的心理狀態也比較好，有助於術後恢復"
        },
        "travel": {
            "eishin": "旅行運極佳。出發時的能量順暢，旅途中容易遇到好的人和好的事。安排在這天出發的旅程，體驗通常超出預期",
            "gyotai": "旅行中的直覺特別準。選餐廳、選景點、選路線都容易踩到好的。不需要做太多攻略，隨性走反而能發現驚喜",
            "mei": "適合一個人或少數好友的深度旅行。你的感受力在今天特別敏銳，能從旅行中獲得比平時更多的感悟",
            "yusui": "旅途平順、不容易遇到延誤或意外。適合需要穩定行程的出差旅行，或者帶長輩出遊"
        },
        "grooming": {
            "eishin": "淨身修儀的最佳時機。剃髮時心念清明，身心調和。宿曜栄親之力加持，當日行法功德倍增",
            "gyotai": "業胎之日的淨身，能深化自身與宿曜的連結。剃髮後身輕意淨，直覺敏銳，適合接續行法或誦經",
            "mei": "本命宿能量最強之日。身儀端正本身即是修行的體現，今天的剃髮能強化本命宿的守護力",
            "yusui": "穩定安寧之日，適合從容淨身。不急不躁地完成剃髮，保持平常心即是最好的狀態"
        },
        "beauty": {
            "eishin": "美容運極佳。今天去做造型的效果特別好，設計師能準確抓到你想要的感覺。染髮、護膚的成品都會讓你滿意",
            "gyotai": "你對自己適合什麼造型的直覺今天特別準。如果一直在猶豫要不要嘗試新風格，今天是最好的時機",
            "mei": "今天做出的造型改變最能展現你的個人特色。適合做比較大幅度的形象改造，效果會比你想像中自然",
            "yusui": "穩定的日子，適合做維護型的美容。染髮補色、定期護膚、修剪整理，今天做的效果持久穩定"
        },
        "dating": {
            "eishin": "桃花運最旺的日子。約會的氣氛會比預期好，告白的成功率也高。你身上散發的魅力讓對方很難不被吸引",
            "gyotai": "你對對方的感覺今天特別準。第一次約會就能判斷出這個人適不適合深入交往。如果覺得對了，就大膽往前走",
            "mei": "你的吸引力在今天達到最大值。不管是相親還是約會，對方對你的第一印象都會非常好。自信地展現自己就好",
            "yusui": "適合不趕時間的深度約會。今天的節奏很舒服，兩個人可以慢慢聊、慢慢了解。不用刻意製造氣氛，自然就好"
        },
        "shopping": {
            "eishin": "購物運極佳。今天買到的東西滿意度高，特別是大額消費和首飾類。你的眼光比平時更準，不容易買到後悔的東西",
            "gyotai": "購物直覺很準。看到喜歡的東西不用猶豫太久，今天的第一反應通常是對的。適合買需要品味判斷的物品",
            "mei": "適合買能代表個人風格的物品。今天你對自己想要什麼特別清楚，不容易被行銷話術帶跑，買到的都是真心喜歡的",
            "yusui": "冷靜理性的購物日。不容易衝動消費，能在預算範圍內買到最划算的選擇。適合比價之後再下手的大額消費"
        }
    }

    def _get_relation_benefit(self, relation_type: str, action: str) -> str:
        """取得關係類型對特定行動的好處描述（按類別差異化）"""
        # 從 action 反查所屬的 category
        category = None
        for cat_key, cat_data in self.LUCKY_DAY_CATEGORIES.items():
            if action in cat_data["actions"]:
                category = cat_key
                break

        if category and category in self.LUCKY_DAY_BENEFITS:
            benefit = self.LUCKY_DAY_BENEFITS[category].get(relation_type)
            if benefit:
                return benefit

        # 通用 fallback
        fallback = {
            "eishin": "貴人運極強，周圍的人會自然而然地想幫你。這天做出的選擇成功率比平時高出許多",
            "gyotai": "直覺比平時更準。如果心裡對某件事有一個傾向，大膽跟著感覺走，結果通常不會讓你失望",
            "mei": "你的存在感和說服力在今天特別強。需要展現自己、爭取機會的事情排在這天最合適",
            "yusui": "能量平穩順暢，適合按部就班地推進計畫。這天做事效率穩定，不會有意外打亂節奏",
            "kisei": "需要比平時更謹慎，多花一點時間確認細節和備案",
            "ankai": "建議避開此日，能量場不利於重要決定"
        }
        return fallback.get(relation_type, "")

    def _get_action_advice(self, category: str, action: str, element: str) -> str:
        """取得特定行動的建議"""
        advice_templates = {
            "career": {
                "interview": f"{element}性本命宿者，面試時展現你最擅長的專業領域。準備好兩三個能具體量化成果的案例，比泛泛而談有效。上午時段精神狀態最佳，面試排在十點左右的效果最好。",
                "resign": f"{element}性本命宿者，離職時保持專業態度，把交接做好是對自己負責。選擇月初或月底提出，給雙方足夠的緩衝時間。不管離開的原因是什麼，好好道別比默默消失更有格局。",
                "opening": f"{element}性本命宿者，開業當天的氣場會影響初期的營運節奏。穿戴與本命元素相合的顏色出席、邀請你信任的朋友到場支持。開業前三個月專注在產品品質而非行銷曝光。",
                "contract": f"{element}性本命宿者，簽約前至少留兩天時間仔細審閱條款。不理解的地方不要不好意思問，模糊的條款事後容易產生爭議。選在你運勢高峰的時段簽署，心理狀態更從容。"
            },
            "study": {
                "enrollment": f"{element}性本命宿者，入學報到那天帶著好奇心去觀察新環境。主動跟同學打招呼、記住老師的名字，第一天的印象會影響整段學習經歷。",
                "exam": f"{element}性本命宿者，考試當天最重要的不是臨時抱佛腳，而是維持平常心。穿一件讓你覺得自信的衣服、提前到場熟悉環境、考前做三次深呼吸。你準備的比你以為的多。",
                "tutor": f"{element}性本命宿者，選補習班的時候先試聽再決定。老師的教學方式跟你的吸收習慣合不合比名氣重要，花一堂課的時間確認值不值得長期投入。"
            },
            "housing": {
                "move_in": f"{element}性本命宿者，搬家當天上午行動最順利。搬完之後在新家煮一壺水、開窗讓空氣流通，用你的生活痕跡取代空間原本的氣場。第一天晚上在新家好好吃一頓飯。",
                "renovation": f"{element}性本命宿者，裝潢開工前確認所有設計細節都已經溝通清楚。動工之後再改方案成本很高，不如前期多花一週確認。開工當天到場監工，展現你對品質的重視。",
                "purchase": f"{element}性本命宿者，購屋時理性分析比感性直覺重要。同一社區至少看三間再做決定，注意採光、通風、和周邊生活機能。房屋座向如果能跟本命元素相合是加分。"
            },
            "marriage": {
                "register": f"{element}性本命宿者，登記那天不用特別隆重，但要讓彼此感覺到這一刻的份量。帶一束花、一封手寫的信、或者一件有紀念意義的小禮物，多年後你們會慶幸留下了這些細節。",
                "wedding": f"{element}性本命宿者，婚禮當天你要做的只有一件事：享受這一天。其他的交給你信任的人去處理。提前跟主持人和攝影師溝通好節奏，確保你有足夠的時間跟重要的賓客說話。",
                "engagement": f"{element}性本命宿者，訂婚是兩個家庭的事，你的任務是讓雙方都感到被尊重。事前跟雙方父母分別溝通期待值，當天的流程盡量簡單明確。真誠比排場重要。"
            },
            "medical": {
                "surgery": f"{element}性本命宿者，手術前最重要的是充分了解流程和恢復計畫。把你的疑慮全部列出來跟醫生討論，不要帶著不安進手術室。準備好術後一到兩週的休養安排。",
                "checkup": f"{element}性本命宿者，健檢前一週維持正常生活即可，不用刻意調整飲食或作息。拿到報告後如果有紅字，不要自己上網查嚇自己，預約回診讓醫生解釋最準確。",
                "visit": f"{element}性本命宿者，看診前把症狀、發生時間、嚴重程度列成簡單的清單帶去。門診時間有限，條理清楚的描述能幫醫生更快做出判斷。有疑問就問，不要回家再後悔。"
            },
            "travel": {
                "abroad": f"{element}性本命宿者，出國前兩天把行李清單核對一次、把重要證件拍照備份在手機裡。到了當地先確認緊急聯絡方式和最近的醫療機構。準備做好了，剩下的就放心享受。",
                "trip": f"{element}性本命宿者，旅遊的精髓在於體驗而非打卡。不用把行程塞滿，留一些空白時間隨性探索。有時候迷路的那條小巷，反而藏著整趟旅行最美的風景。"
            },
            "grooming": {
                "teihatsu": f"{element}性本命宿者，剃髮前先沐浴淨身，以清晨或上午為佳。水曜日（水星之力，清淨智慧）和金曜日（金星之力，莊嚴身儀）是傳統上最適合剃髮的日子。火曜日災厄最重，務必避開。羅刹日不宜舉動百事，應避免。破壊の週中，原典記載栄日「剃髮吉」，其餘日型宜謹慎。剃髮後端坐片刻，收攝身心。"
            },
            "beauty": {
                "hair_coloring": f"{element}性本命宿者，染髮前一天不要洗頭，頭皮的天然油脂能保護髮質。選色的時候考慮你平時的穿著風格和膚色，百搭的色調比流行色更實用。",
                "perm": f"{element}性本命宿者，燙髮是比較大的造型改變，選擇跟你合作過的設計師最安心。提前一週把頭髮養好，避免在髮質受損的時候燙。",
                "nail": f"{element}性本命宿者，美甲選色搭配你本週的穿搭計畫會更實用。如果是第一次做凝膠甲，選有口碑的店家比選便宜的重要。",
                "skincare": f"{element}性本命宿者，做臉或護膚療程前一天避免去角質或使用刺激性保養品。療程後二十四小時內不要上妝、不要曬太陽。",
                "tattoo": f"{element}性本命宿者，紋繡或刺青是永久的改變，確認圖案和位置後至少等三天再決定。選擇衛生條件好、作品風格你喜歡的師傅。"
            },
            "dating": {
                "first_date": f"{element}性本命宿者，第一次約會地點選你熟悉的地方比較自在。不用刻意表演，做自己就好。對方如果值得深入了解，你的真實面貌比精心包裝更有吸引力。",
                "confession": f"{element}性本命宿者，告白不用準備長篇大論，把你的感受用最簡單的話說出來就好。選一個兩個人都放鬆的場合，不要在公共場所給對方壓力。",
                "matchmaking": f"{element}性本命宿者，相親時不要帶著「評估」的心態去看人。放輕鬆當作認識一個新朋友，聊天的品質比條件的比較更能看出一個人的本質。",
                "breakup": f"{element}性本命宿者，分手是一個需要勇氣的決定。做了就不要反覆，拖拖拉拉只會讓兩個人都更痛苦。好好說、面對面說、說清楚原因，是你對這段感情最後的尊重。"
            },
            "shopping": {
                "clothing": f"{element}性本命宿者，買衣服前先整理衣櫃，看看缺什麼再買什麼。帶一個審美品味好的朋友一起去，比自己猶豫半天有效率。",
                "jewelry": f"{element}性本命宿者，買首飾要試戴才知道適不適合。照片上好看的不一定適合你的膚色和體型，親自去店裡比較是最準的方法。",
                "big_purchase": f"{element}性本命宿者，大額消費前把預算上限寫下來，進店之後只看你預算範圍內的選項。不要被「加一點就能升級」的話術帶走，堅守底線是聰明消費的基本功。"
            }
        }
        return advice_templates.get(category, {}).get(action, "選擇運勢良好的日子進行，有助於事半功倍。")

    def _is_generating(self, elem1: str, elem2: str) -> bool:
        """檢查是否為相生關係（含日/月特殊元素）"""
        GENERATING_PAIRS = [
            ("木", "火"), ("火", "土"), ("土", "金"),
            ("金", "水"), ("水", "木"),
            ("日", "火"), ("月", "水")
        ]
        return (elem1, elem2) in GENERATING_PAIRS or (elem2, elem1) in GENERATING_PAIRS

    def _evaluate_day_quality(self, daily_fortune: dict, action_key: str | None = None) -> dict:
        """
        評估某天的品質（負面因素排除、正面因素加持）

        統一處理凌犯/壊の日/羅刹日/暗黒の一週間等排除條件，
        以及甘露日/金剛峯日/業の日/成の日等加持條件。

        Args:
            daily_fortune: calculate_daily_fortune 的回傳
            action_key: 具體行動（如 "denpo", "kanjo", "teihatsu"）

        Returns:
            品質評估結果
        """
        ryouhan = daily_fortune.get("ryouhan")
        sanki = daily_fortune.get("sanki", {})
        special_day = daily_fortune.get("special_day")
        day_type = sanki.get("day_type", "")

        excluded = False
        exclude_reason = ""
        rating_shift = 0
        shift_reasons: list[str] = []
        conflicts: list[str] = []
        boosts: list[str] = []

        # --- 排除條件 ---

        # 1. 凌犯期間
        if ryouhan:
            excluded = True
            exclude_reason = "凌犯期間，吉凶逆轉不穩定，不宜重要行動"
            conflicts.append("凌犯")

        # 2. 壊の日（原典：「宜作鎮壓、降伏怨讎及討伐，餘並不堪」）
        #    降伏法/降伏護摩可行，一般吉日仍排除
        if day_type == "壊の日":
            if not excluded:
                excluded = True
                exclude_reason = "壊の日，降伏法可行，餘事不宜"
            conflicts.append("壊の日")

        # 3. 羅刹日（凌犯中逆轉為吉，但凌犯本身已排除）
        if special_day and special_day.get("type") == "rasetsu":
            if not ryouhan:
                if not excluded:
                    excluded = True
                    exclude_reason = "羅刹日，災厄之日，務必避開"
                conflicts.append("羅刹日")

        # 4. 破壊の週：不再整體排除，改為逐日判斷三九日型
        #    原典 T21n1299 p.397c-398a 各日吉凶：
        #    - 業日：「所作善惡亦不成就，甚衰」→ 已由起始日判斷排除
        #    - 栄日：「諸吉事並大吉」→ 不排除
        #    - 衰日：「唯宜解除諸惡、療病」→ 由降級條件處理
        #    - 安日：「作壇場並吉」→ 不排除
        #    - 危日：「結交、婚姻、歡宴吉」→ 由降級條件處理
        #    - 成日：「修道學問、作諸成就法並吉」→ 不排除
        #    - 壊日：「宜作鎮壓、降伏」→ 已由壊日條件處理
        if sanki.get("is_dark_week", False):
            conflicts.append("破壊の週")
            # 剃髮特殊規則：暗黒の一週間中，栄日原典記載「出家人剃髮...吉」（p.397c-398a），
            # 故栄日不排除剃髮；其餘日型排除
            if action_key == "teihatsu" and not excluded:
                if day_type != "栄の日":
                    excluded = True
                    exclude_reason = "暗黒の一週間（非栄日），不宜剃髮"

        # --- 降級條件 ---

        # 5. 衰の日
        if day_type == "衰の日":
            rating_shift -= 1
            shift_reasons.append("衰の日")
            conflicts.append("衰の日")

        # 6. 危の日
        if day_type == "危の日":
            rating_shift -= 1
            shift_reasons.append("危の日")
            conflicts.append("危の日")

        # --- 加持條件 ---

        # 7. 甘露日
        if special_day and special_day.get("type") == "kanro":
            boosts.append("甘露日")
            if action_key in ("kanjo", "jukai"):
                rating_shift += 1
                shift_reasons.append("甘露日利灌頂/授戒")

        # 8. 金剛峯日
        if special_day and special_day.get("type") == "kongou":
            boosts.append("金剛峯日")

        # 9. 業の日（卷下 p.397c：「所作善惡亦不成就，甚衰」→ 排除）
        #    注：品三 p.391b 另記「所作皆吉祥」，兩處矛盾，系統從卷下
        if day_type == "業の日":
            if not excluded:
                excluded = True
                exclude_reason = "業の日，所作善惡亦不成就"
            conflicts.append("業の日")

        # 10. 命の日（原典：「不宜舉動百事」→ 排除）
        if day_type == "命の日":
            if not excluded:
                excluded = True
                exclude_reason = "命の日，本命宿回歸，不宜舉動百事"
            conflicts.append("命の日")

        # 11. 胎の日（原典：「不宜舉動百事」→ 排除）
        if day_type == "胎の日":
            if not excluded:
                excluded = True
                exclude_reason = "胎の日，再生準備之日，不宜舉動百事"
            conflicts.append("胎の日")

        # 12. 成の日 + 教學
        if day_type == "成の日" and action_key == "teaching":
            rating_shift += 1
            shift_reasons.append("成の日利教學")
            boosts.append("成の日")

        # 衝突判定：同時有實質衝突（非僅破壊の週標記）和加持 → 維持排除
        # 破壊の週只是資訊標記，逐日判斷由各日型條件處理
        real_conflicts = [c for c in conflicts if c != "破壊の週"]
        if boosts and real_conflicts and not excluded:
            excluded = True
            exclude_reason = f"{'、'.join(real_conflicts)}與{'、'.join(boosts)}衝突，宜避開"

        return {
            "excluded": excluded,
            "exclude_reason": exclude_reason,
            "rating_shift": rating_shift,
            "shift_reasons": shift_reasons,
            "conflicts": conflicts,
            "boosts": boosts,
        }

    @staticmethod
    def _shift_rating_name(rating_zh: str, shift: int) -> str:
        """在大吉/吉/中吉之間切換評級"""
        levels = ["中吉", "吉", "大吉"]
        try:
            idx = levels.index(rating_zh)
        except ValueError:
            return rating_zh
        new_idx = max(0, min(len(levels) - 1, idx + shift))
        return levels[new_idx]

    # ==================== 雙人吉日 ====================

    # 關係類型對應的吉日項目
    PAIR_LUCKY_ACTIONS = {
        "dating": {  # 交往對象
            "name": "交往對象",
            "actions": [
                {"key": "date", "name": "約會", "favor_relations": ["eishin", "gyotai", "yusui"], "favor_score": 70},
                {"key": "confession", "name": "告白", "favor_relations": ["eishin", "mei"], "favor_score": 75},
                {"key": "meet_parents", "name": "見家長", "favor_relations": ["eishin", "gyotai"], "favor_score": 80},
                {"key": "engagement", "name": "訂婚", "favor_relations": ["eishin", "gyotai"], "favor_score": 80},
                {"key": "register", "name": "結婚登記", "favor_relations": ["eishin", "mei", "gyotai"], "favor_score": 85},
                {"key": "wedding", "name": "婚禮", "favor_relations": ["eishin", "mei", "gyotai"], "favor_score": 85},
            ]
        },
        "spouse": {  # 配偶
            "name": "配偶",
            "actions": [
                {"key": "date", "name": "約會", "favor_relations": ["eishin", "gyotai", "yusui"], "favor_score": 65},
                {"key": "travel", "name": "旅遊", "favor_relations": ["eishin", "yusui"], "favor_score": 70},
                {"key": "discussion", "name": "重要商量", "favor_relations": ["eishin", "mei"], "favor_score": 75},
            ]
        },
        "parent": {  # 父母
            "name": "父母",
            "actions": [
                {"key": "visit", "name": "探親", "favor_relations": ["eishin", "yusui", "gyotai"], "favor_score": 65},
                {"key": "gift", "name": "送禮", "favor_relations": ["eishin", "yusui"], "favor_score": 60},
                {"key": "discussion", "name": "重要商談", "favor_relations": ["eishin", "mei"], "favor_score": 75},
            ]
        },
        "family": {  # 家人
            "name": "家人",
            "actions": [
                {"key": "gathering", "name": "聚會", "favor_relations": ["eishin", "yusui", "gyotai"], "favor_score": 65},
                {"key": "travel", "name": "旅遊", "favor_relations": ["eishin", "yusui"], "favor_score": 70},
                {"key": "gift", "name": "送禮", "favor_relations": ["eishin", "yusui"], "favor_score": 60},
            ]
        },
        "friend": {  # 朋友/同事
            "name": "朋友/同事",
            "actions": [
                {"key": "gathering", "name": "聚會", "favor_relations": ["eishin", "yusui", "gyotai"], "favor_score": 65},
                {"key": "collaboration", "name": "合作", "favor_relations": ["eishin", "gyotai"], "favor_score": 75},
                {"key": "travel", "name": "旅遊", "favor_relations": ["eishin", "yusui"], "favor_score": 70},
            ]
        },
        "master": {  # 師徒
            "name": "師徒",
            "actions": [
                {"key": "denpo", "name": "傳法", "favor_relations": ["eishin", "mei", "gyotai"], "favor_score": 80},
                {"key": "kanjo", "name": "灌頂", "favor_relations": ["eishin", "mei"], "favor_score": 80},
                {"key": "jukai", "name": "授戒", "favor_relations": ["eishin", "mei", "gyotai"], "favor_score": 80},
                {"key": "teaching", "name": "教學", "favor_relations": ["eishin", "gyotai", "yusui"], "favor_score": 70},
            ]
        }
    }

    def _get_personal_time_tip(self, day_element: str, user_element: str, action: str) -> dict:
        """根據七曜元素和本命元素生成個人吉日的時段建議"""

        ELEMENT_PEAK = {
            "日": "上午十點到十二點",
            "月": "下午六點到九點",
            "火": "下午兩點到四點",
            "水": "上午九點到十一點",
            "木": "上午十點到下午兩點",
            "金": "下午三點到五點",
            "土": "早上八點到十點",
        }

        ELEMENT_AVOID = {
            "日": "傍晚後能量消退，重要決定不要拖到晚上",
            "月": "正午前後能量弱，避免安排正式場合",
            "火": "晚間容易浮躁，不適合需要耐心的事",
            "水": "下午注意力容易下降，複雜事務排上午",
            "木": "傍晚後能量分散，日落前完成重要的事",
            "金": "上午能量還沒到位，重要的事排下午",
            "土": "午後容易拖延，早辦早好",
        }

        return {
            "best_time": ELEMENT_PEAK.get(day_element, "上午"),
            "avoid_time": ELEMENT_AVOID.get(day_element, "")
        }

    def _get_pair_time_tip(
        self,
        relation1_type: str,
        relation2_type: str,
        day_element: str,
        element1: str,
        element2: str,
        action_key: str
    ) -> dict:
        """根據雙方宿曜關係和七曜元素生成時段建議"""

        # 七曜元素對應的能量高峰時段
        ELEMENT_PEAK_HOURS = {
            "日": {"peak": "10:00-12:00", "label": "上午十點到十二點", "note": "日曜能量在正午前最強，適合正式場合"},
            "月": {"peak": "18:00-21:00", "label": "下午六點到九點", "note": "月曜能量在日落後漸強，適合輕鬆的互動"},
            "火": {"peak": "14:00-16:00", "label": "下午兩點到四點", "note": "火曜能量在午後達到高峰，適合需要活力的活動"},
            "水": {"peak": "09:00-11:00", "label": "上午九點到十一點", "note": "水曜能量在早晨清澈穩定，適合需要思考的事務"},
            "木": {"peak": "10:00-14:00", "label": "上午十點到下午兩點", "note": "木曜能量持續時間長，上午到午後都適合行動"},
            "金": {"peak": "15:00-17:00", "label": "下午三點到五點", "note": "金曜能量在午後偏晚時段最集中，適合簽約和決策"},
            "土": {"peak": "08:00-10:00", "label": "早上八點到十點", "note": "土曜能量在清晨最穩定，早起行動效果最好"},
        }

        # 避免的時段
        ELEMENT_AVOID_HOURS = {
            "日": "傍晚後日曜能量消退，重要決定不要拖到晚上",
            "月": "中午前後月曜能量最弱，避免安排正式場合",
            "火": "晚間火曜容易讓人浮躁，不適合需要耐心的溝通",
            "水": "下午容易疲倦，注意力下降，避免處理複雜事務",
            "木": "傍晚後能量分散，盡量在日落前完成重要的事",
            "金": "上午金曜能量還沒到位，重要的事排在下午比較好",
            "土": "午後土曜能量變得沉重，容易拖延，早辦早好",
        }

        peak = ELEMENT_PEAK_HOURS.get(day_element, ELEMENT_PEAK_HOURS["土"])
        avoid = ELEMENT_AVOID_HOURS.get(day_element, "")

        # 根據行動類型微調建議
        ACTION_TIME_TIPS = {
            "date": "約會選在能量高峰前後，兩人的互動會更自然放鬆。不用趕時間，留充裕的相處空間",
            "dinner": "晚餐約會選在六點半到七點入座。太早趕、太晚餓，剛好的時間讓談話更從容",
            "trip": "出發時間盡量排在上午。早出門的旅途心情比較好，也有更多時間享受目的地",
            "gift": "挑禮物選在自己狀態好的時段去，你的品味判斷力跟精神狀態直接相關",
            "meeting": "正式場合排在雙方都精神好的時段。開場前十分鐘到場，從容的態度是最好的開場白",
            "denpo": "傳法儀式排在早課後的上午時段，師徒雙方精神最清明。寅時起身淨身，辰時開壇最為如法",
            "kanjo": "灌頂以上午為宜，日光充足時結界清淨。儀式前師徒都要靜坐片刻收攝身心",
            "jukai": "授戒宜在上午，受者心神安定時理解戒律最為深入。儀式後留時間讓受者提問",
            "teaching": "教學選雙方都精神集中的時段。上午講義理、下午練實修，效率最好",
            "register": "登記和簽約選上午，精神清醒而且處理完還有一整天可以慶祝",
            "wedding": "婚禮儀式排在上午到中午，賓客的精神和心情都在最好的狀態",
            "engagement": "訂婚是溫馨的場合，下午茶時段或晚餐時段都適合，選雙方家庭方便的時間",
            "parent_visit": "拜訪長輩選上午或午後，避開午休時段。帶一份對方喜歡的點心，比空手更體面",
            "family_dinner": "家庭聚餐選週末中午或傍晚。人齊比時間完美更重要",
        }

        tip = ACTION_TIME_TIPS.get(action_key, "")

        # 如果雙方都是好關係，給更積極的提示
        good_relations = {"eishin", "gyotai", "mei", "yusui"}
        if relation1_type in good_relations and relation2_type in good_relations:
            if not tip:
                tip = f"雙方能量都處於良好狀態，{peak['label']}行動效果最好"
        elif not tip:
            tip = peak["note"]

        return {
            "best_time": peak["label"],
            "avoid_time": avoid,
            "tip": tip
        }

    def get_pair_lucky_days(
        self,
        birth_date1: date,
        birth_date2: date,
        relation_type: str,
        days_ahead: int = 30
    ) -> dict:
        """
        計算雙人吉日

        根據兩人的本命宿和關係類型，計算適合共同行動的吉日。

        Args:
            birth_date1: 第一人（自己）的生日
            birth_date2: 第二人（收藏對象）的生日
            relation_type: 關係類型（dating/spouse/parent/family/friend）
            days_ahead: 查詢未來幾天（預設 30）

        Returns:
            各項吉日列表
        """
        from datetime import timedelta

        # 驗證關係類型
        if relation_type not in self.PAIR_LUCKY_ACTIONS:
            raise ValueError(f"無效的關係類型: {relation_type}")

        relation_config = self.PAIR_LUCKY_ACTIONS[relation_type]

        # 取得雙方本命宿資料
        mansion1 = self.get_mansion(birth_date1)
        mansion2 = self.get_mansion(birth_date2)

        # 計算兩人相性
        compatibility = self.calculate_compatibility(birth_date1, birth_date2)

        today = date.today()
        fortune_data = self._load_fortune_data()

        # 為每個行動項目計算吉日
        results = []
        for action in relation_config["actions"]:
            lucky_days = []
            favor_relations = action["favor_relations"]
            favor_score = action["favor_score"]

            for i in range(days_ahead):
                check_date = today + timedelta(days=i)

                # 計算雙方當日運勢
                fortune1 = self.calculate_daily_fortune(birth_date1, check_date)
                fortune2 = self.calculate_daily_fortune(birth_date2, check_date)

                # 取雙方運勢平均
                avg_score = (fortune1["fortune"]["overall"] + fortune2["fortune"]["overall"]) // 2

                # 統一品質評估（雙方都檢查）
                q1 = self._evaluate_day_quality(fortune1, action["key"])
                q2 = self._evaluate_day_quality(fortune2, action["key"])

                if q1["excluded"] or q2["excluded"]:
                    continue

                # 取得當日資訊
                weekday = check_date.weekday()
                jp_weekday = (weekday + 1) % 7
                day_info = fortune_data["weekday_elements"][str(jp_weekday)]
                day_name = day_info["name"]
                day_element = day_info["element"]

                # 計算當日宿（修正後宿位）
                day_mansion_index = self._get_corrected_mansion_index(check_date)

                # 計算雙方與當日宿的關係
                relation1 = self.get_relation_type(mansion1["index"], day_mansion_index)
                relation2 = self.get_relation_type(mansion2["index"], day_mansion_index)

                # 判斷是否吉日
                is_lucky = False
                lucky_reason = ""

                # 雙方都是好關係
                if relation1["type"] in favor_relations and relation2["type"] in favor_relations:
                    is_lucky = True
                    lucky_reason = f"雙方與當日宿同時形成{relation1['name']}/{relation2['name']}的良好關係，能量場高度契合，適合一起{action['name']}"
                # 至少一方是好關係，另一方不是凶日
                elif (relation1["type"] in favor_relations and relation2["type"] not in ["ankai", "kisei"]) or \
                     (relation2["type"] in favor_relations and relation1["type"] not in ["ankai", "kisei"]):
                    if avg_score >= favor_score:
                        is_lucky = True
                        lucky_reason = f"雙方運勢平均 {avg_score} 分，加上其中一方與當日宿關係良好，整體氛圍適合{action['name']}"
                # 雙方運勢都很好
                elif avg_score >= favor_score + 10:
                    if relation1["type"] not in ["ankai", "kisei"] and relation2["type"] not in ["ankai", "kisei"]:
                        is_lucky = True
                        lucky_reason = f"雙方運勢平均高達 {avg_score} 分，兩人的狀態都處於高峰期，很適合一起{action['name']}"

                # master 關係額外規則：傳法/灌頂/授戒雙方都要 >= 60
                if is_lucky and relation_type == "master" and action["key"] in ("denpo", "kanjo", "jukai"):
                    if fortune1["fortune"]["overall"] < 60 or fortune2["fortune"]["overall"] < 60:
                        is_lucky = False

                if is_lucky and len(lucky_days) < 5:
                    rating = "大吉" if avg_score >= 85 else "吉" if avg_score >= 70 else "中吉"

                    # 品質調整：取雙方中較差的 rating_shift
                    min_shift = min(q1["rating_shift"], q2["rating_shift"])
                    if min_shift != 0:
                        rating = self._shift_rating_name(rating, min_shift)

                    # 合併衝突/加持標記
                    all_conflicts = list(set(q1["conflicts"] + q2["conflicts"]))
                    all_boosts = list(set(q1["boosts"] + q2["boosts"]))

                    # 時段建議
                    time_tip = self._get_pair_time_tip(
                        relation1["type"], relation2["type"],
                        day_element, mansion1["element"], mansion2["element"],
                        action["key"]
                    )

                    day_entry: dict = {
                        "date": check_date.isoformat(),
                        "weekday": day_name,
                        "score": avg_score,
                        "rating": rating,
                        "reason": lucky_reason,
                        "best_time": time_tip["best_time"],
                        "avoid_time": time_tip["avoid_time"],
                        "tip": time_tip["tip"]
                    }
                    if all_conflicts:
                        day_entry["conflicts"] = all_conflicts
                    if all_boosts:
                        day_entry["boosts"] = all_boosts

                    lucky_days.append(day_entry)

            results.append({
                "action": action["key"],
                "name": action["name"],
                "lucky_days": lucky_days
            })

        return {
            "relation_type": relation_type,
            "relation_name": relation_config["name"],
            "person1": {
                "mansion": mansion1["name_jp"],
                "reading": mansion1["reading"],
                "element": mansion1["element"]
            },
            "person2": {
                "mansion": mansion2["name_jp"],
                "reading": mansion2["reading"],
                "element": mansion2["element"]
            },
            "compatibility": {
                "relation": compatibility["relation"]["name"],
                "score": compatibility["score"],
                "description": compatibility["relation"]["description"]
            },
            "actions": results
        }

    # ==================== 吉日月曆 ====================

    # 雙人吉日白話建議模板
    # 依關係品質(good/neutral/bad) × action 分類
    PAIR_ADVICE_TEMPLATES = {
        # === good (eishin/gyotai) ===
        ("good", "date"): {
            "summary": "今天你們的互動會特別自然，不用刻意找話題也能聊得開心。氣氛好到連沉默都是舒服的。",
            "do": ["分享最近的想法或感受", "嘗試沒去過的地方", "拍幾張合照留念"],
            "avoid": ["催促對方做決定", "提起讓對方有壓力的話題"]
        },
        ("good", "confession"): {
            "summary": "對方今天對你的好感度比平時高，你說的話會被認真聽進去。直接表達的效果比暗示好。",
            "do": ["找一個兩人都放鬆的場合", "用簡單的話說出你的感受", "給對方回應的空間"],
            "avoid": ["在公共場所造成壓力", "準備太長的台詞反而不自然"]
        },
        ("good", "meet_parents"): {
            "summary": "長輩今天的接受度比較高，你的表現會被用善意的眼光看待。放鬆做自己就好。",
            "do": ["帶一份用心挑選的伴手禮", "主動幫忙但不過度表現", "真誠地回答問題"],
            "avoid": ["過度緊張反而讓氣氛僵硬", "話太多或太少都不好"]
        },
        ("good", "engagement"): {
            "summary": "雙方家庭的能量場今天特別和諧，談條件時容易找到讓雙方都舒服的平衡點。",
            "do": ["事前跟雙方確認期待", "保持從容的節奏", "記錄重要的約定"],
            "avoid": ["在細節上過度計較", "讓任何一方覺得被冷落"]
        },
        ("good", "register"): {
            "summary": "今天登記的能量場特別穩定，這個日期會成為你們回憶裡溫暖的起點。",
            "do": ["帶一件有紀念意義的小物", "儀式結束後一起吃頓好的", "手寫一段話給對方"],
            "avoid": ["行程排太滿反而匆忙", "忘記享受這個時刻"]
        },
        ("good", "wedding"): {
            "summary": "婚禮當天的氛圍會很好，賓客也能感受到你們的幸福。專心享受就好。",
            "do": ["提前跟攝影師溝通想要的畫面", "留時間跟重要的人說話", "接受不完美的小插曲"],
            "avoid": ["因為小細節影響心情", "行程太趕讓自己疲憊"]
        },
        ("good", "travel"): {
            "summary": "旅途中你們的默契會特別好，臨時改行程也能玩得開心。放輕鬆享受過程。",
            "do": ["讓彼此都有想去的地方", "留一些隨性探索的時間", "一起嘗試新事物"],
            "avoid": ["把行程排得太緊", "一個人決定所有事情"]
        },
        ("good", "discussion"): {
            "summary": "今天你們的溝通效率特別高，複雜的事情也能談得清楚。趁這天把重要的事情攤開來聊。",
            "do": ["先聽完對方的想法再回應", "把結論記下來", "感謝對方的坦誠"],
            "avoid": ["打斷對方的話", "用情緒取代論點"]
        },
        ("good", "visit"): {
            "summary": "今天去看長輩的氛圍會特別溫馨，你的陪伴讓對方感覺被重視。",
            "do": ["帶對方喜歡的東西", "多聽少說", "拍幾張照片記錄"],
            "avoid": ["趕時間的感覺", "只顧著滑手機"]
        },
        ("good", "gift"): {
            "summary": "今天送禮的時機很好，對方收到會特別開心。用心比貴重重要。",
            "do": ["挑選對方真正需要或喜歡的", "附上一句手寫的話", "當面送比寄送更有溫度"],
            "avoid": ["送太貴的東西反而造成壓力", "敷衍了事"]
        },
        ("good", "gathering"): {
            "summary": "今天的聚會氣氛會很好，大家都處於放鬆的狀態，容易聊出有意思的話題。",
            "do": ["選一個大家都方便的地點", "主動帶動話題", "拍張團體照"],
            "avoid": ["只跟特定的人聊天", "低頭看手機"]
        },
        ("good", "collaboration"): {
            "summary": "合作的默契今天特別好，分工明確之後效率會很高。是啟動新計畫的好時機。",
            "do": ["先確認雙方的目標一致", "各自負責擅長的部分", "定期回報進度"],
            "avoid": ["模糊的分工", "單方面改變方向"]
        },
        # === neutral (yusui/kisei/mei) ===
        ("neutral", "date"): {
            "summary": "今天的約會節奏不會太快也不會太慢，適合好好認識彼此。不用刻意製造驚喜。",
            "do": ["選一個安靜舒服的地方", "聊一些平時沒機會聊的話題", "保持自然的互動"],
            "avoid": ["安排太多活動", "期待值拉太高"]
        },
        ("neutral", "confession"): {
            "summary": "對方今天的心情平穩，會理性地考慮你說的話。結果不一定馬上有，但會被認真對待。",
            "do": ["選一個不趕時間的場合", "說完之後給對方思考的空間", "不管結果如何保持風度"],
            "avoid": ["用太戲劇化的方式", "要求對方馬上回答"]
        },
        ("neutral", "meet_parents"): {
            "summary": "長輩今天的態度中性偏正面，你的表現不需要特別完美，但基本禮貌要到位。",
            "do": ["準時到場", "回答問題時誠懇", "表現出你對關係的重視"],
            "avoid": ["過度謙虛或過度表現", "忽略任何一方家長"]
        },
        ("neutral", "engagement"): {
            "summary": "條件的溝通需要多一些耐心，雙方可能有不同的想法，但都能透過討論找到共識。",
            "do": ["提前準備好想討論的項目", "保持開放的態度", "把重要的約定寫下來"],
            "avoid": ["堅持己見不讓步", "在小事上花太多時間"]
        },
        ("neutral", "register"): {
            "summary": "登記的流程會順利完成，雖然不會有太多戲劇性的感動，但踏實的幸福感是真實的。",
            "do": ["把流程確認清楚", "帶齊需要的文件", "事後安排一個小慶祝"],
            "avoid": ["把這天跟其他雜事排在一起", "忘記留紀念照"]
        },
        ("neutral", "wedding"): {
            "summary": "婚禮會順利進行，可能有一兩個小插曲但不影響整體。事前的準備越充分越好。",
            "do": ["再確認一次流程表", "指派一個信任的人當天協調", "專注在你們自己的幸福"],
            "avoid": ["當天才處理遺漏的事情", "讓瑣事消耗你的精力"]
        },
        ("neutral", "travel"): {
            "summary": "旅途大致順利，偶爾可能需要調整計畫。保持彈性、互相配合就好。",
            "do": ["備好替代方案", "輪流決定行程", "不舒服就直說"],
            "avoid": ["把行程排到分秒不差", "一個人承擔所有決策"]
        },
        ("neutral", "discussion"): {
            "summary": "溝通需要比平時多一點耐心，但只要雙方都願意聽，就能找到解法。",
            "do": ["把想說的重點先整理好", "用「我覺得」而非「你應該」", "確認彼此的理解一致"],
            "avoid": ["帶著情緒開口", "翻舊帳"]
        },
        ("neutral", "visit"): {
            "summary": "探訪的氣氛平穩，對方會覺得被關心。不用準備太多，人到就是心意。",
            "do": ["帶一些日常的小東西", "聊聊近況", "幫忙做一些小事"],
            "avoid": ["待太久反而讓對方累", "只聊自己的事"]
        },
        ("neutral", "gift"): {
            "summary": "送禮的效果中規中矩，重點在於你有想到對方，而非禮物多貴重。",
            "do": ["選實用的東西", "包裝稍微用心一點", "看對方的反應調整"],
            "avoid": ["送跟對方需求無關的東西", "期待對方有很大的反應"]
        },
        ("neutral", "gathering"): {
            "summary": "聚會的氣氛需要有人帶動，但只要暖場起來就會越來越熱絡。",
            "do": ["準備一兩個話題備用", "注意比較安靜的人", "時間不用太長"],
            "avoid": ["讓場面冷掉太久", "只聊工作或八卦"]
        },
        ("neutral", "collaboration"): {
            "summary": "合作推進的速度中等，需要多確認方向是否一致。多花一點時間溝通是值得的。",
            "do": ["開始前先對齊目標", "遇到分歧馬上討論", "階段性確認成果"],
            "avoid": ["各做各的不溝通", "想當然以為對方理解"]
        },
        # === bad (ankai) ===
        ("bad", "date"): {
            "summary": "今天的互動容易有摩擦，可能是雞毛蒜皮的小事引發不必要的爭執。如果能改天更好。",
            "do": ["選輕鬆不需要做決定的活動", "對方說什麼先不急著反駁", "控制自己的情緒"],
            "avoid": ["去人太多或太吵的地方", "討論敏感話題", "期待太高"]
        },
        ("bad", "confession"): {
            "summary": "今天告白的成功率偏低，對方的接收狀態不太理想。建議等一個更好的時機。",
            "do": ["先按兵不動", "維持正常的互動就好", "觀察對方的狀態"],
            "avoid": ["衝動表白", "用訊息代替面對面", "把對方的冷淡當拒絕"]
        },
        ("bad", "meet_parents"): {
            "summary": "長輩今天的心情可能不太穩定，容易對小事挑剔。如果能延期到更好的日子是首選。",
            "do": ["降低期待值", "保持最基本的禮貌", "不用刻意表現"],
            "avoid": ["說太多自己的事", "急著讓對方喜歡你", "回嘴或辯解"]
        },
        ("bad", "travel"): {
            "summary": "旅途中容易出現延誤、意見不合或突發狀況。多預留緩衝時間，互相包容很重要。",
            "do": ["準備備案", "東西帶齊", "有狀況先深呼吸"],
            "avoid": ["趕行程", "把責任推給對方", "因為小事發脾氣"]
        },
        ("bad", "discussion"): {
            "summary": "今天的溝通容易雞同鴨講，說了半天還是各說各話。建議只處理緊急的事，其他改天談。",
            "do": ["只講最重要的一兩件事", "多用書面確認", "保留彈性"],
            "avoid": ["一次處理太多議題", "用指責的語氣", "在情緒不好時硬聊"]
        },
        ("bad", "visit"): {
            "summary": "今天拜訪的氣氛可能有點緊繃，對方的狀態不太好。簡短問候就好。",
            "do": ["控制拜訪時間", "帶一些對方需要的東西", "少說多做"],
            "avoid": ["待太久", "提起讓對方不舒服的話題", "強迫互動"]
        },
        ("bad", "gathering"): {
            "summary": "聚會中可能有些微妙的氣氛，有人心情不好或話不投機。保持低調就好。",
            "do": ["跟聊得來的人互動", "氣氛不對就早點離開", "不用勉強融入"],
            "avoid": ["挑起爭議話題", "喝太多", "在背後議論"]
        },
        ("bad", "collaboration"): {
            "summary": "合作的摩擦係數今天偏高，容易在方向或細節上產生分歧。能延後就延後。",
            "do": ["用書面確認重要決定", "保持專業態度", "有分歧先暫停"],
            "avoid": ["一意孤行", "在情緒上跟對方對抗", "做出無法挽回的決定"]
        },
        ("bad", "gift"): {
            "summary": "今天送禮的效果可能不如預期，對方的反應偏平淡。不是你的問題，是時機不對。",
            "do": ["如果一定要送就選實用的", "不要期待太大的反應", "改天補送效果更好"],
            "avoid": ["送太貴的東西", "要求對方馬上拆開"]
        },
        ("bad", "engagement"): {
            "summary": "今天談條件容易卡住，雙方的期待落差比較大。建議另找日子再繼續。",
            "do": ["先確認哪些是雙方的底線", "不用急著一次談完", "保持尊重"],
            "avoid": ["最後通牒式的談判", "在情緒不好時做決定", "讓任何一方感到被施壓"]
        },
        ("bad", "register"): {
            "summary": "建議換到更好的日期登記。如果非今天不可，保持平常心、專注在你們的決定本身。",
            "do": ["簡單完成流程", "事後安排一個放鬆的活動", "不要被小事影響心情"],
            "avoid": ["當天處理其他壓力大的事", "過度在意細節"]
        },
        ("bad", "wedding"): {
            "summary": "婚禮日期建議慎選。如果已經無法更改，做好萬全準備就能把風險降到最低。",
            "do": ["所有環節再確認一次", "多準備一兩個備案", "指定一個應急聯絡人"],
            "avoid": ["臨時更改流程", "讓自己承擔所有壓力"]
        },
        # === master 師徒 ===
        ("good", "denpo"): {
            "summary": "師徒之間的法脈傳承在今天特別順暢，弟子的根器和師父的加持力都處於高峰。",
            "do": ["提前齋戒淨身", "選清淨莊嚴的場所", "師徒雙方先靜坐收攝"],
            "avoid": ["倉促行事", "心緒未定時強行開壇"]
        },
        ("good", "kanjo"): {
            "summary": "灌頂的因緣殊勝，受者今天的領受力特別強，加持力容易相應。",
            "do": ["提前準備壇城法器", "受者前夜持戒清淨", "儀式後留時間回向"],
            "avoid": ["受者身心疲憊時勉強進行", "省略必要的前行"]
        },
        ("good", "jukai"): {
            "summary": "授戒的時機很好，受者今天對戒律的理解力和發願心都處於最佳狀態。",
            "do": ["事前講解戒條內容", "確認受者的發心", "儀式莊嚴如法"],
            "avoid": ["趕時間導致受者理解不足", "忽略受者的疑問"]
        },
        ("good", "teaching"): {
            "summary": "教學的效果今天特別好，弟子的專注力和理解力都比平時高。適合講深一點的內容。",
            "do": ["備好教材和實修指導", "觀察弟子的理解程度", "留時間答疑"],
            "avoid": ["一次講太多消化不了", "只講理論不給實修方向"]
        },
        ("neutral", "denpo"): {
            "summary": "傳法的條件中等，師徒雙方的狀態都還可以。做好準備工作能補足時機上的不足。",
            "do": ["充分的前行準備", "師徒先共修暖身", "確認雙方身心狀態"],
            "avoid": ["隨意開壇", "忽略準備工作"]
        },
        ("neutral", "kanjo"): {
            "summary": "灌頂可以進行但要多花心思在前行上。受者的狀態需要用準備工作來調整到位。",
            "do": ["加強前行修法", "確認受者的身心準備", "儀式按部就班"],
            "avoid": ["省略前行步驟", "對受者的準備度要求太低"]
        },
        ("neutral", "jukai"): {
            "summary": "授戒可以進行，受者的接受度中等。多花時間在戒條講解上會有更好的效果。",
            "do": ["逐條講解戒律", "給受者充分的思考時間", "確認受者真正理解"],
            "avoid": ["形式化地走流程", "忽略受者的個別狀況"]
        },
        ("neutral", "teaching"): {
            "summary": "教學效果普通，弟子的吸收速度中等。以基礎和複習為主比較有效率。",
            "do": ["複習上次的內容", "用具體例子說明", "進度不用太快"],
            "avoid": ["講全新的難度高的內容", "一直講不給弟子消化的時間"]
        },
        ("bad", "denpo"): {
            "summary": "傳法的時機不佳，師徒雙方的能量場容易干擾。強烈建議另擇吉日。",
            "do": ["延期到更好的日子", "如果不能延期就加強護摩前行", "師徒各自先調整狀態"],
            "avoid": ["在能量不穩定時傳承重要法脈", "忽略不吉的徵兆"]
        },
        ("bad", "kanjo"): {
            "summary": "灌頂建議改期。今天的能量場不利於加持力的傳遞，受者的領受也容易打折扣。",
            "do": ["改期是最好的選擇", "非改不可就大幅加強前行", "師父先獨修穩定自身"],
            "avoid": ["勉強進行形式上的灌頂", "在師父或受者狀態不佳時開壇"]
        },
        ("bad", "jukai"): {
            "summary": "授戒建議延期。受者今天的心念不夠穩定，勉強受戒反而容易產生障礙。",
            "do": ["另擇吉日", "讓受者多準備一段時間", "先進行預備的學戒課程"],
            "avoid": ["趕進度強行授戒", "忽略受者的身心狀態"]
        },
        ("bad", "teaching"): {
            "summary": "教學效果偏差，弟子的專注力和理解力今天都比較低。輕量的複習比硬教新東西好。",
            "do": ["輕鬆地複習舊內容", "聊一些修行體會", "早點結束讓弟子休息"],
            "avoid": ["講新的重要內容", "因為弟子理解慢而不耐煩"]
        },
    }

    def _get_pair_advice(self, relation_quality: str, action_key: str) -> Optional[dict]:
        """取得雙人吉日的白話建議"""
        advice = self.PAIR_ADVICE_TEMPLATES.get((relation_quality, action_key))
        if advice:
            return advice
        # 通用 fallback
        fallback = self.PAIR_ADVICE_TEMPLATES.get((relation_quality, "date"))
        return fallback

    @staticmethod
    def _classify_relation_quality(relation_type: str) -> str:
        """將宿曜關係分為 good/neutral/bad 三檔"""
        if relation_type in ("eishin", "gyotai"):
            return "good"
        elif relation_type in ("ankai",):
            return "bad"
        else:  # yusui, kisei, mei
            return "neutral"

    def get_lucky_days_calendar(
        self,
        birth_date: date,
        year: int,
        month: int,
        categories: list[str] | None = None
    ) -> dict:
        """
        取得整月吉日月曆（個人）

        掃描指定月份每一天，回傳以日期為 key 的吉日地圖。

        Args:
            birth_date: 西曆生日
            year: 年份
            month: 月份 (1-12)
            categories: 篩選的分類列表，None = 全部

        Returns:
            月曆吉日資料
        """
        import calendar as cal
        from datetime import timedelta

        mansion = self.get_mansion(birth_date)
        user_element = mansion["element"]
        user_index = mansion["index"]
        fortune_data = self._load_fortune_data()

        # 取得當月天數
        _, days_in_month = cal.monthrange(year, month)
        all_cats = self.LUCKY_DAY_CATEGORIES
        target_cats = {k: v for k, v in all_cats.items() if not categories or k in categories}

        days_map: dict[str, list] = {}
        mansion_names = {11: "室宿", 8: "女宿", 21: "鬼宿"}

        for day_num in range(1, days_in_month + 1):
            check_date = date(year, month, day_num)

            # 計算當日運勢
            daily_fortune = self.calculate_daily_fortune(birth_date, check_date)
            score = daily_fortune["fortune"]["overall"]
            day_level = daily_fortune["fortune"].get("level", "chukichi")

            # 取得當日資訊
            weekday = check_date.weekday()
            jp_weekday = (weekday + 1) % 7
            day_element = fortune_data["weekday_elements"][str(jp_weekday)]["element"]
            day_name = fortune_data["weekday_elements"][str(jp_weekday)]["name"]

            # 計算當日宿
            day_mansion_index = self._get_corrected_mansion_index(check_date)
            relation = self.get_relation_type(user_index, day_mansion_index)
            relation_type = relation["type"]

            date_key = check_date.isoformat()
            day_results = []

            # 統一品質評估（每日只算一次，action 無關的部分共用）
            quality_cache: dict[str, dict] = {}

            for cat_key, cat_config in target_cats.items():
                for act_key, action_config in cat_config["actions"].items():
                    favor_relations = action_config.get("favor_relations", ["eishin"])
                    avoid_relations = action_config.get("avoid_relations", ["ankai", "kisei"])
                    favor_score = action_config.get("favor_score", 70)
                    favor_weekdays = action_config.get("favor_weekdays", None)
                    favor_mansions = action_config.get("favor_mansions", None)

                    # 品質評估（含凌犯/壊の日/羅刹日/暗黒等排除）
                    if act_key not in quality_cache:
                        quality_cache[act_key] = self._evaluate_day_quality(daily_fortune, act_key)
                    quality = quality_cache[act_key]

                    if quality["excluded"]:
                        continue

                    # action 特有排除
                    if relation_type in avoid_relations:
                        continue
                    avoid_weekdays = action_config.get("avoid_weekdays", None)
                    if avoid_weekdays and weekday in avoid_weekdays:
                        continue
                    if action_config.get("avoid_birth_mansion") and day_mansion_index == user_index:
                        continue
                    if day_level in ("shokyo", "kyo"):
                        continue

                    # 判斷吉日條件
                    is_lucky = False
                    lucky_reason = ""

                    if relation_type in favor_relations:
                        is_lucky = True
                        lucky_reason = f"{relation['name']}日，{self._get_relation_benefit(relation_type, act_key)}"
                    elif favor_mansions and day_mansion_index in favor_mansions:
                        is_lucky = True
                        m_name = mansion_names.get(day_mansion_index, f"index {day_mansion_index}")
                        lucky_reason = f"當日宿為{m_name}，傳統上特別適合{action_config['name']}"
                    elif day_element == user_element and score >= favor_score:
                        is_lucky = True
                        lucky_reason = f"{day_name}（{day_element}曜）與你的本命元素相同，能量共振"
                    elif self._is_generating(day_element, user_element) and score >= favor_score:
                        is_lucky = True
                        lucky_reason = f"{day_name}的{day_element}曜能量滋養你的本命元素，形成相生"
                    elif score >= favor_score + 5:
                        if favor_weekdays and weekday in favor_weekdays:
                            is_lucky = True
                            lucky_reason = f"運勢{score}分，加上{day_name}適合{action_config['name']}"
                        elif score >= favor_score + 10:
                            is_lucky = True
                            lucky_reason = f"運勢高達{score}分，適合處理重要事務"

                    if is_lucky:
                        rating = self.LEVEL_NAMES.get(day_level, {"zh": "中吉"})["zh"]
                        if quality["rating_shift"] != 0:
                            rating = self._shift_rating_name(rating, quality["rating_shift"])
                        time_tip = self._get_personal_time_tip(day_element, user_element, act_key)

                        day_entry: dict = {
                            "category": cat_key,
                            "category_name": cat_config["name"],
                            "action": act_key,
                            "action_name": action_config["name"],
                            "score": score,
                            "rating": rating,
                            "reason": lucky_reason,
                            "best_time": time_tip["best_time"],
                            "avoid_time": time_tip["avoid_time"]
                        }
                        if quality["conflicts"]:
                            day_entry["conflicts"] = quality["conflicts"]
                        if quality["boosts"]:
                            day_entry["boosts"] = quality["boosts"]

                        day_results.append(day_entry)

            if day_results:
                days_map[date_key] = day_results

        return {
            "year": year,
            "month": month,
            "your_mansion": {
                "name_jp": mansion["name_jp"],
                "reading": mansion["reading"],
                "element": user_element,
                "index": user_index
            },
            "days": days_map
        }

    def get_pair_lucky_days_calendar(
        self,
        birth_date1: date,
        birth_date2: date,
        relation_type: str,
        year: int,
        month: int
    ) -> dict:
        """
        取得整月雙人吉日月曆

        掃描指定月份每一天，回傳以日期為 key 的吉日地圖，每個吉日附帶白話建議。

        Args:
            birth_date1: 第一人（自己）的生日
            birth_date2: 第二人（收藏對象）的生日
            relation_type: 關係類型（dating/spouse/parent/family/friend）
            year: 年份
            month: 月份 (1-12)

        Returns:
            月曆雙人吉日資料
        """
        import calendar as cal
        from datetime import timedelta

        if relation_type not in self.PAIR_LUCKY_ACTIONS:
            raise ValueError(f"無效的關係類型: {relation_type}")

        relation_config = self.PAIR_LUCKY_ACTIONS[relation_type]

        mansion1 = self.get_mansion(birth_date1)
        mansion2 = self.get_mansion(birth_date2)
        compatibility = self.calculate_compatibility(birth_date1, birth_date2)

        fortune_data = self._load_fortune_data()
        _, days_in_month = cal.monthrange(year, month)

        days_map: dict[str, list] = {}

        for day_num in range(1, days_in_month + 1):
            check_date = date(year, month, day_num)

            # 計算雙方當日運勢
            fortune1 = self.calculate_daily_fortune(birth_date1, check_date)
            fortune2 = self.calculate_daily_fortune(birth_date2, check_date)
            avg_score = (fortune1["fortune"]["overall"] + fortune2["fortune"]["overall"]) // 2

            # 取得當日資訊
            weekday = check_date.weekday()
            jp_weekday = (weekday + 1) % 7
            day_info = fortune_data["weekday_elements"][str(jp_weekday)]
            day_name = day_info["name"]
            day_element = day_info["element"]

            day_mansion_index = self._get_corrected_mansion_index(check_date)

            relation1 = self.get_relation_type(mansion1["index"], day_mansion_index)
            relation2 = self.get_relation_type(mansion2["index"], day_mansion_index)

            date_key = check_date.isoformat()
            day_results = []

            for action in relation_config["actions"]:
                favor_relations = action["favor_relations"]
                favor_score = action["favor_score"]

                # 統一品質評估（雙方都檢查）
                dq1 = self._evaluate_day_quality(fortune1, action["key"])
                dq2 = self._evaluate_day_quality(fortune2, action["key"])

                if dq1["excluded"] or dq2["excluded"]:
                    continue

                is_lucky = False
                lucky_reason = ""

                if relation1["type"] in favor_relations and relation2["type"] in favor_relations:
                    is_lucky = True
                    lucky_reason = f"雙方與當日宿同時形成{relation1['name']}/{relation2['name']}的良好關係，能量場高度契合"
                elif (relation1["type"] in favor_relations and relation2["type"] not in ["ankai", "kisei"]) or \
                     (relation2["type"] in favor_relations and relation1["type"] not in ["ankai", "kisei"]):
                    if avg_score >= favor_score:
                        is_lucky = True
                        lucky_reason = f"雙方運勢平均 {avg_score} 分，其中一方與當日宿關係良好"
                elif avg_score >= favor_score + 10:
                    if relation1["type"] not in ["ankai", "kisei"] and relation2["type"] not in ["ankai", "kisei"]:
                        is_lucky = True
                        lucky_reason = f"雙方運勢平均高達 {avg_score} 分，狀態都處於高峰期"

                # master 關係額外規則
                if is_lucky and relation_type == "master" and action["key"] in ("denpo", "kanjo", "jukai"):
                    if fortune1["fortune"]["overall"] < 60 or fortune2["fortune"]["overall"] < 60:
                        is_lucky = False

                if is_lucky:
                    rating = "大吉" if avg_score >= 85 else "吉" if avg_score >= 70 else "中吉"

                    # 品質調整
                    min_shift = min(dq1["rating_shift"], dq2["rating_shift"])
                    if min_shift != 0:
                        rating = self._shift_rating_name(rating, min_shift)

                    all_conflicts = list(set(dq1["conflicts"] + dq2["conflicts"]))
                    all_boosts = list(set(dq1["boosts"] + dq2["boosts"]))

                    time_tip = self._get_pair_time_tip(
                        relation1["type"], relation2["type"],
                        day_element, mansion1["element"], mansion2["element"],
                        action["key"]
                    )

                    # 白話建議
                    rq1 = self._classify_relation_quality(relation1["type"])
                    rq2 = self._classify_relation_quality(relation2["type"])
                    quality_order = {"bad": 0, "neutral": 1, "good": 2}
                    final_quality = rq1 if quality_order[rq1] <= quality_order[rq2] else rq2
                    advice = self._get_pair_advice(final_quality, action["key"])

                    day_entry: dict = {
                        "action": action["key"],
                        "name": action["name"],
                        "score": avg_score,
                        "rating": rating,
                        "reason": lucky_reason,
                        "best_time": time_tip["best_time"],
                        "avoid_time": time_tip["avoid_time"],
                        "tip": time_tip["tip"],
                        "advice": advice
                    }
                    if all_conflicts:
                        day_entry["conflicts"] = all_conflicts
                    if all_boosts:
                        day_entry["boosts"] = all_boosts

                    day_results.append(day_entry)

            if day_results:
                days_map[date_key] = day_results

        return {
            "year": year,
            "month": month,
            "person1": {
                "mansion": mansion1["name_jp"],
                "reading": mansion1["reading"],
                "element": mansion1["element"]
            },
            "person2": {
                "mansion": mansion2["name_jp"],
                "reading": mansion2["reading"],
                "element": mansion2["element"]
            },
            "compatibility": {
                "relation": compatibility["relation"]["name"],
                "score": compatibility["score"],
                "description": compatibility["relation"]["description"]
            },
            "days": days_map
        }


    def check_ryouhan_period(self, target_date: date) -> Optional[dict]:
        """
        判定指定日期是否在凌犯期間（七曜陵逼）

        根據該日期所在農曆月的朔日（初一）七曜，查表判定。
        凌犯期間內甘露日→凶、羅刹日→吉（吉凶逆轉）。

        Args:
            target_date: 西曆日期

        Returns:
            凌犯期間資訊（若不在期間內則返回 None）
        """
        # 注：閏月時 lunar_m 仍為該月數字（如閏四月 lunar_m=4），is_leap 被丟棄。
        # 原典凌犯月別表僅列正月至十二月，不含閏月獨立規則，
        # 故閏月以對應正月的朔日七曜代入，為最保守的 fallback。
        lunar_y, lunar_m, lunar_d, _ = self.solar_to_lunar(target_date)

        # 取得該農曆月朔日（初一）的西曆日期
        # 注：lunar_to_solar 固定 isleap=False，閏月時取正月初一的朔日七曜
        first_day_solar = self.lunar_to_solar(lunar_y, lunar_m, 1)
        if first_day_solar is None:
            return None

        # 朔日的七曜
        jp_weekday_first = (first_day_solar.weekday() + 1) % 7

        # 查表
        ryouhan = self.RYOUHAN_MAP.get((lunar_m, jp_weekday_first))
        if ryouhan is None:
            return None

        start_day, end_day = ryouhan

        # 判定當日農曆日是否在凌犯期間內
        if start_day <= lunar_d <= end_day:
            weekday_names = {0: "日曜", 1: "月曜", 2: "火曜", 3: "水曜", 4: "木曜", 5: "金曜", 6: "土曜"}
            wn = weekday_names[jp_weekday_first]
            month_desc = self.RYOUHAN_DESCRIPTIONS.get(lunar_m, {})

            return {
                "active": True,
                "reading": "りょうはんきかん",
                "lunar_month": lunar_m,
                "start_day": start_day,
                "end_day": end_day,
                "weekday_name": wn,
                "period_label": f"{lunar_m}月{wn}期",
                "description": month_desc.get("zh", f"農曆{lunar_m}月{start_day}日～{end_day}日為凌犯期間"),
                "description_ja": month_desc.get("ja", ""),
                "description_classic": month_desc.get("classic", ""),
                "source": "宿曜經卷五・七曜陵逼",
                "formula": {
                    "step1": f"西曆 {target_date} → 農曆 {lunar_y}/{lunar_m}/{lunar_d}",
                    "step2": f"農曆{lunar_m}月初一 = {first_day_solar}（{wn}）",
                    "step3": f"查表 RYOUHAN_MAP[({lunar_m}, {jp_weekday_first})] = ({start_day}, {end_day})",
                    "step4": f"農曆{lunar_d}日 {'在' if start_day <= lunar_d <= end_day else '不在'} [{start_day}, {end_day}] 區間"
                }
            }

        return None

    def get_rokugai_suku(self, birth_mansion_index: int) -> list[dict]:
        """
        計算六害宿

        凌犯期間中，以本命宿為基準，順時計方向計算 6 個大凶日宿。
        偏移量對應三九秘法中的特定位置（命/一九安/業/二九安/二九壊/三九栄）。

        Args:
            birth_mansion_index: 本命宿索引 (0-26)

        Returns:
            六害宿列表（含宿名、偏移、凶度）
        """
        results = []
        for name, info in self.ROKUGAI_OFFSETS.items():
            # 順時計 = 從本命宿往前數（加上偏移）
            target_index = (birth_mansion_index + info["offset"]) % 27
            target_mansion = self.mansions_data[target_index]
            results.append({
                "name": name,
                "name_reading": info["reading"],
                "mansion_index": target_index,
                "mansion_name": target_mansion["name_jp"],
                "mansion_reading": target_mansion["reading"],
                "severity": info["severity"],
                "offset": info["offset"]
            })
        # 按凶度排序（1=最凶）
        results.sort(key=lambda x: x["severity"])
        return results

    def get_sanki_cycle(self, birth_mansion_index: int, day_mansion_index: int) -> dict:
        """
        計算日運三期サイクル

        27 日為一循環，從命宿開始依序分三期各 9 天：
        - 躍動の週（一九/活動期）：命宿起 9 天
        - 破壊の週（二九/衰退期）：業宿起 9 天
        - 再生の週（三九/轉換期）：胎宿起 9 天

        Args:
            birth_mansion_index: 本命宿索引
            day_mansion_index: 當日宿索引

        Returns:
            當日所屬的三期資訊
        """
        # 計算當日宿相對於命宿的距離（前向）
        distance = (day_mansion_index - birth_mansion_index) % 27

        # 分三期：0-8 = 躍動, 9-17 = 破壊, 18-26 = 再生
        period_index = distance // 9
        day_in_period = (distance % 9) + 1  # 第幾天（1-9）

        cycle_info = self.SANKI_CYCLE[period_index]

        # 暗黒の一週間：破壊の週 distance 9-15（業→栄→衰→安→危→成→壊）
        is_dark_week = (9 <= distance <= 15)

        # 日型判定：第 1 天為期起始日（命/業/胎），第 2-9 天為共通日型
        period_num = period_index + 1  # 1=一九, 2=二九, 3=三九
        if day_in_period == 1:
            day_type = self.SANKI_DAY_TYPES["period_start"][period_num]
        else:
            day_type = self.SANKI_DAY_TYPES["day"][day_in_period]

        return {
            "period": cycle_info["name"],
            "period_reading": cycle_info["reading"],
            "period_index": period_num,
            "day_in_period": day_in_period,
            "is_dark_week": is_dark_week,
            "day_type": day_type["name"],
            "day_type_reading": day_type["reading"],
            "day_description": day_type["description"],
            "day_description_ja": day_type.get("description_ja", ""),
            "period_description": cycle_info["description"],
            "period_description_classic": cycle_info.get("description_classic", ""),
            "period_description_ja": cycle_info.get("description_ja", "")
        }

    def _analyze_compound_factors(
        self,
        ryouhan: dict | None,
        special_day_type: str | None,
        mansion_relation_type: str,
        sanki: dict,
        rokugai: dict | None
    ) -> list[dict]:
        """
        多因素交叉分析：偵測已知的因素疊加組合

        Returns:
            list[dict]，按 severity 降序排列。每個 dict 包含：
            pattern, severity, name, description, description_ja, description_classic
        """
        results = []
        is_dark_week = sanki.get("is_dark_week", False)
        is_auspicious_relation = mansion_relation_type in ("eishin", "mei")
        is_mild_auspicious = mansion_relation_type in ("eishin", "mei", "kisei")

        # 1. triple_auspicious：甘露/金剛 + 栄親/命（破壊の週的栄日/安日/成日仍可觸發）
        if special_day_type in ("kanro", "kongou") and is_auspicious_relation:
            if not ryouhan:
                results.append({
                    "pattern": "triple_auspicious",
                    "severity": 5,
                    "name": "三重大吉",
                    "description": "特殊吉日與大吉宿曜關係重疊，多重吉因加持之下，是難得的絕佳時機。把握今天推進重要事項。",
                    "description_ja": "特殊吉日と大吉の宿曜関係が重なり、三重の吉因が揃う極めて稀な好日。重要な事柄を進めるに最適。",
                    "description_classic": "吉日吉宿相重，三因具足，百事大吉。此日興造百事，無不成就。"
                })

        # 2. ryouhan_trap：凌犯 + 栄親/命
        if ryouhan and is_auspicious_relation:
            results.append({
                "pattern": "ryouhan_trap",
                "severity": 5,
                "name": "凌犯陷阱",
                "description": "凌犯期間遇上表面大吉的宿曜關係，看似順遂實則暗藏風險。高分不代表安全，重大決策務必延後。",
                "description_ja": "凌犯期間中に大吉の宿曜関係が重なる「表吉実険」の配置。好調に見えても判断を誤りやすく、重要な決断は延期すべし。",
                "description_classic": "凌犯之中遇吉配，表吉實險，如鏡花水月。宜慎之又慎，不可輕信順境。"
            })

        # 3. ryouhan_kanro_reversed：凌犯 + 甘露日
        if ryouhan and special_day_type == "kanro":
            results.append({
                "pattern": "ryouhan_kanro_reversed",
                "severity": 4,
                "name": "甘露逆轉",
                "description": "本應是甘露大吉日，但凌犯期間使吉凶逆轉。原本的福澤被遮蔽，不宜以吉日心態行事。",
                "description_ja": "本来は甘露の大吉日なるも、凌犯期間により吉凶逆転。福徳が覆われ、吉日としての効力を失う。",
                "description_classic": "甘露遇凌犯，法雨化毒霧。本吉反凶，不可妄動。"
            })

        # 4. ryouhan_rokugai：凌犯 + 六害宿
        if ryouhan and rokugai:
            results.append({
                "pattern": "ryouhan_rokugai",
                "severity": 4,
                "name": "凌犯六害",
                "description": "凌犯期間又逢六害宿，雙重凶因疊加。今日需格外謹慎，避免重要行動，靜守為宜。",
                "description_ja": "凌犯期間中に六害宿が重なり、二重の凶因が作用する。格別の注意を要し、重要な行動を控え静かに過ごすべし。",
                "description_classic": "凌犯六害相重，禍不單行。宜閉門靜守，不可興作。"
            })

        # 5. compounded_negative：安壊 + 破壊の週の凶日型（業/衰/危/壊）
        sanki_day_type = sanki.get("day_type", "")
        dark_week_bad_days = ("業の日", "衰の日", "危の日", "壊の日")
        if mansion_relation_type == "ankai" and is_dark_week and sanki_day_type in dark_week_bad_days:
            results.append({
                "pattern": "compounded_negative",
                "severity": 4,
                "name": "凶因重疊",
                "description": "安壊的破壞性與破壊の週的凶日型重疊，運勢處於谷底。今天不是行動的日子，專注在不需要外界配合的事情上。",
                "description_ja": "安壊の破壊性と破壊の週の凶日型が重なり、運勢は最低点に。行動を控え、外部との関わりを最小限に留めるべし。",
                "description_classic": "安壊逢破壊の凶日，凶上加凶。宜靜守本分，不可妄動求進。"
            })

        # 6. dark_rasetsu：羅刹日 + 暗黒の一週間
        if special_day_type == "rasetsu" and is_dark_week:
            if not ryouhan:  # 凌犯中羅刹已逆轉為吉，不算此組合
                results.append({
                    "pattern": "dark_rasetsu",
                    "severity": 3,
                    "name": "暗黒羅刹",
                    "description": "羅刹日的障礙加上暗黒の一週間的低迷，今天做什麼都容易卡住。放低期待，處理簡單的例行事務就好。",
                    "description_ja": "羅刹日の障碍と暗黒の一週間の低迷が重なる。何事も停滞しやすく、期待値を下げて日常の事務に専念すべし。",
                    "description_classic": "羅刹逢暗黒，障碍重重。宜低首靜行，不可強求。"
                })

        # 7. double_auspicious：金剛峯 + 栄親/命
        if special_day_type == "kongou" and is_auspicious_relation:
            if not ryouhan:  # 凌犯中已觸發 ryouhan_trap，不重複
                results.append({
                    "pattern": "double_auspicious",
                    "severity": 3,
                    "name": "雙重吉配",
                    "description": "金剛峯日的堅固守護加上大吉的宿曜關係，今天啟動的計畫特別容易持續下去。適合做需要長期堅持的決定。",
                    "description_ja": "金剛峯日の堅固なる守護と大吉の宿曜関係が重なる好配置。この日に始めたことは持続しやすく、長期的な決断に最適。",
                    "description_classic": "金剛遇吉配，堅牢雙成。此日興造，久長不壞。"
                })

        # 按 severity 降序排列
        results.sort(key=lambda x: x["severity"], reverse=True)
        return results

    def get_special_days_for_month(self, year: int, month: int) -> list[dict]:
        """
        取得指定月份的所有特殊日（甘露日/金剛峯日/羅刹日）

        特殊日是全域的，由 (七曜, 當日宿) 決定，不需要個人生日。

        Args:
            year: 西曆年份
            month: 西曆月份 (1-12)

        Returns:
            特殊日列表
        """
        import calendar

        fortune_data = self._load_fortune_data()
        weekday_elements = fortune_data["weekday_elements"]

        days_in_month = calendar.monthrange(year, month)[1]
        results = []

        for day in range(1, days_in_month + 1):
            target_date = date(year, month, day)

            # 當日宿（修正後宿位）
            try:
                day_mansion_index = self._get_corrected_mansion_index(target_date)
            except Exception:
                continue
            day_mansion = self.mansions_data[day_mansion_index]

            # 七曜
            weekday = target_date.weekday()
            jp_weekday = (weekday + 1) % 7
            day_info = weekday_elements[str(jp_weekday)]

            # 查特殊日
            special_day_key = (jp_weekday, day_mansion_index)
            special_day_type = self.SPECIAL_DAY_MAP.get(special_day_key)

            if special_day_type:
                info = self.SPECIAL_DAY_INFO[special_day_type]
                # 凌犯期間判定
                ryouhan = self.check_ryouhan_period(target_date)
                level = info["level"]
                ryouhan_reversed = False
                if ryouhan:
                    if special_day_type in ("kanro", "kongou"):
                        level = "凶（凌犯逆轉）"
                        ryouhan_reversed = True
                    elif special_day_type == "rasetsu":
                        level = "吉（凌犯逆轉）"
                        ryouhan_reversed = True

                results.append({
                    "date": target_date.isoformat(),
                    "weekday": day_info["name"].replace("曜日", ""),
                    "type": special_day_type,
                    "name": info["name"],
                    "reading": info["reading"],
                    "level": level,
                    "mansion": day_mansion["name_jp"],
                    "mansion_reading": day_mansion["reading"],
                    "description": info["description"],
                    "description_classic": info.get("description_classic", ""),
                    "description_ja": info.get("description_ja", ""),
                    "ryouhan_reversed": ryouhan_reversed
                })

        return results

    def get_calendar_month(self, year: int, month: int, birth_date: Optional[date] = None) -> dict:
        """
        取得整月的統合月曆資料

        整合宿位、七曜、凌犯期間、甘露/金剛峯/羅刹日，
        以及（有 birth_date 時的）三期サイクル、六害宿、簡化運勢分數。

        Args:
            year: 西曆年份
            month: 西曆月份 (1-12)
            birth_date: 出生日期（可選）

        Returns:
            統合月曆資料
        """
        import calendar as cal

        fortune_data = self._load_fortune_data()
        weekday_elements = fortune_data["weekday_elements"]

        days_in_month = cal.monthrange(year, month)[1]

        # 個人資料（若有 birth_date）
        user_index = None
        user_element = None
        user_mansion_info = None
        rokugai_indices = set()
        if birth_date:
            user_mansion = self.get_mansion(birth_date)
            user_index = user_mansion["index"]
            user_element = user_mansion["element"]
            user_mansion_info = {
                "name_jp": user_mansion["name_jp"],
                "reading": user_mansion["reading"],
                "element": user_element,
                "index": user_index,
            }
            # 預算六害宿索引（避免每日重算）
            for rg in self.get_rokugai_suku(user_index):
                rokugai_indices.add(rg["mansion_index"])

        days = []
        stats = {
            "ryouhan_days": 0,
            "kanro_count": 0,
            "kongou_count": 0,
            "rasetsu_count": 0,
        }

        for day_num in range(1, days_in_month + 1):
            target_date = date(year, month, day_num)

            # 當日宿（修正後宿位）
            try:
                day_mansion_index = self._get_corrected_mansion_index(target_date)
            except Exception:
                continue
            day_mansion = self.mansions_data[day_mansion_index]

            # 七曜
            weekday = target_date.weekday()
            jp_weekday = (weekday + 1) % 7
            day_info = weekday_elements[str(jp_weekday)]

            # 凌犯判定
            ryouhan = self.check_ryouhan_period(target_date)
            if ryouhan:
                stats["ryouhan_days"] += 1

            # 特殊日
            special_day_key = (jp_weekday, day_mansion_index)
            special_day_type = self.SPECIAL_DAY_MAP.get(special_day_key)
            special_day = None
            if special_day_type:
                info = self.SPECIAL_DAY_INFO[special_day_type]
                level = info["level"]
                ryouhan_reversed = False
                if ryouhan:
                    if special_day_type in ("kanro", "kongou"):
                        level = "凶（凌犯逆轉）"
                        ryouhan_reversed = True
                    elif special_day_type == "rasetsu":
                        level = "吉（凌犯逆轉）"
                        ryouhan_reversed = True
                special_day = {
                    "type": special_day_type,
                    "name": info["name"],
                    "level": level,
                    "ryouhan_reversed": ryouhan_reversed,
                }
                stats[f"{special_day_type}_count"] = stats.get(f"{special_day_type}_count", 0) + 1

            # 組裝每日資料
            day_entry = {
                "date": target_date.isoformat(),
                "day": day_num,
                "weekday": day_info["name"].replace("曜日", ""),
                "day_mansion": {
                    "name_jp": day_mansion["name_jp"],
                    "index": day_mansion_index,
                    "element": day_mansion["element"],
                },
                "special_day": special_day,
                "ryouhan": {"active": True, "lunar_month": ryouhan["lunar_month"]} if ryouhan else None,
            }

            # 個人化層（等級制）
            if user_index is not None:
                relation = self.get_relation_type(user_index, day_mansion_index)
                sanki = self.get_sanki_cycle(user_index, day_mansion_index)

                # 等級判定（簡化版，復用 _determine_daily_level）
                cal_level, cal_base_level, cal_overflow = self._determine_daily_level(
                    relation["type"], ryouhan, special_day_type
                )
                day_element = day_info["element"]
                _, element_bonus = self._calc_fortune_element_relation(user_element, day_element)
                fortune_score = max(30, min(100, self.LEVEL_DISPLAY_SCORE[cal_level] + int(element_bonus / 2) + cal_overflow))

                # 六害宿（凌犯期間中才標記，不影響分數）
                rokugai = None
                if ryouhan and day_mansion_index in rokugai_indices:
                    rokugai = True

                day_entry["personal"] = {
                    "relation_type": relation["type"],
                    "relation_name": relation["name"],
                    "fortune_score": fortune_score,
                    "level": cal_level,
                    "level_name": self.LEVEL_NAMES[cal_level]["zh"],
                    "sanki_period": sanki["period"],
                    "sanki_period_index": sanki["period_index"],
                    "sanki_day_type": sanki.get("day_type", ""),
                    "is_dark_week": sanki["is_dark_week"],
                    "rokugai": rokugai,
                }

            days.append(day_entry)

        result = {
            "year": year,
            "month": month,
            "days": days,
            "statistics": stats,
        }

        if user_mansion_info:
            result["personal"] = {"your_mansion": user_mansion_info}

        return result

    # ========================================================================
    # ICS 月曆產生（RFC 5545）
    # ========================================================================

    @staticmethod
    def _ics_escape(text: str) -> str:
        """跳脫 ICS 特殊字元"""
        return (
            text
            .replace('\\', '\\\\')
            .replace(';', '\\;')
            .replace(',', '\\,')
            .replace('\n', '\\n')
        )

    @staticmethod
    def _ics_fold_line(line: str) -> str:
        """RFC 5545 行摺疊：第一行 75 bytes，後續行 74 bytes（含前綴空格）"""
        encoded = line.encode('utf-8')
        if len(encoded) <= 75:
            return line

        parts: list[str] = []
        start = 0

        while start < len(line):
            max_bytes = 75 if start == 0 else 74
            end = start
            current_bytes = 0

            while end < len(line):
                char_bytes = len(line[end].encode('utf-8'))
                if current_bytes + char_bytes > max_bytes:
                    break
                current_bytes += char_bytes
                end += 1

            if end == start:
                # 單一字元超過限制（不應發生），強制推進
                end = start + 1

            parts.append(line[start:end])
            start = end

        return '\r\n '.join(parts)

    @staticmethod
    def _ics_format_date(d: date) -> str:
        """日期格式化為 ICS VALUE=DATE 格式（例: 20260115）"""
        return d.strftime('%Y%m%d')

    @staticmethod
    def _ics_fortune_level(score: int, level_name: str = "") -> str:
        """運勢分數轉等級名稱"""
        if level_name:
            return level_name
        if score >= 90:
            return '大吉'
        if score >= 75:
            return '吉'
        if score >= 60:
            return '中吉'
        if score >= 45:
            return '小凶'
        return '凶'

    @staticmethod
    def _ics_day_tip(level: str | None, personal: dict | None, day: dict) -> str:
        """白話提醒：依特殊日、凌犯、破壊の週、一般等級產生每日建議"""
        has_ryouhan = bool(day.get('ryouhan') and day['ryouhan'].get('active'))
        is_dark = bool(personal and personal.get('is_dark_week'))
        has_rokugai = bool(personal and personal.get('rokugai'))
        special_type = day['special_day']['type'] if day.get('special_day') else None
        reversed_ = bool(day.get('special_day') and day['special_day'].get('ryouhan_reversed'))

        # 特殊日優先
        if special_type == 'kanro' and not reversed_:
            return '甘露日：今天是難得的大吉日，適合開始新計畫、簽約、重要面談'
        if special_type == 'kanro' and reversed_:
            rokugai_suffix = '。又逢六害宿，宜修福：入灌頂及護摩，並修諸功德' if has_rokugai else ''
            return f'甘露日但在凌犯期間，吉凶逆轉。此時不宜因日名而草率行動，宜靜觀待時{rokugai_suffix}'
        if special_type == 'kongou' and not reversed_:
            return '金剛峯日：氣場強勢的一天，適合處理棘手的事、談判、護摩修法、下決心'
        if special_type == 'kongou' and reversed_:
            rokugai_suffix = '。又逢六害宿，宜修福：入灌頂及護摩，並修諸功德' if has_rokugai else ''
            return f'金剛峯日但在凌犯期間，吉凶逆轉。強勢能量易生阻力，宜靜觀待時{rokugai_suffix}'
        if special_type == 'rasetsu' and not reversed_:
            return '羅刹日：百事不宜，能延就延，今天不適合做重要決定'
        if special_type == 'rasetsu' and reversed_:
            rokugai_suffix = '。但逢六害宿，仍宜修福：入灌頂及護摩，並修諸功德' if has_rokugai else ''
            return f'羅刹日但凌犯逆轉，凶象減弱。保持平常心即可，無需過度擔憂{rokugai_suffix}'

        # 凌犯 + 六害宿（最需警戒）
        if has_ryouhan and has_rokugai:
            return '凌犯期間碰上六害宿，今天最該避開。原典記載宜修福：入灌頂及護摩，並修諸功德'

        # 破壊の週：依三九日型分別建議（原典各日吉凶不同）
        if is_dark:
            day_type = (personal or {}).get('sanki_day_type', '')
            if day_type == '栄の日':
                return '破壊の週但逢栄日，原典記載諸吉事大吉。可正常行動'
            if day_type == '安の日':
                return '破壊の週但逢安日，原典記載作壇場吉。穩定踏實的一天'
            if day_type == '成の日':
                return '破壊の週但逢成日，原典記載修道學問、成就法吉。適合修行精進'
            if day_type == '壊の日':
                return '破壊の週壊日，原典記載降伏法可行，餘事不宜'
            if day_type == '業の日':
                return '破壊の週業日，原典記載所作不成就。低調收斂為上'
            if day_type == '衰の日':
                return '破壊の週衰日，原典記載宜解除諸惡、療病。保守度過'
            if day_type == '危の日':
                return '破壊の週危日，原典記載結交、歡宴聚會吉。社交可行，重大決定宜避開'
            return '破壊の週，整體氣運偏弱，做好手邊的事就好'

        # 凌犯期間（無特殊日、無六害宿）
        if has_ryouhan:
            return '凌犯期間：吉凶可能相反，宜修福（護摩、諸功德），穩住心態'

        # 一般日按等級
        if level == '大吉':
            return '運勢很好的一天，想做什麼就行動吧，機會來了別猶豫'
        if level == '吉':
            return '不錯的一天，適合推進計畫、見重要的人'
        if level == '中吉':
            return '普通偏好，按部就班做事就行，不需要特別小心'
        if level == '小凶':
            return '稍微注意一下，別做太冒險的決定，穩穩來就沒問題'
        if level == '凶':
            return '運勢偏低，避開重大決策和衝突，今天適合休息充電'

        return '平穩的一天'

    def generate_ics_calendar(self, birth_date: date, year: int) -> str:
        """
        產生整年 ICS 月曆字串（RFC 5545）

        整合 12 個月的月曆資料，為每天產生一個全天事件，
        包含運勢等級、三期、特殊日標記及白話提醒。

        Args:
            birth_date: 出生日期
            year: 西曆年份

        Returns:
            RFC 5545 格式的 ICS 字串
        """
        from datetime import timedelta, datetime, timezone

        # 取得使用者本命宿資訊
        user_mansion = self.get_mansion(birth_date)
        mansion_name = user_mansion['name_jp']
        mansion_element = user_mansion['element']
        user_index = user_mansion['index']

        # DTSTAMP：產生時間（UTC）
        dtstamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')

        # VCALENDAR 標頭
        lines: list[str] = [
            'BEGIN:VCALENDAR',
            'VERSION:2.0',
            self._ics_fold_line(f'PRODID:-//Sukuyodo//Fortune Calendar//{year}//ZH'),
            'CALSCALE:GREGORIAN',
            'METHOD:PUBLISH',
            self._ics_fold_line(
                f'X-WR-CALNAME:{self._ics_escape(f"{mansion_name}({mansion_element}) {year} 年運勢")}'
            ),
            'X-WR-TIMEZONE:Asia/Taipei',
        ]

        # 逐月取得月曆資料
        event_index = 0
        for month in range(1, 13):
            cal_data = self.get_calendar_month(year, month, birth_date)

            for day in cal_data['days']:
                personal = day.get('personal')
                level = None
                if personal:
                    level = self._ics_fortune_level(
                        personal['fortune_score'],
                        personal.get('level_name', '')
                    )

                    # 補算 sanki_day_type（若 API 回傳已包含則跳過）
                    if 'sanki_day_type' not in personal or personal.get('sanki_day_type') is None:
                        day_mansion_index = day['day_mansion']['index']
                        sanki_info = self.get_sanki_cycle(user_index, day_mansion_index)
                        personal['sanki_day_type'] = sanki_info['day_type']

                # 標題：等級 | 三期縮寫 | 特殊標記
                title_segments: list[str] = []
                if level:
                    title_segments.append(level)
                if personal:
                    sanki_short = personal['sanki_period'].replace('の週', '')
                    title_segments.append(sanki_short)

                # 第三段：特殊標記
                markers: list[str] = []
                if day.get('special_day'):
                    reversed_tag = '(逆転)' if day['special_day'].get('ryouhan_reversed') else ''
                    markers.append(f"{day['special_day']['name']}{reversed_tag}")
                if day.get('ryouhan') and day['ryouhan'].get('active') and not day.get('special_day'):
                    markers.append('凌犯')
                if personal and personal.get('is_dark_week'):
                    markers.append('暗黒')
                if personal and personal.get('rokugai'):
                    markers.append('六害宿')
                if markers:
                    title_segments.append(' '.join(markers))

                summary = ' | '.join(title_segments)

                # 白話提醒
                tip = self._ics_day_tip(level, personal, day)

                # 描述（白話提醒 + 詳細資訊）
                desc_parts: list[str] = [tip, '---']
                if personal:
                    desc_parts.append(f"運勢: {personal['fortune_score']} ({level})")
                    desc_parts.append(f"關係: {personal['relation_name']}")
                    desc_parts.append(
                        f"宿: {day['day_mansion']['name_jp']}"
                        f"({day['day_mansion']['element']}) - {day['weekday']}"
                    )
                    desc_parts.append(f"三期: {personal['sanki_period']}")
                if day.get('special_day'):
                    sd = day['special_day']
                    if sd.get('ryouhan_reversed'):
                        sd_label = f"{sd['name']} (凌犯逆転: {sd['level']})"
                    else:
                        sd_label = f"{sd['name']} ({sd['level']})"
                    desc_parts.append(f"特殊日: {sd_label}")
                if day.get('ryouhan') and day['ryouhan'].get('active'):
                    desc_parts.append('-- 凌犯期間: 吉凶逆転に注意 --')
                if personal and personal.get('is_dark_week'):
                    day_type = personal.get('sanki_day_type', '')
                    desc_parts.append(f"-- 破壊の週 ({day_type or '二九'}) --")
                if personal and personal.get('rokugai'):
                    desc_parts.append('-- 六害宿 --')

                description = '\\n'.join(desc_parts)

                # 全天事件日期
                target_date = date.fromisoformat(day['date'])
                dt_start = self._ics_format_date(target_date)
                dt_end = self._ics_format_date(target_date + timedelta(days=1))

                # VEVENT
                uid = f"{day['date']}-{event_index}@sukuyodo"
                lines.append('BEGIN:VEVENT')
                lines.append(f'DTSTAMP:{dtstamp}')
                lines.append(self._ics_fold_line(f'UID:{uid}'))
                lines.append(f'DTSTART;VALUE=DATE:{dt_start}')
                lines.append(f'DTEND;VALUE=DATE:{dt_end}')
                lines.append(self._ics_fold_line(f'SUMMARY:{self._ics_escape(summary)}'))
                if description:
                    lines.append(self._ics_fold_line(f'DESCRIPTION:{description}'))
                lines.append('TRANSP:TRANSPARENT')
                lines.append('END:VEVENT')

                event_index += 1

        lines.append('END:VCALENDAR')

        return '\r\n'.join(lines)


# 全域實例
sukuyodo_service = SukuyodoService()
