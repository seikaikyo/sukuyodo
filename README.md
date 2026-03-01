<div align="center">

# 宿曜道 Sukuyodo

**Japanese Esoteric Buddhist Astrology System**

**日本密教宿曜占星術システム**

**日本真言宗密教占星術系統**

[Live Demo](https://sukuyodo.dashai.dev/) | [API](https://sukuyodo-backend.onrender.com/docs)

</div>

---

## English

Sukuyodo is a computational astrology system based on the *Xiuyao Jing* (宿曜經, T21 No.1299), a Buddhist astrological text translated by Amoghavajra (不空三藏) in 759 CE during the Tang dynasty. The system maps birthdays to 27 lunar mansions through the Chinese lunisolar calendar and calculates interpersonal compatibility using the Three-Nine Secret Method (三九秘法).

All calculations are verified against the original Taisho Tripitaka text (CBETA, Koryo edition), with 729 compatibility combinations, 23 Ryouhan pairs, and 21 special day groups confirmed across 6 rounds of automated testing (230+ items).

### Features

- **Natal Mansion** — Map any birthday to one of 27 lunar mansions with element, planet, and personality traits
- **Compatibility** — Six relationship types (命/業胎/栄親/友衰/安壊/危成), distance classification, element bonuses
- **Classical Sutra Analysis** — Bidirectional Three-Nine position mapping with direct sutra quotes (T21 p.397c-398a) and plain-language interpretation
- **Fortune** — Daily, weekly, monthly, yearly fortune with Nine-Star Year Fate (九曜流年) and Ryouhan reversal detection
- **Auspicious Days** — Category-based filtering with Kanro, Kongou, Rasetsu cross-references and Dark Week avoidance

---

## 日本語

宿曜道は、唐代に不空三藏が漢訳した『宿曜経』(大正蔵 T21 No.1299, 759年)に基づく密教占星術システムです。旧暦を用いて誕生日を二十七宿に変換し、三九秘法により人間関係の相性を算出します。

すべての計算は大正蔵原典(CBETA、高麗蔵底本)と照合済みです。729通りの相性組合せ、凌犯23組、特殊日21組を含む230項目以上を6回の自動検証で確認しています。

### 機能

- **本命宿** — 誕生日から二十七宿を判定、五行・七曜・性格特性を表示
- **相性診断** — 六種関係(命/業胎/栄親/友衰/安壊/危成)、距離分類、五行加算
- **原典三九秘法** — 双方向の三九位置分析、経文直接引用(T21 p.397c-398a)、現代語解釈
- **運勢** — 日運/週運/月運/年運、九曜流年(寺院典拠)、凌犯逆転検出
- **吉日検索** — 用途別フィルタ(仕事/引越/結婚/理髪等)、甘露日/金剛峯日/羅刹日、暗黒の一週間回避

---

## 正體中文

宿曜道是以唐代不空三藏所譯《宿曜經》(大正藏 T21 No.1299, 759年)為基礎的密教占星術系統。透過農曆將生日對應至二十七宿，以三九秘法計算人際相性。

所有運算皆與大正藏原典(CBETA 高麗藏底本)比對驗證，涵蓋 729 種相性組合、23 組凌犯、21 組特殊日，經 6 輪自動化測試共 230 餘項全數通過。

### 功能

- **本命宿查詢** — 任何生日轉換至二十七宿，顯示五行、七曜、性格特質
- **相性診斷** — 六種關係類型(命/業胎/栄親/友衰/安壊/危成)、距離分類、五行加成
- **原典三九秘法** — 雙向三九位置分析，直接引用經文(T21 p.397c-398a)，白話解讀
- **運勢** — 日運/週運/月運/年運、九曜流年(寺院原典)、凌犯逆轉偵測
- **吉日查詢** — 依用途篩選(事業/搬遷/婚姻/剃髮等)、甘露日/金剛峯日/羅刹日、暗黒の一週間迴避

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + SQLModel + PostgreSQL (Neon) |
| Frontend | Vite + Vue 3 + TypeScript + PrimeVue |
| Deployment | Render (API) + Vercel (SPA) |
| Calendar | lunarcalendar (Python) |
| Reference | CBETA Taisho Tripitaka T21n1299 (Koryo edition) |

## Architecture

```
sukuyodo/
├── backend/
│   ├── data/              # 27 mansions JSON, CBETA reference
│   ├── services/
│   │   └── sukuyodo.py    # Core calculation engine (~5000 lines)
│   ├── routers/           # FastAPI endpoints
│   └── main.py
├── frontend/
│   ├── src/
│   │   ├── components/    # MatchTab, FortuneTab, CalendarTab
│   │   ├── composables/   # useSukuyodo.ts (API + types)
│   │   └── styles/        # Design system variables
│   └── vite.config.ts
└── openspec/              # Change proposals (spec-driven development)
```

## Local Development

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8001

# Frontend
cd frontend
npm install && npm run dev
```

## License

MIT
