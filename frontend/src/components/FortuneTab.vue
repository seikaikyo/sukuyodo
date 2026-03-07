<script setup lang="ts">
import { ref, computed, watch } from 'vue'

import type { DailyFortune, WeeklyFortune, MonthlyFortune, YearlyFortune, Mansion } from '../composables/useSukuyodo'
import { getScoreClass, formatDate } from '../utils/fortune-helpers'
import { generateDecadeReport } from '../utils/report-generator'
import { generateIcsCalendar, downloadIcs } from '../utils/ics-generator'
import { apiFetch, getApiUrl } from '../config/api'
import { useProfile } from '../stores/profile'

const props = defineProps<{
  activeTab: 'daily' | 'weekly' | 'monthly' | 'yearly' | 'decade'
  dailyFortune: DailyFortune | null
  weeklyFortune: WeeklyFortune | null
  monthlyFortune: MonthlyFortune | null
  yearlyFortune: YearlyFortune | null
  yearlyRange: YearlyFortune[]
  yearlyRangeLoading: boolean
  expandedMonthlyWeek: number | null
  currentWeekNumber: number
  mansion: Mansion | null
  birthDate: string
  expandedYearlyMonth: number | null
  yearlyMonthDetail: MonthlyFortune | null
  yearlyMonthLoading: boolean
  expandedYearlyWeek: number | null
  fetchFullYearCalendar: (year: number) => Promise<any[]>
}>()

const emit = defineEmits<{
  'update:activeTab': [value: 'daily' | 'weekly' | 'monthly' | 'yearly' | 'decade']
  'toggleWeek': [week: number]
  'selectDay': [date: string]
  'fetchYearlyRange': [startYear: number, endYear: number]
  'navigate-knowledge': [tab: string]
  'toggleYearlyMonth': [month: number]
  'toggleYearlyWeek': [week: number]
}>()

const KUYOU_LEVEL_READING: Record<string, string> = {
  '大吉': 'だいきち',
  '半吉': 'はんきち',
  '末吉': 'すえきち',
  '大凶': 'だいきょう',
}

function getKuyouLevelClass(level: string) {
  if (level === '大吉') return 'level-great'
  if (level === '吉') return 'level-good'
  if (level === '半吉') return 'level-half'
  return 'level-bad'
}

function getPracticeLevelClass(level: string) {
  if (level === '弘法') return 'level-dharma'
  if (level === '增上') return 'level-growth'
  if (level === '調和') return 'level-harmony'
  return 'level-diligent'
}

// 修行者觀 / 世俗觀 切換（永遠預設世俗觀，使用者手動切換）
useProfile()
const decadePerspective = ref<'secular' | 'practitioner'>('secular')
const isPractitioner = computed(() => decadePerspective.value === 'practitioner')

// 特殊日修法指引（品第八, T21 p.398b-c）
const SPECIAL_DAY_PRACTICE: Record<string, string> = {
  kanro: '宜冊立、受灌頂法、造作寺宇及受戒、習學經法、出家修道，一切並吉',
  kongou: '宜作一切降伏法，誦日天子呪及作護摩，並諸猛利等事',
  rasetsu: '不宜舉百事，必有殃禍'
}

// 凌犯逆轉時追加引文（品第三, T21 p.391b-c）
const RYOUHAN_REVERSAL_PRACTICE: Record<string, string> = {
  kanro: '犯逼守命、胎之宿，此人是厄會之時也，宜修功德、持真言念誦、立道場以禳之',
  rasetsu: '若犯衰、危、壞等宿者，則所求稱意、百事通達'
}

// 三九法修行提示（卷下, T21 p.397c-398a）
// key 對應後端 SANKI_DAY_TYPES 的 name 欄位
const SANKI_PRACTICE: Record<string, string> = {
  '命の日': '不宜舉動百事',
  '胎の日': '不宜舉動百事',
  '栄の日': '出家人剃髮、割爪甲、沐浴、承事師主、啟請法要並吉',
  '安の日': '作壇場並吉',
  '成の日': '宜修道學問、合和長年藥法，作諸成就法並吉',
  '業の日': '所作善惡亦不成就，甚衰',
  '危の日': '宜結交、定婚姻，歡宴聚會並吉',
  '壊の日': '宜作鎮壓、降伏怨讎及討伐阻壞奸惡之謀，餘並不堪',
  '友の日': '宜結交、定婚姻，歡宴聚會並吉',
  '親の日': '宜結交、定婚姻，歡宴聚會並吉',
  '衰の日': '唯宜解除諸惡、療病'
}

// 流年相關
const currentYear = new Date().getFullYear()
const decadeStartYear = ref(currentYear - 2)
const expandedDecadeYear = ref<number | null>(null)

const decadeEndYear = computed(() => decadeStartYear.value + 9)

function loadDecade() {
  emit('fetchYearlyRange', decadeStartYear.value, decadeEndYear.value)
}

function prevDecade() {
  decadeStartYear.value -= 10
  expandedDecadeYear.value = null
  loadDecade()
}

function nextDecade() {
  decadeStartYear.value += 10
  expandedDecadeYear.value = null
  loadDecade()
}

function toggleDecadeYear(year: number) {
  expandedDecadeYear.value = expandedDecadeYear.value === year ? null : year
}

// 首次切到流年 tab 時自動載入
watch(() => props.activeTab, (tab) => {
  if (tab === 'decade' && props.yearlyRange.length === 0 && !props.yearlyRangeLoading) {
    loadDecade()
  }
})

// SVG 圖表計算
const svgWidth = 620
const svgHeight = 220
const padLeft = 55
const padRight = 35
const padTop = 25
const padBottom = 25
const chartWidth = svgWidth - padLeft - padRight
const chartHeight = svgHeight - padTop - padBottom
const minScore = 30
const maxScore = 100

function scoreToY(score: number): number {
  return padTop + chartHeight - ((score - minScore) / (maxScore - minScore)) * chartHeight
}

function yearToX(index: number): number {
  if (props.yearlyRange.length <= 1) return padLeft
  return padLeft + (index / (props.yearlyRange.length - 1)) * chartWidth
}

// 折線圖路徑
const overallPath = computed(() => {
  if (props.yearlyRange.length === 0) return ''
  return props.yearlyRange
    .map((y, i) => `${i === 0 ? 'M' : 'L'}${yearToX(i).toFixed(1)},${scoreToY(y.fortune.overall).toFixed(1)}`)
    .join(' ')
})

// Y 軸格線
const yGridLines = computed(() => {
  const lines = []
  for (let s = 40; s <= 100; s += 10) {
    lines.push({ score: s, y: scoreToY(s) })
  }
  return lines
})

// 短星名（2 字）
function shortStarName(name: string): string {
  if (name.length <= 2) return name
  return name.replace('曜星', '').replace('星', '')
}

// 本年月度折線圖計算
const currentMonth = new Date().getMonth() + 1

const monthlySvgWidth = 560
const monthlySvgHeight = 160
const monthlyPadLeft = 40
const monthlyPadRight = 20
const monthlyPadTop = 25
const monthlyPadBottom = 25
const monthlyChartWidth = monthlySvgWidth - monthlyPadLeft - monthlyPadRight
const monthlyChartHeight = monthlySvgHeight - monthlyPadTop - monthlyPadBottom

function monthScoreToY(score: number): number {
  return monthlyPadTop + monthlyChartHeight - ((score - minScore) / (maxScore - minScore)) * monthlyChartHeight
}

function monthToX(index: number): number {
  return monthlyPadLeft + (index / 11) * monthlyChartWidth
}

const monthlyTrendPath = computed(() => {
  const trend = props.yearlyFortune?.monthly_trend
  if (!trend || trend.length === 0) return ''
  return trend
    .map((m, i) => `${i === 0 ? 'M' : 'L'}${monthToX(i).toFixed(1)},${monthScoreToY(m.score).toFixed(1)}`)
    .join(' ')
})

const monthYGridLines = computed(() => {
  const lines = []
  for (let s = 40; s <= 100; s += 20) {
    lines.push({ score: s, y: monthScoreToY(s) })
  }
  return lines
})

function exportDecadeReport() {
  if (!props.mansion || props.yearlyRange.length === 0) return
  generateDecadeReport({
    yearlyRange: props.yearlyRange,
    mansionName: props.mansion.name_jp,
    mansionReading: props.mansion.reading,
    mansionElement: props.mansion.element,
    birthDate: props.birthDate,
    perspective: decadePerspective.value,
  })
}

const icsExporting = ref(false)

async function exportIcsCalendar() {
  if (!props.mansion || !props.birthDate || icsExporting.value) return
  const year = props.yearlyFortune?.year ?? new Date().getFullYear()

  icsExporting.value = true
  try {
    const calendars = await props.fetchFullYearCalendar(year)
    if (calendars.length === 0) {
      console.error('No calendar data available for ICS export')
      return
    }

    const icsContent = generateIcsCalendar({
      calendars,
      mansionName: props.mansion.name_jp,
      mansionElement: props.mansion.element,
      birthDate: props.birthDate,
      year,
    })

    if (icsContent) {
      const bd = props.birthDate.replace(/-/g, '')
      const filename = `sukuyodo_${year}_${props.mansion.name_jp}_${bd}.ics`
      downloadIcs(icsContent, filename)
    }
  } catch (e) {
    console.error('ICS export failed', e)
  } finally {
    icsExporting.value = false
  }
}

// ICS 日曆訂閱
const subscribeLoading = ref(false)
const subscribeDialogOpen = ref(false)
const subscribeUrls = ref<{ webcal_url: string; https_url: string; expires_at: string } | null>(null)
const subscribeCopied = ref(false)

async function openSubscribeDialog() {
  if (!props.birthDate || subscribeLoading.value) return
  const year = props.yearlyFortune?.year ?? new Date().getFullYear()

  subscribeLoading.value = true
  try {
    const res = await apiFetch(getApiUrl('/calendar/subscribe'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ birth_date: props.birthDate, year }),
    })
    if (!res.ok) throw new Error('subscribe failed')
    const json = await res.json()
    subscribeUrls.value = json.data
    subscribeDialogOpen.value = true
  } catch (e) {
    console.error('Subscribe failed', e)
  } finally {
    subscribeLoading.value = false
  }
}

function openWebcal() {
  if (subscribeUrls.value) {
    window.location.href = subscribeUrls.value.webcal_url
  }
}

async function copySubscribeUrl() {
  if (!subscribeUrls.value) return
  try {
    await navigator.clipboard.writeText(subscribeUrls.value.https_url)
    subscribeCopied.value = true
    setTimeout(() => { subscribeCopied.value = false }, 2000)
  } catch {
    // fallback
    const input = document.createElement('input')
    input.value = subscribeUrls.value.https_url
    document.body.appendChild(input)
    input.select()
    document.execCommand('copy')
    document.body.removeChild(input)
    subscribeCopied.value = true
    setTimeout(() => { subscribeCopied.value = false }, 2000)
  }
}
</script>

<template>
  <section class="fortune-tab">
    <div class="sub-tabs" role="tablist" aria-label="運勢週期選擇">
      <button
        class="pill-btn"
        :class="{ active: activeTab === 'daily' }"
        role="tab"
        :aria-selected="activeTab === 'daily'"
        aria-controls="panel-fortune-daily"
        @click="emit('update:activeTab', 'daily')"
      >今日</button>
      <button
        class="pill-btn"
        :class="{ active: activeTab === 'weekly' }"
        role="tab"
        :aria-selected="activeTab === 'weekly'"
        aria-controls="panel-fortune-weekly"
        @click="emit('update:activeTab', 'weekly')"
      >本週</button>
      <button
        class="pill-btn"
        :class="{ active: activeTab === 'monthly' }"
        role="tab"
        :aria-selected="activeTab === 'monthly'"
        aria-controls="panel-fortune-monthly"
        @click="emit('update:activeTab', 'monthly')"
      >本月</button>
      <button
        class="pill-btn"
        :class="{ active: activeTab === 'yearly' }"
        role="tab"
        :aria-selected="activeTab === 'yearly'"
        aria-controls="panel-fortune-yearly"
        @click="emit('update:activeTab', 'yearly')"
      >本年</button>
      <button
        class="pill-btn"
        :class="{ active: activeTab === 'decade' }"
        role="tab"
        :aria-selected="activeTab === 'decade'"
        aria-controls="panel-fortune-decade"
        @click="emit('update:activeTab', 'decade')"
      >流年</button>
    </div>

    <!-- Daily Fortune -->
    <div v-if="activeTab === 'daily'" id="panel-fortune-daily" class="fortune-content" role="tabpanel">
      <template v-if="dailyFortune">
        <div class="fortune-card">
          <h3 class="fortune-title">
            {{ dailyFortune.date }} {{ dailyFortune.weekday.name }}
            <span class="weekday-element">({{ dailyFortune.weekday.element }}曜)</span>
          </h3>

          <div class="score-bars">
            <div class="score-row overall-row">
              <span class="score-label">整體</span>
              <div class="score-bar">
                <div class="score-fill" :class="getScoreClass(dailyFortune.fortune.overall)" :style="{ width: dailyFortune.fortune.overall + '%' }"></div>
              </div>
              <span class="score-value" :class="getScoreClass(dailyFortune.fortune.overall)">{{ dailyFortune.fortune.overall }}</span>
            </div>
            <div class="score-group">
              <div class="score-row">
                <span class="score-label">事業</span>
                <div class="score-bar">
                  <div class="score-fill" :class="getScoreClass(dailyFortune.fortune.career)" :style="{ width: dailyFortune.fortune.career + '%' }"></div>
                </div>
                <span class="score-value">{{ dailyFortune.fortune.career }}</span>
              </div>
              <p v-if="dailyFortune.fortune.career_desc" class="score-desc">{{ dailyFortune.fortune.career_desc }}</p>
            </div>
            <div class="score-group">
              <div class="score-row">
                <span class="score-label">感情</span>
                <div class="score-bar">
                  <div class="score-fill" :class="getScoreClass(dailyFortune.fortune.love)" :style="{ width: dailyFortune.fortune.love + '%' }"></div>
                </div>
                <span class="score-value">{{ dailyFortune.fortune.love }}</span>
              </div>
              <p v-if="dailyFortune.fortune.love_desc" class="score-desc">{{ dailyFortune.fortune.love_desc }}</p>
            </div>
            <div class="score-group">
              <div class="score-row">
                <span class="score-label">健康</span>
                <div class="score-bar">
                  <div class="score-fill" :class="getScoreClass(dailyFortune.fortune.health)" :style="{ width: dailyFortune.fortune.health + '%' }"></div>
                </div>
                <span class="score-value">{{ dailyFortune.fortune.health }}</span>
              </div>
              <p v-if="dailyFortune.fortune.health_desc" class="score-desc">{{ dailyFortune.fortune.health_desc }}</p>
            </div>
            <div class="score-group">
              <div class="score-row">
                <span class="score-label">財運</span>
                <div class="score-bar">
                  <div class="score-fill" :class="getScoreClass(dailyFortune.fortune.wealth)" :style="{ width: dailyFortune.fortune.wealth + '%' }"></div>
                </div>
                <span class="score-value">{{ dailyFortune.fortune.wealth }}</span>
              </div>
              <p v-if="dailyFortune.fortune.wealth_desc" class="score-desc">{{ dailyFortune.fortune.wealth_desc }}</p>
            </div>
          </div>

          <div class="score-legend">
            <span class="legend-item"><span class="legend-dot excellent"></span>90+ <ruby>大吉<rp>(</rp><rt>だいきち</rt><rp>)</rp></ruby></span>
            <span class="legend-item"><span class="legend-dot good"></span>75+ <ruby>吉<rp>(</rp><rt>きち</rt><rp>)</rp></ruby></span>
            <span class="legend-item"><span class="legend-dot fair"></span>60+ <ruby>中吉<rp>(</rp><rt>ちゅうきち</rt><rp>)</rp></ruby></span>
            <span class="legend-item"><span class="legend-dot caution"></span>45+ <ruby>小凶<rp>(</rp><rt>しょうきょう</rt><rp>)</rp></ruby></span>
            <span class="legend-item"><span class="legend-dot warning"></span>&lt;45 <ruby>凶<rp>(</rp><rt>きょう</rt><rp>)</rp></ruby></span>
          </div>

          <div v-if="dailyFortune.compound_analysis?.length" class="compound-analysis">
            <div v-for="ca in dailyFortune.compound_analysis" :key="ca.pattern"
                 class="compound-item" :class="'severity-' + ca.severity">
              <span class="compound-label">{{ ca.name }}</span>
              <p class="compound-desc">{{ ca.description }}</p>
            </div>
          </div>

          <div v-if="dailyFortune.special_day" class="special-day-banner" :class="[dailyFortune.special_day.type, { reversed: dailyFortune.special_day.ryouhan_reversed }]">
            <span class="special-day-level">{{ dailyFortune.special_day.level }}</span>
            <span class="special-day-name term-link" @click="emit('navigate-knowledge', 'special-days')"><ruby v-if="dailyFortune.special_day.reading">{{ dailyFortune.special_day.name }}<rp>(</rp><rt>{{ dailyFortune.special_day.reading }}</rt><rp>)</rp></ruby><template v-else>{{ dailyFortune.special_day.name }}</template></span>
            <p class="special-day-desc">{{ dailyFortune.special_day.description }}</p>
            <p v-if="dailyFortune.special_day.ryouhan_reversed" class="special-day-reversed">
              凌犯期間，吉凶逆轉（凌犯期間中のため吉凶が逆轉しています）
            </p>
            <div v-if="isPractitioner && SPECIAL_DAY_PRACTICE[dailyFortune.special_day.type]" class="practice-scripture">
              <p class="scripture-text">{{ SPECIAL_DAY_PRACTICE[dailyFortune.special_day.type] }}</p>
              <span class="scripture-source">品第八, T21 p.398b-c</span>
            </div>
            <div v-if="isPractitioner && dailyFortune.special_day.ryouhan_reversed && RYOUHAN_REVERSAL_PRACTICE[dailyFortune.special_day.type]" class="practice-scripture ryouhan-scripture">
              <p class="scripture-text">{{ RYOUHAN_REVERSAL_PRACTICE[dailyFortune.special_day.type] }}</p>
              <span class="scripture-source">品第三, T21 p.391b-c</span>
            </div>
          </div>

          <div v-if="dailyFortune.ryouhan" class="ryouhan-banner">
            <span class="ryouhan-label term-link" @click="emit('navigate-knowledge', 'ryouhan')"><ruby v-if="dailyFortune.ryouhan.reading">{{ dailyFortune.ryouhan.period_label || '凌犯期間' }}<rp>(</rp><rt>{{ dailyFortune.ryouhan.reading }}</rt><rp>)</rp></ruby><template v-else>{{ dailyFortune.ryouhan.period_label || '凌犯期間' }}</template></span>
            <p class="ryouhan-desc">{{ dailyFortune.ryouhan.description }}</p>
            <p v-if="dailyFortune.fortune.ryouhan_warning" class="ryouhan-warning">{{ dailyFortune.fortune.ryouhan_warning }}</p>
            <span v-if="dailyFortune.ryouhan.source" class="ryouhan-source">{{ dailyFortune.ryouhan.source }}</span>
          </div>

          <div v-if="dailyFortune.rokugai" class="rokugai-banner">
            <span class="rokugai-label term-link" @click="emit('navigate-knowledge', 'relations')">六害宿「<ruby v-if="dailyFortune.rokugai.name_reading">{{ dailyFortune.rokugai.name }}<rp>(</rp><rt>{{ dailyFortune.rokugai.name_reading }}</rt><rp>)</rp></ruby><template v-else>{{ dailyFortune.rokugai.name }}</template>」</span>
            <p class="rokugai-desc">{{ dailyFortune.rokugai.description }}</p>
          </div>

          <div v-if="dailyFortune.sanki" class="sanki-box" :class="{ 'dark-week': dailyFortune.sanki.is_dark_week }">
            <div class="sanki-header">
              <span class="sanki-period term-link" :class="'sanki-' + dailyFortune.sanki.period_index" @click="emit('navigate-knowledge', 'sanki')">
                <ruby v-if="dailyFortune.sanki.period_reading">{{ dailyFortune.sanki.period }}<rp>(</rp><rt>{{ dailyFortune.sanki.period_reading }}</rt><rp>)</rp></ruby>
                <template v-else>{{ dailyFortune.sanki.period }}</template>
              </span>
              <span class="sanki-day-type">
                <ruby v-if="dailyFortune.sanki.day_type_reading">{{ dailyFortune.sanki.day_type }}<rp>(</rp><rt>{{ dailyFortune.sanki.day_type_reading }}</rt><rp>)</rp></ruby>
                <template v-else>{{ dailyFortune.sanki.day_type }}</template>
              </span>
              <span v-if="dailyFortune.sanki.is_dark_week" class="dark-week-label"><ruby>暗黒の一週間<rp>(</rp><rt>あんこくのいっしゅうかん</rt><rp>)</rp></ruby></span>
            </div>
            <p class="sanki-day-desc">{{ dailyFortune.sanki.day_description }}</p>
            <p class="sanki-period-desc">{{ dailyFortune.sanki.period_description }}</p>
            <div v-if="isPractitioner && SANKI_PRACTICE[dailyFortune.sanki.day_type]" class="practice-scripture sanki-scripture">
              <p class="scripture-text">{{ SANKI_PRACTICE[dailyFortune.sanki.day_type] }}</p>
              <span class="scripture-source">卷下, T21 p.397c-398a</span>
            </div>
          </div>

          <div class="lucky-info">
            <div class="lucky-item">
              <span class="lucky-label">幸運色</span>
              <span class="lucky-value">
                <span class="color-dot" :style="{ background: dailyFortune.lucky.color_hex }"></span>
                <ruby v-if="dailyFortune.lucky.color_reading">{{ dailyFortune.lucky.color }}<rp>(</rp><rt>{{ dailyFortune.lucky.color_reading }}</rt><rp>)</rp></ruby>
                <template v-else>{{ dailyFortune.lucky.color }}</template>
              </span>
            </div>
            <div class="lucky-item">
              <span class="lucky-label">幸運方位</span>
              <span class="lucky-value">
                <ruby v-if="dailyFortune.lucky.direction_reading">{{ dailyFortune.lucky.direction }}<rp>(</rp><rt>{{ dailyFortune.lucky.direction_reading }}</rt><rp>)</rp></ruby>
                <template v-else>{{ dailyFortune.lucky.direction }}</template>
              </span>
            </div>
            <div class="lucky-item">
              <span class="lucky-label">幸運數字</span>
              <span class="lucky-value">{{ dailyFortune.lucky.numbers.join(', ') }}</span>
            </div>
          </div>

          <div class="mansion-hint">
            <h4>
              今日宿曜提示
              <span class="hint-relation term-link" :class="dailyFortune.mansion_relation.type" @click="emit('navigate-knowledge', 'relations')">{{ dailyFortune.mansion_relation.name_jp || dailyFortune.mansion_relation.name }}</span>
            </h4>
            <p class="hint-mansions">
              本命宿 <strong>{{ dailyFortune.your_mansion.name_jp }}</strong>（{{ dailyFortune.your_mansion.element }}）
              ／當日宿 <strong>{{ dailyFortune.day_mansion.name_jp }}</strong>（{{ dailyFortune.day_mansion.element }}）
            </p>
            <p>{{ dailyFortune.mansion_relation.description }}</p>
            <p v-if="dailyFortune.element_relation" class="hint-element">
              {{ dailyFortune.element_relation.description }}
            </p>
          </div>

          <div v-if="dailyFortune.day_mansion?.day_fortune" class="day-fortune-box" :class="{ 'most-auspicious': dailyFortune.day_mansion.day_fortune.is_most_auspicious }">
            <h4>
              {{ dailyFortune.day_mansion.name_jp }}日 行事宜忌
              <span v-if="dailyFortune.day_mansion.day_fortune.is_most_auspicious" class="best-day-badge">最吉日</span>
            </h4>
            <div class="day-fortune-tags">
              <span v-for="item in dailyFortune.day_mansion.day_fortune.auspicious" :key="'a-'+item" class="day-tag auspicious">{{ item }}</span>
              <span v-for="item in dailyFortune.day_mansion.day_fortune.inauspicious" :key="'i-'+item" class="day-tag inauspicious">{{ item }}</span>
            </div>
            <p class="day-fortune-classic">{{ dailyFortune.day_mansion.day_fortune.summary_classic }}</p>
            <p class="day-fortune-ja">{{ dailyFortune.day_mansion.day_fortune.summary_ja }}</p>
            <p class="day-fortune-zh">{{ dailyFortune.day_mansion.day_fortune.summary }}</p>
            <p class="day-fortune-source">出典：宿曜經卷下「二十八宿行事吉凶」</p>
          </div>

          <div class="advice-box" style="margin-top: var(--space-md)">
            <h4>今日建議</h4>
            <p>{{ dailyFortune.advice }}</p>
          </div>
        </div>
      </template>
      <div v-else class="loading-state">
        <sl-spinner></sl-spinner>
      </div>
    </div>

    <!-- Weekly Fortune -->
    <div v-if="activeTab === 'weekly'" id="panel-fortune-weekly" class="fortune-content" role="tabpanel">
      <template v-if="weeklyFortune">
        <div class="fortune-card">
          <h3 class="fortune-title">
            本週運勢
            <span class="date-range">({{ formatDate(weeklyFortune.week_start) }} ~ {{ formatDate(weeklyFortune.week_end) }})</span>
          </h3>

          <div class="score-bars">
            <div class="score-row">
              <span class="score-label">整體</span>
              <div class="score-bar">
                <div class="score-fill" :class="getScoreClass(weeklyFortune.fortune.overall)" :style="{ width: weeklyFortune.fortune.overall + '%' }"></div>
              </div>
              <span class="score-value">{{ weeklyFortune.fortune.overall }}</span>
            </div>
            <div class="score-row">
              <span class="score-label">事業</span>
              <div class="score-bar">
                <div class="score-fill" :class="getScoreClass(weeklyFortune.fortune.career)" :style="{ width: weeklyFortune.fortune.career + '%' }"></div>
              </div>
              <span class="score-value">{{ weeklyFortune.fortune.career }}</span>
            </div>
            <div class="score-row">
              <span class="score-label">感情</span>
              <div class="score-bar">
                <div class="score-fill" :class="getScoreClass(weeklyFortune.fortune.love)" :style="{ width: weeklyFortune.fortune.love + '%' }"></div>
              </div>
              <span class="score-value">{{ weeklyFortune.fortune.love }}</span>
            </div>
            <div class="score-row">
              <span class="score-label">健康</span>
              <div class="score-bar">
                <div class="score-fill" :class="getScoreClass(weeklyFortune.fortune.health)" :style="{ width: weeklyFortune.fortune.health + '%' }"></div>
              </div>
              <span class="score-value">{{ weeklyFortune.fortune.health }}</span>
            </div>
            <div class="score-row">
              <span class="score-label">財運</span>
              <div class="score-bar">
                <div class="score-fill" :class="getScoreClass(weeklyFortune.fortune.wealth)" :style="{ width: weeklyFortune.fortune.wealth + '%' }"></div>
              </div>
              <span class="score-value">{{ weeklyFortune.fortune.wealth }}</span>
            </div>
          </div>

          <div class="score-legend">
            <span class="legend-item"><span class="legend-dot excellent"></span>90+ <ruby>大吉<rp>(</rp><rt>だいきち</rt><rp>)</rp></ruby></span>
            <span class="legend-item"><span class="legend-dot good"></span>75+ <ruby>吉<rp>(</rp><rt>きち</rt><rp>)</rp></ruby></span>
            <span class="legend-item"><span class="legend-dot fair"></span>60+ <ruby>中吉<rp>(</rp><rt>ちゅうきち</rt><rp>)</rp></ruby></span>
            <span class="legend-item"><span class="legend-dot caution"></span>45+ <ruby>小凶<rp>(</rp><rt>しょうきょう</rt><rp>)</rp></ruby></span>
            <span class="legend-item"><span class="legend-dot warning"></span>&lt;45 <ruby>凶<rp>(</rp><rt>きょう</rt><rp>)</rp></ruby></span>
          </div>

          <div v-if="weeklyFortune.lucky" class="lucky-info">
            <div class="lucky-item">
              <span class="lucky-label">幸運色</span>
              <span class="lucky-value">
                <span class="color-dot" :style="{ background: weeklyFortune.lucky.color_hex }"></span>
                <ruby v-if="weeklyFortune.lucky.color_reading">{{ weeklyFortune.lucky.color }}<rp>(</rp><rt>{{ weeklyFortune.lucky.color_reading }}</rt><rp>)</rp></ruby>
                <template v-else>{{ weeklyFortune.lucky.color }}</template>
              </span>
            </div>
            <div class="lucky-item">
              <span class="lucky-label">幸運方位</span>
              <span class="lucky-value">
                <ruby v-if="weeklyFortune.lucky.direction_reading">{{ weeklyFortune.lucky.direction }}<rp>(</rp><rt>{{ weeklyFortune.lucky.direction_reading }}</rt><rp>)</rp></ruby>
                <template v-else>{{ weeklyFortune.lucky.direction }}</template>
              </span>
            </div>
          </div>

          <div v-if="weeklyFortune.focus" class="weekly-focus">
            <h4>本週焦點</h4>
            <p>{{ weeklyFortune.focus }}</p>
          </div>

          <div v-if="weeklyFortune.category_tips" class="category-descriptions">
            <div v-if="weeklyFortune.category_tips.career" class="category-desc-item">
              <h4>事業</h4>
              <p>{{ weeklyFortune.category_tips.career }}</p>
            </div>
            <div v-if="weeklyFortune.category_tips.love" class="category-desc-item">
              <h4>感情</h4>
              <p>{{ weeklyFortune.category_tips.love }}</p>
            </div>
            <div v-if="weeklyFortune.category_tips.health" class="category-desc-item">
              <h4>健康</h4>
              <p>{{ weeklyFortune.category_tips.health }}</p>
            </div>
          </div>

          <div class="daily-overview">
            <h4>每日概覽（點擊查看詳情）</h4>
            <div class="daily-list">
              <button
                v-for="day in weeklyFortune.daily_overview"
                :key="day.date"
                class="daily-item"
                :class="[getScoreClass(day.score), { 'is-today': day.is_today, 'is-yesterday': day.is_yesterday, 'chip-ryouhan': day.ryouhan_active, 'chip-dark-week': day.is_dark_week }]"
                :aria-label="`查看 ${formatDate(day.date)} ${day.weekday} 詳細運勢`"
                @click="emit('selectDay', day.date)"
              >
                <span class="day-label" v-if="day.is_today">今日</span>
                <span class="day-label yesterday" v-else-if="day.is_yesterday">昨日</span>
                <span class="day-date">{{ formatDate(day.date) }}</span>
                <span class="day-weekday">{{ day.weekday }}</span>
                <span class="day-score">{{ day.score }}</span>
                <span v-if="day.special_day" class="day-special">{{ day.special_day.charAt(0) }}</span>
              </button>
            </div>
          </div>

          <div v-if="weeklyFortune.week_warnings?.length" class="week-alerts">
            <p v-for="w in weeklyFortune.week_warnings" :key="w" class="week-warning-item">{{ w }}</p>
          </div>

          <div class="advice-box">
            <h4>本週建議</h4>
            <p>{{ weeklyFortune.advice }}</p>
          </div>
        </div>
      </template>
      <div v-else class="loading-state">
        <sl-spinner></sl-spinner>
      </div>
    </div>

    <!-- Monthly Fortune -->
    <div v-if="activeTab === 'monthly'" id="panel-fortune-monthly" class="fortune-content" role="tabpanel">
      <template v-if="monthlyFortune">
        <div class="fortune-card">
          <h3 class="fortune-title">
            {{ monthlyFortune.year }} 年 {{ monthlyFortune.month }} 月
          </h3>

          <div v-if="monthlyFortune.month_mansion || monthlyFortune.lunar_month" class="month-mansion-info">
            <span v-if="monthlyFortune.lunar_month" class="lunar-month">農曆{{ monthlyFortune.lunar_month }}月</span>
            <span v-if="monthlyFortune.month_mansion" class="month-mansion">
              當月宿：<strong>{{ monthlyFortune.month_mansion.name_jp }}</strong>（{{ monthlyFortune.month_mansion.element }}）
            </span>
            <span v-if="monthlyFortune.relation" class="month-relation hint-relation term-link" :class="monthlyFortune.relation.type" @click="emit('navigate-knowledge', 'relations')">
              <ruby v-if="monthlyFortune.relation.reading">{{ monthlyFortune.relation.name_jp || monthlyFortune.relation.name }}<rp>(</rp><rt>{{ monthlyFortune.relation.reading }}</rt><rp>)</rp></ruby>
              <template v-else>{{ monthlyFortune.relation.name_jp || monthlyFortune.relation.name }}</template>
            </span>
          </div>
          <p v-if="monthlyFortune.relation?.description" class="month-relation-desc">{{ monthlyFortune.relation.description }}</p>

          <div v-if="monthlyFortune.month_warnings?.length || monthlyFortune.ryouhan_info" class="month-alerts">
            <div v-if="monthlyFortune.ryouhan_info" class="ryouhan-month-info">
              本月 {{ monthlyFortune.ryouhan_info.affected_days }} / {{ monthlyFortune.ryouhan_info.total_days }} 天處於凌犯期間
            </div>
            <p v-for="w in monthlyFortune.month_warnings" :key="w" class="month-warning-item">{{ w }}</p>
          </div>

          <div v-if="monthlyFortune.theme" class="theme-box">
            <h4>{{ monthlyFortune.theme.title }}</h4>
            <p class="theme-focus">{{ monthlyFortune.theme.focus }}</p>
            <p v-if="monthlyFortune.theme.description" class="theme-desc">{{ monthlyFortune.theme.description }}</p>
          </div>

          <div class="score-bars">
            <div class="score-row">
              <span class="score-label">整體</span>
              <div class="score-bar">
                <div class="score-fill" :class="getScoreClass(monthlyFortune.fortune.overall)" :style="{ width: monthlyFortune.fortune.overall + '%' }"></div>
              </div>
              <span class="score-value">{{ monthlyFortune.fortune.overall }}</span>
            </div>
            <div class="score-row">
              <span class="score-label">事業</span>
              <div class="score-bar">
                <div class="score-fill" :class="getScoreClass(monthlyFortune.fortune.career)" :style="{ width: monthlyFortune.fortune.career + '%' }"></div>
              </div>
              <span class="score-value">{{ monthlyFortune.fortune.career }}</span>
            </div>
            <div class="score-row">
              <span class="score-label">感情</span>
              <div class="score-bar">
                <div class="score-fill" :class="getScoreClass(monthlyFortune.fortune.love)" :style="{ width: monthlyFortune.fortune.love + '%' }"></div>
              </div>
              <span class="score-value">{{ monthlyFortune.fortune.love }}</span>
            </div>
            <div class="score-row">
              <span class="score-label">健康</span>
              <div class="score-bar">
                <div class="score-fill" :class="getScoreClass(monthlyFortune.fortune.health)" :style="{ width: monthlyFortune.fortune.health + '%' }"></div>
              </div>
              <span class="score-value">{{ monthlyFortune.fortune.health }}</span>
            </div>
            <div class="score-row">
              <span class="score-label">財運</span>
              <div class="score-bar">
                <div class="score-fill" :class="getScoreClass(monthlyFortune.fortune.wealth)" :style="{ width: monthlyFortune.fortune.wealth + '%' }"></div>
              </div>
              <span class="score-value">{{ monthlyFortune.fortune.wealth }}</span>
            </div>
          </div>

          <div class="score-legend">
            <span class="legend-item"><span class="legend-dot excellent"></span>90+ <ruby>大吉<rp>(</rp><rt>だいきち</rt><rp>)</rp></ruby></span>
            <span class="legend-item"><span class="legend-dot good"></span>75+ <ruby>吉<rp>(</rp><rt>きち</rt><rp>)</rp></ruby></span>
            <span class="legend-item"><span class="legend-dot fair"></span>60+ <ruby>中吉<rp>(</rp><rt>ちゅうきち</rt><rp>)</rp></ruby></span>
            <span class="legend-item"><span class="legend-dot caution"></span>45+ <ruby>小凶<rp>(</rp><rt>しょうきょう</rt><rp>)</rp></ruby></span>
            <span class="legend-item"><span class="legend-dot warning"></span>&lt;45 <ruby>凶<rp>(</rp><rt>きょう</rt><rp>)</rp></ruby></span>
          </div>

          <!-- 本月策略 -->
          <div v-if="monthlyFortune.strategy" class="strategy-section monthly-strategy">
            <h4 class="strategy-title">本月策略</h4>

            <!-- 最佳行動區間 -->
            <div v-if="monthlyFortune.strategy.action_windows.length" class="strategy-block best-block">
              <div class="strategy-block-header">
                <span class="strategy-icon best-icon">&#9679;</span>
                <span class="strategy-label">行動區間</span>
              </div>
              <div v-for="(w, i) in monthlyFortune.strategy.action_windows" :key="i" class="strategy-item">
                <span class="strategy-months safe-tag">{{ formatDate(w.start_date) }}~{{ formatDate(w.end_date) }}</span>
                <span class="strategy-avg">{{ w.days }}天 均分{{ w.avg_score }}</span>
              </div>
            </div>

            <!-- 最佳日 + 迴避日 -->
            <div class="strategy-days-row">
              <div v-if="monthlyFortune.strategy.best_days.length" class="strategy-days-col">
                <span class="strategy-label best-label">推薦日</span>
                <div class="strategy-day-tags">
                  <span
                    v-for="d in monthlyFortune.strategy.best_days"
                    :key="d.date"
                    class="strategy-day-tag best-day-tag"
                    :title="d.reason"
                  >{{ formatDate(d.date) }} {{ d.weekday?.replace('曜日', '') }} {{ d.score }}</span>
                </div>
              </div>
              <div v-if="monthlyFortune.strategy.avoid_days.length" class="strategy-days-col">
                <span class="strategy-label caution-label">迴避日</span>
                <div class="strategy-day-tags">
                  <span
                    v-for="d in monthlyFortune.strategy.avoid_days"
                    :key="d.date"
                    class="strategy-day-tag avoid-day-tag"
                    :title="d.reasons?.join('、')"
                  >{{ formatDate(d.date) }} {{ d.weekday?.replace('曜日', '') }} {{ d.score }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="weekly-overview">
            <h4>三期概覽</h4>
            <div class="weekly-list">
              <div
                v-for="w in monthlyFortune.weekly"
                :key="w.week"
                class="weekly-item-wrapper"
              >
                <button
                  class="weekly-item"
                  :class="{ expanded: expandedMonthlyWeek === w.week, 'has-dark': w.has_dark_week }"
                  :aria-expanded="expandedMonthlyWeek === w.week"
                  :aria-controls="`week-detail-${w.week}`"
                  @click="emit('toggleWeek', w.week)"
                  @keydown.enter="emit('toggleWeek', w.week)"
                  @keydown.space.prevent="emit('toggleWeek', w.week)"
                >
                  <span class="week-toggle" aria-hidden="true">{{ expandedMonthlyWeek === w.week ? '▼' : '▶' }}</span>
                  <span class="week-num"><ruby>{{ w.period_name }}<rp>(</rp><rt>{{ w.period_reading }}</rt><rp>)</rp></ruby></span>
                  <span class="week-days-count">{{ w.days_count }}日</span>
                  <span v-if="w.week === currentWeekNumber" class="week-current-tag">本期</span>
                  <div class="week-bar">
                    <div class="week-fill" :class="getScoreClass(w.score)" :style="{ width: w.score + '%' }"></div>
                  </div>
                  <span class="week-score">{{ w.score }}</span>
                </button>

                <!-- 展開的週詳細內容 -->
                <div
                  v-if="expandedMonthlyWeek === w.week"
                  :id="`week-detail-${w.week}`"
                  class="week-detail"
                >
                  <div class="week-detail-content">
                    <div class="week-date-range">
                      {{ formatDate(w.week_start) }} ~ {{ formatDate(w.week_end) }}
                    </div>

                    <div v-if="w.warnings?.length" class="week-alerts">
                      <p v-for="ww in w.warnings" :key="ww" class="week-warning-item">{{ ww }}</p>
                    </div>

                    <div class="week-detail-daily">
                      <span class="daily-label">每日：</span>
                      <div class="daily-chips">
                        <button
                          v-for="day in w.daily_overview"
                          :key="day.date"
                          class="daily-chip clickable"
                          :class="[getScoreClass(day.score), { 'chip-ryouhan': day.ryouhan_active, 'chip-dark-week': day.is_dark_week }]"
                          :aria-label="`${formatDate(day.date)} ${day.weekday} ${day.sanki_day_type || ''} 運勢 ${day.score} 分，點擊查看詳情`"
                          @click="emit('selectDay', day.date)"
                        >
                          {{ formatDate(day.date) }} {{ day.weekday?.replace('曜日', '') }} {{ day.score }}
                          <span v-if="day.sanki_day_type" class="day-type">{{ day.sanki_day_type.replace('の日', '') }}</span>
                          <span v-if="day.special_day" class="day-special">{{ day.special_day.charAt(0) }}</span>
                        </button>
                      </div>
                    </div>

                    <div class="week-detail-focus">
                      <span class="focus-label">重點：</span>
                      <span class="focus-text">{{ w.focus }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="advice-box">
            <h4>本月建議</h4>
            <p>{{ monthlyFortune.advice }}</p>
          </div>
        </div>
      </template>
      <div v-else class="loading-state">
        <sl-spinner></sl-spinner>
      </div>
    </div>

    <!-- Yearly Fortune (本年) -->
    <div v-if="activeTab === 'yearly'" id="panel-fortune-yearly" class="fortune-content" role="tabpanel">
      <template v-if="yearlyFortune">
        <div class="fortune-card">
          <!-- 當年九曜星摘要 -->
          <h3 class="fortune-title">{{ yearlyFortune.year }} 年運勢</h3>

          <!-- 視角切換 -->
          <div class="perspective-toggle" role="radiogroup" aria-label="觀點切換">
            <button
              class="perspective-btn"
              :class="{ active: decadePerspective === 'secular' }"
              role="radio"
              :aria-checked="decadePerspective === 'secular'"
              @click="decadePerspective = 'secular'"
            >世俗觀</button>
            <button
              class="perspective-btn"
              :class="{ active: decadePerspective === 'practitioner' }"
              role="radio"
              :aria-checked="decadePerspective === 'practitioner'"
              @click="decadePerspective = 'practitioner'"
            >修行者觀</button>
            <button
              v-if="birthDate"
              class="export-btn"
              :disabled="icsExporting"
              @click="exportIcsCalendar"
            >{{ icsExporting ? '匯出中...' : '匯出日曆' }}</button>
            <button
              v-if="birthDate"
              class="export-btn subscribe-btn"
              :disabled="subscribeLoading"
              @click="openSubscribeDialog"
            >{{ subscribeLoading ? '處理中...' : '訂閱日曆' }}</button>
          </div>

          <div v-if="yearlyFortune.kuyou_star" class="current-year-kuyou">
            <span class="kuyou-name term-link" @click="emit('navigate-knowledge', 'kuyou')"><ruby v-if="yearlyFortune.kuyou_star.reading">{{ yearlyFortune.kuyou_star.name }}<rp>(</rp><rt>{{ yearlyFortune.kuyou_star.reading }}</rt><rp>)</rp></ruby><template v-else>{{ yearlyFortune.kuyou_star.name }}</template></span>
            <template v-if="isPractitioner && yearlyFortune.shingon">
              <span class="practice-level" :class="getPracticeLevelClass(yearlyFortune.shingon.practice_level)">{{ yearlyFortune.shingon.practice_name }}</span>
            </template>
            <template v-else>
              <span class="kuyou-level" :class="getKuyouLevelClass(yearlyFortune.kuyou_star.level)"><ruby v-if="KUYOU_LEVEL_READING[yearlyFortune.kuyou_star.level]">{{ yearlyFortune.kuyou_star.level }}<rp>(</rp><rt>{{ KUYOU_LEVEL_READING[yearlyFortune.kuyou_star.level] }}</rt><rp>)</rp></ruby><template v-else>{{ yearlyFortune.kuyou_star.level }}</template></span>
            </template>
            <span class="current-year-score" :class="getScoreClass(yearlyFortune.fortune.overall)">{{ yearlyFortune.fortune.overall }}</span>
          </div>
          <p v-if="yearlyFortune.kuyou_star" class="current-year-desc">
            {{ isPractitioner && yearlyFortune.shingon ? yearlyFortune.shingon.description : yearlyFortune.kuyou_star.description }}
          </p>
          <div class="current-year-scores" style="margin-bottom: var(--space-md)">
            <div class="mini-score-item">
              <span class="mini-label">{{ isPractitioner && yearlyFortune.shingon ? yearlyFortune.shingon.category_labels.career : '事業' }}</span>
              <span class="mini-value" :class="getScoreClass(yearlyFortune.fortune.career)">{{ yearlyFortune.fortune.career }}</span>
            </div>
            <div class="mini-score-item">
              <span class="mini-label">{{ isPractitioner && yearlyFortune.shingon ? yearlyFortune.shingon.category_labels.love : '感情' }}</span>
              <span class="mini-value" :class="getScoreClass(yearlyFortune.fortune.love)">{{ yearlyFortune.fortune.love }}</span>
            </div>
            <div class="mini-score-item">
              <span class="mini-label">{{ isPractitioner && yearlyFortune.shingon ? yearlyFortune.shingon.category_labels.health : '健康' }}</span>
              <span class="mini-value" :class="getScoreClass(yearlyFortune.fortune.health)">{{ yearlyFortune.fortune.health }}</span>
            </div>
            <div class="mini-score-item">
              <span class="mini-label">{{ isPractitioner && yearlyFortune.shingon ? yearlyFortune.shingon.category_labels.wealth : '財運' }}</span>
              <span class="mini-value" :class="getScoreClass(yearlyFortune.fortune.wealth)">{{ yearlyFortune.fortune.wealth }}</span>
            </div>
          </div>

          <!-- 修行者觀：詳細修行資訊 -->
          <template v-if="isPractitioner && yearlyFortune.shingon">
            <div class="shingon-mantra-box">
              <div class="mantra-bija-section">
                <span v-if="yearlyFortune.shingon.mantra.siddham_unicode" class="bija-siddham">{{ yearlyFortune.shingon.mantra.siddham_unicode }}</span>
                <span v-if="yearlyFortune.shingon.mantra.siddham_roman" class="bija-iast">{{ yearlyFortune.shingon.mantra.siddham_roman }}</span>
                <span class="bija-buddha">{{ yearlyFortune.shingon.mantra.buddha }}</span>
              </div>
              <div class="mantra-text-section">
                <p class="mantra-label">真言</p>
                <p class="mantra-text">{{ yearlyFortune.shingon.mantra.text }}</p>
                <p class="mantra-reading">{{ yearlyFortune.shingon.mantra.reading }}</p>
              </div>
            </div>
            <div class="shingon-homa-box">
              <span class="homa-type">{{ yearlyFortune.shingon.homa_type }}</span>
              <span class="homa-desc">{{ yearlyFortune.shingon.homa_description }}</span>
            </div>
            <p class="practice-focus-text">修行重心：{{ yearlyFortune.shingon.practice_focus }}</p>
            <div v-if="yearlyFortune.shingon.theme" class="card-theme">
              <strong>{{ yearlyFortune.shingon.theme.title }}</strong>
              <p>{{ yearlyFortune.shingon.theme.description }}</p>
            </div>
            <div v-if="yearlyFortune.shingon.core_teaching" class="core-teaching-box">
              <p>{{ yearlyFortune.shingon.core_teaching }}</p>
            </div>
            <div v-if="yearlyFortune.shingon.recommended_practices?.length" class="recommended-practices">
              <h5>推薦修法</h5>
              <div class="practice-tags">
                <span v-for="(p, i) in yearlyFortune.shingon.recommended_practices" :key="i" class="practice-tag">{{ p }}</span>
              </div>
            </div>
            <div v-if="yearlyFortune.shingon.category_practice" class="category-descriptions">
              <div v-if="yearlyFortune.shingon.category_practice.career" class="category-desc-item">
                <h4>{{ yearlyFortune.shingon.category_labels.career }}</h4>
                <p>{{ yearlyFortune.shingon.category_practice.career }}</p>
              </div>
              <div v-if="yearlyFortune.shingon.category_practice.love" class="category-desc-item">
                <h4>{{ yearlyFortune.shingon.category_labels.love }}</h4>
                <p>{{ yearlyFortune.shingon.category_practice.love }}</p>
              </div>
              <div v-if="yearlyFortune.shingon.category_practice.health" class="category-desc-item">
                <h4>{{ yearlyFortune.shingon.category_labels.health }}</h4>
                <p>{{ yearlyFortune.shingon.category_practice.health }}</p>
              </div>
              <div v-if="yearlyFortune.shingon.category_practice.wealth" class="category-desc-item">
                <h4>{{ yearlyFortune.shingon.category_labels.wealth }}</h4>
                <p>{{ yearlyFortune.shingon.category_practice.wealth }}</p>
              </div>
            </div>
            <div v-if="yearlyFortune.shingon.opportunities?.length" class="opportunities">
              <h4>修行好時機</h4>
              <ul>
                <li v-for="(opp, i) in yearlyFortune.shingon.opportunities" :key="i">{{ opp }}</li>
              </ul>
            </div>
            <div v-if="yearlyFortune.shingon.warnings?.length" class="warnings">
              <h4>修行注意事項</h4>
              <ul>
                <li v-for="(warn, i) in yearlyFortune.shingon.warnings" :key="i">{{ warn }}</li>
              </ul>
            </div>
            <p v-if="yearlyFortune.shingon.advice" class="card-advice">{{ yearlyFortune.shingon.advice }}</p>
          </template>

          <!-- 各月運勢卡片（可展開） -->
          <h4 class="monthly-section-title">各月運勢</h4>
          <div v-if="yearlyFortune.monthly_trend?.length" class="monthly-card-list">
            <div
              v-for="m in yearlyFortune.monthly_trend"
              :key="m.month"
              class="monthly-card-wrapper"
            >
              <button
                class="monthly-card"
                :class="{
                  'is-current-month': m.month === currentMonth,
                  'expanded': expandedYearlyMonth === m.month
                }"
                :aria-expanded="expandedYearlyMonth === m.month"
                :aria-controls="`yearly-month-detail-${m.month}`"
                @click="emit('toggleYearlyMonth', m.month)"
              >
                <span class="monthly-card-toggle" aria-hidden="true">{{ expandedYearlyMonth === m.month ? '▼' : '▶' }}</span>
                <span class="monthly-month">{{ m.month }}月</span>
                <div class="monthly-bar-wrapper">
                  <div class="monthly-bar-fill" :class="getScoreClass(m.score)" :style="{ width: m.score + '%' }"></div>
                </div>
                <span class="monthly-score" :class="getScoreClass(m.score)">{{ m.score }}</span>
                <span v-if="m.special_day_counts" class="monthly-special-days">
                  <span v-if="m.special_day_counts.kanro" class="sd-badge kanro" :title="`甘露日 ${m.special_day_counts.kanro} 日`">甘{{ m.special_day_counts.kanro }}</span>
                  <span v-if="m.special_day_counts.kongou" class="sd-badge kongou" :title="`金剛峯日 ${m.special_day_counts.kongou} 日`">金{{ m.special_day_counts.kongou }}</span>
                  <span v-if="m.special_day_counts.rasetsu" class="sd-badge rasetsu" :title="`羅刹日 ${m.special_day_counts.rasetsu} 日`">羅{{ m.special_day_counts.rasetsu }}</span>
                </span>
                <p v-if="m.tip" class="monthly-tip">{{ m.tip }}</p>
              </button>

              <!-- 展開的月份詳細：週次 + 每日 -->
              <div
                v-if="expandedYearlyMonth === m.month"
                :id="`yearly-month-detail-${m.month}`"
                class="monthly-card-detail"
              >
                <div v-if="yearlyMonthLoading" class="week-detail-loading">
                  <sl-spinner></sl-spinner>
                </div>
                <template v-else-if="yearlyMonthDetail">
                  <div class="weekly-list">
                    <div
                      v-for="w in yearlyMonthDetail.weekly"
                      :key="w.week"
                      class="weekly-item-wrapper"
                    >
                      <button
                        class="weekly-item"
                        :class="{ expanded: expandedYearlyWeek === w.week, 'has-dark': w.has_dark_week }"
                        :aria-expanded="expandedYearlyWeek === w.week"
                        :aria-controls="`yearly-week-detail-${m.month}-${w.week}`"
                        @click.stop="emit('toggleYearlyWeek', w.week)"
                      >
                        <span class="week-toggle" aria-hidden="true">{{ expandedYearlyWeek === w.week ? '▼' : '▶' }}</span>
                        <span class="week-num"><ruby>{{ w.period_name }}<rp>(</rp><rt>{{ w.period_reading }}</rt><rp>)</rp></ruby></span>
                        <span class="week-days-count">{{ w.days_count }}日</span>
                        <span v-if="m.month === currentMonth && w.week === currentWeekNumber" class="week-current-tag">本期</span>
                        <div class="week-bar">
                          <div class="week-fill" :class="getScoreClass(w.score)" :style="{ width: w.score + '%' }"></div>
                        </div>
                        <span class="week-score">{{ w.score }}</span>
                      </button>

                      <div
                        v-if="expandedYearlyWeek === w.week"
                        :id="`yearly-week-detail-${m.month}-${w.week}`"
                        class="week-detail"
                      >
                        <div class="week-detail-content">
                          <div class="week-date-range">
                            {{ formatDate(w.week_start) }} ~ {{ formatDate(w.week_end) }}
                          </div>
                          <div class="week-detail-daily">
                            <span class="daily-label">每日：</span>
                            <div class="daily-chips">
                              <button
                                v-for="day in w.daily_overview"
                                :key="day.date"
                                class="daily-chip clickable"
                                :class="[getScoreClass(day.score), { 'chip-ryouhan': day.ryouhan_active, 'chip-dark-week': day.is_dark_week }]"
                                :aria-label="`${formatDate(day.date)} ${day.weekday} ${day.sanki_day_type || ''} 運勢 ${day.score} 分，點擊查看詳情`"
                                @click.stop="emit('selectDay', day.date)"
                              >
                                {{ formatDate(day.date) }} {{ day.weekday?.replace('曜日', '') }} {{ day.score }}
                                <span v-if="day.sanki_day_type" class="day-type">{{ day.sanki_day_type.replace('の日', '') }}</span>
                              </button>
                            </div>
                          </div>
                          <div class="week-detail-focus">
                            <span class="focus-label">重點：</span>
                            <span class="focus-text">{{ w.focus }}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </template>
              </div>
            </div>
          </div>

          <!-- 月度趨勢折線圖 -->
          <div v-if="yearlyFortune.monthly_trend?.length" class="yearly-chart-wrapper">
            <h4 class="chart-title">月度趨勢</h4>
            <div class="chart-scroll-container">
              <svg
                :viewBox="`0 0 ${monthlySvgWidth} ${monthlySvgHeight}`"
                class="yearly-chart"
                role="img"
                aria-label="月度運勢折線圖"
              >
                <!-- 背景帶 -->
                <rect
                  :x="monthlyPadLeft" :y="monthScoreToY(100)" :width="monthlyChartWidth" :height="monthScoreToY(75) - monthScoreToY(100)"
                  fill="rgba(80, 180, 80, 0.08)"
                />
                <rect
                  :x="monthlyPadLeft" :y="monthScoreToY(55)" :width="monthlyChartWidth" :height="monthScoreToY(minScore) - monthScoreToY(55)"
                  fill="rgba(220, 80, 80, 0.08)"
                />

                <!-- 格線 -->
                <g v-for="line in monthYGridLines" :key="line.score">
                  <line
                    :x1="monthlyPadLeft" :y1="line.y" :x2="monthlyPadLeft + monthlyChartWidth" :y2="line.y"
                    stroke="var(--border)" stroke-width="0.5" stroke-dasharray="4,4"
                  />
                  <text
                    :x="monthlyPadLeft - 6" :y="line.y + 4"
                    text-anchor="end" fill="var(--text-secondary)" font-size="11"
                  >{{ line.score }}</text>
                </g>

                <!-- 折線 -->
                <path
                  :d="monthlyTrendPath"
                  fill="none" stroke="var(--accent)" stroke-width="2.5"
                  stroke-linecap="round" stroke-linejoin="round"
                />

                <!-- 節點 -->
                <g v-for="(m, i) in yearlyFortune.monthly_trend" :key="'mdot-' + m.month">
                  <circle
                    :cx="monthToX(i)" :cy="monthScoreToY(m.score)" r="4"
                    :fill="m.month === currentMonth ? 'var(--accent)' : 'var(--bg-surface)'"
                    stroke="var(--accent)" stroke-width="2"
                  />
                  <text
                    :x="monthToX(i)" :y="monthScoreToY(m.score) - 10"
                    text-anchor="middle" fill="var(--text-primary)" font-size="11" font-weight="600"
                  >{{ m.score }}</text>
                  <text
                    :x="monthToX(i)" :y="monthlySvgHeight - 4"
                    text-anchor="middle" fill="var(--text-secondary)" font-size="11"
                    :font-weight="m.month === currentMonth ? '700' : '400'"
                  >{{ m.month }}月</text>
                </g>
              </svg>
            </div>
          </div>

          <div class="score-legend">
            <span class="legend-item"><span class="legend-dot excellent"></span>90+ <ruby>大吉<rp>(</rp><rt>だいきち</rt><rp>)</rp></ruby></span>
            <span class="legend-item"><span class="legend-dot good"></span>75+ <ruby>吉<rp>(</rp><rt>きち</rt><rp>)</rp></ruby></span>
            <span class="legend-item"><span class="legend-dot fair"></span>60+ <ruby>中吉<rp>(</rp><rt>ちゅうきち</rt><rp>)</rp></ruby></span>
            <span class="legend-item"><span class="legend-dot caution"></span>45+ <ruby>小凶<rp>(</rp><rt>しょうきょう</rt><rp>)</rp></ruby></span>
            <span class="legend-item"><span class="legend-dot warning"></span>&lt;45 <ruby>凶<rp>(</rp><rt>きょう</rt><rp>)</rp></ruby></span>
          </div>

          <!-- 趨吉避凶策略 -->
          <div v-if="yearlyFortune.strategy" class="strategy-section">
            <h4 class="strategy-title">趨吉避凶策略</h4>

            <!-- 年度節奏 -->
            <div v-if="yearlyFortune.strategy.yearly_rhythm" class="strategy-block rhythm-block">
              <div class="strategy-block-header">
                <span class="strategy-icon">&#x2014;</span>
                <span class="strategy-label">年度節奏</span>
                <span class="rhythm-halves">
                  上半年 {{ yearlyFortune.strategy.yearly_rhythm.first_half_avg }} / 下半年 {{ yearlyFortune.strategy.yearly_rhythm.second_half_avg }}
                </span>
              </div>
              <p class="strategy-desc">{{ yearlyFortune.strategy.yearly_rhythm.description }}</p>
            </div>

            <!-- 避風港 -->
            <div v-if="yearlyFortune.strategy.safe_havens.length" class="strategy-block safe-block">
              <div class="strategy-block-header">
                <span class="strategy-icon safe-icon">&#9650;</span>
                <span class="strategy-label">避風港月份</span>
              </div>
              <div v-for="h in [...yearlyFortune.strategy.safe_havens].sort((a, b) => a.start_month - b.start_month)" :key="h.start_month" class="strategy-item safe-item">
                <span class="strategy-months safe-tag">{{ h.start_month }}-{{ h.end_month }}月</span>
                <span class="strategy-avg">均分 {{ h.avg_score }}</span>
                <p class="strategy-item-desc">{{ h.description }}</p>
              </div>
            </div>

            <!-- 最佳行動月 -->
            <div v-if="yearlyFortune.strategy.best_months.length" class="strategy-block best-block">
              <div class="strategy-block-header">
                <span class="strategy-icon best-icon">&#9679;</span>
                <span class="strategy-label">最佳行動月</span>
              </div>
              <div v-for="b in [...yearlyFortune.strategy.best_months].sort((a, b) => a.month - b.month)" :key="b.month" class="strategy-item best-item">
                <span class="strategy-months best-tag">{{ b.month }}月</span>
                <span class="strategy-score" :class="getScoreClass(b.score)">{{ b.score }}</span>
                <p class="strategy-item-desc">{{ b.description }}</p>
              </div>
            </div>

            <!-- 警戒月 -->
            <div v-if="yearlyFortune.strategy.caution_months.length" class="strategy-block caution-block">
              <div class="strategy-block-header">
                <span class="strategy-icon caution-icon">&#9660;</span>
                <span class="strategy-label">警戒月份</span>
              </div>
              <div v-for="c in [...yearlyFortune.strategy.caution_months].sort((a, b) => a.month - b.month)" :key="c.month" class="strategy-item caution-item">
                <span class="strategy-months caution-tag">{{ c.month }}月</span>
                <span class="strategy-score" :class="getScoreClass(c.score)">{{ c.score }}</span>
                <p class="strategy-item-desc">{{ c.description }}</p>
              </div>
            </div>

            <!-- 凌犯概覽 -->
            <div v-if="yearlyFortune.strategy.ryouhan_outlook.affected_months.length" class="strategy-block ryouhan-block">
              <div class="strategy-block-header">
                <span class="strategy-icon ryouhan-icon">&#9888;</span>
                <span class="strategy-label">凌犯概覽</span>
                <span class="ryouhan-months-list">{{ yearlyFortune.strategy.ryouhan_outlook.affected_months.map(m => m + '月').join('、') }}</span>
              </div>
              <p class="strategy-desc">{{ yearlyFortune.strategy.ryouhan_outlook.description }}</p>
            </div>
          </div>

          <!-- 月度修行里程碑（僅修行者觀） -->
          <div v-if="isPractitioner && yearlyFortune.shingon?.monthly_tips && Object.keys(yearlyFortune.shingon.monthly_tips).length" class="monthly-milestones">
            <h4 class="milestones-title">月度修行里程碑</h4>
            <div class="milestone-list">
              <div v-for="month in 12" :key="month" class="milestone-item" :class="{ 'is-current-month': month === currentMonth }">
                <span class="milestone-month">{{ month }}月</span>
                <span class="milestone-text">{{ yearlyFortune.shingon.monthly_tips[String(month)] }}</span>
              </div>
            </div>
          </div>

          <div v-if="yearlyFortune.advice" class="advice-box">
            <h4>本年建議</h4>
            <p>{{ yearlyFortune.advice }}</p>
          </div>
        </div>
      </template>
      <div v-else class="loading-state">
        <sl-spinner></sl-spinner>
      </div>
    </div>

    <!-- Decade Fortune (流年) -->
    <div v-if="activeTab === 'decade'" id="panel-fortune-decade" class="fortune-content" role="tabpanel">
      <div class="fortune-card">
        <!-- 年份範圍導覽 -->
        <div class="decade-nav">
          <button class="decade-nav-btn" @click="prevDecade" aria-label="前十年">&lt; 前十年</button>
          <span class="decade-range">{{ decadeStartYear }}-{{ decadeEndYear }}</span>
          <button class="decade-nav-btn" @click="nextDecade" aria-label="後十年">後十年 &gt;</button>
        </div>

        <!-- 視角切換 -->
        <div class="perspective-toggle" role="radiogroup" aria-label="觀點切換">
          <button
            class="perspective-btn"
            :class="{ active: decadePerspective === 'secular' }"
            role="radio"
            :aria-checked="decadePerspective === 'secular'"
            @click="decadePerspective = 'secular'"
          >世俗觀</button>
          <button
            class="perspective-btn"
            :class="{ active: decadePerspective === 'practitioner' }"
            role="radio"
            :aria-checked="decadePerspective === 'practitioner'"
            @click="decadePerspective = 'practitioner'"
          >修行者觀</button>
          <button
            v-if="yearlyRange.length > 0"
            class="export-btn"
            @click="exportDecadeReport"
          >匯出報告</button>
        </div>

        <template v-if="yearlyRangeLoading">
          <div class="loading-state">
            <sl-spinner></sl-spinner>
          </div>
        </template>

        <template v-else-if="yearlyRange.length > 0">
          <!-- 九曜循環總覽 -->
          <div class="kuyou-cycle">
            <h4 class="kuyou-cycle-title">九曜循環總覽</h4>
            <div class="kuyou-cycle-grid">
              <div
                v-for="y in yearlyRange"
                :key="y.year"
                class="kuyou-cycle-cell"
                :class="{ 'is-current-year': y.year === currentYear }"
              >
                <span class="cycle-year">'{{ String(y.year).slice(-2) }}</span>
                <span class="cycle-star">{{ shortStarName(y.kuyou_star.name) }}</span>
                <template v-if="isPractitioner && y.shingon">
                  <span class="cycle-level practice-level" :class="getPracticeLevelClass(y.shingon.practice_level)">{{ y.shingon.practice_name.replace('期', '') }}</span>
                </template>
                <template v-else>
                  <span class="cycle-level kuyou-level" :class="getKuyouLevelClass(y.kuyou_star.level)">{{ y.kuyou_star.level }}</span>
                </template>
              </div>
            </div>
          </div>

          <!-- SVG 折線圖 -->
          <div class="decade-chart-wrapper">
            <h4 class="chart-title">十年整體運勢趨勢</h4>
            <div class="chart-scroll-container">
              <svg
                :viewBox="`0 0 ${svgWidth} ${svgHeight}`"
                class="decade-chart"
                role="img"
                aria-label="十年運勢折線圖"
              >
                <!-- 背景帶 -->
                <rect
                  :x="padLeft" :y="scoreToY(100)" :width="chartWidth" :height="scoreToY(75) - scoreToY(100)"
                  fill="rgba(80, 180, 80, 0.08)"
                />
                <rect
                  :x="padLeft" :y="scoreToY(55)" :width="chartWidth" :height="scoreToY(minScore) - scoreToY(55)"
                  :fill="isPractitioner ? 'rgba(123, 31, 162, 0.08)' : 'rgba(220, 80, 80, 0.08)'"
                />

                <!-- 格線 -->
                <g v-for="line in yGridLines" :key="line.score">
                  <line
                    :x1="padLeft" :y1="line.y" :x2="padLeft + chartWidth" :y2="line.y"
                    stroke="var(--border)" stroke-width="0.5" stroke-dasharray="4,4"
                  />
                  <text
                    :x="padLeft - 8" :y="line.y + 4"
                    text-anchor="end" fill="var(--text-secondary)" font-size="11"
                  >{{ line.score }}</text>
                </g>

                <!-- 折線 -->
                <path
                  :d="overallPath"
                  fill="none" stroke="var(--accent)" stroke-width="2.5"
                  stroke-linecap="round" stroke-linejoin="round"
                />

                <!-- 節點 -->
                <g v-for="(y, i) in yearlyRange" :key="'dot-' + y.year">
                  <circle
                    :cx="yearToX(i)" :cy="scoreToY(y.fortune.overall)" r="4"
                    :fill="y.year === currentYear ? 'var(--accent)' : 'var(--bg-surface)'"
                    stroke="var(--accent)" stroke-width="2"
                  />
                  <!-- 分數標註 -->
                  <text
                    :x="yearToX(i)" :y="scoreToY(y.fortune.overall) - 10"
                    text-anchor="middle" fill="var(--text-primary)" font-size="11" font-weight="600"
                  >{{ y.fortune.overall }}</text>
                  <!-- X 軸年份 -->
                  <text
                    :x="yearToX(i)" :y="svgHeight - 4"
                    text-anchor="middle" fill="var(--text-secondary)" font-size="11"
                    :font-weight="y.year === currentYear ? '700' : '400'"
                  >{{ String(y.year).slice(-2) }}</text>
                </g>
              </svg>
            </div>
          </div>

          <div class="score-legend">
            <span class="legend-item"><span class="legend-dot excellent"></span>90+ <ruby>大吉<rp>(</rp><rt>だいきち</rt><rp>)</rp></ruby></span>
            <span class="legend-item"><span class="legend-dot good"></span>75+ <ruby>吉<rp>(</rp><rt>きち</rt><rp>)</rp></ruby></span>
            <span class="legend-item"><span class="legend-dot fair"></span>60+ <ruby>中吉<rp>(</rp><rt>ちゅうきち</rt><rp>)</rp></ruby></span>
            <span class="legend-item"><span class="legend-dot caution"></span>45+ <ruby>小凶<rp>(</rp><rt>しょうきょう</rt><rp>)</rp></ruby></span>
            <span class="legend-item"><span class="legend-dot warning"></span>&lt;45 <ruby>凶<rp>(</rp><rt>きょう</rt><rp>)</rp></ruby></span>
          </div>

          <!-- 年度卡片列表 -->
          <div class="decade-cards">
            <div
              v-for="y in yearlyRange"
              :key="'card-' + y.year"
              class="decade-card"
              :class="{ 'is-current-year': y.year === currentYear }"
            >
              <button
                class="decade-card-header"
                :aria-expanded="expandedDecadeYear === y.year"
                @click="toggleDecadeYear(y.year)"
              >
                <div class="card-header-left">
                  <span class="card-year">{{ y.year }}</span>
                  <span class="card-star">{{ y.kuyou_star.name }}</span>
                  <template v-if="isPractitioner && y.shingon">
                    <span class="practice-level" :class="getPracticeLevelClass(y.shingon.practice_level)">{{ y.shingon.practice_name }}</span>
                  </template>
                  <template v-else>
                    <span class="kuyou-level" :class="getKuyouLevelClass(y.kuyou_star.level)">{{ y.kuyou_star.level }}</span>
                  </template>
                </div>
                <div class="card-header-right">
                  <div class="card-mini-scores">
                    <span class="mini-score" :class="getScoreClass(y.fortune.overall)">{{ y.fortune.overall }}</span>
                  </div>
                  <span class="card-toggle" aria-hidden="true">{{ expandedDecadeYear === y.year ? '▼' : '▶' }}</span>
                </div>
              </button>

              <div v-if="expandedDecadeYear === y.year" class="decade-card-detail">
                <div class="card-scores">
                  <div class="score-row">
                    <span class="score-label">整體</span>
                    <div class="score-bar"><div class="score-fill" :class="getScoreClass(y.fortune.overall)" :style="{ width: y.fortune.overall + '%' }"></div></div>
                    <span class="score-value">{{ y.fortune.overall }}</span>
                  </div>
                  <div class="score-row">
                    <span class="score-label">{{ isPractitioner && y.shingon ? y.shingon.category_labels.career : '事業' }}</span>
                    <div class="score-bar"><div class="score-fill" :class="getScoreClass(y.fortune.career)" :style="{ width: y.fortune.career + '%' }"></div></div>
                    <span class="score-value">{{ y.fortune.career }}</span>
                  </div>
                  <div class="score-row">
                    <span class="score-label">{{ isPractitioner && y.shingon ? y.shingon.category_labels.love : '感情' }}</span>
                    <div class="score-bar"><div class="score-fill" :class="getScoreClass(y.fortune.love)" :style="{ width: y.fortune.love + '%' }"></div></div>
                    <span class="score-value">{{ y.fortune.love }}</span>
                  </div>
                  <div class="score-row">
                    <span class="score-label">{{ isPractitioner && y.shingon ? y.shingon.category_labels.health : '健康' }}</span>
                    <div class="score-bar"><div class="score-fill" :class="getScoreClass(y.fortune.health)" :style="{ width: y.fortune.health + '%' }"></div></div>
                    <span class="score-value">{{ y.fortune.health }}</span>
                  </div>
                  <div class="score-row">
                    <span class="score-label">{{ isPractitioner && y.shingon ? y.shingon.category_labels.wealth : '財運' }}</span>
                    <div class="score-bar"><div class="score-fill" :class="getScoreClass(y.fortune.wealth)" :style="{ width: y.fortune.wealth + '%' }"></div></div>
                    <span class="score-value">{{ y.fortune.wealth }}</span>
                  </div>
                </div>

                <!-- 修行者觀：詳細修行資訊 -->
                <template v-if="isPractitioner && y.shingon">
                  <div class="shingon-mantra-box">
                    <div class="mantra-bija-section">
                      <span v-if="y.shingon.mantra.siddham_unicode" class="bija-siddham">{{ y.shingon.mantra.siddham_unicode }}</span>
                      <span v-if="y.shingon.mantra.siddham_roman" class="bija-iast">{{ y.shingon.mantra.siddham_roman }}</span>
                      <span class="bija-buddha">{{ y.shingon.mantra.buddha }}</span>
                    </div>
                    <div class="mantra-text-section">
                      <p class="mantra-label">真言</p>
                      <p class="mantra-text">{{ y.shingon.mantra.text }}</p>
                      <p class="mantra-reading">{{ y.shingon.mantra.reading }}</p>
                    </div>
                  </div>
                  <div class="shingon-homa-box">
                    <span class="homa-type">{{ y.shingon.homa_type }}</span>
                    <span class="homa-desc">{{ y.shingon.homa_description }}</span>
                  </div>
                  <p class="practice-focus-text">修行重心：{{ y.shingon.practice_focus }}</p>
                  <div v-if="y.shingon.theme" class="card-theme">
                    <strong>{{ y.shingon.theme.title }}</strong>
                    <p>{{ y.shingon.theme.description }}</p>
                  </div>
                  <div v-if="y.shingon.core_teaching" class="core-teaching-box">
                    <p>{{ y.shingon.core_teaching }}</p>
                  </div>
                  <div v-if="y.shingon.recommended_practices?.length" class="recommended-practices">
                    <h5>推薦修法</h5>
                    <div class="practice-tags">
                      <span v-for="(p, i) in y.shingon.recommended_practices" :key="i" class="practice-tag">{{ p }}</span>
                    </div>
                  </div>
                  <div v-if="y.shingon.category_practice" class="category-descriptions">
                    <div v-if="y.shingon.category_practice.career" class="category-desc-item">
                      <h4>{{ y.shingon.category_labels.career }}</h4>
                      <p>{{ y.shingon.category_practice.career }}</p>
                    </div>
                    <div v-if="y.shingon.category_practice.love" class="category-desc-item">
                      <h4>{{ y.shingon.category_labels.love }}</h4>
                      <p>{{ y.shingon.category_practice.love }}</p>
                    </div>
                    <div v-if="y.shingon.category_practice.health" class="category-desc-item">
                      <h4>{{ y.shingon.category_labels.health }}</h4>
                      <p>{{ y.shingon.category_practice.health }}</p>
                    </div>
                    <div v-if="y.shingon.category_practice.wealth" class="category-desc-item">
                      <h4>{{ y.shingon.category_labels.wealth }}</h4>
                      <p>{{ y.shingon.category_practice.wealth }}</p>
                    </div>
                  </div>
                  <div v-if="y.shingon.opportunities?.length" class="opportunities">
                    <h4>修行好時機</h4>
                    <ul>
                      <li v-for="(opp, i) in y.shingon.opportunities" :key="i">{{ opp }}</li>
                    </ul>
                  </div>
                  <div v-if="y.shingon.warnings?.length" class="warnings">
                    <h4>修行注意事項</h4>
                    <ul>
                      <li v-for="(warn, i) in y.shingon.warnings" :key="i">{{ warn }}</li>
                    </ul>
                  </div>
                  <p v-if="y.shingon.advice" class="card-advice">{{ y.shingon.advice }}</p>
                </template>

                <!-- 世俗觀：原有內容 -->
                <template v-else>
                  <p class="card-buddha">守護佛：{{ y.kuyou_star.buddha }}</p>
                  <div v-if="y.theme" class="card-theme">
                    <strong>{{ y.theme.title }}</strong>
                    <p>{{ y.theme.description }}</p>
                  </div>
                  <p v-if="y.advice" class="card-advice">{{ y.advice }}</p>
                </template>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>
    <!-- 訂閱日曆 Dialog -->
    <div v-if="subscribeDialogOpen" class="subscribe-overlay" @click.self="subscribeDialogOpen = false">
      <div class="subscribe-dialog" role="dialog" aria-label="訂閱日曆">
        <h3 class="subscribe-title">訂閱日曆</h3>
        <p class="subscribe-desc">日曆 app 會每天自動更新，不需要重新匯入。</p>

        <div class="subscribe-actions">
          <button class="subscribe-action-btn primary" @click="openWebcal">
            <sl-icon name="calendar-plus" aria-hidden="true"></sl-icon>
            加入日曆 app
          </button>
          <button class="subscribe-action-btn" @click="copySubscribeUrl">
            <sl-icon :name="subscribeCopied ? 'check-lg' : 'clipboard'" aria-hidden="true"></sl-icon>
            {{ subscribeCopied ? '已複製' : '複製連結' }}
          </button>
        </div>

        <div v-if="subscribeUrls" class="subscribe-url-box">
          <code class="subscribe-url">{{ subscribeUrls.https_url }}</code>
        </div>

        <p class="subscribe-hint">
          iPhone/Mac 點「加入日曆 app」即可。<br>
          Google Calendar 請複製連結後，到設定 > 透過 URL 新增日曆。
        </p>

        <button class="subscribe-close" @click="subscribeDialogOpen = false" aria-label="關閉">
          <sl-icon name="x-lg" aria-hidden="true"></sl-icon>
        </button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.sub-tabs {
  display: flex;
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
}

.fortune-content {
  animation: fadeIn 0.3s ease;
}

.fortune-card {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: var(--space-md);
}

.fortune-title {
  font-size: var(--font-lg);
  margin: 0 0 var(--space-md);
  color: var(--text-primary);
  text-wrap: balance;
}

.weekday-element,
.date-range,
.year-info {
  color: var(--text-secondary);
  font-size: var(--font-sm);
  font-weight: 400;
}

.score-bars {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
}

.score-row {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.score-label {
  width: 48px;
  color: var(--text-secondary);
  font-size: var(--font-sm);
}

.score-bar {
  flex: 1;
  height: 8px;
  background: var(--bg-elevated);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.score-fill {
  height: 100%;
  border-radius: var(--radius-sm);
  transition: width 0.5s ease;
}

.score-fill.excellent { background: var(--stellar); }
.score-fill.good { background: var(--success); }
.score-fill.fair { background: var(--info); }
.score-fill.caution { background: var(--caution); }
.score-fill.warning { background: var(--warning); }

.score-value {
  width: 32px;
  text-align: right;
  font-size: var(--font-sm);
  font-variant-numeric: tabular-nums;
  color: var(--text-secondary);
}

.score-value.excellent { color: var(--stellar); font-weight: 600; }
.score-value.good { color: var(--success); font-weight: 600; }
.score-value.fair { color: var(--info); font-weight: 600; }
.score-value.caution { color: var(--caution); font-weight: 600; }
.score-value.warning { color: var(--warning); font-weight: 600; }

.score-group {
  display: flex;
  flex-direction: column;
}

.score-desc {
  margin: 2px 0 var(--space-xs);
  padding-left: calc(48px + var(--space-md));
  font-size: var(--font-xs);
  color: var(--text-secondary);
  line-height: 1.5;
  opacity: 0.85;
}

.score-legend {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  padding: var(--space-xs) 0;
  margin-bottom: var(--space-md);
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--text-secondary);
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 2px;
}

.legend-dot.excellent { background: var(--stellar); }
.legend-dot.good { background: var(--success); }
.legend-dot.fair { background: var(--info); }
.legend-dot.caution { background: var(--caution); }
.legend-dot.warning { background: var(--warning); }

.overall-row {
  padding-bottom: var(--space-sm);
  margin-bottom: var(--space-xs);
  border-bottom: 1px solid var(--border);
}

.overall-row .score-label {
  font-weight: 600;
  color: var(--text-primary);
}

.overall-row .score-bar {
  height: 10px;
}

.special-day-banner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-md);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-md);
  border: 1px solid var(--border);
}

.special-day-banner.kanro {
  background: linear-gradient(135deg, rgba(255, 215, 0, 0.12), rgba(255, 183, 0, 0.08));
  border-color: rgba(255, 183, 0, 0.4);
}

.special-day-banner.kongou {
  background: linear-gradient(135deg, rgba(100, 200, 100, 0.12), rgba(80, 180, 80, 0.08));
  border-color: rgba(80, 180, 80, 0.4);
}

.special-day-banner.rasetsu {
  background: linear-gradient(135deg, rgba(220, 80, 80, 0.12), rgba(200, 60, 60, 0.08));
  border-color: rgba(200, 60, 60, 0.4);
}

.special-day-level {
  font-size: var(--font-xs);
  font-weight: 700;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  white-space: nowrap;
}

.kanro .special-day-level {
  background: rgba(255, 183, 0, 0.25);
  color: #b8860b;
}

.kongou .special-day-level {
  background: rgba(80, 180, 80, 0.25);
  color: #2e7d32;
}

.rasetsu .special-day-level {
  background: rgba(200, 60, 60, 0.25);
  color: #c62828;
}

.special-day-name {
  font-weight: 600;
  font-size: var(--font-base);
}

.special-day-desc {
  width: 100%;
  margin: var(--space-xs) 0 0;
  font-size: var(--font-sm);
  color: var(--text-secondary);
  line-height: 1.5;
}

.special-day-reversed {
  width: 100%;
  margin: var(--space-xs) 0 0;
  font-size: var(--font-xs);
  color: #b8860b;
  font-weight: 600;
}

.special-day-banner.reversed {
  border-style: dashed;
}

.ryouhan-banner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-md);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-md);
  background: linear-gradient(135deg, rgba(128, 0, 128, 0.10), rgba(100, 0, 100, 0.06));
  border: 1px dashed rgba(128, 0, 128, 0.4);
}

.ryouhan-label {
  font-size: var(--font-xs);
  font-weight: 700;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  background: rgba(128, 0, 128, 0.2);
  color: #4A3B6B;
  white-space: nowrap;
}

.ryouhan-desc {
  width: 100%;
  margin: var(--space-xs) 0 0;
  font-size: var(--font-sm);
  color: var(--text-secondary);
  line-height: 1.5;
}

.ryouhan-warning {
  width: 100%;
  margin: var(--space-xs) 0 0;
  font-size: var(--font-sm);
  color: #4A3B6B;
  font-weight: 600;
  line-height: 1.5;
}

.ryouhan-source {
  font-size: var(--font-xs);
  color: var(--text-secondary);
  opacity: 0.7;
  font-style: italic;
}

.compound-analysis {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
}

.compound-item {
  padding: var(--space-md);
  border-radius: var(--radius-md);
  border: 1px solid var(--border);
}

.compound-item.severity-5 {
  background: linear-gradient(135deg, rgba(128, 0, 128, 0.12), rgba(220, 80, 80, 0.08));
  border-color: rgba(128, 0, 128, 0.4);
}

.compound-item.severity-4 {
  background: linear-gradient(135deg, rgba(234, 179, 8, 0.12), rgba(200, 140, 0, 0.08));
  border-color: rgba(200, 140, 0, 0.4);
}

.compound-item.severity-3 {
  background: linear-gradient(135deg, rgba(150, 150, 150, 0.10), rgba(120, 120, 120, 0.06));
  border-color: rgba(120, 120, 120, 0.3);
}

.compound-item.severity-2,
.compound-item.severity-1 {
  background: var(--bg-elevated);
  border-color: var(--border);
}

.compound-label {
  font-size: var(--font-sm);
  font-weight: 700;
}

.compound-desc {
  margin: var(--space-xs) 0 0;
  font-size: var(--font-sm);
  color: var(--text-secondary);
  line-height: 1.5;
}

.week-alerts,
.month-alerts {
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-md);
  background: linear-gradient(135deg, rgba(128, 0, 128, 0.06), rgba(100, 0, 100, 0.03));
  border: 1px dashed rgba(128, 0, 128, 0.25);
}

.week-warning-item,
.month-warning-item {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  margin: 2px 0;
  line-height: 1.4;
}

.ryouhan-month-info {
  font-size: var(--font-sm);
  font-weight: 600;
  color: #4A3B6B;
  margin-bottom: var(--space-xs);
}

.rokugai-banner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-md);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-md);
  background: linear-gradient(135deg, rgba(180, 0, 0, 0.12), rgba(150, 0, 0, 0.06));
  border: 1px solid rgba(180, 0, 0, 0.5);
}

.rokugai-label {
  font-size: var(--font-xs);
  font-weight: 700;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  background: rgba(180, 0, 0, 0.25);
  color: #b71c1c;
  white-space: nowrap;
}

.rokugai-desc {
  width: 100%;
  margin: var(--space-xs) 0 0;
  font-size: var(--font-sm);
  color: var(--text-secondary);
  line-height: 1.5;
}

.sanki-box {
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-md);
}

.sanki-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
  margin-bottom: var(--space-xs);
}

.sanki-period {
  font-size: var(--font-sm);
  font-weight: 600;
}

.sanki-1 { color: #2196f3; }
.sanki-2 { color: #f44336; }
.sanki-3 { color: #4caf50; }

.sanki-day-type {
  font-size: var(--font-sm);
  font-weight: 600;
  color: var(--text-primary);
}

.sanki-day-desc {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0 0 var(--space-xs);
}

.sanki-period-desc {
  font-size: var(--font-xs);
  color: var(--text-secondary);
  opacity: 0.7;
  line-height: 1.5;
  margin: 0;
}

.sanki-box.dark-week {
  background: linear-gradient(135deg, rgba(180, 0, 0, 0.08), rgba(100, 0, 0, 0.04));
  border-color: rgba(180, 0, 0, 0.3);
}

.dark-week-label {
  font-size: var(--font-xs);
  font-weight: 600;
  color: #c62828;
  padding: 1px 6px;
  background: rgba(200, 60, 60, 0.15);
  border-radius: var(--radius-sm);
}

.lucky-info {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-md);
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-md);
}

.lucky-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.lucky-label {
  color: var(--text-secondary);
  font-size: var(--font-xs);
}

.lucky-value {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: var(--font-sm);
}

.color-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

/* Mansion Hint */
.mansion-hint {
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-md);
}

.mansion-hint h4 {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: var(--font-sm);
  color: var(--text-primary);
  margin: 0 0 var(--space-sm);
}

.hint-relation {
  font-size: var(--font-xs);
  font-weight: 600;
  padding: 2px 8px;
  border-radius: var(--radius-full);
}

.hint-relation.eishin { background: var(--stellar); color: var(--text-on-accent); }
.hint-relation.gyotai { background: var(--success); color: var(--text-on-accent); }
.hint-relation.mei { background: var(--info); color: var(--text-on-accent); }
.hint-relation.yusui { background: var(--text-secondary); color: var(--text-on-accent); }
.hint-relation.kisei { background: var(--caution); color: var(--text-on-accent); }
.hint-relation.ankai { background: var(--warning); color: var(--text-on-accent); }

.hint-mansions {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  margin: 0 0 var(--space-sm);
}

.hint-mansions strong {
  color: var(--text-primary);
}

.mansion-hint p {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0 0 var(--space-xs);
}

.mansion-hint p:last-child {
  margin-bottom: 0;
}

.hint-element {
  font-style: italic;
  opacity: 0.85;
}

.day-fortune-box {
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  border: 1px solid var(--border);
}

.day-fortune-box.most-auspicious {
  border-color: var(--score-high, #c9a43c);
  background: color-mix(in srgb, var(--score-high, #c9a43c) 6%, var(--bg-elevated));
}

.day-fortune-box h4 {
  font-size: var(--font-sm);
  color: var(--text-primary);
  margin: 0 0 var(--space-xs);
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.best-day-badge {
  font-size: 0.7rem;
  padding: 1px 6px;
  border-radius: var(--radius-sm);
  background: var(--score-high, #c9a43c);
  color: var(--text-on-accent);
  font-weight: 600;
}

.day-fortune-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: var(--space-xs);
}

.day-tag {
  font-size: 0.75rem;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-weight: 500;
}

.day-tag.auspicious {
  background: color-mix(in srgb, var(--score-high, #c9a43c) 15%, var(--bg-surface));
  color: var(--score-high, #c9a43c);
}

.day-tag.inauspicious {
  background: color-mix(in srgb, var(--score-low, #b44) 12%, var(--bg-surface));
  color: var(--score-low, #b44);
}

.day-fortune-classic,
.day-fortune-ja,
.day-fortune-zh {
  margin: 0;
  font-size: 0.75rem;
  line-height: 1.5;
}

.day-fortune-classic {
  color: var(--text-tertiary);
  font-style: italic;
}

.day-fortune-ja {
  color: var(--text-tertiary);
  margin-top: 2px;
}

.day-fortune-zh {
  color: var(--text-secondary);
  margin-top: 2px;
}

.day-fortune-source {
  margin: var(--space-xs) 0 0;
  font-size: 0.65rem;
  color: var(--text-tertiary);
  opacity: 0.7;
  text-align: right;
}

.advice-box {
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  border-left: 3px solid var(--accent);
}

.advice-box h4 {
  font-size: var(--font-sm);
  color: var(--accent);
  margin: 0 0 var(--space-sm);
}

.advice-box p {
  margin: 0;
  font-size: var(--font-sm);
  color: var(--text-secondary);
  line-height: 1.6;
}

.kuyou-star-box {
  padding: var(--space-md);
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-md);
}

.kuyou-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

.kuyou-name {
  font-size: var(--font-lg);
  font-weight: 700;
}

.kuyou-level {
  font-size: var(--font-xs);
  font-weight: 700;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
}

.kuyou-level.level-great {
  background: rgba(255, 183, 0, 0.2);
  color: #b8860b;
}

.kuyou-level.level-good {
  background: rgba(80, 180, 80, 0.2);
  color: #2e7d32;
}

.kuyou-level.level-half {
  background: rgba(100, 150, 220, 0.2);
  color: #1565c0;
}

.kuyou-level.level-bad {
  background: rgba(200, 60, 60, 0.2);
  color: #c62828;
}

.kuyou-fortune-name {
  font-size: var(--font-sm);
  color: var(--text-secondary);
}

.kuyou-age {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  margin: var(--space-xs) 0 0;
}

.kuyou-desc {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  line-height: 1.6;
  margin: var(--space-sm) 0 0;
}

.kuyou-buddha {
  font-size: var(--font-xs);
  color: var(--text-secondary);
  margin: var(--space-sm) 0 0;
  font-style: italic;
}

.kuyou-buddha-note {
  font-size: 11px;
  color: var(--text-tertiary, var(--text-secondary));
  margin: 2px 0 0;
  opacity: 0.7;
}

.theme-box {
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-md);
}

.theme-box h4 {
  color: var(--accent);
  margin: 0 0 var(--space-xs);
}

.theme-box .theme-focus {
  color: var(--text-secondary);
  font-size: var(--font-sm);
  margin: 0;
}

.theme-box .theme-desc {
  color: var(--text-secondary);
  font-size: var(--font-sm);
  line-height: 1.6;
  margin: var(--space-sm) 0 0;
}

/* Weekly Focus */
.weekly-focus {
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-md);
}

.weekly-focus h4 {
  font-size: var(--font-sm);
  color: var(--accent);
  margin: 0 0 var(--space-sm);
}

.weekly-focus p {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0;
}

.daily-overview,
.weekly-overview {
  margin-bottom: var(--space-md);
}

.daily-overview h4,
.weekly-overview h4 {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  margin: 0 0 var(--space-sm);
}

.daily-list {
  display: flex;
  gap: var(--space-sm);
  overflow-x: auto;
  padding-bottom: var(--space-sm);
  -webkit-overflow-scrolling: touch;
  scrollbar-width: thin;
  mask-image: linear-gradient(to right, transparent, black 8px, black calc(100% - 24px), transparent);
  -webkit-mask-image: linear-gradient(to right, transparent, black 8px, black calc(100% - 24px), transparent);
}

.daily-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: var(--space-xs) var(--space-sm);
  background: var(--bg-elevated);
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  min-width: 52px;
  cursor: pointer;
  font: inherit;
  color: inherit;
  transition: background-color 0.2s, border-color 0.2s, transform 0.15s;
}

.daily-item:hover {
  background: var(--bg-primary);
  border-color: var(--border);
  transform: translateY(-2px);
}

.daily-item:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.daily-item.excellent { border-bottom: 2px solid var(--stellar); }
.daily-item.good { border-bottom: 2px solid var(--success); }
.daily-item.fair { border-bottom: 2px solid var(--info); }
.daily-item.caution { border-bottom: 2px solid var(--caution); }
.daily-item.warning { border-bottom: 2px solid var(--warning); }

.daily-item.is-today {
  background: var(--accent);
  color: var(--text-on-accent);
  border-color: var(--accent);
}

.daily-item.is-today:hover {
  background: var(--accent);
  opacity: 0.9;
}

.daily-item.is-today .day-date,
.daily-item.is-today .day-weekday {
  color: var(--text-on-accent);
}

.daily-item.is-yesterday {
  opacity: 0.7;
}

.day-label {
  font-size: var(--font-xs);
  font-weight: 600;
  color: var(--accent);
  background: rgba(139, 105, 20, 0.12);
  padding: 1px 6px;
  border-radius: var(--radius-sm);
  margin-bottom: 2px;
}

.daily-item.is-today .day-label {
  color: var(--text-on-accent);
  background: rgba(0, 0, 0, 0.15);
}

.day-label.yesterday {
  color: var(--text-secondary);
  background: var(--bg-elevated);
}

.day-date {
  font-size: var(--font-xs);
  color: var(--text-secondary);
}

.day-weekday {
  font-size: var(--font-sm);
}

.day-score {
  font-size: var(--font-lg);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.day-special {
  font-size: 10px;
  color: var(--text-secondary);
  line-height: 1;
}

.daily-item.chip-ryouhan {
  border-left: 2px solid var(--rasetsu-color);
}

.daily-item.chip-dark-week:not(.is-today) {
  background: var(--dark-week-bg);
}

.daily-chip.chip-ryouhan {
  border-left-color: var(--rasetsu-color);
}

.daily-chip.chip-dark-week {
  background: var(--dark-week-bg);
}

.daily-chip .day-special {
  font-size: 10px;
  margin-left: 2px;
  color: var(--text-secondary);
}

.daily-chip .day-type {
  font-size: 10px;
  margin-left: 2px;
  color: var(--text-muted);
}

.weekly-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.weekly-item-wrapper {
  display: flex;
  flex-direction: column;
}

.weekly-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  width: 100%;
  padding: var(--space-sm) var(--space-md);
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background-color 0.2s, border-color 0.2s;
  font: inherit;
  color: inherit;
  text-align: left;
}

.weekly-item:hover {
  background: var(--bg-elevated);
  border-color: var(--border);
}

.weekly-item:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.weekly-item.expanded {
  background: var(--bg-elevated);
  border-color: var(--accent);
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
}

.week-toggle {
  width: 16px;
  font-size: var(--font-xs);
  color: var(--text-secondary);
  flex-shrink: 0;
}

.week-num {
  min-width: 56px;
  font-size: var(--font-sm);
  color: var(--text-secondary);
  flex-shrink: 0;
}

.week-num ruby rt {
  font-size: 9px;
  color: var(--text-muted);
}

.week-days-count {
  font-size: var(--font-xs);
  color: var(--text-muted);
  flex-shrink: 0;
}

.weekly-item.has-dark {
  border-left: 2px solid var(--dark-week-bg, #4a3a5c);
}

.week-current-tag {
  font-size: var(--font-xs);
  color: var(--accent);
  background: rgba(139, 105, 20, 0.12);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
}

.week-bar {
  flex: 1;
  height: 8px;
  background: var(--bg-elevated);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.week-fill {
  height: 100%;
  border-radius: var(--radius-sm);
}

.week-fill.excellent { background: var(--stellar); }
.week-fill.good { background: var(--success); }
.week-fill.fair { background: var(--info); }
.week-fill.caution { background: var(--caution); }
.week-fill.warning { background: var(--warning); }

.week-score {
  width: 32px;
  text-align: right;
  font-size: var(--font-sm);
  font-variant-numeric: tabular-nums;
  color: var(--text-secondary);
  flex-shrink: 0;
}

/* Week Detail Expansion */
.week-detail {
  background: var(--bg-elevated);
  border: 1px solid var(--accent);
  border-top: none;
  border-radius: 0 0 var(--radius-md) var(--radius-md);
  padding: var(--space-md);
  animation: slideDown 0.2s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.week-detail-loading {
  display: flex;
  justify-content: center;
  padding: var(--space-md);
}

.week-detail-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.week-detail-scores {
  display: flex;
  gap: var(--space-lg);
  flex-wrap: wrap;
}

.detail-score-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.detail-label {
  font-size: var(--font-sm);
  color: var(--text-secondary);
}

.detail-value {
  font-size: var(--font-md);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.detail-value.excellent { color: var(--stellar); }
.detail-value.good { color: var(--success); }
.detail-value.fair { color: var(--info); }
.detail-value.caution { color: var(--caution); }
.detail-value.warning { color: var(--warning); }

.week-detail-daily {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

.daily-label {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  flex-shrink: 0;
}

.daily-chips {
  display: flex;
  gap: var(--space-xs);
  flex-wrap: wrap;
}

.daily-chip {
  font-size: var(--font-xs);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  background: var(--bg-primary);
  font-variant-numeric: tabular-nums;
}

.daily-chip.excellent { border-left: 2px solid var(--stellar); }
.daily-chip.good { border-left: 2px solid var(--success); }
.daily-chip.fair { border-left: 2px solid var(--info); }
.daily-chip.caution { border-left: 2px solid var(--caution); }
.daily-chip.warning { border-left: 2px solid var(--warning); }

.daily-chip.clickable {
  cursor: pointer;
  border: none;
  font: inherit;
  transition: background-color 0.2s, transform 0.15s;
}

.daily-chip.clickable:hover {
  background: var(--bg-elevated);
  transform: translateY(-1px);
}

.daily-chip.clickable:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.week-date-range {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  margin-bottom: var(--space-sm);
}

.week-detail-focus {
  font-size: var(--font-sm);
  line-height: 1.5;
}

.focus-label {
  color: var(--accent);
  margin-right: var(--space-xs);
}

.focus-text {
  color: var(--text-secondary);
}

.week-detail-advice {
  font-size: var(--font-sm);
  line-height: 1.5;
}

.advice-label {
  color: var(--accent);
  margin-right: var(--space-xs);
}

.advice-text {
  color: var(--text-secondary);
}

@media (prefers-reduced-motion: reduce) {
  .week-detail {
    animation: none;
  }
}

/* Monthly Trend */
.monthly-trend {
  margin-bottom: var(--space-md);
}

.monthly-trend h4 {
  font-size: var(--font-sm);
  color: var(--accent);
  margin: 0 0 var(--space-sm);
}

.trend-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.trend-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.trend-month {
  width: 36px;
  font-size: var(--font-xs);
  color: var(--text-secondary);
  text-align: right;
  flex-shrink: 0;
}

.trend-bar {
  flex: 1;
  height: 6px;
  background: var(--bg-elevated);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.trend-fill {
  height: 100%;
  border-radius: var(--radius-sm);
  transition: width 0.5s ease;
}

.trend-fill.excellent { background: var(--stellar); }
.trend-fill.good { background: var(--success); }
.trend-fill.fair { background: var(--info); }
.trend-fill.caution { background: var(--caution); }
.trend-fill.warning { background: var(--warning); }

.trend-score {
  width: 28px;
  text-align: right;
  font-size: var(--font-xs);
  font-variant-numeric: tabular-nums;
  flex-shrink: 0;
}

.trend-score.excellent { color: var(--stellar); font-weight: 600; }
.trend-score.good { color: var(--success); font-weight: 600; }
.trend-score.fair { color: var(--info); }
.trend-score.caution { color: var(--caution); }
.trend-score.warning { color: var(--warning); }

/* Month Mansion Info */
.month-mansion-info {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
  margin-bottom: var(--space-md);
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  font-size: var(--font-sm);
  color: var(--text-secondary);
}

.month-mansion-info strong {
  color: var(--text-primary);
}

.lunar-month {
  padding: 2px 8px;
  background: rgba(139, 105, 20, 0.08);
  border-radius: var(--radius-sm);
  font-size: var(--font-xs);
  color: var(--accent);
  font-weight: 500;
}

.month-relation-desc {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  margin: 0 0 var(--space-md);
  line-height: 1.6;
}

.opportunities,
.warnings {
  margin-bottom: var(--space-md);
}

.opportunities h4 {
  color: var(--stellar);
  font-size: var(--font-sm);
  margin: 0 0 var(--space-sm);
}

.warnings h4 {
  color: var(--warning);
  font-size: var(--font-sm);
  margin: 0 0 var(--space-sm);
}

.opportunities ul,
.warnings ul {
  margin: 0;
  padding-left: var(--space-lg);
}

.opportunities li,
.warnings li {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  margin-bottom: var(--space-xs);
}

.category-descriptions {
  margin-bottom: var(--space-md);
}

.category-desc-item {
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-sm);
}

.category-desc-item h4 {
  color: var(--accent);
  font-size: var(--font-sm);
  margin: 0 0 var(--space-xs);
}

.category-desc-item p {
  color: var(--text-secondary);
  font-size: var(--font-sm);
  line-height: 1.6;
  margin: 0;
}

.loading-state {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: var(--space-2xl);
}

/* ============================================================
   Yearly (本年) Tab
   ============================================================ */
.monthly-section-title {
  font-size: var(--font-sm);
  color: var(--accent);
  margin: 0 0 var(--space-sm);
}

.monthly-card-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: var(--space-md);
}

.monthly-card-wrapper {
  display: flex;
  flex-direction: column;
}

.monthly-card {
  display: grid;
  grid-template-columns: 16px 36px 1fr 32px;
  align-items: center;
  gap: var(--space-sm);
  width: 100%;
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-sm);
  border: 1px solid transparent;
  border-left: 3px solid transparent;
  cursor: pointer;
  transition: background-color 0.2s, border-color 0.2s;
  font: inherit;
  color: inherit;
  text-align: left;
}

.monthly-card:hover {
  background: rgba(0, 0, 0, 0.03);
  border-color: var(--border);
  border-left-color: transparent;
}

.monthly-card:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.monthly-card.expanded {
  background: var(--bg-elevated);
  border-color: var(--accent);
  border-left-color: var(--accent);
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
}

.monthly-card.is-current-month {
  border-left-color: var(--accent);
  background: rgba(139, 105, 20, 0.05);
}

.monthly-card-toggle {
  width: 16px;
  font-size: var(--font-xs);
  color: var(--text-secondary);
  flex-shrink: 0;
}

.monthly-card-detail {
  background: var(--bg-elevated);
  border: 1px solid var(--accent);
  border-top: none;
  border-radius: 0 0 var(--radius-md) var(--radius-md);
  padding: var(--space-md);
  animation: slideDown 0.2s ease;
}

.monthly-month {
  font-size: var(--font-xs);
  color: var(--text-secondary);
  text-align: right;
  flex-shrink: 0;
}

.monthly-card.is-current-month .monthly-month {
  color: var(--accent);
  font-weight: 600;
}

.monthly-bar-wrapper {
  height: 8px;
  background: var(--bg-primary);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.monthly-bar-fill {
  height: 100%;
  border-radius: var(--radius-sm);
  transition: width 0.5s ease;
}

.monthly-bar-fill.excellent { background: var(--stellar); }
.monthly-bar-fill.good { background: var(--success); }
.monthly-bar-fill.fair { background: var(--info); }
.monthly-bar-fill.caution { background: var(--caution); }
.monthly-bar-fill.warning { background: var(--warning); }

.monthly-score {
  font-size: var(--font-xs);
  font-variant-numeric: tabular-nums;
  text-align: right;
  flex-shrink: 0;
}

.monthly-score.excellent { color: var(--stellar); font-weight: 600; }
.monthly-score.good { color: var(--success); font-weight: 600; }
.monthly-score.fair { color: var(--info); }
.monthly-score.caution { color: var(--caution); }
.monthly-score.warning { color: var(--warning); }

.monthly-special-days {
  display: flex;
  gap: 2px;
  flex-shrink: 0;
}

.sd-badge {
  font-size: 10px;
  padding: 1px 4px;
  border-radius: var(--radius-sm);
  font-weight: 600;
  line-height: 1.3;
}

.sd-badge.kanro { background: rgba(74, 155, 107, 0.25); color: var(--kanro-color); }
.sd-badge.kongou { background: rgba(212, 175, 55, 0.25); color: var(--kongou-color); }
.sd-badge.rasetsu { background: rgba(232, 93, 76, 0.25); color: var(--rasetsu-color); }

.monthly-tip {
  grid-column: 1 / -1;
  font-size: var(--font-xs);
  color: var(--text-secondary);
  line-height: 1.5;
  margin: 0;
  padding-left: calc(16px + 36px + var(--space-sm) * 2);
}

.yearly-chart-wrapper {
  margin-bottom: var(--space-md);
}

.yearly-chart {
  width: 100%;
  min-width: 480px;
  height: auto;
  display: block;
}

/* ============================================================
   Decade (流年) Tab
   ============================================================ */
/* 當年摘要 */
.current-year-summary {
  padding: var(--space-md);
  background: linear-gradient(135deg, var(--bg-elevated) 0%, var(--bg-surface) 100%);
  border: 1px solid var(--accent);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-lg);
}

.current-year-title {
  font-size: var(--font-lg);
  margin: 0 0 var(--space-sm);
  color: var(--accent);
}

.current-year-kuyou {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
}

.current-year-kuyou .kuyou-name {
  font-weight: 600;
}

.current-year-score {
  font-size: var(--font-xl);
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  margin-left: auto;
}

.current-year-desc {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0 0 var(--space-sm);
}

.current-year-scores {
  display: flex;
  gap: var(--space-md);
  flex-wrap: wrap;
}

.mini-score-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.mini-score-item .mini-label {
  font-size: var(--font-xs);
  color: var(--text-secondary);
}

.mini-score-item .mini-value {
  font-size: var(--font-base);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.decade-nav {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-md);
  margin-bottom: var(--space-md);
}

.decade-nav-btn {
  padding: var(--space-xs) var(--space-md);
  min-height: 44px;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: var(--font-sm);
  cursor: pointer;
  transition: border-color 0.2s, color 0.2s;
}

.decade-nav-btn:hover {
  border-color: var(--accent);
  color: var(--text-primary);
}

.decade-nav-btn:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.decade-range {
  font-size: var(--font-lg);
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--text-primary);
}

/* 九曜循環 */
.kuyou-cycle {
  margin-bottom: var(--space-md);
}

.kuyou-cycle-title {
  font-size: var(--font-sm);
  color: var(--accent);
  margin: 0 0 var(--space-sm);
}

.kuyou-cycle-grid {
  display: flex;
  gap: 4px;
  overflow-x: auto;
  padding-bottom: var(--space-xs);
  -webkit-overflow-scrolling: touch;
  scrollbar-width: thin;
}

.kuyou-cycle-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: var(--space-xs) var(--space-sm);
  background: var(--bg-elevated);
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  min-width: 52px;
  flex-shrink: 0;
}

.kuyou-cycle-cell.is-current-year {
  border-color: var(--accent);
  background: rgba(139, 105, 20, 0.06);
}

.cycle-year {
  font-size: var(--font-xs);
  color: var(--text-secondary);
  font-variant-numeric: tabular-nums;
}

.cycle-star {
  font-size: var(--font-sm);
  font-weight: 600;
  color: var(--text-primary);
}

.cycle-level {
  font-size: 11px;
}

/* SVG 圖表 */
.decade-chart-wrapper {
  margin-bottom: var(--space-md);
}

.chart-title {
  font-size: var(--font-sm);
  color: var(--accent);
  margin: 0 0 var(--space-sm);
}

.chart-scroll-container {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: thin;
}

.decade-chart {
  width: 100%;
  min-width: 480px;
  height: auto;
  display: block;
}

/* 年度卡片 */
.decade-cards {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.decade-card {
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.decade-card.is-current-year {
  border-color: var(--accent);
}

.decade-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-elevated);
  border: none;
  cursor: pointer;
  font: inherit;
  color: inherit;
  transition: background-color 0.2s;
  min-height: 44px;
}

.decade-card-header:hover {
  background: var(--bg-primary);
}

.decade-card-header:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.card-header-left {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

.card-year {
  font-weight: 700;
  font-size: var(--font-base);
  font-variant-numeric: tabular-nums;
}

.card-star {
  font-size: var(--font-sm);
  color: var(--text-secondary);
}

.card-header-right {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.mini-score {
  font-size: var(--font-base);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.mini-score.excellent { color: var(--stellar); }
.mini-score.good { color: var(--success); }
.mini-score.fair { color: var(--info); }
.mini-score.caution { color: var(--caution); }
.mini-score.warning { color: var(--warning); }

.card-toggle {
  width: 16px;
  font-size: var(--font-xs);
  color: var(--text-secondary);
}

.decade-card-detail {
  padding: var(--space-md);
  background: var(--bg-surface);
  border-top: 1px solid var(--border);
  animation: slideDown 0.2s ease;
}

.card-scores {
  margin-bottom: var(--space-md);
}

.card-buddha {
  font-size: var(--font-xs);
  color: var(--text-secondary);
  font-style: italic;
  margin: 0 0 var(--space-sm);
}

.card-theme {
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-sm);
}

.card-theme strong {
  display: block;
  font-size: var(--font-sm);
  color: var(--accent);
  margin-bottom: var(--space-xs);
}

.card-theme p {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0;
}

.card-advice {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0;
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  border-left: 3px solid var(--accent);
}

/* 視角切換 */
.perspective-toggle {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 4px;
  margin-bottom: var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-full);
  padding: 3px;
  width: fit-content;
  margin-left: auto;
  margin-right: auto;
}

.export-btn {
  padding: var(--space-xs) var(--space-md);
  min-height: 36px;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius-full);
  color: var(--text-secondary);
  font-size: var(--font-sm);
  cursor: pointer;
  transition: background-color 0.2s, border-color 0.2s, color 0.2s;
  white-space: nowrap;
  margin-left: var(--space-sm);
}

.export-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.export-btn:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.perspective-btn {
  padding: var(--space-xs) var(--space-md);
  min-height: 36px;
  background: transparent;
  border: none;
  border-radius: var(--radius-full);
  color: var(--text-secondary);
  font-size: var(--font-sm);
  cursor: pointer;
  transition: background-color 0.2s, color 0.2s;
  white-space: nowrap;
}

.perspective-btn:hover {
  color: var(--text-primary);
}

.perspective-btn.active {
  background: var(--accent);
  color: var(--text-on-accent);
}

.perspective-btn:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

/* 修行者觀色標 */
.practice-level {
  font-size: var(--font-xs);
  font-weight: 700;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
}

.practice-level.level-dharma {
  background: rgba(255, 183, 0, 0.2);
  color: #b8860b;
}

.practice-level.level-growth {
  background: rgba(80, 180, 80, 0.2);
  color: #2e7d32;
}

.practice-level.level-harmony {
  background: rgba(100, 150, 220, 0.2);
  color: #1565c0;
}

.practice-level.level-diligent {
  background: rgba(123, 31, 162, 0.2);
  color: #4A3B6B;
}

/* 真言宗修行資料 */
.shingon-mantra-box {
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-sm);
  border-left: 3px solid #4A3B6B;
  overflow: hidden;
}

.mantra-bija-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: var(--space-md) var(--space-md) var(--space-sm);
  border-bottom: 1px solid var(--border);
}

.bija-siddham {
  font-family: 'Noto Sans Siddham', serif;
  font-size: 2.5rem;
  line-height: 1.2;
  color: #4A3B6B;
}

.bija-iast {
  font-size: 0.75rem;
  color: var(--text-secondary);
  font-style: italic;
}

.bija-buddha {
  font-size: 0.875rem;
  font-weight: 700;
  color: var(--text-primary);
}

.mantra-text-section {
  padding: var(--space-sm) var(--space-md);
}

.mantra-label {
  font-size: var(--font-xs);
  color: #4A3B6B;
  font-weight: 600;
  margin: 0 0 var(--space-xs);
}

.mantra-text {
  font-size: var(--font-sm);
  color: var(--text-primary);
  line-height: 1.8;
  margin: 0 0 var(--space-xs);
  word-break: keep-all;
  overflow-wrap: break-word;
}

.mantra-reading {
  font-size: var(--font-xs);
  color: var(--text-secondary);
  margin: 0;
  word-break: keep-all;
  overflow-wrap: break-word;
}

.shingon-homa-box {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
  flex-wrap: wrap;
}

.homa-type {
  font-size: var(--font-xs);
  font-weight: 600;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  background: rgba(123, 31, 162, 0.15);
  color: #4A3B6B;
  white-space: nowrap;
}

.homa-desc {
  font-size: var(--font-xs);
  color: var(--text-secondary);
}

.practice-focus-text {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  margin: 0 0 var(--space-sm);
  font-style: italic;
}

.core-teaching-box {
  padding: var(--space-sm) var(--space-md);
  background: rgba(123, 31, 162, 0.06);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-sm);
  border-left: 3px solid rgba(123, 31, 162, 0.3);
}

.core-teaching-box p {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0;
  font-style: italic;
}

.recommended-practices {
  margin-bottom: var(--space-sm);
}

.recommended-practices h5 {
  font-size: var(--font-xs);
  color: #4A3B6B;
  margin: 0 0 var(--space-xs);
}

.practice-tags {
  display: flex;
  gap: var(--space-xs);
  flex-wrap: wrap;
}

.practice-tag {
  font-size: var(--font-xs);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  background: rgba(123, 31, 162, 0.1);
  color: #4A3B6B;
}

/* Responsive */
@media (min-width: 1024px) {
  .decade-cards {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 767px) {
  .fortune-card {
    padding: var(--space-sm);
  }

  .score-desc {
    padding-left: calc(40px + var(--space-sm));
  }

  .score-label {
    width: 40px;
  }

  .lucky-info {
    gap: var(--space-sm);
  }

  .lucky-item {
    min-width: calc(50% - var(--space-sm));
  }

  .daily-item {
    min-width: 48px;
    padding: var(--space-xs);
  }

  .day-score {
    font-size: var(--font-base);
  }

  .weekly-item {
    padding: var(--space-sm);
    gap: var(--space-xs);
  }

  .week-num {
    width: 48px;
    font-size: var(--font-xs);
  }

  .trend-month {
    width: 28px;
  }

  .kuyou-star-box {
    padding: var(--space-sm);
  }

  .kuyou-cycle-grid {
    mask-image: linear-gradient(to right, transparent, black 8px, black calc(100% - 24px), transparent);
    -webkit-mask-image: linear-gradient(to right, transparent, black 8px, black calc(100% - 24px), transparent);
  }

  .decade-chart {
    min-width: 520px;
  }

  .chart-scroll-container {
    mask-image: linear-gradient(to right, transparent, black 8px, black calc(100% - 24px), transparent);
    -webkit-mask-image: linear-gradient(to right, transparent, black 8px, black calc(100% - 24px), transparent);
  }

  .decade-nav-btn {
    padding: var(--space-xs) var(--space-sm);
    font-size: var(--font-xs);
  }

  .decade-range {
    font-size: var(--font-base);
  }
}

@media (prefers-reduced-motion: reduce) {
  .fortune-content {
    animation: none;
  }

  .score-fill {
    transition: none;
  }

  .decade-card-detail {
    animation: none;
  }
}

/* === Strategy Section === */
.strategy-section {
  margin-top: var(--space-lg);
  padding: var(--space-md);
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border);
}

.strategy-title {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 var(--space-md) 0;
}

.strategy-block {
  margin-bottom: var(--space-md);
  padding-bottom: var(--space-sm);
  border-bottom: 1px solid var(--border-light, rgba(128, 128, 128, 0.15));
}

.strategy-block:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.strategy-block-header {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  margin-bottom: var(--space-xs);
  flex-wrap: wrap;
}

.strategy-icon {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.safe-icon { color: #50b050; }
.best-icon { color: var(--accent); }
.caution-icon { color: #e07040; }
.ryouhan-icon { color: #cc4444; }

.strategy-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-primary);
}

.rhythm-halves,
.ryouhan-months-list {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-left: auto;
}

.strategy-desc {
  font-size: 0.82rem;
  color: var(--text-secondary);
  line-height: 1.5;
  margin: var(--space-xs) 0 0 0;
}

.strategy-item {
  display: flex;
  align-items: baseline;
  gap: var(--space-xs);
  flex-wrap: wrap;
  margin-top: var(--space-xs);
}

.strategy-months {
  font-size: 0.78rem;
  font-weight: 600;
  padding: 1px 8px;
  border-radius: 10px;
  white-space: nowrap;
}

.safe-tag {
  background: rgba(80, 176, 80, 0.12);
  color: #50b050;
}

.best-tag {
  background: rgba(var(--accent-rgb, 59, 130, 246), 0.12);
  color: var(--accent);
}

.caution-tag {
  background: rgba(224, 112, 64, 0.12);
  color: #e07040;
}

.strategy-score {
  font-size: 0.82rem;
  font-weight: 600;
}

.strategy-avg {
  font-size: 0.78rem;
  color: var(--text-secondary);
}

.strategy-item-desc {
  font-size: 0.8rem;
  color: var(--text-secondary);
  line-height: 1.4;
  margin: 0;
  flex-basis: 100%;
}

/* Monthly Strategy */
.strategy-days-row {
  display: flex;
  gap: var(--space-md);
  flex-wrap: wrap;
}

.strategy-days-col {
  flex: 1;
  min-width: 140px;
}

.best-label { color: #50b050; }
.caution-label { color: #e07040; }

.strategy-day-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: var(--space-xs);
}

.strategy-day-tag {
  font-size: 0.75rem;
  padding: 2px 8px;
  border-radius: 8px;
  white-space: nowrap;
}

.best-day-tag {
  background: rgba(80, 176, 80, 0.12);
  color: #50b050;
}

.avoid-day-tag {
  background: rgba(224, 112, 64, 0.12);
  color: #e07040;
}

/* === 經文引用區塊 === */
.practice-scripture {
  margin-top: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  background: rgba(123, 31, 162, 0.06);
  border-radius: var(--radius-md);
  border-left: 3px solid rgba(123, 31, 162, 0.3);
}

.practice-scripture.ryouhan-scripture {
  margin-top: var(--space-xs);
  border-left-color: #cc4444;
  background: rgba(204, 68, 68, 0.06);
}

.practice-scripture.sanki-scripture {
  margin-top: var(--space-sm);
}

.scripture-text {
  font-size: var(--font-sm);
  color: var(--text-primary);
  line-height: 1.6;
  margin: 0 0 var(--space-xs);
  font-style: italic;
}

.scripture-source {
  font-size: var(--font-xs);
  color: var(--text-secondary);
}

/* === 月度修行里程碑 === */
.monthly-milestones {
  margin-top: var(--space-lg);
  padding: var(--space-md);
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border);
}

.milestones-title {
  font-size: 1rem;
  font-weight: 700;
  color: #4A3B6B;
  margin: 0 0 var(--space-md) 0;
}

.milestone-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.milestone-item {
  display: flex;
  align-items: baseline;
  gap: var(--space-sm);
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
}

.milestone-item.is-current-month {
  background: rgba(123, 31, 162, 0.08);
}

.milestone-month {
  font-size: var(--font-sm);
  font-weight: 600;
  color: #4A3B6B;
  min-width: 36px;
  flex-shrink: 0;
}

.milestone-text {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  line-height: 1.5;
}

/* 訂閱按鈕 */
.subscribe-btn {
  background: var(--bg-elevated);
  border-color: var(--accent);
  color: var(--accent);
}

.subscribe-btn:hover {
  background: var(--accent);
  color: var(--bg-surface);
}

/* 訂閱 Dialog */
.subscribe-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 16px;
}

.subscribe-dialog {
  position: relative;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg, 12px);
  padding: 24px;
  max-width: 420px;
  width: 100%;
}

.subscribe-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 8px;
}

.subscribe-desc {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0 0 20px;
}

.subscribe-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.subscribe-action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 16px;
  border-radius: var(--radius-md, 8px);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid var(--border);
  background: var(--bg-elevated);
  color: var(--text-primary);
  min-height: 44px;
  transition: background-color 0.2s;
}

.subscribe-action-btn:hover {
  background: var(--bg-surface);
}

.subscribe-action-btn.primary {
  background: var(--accent);
  color: var(--bg-surface);
  border-color: var(--accent);
}

.subscribe-action-btn.primary:hover {
  opacity: 0.9;
}

.subscribe-url-box {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm, 4px);
  padding: 8px 12px;
  margin-bottom: 12px;
  overflow-x: auto;
}

.subscribe-url {
  font-size: 11px;
  color: var(--text-secondary);
  word-break: break-all;
  line-height: 1.4;
}

.subscribe-hint {
  font-size: 12px;
  color: var(--text-muted, var(--text-secondary));
  line-height: 1.6;
  margin: 0;
}

.subscribe-close {
  position: absolute;
  top: 12px;
  right: 12px;
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 4px;
  min-width: 44px;
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.subscribe-close:hover {
  color: var(--text-primary);
}
</style>
