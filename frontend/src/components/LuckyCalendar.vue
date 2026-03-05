<script setup lang="ts">
import { computed, ref } from 'vue'
import type { LuckyCalendarDay } from '../composables/useSukuyodo'

interface Props {
  days: Record<string, LuckyCalendarDay[]>
  year: number
  month: number
  loading: boolean
  mode: 'personal' | 'pair'
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'changeMonth', delta: number): void
}>()

const selectedDate = ref<string | null>(null)

const WEEKDAY_HEADERS = ['日', '月', '火', '水', '木', '金', '土']

// 分類色彩映射（個人吉日用）
const CATEGORY_COLORS: Record<string, { bg: string; color: string; abbr: string }> = {
  career:   { bg: 'rgba(61, 90, 128, 0.25)', color: '#3D5A80', abbr: '事' },
  study:    { bg: 'rgba(37, 99, 235, 0.20)', color: '#2563EB', abbr: '學' },
  marriage: { bg: 'rgba(197, 48, 48, 0.20)', color: '#C53030', abbr: '婚' },
  travel:   { bg: 'rgba(90, 127, 165, 0.25)', color: '#5A7FA5', abbr: '旅' },
  dating:   { bg: 'rgba(232, 93, 76, 0.20)', color: '#E85D4C', abbr: '情' },
  medical:  { bg: 'rgba(45, 122, 79, 0.20)', color: '#2D7A4F', abbr: '醫' },
  housing:  { bg: 'rgba(139, 115, 85, 0.20)', color: '#8B7355', abbr: '宅' },
  grooming: { bg: 'rgba(139, 92, 246, 0.20)', color: '#8B5CF6', abbr: '修' },
  beauty:   { bg: 'rgba(219, 39, 119, 0.20)', color: '#DB2777', abbr: '美' },
  shopping: { bg: 'rgba(184, 134, 11, 0.20)', color: '#B8860B', abbr: '購' },
}

// 雙人 action 縮寫映射
const ACTION_ABBRS: Record<string, string> = {
  date: '約',
  confession: '告',
  meet_parents: '見',
  engagement: '訂',
  register: '登',
  wedding: '禮',
  travel: '旅',
  discussion: '商',
  visit: '訪',
  gift: '送',
  gathering: '聚',
  collaboration: '合',
}

const monthLabel = computed(() => `${props.year}年${props.month}月`)

const todayStr = computed(() => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
})

// 月曆格子
const calendarGrid = computed(() => {
  const firstDate = new Date(props.year, props.month - 1, 1)
  const startWeekday = firstDate.getDay()
  const daysInMonth = new Date(props.year, props.month, 0).getDate()

  const grid: (number | null)[] = []
  for (let i = 0; i < startWeekday; i++) grid.push(null)
  for (let d = 1; d <= daysInMonth; d++) grid.push(d)
  return grid
})

function getDateKey(dayNum: number): string {
  return `${props.year}-${String(props.month).padStart(2, '0')}-${String(dayNum).padStart(2, '0')}`
}

function getDayItems(dayNum: number): LuckyCalendarDay[] {
  return props.days[getDateKey(dayNum)] || []
}

// 取得該日的唯一分類集合（個人模式）
function getDayCategories(dayNum: number): { bg: string; color: string; abbr: string }[] {
  const items = getDayItems(dayNum)
  const seen = new Set<string>()
  const result: { bg: string; color: string; abbr: string }[] = []
  for (const item of items) {
    if (!seen.has(item.category)) {
      seen.add(item.category)
      result.push(CATEGORY_COLORS[item.category] || { bg: 'rgba(0,0,0,0.1)', color: '#666', abbr: item.category_name[0] })
    }
    if (result.length >= 3) break
  }
  return result
}

// 取得該日的唯一 action 集合（雙人模式）
function getDayActions(dayNum: number): { abbr: string; name: string }[] {
  const items = getDayItems(dayNum)
  const seen = new Set<string>()
  const result: { abbr: string; name: string }[] = []
  for (const item of items) {
    if (!seen.has(item.action)) {
      seen.add(item.action)
      result.push({ abbr: ACTION_ABBRS[item.action] || item.action_name?.[0] || item.name?.[0] || '?', name: (item as any).name || item.action_name || item.action })
    }
    if (result.length >= 3) break
  }
  return result
}

function getExtraCount(dayNum: number): number {
  const items = getDayItems(dayNum)
  if (props.mode === 'personal') {
    const cats = new Set(items.map(i => i.category))
    return Math.max(0, cats.size - 3)
  } else {
    const actions = new Set(items.map(i => i.action))
    return Math.max(0, actions.size - 3)
  }
}

function toggleDay(dayNum: number) {
  const key = getDateKey(dayNum)
  if (!getDayItems(dayNum).length) return
  selectedDate.value = selectedDate.value === key ? null : key
}

function isSelected(dayNum: number): boolean {
  return selectedDate.value === getDateKey(dayNum)
}

// 在格子後面計算展開行的位置
const expandedRow = computed(() => {
  if (!selectedDate.value) return null
  const dayNum = parseInt(selectedDate.value.split('-')[2])
  const firstDate = new Date(props.year, props.month - 1, 1)
  const startWeekday = firstDate.getDay()
  const cellIndex = startWeekday + dayNum - 1
  const row = Math.floor(cellIndex / 7)
  return row
})

// 將格子按行分組，插入展開面板
const gridWithExpand = computed(() => {
  const grid = calendarGrid.value
  const rows: { type: 'cells' | 'expand'; cells?: (number | null)[]; date?: string; items?: LuckyCalendarDay[] }[] = []

  for (let i = 0; i < grid.length; i += 7) {
    const rowCells = grid.slice(i, i + 7)
    rows.push({ type: 'cells', cells: rowCells })

    // 如果這行包含選中的日期，在行後面插入展開面板
    if (expandedRow.value !== null && Math.floor(i / 7) === expandedRow.value && selectedDate.value) {
      const items = props.days[selectedDate.value] || []
      if (items.length > 0) {
        rows.push({ type: 'expand', date: selectedDate.value, items })
      }
    }
  }

  return rows
})

function formatExpandDate(dateStr: string): string {
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}/${d.getDate()}`
}

function getWeekdayName(dateStr: string): string {
  const d = new Date(dateStr)
  const names = ['日', '月', '火', '水', '木', '金', '土']
  return names[d.getDay()] + '曜'
}

function getRatingClass(rating: string): string {
  if (rating === '大吉') return 'top'
  if (rating === '吉') return 'good'
  return 'mid'
}
</script>

<template>
  <div class="lucky-calendar">
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

    <!-- 圖例 -->
    <div v-if="mode === 'personal'" class="calendar-legend">
      <span v-for="(info, key) in CATEGORY_COLORS" :key="key" class="legend-item">
        <span class="legend-badge" :style="{ background: info.bg, color: info.color }">{{ info.abbr }}</span>
      </span>
    </div>

    <!-- 載入中 -->
    <div v-if="loading" class="calendar-loading">
      <sl-spinner></sl-spinner>
      <span>讀取中...</span>
    </div>

    <!-- 月曆 -->
    <div v-else class="calendar-body">
      <template v-for="(row, rowIdx) in gridWithExpand" :key="rowIdx">
        <!-- 日期格子行 -->
        <div v-if="row.type === 'cells'" class="calendar-row">
          <!-- 星期標頭（只在第一行前面顯示） -->
          <template v-if="rowIdx === 0">
            <div class="weekday-row">
              <div
                v-for="header in WEEKDAY_HEADERS"
                :key="header"
                class="weekday-header"
                :class="{ weekend: header === '日' || header === '土' }"
              >{{ header }}</div>
            </div>
          </template>

          <div class="grid-row">
            <template v-for="(cell, cellIdx) in row.cells" :key="cellIdx">
              <div v-if="cell === null" class="day-cell empty"></div>
              <div
                v-else
                class="day-cell"
                :class="{
                  'is-today': getDateKey(cell) === todayStr,
                  'has-items': getDayItems(cell).length > 0,
                  'is-selected': isSelected(cell),
                }"
                @click="toggleDay(cell)"
              >
                <span class="day-number">{{ cell }}</span>

                <!-- 個人模式：分類色塊 -->
                <div v-if="mode === 'personal'" class="day-badges">
                  <span
                    v-for="cat in getDayCategories(cell)"
                    :key="cat.abbr"
                    class="day-badge"
                    :style="{ background: cat.bg, color: cat.color }"
                  >{{ cat.abbr }}</span>
                  <span v-if="getExtraCount(cell) > 0" class="day-badge extra">+{{ getExtraCount(cell) }}</span>
                </div>

                <!-- 雙人模式：action 縮寫 -->
                <div v-else class="day-badges">
                  <span
                    v-for="act in getDayActions(cell)"
                    :key="act.abbr"
                    class="day-badge pair-badge"
                  >{{ act.abbr }}</span>
                  <span v-if="getExtraCount(cell) > 0" class="day-badge extra">+{{ getExtraCount(cell) }}</span>
                </div>
              </div>
            </template>
          </div>
        </div>

        <!-- 展開詳情面板 -->
        <div v-else-if="row.type === 'expand' && row.items && row.date" class="expand-panel">
          <div class="expand-header">
            <span class="expand-date">{{ formatExpandDate(row.date) }} {{ getWeekdayName(row.date) }}</span>
            <button class="expand-close" @click="selectedDate = null" aria-label="關閉">
              <sl-icon name="x-lg"></sl-icon>
            </button>
          </div>

          <div class="expand-items">
            <div
              v-for="(item, itemIdx) in row.items"
              :key="itemIdx"
              class="expand-item"
            >
              <div class="item-header">
                <span v-if="mode === 'personal'" class="item-category-badge" :style="{
                  background: (CATEGORY_COLORS[item.category] || {}).bg || 'rgba(0,0,0,0.1)',
                  color: (CATEGORY_COLORS[item.category] || {}).color || '#666'
                }">{{ item.category_name || '' }}</span>
                <span class="item-action-name">{{ (item as any).name || item.action_name || '' }}</span>
                <span class="item-rating" :class="getRatingClass(item.rating)">{{ item.rating }}</span>
                <span class="item-score">{{ item.score }}分</span>
              </div>

              <p v-if="item.reason" class="item-reason">{{ item.reason }}</p>

              <div v-if="item.best_time || item.avoid_time" class="item-times">
                <div v-if="item.best_time" class="time-row best">
                  <span class="time-label">推薦時段</span>
                  <span class="time-value">{{ item.best_time }}</span>
                </div>
                <div v-if="item.avoid_time" class="time-row avoid">
                  <span class="time-label">留意事項</span>
                  <span class="time-value">{{ item.avoid_time }}</span>
                </div>
              </div>

              <p v-if="item.tip" class="item-tip">{{ item.tip }}</p>

              <!-- 雙人白話建議 -->
              <div v-if="item.advice" class="advice-box">
                <p class="advice-summary">{{ item.advice.summary }}</p>
                <div v-if="item.advice.do?.length" class="advice-list do-list">
                  <span class="advice-label">宜</span>
                  <ul>
                    <li v-for="(d, i) in item.advice.do" :key="i">{{ d }}</li>
                  </ul>
                </div>
                <div v-if="item.advice.avoid?.length" class="advice-list avoid-list">
                  <span class="advice-label">忌</span>
                  <ul>
                    <li v-for="(a, i) in item.advice.avoid" :key="i">{{ a }}</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.lucky-calendar {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

/* 月份導覽 */
.calendar-nav {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-md);
}

.nav-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  min-height: 44px;
  min-width: 44px;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  cursor: pointer;
  transition: background-color 0.2s, border-color 0.2s;
}

.nav-btn:hover {
  background: var(--bg-elevated);
  border-color: var(--accent);
  color: var(--text-primary);
}

.nav-btn:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.month-label {
  font-size: 18px;
  font-weight: 600;
  color: var(--accent);
  margin: 0;
  min-width: 120px;
  text-align: center;
}

/* 圖例 */
.calendar-legend {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--space-xs);
}

.legend-item {
  display: flex;
  align-items: center;
}

.legend-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  padding: 1px 5px;
  border-radius: 3px;
  line-height: 16px;
}

/* 載入中 */
.calendar-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  padding: var(--space-xl);
  color: var(--text-secondary);
}

/* 月曆主體 */
.calendar-body {
  display: flex;
  flex-direction: column;
}

/* 星期標頭 */
.weekday-row {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 3px;
}

.weekday-header {
  text-align: center;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  padding: 4px 0 8px;
}

.weekday-header.weekend {
  color: var(--rasetsu-color);
}

/* 格子行 */
.grid-row {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 3px;
}

/* 日期格子 */
.day-cell {
  position: relative;
  min-height: 64px;
  padding: 4px 2px;
  background: var(--bg-surface);
  border-radius: var(--radius-sm);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  transition: background-color 0.15s, border-color 0.15s;
  border: 1px solid transparent;
}

.day-cell.empty {
  background: transparent;
  cursor: default;
}

.day-cell.has-items {
  cursor: pointer;
}

.day-cell.has-items:hover {
  background: var(--bg-elevated);
  border-color: var(--border);
}

.day-cell:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.day-cell.is-today {
  border-color: var(--kongou-color);
  box-shadow: 0 0 0 1px var(--kongou-color);
}

.day-cell.is-selected {
  border-color: var(--accent);
  background: rgba(139, 105, 20, 0.08);
}

.day-number {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
}

/* 分類/action 色塊 */
.day-badges {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 2px;
  min-height: 18px;
}

.day-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 9px;
  font-weight: 700;
  padding: 1px 4px;
  border-radius: 2px;
  line-height: 14px;
  white-space: nowrap;
}

.day-badge.pair-badge {
  background: rgba(139, 92, 246, 0.20);
  color: #8B5CF6;
}

.day-badge.extra {
  background: rgba(0, 0, 0, 0.06);
  color: var(--text-secondary);
  font-size: 8px;
}

/* 展開面板 */
.expand-panel {
  background: var(--bg-surface);
  border: 1px solid var(--accent);
  border-radius: var(--radius-md);
  padding: var(--space-md);
  margin: var(--space-xs) 0;
  animation: expandIn 0.2s ease;
}

@keyframes expandIn {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}

.expand-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-md);
  padding-bottom: var(--space-sm);
  border-bottom: 1px solid var(--border);
}

.expand-date {
  font-size: var(--font-lg);
  font-weight: 700;
  color: var(--accent);
}

.expand-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  min-height: 44px;
  min-width: 44px;
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: background-color 0.2s;
}

.expand-close:hover {
  background: var(--bg-elevated);
  color: var(--text-primary);
}

/* 展開項目 */
.expand-items {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.expand-item {
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--accent);
}

.item-header {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  flex-wrap: wrap;
}

.item-category-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: var(--radius-xs);
}

.item-action-name {
  font-size: var(--font-sm);
  font-weight: 600;
  color: var(--text-primary);
}

.item-rating {
  padding: 2px 8px;
  border-radius: var(--radius-xs);
  font-size: var(--font-xs);
  font-weight: 700;
  letter-spacing: 0.5px;
}

.item-rating.top {
  background: linear-gradient(135deg, #b45309, #d97706);
  color: var(--text-on-accent);
}

.item-rating.good {
  background: var(--success);
  color: var(--text-on-accent);
}

.item-rating.mid {
  background: rgba(59, 130, 246, 0.15);
  color: var(--info);
}

.item-score {
  font-size: var(--font-xs);
  color: var(--text-secondary);
  margin-left: auto;
}

.item-reason {
  margin: var(--space-xs) 0 0;
  font-size: var(--font-xs);
  color: var(--text-secondary);
  line-height: 1.5;
}

.item-times {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  margin-top: var(--space-xs);
}

.time-row {
  display: flex;
  align-items: baseline;
  gap: var(--space-sm);
  font-size: var(--font-xs);
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-xs);
}

.time-row.best {
  background: rgba(22, 163, 74, 0.08);
}

.time-row.avoid {
  background: rgba(234, 179, 8, 0.08);
}

.time-label {
  font-weight: 600;
  flex-shrink: 0;
  min-width: 60px;
}

.time-row.best .time-label { color: var(--success); }
.time-row.avoid .time-label { color: #b45309; }

.time-value {
  color: var(--text-secondary);
  line-height: 1.5;
}

.item-tip {
  margin: var(--space-xs) 0 0;
  font-size: var(--font-xs);
  color: var(--text-secondary);
  font-style: italic;
  line-height: 1.5;
}

/* 白話建議區塊 */
.advice-box {
  margin-top: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  background: rgba(139, 92, 246, 0.06);
  border-radius: var(--radius-sm);
  border-left: 3px solid #8B5CF6;
}

.advice-summary {
  margin: 0 0 var(--space-sm);
  font-size: var(--font-sm);
  color: var(--text-primary);
  line-height: 1.6;
}

.advice-list {
  display: flex;
  gap: var(--space-sm);
  margin-bottom: var(--space-xs);
}

.advice-label {
  font-size: var(--font-xs);
  font-weight: 700;
  padding: 1px 6px;
  border-radius: var(--radius-xs);
  flex-shrink: 0;
  line-height: 20px;
}

.do-list .advice-label {
  background: rgba(45, 122, 79, 0.15);
  color: var(--success);
}

.avoid-list .advice-label {
  background: rgba(197, 48, 48, 0.15);
  color: var(--rasetsu-color);
}

.advice-list ul {
  margin: 0;
  padding-left: 16px;
  font-size: var(--font-xs);
  color: var(--text-secondary);
  line-height: 1.6;
}

/* 響應式 - 小螢幕 */
@media (max-width: 479px) {
  .day-cell {
    min-height: 52px;
    padding: 2px 1px;
    gap: 2px;
  }

  .day-number {
    font-size: 12px;
  }

  .day-badge {
    font-size: 8px;
    padding: 0 3px;
    line-height: 12px;
  }

  .legend-badge {
    font-size: 9px;
    padding: 0 4px;
  }

  .expand-item {
    padding: var(--space-xs) var(--space-sm);
  }
}

/* 響應式 - 桌面 */
@media (min-width: 768px) {
  .day-cell {
    min-height: 80px;
    padding: 4px 3px;
  }

  .day-number {
    font-size: 16px;
  }

  .day-badge {
    font-size: 10px;
    padding: 1px 5px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .expand-panel {
    animation: none;
  }
}
</style>
