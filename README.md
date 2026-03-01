# Sukuyodo (宿曜道)

Japanese Esoteric Buddhist Astrology System / 日本真言宗宿曜占星術系統

Based on the *Xiuyao Jing* (宿曜經, T21 No.1299), a Tang dynasty Buddhist astrological text translated by Amoghavajra (不空三藏) in 759 CE. This system maps birthdays to 27 lunar mansions and analyzes interpersonal compatibility using the Three-Nine Secret Method (三九秘法).

**[Live Demo](https://sukuyodo.dashai.dev/)**

## Features

**Natal Mansion Lookup (本命宿查詢)**
- Convert any birthday to one of 27 lunar mansions via the Chinese lunisolar calendar
- Each mansion has associated element (五行), weekday planet (七曜), and personality traits

**Compatibility Analysis (相性診斷)**
- Six relationship types: 命 / 業胎 / 栄親 / 友衰 / 安壊 / 危成
- Distance classification: near / mid / far with distinct interpretations
- Element bonus calculation (五行相生 +5/+10)

**Classical Sutra Analysis (原典三九秘法)**
- Three-Nine position mapping with bidirectional analysis
- Direct sutra quotes from T21 p.397c-398a with CBETA references
- Plain-language interpretations personalized with actual mansion names

**Fortune (運勢)**
- Daily / Weekly / Monthly / Yearly fortune based on mansion cycles
- Nine-Star Year Fate (九曜流年) with classical temple-sourced ratings
- Ryouhan (凌犯) reversal detection

**Auspicious Days (吉日查詢)**
- Category-based filtering: career, moving, marriage, grooming, etc.
- Cross-references Kanro (甘露日), Kongou (金剛峯日), Rasetsu (羅刹日)
- Dark Week (暗黒の一週間) avoidance

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + SQLModel + PostgreSQL (Neon) |
| Frontend | Vite + Vue 3 + TypeScript + Shoelace |
| Deployment | Render (API) + Vercel (SPA) |
| Calendar | lunarcalendar (Python) for solar-to-lunar conversion |
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
│   │   ├── components/    # MatchTab, FortuneTab, CalendarTab, etc.
│   │   ├── composables/   # useSukuyodo.ts (API + types)
│   │   └── styles/        # Design system variables
│   └── vite.config.ts
└── openspec/              # Change proposals (spec-driven development)
```

## Verification

All calculations are cross-verified against:
- **CBETA T21n1299** (Taisho Tripitaka, Koryo edition) — primary source
- **Yakumoin.net** (八雲院) — 27-mansion compatibility tables
- **Temple sources** (放生寺/大聖院/岡寺) — Nine-Star ratings

729 compatibility combinations, 23 Ryouhan pairs, 21 special day groups, and 6 Six-Harm mansions have been verified across 6 rounds of automated testing (230+ test items).

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
