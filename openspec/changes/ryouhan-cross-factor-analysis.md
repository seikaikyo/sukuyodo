---
title: 凌犯逆轉機制與多因素交叉分析
type: feature
status: completed
created: 2026-02-18
---

# 凌犯逆轉機制與多因素交叉分析

## 背景

透過真實案例驗證（觜宿 vs 尾宿流年對比），發現系統在以下六個面向存在判讀盲點，可能導致使用者嚴重誤判運勢：

1. 凌犯期間分數調整過於保守（僅 -3~-5 分）
2. 凌犯期間文字描述未反轉（正面描述照常顯示）
3. 多重因素交叉影響無綜合分析
4. 日運端點缺少原典描述
5. 凌犯中分數顯示具誤導性
6. 因素優先級未定義

## 變更內容

### 1. 凌犯描述反轉機制

凌犯期間，`career_desc` / `love_desc` / `health_desc` / `wealth_desc` 必須反轉或替換為凌犯專用警告描述。

**規則：**
- 凌犯中 score >= 70 的分類 → 替換為「表面順利但暗藏誤判風險」類描述
- 凌犯中 score < 50 的分類 → 替換為「表面困難但可能有轉機」類描述
- 凌犯中 50-69 的分類 → 替換為「情勢不明，宜靜觀」類描述

**新增資料：**
- `RYOUHAN_CATEGORY_DESCRIPTIONS`: 凌犯專用描述池（career/love/health/wealth 各 3 級）

### 2. 多因素交叉分析（compound_analysis）

API 回傳新增 `compound_analysis` 欄位，偵測多因素疊加時產生綜合判讀。

**偵測的組合：**

| 組合 | 效果 | 說明 |
|------|------|------|
| 甘露日 + 榮親/命 | 三重大吉加持 | 天時地利人和，極為罕見的好日 |
| 凌犯 + 暗黒の一週間 | 雙重凶疊加 | 判斷力與運勢同時受損 |
| 凌犯 + 安壊日 | 表凶實有轉機 | 凌犯逆轉安壊的凶性 |
| 凌犯 + 榮親/大吉 | 表吉實為陷阱 | 最危險的組合，會誤判情勢 |
| 甘露日 + 凌犯 | 吉性被逆轉 | 甘露日的保護力被凌犯抵消 |
| 六害宿 + 凌犯 | 小人 + 逆轉 | 人際關係的判斷完全失準 |
| 羅刹日 + 暗黒の一週間 | 凶上加凶 | 不宜進行任何重要行動 |
| 金剛峯日 + 榮親 | 吉上加吉 | 適合重要決策和行動 |
| 本命宿日 + 甘露日 | 特殊吉日 | 修行者的最佳修法日 |

**回傳格式：**
```json
{
  "compound_analysis": {
    "factors": ["甘露日", "榮親", "再生の週"],
    "compound_type": "triple_auspicious",
    "significance": "high",
    "summary": "三重吉因素互相加持，天時地利人和...",
    "summary_ja": "三重の吉因が重なり...",
    "priority_factor": "甘露日",
    "advice": "極為罕見的大吉組合，適合進行重要決定..."
  }
}
```

### 3. 日運端點加入原典描述

`/api/sukuyodo/fortune/daily/{date}` 回傳中增加：

- `your_mansion.personality_classic` — 本命宿原典性格描述
- `your_mansion.career_classic` — 本命宿原典事業描述
- `mansion_relation.description_classic` — 宿關係原典描述
- `mansion_relation.description_ja` — 宿關係日文描述

### 4. 凌犯分數顯示改善

`fortune` 物件中新增凌犯標記欄位：

```json
{
  "fortune": {
    "overall": 86,
    "career": 98,
    "ryouhan_active": true,
    "ryouhan_warning": "凌犯期間中，顯示分數的意義反轉。高分代表反轉力道強，非好運程度。",
    "ryouhan_warning_ja": "凌犯期間中につき、表示スコアの意味が逆転します。高得点は反転の力の強さを示し、好運を意味しません。",
    "effective_interpretation": "caution"
  }
}
```

## 影響範圍

| 檔案 | 修改內容 |
|------|---------|
| `backend/services/sukuyodo.py` | 凌犯描述反轉邏輯、多因素分析函式、分數標記 |
| `backend/data/sukuyodo_fortune.json` | 新增 `RYOUHAN_CATEGORY_DESCRIPTIONS` 凌犯專用描述 |
| `backend/data/sukuyodo_mansions.json` | 確認原典資料完整性（已有，需確認日運端點有使用） |

## 不修改的部分

- 前端顯示（由前端自行處理 `compound_analysis` 和 `ryouhan_warning`）
- 相性計算邏輯（已驗證正確）
- 九曜流年計算（已驗證正確）
- 三期サイクル計算（已驗證正確）

## 技術設計

### 因素優先級定義

當多個因素同時存在時的判讀優先順序：

```
1. 凌犯期間（最高）— 會逆轉所有其他因素的吉凶
2. 特殊日（甘露/金剛峯/羅刹）— 七曜與宿的特殊共鳴
3. 六害宿 — 人際層面的干擾
4. 暗黒の一週間 — 27 日循環的低潮期
5. 宿關係（榮親/安壊等）— 每日基本盤
6. 三期サイクル日類型 — 最細緻的日常節奏
```

### 凌犯描述反轉邏輯

```python
def get_category_desc_with_ryouhan(category: str, score: int, ryouhan_active: bool) -> str:
    if ryouhan_active:
        # 凌犯中使用專用描述池
        return get_ryouhan_desc(category, score)
    else:
        return get_category_desc(category, score)

def get_ryouhan_desc(category: str, score: int) -> str:
    descs = RYOUHAN_CATEGORY_DESCRIPTIONS.get(category, {})
    if score >= 70:
        # 高分 = 反轉力道強 = 更需警惕
        pool = descs.get("high_reversal", [""])
    elif score >= 50:
        pool = descs.get("mid_reversal", [""])
    else:
        # 低分 = 凶被逆轉 = 可能有轉機
        pool = descs.get("low_reversal", [""])
    return random.choice(pool) if pool else ""
```

### 多因素分析函式

```python
def analyze_compound_factors(
    special_day: dict | None,
    ryouhan: dict | None,
    rokugai: dict | None,
    sanki: dict,
    mansion_relation_type: str,
    is_dark_week: bool
) -> dict | None:
    factors = []
    if special_day:
        factors.append(special_day["name"])
    if ryouhan:
        factors.append("凌犯期間")
    if rokugai:
        factors.append("六害宿")
    if is_dark_week:
        factors.append("暗黒の一週間")
    # ... 偵測已知組合，產生綜合判讀
```

## 測試計畫

### 驗證案例 1：你的 2/23（三重大吉）
- 甘露日 + 榮親 + 再生之週 → compound_type = "triple_auspicious"
- 描述應強調三因素互相加持
- 分數維持 100，無凌犯標記

### 驗證案例 2：經理的 7/7（凌犯陷阱）
- 大吉(eishin) + 凌犯 + 暗黒の一週間 → compound_type = "ryouhan_trap"
- career_desc 應替換為凌犯警告描述
- ryouhan_warning 標記啟用
- 原始分數 86 保留但標註「意義反轉」

### 驗證案例 3：經理的 2/23（多重凶疊加）
- 安壊 + 暗黒の一週間 + 破壊之週 → compound_type = "compounded_negative"
- 但甘露日同時存在 → 說明甘露日的吉性被安壊抵消

### 驗證案例 4：觜宿原典描述
- 日運端點應回傳 personality_classic: "明辨是非，善言論..."
- 與現代描述並列，供判讀者交叉參照

### 驗證案例 5：凌犯中的凶日（經理 7/1）
- 安壊(凶) + 凌犯 → 凶被逆轉，可能有轉機
- 描述應反映「表面困難但可能出現意外轉折」

## Checklist

- [x] 建立 RYOUHAN_CATEGORY_DESCRIPTIONS 凌犯專用描述池
- [x] 修改 get_category_desc 支援凌犯反轉
- [x] 實作 analyze_compound_factors 多因素分析函式
- [x] 日運端點加入原典描述欄位
- [x] fortune 物件加入 ryouhan_active / ryouhan_warning / effective_interpretation 標記
- [x] 定義因素優先級常數 FACTOR_PRIORITY
- [x] 用 5 個驗證案例測試
- [x] API 回傳格式向下相容（新增欄位，不改既有欄位）
