// iCalendar (.ics) 產生工具
// RFC 5545: https://datatracker.ietf.org/doc/html/rfc5545

// ============================================================================
// Types (對應月曆 API /calendar/monthly/ 回傳結構)
// ============================================================================

interface DayMansion {
  name_jp: string
  index: number
  element: string
}

interface SpecialDay {
  type: string
  name: string
  level: string
  ryouhan_reversed: boolean
}

interface PersonalDay {
  relation_type: string
  relation_name: string
  fortune_score: number
  level?: string
  level_name?: string
  sanki_period: string
  sanki_period_index: number
  is_dark_week: boolean
  rokugai: boolean | null
}

interface CalendarDay {
  date: string
  day: number
  weekday: string
  day_mansion: DayMansion
  special_day: SpecialDay | null
  ryouhan: { active: boolean; lunar_month: number } | null
  japanese_calendar: { types: string[]; labels: string[]; is_super_lucky: boolean } | null
  personal?: PersonalDay
}

export interface CalendarData {
  year: number
  month: number
  days: CalendarDay[]
  statistics: {
    ryouhan_days: number
    kanro_count: number
    kongou_count: number
    rasetsu_count: number
  }
  personal?: {
    your_mansion: {
      name_jp: string
      reading: string
      element: string
      index: number
    }
  }
}

export interface IcsParams {
  calendars: CalendarData[]
  mansionName: string
  mansionElement: string
  birthDate: string
  year: number
}

// ============================================================================
// 輔助函式
// ============================================================================

function escapeIcsText(text: string): string {
  return text
    .replace(/\\/g, '\\\\')
    .replace(/;/g, '\\;')
    .replace(/,/g, '\\,')
    .replace(/\n/g, '\\n')
}

function foldLine(line: string): string {
  const encoder = new TextEncoder()
  const bytes = encoder.encode(line)
  if (bytes.length <= 75) return line

  const parts: string[] = []
  let start = 0

  while (start < line.length) {
    // 第一行 75 bytes，後續行 74 bytes（含前綴空格）
    const maxBytes = start === 0 ? 75 : 74
    let end = start
    let currentBytes = 0

    while (end < line.length) {
      const charBytes = encoder.encode(line[end]).length
      if (currentBytes + charBytes > maxBytes) break
      currentBytes += charBytes
      end++
    }

    if (end === start) {
      // 單一字元超過限制（不應發生），強制推進
      end = start + 1
    }

    parts.push(line.substring(start, end))
    start = end
  }

  return parts.join('\r\n ')
}

function formatIcsDate(dateStr: string): string {
  // "2026-01-15" → "20260115"
  return dateStr.replace(/-/g, '')
}

function getFortuneLevel(score: number, levelName?: string): string {
  if (levelName) return levelName
  if (score >= 90) return '大吉'
  if (score >= 75) return '吉'
  if (score >= 60) return '中吉'
  if (score >= 45) return '小凶'
  return '凶'
}

function generateUid(date: string, index: number): string {
  return `${date}-${index}@sukuyodo`
}

// ============================================================================
// ICS 產生
// ============================================================================

function buildDayEvent(day: CalendarDay, index: number): string[] {
  const personal = day.personal
  const level = personal
    ? getFortuneLevel(personal.fortune_score, personal.level_name)
    : null

  // 標題: 等級 | 三期 | 特殊日/凌犯/暗黒
  // 例: 中吉 | 躍動 | 甘露日
  //     凶 | 破壊 | 羅刹日 凌犯 暗黒
  //     大吉 | 再生
  const titleSegments: string[] = []
  if (level) titleSegments.push(level)
  if (personal) {
    // 三期：去掉「の週」縮短
    const sankiShort = personal.sanki_period.replace('の週', '')
    titleSegments.push(sankiShort)
  }
  // 第三段：特殊標記
  const markers: string[] = []
  if (day.special_day) {
    const reversed = day.special_day.ryouhan_reversed ? '(逆転)' : ''
    markers.push(`${day.special_day.name}${reversed}`)
  }
  if (day.ryouhan?.active && !day.special_day) {
    markers.push('凌犯')
  }
  if (personal?.is_dark_week) {
    markers.push('暗黒')
  }
  if (personal?.rokugai) {
    markers.push('六害宿')
  }
  if (markers.length > 0) {
    titleSegments.push(markers.join(' '))
  }
  const summary = titleSegments.join(' | ')

  // 描述（詳細資訊）
  const descParts: string[] = []
  if (personal) {
    descParts.push(`運勢: ${personal.fortune_score} (${level})`)
    descParts.push(`關係: ${personal.relation_name}`)
    descParts.push(`宿: ${day.day_mansion.name_jp}(${day.day_mansion.element}) - ${day.weekday}`)
    descParts.push(`三期: ${personal.sanki_period}`)
  }
  if (day.special_day) {
    const sdLabel = day.special_day.ryouhan_reversed
      ? `${day.special_day.name} (凌犯逆転: ${day.special_day.level})`
      : `${day.special_day.name} (${day.special_day.level})`
    descParts.push(`特殊日: ${sdLabel}`)
  }
  if (day.ryouhan?.active) {
    descParts.push('-- 凌犯期間: 吉凶逆転に注意 --')
  }
  if (personal?.is_dark_week) {
    descParts.push('-- 暗黒の一週間 --')
  }
  if (personal?.rokugai) {
    descParts.push('-- 六害宿 --')
  }

  const description = descParts.join('\\n')

  // 全天事件（DTSTART/DTEND 都用 VALUE=DATE）
  const dtStart = formatIcsDate(day.date)
  // 全天事件的 DTEND 是隔天
  const nextDate = new Date(day.date)
  nextDate.setDate(nextDate.getDate() + 1)
  const dtEnd = formatIcsDate(nextDate.toISOString().slice(0, 10))

  const lines: string[] = [
    'BEGIN:VEVENT',
    foldLine(`UID:${generateUid(day.date, index)}`),
    `DTSTART;VALUE=DATE:${dtStart}`,
    `DTEND;VALUE=DATE:${dtEnd}`,
    foldLine(`SUMMARY:${escapeIcsText(summary)}`),
  ]

  if (description) {
    lines.push(foldLine(`DESCRIPTION:${description}`))
  }

  lines.push('TRANSP:TRANSPARENT')
  lines.push('END:VEVENT')

  return lines
}

export function generateIcsCalendar(params: IcsParams): string | null {
  const { calendars, mansionName, mansionElement, birthDate, year } = params

  // 收集所有日期的事件
  const allDays: CalendarDay[] = []
  for (const cal of calendars) {
    allDays.push(...cal.days)
  }

  if (allDays.length === 0) return null

  const now = new Date()
  const dtstamp = now.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '')

  const lines: string[] = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    foldLine(`PRODID:-//Sukuyodo//Fortune Calendar//${year}//ZH`),
    'CALSCALE:GREGORIAN',
    'METHOD:PUBLISH',
    foldLine(`X-WR-CALNAME:${escapeIcsText(`${mansionName}(${mansionElement}) ${year} 年運勢`)}`),
    `X-WR-TIMEZONE:Asia/Taipei`,
  ]

  for (let i = 0; i < allDays.length; i++) {
    const day = allDays[i]
    const eventLines = buildDayEvent(day, i)
    // 每個事件加入 DTSTAMP
    const insertIdx = eventLines.indexOf('BEGIN:VEVENT') + 1
    eventLines.splice(insertIdx, 0, `DTSTAMP:${dtstamp}`)
    lines.push(...eventLines)
  }

  lines.push('END:VCALENDAR')

  return lines.join('\r\n')
}

export function downloadIcs(content: string, filename: string) {
  const blob = new Blob([content], { type: 'text/calendar;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
