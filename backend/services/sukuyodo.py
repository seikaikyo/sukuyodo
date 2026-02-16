"""宿曜道計算服務 - 日本真言宗占星術"""
import json
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

    def __init__(self):
        self._mansions_data = None
        self._relations_data = None
        self._elements_data = None
        self._metadata = None
        self._month_mansion_table = None

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

        # 綜合分數
        final_score = min(100, relation["score"] + element_bonus)

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
            "summary": self._generate_summary(mansion1, mansion2, relation)
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
        relation: dict
    ) -> str:
        """生成相性總結"""
        rel_name = relation["name"]
        name1 = mansion1["name_jp"]
        name2 = mansion2["name_jp"]
        score = relation["score"]

        if score >= 90:
            level = "非常合拍"
        elif score >= 75:
            level = "相當不錯"
        elif score >= 60:
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
            包含榮親、業胎、安壊三類配對宿位的資料
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
                "relation": "榮親",
                "reading": "えいしん",
                "distances": [1, 8, 10, 17, 19, 26],
                "score": 95,
                "description": "最適合結婚的對象，互相提攜成長的良緣",
                "detailed": "榮親在宿曜道中被視為最理想的結合。你們的能量場互相加持，一方有光芒時另一方也會跟著閃耀。不是那種激烈的來電，而是越相處越覺得「跟這個人在一起什麼都會變好」的踏實感。在職場上你們是天然的好搭檔，在感情中是能共同成長的伴侶。維持這段關係的秘訣是讓彼此都有發光的舞台，不要只有一方在付出。"
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
                "detailed": "安壊是宿曜道中最有戲劇性的關係。安方會被壊方強烈吸引，壊方則不自覺地對安方施加壓力。這種不對等的能量讓關係充滿張力和刺激感。如果雙方都能意識到這種動態並刻意平衡，反而能碰撞出驚人的火花。但如果放任不管，壊方可能不斷越界，安方持續退讓，最終走向破裂。關鍵是建立明確的界線和坦誠的溝通機制。"
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
        "eishin": (85, 95),   # 榮親 - 大吉 - 最佳配對日
        "gyotai": (78, 88),   # 業胎 - 吉 - 前世因緣日
        "mei": (72, 82),      # 命 - 中吉 - 同宿日
        "yusui": (60, 72),    # 友衰 - 中吉偏低 - 舒適但易懈怠
        "kisei": (45, 58),    # 危成 - 小吉 - 需謹慎
        "ankai": (32, 48),    # 安壞 - 凶 - 權力不對等日
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
        (1, 8): "kongou",   # 月曜 + 女宿
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
            "description": "宿曜經記載的大吉日。七曜與當日宿的能量完全調和，萬事順遂。適合護摩供養、灌頂傳法、開眼供養、入佛開光、結婚、簽約、搬遷、開業等重要行動。"
        },
        "kongou": {
            "name": "金剛峯日",
            "reading": "こんごうぶび",
            "level": "吉",
            "description": "宿曜經記載的吉日。七曜與當日宿形成堅固的守護能量，做事容易成就。適合修法、寫經、授戒、出家受戒、面試、考試等需要毅力與持續力的行動。"
        },
        "rasetsu": {
            "name": "羅刹日",
            "reading": "らせつび",
            "level": "凶",
            "description": "宿曜經記載的凶日。七曜與當日宿的能量產生衝突，容易遇到阻礙。避免護摩、灌頂、簽約、遠行。適合靜坐禪修、誦經迴向、閉關自修、整理反省。"
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
            "neutral": [
                "財務狀態平穩，沒有大起大落。這種環境最適合做長期理財規劃——定期定額投資、重新配置資產比例、或者開始研究一個你一直想了解的投資工具。不要期待今年有爆發性的財務增長，但持續穩定的累積到年底也是一筆可觀的數目。",
                "今年的財運中規中矩，收入跟付出成正比。想多賺就得多做，沒有捷徑。把注意力放在提升自己的賺錢能力上面——技能升級帶來的加薪、作品集帶來的副業機會——這些投入的回報比任何理財技巧都可靠。"
            ]
        }
    }

    # 角色別相處建議：根據關係類型提供不同身份的互動指南
    ROLE_DESCRIPTIONS = {
        "eishin": {
            "colleague": "榮親在職場上是最強的搭檔組合。你們天然地互相加持，一個人的提案被另一個人補充之後總是變得更完整。分工的時候各自負責擅長的部分，彙整時反而比一個人全做更快更好。如果有機會合作專案，不要猶豫直接組隊。唯一要注意的是功勞的歸屬——因為你們太容易合作成功，有時候會忘了釐清各自的貢獻，事先講清楚比事後爭論好。",
            "friend": "榮親的友誼有一種自然而然的滋養感，跟對方聊完天之後你會覺得被充電了。你們適合一起做有建設性的事——一起運動、一起學東西、一起參加活動。這種朋友不會讓你越來越懶，反而是在對方身邊你會不自覺地想變得更好。遇到人生重大決定的時候，聽聽對方的想法，榮親朋友給的建議通常特別有參考價值。",
            "lover": "榮親在感情中是越相處越舒服的類型。初識時可能不是一見鍾情的驚天動地，但日子一長你會發現這個人讓你的生活全面升級。彼此的價值觀契合度高，生活習慣也容易磨合。重點是兩個人都要有各自的舞台——如果只有一方在成長，另一方容易產生不安全感。安排定期的共同活動和各自的獨處時間，維持健康的距離。",
            "family": "榮親關係的家人相處起來最輕鬆。你們之間的理解是天然的，很多事不需要解釋對方就能體會。作為親子關係，父母和孩子之間很少有真正的衝突，因為雙方都願意替對方著想。作為兄弟姐妹，你們是對方最強的後盾。家庭中如果有重大決策需要討論，你們之間的溝通效率最高。"
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
        # 根據目標日期的農曆計算當天的宿位
        lunar_y, lunar_m, lunar_d, _ = self.solar_to_lunar(target_date)
        day_mansion_index = self.get_mansion_index(lunar_m, lunar_d)
        day_mansion = self.mansions_data[day_mansion_index]

        # === 三九秘法：計算本命宿與當日宿的關係 ===
        mansion_relation = self.get_relation_type(user_index, day_mansion_index)
        mansion_relation_type = mansion_relation["type"]

        # 根據關係類型決定基礎分數範圍
        score_range = self.RELATION_SCORE_RANGES.get(
            mansion_relation_type,
            (55, 70)  # 預設：未知關係
        )

        # 設定隨機種子確保同一天同一人結果一致
        random.seed(f"{birth_date.isoformat()}{target_date.isoformat()}")

        # 基礎分數（根據宿曜關係）
        base_score = random.randint(score_range[0], score_range[1])

        # === 次要因素：七曜元素微調 ===
        weekday = target_date.weekday()
        jp_weekday = (weekday + 1) % 7
        day_info = fortune_data["weekday_elements"][str(jp_weekday)]
        day_element = day_info["element"]

        # 元素相性微調（-5 到 +5）
        element_relation_type, element_bonus = self._calc_fortune_element_relation(
            user_element, day_element
        )
        # 將元素加成縮小為次要因素（截斷除法，避免負數偏移）
        element_adjustment = int(element_bonus / 2)  # ±20→±10, ±10→±5, ±5→±2
        element_desc = fortune_data["element_relations"].get(
            element_relation_type,
            fortune_data["element_relations"]["neutral"]
        )["description"]

        # 最終總分
        overall_score = max(30, min(100, base_score + element_adjustment))

        # === 計算各項運勢 ===
        def calc_category_score(category: str) -> int:
            cat_data = fortune_data["fortune_categories"][category]
            # 有利元素加成
            cat_bonus = 3 if user_element in cat_data["favorable_elements"] else 0
            day_bonus = 2 if day_element in cat_data["favorable_elements"] else 0
            # 宿曜關係影響各項運勢
            relation_factor = (score_range[0] + score_range[1]) // 2 - 65  # 相對於中性的偏移
            variation = random.randint(-6, 6)
            return max(30, min(100, 65 + relation_factor + cat_bonus + day_bonus + element_adjustment + variation))

        career_score = calc_category_score("career")
        love_score = calc_category_score("love")
        health_score = calc_category_score("health")
        wealth_score = calc_category_score("wealth")

        # === 選擇建議 ===
        if overall_score >= 85:
            advice_list = fortune_data["daily_advice"]["excellent"]
        elif overall_score >= 70:
            advice_list = fortune_data["daily_advice"]["good"]
        elif overall_score >= 55:
            advice_list = fortune_data["daily_advice"]["neutral"]
        elif overall_score >= 40:
            advice_list = fortune_data["daily_advice"]["caution"]
        else:
            advice_list = fortune_data["daily_advice"]["challenging"]

        advice = random.choice(advice_list)

        # === 甘露日/金剛峯日/羅刹日判定 ===
        special_day_key = (jp_weekday, day_mansion_index)
        special_day_type = self.SPECIAL_DAY_MAP.get(special_day_key)
        special_day = None
        if special_day_type:
            special_day = dict(self.SPECIAL_DAY_INFO[special_day_type])
            special_day["type"] = special_day_type
            # 甘露日加分、羅刹日減分
            if special_day_type == "kanro":
                overall_score = min(100, overall_score + 10)
            elif special_day_type == "rasetsu":
                overall_score = max(30, overall_score - 10)

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
                "index": day_mansion_index
            },
            "your_mansion": {
                "name_jp": mansion["name_jp"],
                "reading": mansion["reading"],
                "element": user_element,
                "index": mansion["index"]
            },
            "mansion_relation": {
                "type": mansion_relation_type,
                "name": self.DAILY_FORTUNE_RELATION_NAMES.get(mansion_relation_type, mansion_relation["name"]),
                "reading": mansion_relation.get("reading", ""),
                "description": random.choice(self.DAILY_FORTUNE_DESCRIPTIONS.get(mansion_relation_type, [mansion_relation["description"]]))
            },
            "element_relation": {
                "type": element_relation_type,
                "description": element_desc
            },
            "fortune": {
                "overall": overall_score,
                "career": career_score,
                "love": love_score,
                "health": health_score,
                "wealth": wealth_score
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
            "special_day": special_day
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
        # MONTH_START_MANSION 是農曆月份表，需先將西曆轉農曆
        mid_date = date(year, month, 15)
        _, lunar_month_for_mansion, _, _ = self.solar_to_lunar(mid_date)
        month_mansion_index = self.MONTH_START_MANSION.get(lunar_month_for_mansion, 0)
        month_mansion = self.mansions_data[month_mansion_index]

        # 計算本命宿與月宿的關係
        relation = self.get_relation_type(user_index, month_mansion_index)

        # 基於關係類型計算基礎分數
        base_score = relation["score"]

        # 月份主題加成
        month_theme = fortune_data["monthly_themes"].get(str(month), {})
        theme_element = month_theme.get("element_boost", "土")
        if user_element == theme_element:
            base_score = min(100, base_score + 5)

        # 計算各項運勢
        random.seed(f"{birth_date.isoformat()}{year}{month}")

        def calc_monthly_category(category: str) -> int:
            cat_data = fortune_data["fortune_categories"][category]
            cat_bonus = 8 if user_element in cat_data["favorable_elements"] else 0
            variation = random.randint(-10, 10)
            return max(30, min(100, base_score + cat_bonus + variation))

        # 計算每週運勢（以該月日期為準，非 ISO 週數）
        weekly = []
        first_day = date(year, month, 1)

        # 計算該月有多少天
        if month == 12:
            next_month_first = date(year + 1, 1, 1)
        else:
            next_month_first = date(year, month + 1, 1)
        days_in_month = (next_month_first - first_day).days

        # 將月份分成每 7 天一週
        week_num = 0
        day_offset = 0
        while day_offset < days_in_month:
            week_num += 1
            week_start = first_day + timedelta(days=day_offset)
            week_end_offset = min(day_offset + 6, days_in_month - 1)
            week_end = first_day + timedelta(days=week_end_offset)

            week_seed = f"{birth_date.isoformat()}{year}{month}week{week_num}"
            random.seed(week_seed)
            week_score = max(40, min(100, base_score + random.randint(-15, 15)))
            categories = ["career", "love", "health", "wealth"]
            focus = random.choice(categories)

            # 計算該週每日運勢
            daily_overview = []
            for d in range(week_end_offset - day_offset + 1):
                day_date = week_start + timedelta(days=d)
                daily_fortune = self.calculate_daily_fortune(birth_date, day_date)
                daily_overview.append({
                    "date": day_date.isoformat(),
                    "weekday": daily_fortune["weekday"]["name"],
                    "score": daily_fortune["fortune"]["overall"]
                })

            weekly.append({
                "week": week_num,
                "week_start": week_start.isoformat(),
                "week_end": week_end.isoformat(),
                "score": week_score,
                "focus": fortune_data["fortune_categories"][focus]["name"],
                "daily_overview": daily_overview
            })

            day_offset += 7

        random.seed(f"{birth_date.isoformat()}{year}{month}")

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
                "reading": relation.get("reading", ""),
                "description": random.choice(self.MONTHLY_FORTUNE_DESCRIPTIONS.get(relation["type"], [relation["description"]]))
            },
            "theme": {
                "title": month_theme.get("theme", ""),
                "focus": month_theme.get("focus", ""),
                "element_boost": theme_element,
                "description": random.choice(self.MONTHLY_THEME_DESCRIPTIONS.get(relation["type"], ["本月能量平穩，按照自己的步調前進即可。"]))
            },
            "fortune": {
                "overall": base_score,
                "career": calc_monthly_category("career"),
                "love": calc_monthly_category("love"),
                "health": calc_monthly_category("health"),
                "wealth": calc_monthly_category("wealth")
            },
            "weekly": weekly,
            "advice": random.choice(self.MONTHLY_FORTUNE_ADVICE.get(relation["type"], [f"本月運勢{self.DAILY_FORTUNE_RELATION_NAMES.get(relation['type'], '平穩')}，順其自然即可。"]))
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

        # 基礎分數
        base_score = 70 + base_bonus

        # 計算各項運勢
        random.seed(f"{birth_date.isoformat()}{target_date.isoformat()}")

        def calc_weekly_category(category: str) -> int:
            cat_data = fortune_data["fortune_categories"][category]
            cat_bonus = 6 if user_element in cat_data["favorable_elements"] else 0
            day_bonus = 4 if center_element in cat_data["favorable_elements"] else 0
            variation = random.randint(-10, 10)
            return max(30, min(100, base_score + cat_bonus + day_bonus + variation))

        overall_score = max(30, min(100, base_score))
        career_score = calc_weekly_category("career")
        love_score = calc_weekly_category("love")
        health_score = calc_weekly_category("health")
        wealth_score = calc_weekly_category("wealth")

        # 計算每日運勢概覽（8天：昨天 + 今天 + 未來6天）
        daily_overview = []
        for day_offset in range(-1, 7):  # -1 = 昨天, 0 = 今天, 1-6 = 未來
            day_date = target_date + timedelta(days=day_offset)
            daily_fortune = self.calculate_daily_fortune(birth_date, day_date)
            daily_overview.append({
                "date": day_date.isoformat(),
                "weekday": daily_fortune["weekday"]["name"],
                "score": daily_fortune["fortune"]["overall"],
                "is_today": day_offset == 0,
                "is_yesterday": day_offset == -1
            })

        # 選擇建議
        if overall_score >= 85:
            advice_list = fortune_data["daily_advice"]["excellent"]
        elif overall_score >= 70:
            advice_list = fortune_data["daily_advice"]["good"]
        elif overall_score >= 55:
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
            "advice": advice,
            "focus": random.choice(self.WEEKLY_FORTUNE_FOCUS.get(relation_type, self.WEEKLY_FORTUNE_FOCUS["neutral"])),
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
            "level": "吉", "fortune_name": "喜運",
            "element": "水", "base_score": 68,
            "buddha": "彌勒菩薩",
            "description": "心裡的煩惱比實際的困難多。運氣本身不差，但你會因為想太多而覺得不順。春夏保持低調、減少不必要的社交，秋冬之後萬事轉好。長輩和貴人的建議在今年特別值得參考，遇到猶豫的事找有經驗的人聊聊。"
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
            "description": "需要格外謹慎的一年。人際衝突頻繁、事業上容易遇到挫折、健康也需要留心。家庭關係和工作關係都可能因為一句話、一個誤會而產生裂痕。控制情緒是今年最重要的課題。遇到讓你想發火的事情，先離開現場冷靜十分鐘再回應。"
        },
        {
            "name": "計都星", "reading": "けいとせい",
            "level": "大凶", "fortune_name": "滞運",
            "element": None, "base_score": 45,
            "buddha": "釋迦如來",
            "description": "努力得不到回報、計畫被迫中斷的一年。春季三個月特別要注意，到秋天才會稍微好轉。這不是你的問題，是時運的週期。你能做的是降低期望值、減少冒險、把精力放在守住現有的成果上。忍耐是唯一的策略，忍過去之後你會更強。"
        },
        {
            "name": "月曜星", "reading": "げつようせい",
            "level": "吉", "fortune_name": "進運",
            "element": "月", "base_score": 75,
            "buddha": "勢至菩薩",
            "description": "穩步前進、漸入佳境的一年。工作上會遇到對你有幫助的人脈，喜事可能不只一件。適合拓展交際圈、接受新的挑戰。但不要因為看到機會就盲目衝刺，穩健推進比急躁冒進更能把好運留住。"
        },
        {
            "name": "木曜星", "reading": "もくようせい",
            "level": "大吉", "fortune_name": "吉運",
            "element": "木", "base_score": 80,
            "buddha": "藥師如來",
            "description": "如春天發芽般，做什麼都容易成長的一年。婚姻運好、家庭安泰、私人生活充實。不管是開始一段新關係、搬家、還是轉換跑道，今年的選擇都容易帶來好結果。但好運不等於不用努力，鬆懈是吉年最大的浪費。"
        }
    ]

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

        # 九曜星與本命元素的關係
        if star_element:
            star_relation, star_bonus = self._calc_fortune_element_relation(user_element, star_element)
        else:
            # 羅喉星/計都星無元素，使用 conflicting 作為預設
            star_relation = "conflicting"
            star_bonus = -10

        base_score = star["base_score"] + star_bonus // 2

        warnings = []

        # 計算每月趨勢
        random.seed(f"{birth_date.isoformat()}{year}")
        monthly_trend = []
        for m in range(1, 13):
            month_score = max(40, min(100, base_score + random.randint(-20, 20)))
            monthly_trend.append({
                "month": m,
                "score": month_score
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

        # 各項運勢
        random.seed(f"{birth_date.isoformat()}{year}categories")
        star_element_for_cat = star_element if star_element else "土"

        def calc_yearly_category(category: str) -> int:
            cat_data = fortune_data["fortune_categories"][category]
            cat_bonus = 10 if user_element in cat_data["favorable_elements"] else 0
            year_boost = 5 if star_element_for_cat in cat_data["favorable_elements"] else 0
            variation = random.randint(-12, 12)
            return max(35, min(100, base_score + cat_bonus + year_boost + variation))

        # 年度建議（根據九曜星元素與本命元素的關係）
        advice_key = star_relation if star_relation in self.YEARLY_FORTUNE_ADVICE else "neutral"
        random.seed(f"{birth_date.isoformat()}{year}advice")
        advice = random.choice(self.YEARLY_FORTUNE_ADVICE[advice_key])

        # 年度主題：使用九曜星的 fortune_name 作為標題
        theme_key = star_relation if star_relation in self.YEARLY_THEME_DESCRIPTIONS else "neutral"
        random.seed(f"{birth_date.isoformat()}{year}theme")
        theme_description = random.choice(self.YEARLY_THEME_DESCRIPTIONS[theme_key])

        # 各項分述
        category_descriptions = {}
        for cat in ["career", "love", "health", "wealth"]:
            cat_key = star_relation if star_relation in self.YEARLY_CATEGORY_DESCRIPTIONS.get(cat, {}) else "neutral"
            random.seed(f"{birth_date.isoformat()}{year}catdesc_{cat}")
            cat_descs = self.YEARLY_CATEGORY_DESCRIPTIONS.get(cat, {}).get(cat_key, [""])
            category_descriptions[cat] = random.choice(cat_descs)

        # 月趨勢加入提示
        month_tips = {
            1: "新年開局，設定目標比急著行動更有價值",
            2: "承接年初的能量，開始具體推進計畫",
            3: "春天適合播種，把想做的事情付諸行動",
            4: "穩定推進期，專注於手上最重要的事",
            5: "年度中間點，做一次階段性的進度盤點",
            6: "上半年的收尾，整理成果並調整下半年的方向",
            7: "下半年的起點，重新評估優先順序",
            8: "執行力高峰期，適合全力衝刺關鍵目標",
            9: "秋天的收穫期，善用前幾個月累積的成果",
            10: "進入年度倒數，集中精力完成年初設定的目標",
            11: "減法的月份，砍掉做不完的項目，聚焦核心",
            12: "年度總結，盤點收穫、反思不足、規劃明年"
        }
        for item in monthly_trend:
            item["tip"] = month_tips.get(item["month"], "")

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
            "advice": advice
        }

    # 職業類型資料
    CAREER_BY_ELEMENT = {
        "日": {
            "categories": [
                {"name": "領導管理", "jobs": ["企業主管", "專案經理", "創業家", "執行長"]},
                {"name": "表演藝術", "jobs": ["演員", "導演", "主持人", "藝術家"]},
                {"name": "公共事務", "jobs": ["政治人物", "公關", "發言人", "外交官"]}
            ],
            "traits": "日性能量賦予領導特質和決斷力，使你在需要統籌全局、激勵團隊的位置上能充分發揮。你的存在感和自信是帶領他人前進的重要資源。"
        },
        "月": {
            "categories": [
                {"name": "照護服務", "jobs": ["護理師", "社工", "心理諮商師", "幼教老師"]},
                {"name": "藝術創作", "jobs": ["作家", "插畫家", "音樂家", "設計師"]},
                {"name": "生活產業", "jobs": ["餐飲業", "旅遊業", "美容美髮", "花藝師"]}
            ],
            "traits": "月性能量賦予細膩的感受力和同理心，使你能理解他人的需求和情緒。在需要照顧他人或創造美好體驗的領域，你能展現獨特的價值。"
        },
        "火": {
            "categories": [
                {"name": "業務銷售", "jobs": ["業務主管", "行銷經理", "房仲", "保險業務"]},
                {"name": "體能相關", "jobs": ["運動員", "教練", "軍警消防", "廚師"]},
                {"name": "技術工程", "jobs": ["機械工程師", "電機工程師", "建築師", "技師"]}
            ],
            "traits": "火性能量帶來強大的行動力和執行力，使你在需要主動出擊、快速決策的環境中如魚得水。你的熱情和衝勁是推動事情前進的動力。"
        },
        "水": {
            "categories": [
                {"name": "研究分析", "jobs": ["研究員", "數據分析師", "市場調查員", "科學家"]},
                {"name": "資訊科技", "jobs": ["軟體工程師", "系統分析師", "AI 工程師", "資安專家"]},
                {"name": "金融財務", "jobs": ["投資分析師", "精算師", "財務顧問", "交易員"]}
            ],
            "traits": "水性能量賦予靈活的思維和分析能力，使你善於處理複雜的問題和變化的情境。在需要邏輯思考、數據分析的領域，你的能力能得到充分發揮。"
        },
        "木": {
            "categories": [
                {"name": "教育文化", "jobs": ["教師", "教授", "培訓講師", "圖書館員"]},
                {"name": "法律媒體", "jobs": ["律師", "法官", "記者", "編輯"]},
                {"name": "環保農業", "jobs": ["環保工程師", "農業專家", "園藝師", "獸醫"]}
            ],
            "traits": "木性能量代表成長和正義，使你具有傳承知識、引導他人的天賦。在需要教育啟發、維護公平的領域，你的價值觀和理想能成為指引方向的力量。"
        },
        "金": {
            "categories": [
                {"name": "金融會計", "jobs": ["會計師", "稽核員", "銀行家", "證券分析師"]},
                {"name": "精密工業", "jobs": ["珠寶設計師", "精密機械師", "品管工程師", "鐘錶師"]},
                {"name": "法務行政", "jobs": ["法務專員", "行政主管", "人資經理", "採購專員"]}
            ],
            "traits": "金性能量帶來嚴謹和精確的特質，使你在需要高標準品質控管的領域能夠勝任。你對細節的講究和專業判斷力，是確保成果品質的重要保障。"
        },
        "土": {
            "categories": [
                {"name": "不動產", "jobs": ["建築師", "室內設計師", "不動產經紀", "土地開發"]},
                {"name": "行政管理", "jobs": ["行政助理", "總務主管", "秘書", "辦公室經理"]},
                {"name": "物流倉儲", "jobs": ["物流經理", "倉管人員", "供應鏈管理", "貨運業"]}
            ],
            "traits": "土性能量賦予穩定和務實的特質，使你在需要長期耕耘、穩健推進的領域能夠發光。你的可靠和耐心是建立持久成就的基礎。"
        }
    }

    def get_career_guidance(self, birth_date: date) -> dict:
        """
        取得求職離職指引

        Args:
            birth_date: 西曆生日

        Returns:
            職業建議和吉日列表
        """
        from datetime import timedelta

        mansion = self.get_mansion(birth_date)
        user_element = mansion["element"]
        user_index = mansion["index"]

        # 取得適合職業
        career_data = self.CAREER_BY_ELEMENT.get(user_element, self.CAREER_BY_ELEMENT["土"])
        suitable_careers = career_data["categories"]
        career_traits = career_data["traits"]

        # 計算未來 30 天的吉日
        today = date.today()
        job_seeking_days = []
        resignation_days = []
        avoid_days = []

        fortune_data = self._load_fortune_data()

        for i in range(30):
            check_date = today + timedelta(days=i)

            # 計算當日運勢分數
            daily_fortune = self.calculate_daily_fortune(birth_date, check_date)
            score = daily_fortune["fortune"]["overall"]

            # 取得當日七曜元素
            weekday = check_date.weekday()
            jp_weekday = (weekday + 1) % 7
            day_element = fortune_data["weekday_elements"][str(jp_weekday)]["element"]
            day_name = fortune_data["weekday_elements"][str(jp_weekday)]["name"]

            # 計算當日宿
            lunar_year, lunar_month, lunar_day, _ = self.solar_to_lunar(check_date)
            day_mansion_index = self.get_mansion_index(lunar_month, lunar_day)

            # 計算與本命宿的關係
            relation = self.get_relation_type(user_index, day_mansion_index)
            relation_type = relation["type"]

            # 判斷求職吉日
            is_job_seeking_lucky = False
            job_reason = ""

            if relation_type in ["eishin", "gyotai"]:
                is_job_seeking_lucky = True
                job_reason = f"{relation['name']}日，貴人運旺"
            elif day_element == user_element:
                is_job_seeking_lucky = True
                job_reason = f"{day_name}（{day_element}）同元素，能量充沛"
            elif self._is_generating(day_element, user_element):
                is_job_seeking_lucky = True
                job_reason = f"{day_name}，元素相生，運勢順利"
            elif score >= 75:
                is_job_seeking_lucky = True
                job_reason = f"運勢佳（{score}分），適合面試"

            if is_job_seeking_lucky and len(job_seeking_days) < 5:
                job_seeking_days.append({
                    "date": check_date.isoformat(),
                    "weekday": day_name,
                    "score": score,
                    "reason": job_reason
                })

            # 判斷離職吉日（月底、月初，運勢穩定）
            is_resignation_ok = False
            resign_reason = ""

            if check_date.day <= 5 or check_date.day >= 25:
                if score >= 65 and relation_type not in ["ankai", "kisei"]:
                    is_resignation_ok = True
                    resign_reason = "月初/月底，運勢穩定" if score >= 70 else "運勢平穩，可行"

            if is_resignation_ok and len(resignation_days) < 3:
                resignation_days.append({
                    "date": check_date.isoformat(),
                    "weekday": day_name,
                    "score": score,
                    "reason": resign_reason
                })

            # 需避開的日子
            if score < 50 or relation_type in ["ankai", "kisei"]:
                if len(avoid_days) < 5:
                    avoid_reason = "運勢低迷" if score < 50 else f"{relation['name']}日，不宜重大決定"
                    avoid_days.append({
                        "date": check_date.isoformat(),
                        "weekday": day_name,
                        "score": score,
                        "reason": avoid_reason
                    })

        return {
            "your_mansion": {
                "name_jp": mansion["name_jp"],
                "reading": mansion["reading"],
                "element": user_element
            },
            "suitable_careers": suitable_careers,
            "career_traits": career_traits,
            "lucky_days": {
                "job_seeking": job_seeking_days,
                "resignation": resignation_days
            },
            "avoid_days": avoid_days,
            "general_advice": self._get_career_advice(user_element)
        }

    # ==================== 通用吉日查詢 ====================

    # 吉日查詢類別定義
    # 關係類型對照：mei(命), gyotai(業胎), eishin(榮親), yusui(友衰), ankai(安壞), kisei(危成)
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
        "beauty": {
            "name": "美容",
            "icon": "scissors",
            "actions": {
                "haircut": {"name": "剪頭髮", "favor_relations": ["eishin", "yusui"], "favor_weekdays": [1, 3, 5], "favor_score": 70},
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
                "breakup": {"name": "分手", "favor_relations": ["yusui", "ankai"], "favor_score": 60}
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
        month_day_range = action_config.get("month_day_range", None)

        for i in range(days_ahead):
            check_date = today + timedelta(days=i)

            # 計算當日運勢分數
            daily_fortune = self.calculate_daily_fortune(birth_date, check_date)
            score = daily_fortune["fortune"]["overall"]

            # 取得當日資訊
            weekday = check_date.weekday()
            jp_weekday = (weekday + 1) % 7
            day_element = fortune_data["weekday_elements"][str(jp_weekday)]["element"]
            day_name = fortune_data["weekday_elements"][str(jp_weekday)]["name"]

            # 計算當日宿
            lunar_year, lunar_month, lunar_day, _ = self.solar_to_lunar(check_date)
            day_mansion_index = self.get_mansion_index(lunar_month, lunar_day)

            # 計算與本命宿的關係
            relation = self.get_relation_type(user_index, day_mansion_index)
            relation_type = relation["type"]

            # 判斷是否吉日
            is_lucky = False
            lucky_reason = ""

            # 檢查避開的關係
            if relation_type in avoid_relations:
                if len(avoid_days) < 5:
                    avoid_days.append({
                        "date": check_date.isoformat(),
                        "weekday": day_name,
                        "score": score,
                        "reason": f"{relation['name']}日，不宜{action_config['name']}"
                    })
                continue

            # 檢查運勢過低
            if score < 50:
                if len(avoid_days) < 5:
                    avoid_days.append({
                        "date": check_date.isoformat(),
                        "weekday": day_name,
                        "score": score,
                        "reason": "運勢低迷，建議避開"
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
                # 計算評級
                rating = "大吉" if score >= 85 else "吉" if score >= 70 else "中吉"

                # 時段建議
                time_tip = self._get_personal_time_tip(day_element, user_element, action)

                lucky_days.append({
                    "date": check_date.isoformat(),
                    "weekday": day_name,
                    "score": score,
                    "rating": rating,
                    "reason": lucky_reason,
                    "best_time": time_tip["best_time"],
                    "avoid_time": time_tip["avoid_time"]
                })

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

    def get_all_lucky_day_categories(self) -> list:
        """取得所有吉日查詢類別"""
        return [
            {
                "key": key,
                "name": cat["name"],
                "icon": cat["icon"],
                "actions": [
                    {"key": act_key, "name": act["name"]}
                    for act_key, act in cat["actions"].items()
                ]
            }
            for key, cat in self.LUCKY_DAY_CATEGORIES.items()
        ]

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
        "beauty": {
            "eishin": "美容運極佳。今天去做造型的效果特別好，設計師能準確抓到你想要的感覺。不管是剪髮、染髮還是護膚，成品都會讓你滿意",
            "gyotai": "你對自己適合什麼造型的直覺今天特別準。如果一直在猶豫要不要嘗試新風格，今天是最好的時機。跟著感覺選不會錯",
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
            "beauty": {
                "haircut": f"{element}性本命宿者，剪髮前先收集三到五張你喜歡的參考圖給設計師。比起口頭描述，圖片能更準確地傳達你的想法。下午兩點到四點是設計師手感最穩的時段。",
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

    def _get_career_advice(self, element: str) -> str:
        """取得職涯建議"""
        advice_map = {
            "日": "日性能量賦予你領導者的氣質，求職時可著重展現統籌協調和決策能力。面試中適度分享對工作的願景和想法，能讓面試官看到你的潛力。",
            "月": "月性能量帶來的同理心和感受力是重要的職場資產。建議在求職過程中強調團隊協作和照顧他人的經驗。選擇能發揮感性特質的工作環境，有助於長期發展。",
            "火": "火性能量帶來的行動力和執行力是職場上的競爭優勢。面試時展現積極主動的態度會加分。建議選擇有挑戰性、能持續發揮執行力的職位。",
            "水": "水性能量賦予的分析和思考能力是重要的專業資源。求職時建議準備充分的資料和數據來佐證你的能力。需要策略思考的工作能讓你發揮所長。",
            "木": "木性能量帶來的正直和理想性是珍貴的特質。選擇符合個人價值觀的工作對長期發展很重要。教育、法律、環保等能實踐理想的領域可能帶來較高的工作滿足感。",
            "金": "金性能量賦予的嚴謹和精確是專業工作的重要特質。面試時展現對品質的堅持和專業判斷力。需要高標準品質控管的職位能讓你充分發揮。",
            "土": "土性能量帶來的穩定和可靠是團隊中重要的支柱特質。建議選擇穩定的工作環境，能讓你的踏實特質得到發揮。長期耕耘型的職位往往能帶來豐碩的成果。"
        }
        return advice_map.get(element, "建議根據個人特質，選擇能充分發揮所長的工作方向。")

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

                # 取得當日資訊
                weekday = check_date.weekday()
                jp_weekday = (weekday + 1) % 7
                day_info = fortune_data["weekday_elements"][str(jp_weekday)]
                day_name = day_info["name"]
                day_element = day_info["element"]

                # 計算當日宿
                lunar_year, lunar_month, lunar_day, _ = self.solar_to_lunar(check_date)
                day_mansion_index = self.get_mansion_index(lunar_month, lunar_day)

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

                if is_lucky and len(lucky_days) < 5:
                    rating = "大吉" if avg_score >= 85 else "吉" if avg_score >= 70 else "中吉"

                    # 時段建議
                    time_tip = self._get_pair_time_tip(
                        relation1["type"], relation2["type"],
                        day_element, mansion1["element"], mansion2["element"],
                        action["key"]
                    )

                    lucky_days.append({
                        "date": check_date.isoformat(),
                        "weekday": day_name,
                        "score": avg_score,
                        "rating": rating,
                        "reason": lucky_reason,
                        "best_time": time_tip["best_time"],
                        "avoid_time": time_tip["avoid_time"],
                        "tip": time_tip["tip"]
                    })

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

            # 農曆轉換
            try:
                _, lunar_m, lunar_d, _ = self.solar_to_lunar(target_date)
            except Exception:
                continue

            # 當日宿
            day_mansion_index = self.get_mansion_index(lunar_m, lunar_d)
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
                results.append({
                    "date": target_date.isoformat(),
                    "weekday": day_info["name"].replace("曜日", ""),
                    "type": special_day_type,
                    "name": info["name"],
                    "reading": info["reading"],
                    "level": info["level"],
                    "mansion": day_mansion["name_jp"],
                    "mansion_reading": day_mansion["reading"],
                    "description": info["description"]
                })

        return results


# 全域實例
sukuyodo_service = SukuyodoService()
