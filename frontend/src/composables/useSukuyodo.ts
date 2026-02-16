import { ref, computed, watch } from 'vue'
import { useProfile } from '../stores/profile'
import { getApiUrl } from '../config/api'

// ============================================================================
// Type Definitions
// ============================================================================

export interface LifeStages {
  twenties: string
  thirties: string
  forties: string
  fifties_plus: string
}

export interface Mansion {
  index: number
  name_jp: string
  name_zh: string
  reading: string
  element: string
  personality: string
  keywords: string[]
  love: string
  career: string
  health: string
  life_stages?: LifeStages
  seasonal?: string
  lunar_date?: {
    year: number
    month: number
    day: number
    display: string
  }
}

export interface Relation {
  type: string
  name: string
  name_jp: string
  reading: string
  description: string
  detailed: string
  advice: string
  tips: string[]
  avoid: string[]
  good_for: string[]
  distance_type?: 'near' | 'mid' | 'far' | null
  distance_type_name?: string
  direction?: string | null
  love?: string
  career?: string
  roles?: Record<string, string>
}

export interface Person {
  date: string
  mansion: string
  reading: string
  element: string
  element_reading: string
  element_traits: string
  keywords: string[]
  index: number
}

export interface Calculation {
  distance: number
  formula: string
  element_relation: string
}

export interface CompatibilityResult {
  person1: Person
  person2: Person
  relation: Relation
  calculation: Calculation
  score: number
  element_bonus: number
  summary: string
}

export interface FortuneScores {
  overall: number
  career: number
  love: number
  health: number
  wealth: number
  career_desc?: string
  love_desc?: string
  health_desc?: string
  wealth_desc?: string
}

export interface MansionRelation {
  type: string
  name: string
  reading: string
  description: string
}

export interface DailyFortune {
  date: string
  weekday: {
    name: string
    reading: string
    element: string
    planet: string
  }
  your_mansion: {
    name_jp: string
    reading: string
    element: string
    index: number
  }
  day_mansion: {
    name_jp: string
    reading: string
    element: string
    index: number
  }
  mansion_relation: MansionRelation
  element_relation: {
    type: string
    description: string
  }
  fortune: FortuneScores
  advice: string
  lucky: {
    direction: string
    direction_reading: string
    color: string
    color_reading: string
    color_hex: string
    numbers: number[]
  }
  special_day?: {
    type: string
    name: string
    reading: string
    level: string
    description: string
    ryouhan_reversed?: boolean
    original_level?: string
  } | null
  ryouhan?: {
    active: boolean
    lunar_month: number
    start_day: number
    end_day: number
    description: string
  } | null
  rokugai?: {
    active: boolean
    name: string
    severity: number
    description: string
  } | null
  sanki?: {
    period: string
    period_reading: string
    period_index: number
    day_in_period: number
    is_dark_week: boolean
    day_type: string
    day_type_reading: string
    day_description: string
    period_description: string
  } | null
}

export interface WeeklyFortune {
  center_date: string
  week_start: string
  week_end: string
  today_element: {
    name: string
    reading: string
    element: string
    planet: string
  }
  your_mansion: {
    name_jp: string
    reading: string
    element: string
    index: number
  }
  element_relation: {
    type: string
    description: string
  }
  fortune: FortuneScores
  daily_overview: {
    date: string
    weekday: string
    score: number
    is_today: boolean
    is_yesterday: boolean
  }[]
  advice: string
  focus?: string
  category_tips?: {
    career: string
    love: string
    health: string
  }
  lucky: {
    direction: string
    direction_reading: string
    color: string
    color_reading: string
    color_hex: string
  }
}

export interface MonthlyFortune {
  year: number
  month: number
  month_mansion: {
    name_jp: string
    reading: string
    index: number
    element: string
  }
  your_mansion: {
    name_jp: string
    reading: string
    element: string
    index: number
  }
  relation: {
    type: string
    name: string
    reading: string
    description: string
  }
  theme: {
    title: string
    focus: string
    element_boost: string
  }
  fortune: FortuneScores
  weekly: {
    week: number
    week_start: string
    week_end: string
    score: number
    focus: string
    daily_overview: {
      date: string
      weekday: string
      score: number
    }[]
  }[]
  advice: string
}

export interface YearlyFortune {
  year: number
  kuyou_star: {
    name: string
    reading: string
    level: string
    fortune_name: string
    element: string | null
    buddha: string
    description: string
    kazoe_age: number
  }
  your_mansion: {
    name_jp: string
    reading: string
    element: string
    index: number
  }
  fortune: FortuneScores
  theme?: {
    title: string
    description: string
  }
  category_descriptions?: {
    career: string
    love: string
    health: string
    wealth: string
  }
  monthly_trend: {
    month: number
    score: number
    tip?: string
  }[]
  opportunities: string[]
  warnings: string[]
  advice: string
}

export interface LunarDate {
  lunar_month: number
  lunar_month_name: string
  lunar_day: number
  display: string
  solar_dates?: { lunar_year: number; solar_date: string; display: string }[]
}

export interface CompatibleMansion {
  name_jp: string
  name_zh: string
  reading: string
  index: number
  element: string
  element_reading: string
  keywords: string[]
  personality: string
  lunar_dates: LunarDate[]
}

export interface CompatibilityCategory {
  relation: string
  reading: string
  score: number
  description: string
  detailed?: string
  mansions: CompatibleMansion[]
}

export interface CompatibilityFinderResult {
  your_mansion: {
    name_jp: string
    name_zh: string
    reading: string
    index: number
    element: string
    lunar_date: {
      year: number
      month: number
      day: number
      display: string
    }
  }
  mei: CompatibilityCategory
  gyotai: CompatibilityCategory
  eishin: CompatibilityCategory
  yusui: CompatibilityCategory
  ankai: CompatibilityCategory
  kisei: CompatibilityCategory
}

export interface LuckyDayAction {
  key: string
  name: string
}

export interface LuckyDayCategory {
  key: string
  name: string
  icon: string
  actions: LuckyDayAction[]
}

export interface LuckyDay {
  date: string
  weekday: string
  score: number
  rating?: string
  reason: string
  best_time?: string
  avoid_time?: string
  tip?: string
}

export interface LuckyDayResult {
  category: string
  category_name: string
  action: string
  action_name: string
  your_mansion: {
    name_jp: string
    reading: string
    element: string
  }
  lucky_days: LuckyDay[]
  avoid_days: LuckyDay[]
  advice: string
}

export interface LuckyDaySummaryItem {
  name: string
  lucky_days: LuckyDay[]
}

export interface LuckyDaySummary {
  your_mansion: Mansion
  summary: LuckyDaySummaryItem[]
}

export interface PairLuckyAction {
  action: string
  name: string
  lucky_days: LuckyDay[]
}

// 日本選日曆注型別
export interface JapaneseLuckyDay {
  date: string
  weekday: string
  types: string[]
  labels: string[]
  descriptions?: string[]
  is_super_lucky: boolean
  stem_branch: string
  rokuyo: string
}

export interface JapaneseUnluckyDay {
  date: string
  weekday: string
  type: string
  label: string
  stem_branch: string
  rokuyo: string
}

export interface JapaneseCalendarSummary {
  tensya_count: number
  ichiryumanbai_count: number
  tora_count: number
  mi_count: number
  super_lucky_count: number
  fujoubyou_count: number
}

export interface DayTypeDescription {
  name: string
  reading: string
  short: string
  description: string
}

export interface JapaneseCalendarResult {
  year: number
  month: number
  days: JapaneseLuckyDay[]
  unlucky_days: JapaneseUnluckyDay[]
  summary: JapaneseCalendarSummary
  day_type_descriptions?: Record<string, DayTypeDescription>
}

export interface PairLuckyDaysResult {
  relation_type: string
  relation_name: string
  person1: {
    mansion: string
    reading: string
    element: string
  }
  person2: {
    mansion: string
    reading: string
    element: string
  }
  compatibility: {
    relation: string
    score: number
    description: string
  }
  actions: PairLuckyAction[]
}

export interface SpecialDay {
  date: string
  weekday: string
  type: string
  name: string
  reading: string
  level: string
  mansion: string
  mansion_reading: string
  description: string
  ryouhan_reversed?: boolean
}

export interface SpecialDaysResult {
  year: number
  month: number
  days: SpecialDay[]
  summary: {
    kanro_count: number
    kongou_count: number
    rasetsu_count: number
  }
}

export interface WheelMansion {
  index: number
  name_jp: string
  name_zh: string
  reading: string
  element: string
  personality?: string
  keywords?: string[]
}

export interface RelationType {
  type: string
  name: string
  name_jp: string
  reading: string
  score: number
  description: string
  detailed: string
  advice: string
  tips: string[]
  avoid: string[]
  good_for: string[]
}

export interface ElementType {
  name: string
  reading: string
  planet: string
  traits: string
  energy: string
  description: string
  detailed_traits?: string
  interactions?: string
  life_advice?: string
}

export interface HistoryEntry {
  title: string
  content: string
}

export interface MonthMansionEntry {
  month: number
  name: string
  start_mansion: string
  start_index: number
  reading: string
}

export interface MonthMansionTable {
  calendar_description: string
  months: MonthMansionEntry[]
}

export interface PartnerCompatibility {
  partnerId: string
  nickname: string
  birthDate: string
  mansion: {
    name_jp: string
    reading: string
    element: string
  }
  relation: Relation
  score: number
  element_bonus: number
  summary: string
  calculation: {
    distance: number
    element_relation: string
    person1_element?: string
    person2_element?: string
  }
}

export interface KeyConcept {
  title: string
  content: string
}

export interface PracticalGuide {
  title: string
  content: string
}

export interface KnowledgeSection {
  title: string
  content: string
}

export interface KnowledgeTable {
  description: string
  headers: string[]
  rows: string[][]
}

export interface SpecialDaysKnowledge {
  title: string
  sections: KnowledgeSection[]
  day_map_table: KnowledgeTable
}

export interface KuyouKnowledge {
  title: string
  sections: KnowledgeSection[]
  stars_table: KnowledgeTable
}

export interface Metadata {
  name: string
  reading: string
  origin: string
  origin_reading: string
  founder: string
  founder_reading: string
  scripture: string
  scripture_reading: string
  method: string
  method_reading: string
  history?: HistoryEntry[]
  key_concepts?: KeyConcept[]
  practical_guide?: PracticalGuide[]
  special_days_knowledge?: SpecialDaysKnowledge
  kuyou_knowledge?: KuyouKnowledge
  ryouhan_knowledge?: {
    title: string
    sections: { title: string; content: string }[]
    ryouhan_table?: {
      description: string
      headers: string[]
      rows: string[][]
    }
  }
  sanki_knowledge?: {
    title: string
    sections: { title: string; content: string }[]
  }
  month_mansion_table?: MonthMansionTable
}

// ============================================================================
// Composable
// ============================================================================

export function useSukuyodo() {
  const { myBirthDate, profile } = useProfile()

  // 計算有填寫生日的對象
  const partnersWithBirthDate = computed(() => {
    return profile.value.partners.filter(p => p.birthDate)
  })

  // Tab Navigation
  const activeMainTab = ref<'fortune' | 'match' | 'lucky' | 'knowledge'>('fortune')
  const activeFortuneTab = ref<'daily' | 'weekly' | 'monthly' | 'yearly'>('daily')
  const activeMatchTab = ref<'finder' | 'compat' | 'partners'>('finder')
  const activeKnowledgeTab = ref<'mansion' | 'wheel' | 'relations' | 'elements' | 'special-days' | 'kuyou' | 'ryouhan' | 'sanki' | 'calendar' | 'history'>('mansion')

  // Query UI
  const showQueryDialog = ref(false)
  const birthDate = ref('')
  const lookupLoading = ref(false)
  const lookupError = ref('')

  // Mansion Data
  const mansion = ref<Mansion | null>(null)
  const metadata = ref<Metadata | null>(null)
  const allMansions = ref<WheelMansion[]>([])
  const allRelations = ref<RelationType[]>([])
  const allElements = ref<ElementType[]>([])
  const selectedWheelMansion = ref<WheelMansion | null>(null)

  // Fortune Data
  const dailyFortune = ref<DailyFortune | null>(null)
  const weeklyFortune = ref<WeeklyFortune | null>(null)
  const monthlyFortune = ref<MonthlyFortune | null>(null)
  const yearlyFortune = ref<YearlyFortune | null>(null)
  const fortuneLoading = ref(false)

  // Monthly Week Expansion
  const expandedMonthlyWeek = ref<number | null>(null)

  // Compatibility
  const compatFinder = ref<CompatibilityFinderResult | null>(null)
  const finderLoading = ref(false)
  const selectedMansion = ref<CompatibleMansion | null>(null)

  // Pair Diagnosis
  const date2 = ref('')
  const compatibility = ref<CompatibilityResult | null>(null)
  const compatLoading = ref(false)
  const compatError = ref('')

  // Partner Compatibilities
  const partnerCompatibilities = ref<PartnerCompatibility[]>([])
  const partnerCompatLoading = ref(false)

  // Lucky Days
  const luckyDayCategories = ref<LuckyDayCategory[]>([])
  const selectedLuckyCategory = ref<string | null>(null)
  const selectedLuckyAction = ref<string | null>(null)
  const luckyDayResult = ref<LuckyDayResult | null>(null)
  const luckyDayLoading = ref(false)
  const luckyDaySummary = ref<LuckyDaySummary | null>(null)
  const luckyDaySummaryLoading = ref(false)

  // Pair Lucky Days
  const activeLuckyTab = ref<'personal' | 'pair'>('personal')
  const selectedPartnerId = ref<string | null>(null)
  const pairLuckyDays = ref<PairLuckyDaysResult | null>(null)
  const pairLuckyDaysLoading = ref(false)

  // Japanese Calendar (選日曆注)
  const japaneseCalendar = ref<JapaneseCalendarResult | null>(null)
  const japaneseCalendarLoading = ref(false)

  // Special Days (宿曜特殊日)
  const specialDays = ref<SpecialDaysResult | null>(null)
  const specialDaysLoading = ref(false)

  // Knowledge
  const expandedRelation = ref<string | null>(null)

  // ============================================================================
  // Computed
  // ============================================================================

  const elementColors: Record<string, string> = {
    '日': '#C4A052',
    '月': '#8B7355',
    '火': '#E85D4C',
    '水': '#5B8FA8',
    '木': '#7CB3D9',
    '金': '#E89B3C',
    '土': '#a8a29e'
  }

  const mansionElementColor = computed(() => {
    return mansion.value ? elementColors[mansion.value.element] || '#f59e0b' : '#f59e0b'
  })

  const currentCategoryActions = computed(() => {
    if (!selectedLuckyCategory.value) return []
    const cat = luckyDayCategories.value.find(c => c.key === selectedLuckyCategory.value)
    return cat?.actions || []
  })

  const relationKeys = [
    { key: 'eishin', cssClass: 'excellent' },
    { key: 'gyotai', cssClass: 'good' },
    { key: 'mei', cssClass: 'fair' },
    { key: 'kisei', cssClass: 'caution' },
    { key: 'yusui', cssClass: 'neutral' },
    { key: 'ankai', cssClass: 'warning' }
  ]

  // ============================================================================
  // Helper Functions
  // ============================================================================

  function getFortuneLevel(score: number) {
    if (score >= 90) return { text: '大吉', class: 'excellent' }
    if (score >= 75) return { text: '吉', class: 'good' }
    if (score >= 60) return { text: '中吉', class: 'fair' }
    if (score >= 45) return { text: '小吉', class: 'caution' }
    return { text: '凶', class: 'warning' }
  }

  function getMansionRelationClass(relationType: string) {
    const classMap: Record<string, string> = {
      'eishin': 'excellent',
      'gyotai': 'good',
      'mei': 'fair',
      'yusui': 'neutral',
      'kisei': 'caution',
      'ankai': 'warning'
    }
    return classMap[relationType] || 'neutral'
  }

  function getScoreClass(score: number) {
    if (score >= 90) return 'excellent'
    if (score >= 75) return 'good'
    if (score >= 60) return 'fair'
    if (score >= 45) return 'caution'
    return 'warning'
  }

  function getScoreLevel(score: number) {
    if (score >= 90) return { text: '天作之合', class: 'excellent' }
    if (score >= 75) return { text: '相當不錯', class: 'good' }
    if (score >= 60) return { text: '需要磨合', class: 'fair' }
    return { text: '多加小心', class: 'warning' }
  }

  function formatDate(dateStr: string) {
    const d = new Date(dateStr)
    return `${d.getMonth() + 1}/${d.getDate()}`
  }

  // ============================================================================
  // API Functions
  // ============================================================================

  async function lookupMansion() {
    if (!birthDate.value) return

    lookupLoading.value = true
    lookupError.value = ''
    mansion.value = null
    compatFinder.value = null
    selectedMansion.value = null
    dailyFortune.value = null
    weeklyFortune.value = null
    monthlyFortune.value = null
    yearlyFortune.value = null
    luckyDayResult.value = null

    try {
      const res = await fetch(getApiUrl(`/mansion/${birthDate.value}`))
      if (res.ok) {
        const data = await res.json()
        if (data.success) {
          mansion.value = data.data
          showQueryDialog.value = false
          // 只在非對象日期時儲存（避免覆蓋自己的生日）
          const isPartnerDate = profile.value.partners.some(p => p.birthDate === birthDate.value)
          if (!isPartnerDate) {
            profile.value.birthDate = birthDate.value
          }
          fetchCompatibleMansions()
          fetchAllFortunes()
          fetchLuckyDaySummary()
          fetchJapaneseCalendar()
          fetchSpecialDays()
        } else {
          lookupError.value = data.error || '查詢失敗'
        }
      } else {
        const err = await res.json()
        lookupError.value = err.detail || '查詢失敗'
      }
    } catch {
      lookupError.value = '無法連線到伺服器'
    } finally {
      lookupLoading.value = false
    }
  }

  async function fetchCompatibleMansions() {
    if (!birthDate.value) return
    finderLoading.value = true

    try {
      const res = await fetch(getApiUrl(`/compatibility-finder/${birthDate.value}`))
      if (res.ok) {
        const data = await res.json()
        if (data.success) {
          compatFinder.value = data.data
        }
      }
    } catch {
      console.error('Failed to fetch compatible mansions')
    } finally {
      finderLoading.value = false
    }
  }

  async function fetchDailyFortune() {
    if (!birthDate.value) return
    fortuneLoading.value = true

    const today = new Date().toISOString().split('T')[0]
    try {
      const res = await fetch(getApiUrl(`/fortune/daily/${today}?birth_date=${birthDate.value}`))
      if (res.ok) {
        const data = await res.json()
        if (data.success) {
          dailyFortune.value = data.data
        }
      }
    } catch {
      console.error('Failed to fetch daily fortune')
    } finally {
      fortuneLoading.value = false
    }
  }

  async function fetchDailyFortuneForDate(targetDate: string) {
    if (!birthDate.value) return
    fortuneLoading.value = true

    try {
      const res = await fetch(getApiUrl(`/fortune/daily/${targetDate}?birth_date=${birthDate.value}`))
      if (res.ok) {
        const data = await res.json()
        if (data.success) {
          dailyFortune.value = data.data
          activeFortuneTab.value = 'daily'
        }
      }
    } catch {
      console.error('Failed to fetch daily fortune for date')
    } finally {
      fortuneLoading.value = false
    }
  }

  async function fetchWeeklyFortune() {
    if (!birthDate.value) return
    fortuneLoading.value = true

    // 使用今天作為中心日期（滾動視窗）
    const today = new Date().toISOString().split('T')[0]

    try {
      const res = await fetch(getApiUrl(`/fortune/weekly/${today}?birth_date=${birthDate.value}`))
      if (res.ok) {
        const data = await res.json()
        if (data.success) {
          weeklyFortune.value = data.data
        }
      }
    } catch {
      console.error('Failed to fetch weekly fortune')
    } finally {
      fortuneLoading.value = false
    }
  }

  // 計算當月第幾週（用於標示「本週」）
  const currentWeekNumber = computed(() => {
    const today = new Date()
    return Math.ceil(today.getDate() / 7)
  })

  // 切換月運勢中的週次展開（資料已內嵌，無需額外 fetch）
  function toggleMonthlyWeek(week: number) {
    if (expandedMonthlyWeek.value === week) {
      expandedMonthlyWeek.value = null
    } else {
      expandedMonthlyWeek.value = week
    }
  }

  async function fetchMonthlyFortune() {
    if (!birthDate.value) return
    fortuneLoading.value = true

    const now = new Date()
    try {
      const res = await fetch(getApiUrl(`/fortune/monthly/${now.getFullYear()}/${now.getMonth() + 1}?birth_date=${birthDate.value}`))
      if (res.ok) {
        const data = await res.json()
        if (data.success) {
          monthlyFortune.value = data.data
          // 預設展開當前週
          if (expandedMonthlyWeek.value === null) {
            expandedMonthlyWeek.value = currentWeekNumber.value
          }
        }
      }
    } catch {
      console.error('Failed to fetch monthly fortune')
    } finally {
      fortuneLoading.value = false
    }
  }

  async function fetchYearlyFortune() {
    if (!birthDate.value) return
    fortuneLoading.value = true

    const year = new Date().getFullYear()
    try {
      const res = await fetch(getApiUrl(`/fortune/yearly/${year}?birth_date=${birthDate.value}`))
      if (res.ok) {
        const data = await res.json()
        if (data.success) {
          yearlyFortune.value = data.data
        }
      }
    } catch {
      console.error('Failed to fetch yearly fortune')
    } finally {
      fortuneLoading.value = false
    }
  }

  async function fetchAllFortunes() {
    await Promise.all([
      fetchDailyFortune(),
      fetchWeeklyFortune(),
      fetchMonthlyFortune(),
      fetchYearlyFortune()
    ])
  }

  async function fetchLuckyDayCategories() {
    try {
      const res = await fetch(getApiUrl('/lucky-days/categories'))
      if (res.ok) {
        const data = await res.json()
        if (data.success) {
          luckyDayCategories.value = data.categories
        }
      }
    } catch {
      console.error('Failed to fetch lucky day categories')
    }
  }

  async function fetchLuckyDays() {
    const queryDate = birthDate.value || myBirthDate.value
    if (!queryDate || !selectedLuckyCategory.value || !selectedLuckyAction.value) return

    luckyDayLoading.value = true
    luckyDayResult.value = null

    try {
      const res = await fetch(
        getApiUrl(`/lucky-days/${queryDate}?category=${selectedLuckyCategory.value}&action=${selectedLuckyAction.value}`)
      )
      if (res.ok) {
        const data = await res.json()
        if (data.success) {
          luckyDayResult.value = data.data
        }
      }
    } catch {
      console.error('Failed to fetch lucky days')
    } finally {
      luckyDayLoading.value = false
    }
  }

  async function fetchLuckyDaySummary() {
    const queryDate = birthDate.value || myBirthDate.value
    if (!queryDate) return

    luckyDaySummaryLoading.value = true
    luckyDaySummary.value = null

    try {
      const res = await fetch(getApiUrl(`/lucky-days/summary/${queryDate}`))
      if (res.ok) {
        const data = await res.json()
        if (data.success) {
          luckyDaySummary.value = data.data
        }
      }
    } catch {
      console.error('Failed to fetch lucky days summary')
    } finally {
      luckyDaySummaryLoading.value = false
    }
  }

  async function fetchJapaneseCalendar(year?: number, month?: number) {
    const now = new Date()
    const targetYear = year ?? now.getFullYear()
    const targetMonth = month ?? now.getMonth() + 1

    japaneseCalendarLoading.value = true
    japaneseCalendar.value = null

    try {
      const res = await fetch(getApiUrl(`/calendar/lucky-days/${targetYear}/${targetMonth}`))
      if (res.ok) {
        const data = await res.json()
        if (data.success) {
          japaneseCalendar.value = data.data
        }
      }
    } catch {
      console.error('Failed to fetch Japanese calendar')
    } finally {
      japaneseCalendarLoading.value = false
    }
  }

  async function fetchSpecialDays(year?: number, month?: number) {
    const now = new Date()
    const targetYear = year ?? now.getFullYear()
    const targetMonth = month ?? now.getMonth() + 1

    specialDaysLoading.value = true

    try {
      const res = await fetch(getApiUrl(`/special-days/${targetYear}/${targetMonth}`))
      if (res.ok) {
        const data = await res.json()
        if (data.success) {
          specialDays.value = data.data
        }
      }
    } catch {
      console.error('Failed to fetch special days')
    } finally {
      specialDaysLoading.value = false
    }
  }

  async function fetchPairLuckyDays(partnerId: string) {
    const myDate = birthDate.value || myBirthDate.value
    if (!myDate) return

    const partner = profile.value.partners.find(p => p.id === partnerId)
    if (!partner || !partner.birthDate) return

    selectedPartnerId.value = partnerId
    pairLuckyDaysLoading.value = true
    pairLuckyDays.value = null

    try {
      const res = await fetch(
        getApiUrl(`/lucky-days/pair/${myDate}/${partner.birthDate}?relation=${partner.relation}`)
      )
      if (res.ok) {
        const data = await res.json()
        if (data.success) {
          pairLuckyDays.value = data.data
        }
      }
    } catch {
      console.error('Failed to fetch pair lucky days')
    } finally {
      pairLuckyDaysLoading.value = false
    }
  }

  function clearPairSelection() {
    selectedPartnerId.value = null
    pairLuckyDays.value = null
  }

  async function calculateCompatibility() {
    if (!myBirthDate.value || !date2.value) return

    compatLoading.value = true
    compatError.value = ''
    compatibility.value = null

    try {
      const res = await fetch(getApiUrl('/compatibility'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          date1: myBirthDate.value,
          date2: date2.value
        })
      })
      if (res.ok) {
        const data = await res.json()
        if (data.success) {
          compatibility.value = data.data
        } else {
          compatError.value = data.error || '分析失敗'
        }
      } else {
        const err = await res.json()
        compatError.value = err.detail || '分析失敗'
      }
    } catch {
      compatError.value = '無法連線到伺服器'
    } finally {
      compatLoading.value = false
    }
  }

  async function fetchPartnerCompatibilities() {
    if (!myBirthDate.value || partnersWithBirthDate.value.length === 0) return

    partnerCompatLoading.value = true
    partnerCompatibilities.value = []

    try {
      const results: PartnerCompatibility[] = []

      for (const partner of partnersWithBirthDate.value) {
        const res = await fetch(getApiUrl('/compatibility'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            date1: myBirthDate.value,
            date2: partner.birthDate
          })
        })

        if (res.ok) {
          const data = await res.json()
          if (data.success) {
            const compat = data.data as CompatibilityResult
            results.push({
              partnerId: partner.id,
              nickname: partner.nickname,
              birthDate: partner.birthDate,
              mansion: {
                name_jp: compat.person2.mansion,
                reading: compat.person2.reading,
                element: compat.person2.element
              },
              relation: compat.relation,
              score: compat.score,
              element_bonus: compat.element_bonus,
              summary: compat.summary,
              calculation: {
                distance: compat.calculation.distance,
                element_relation: compat.calculation.element_relation,
                person1_element: compat.person1.element,
                person2_element: compat.person2.element
              }
            })
          }
        }
      }

      partnerCompatibilities.value = results.sort((a, b) => b.score - a.score)
    } catch {
      console.error('Failed to fetch partner compatibilities')
    } finally {
      partnerCompatLoading.value = false
    }
  }

  async function loadMetadata() {
    try {
      const res = await fetch(getApiUrl('/metadata'))
      if (res.ok) {
        metadata.value = await res.json()
      }
    } catch {
      console.error('Failed to load metadata')
    }
  }

  async function loadAllMansions() {
    try {
      const res = await fetch(getApiUrl('/mansions'))
      if (res.ok) {
        const data = await res.json()
        if (data.success && data.mansions) {
          allMansions.value = data.mansions
        }
      }
    } catch {
      console.error('Failed to load mansions')
    }
  }

  async function loadRelations() {
    try {
      const res = await fetch(getApiUrl('/relations'))
      if (res.ok) {
        const data = await res.json()
        if (data.relations) {
          allRelations.value = data.relations
        }
      }
    } catch {
      console.error('Failed to load relations')
    }
  }

  async function loadElements() {
    try {
      const res = await fetch(getApiUrl('/elements'))
      if (res.ok) {
        const data = await res.json()
        if (data.elements) {
          allElements.value = data.elements
        }
      }
    } catch {
      console.error('Failed to load elements')
    }
  }

  // ============================================================================
  // Event Handlers
  // ============================================================================

  function selectLuckyCategory(categoryKey: string) {
    selectedLuckyCategory.value = categoryKey
    selectedLuckyAction.value = null
    luckyDayResult.value = null
  }

  function selectLuckyAction(actionKey: string) {
    selectedLuckyAction.value = actionKey
    fetchLuckyDays()
  }

  function handleWheelSelect(m: WheelMansion) {
    if (selectedWheelMansion.value?.index === m.index) {
      selectedWheelMansion.value = null
    } else {
      selectedWheelMansion.value = m
    }
  }

  function toggleRelation(type: string) {
    expandedRelation.value = expandedRelation.value === type ? null : type
  }

  function quickSelect(date: string) {
    birthDate.value = date
    lookupMansion()
  }

  // Watch for partner tab switch
  watch(activeMatchTab, (tab) => {
    if (tab === 'partners' && partnerCompatibilities.value.length === 0) {
      fetchPartnerCompatibilities()
    }
  })

  // ============================================================================
  // Init
  // ============================================================================

  async function init() {
    await Promise.all([
      loadMetadata(),
      loadAllMansions(),
      loadRelations(),
      loadElements(),
      fetchLuckyDayCategories()
    ])

    // Auto-load if profile has birthdate
    if (myBirthDate.value) {
      birthDate.value = myBirthDate.value
      lookupMansion()
    }
  }

  return {
    // Profile
    myBirthDate,
    partnersWithBirthDate,

    // Tab Navigation
    activeMainTab,
    activeFortuneTab,
    activeMatchTab,
    activeKnowledgeTab,

    // Query UI
    showQueryDialog,
    birthDate,
    lookupLoading,
    lookupError,

    // Mansion Data
    mansion,
    metadata,
    allMansions,
    allRelations,
    allElements,
    selectedWheelMansion,

    // Fortune Data
    dailyFortune,
    weeklyFortune,
    monthlyFortune,
    yearlyFortune,
    fortuneLoading,
    expandedMonthlyWeek,
    currentWeekNumber,

    // Compatibility
    compatFinder,
    finderLoading,
    selectedMansion,
    // Pair Diagnosis
    date2,
    compatibility,
    compatLoading,
    compatError,

    // Partner Compatibilities
    partnerCompatibilities,
    partnerCompatLoading,

    // Lucky Days
    luckyDayCategories,
    selectedLuckyCategory,
    selectedLuckyAction,
    luckyDayResult,
    luckyDayLoading,
    luckyDaySummary,
    luckyDaySummaryLoading,
    japaneseCalendar,
    japaneseCalendarLoading,
    specialDays,
    specialDaysLoading,
    activeLuckyTab,
    selectedPartnerId,
    pairLuckyDays,
    pairLuckyDaysLoading,

    // Computed
    elementColors,
    mansionElementColor,
    currentCategoryActions,
    relationKeys,

    // Helper Functions
    getFortuneLevel,
    getMansionRelationClass,
    getScoreClass,
    getScoreLevel,
    formatDate,

    // API Functions
    lookupMansion,
    fetchLuckyDays,
    fetchLuckyDaySummary,
    fetchJapaneseCalendar,
    fetchSpecialDays,
    fetchPairLuckyDays,
    clearPairSelection,
    calculateCompatibility,
    fetchPartnerCompatibilities,
    fetchDailyFortuneForDate,

    // Event Handlers
    selectLuckyCategory,
    selectLuckyAction,
    handleWheelSelect,
    quickSelect,
    toggleMonthlyWeek,

    // Init
    init
  }
}
