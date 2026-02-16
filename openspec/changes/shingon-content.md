---
title: 真言宗專用內容補充、佛尊改佛菩薩
type: fix
status: completed
created: 2026-02-16
---

# 真言宗專用內容補充

## 變更內容

1. 特殊日加入真言宗佛事建議（護摩、修法、出家、灌頂、寫經等）
2. 全站「佛尊」統一改為「佛菩薩」
3. 知識內容加入真言宗修行脈絡的說明

## 影響範圍

| 檔案 | 修改 |
|------|------|
| `backend/services/sukuyodo.py` | SPECIAL_DAY_INFO 描述加入真言宗佛事 |
| `backend/data/sukuyodo_mansions.json` | 知識內容加入真言宗行事、佛尊→佛菩薩 |
| `frontend/src/components/LuckyDaysTab.vue` | advice 加入真言宗行事 |
| `frontend/src/components/FortuneTab.vue` | 佛尊→佛菩薩 |

## 測試計畫

1. 特殊日卡片顯示真言宗相關建議
2. 全站無「佛尊」殘留
3. 知識 tab 內容正確
