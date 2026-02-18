<script setup lang="ts">
import { computed } from 'vue'

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

interface JapaneseCalendar {
  types: string[]
  labels: string[]
  is_super_lucky: boolean
}

interface PersonalDay {
  relation_type: string
  relation_name: string
  fortune_score: number
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
  japanese_calendar: JapaneseCalendar | null
  personal?: PersonalDay
}

interface CalendarData {
  year: number
  month: number
  days: CalendarDay[]
  statistics: {
    ryouhan_days: number
    kanro_count: number
    kongou_count: number
    rasetsu_count: number
    tensya_count?: number
    ichiryumanbai_count?: number
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

interface Props {
  calendarData: CalendarData | null
  loading: boolean
  hasBirthDate: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'changeMonth', delta: number): void
  (e: 'selectDay', date: string): void
}>()

const WEEKDAY_HEADERS = ['日', '月', '火', '水', '木', '金', '土']

const elementColors: Record<string, string> = {
  '木': '#4A9B5A',
  '金': '#C4A052',
  '土': '#8B7355',
  '日': '#E89B3C',
  '月': '#7CB3D9',
  '火': '#E85D4C',
  '水': '#2D3436'
}

const todayStr = computed(() => {
  const d = new Date()
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
})

const monthLabel = computed(() => {
  if (!props.calendarData) return ''
  return `${props.calendarData.year}年${props.calendarData.month}月`
})

// 計算月曆格子（補齊前面空白）
const calendarGrid = computed(() => {
  if (!props.calendarData || props.calendarData.days.length === 0) return []

  const firstDay = new Date(props.calendarData.days[0].date)
  const startWeekday = firstDay.getDay() // 0=Sun

  const grid: (CalendarDay | null)[] = []
  for (let i = 0; i < startWeekday; i++) {
    grid.push(null)
  }
  for (const day of props.calendarData.days) {
    grid.push(day)
  }
  return grid
})

function getMansionAbbr(name: string): string {
  return name.replace('宿', '')
}

function getScoreColor(score: number): string {
  if (score >= 80) return 'var(--kanro-color)'
  if (score >= 65) return 'var(--kongou-color)'
  if (score >= 50) return 'var(--text-secondary)'
  return 'var(--rasetsu-color)'
}

function getSankiColor(periodIndex: number): string {
  if (periodIndex === 1) return 'var(--kanro-color)'
  if (periodIndex === 2) return 'var(--rasetsu-color)'
  return '#5C8FA8'
}
</script>

<template>
  <div class="fortune-calendar">
    <!-- 月份導覽 -->
    <div class="calendar-nav">
      <button class="nav-btn" @click="emit('changeMonth', -1)" aria-label="上個月">
        <sl-icon name="chevron-left" aria-hidden="true"></sl-icon>
      </button>
      <h3 class="month-label">{{ monthLabel }}</h3>
      <button class="nav-btn" @click="emit('changeMonth', 1)" aria-label="下個月">
        <sl-icon name="chevron-right" aria-hidden="true"></sl-icon>
      </button>
    </div>

    <!-- 統計列 -->
    <div v-if="calendarData" class="calendar-stats">
      <span v-if="calendarData.statistics.kanro_count" class="stat-badge kanro">
        甘 {{ calendarData.statistics.kanro_count }}
      </span>
      <span v-if="calendarData.statistics.kongou_count" class="stat-badge kongou">
        金 {{ calendarData.statistics.kongou_count }}
      </span>
      <span v-if="calendarData.statistics.rasetsu_count" class="stat-badge rasetsu">
        羅 {{ calendarData.statistics.rasetsu_count }}
      </span>
      <span v-if="calendarData.statistics.ryouhan_days" class="stat-badge ryouhan">
        凌犯 {{ calendarData.statistics.ryouhan_days }}日
      </span>
      <span v-if="calendarData.statistics.tensya_count" class="stat-badge tensya">
        天赦 {{ calendarData.statistics.tensya_count }}
      </span>
      <span v-if="calendarData.statistics.ichiryumanbai_count" class="stat-badge ichiryu">
        万倍 {{ calendarData.statistics.ichiryumanbai_count }}
      </span>
    </div>

    <!-- 圖例 -->
    <div class="calendar-legend">
      <span class="legend-item"><span class="legend-dot kanro"></span>甘露</span>
      <span class="legend-item"><span class="legend-dot kongou"></span>金剛</span>
      <span class="legend-item"><span class="legend-dot rasetsu"></span>羅刹</span>
      <span class="legend-item"><span class="legend-dot ryouhan-legend"></span>凌犯</span>
      <template v-if="hasBirthDate">
        <span class="legend-item"><span class="legend-bar sanki-1"></span>躍動</span>
        <span class="legend-item"><span class="legend-bar sanki-2"></span>破壊</span>
        <span class="legend-item"><span class="legend-bar sanki-3"></span>再生</span>
      </template>
    </div>

    <!-- 載入中 -->
    <div v-if="loading" class="calendar-loading">
      <sl-spinner></sl-spinner>
      <span>讀取中...</span>
    </div>

    <!-- 月曆格 -->
    <div v-else-if="calendarData" class="calendar-grid">
      <!-- 星期標頭 -->
      <div
        v-for="header in WEEKDAY_HEADERS"
        :key="header"
        class="weekday-header"
        :class="{ 'weekend': header === '日' || header === '土' }"
      >{{ header }}</div>

      <!-- 日期格子 -->
      <template v-for="(cell, idx) in calendarGrid" :key="idx">
        <div v-if="cell === null" class="day-cell empty"></div>
        <div
          v-else
          class="day-cell"
          :class="{
            'is-today': cell.date === todayStr,
            'is-ryouhan': cell.ryouhan,
            'is-dark-week': cell.personal?.is_dark_week,
            'has-jp-lucky': cell.japanese_calendar?.is_super_lucky,
          }"
          @click="emit('selectDay', cell.date)"
        >
          <!-- 三期色帶 -->
          <div
            v-if="cell.personal"
            class="sanki-bar"
            :style="{ background: getSankiColor(cell.personal.sanki_period_index) }"
          ></div>

          <!-- 日期數字 -->
          <span class="day-number">{{ cell.day }}</span>

          <!-- 宿名 -->
          <span
            class="mansion-abbr"
            :style="{ color: elementColors[cell.day_mansion.element] || '#666' }"
          >{{ getMansionAbbr(cell.day_mansion.name_jp) }}</span>

          <!-- 特殊日標籤 -->
          <div class="day-tags">
            <span v-if="cell.special_day?.type === 'kanro'" class="tag kanro">甘</span>
            <span v-if="cell.special_day?.type === 'kongou'" class="tag kongou">金</span>
            <span v-if="cell.special_day?.type === 'rasetsu'" class="tag rasetsu">羅</span>
          </div>

          <!-- 日本選日標記 -->
          <div v-if="cell.japanese_calendar?.types?.length" class="jp-tags">
            <span
              v-for="label in cell.japanese_calendar.labels.slice(0, 2)"
              :key="label"
              class="jp-tag"
            >{{ label.slice(0, 2) }}</span>
          </div>

          <!-- 六害宿標記 -->
          <div v-if="cell.personal?.rokugai" class="rokugai-mark"></div>

          <!-- 運勢分數 -->
          <span
            v-if="cell.personal"
            class="fortune-dot"
            :style="{ background: getScoreColor(cell.personal.fortune_score) }"
            :title="`${cell.personal.fortune_score}點 ${cell.personal.relation_name}`"
          ></span>
        </div>
      </template>
    </div>

    <!-- 無生日提示 -->
    <p v-if="!hasBirthDate && calendarData" class="no-birth-hint">
      查詢本命宿後可顯示個人三期/運勢分數
    </p>
  </div>
</template>

<style scoped>
.fortune-calendar {
  display: flex;
  flex-direction: column;
  gap: var(--space-md, 16px);
}

/* 月份導覽 */
.calendar-nav {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-md, 16px);
}

.nav-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  min-height: 44px;
  min-width: 44px;
  background: var(--bg-surface, #292524);
  border: 1px solid var(--border, #57534e);
  border-radius: var(--radius-md, 8px);
  color: var(--text-secondary, #a8a29e);
  cursor: pointer;
  transition: background-color 0.2s, border-color 0.2s;
}

.nav-btn:hover {
  background: var(--bg-elevated, #44403c);
  border-color: var(--accent, #f59e0b);
  color: var(--text-primary, #fafaf9);
}

.nav-btn:focus-visible {
  outline: 2px solid var(--accent, #f59e0b);
  outline-offset: 2px;
}

.month-label {
  font-size: 18px;
  font-weight: 600;
  color: var(--accent, #f59e0b);
  margin: 0;
  min-width: 120px;
  text-align: center;
}

/* 統計列 */
.calendar-stats {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--space-sm, 8px);
}

.stat-badge {
  padding: 2px 8px;
  border-radius: var(--radius-full, 9999px);
  font-size: 12px;
  font-weight: 600;
}

.stat-badge.kanro { background: rgba(74, 155, 107, 0.2); color: var(--kanro-color); }
.stat-badge.kongou { background: rgba(212, 175, 55, 0.2); color: var(--kongou-color); }
.stat-badge.rasetsu { background: rgba(232, 93, 76, 0.2); color: var(--rasetsu-color); }
.stat-badge.ryouhan { background: var(--ryouhan-bg); color: #ff9999; }
.stat-badge.tensya { background: rgba(212, 175, 55, 0.15); color: var(--kongou-color); }
.stat-badge.ichiryu { background: rgba(74, 155, 107, 0.15); color: var(--kanro-color); }

/* 圖例 */
.calendar-legend {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--space-sm, 8px);
  font-size: 11px;
  color: var(--text-secondary, #a8a29e);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.legend-dot.kanro { background: var(--kanro-color); }
.legend-dot.kongou { background: var(--kongou-color); }
.legend-dot.rasetsu { background: var(--rasetsu-color); }
.legend-dot.ryouhan-legend { background: rgba(255, 100, 100, 0.4); }

.legend-bar {
  width: 16px;
  height: 3px;
  border-radius: 2px;
}

.legend-bar.sanki-1 { background: var(--kanro-color); }
.legend-bar.sanki-2 { background: var(--rasetsu-color); }
.legend-bar.sanki-3 { background: #5C8FA8; }

/* 載入 */
.calendar-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm, 8px);
  padding: var(--space-xl, 32px);
  color: var(--text-secondary, #a8a29e);
}

/* 月曆格 */
.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 3px;
}

.weekday-header {
  text-align: center;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary, #a8a29e);
  padding: 4px 0 8px;
}

.weekday-header.weekend {
  color: var(--rasetsu-color);
}

/* 日期格子 */
.day-cell {
  position: relative;
  min-height: 64px;
  padding: 3px;
  background: var(--bg-surface, #292524);
  border-radius: var(--radius-sm, 4px);
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  transition: background-color 0.15s, border-color 0.15s;
  border: 1px solid transparent;
  overflow: hidden;
}

.day-cell.empty {
  background: transparent;
  cursor: default;
}

.day-cell:not(.empty):hover {
  background: var(--bg-elevated, #44403c);
  border-color: var(--border, #57534e);
}

.day-cell.is-today {
  border-color: var(--kongou-color);
  box-shadow: 0 0 0 1px var(--kongou-color);
}

.day-cell.is-ryouhan {
  background: var(--ryouhan-bg);
}

.day-cell.is-dark-week {
  background: var(--dark-week-bg);
}

.day-cell.is-ryouhan.is-dark-week {
  background: linear-gradient(135deg, var(--ryouhan-bg), var(--dark-week-bg));
}

.day-cell.has-jp-lucky {
  box-shadow: inset 0 0 0 1px rgba(212, 175, 55, 0.3);
}

/* 三期色帶 */
.sanki-bar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
}

/* 日期數字 */
.day-number {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary, #fafaf9);
  line-height: 1;
  margin-top: 4px;
}

/* 宿名 */
.mansion-abbr {
  font-size: 11px;
  font-weight: 600;
  line-height: 1;
}

/* 特殊日標籤 */
.day-tags {
  display: flex;
  gap: 1px;
}

.tag {
  font-size: 9px;
  font-weight: 700;
  padding: 1px 4px;
  border-radius: 2px;
  line-height: 14px;
}

.tag.kanro { background: rgba(74, 155, 107, 0.3); color: var(--kanro-color); }
.tag.kongou { background: rgba(212, 175, 55, 0.3); color: var(--kongou-color); }
.tag.rasetsu { background: rgba(232, 93, 76, 0.3); color: var(--rasetsu-color); }

/* 日本選日 */
.jp-tags {
  display: flex;
  gap: 1px;
}

.jp-tag {
  font-size: 8px;
  color: var(--kongou-color);
  opacity: 0.8;
}

/* 六害宿標記 */
.rokugai-mark {
  position: absolute;
  top: 3px;
  right: 3px;
  width: 0;
  height: 0;
  border-left: 5px solid transparent;
  border-top: 5px solid var(--rasetsu-color);
}

/* 運勢分數 */
.fortune-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  position: absolute;
  bottom: 3px;
  right: 3px;
}

/* 無生日提示 */
.no-birth-hint {
  text-align: center;
  font-size: 12px;
  color: var(--text-muted, #6B5A8E);
  margin: 0;
}

/* 響應式 */
@media (min-width: 768px) {
  .day-cell {
    min-height: 90px;
    padding: 4px;
    gap: 2px;
  }

  .day-number {
    font-size: 16px;
    margin-top: 6px;
  }

  .mansion-abbr {
    font-size: 12px;
  }

  .tag {
    font-size: 10px;
    padding: 1px 5px;
    line-height: 16px;
  }

  .jp-tag {
    font-size: 9px;
  }

  .fortune-dot {
    width: 10px;
    height: 10px;
  }
}

@media (prefers-reduced-motion: reduce) {
  * {
    transition: none !important;
  }
}
</style>
