---
title: 宿曜道核心計算嚴重 Bug 修復
type: fix
status: completed
created: 2026-02-14
---

# 宿曜道核心計算嚴重 Bug 修復

## 變更內容

修復 5 個經審計發現的嚴重計算錯誤，涵蓋本命宿計算、七曜轉換、關係類型比對、一粒萬倍日、六曜計算。

## 嚴重 Bug 清單

### BUG-1: MONTH_START_MANSION 偏移 1 宿 (8/12 個月錯誤)

**檔案**: `backend/services/sukuyodo.py:18-31`
**影響**: 約 67% 使用者得到錯誤的本命宿

修正值：
| 月 | 錯誤 | 正確 |
|----|------|------|
| 1月 | 11(危宿) | 12(室宿) |
| 2月 | 13(壁宿) | 14(奎宿) |
| 3月 | 15(婁宿) | 16(胃宿) |
| 4月 | 17(昴宿) | 18(畢宿) |
| 5月 | 19(觜宿) | 20(参宿) |
| 6月 | 21(井宿) | 22(鬼宿) |
| 7月 | 24(星宿) | 25(張宿) |
| 8月 | 0(角宿) | 0(角宿) -- 不變 |
| 9月 | 2(氐宿) | 2(氐宿) -- 不變 |
| 10月 | 4(心宿) | 4(心宿) -- 不變 |
| 11月 | 7(斗宿) | 7(斗宿) -- 不變 |
| 12月 | 9(女宿) | 10(虚宿) |

### BUG-2: 3 個函數未做 jp_weekday 轉換

**檔案**: `backend/services/sukuyodo.py`
**影響**: 吉日計算、職涯指引的七曜元素全部錯配

需修改的函數：
- `get_career_guidance` (~L1377): 加 `jp_weekday = (weekday + 1) % 7`
- `get_lucky_days` (~L1606): 同上
- `get_pair_lucky_days` (~L1889): 同上

### BUG-3: 中文 key 比對 romaji value

**檔案**: `backend/services/sukuyodo.py`
**影響**: 求職吉日判斷、離職日排除、吉日原因描述全部失效

需修改的位置：
- L1392: `["榮親", "業胎"]` -> `["eishin", "gyotai"]`
- L1418: `["安壞", "危成"]` -> `["ankai", "kisei"]`
- L1431: `["安壞", "危成"]` -> `["ankai", "kisei"]`
- L1715-1723: `_get_relation_benefit` dict key 改為 romaji

### BUG-4: 一粒萬倍日 9/12 個月錯誤

**檔案**: `backend/services/japanese_calendar.py:44-57`
**影響**: 一粒萬倍日判定幾乎全錯

替換整個 `ICHIRYUMANBAI_MAP`，改為正確的傳統定義：
```
1月: 丑(1)、午(6)    -- 不變
2月: 酉(9)、寅(2)    -- 索引 8->9
3月: 子(0)、卯(3)    -- 不變
4月: 卯(3)、辰(4)    -- 第二個改
5月: 巳(5)、午(6)    -- 兩個都改
6月: 午(6)、酉(9)    -- 兩個都改
7月: 子(0)、未(7)    -- 兩個都改
8月: 卯(3)、申(8)    -- 兩個都改
9月: 午(6)、酉(9)    -- 兩個都改
10月: 酉(9)、戌(10)  -- 兩個都改
11月: 子(0)、亥(11)  -- 兩個都改
12月: 子(0)、卯(3)   -- 不變
```

### BUG-5: 六曜計算使用西曆 + 排列順序錯

**檔案**: `backend/services/japanese_calendar.py:278, 31`
**影響**: 所有六曜結果錯誤

修正：
1. L31 排列順序改為 `["大安", "赤口", "先勝", "友引", "先負", "仏滅"]`
2. L278 改用農曆月日計算：先呼叫 `solar_to_lunar()` 取得農曆月日，再 `(lunar_month + lunar_day) % 6`

## 影響範圍

| 檔案 | 修改內容 |
|------|---------|
| `backend/services/sukuyodo.py` | BUG-1, BUG-2, BUG-3 |
| `backend/services/japanese_calendar.py` | BUG-4, BUG-5 |

共 2 個檔案，修改行數估計 ~30 行。

## 測試計畫

1. BUG-1: 用已知生日 (1977/10/29) 驗證本命宿是否與八雲院一致
2. BUG-2: 確認 get_career_guidance / get_lucky_days 回傳的七曜元素正確
3. BUG-3: 確認 eishin/gyotai 日被正確標記為求職吉日
4. BUG-4: 對照 2026 年日本曆注驗證一粒萬倍日
5. BUG-5: 對照 2026 年日本曆注驗證六曜

## Checklist

- [x] BUG-1: MONTH_START_MANSION 修正
- [x] BUG-2: jp_weekday 轉換修正
- [x] BUG-3: romaji key 修正
- [x] BUG-4: 一粒萬倍日修正
- [x] BUG-5: 六曜計算修正
- [x] 驗證測試全部通過
- [x] 運勢日曆重新產生
