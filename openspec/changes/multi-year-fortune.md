---
title: 十年流年功能
type: feature
status: completed
created: 2026-02-16
---

# 十年流年功能

## 變更內容

新增「流年」子 tab，顯示 10 年九曜流年趨勢圖與年度摘要。
使用者可一次查看未來/過去數年的運勢走向，掌握大週期規律。

功能包含：
- 後端新增 `/fortune/yearly-range` 批次查詢端點
- 前端 FortuneTab 新增第五個子 tab「流年」
- SVG 折線圖呈現 10 年 overall/career/love/health/wealth 趨勢
- 九曜星循環視覺化（大吉/吉/半吉/大凶色標）
- 年份範圍切換（預設當前年-2 ~ +7）

## 影響範圍

| 檔案 | 修改內容 |
|------|---------|
| `backend/routers/sukuyodo.py` | 新增 yearly-range 端點 |
| `backend/services/sukuyodo.py` | 新增 calculate_yearly_fortune_range 方法 |
| `frontend/src/composables/useSukuyodo.ts` | 新增型別 + API 呼叫 |
| `frontend/src/components/FortuneTab.vue` | 新增「流年」子 tab + SVG 圖表 |

## 測試計畫

1. `curl /api/sukuyodo/fortune/yearly-range?birth_date=1977-10-29&start_year=2024&end_year=2033` 確認回傳 10 年資料
2. 單年結果與既有 `/fortune/yearly/2026` 一致
3. 前端切換到「流年」tab 顯示折線圖
4. 年份範圍切換正常
5. 響應式：手機版圖表可橫滑

## Checklist

- [ ] 後端 yearly-range 端點
- [ ] 前端型別定義
- [ ] FortuneTab 流年子 tab
- [ ] SVG 折線圖
- [ ] 九曜星標記
- [ ] 響應式設計
- [ ] API 測試
- [ ] 瀏覽器測試
