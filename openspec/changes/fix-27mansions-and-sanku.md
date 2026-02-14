---
title: 修正 27 宿構成與三九秘法距離分配
type: fix
status: in-progress
created: 2026-02-14
---

# 修正 27 宿構成與三九秘法距離分配

## 變更內容

### Bug 1: 27 宿列表包含牛宿（應排除）

程式碼使用的 27 宿包含「牛宿」、排除「軫宿」，與日本宿曜経標準相反。

- 標準：排除牛宿，包含軫宿（八雲院、syukuyo.com、unkoi.com 等主流網站一致）
- 影響：斗宿之後所有宿的索引偏移 +1，導致部分生日的本命宿計算結果錯誤
- 範例：1977/10/29 應為「觜宿」(火)，程式算出「畢宿」(月)

修正後的 27 宿順序：
```
0:角 1:亢 2:氐 3:房 4:心 5:尾 6:箕 7:斗
8:女 9:虛 10:危 11:室 12:壁 13:奎 14:婁 15:胃
16:昴 17:畢 18:觜 19:参 20:井 21:鬼 22:柳 23:星
24:張 25:翼 26:軫
```

### Bug 2: 三九秘法距離分配錯誤

標準三九秘法排列（來源：宿曜経、SARAスクール）：
```
命(0) → 栄(1), 衰(2), 安(3), 危(4), 成(5), 壊(6), 友(7), 親(8)
業(9) → 栄(10), 衰(11), 安(12), 危(13), 成(14), 壊(15), 友(16), 親(17)
胎(18) → 栄(19), 衰(20), 安(21), 危(22), 成(23), 壊(24), 友(25), 親(26)
```

配對後標準分組：
| 關係 | 標準距離 | 程式距離（錯） |
|------|---------|---------------|
| 栄親 | {1, 8, 10, 17, 19, 26} | {1, 3, 10, 12, 15, 17, 24, 26} |
| 友衰 | {2, 7, 11, 16, 20, 25} | {2, 5, 11, 13, 14, 16, 22, 25} |
| 安壊 | {3, 6, 12, 15, 21, 24} | {4, 6, 21, 23} |
| 危成 | {4, 5, 13, 14, 22, 23} | {7, 8, 19, 20} |

14/27 個距離分配錯誤（52%），影響所有配對關係判定和每日運勢。

### 附帶修正: DISTANCE_TYPE_MAP

需同步更新近距離/中距離/遠距離分類：

標準 DISTANCE_TYPE_MAP：
```python
DISTANCE_TYPE_MAP = {
    "eishin": {
        "near": {"distances": [1, 26], "direction_map": {1: "栄", 26: "親"}},
        "mid":  {"distances": [10, 17], "direction_map": {10: "栄", 17: "親"}},
        "far":  {"distances": [8, 19], "direction_map": {8: "親", 19: "栄"}}
    },
    "yusui": {
        "near": {"distances": [2, 25], "direction_map": {2: "衰", 25: "友"}},
        "mid":  {"distances": [11, 16], "direction_map": {11: "衰", 16: "友"}},
        "far":  {"distances": [7, 20], "direction_map": {7: "友", 20: "衰"}}
    },
    "ankai": {
        "near": {"distances": [3, 24], "direction_map": {3: "安", 24: "壊"}},
        "mid":  {"distances": [12, 15], "direction_map": {12: "安", 15: "壊"}},
        "far":  {"distances": [6, 21], "direction_map": {6: "壊", 21: "安"}}
    },
    "kisei": {
        "near": {"distances": [4, 23], "direction_map": {4: "危", 23: "成"}},
        "mid":  {"distances": [13, 14], "direction_map": {13: "危", 14: "成"}},
        "far":  {"distances": [5, 22], "direction_map": {5: "成", 22: "危"}}
    },
    "mei":    {"near": {"distances": [0], "direction_map": {0: "命"}}},
    "gyotai": {
        "near": {"distances": [9], "direction_map": {9: "業"}},
        "far":  {"distances": [18], "direction_map": {18: "胎"}}
    }
}
```

### 附帶修正: MONTH_START_MANSION

移除牛宿後，斗宿之後的索引全部 -1：
```python
MONTH_START_MANSION = {
    1: 11,   # 正月：室宿 (was 12)
    2: 13,   # 二月：奎宿 (was 14)
    3: 15,   # 三月：胃宿 (was 16)
    4: 17,   # 四月：畢宿 (was 18)
    5: 19,   # 五月：参宿 (was 20)
    6: 21,   # 六月：鬼宿 (was 22)
    7: 24,   # 七月：張宿 (was 25)
    8: 0,    # 八月：角宿 (unchanged)
    9: 2,    # 九月：氐宿 (unchanged)
    10: 4,   # 十月：心宿 (unchanged)
    11: 7,   # 十一月：斗宿 (unchanged)
    12: 9,   # 十二月：虛宿 (was 10)
}
```

## 影響範圍

| 檔案 | 修改內容 |
|------|---------|
| `backend/data/sukuyodo_mansions.json` | 移除牛宿、新增軫宿、重新排列索引、修正 relations distances |
| `backend/services/sukuyodo.py` | 修正 MONTH_START_MANSION、DISTANCE_TYPE_MAP、RELATION_SCORE_RANGES |
| `backend/services/japanese_calendar.py` | 無需修改（不依賴 27 宿） |

## 測試計畫

1. 驗證 1977/10/29 → 農曆九月十七 → 觜宿 (火)
2. 驗證 27 宿順序完整（0-26 無缺漏，七曜循環正確）
3. 驗證三九秘法距離覆蓋 0-26 全部 27 個距離
4. 驗證 MONTH_START_MANSION 宿名與索引一致
5. 以 1977/10/29 計算今日運勢，確認宿曜關係判定正確
6. 對照線上計算器（八雲院/syukuyo.com）交叉驗證

## Checklist

- [ ] 移除牛宿，新增軫宿資料
- [ ] 更新 27 宿索引
- [ ] 修正 relations distances
- [ ] 修正 MONTH_START_MANSION
- [ ] 修正 DISTANCE_TYPE_MAP
- [ ] 修正 find_compatible_mansions 中的距離定義
- [ ] 執行全部測試驗證
