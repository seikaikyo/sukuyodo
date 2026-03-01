<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import type {
  CompatibilityFinderResult,
  CompatibleMansion,
  CompatibilityResult,
  PartnerCompatibility,
  Relation,
  CompanyBatchResult,
  CompanyAnalysisItem,
  LuckyDatesResult,
  GcisCompany
} from '../composables/useSukuyodo'
import type { JobSeeker } from '../stores/profile'
import { getScoreClass, getScoreLevel, getLocalDateStr } from '../utils/fortune-helpers'
import { generateCompatReport, generatePairedDecadeReport } from '../utils/report-generator'
import { getApiUrl } from '../config/api'

const expandedPartnerId = ref<string | null>(null)
const pairedReportLoading = ref(false)
const partnerPairedLoading = ref<string | null>(null)

// GCIS 搜尋下拉
const gcisDropdownOpen = ref(false)
let gcisDebounceTimer: ReturnType<typeof setTimeout> | null = null

function handleCompanyNameInput(value: string) {
  emit('update:companyName', value)
  if (gcisDebounceTimer) clearTimeout(gcisDebounceTimer)
  if (value.trim().length < 2) {
    gcisDropdownOpen.value = false
    return
  }
  gcisDebounceTimer = setTimeout(() => {
    emit('searchGcis', value)
    gcisDropdownOpen.value = true
  }, 500)
}

function handleSelectGcis(company: GcisCompany) {
  emit('selectGcis', company)
  emit('update:companyName', company.name)
  emit('update:companyDate', company.founding_date)
  gcisDropdownOpen.value = false
}

function handleGcisBlur() {
  // 延遲關閉以允許點擊選項
  setTimeout(() => { gcisDropdownOpen.value = false }, 200)
}

function togglePartner(id: string) {
  const isExpanding = expandedPartnerId.value !== id
  expandedPartnerId.value = isExpanding ? id : null
  if (isExpanding) {
    nextTick(() => {
      const el = document.querySelector('.partner-detail')
      el?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    })
  }
}

export interface CompanyCompatItem extends PartnerCompatibility {
  companyId: string
  companyName: string
  companyMemo?: string
  jobUrl?: string
}

export interface CompanySearchResult {
  name: string
  founding_date: string
  score: number
  relation_name: string
  relation_type: string
  direction: string
  distance_type: string
  distance_type_name: string
  element_bonus: number
  verdict: string
  job_title: string
  location: string
  job_url: string
  person1_mansion: string
  person1_element: string
  person2_mansion: string
  person2_element: string
}

const props = defineProps<{
  activeTab: 'finder' | 'compat' | 'partners' | 'company'
  compatFinder: CompatibilityFinderResult | null
  finderLoading: boolean
  selectedMansion: CompatibleMansion | null
  date2: string
  compatibility: CompatibilityResult | null
  compatLoading: boolean
  compatError: string
  partnerCompatibilities: PartnerCompatibility[]
  partnerCompatLoading: boolean
  partnersWithBirthDate: { id: string; nickname: string; birthDate?: string }[]
  elementColors: Record<string, string>
  birthDate: string
  mansion: { name_jp: string; reading: string; element: string } | null
  // Company
  companyName: string
  companyDate: string
  companyCompat: CompatibilityResult | null
  companyCompatLoading: boolean
  companyCompatError: string
  companyCompatibilities: CompanyCompatItem[]
  companyCompatLoading2: boolean
  // Company Auto Search
  companySearchResults: CompanySearchResult[]
  companySearchLoading: boolean
  companySearchError: string
  // GCIS Company Search
  gcisResults: GcisCompany[]
  gcisLoading: boolean
  // Company Batch Analysis
  companyBatchResult: CompanyBatchResult | null
  companyBatchLoading: boolean
  // Job Seekers
  jobSeekers: JobSeeker[]
  activeSeekerId: string
  seekerBatchResults: Record<string, CompanyBatchResult | null>
  seekerBatchLoading: Record<string, boolean>
  luckyDatesResult: LuckyDatesResult | null
  luckyDatesLoading: boolean
  seekerLuckyDates: Record<string, LuckyDatesResult | null>
  userName: string
}>()

async function handleExportPairedReport() {
  if (!props.compatibility || !props.birthDate || !props.date2) return
  pairedReportLoading.value = true
  try {
    const c = props.compatibility
    const p2Match = props.partnersWithBirthDate.find(p => p.birthDate === props.date2)
    const p2Name = p2Match?.nickname || '對方'
    await generatePairedDecadeReport({
      person1: {
        mansion: c.person1.mansion,
        reading: c.person1.reading,
        element: c.person1.element,
        date: props.birthDate,
        name: '你'
      },
      person2: {
        mansion: c.person2.mansion,
        reading: c.person2.reading,
        element: c.person2.element,
        date: props.date2,
        name: p2Name
      },
      compat: {
        score: c.score,
        relationName: c.relation.name,
        reading: c.relation.reading,
        distanceTypeName: c.relation.distance_type_name,
        elementRelation: c.calculation?.element_relation || '',
        direction: c.relation.direction ?? undefined,
        summary: c.summary
      },
      apiUrl: getApiUrl('')
    })
  } catch (e) {
    console.error('匯出雙人流年報告失敗', e)
  } finally {
    pairedReportLoading.value = false
  }
}

async function handlePartnerPairedReport(pc: PartnerCompatibility) {
  if (!props.birthDate || !props.mansion || !pc.birthDate) return
  partnerPairedLoading.value = pc.partnerId
  try {
    await generatePairedDecadeReport({
      person1: {
        mansion: props.mansion.name_jp,
        reading: props.mansion.reading,
        element: props.mansion.element,
        date: props.birthDate,
        name: '你'
      },
      person2: {
        mansion: pc.mansion.name_jp,
        reading: pc.mansion.reading,
        element: pc.mansion.element,
        date: pc.birthDate,
        name: pc.nickname
      },
      compat: {
        score: pc.score,
        relationName: pc.relation.name,
        reading: pc.relation.reading,
        distanceTypeName: pc.relation.distance_type_name,
        elementRelation: pc.calculation?.element_relation || '',
        direction: pc.relation.direction ?? undefined,
        summary: pc.summary
      },
      apiUrl: getApiUrl('')
    })
  } catch (e) {
    console.error('匯出雙人流年報告失敗', e)
  } finally {
    partnerPairedLoading.value = null
  }
}

// Auto search state
const searchKeywords = ref('MES 智慧製造')
const searchArea = ref('6001014000')

const areaOptions = [
  { label: '台南善化 (南科)', value: '6001014000' },
  { label: '台南全區', value: '6001000000' },
  { label: '台南新市', value: '6001015000' },
  { label: '高雄全區', value: '6003000000' },
]

function saveSearchResult(result: CompanySearchResult) {
  handleCurrentSaveCompany({
    name: result.name,
    foundingDate: result.founding_date,
    memo: `${result.job_title} | ${result.location}`,
    jobUrl: result.job_url,
  })
}

const emit = defineEmits<{
  'update:activeTab': [value: 'finder' | 'compat' | 'partners' | 'company']
  'update:selectedMansion': [value: CompatibleMansion | null]
  'update:date2': [value: string]
  'update:companyName': [value: string]
  'update:companyDate': [value: string]
  'update:activeSeekerId': [value: string]
  calculateCompatibility: []
  calculateCompanyCompatibility: []
  saveCompany: [data: { name: string; foundingDate: string; memo?: string; jobUrl?: string }]
  removeCompany: [id: string]
  importCompanies: []
  searchCompanies: [keywords: string, area: string]
  searchGcis: [keyword: string]
  selectGcis: [company: GcisCompany]
  addJobSeeker: [data: { name: string; birthDate: string }]
  removeJobSeeker: [id: string]
  seekerSaveCompany: [seekerId: string, data: { name: string; foundingDate: string; memo?: string; jobUrl?: string }]
  seekerRemoveCompany: [seekerId: string, companyId: string]
  seekerImportCompanies: [seekerId: string, jsonFile: string]
  'navigate-knowledge': [tab: string]
  'navigate-lucky': []
}>()

const relationKeys = [
  { key: 'eishin', cssClass: 'excellent' },
  { key: 'gyotai', cssClass: 'good' },
  { key: 'mei', cssClass: 'fair' },
  { key: 'kisei', cssClass: 'caution' },
  { key: 'yusui', cssClass: 'neutral' },
  { key: 'ankai', cssClass: 'warning' }
]

const roleLabels: Record<string, string> = {
  colleague: '同事/工作夥伴',
  friend: '朋友',
  lover: '戀人/配偶',
  family: '家人'
}

// 方向白話解釋
const directionDesc: Record<string, string> = {
  '栄': '受到正面提升和好運',
  '親': '自然感到親近、被吸引',
  '友': '主動付出和照顧',
  '成': '借力成事、互相精進',
  '命': '本命共鳴、互相牽制',
  '衰': '被照顧，但容易感到消耗',
  '危': '面對變動和不確定性',
  '壊': '既有模式被打破',
  '安': '得到安定和穩固感',
  '胎': '感受到未來延續的可能',
  '業': '感受到深厚的因果牽連'
}

// 方向配對：direction → 反方向
const directionPairs: Record<string, string> = {
  '栄': '親', '親': '栄',
  '友': '衰', '衰': '友',
  '安': '壊', '壊': '安',
  '危': '成', '成': '危',
  '命': '命',
  '業': '胎', '胎': '業'
}

function getInverseDirection(dir: string): string {
  return directionPairs[dir] || dir
}

// 元素關係白話解釋
function getElementDesc(el1: string, el2: string, calcRelation: string): string {
  if (el1 === el2) return `同為${el1}元素，能量共鳴互相增強`
  if (calcRelation.includes('生')) {
    // 判斷誰生誰
    const genMap: Record<string, string> = {
      '木': '火', '火': '土', '土': '金', '金': '水', '水': '木'
    }
    if (genMap[el2] === el1) return `${el2}生${el1} — 對方的能量自然滋養你`
    if (genMap[el1] === el2) return `${el1}生${el2} — 你的能量自然滋養對方`
  }
  if (calcRelation.includes('剋')) {
    const keMap: Record<string, string> = {
      '木': '土', '火': '金', '土': '水', '金': '木', '水': '火'
    }
    if (keMap[el1] === el2) return `${el1}剋${el2} — 你的能量壓制對方`
    if (keMap[el2] === el1) return `${el2}剋${el1} — 對方的能量壓制你`
  }
  if (calcRelation.includes('洩')) {
    return `能量有洩散傾向，長期相處需要刻意補充`
  }
  return calcRelation.replace(/[+\-]\d+\s*分/, '').trim()
}

function handleMansionClick(m: CompatibleMansion) {
  emit('update:selectedMansion', props.selectedMansion?.index === m.index ? null : m)
}

// Job Seeker state
const showAddSeekerDialog = ref(false)
const newSeekerName = ref('')
const newSeekerBirthDate = ref('')
const confirmDeleteSeekerId = ref<string | null>(null)

function switchSeeker(id: string) {
  emit('update:activeSeekerId', id)
}

function submitAddSeeker() {
  if (!newSeekerName.value.trim() || !newSeekerBirthDate.value) return
  emit('addJobSeeker', {
    name: newSeekerName.value.trim(),
    birthDate: newSeekerBirthDate.value
  })
  newSeekerName.value = ''
  newSeekerBirthDate.value = ''
  showAddSeekerDialog.value = false
}

function confirmRemoveSeeker(id: string) {
  confirmDeleteSeekerId.value = id
}

function executeRemoveSeeker(id: string) {
  emit('removeJobSeeker', id)
  confirmDeleteSeekerId.value = null
}

// Computed: 當前 seeker 的 batch result / loading / companies
const currentBatchResult = computed(() => {
  if (props.activeSeekerId === 'self') return props.companyBatchResult
  return props.seekerBatchResults[props.activeSeekerId] || null
})

const currentBatchLoading = computed(() => {
  if (props.activeSeekerId === 'self') return props.companyBatchLoading
  return props.seekerBatchLoading[props.activeSeekerId] || false
})

const currentSeeker = computed(() => {
  if (props.activeSeekerId === 'self') return null
  return props.jobSeekers.find(s => s.id === props.activeSeekerId) || null
})

const isSelf = computed(() => props.activeSeekerId === 'self')

const currentLuckyDates = computed(() => {
  if (props.activeSeekerId === 'self') return props.luckyDatesResult
  return props.seekerLuckyDates[props.activeSeekerId] || null
})

// 處理 seeker 的儲存/刪除/匯入
function handleCurrentSaveCompany(data: { name: string; foundingDate: string; memo?: string; jobUrl?: string }) {
  if (isSelf.value) {
    emit('saveCompany', data)
  } else {
    emit('seekerSaveCompany', props.activeSeekerId, data)
  }
}

function handleCurrentRemoveCompany(id: string) {
  if (isSelf.value) {
    emit('removeCompany', id)
  } else {
    emit('seekerRemoveCompany', props.activeSeekerId, id)
  }
}

function handleCurrentImport() {
  if (isSelf.value) {
    emit('importCompanies')
  } else if (currentSeeker.value) {
    const jsonFile = `companies-${currentSeeker.value.name.toLowerCase()}.json`
    emit('seekerImportCompanies', props.activeSeekerId, jsonFile)
  }
}

// Company verdict
const expandedCompanyId = ref<string | null>(null)
const confirmDeleteCompanyId = ref<string | null>(null)

function toggleCompany(id: string) {
  const isExpanding = expandedCompanyId.value !== id
  expandedCompanyId.value = isExpanding ? id : null
  if (isExpanding) {
    nextTick(() => {
      const el = document.querySelector('.company-detail')
      el?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    })
  }
}

function deleteCompany(id: string) {
  handleCurrentRemoveCompany(id)
  confirmDeleteCompanyId.value = null
  if (expandedCompanyId.value === id) expandedCompanyId.value = null
}

interface CompanyVerdict {
  level: 'recommend' | 'caution' | 'avoid'
  text: string
  detail: string
}

// 梯隊分組
function getCompaniesByTier(tier: number): CompanyAnalysisItem[] {
  const result = currentBatchResult.value
  if (!result) return []
  return result.companies.filter(c => c.tier.rank === tier)
}

// 九曜等級 CSS class
function formatShortDate(dateStr: string): string {
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}/${d.getDate()}`
}

function getKuyouLevelClass(level: string): string {
  switch (level) {
    case '大吉': return 'kuyou-daikichi'
    case '半吉': return 'kuyou-hankichi'
    case '末吉': return 'kuyou-suekichi'
    case '大凶': return 'kuyou-daikyo'
    default: return ''
  }
}

// RC 風險 CSS class
function getRefCheckClass(riskLevel: string): string {
  switch (riskLevel) {
    case 'high': return 'rc-high'
    case 'medium': return 'rc-medium'
    case 'low': return 'rc-low'
    default: return ''
  }
}

function getCompanyVerdict(relation: Relation): CompanyVerdict {
  const type = relation.type
  const dir = relation.direction || ''

  // 栄親
  if (type === 'eishin') {
    if (dir === '栄') {
      return { level: 'recommend', text: '推薦', detail: '你是栄方，公司自然帶給你助力和好運' }
    }
    return { level: 'recommend', text: '適合', detail: '你是親方，會自然投入付出，確保回報合理即可' }
  }
  // 友衰
  if (type === 'yusui') {
    if (dir === '友') {
      return { level: 'caution', text: '留意', detail: '你是友方（給予側），注意付出與回報是否平衡' }
    }
    return { level: 'caution', text: '留意', detail: '你是衰方（接受側），短期有利但長期需觀察' }
  }
  // 命/業/胎
  if (type === 'mei' || type === 'gyotai') {
    return { level: 'caution', text: '中性', detail: '命業胎關係，緣分深但需看其他條件綜合判斷' }
  }
  // 危成
  if (type === 'kisei') {
    if (dir === '危') {
      return { level: 'caution', text: '留意', detail: '你是危方，這間公司會帶來變化與挑戰，需主動適應並調整策略' }
    }
    return { level: 'caution', text: '可考慮', detail: '你是成方（被借力），能發揮價值但留意風險' }
  }
  // 安壊
  if (type === 'ankai') {
    if (dir === '壊') {
      return { level: 'caution', text: '謹慎', detail: '你是壊方，有能力打破現狀推動改變，但需注意節奏避免過度衝突' }
    }
    return { level: 'caution', text: '留意', detail: '你是安方，表面穩定但可能被動、難以主導' }
  }

  return { level: 'caution', text: '中性', detail: '請參考相性分數綜合判斷' }
}
</script>

<template>
  <section class="match-tab">
    <div class="sub-tabs" role="tablist" aria-label="配對功能選擇">
      <button
        class="pill-btn"
        :class="{ active: activeTab === 'finder' }"
        role="tab"
        :aria-selected="activeTab === 'finder'"
        aria-controls="panel-match-finder"
        @click="emit('update:activeTab', 'finder')"
      >尋找配對</button>
      <button
        class="pill-btn"
        :class="{ active: activeTab === 'compat' }"
        role="tab"
        :aria-selected="activeTab === 'compat'"
        aria-controls="panel-match-compat"
        @click="emit('update:activeTab', 'compat')"
      >相性診斷</button>
      <button
        class="pill-btn"
        :class="{ active: activeTab === 'partners' }"
        role="tab"
        :aria-selected="activeTab === 'partners'"
        aria-controls="panel-match-partners"
        @click="emit('update:activeTab', 'partners')"
      >我的配對</button>
      <button
        class="pill-btn"
        :class="{ active: activeTab === 'company' }"
        role="tab"
        :aria-selected="activeTab === 'company'"
        aria-controls="panel-match-company"
        @click="emit('update:activeTab', 'company')"
      >公司速查</button>
    </div>

    <!-- Finder -->
    <div v-if="activeTab === 'finder'" id="panel-match-finder" class="match-content" role="tabpanel">
      <template v-if="compatFinder">
        <div class="finder-intro">
          <p>宿曜經將 27 宿之間的關係分為六種，由宿與宿之間的距離和元素交互決定。
            分數越高代表自然和諧度越強，但低分不代表不合，而是相處時需要更多覺察。
            點擊宿名可查看該宿的農曆日期對照。</p>
        </div>
        <div class="relation-grid">
          <div
            v-for="rk in relationKeys"
            :key="rk.key"
            class="relation-section"
            :class="rk.cssClass"
          >
            <h4 class="relation-title">
              {{ (compatFinder as any)[rk.key]?.relation }}
              <span class="relation-score">{{ (compatFinder as any)[rk.key]?.score }} 分</span>
            </h4>
            <p class="relation-desc">{{ (compatFinder as any)[rk.key]?.description }}</p>
            <p v-if="(compatFinder as any)[rk.key]?.detailed" class="relation-detailed">
              {{ (compatFinder as any)[rk.key]?.detailed }}
            </p>
            <div class="mansion-chips">
              <button
                v-for="m in (compatFinder as any)[rk.key]?.mansions"
                :key="m.index"
                class="mansion-chip"
                :class="{ active: selectedMansion?.index === m.index }"
                :aria-label="`${m.name_jp}（${m.reading}）${m.element}曜`"
                :aria-pressed="selectedMansion?.index === m.index"
                @click="handleMansionClick(m)"
              >
                {{ m.name_jp }}
                <span class="chip-element" :style="{ background: elementColors[m.element] }">{{ m.element }}</span>
              </button>
            </div>
          </div>
        </div>

        <!-- Selected Mansion Detail -->
        <div v-if="selectedMansion" class="mansion-detail">
          <h4>{{ selectedMansion.name_jp }}（{{ selectedMansion.reading }}）</h4>
          <p>{{ selectedMansion.personality }}</p>
          <div class="keywords">
            <span v-for="kw in selectedMansion.keywords" :key="kw" class="keyword">{{ kw }}</span>
          </div>
          <div v-if="selectedMansion.lunar_dates?.length" class="lunar-dates">
            <h5>農曆日期對照</h5>
            <div class="lunar-date-chips">
              <span
                v-for="ld in selectedMansion.lunar_dates"
                :key="ld.display"
                class="lunar-date-chip"
              >{{ ld.display }}</span>
            </div>
          </div>
        </div>
      </template>
      <div v-else-if="finderLoading" class="loading-state">
        <sl-spinner></sl-spinner>
      </div>
    </div>

    <!-- Compatibility Diagnosis -->
    <div v-if="activeTab === 'compat'" id="panel-match-compat" class="match-content" role="tabpanel">
      <div class="compat-form">
        <sl-input
          type="date"
          name="partner-birthday"
          :value="date2"
          label="對方生日"
          :max="getLocalDateStr()"
          @sl-input="emit('update:date2', ($event.target as HTMLInputElement).value)"
        ></sl-input>
        <button
          class="btn-primary"
          :disabled="!date2 || compatLoading"
          @click="emit('calculateCompatibility')"
        >
          <sl-spinner v-if="compatLoading"></sl-spinner>
          <span v-else>分析</span>
        </button>
      </div>

      <div v-if="compatError" class="error-msg">{{ compatError }}</div>

      <div v-if="compatibility" class="compat-result">
        <div class="compat-result-header">
          <div class="compat-score" :class="getScoreLevel(compatibility.score).class">
            <span class="score-num">{{ compatibility.score }}</span>
            <span class="score-text">{{ getScoreLevel(compatibility.score).text }}</span>
          </div>
          <div class="export-btns">
            <button class="export-btn" @click="generateCompatReport(compatibility!)">匯出報告</button>
            <button
              class="export-btn"
              :disabled="pairedReportLoading || !birthDate"
              @click="handleExportPairedReport"
            >
              <sl-spinner v-if="pairedReportLoading"></sl-spinner>
              <span v-else>匯出雙人流年</span>
            </button>
          </div>
        </div>

        <div class="compat-persons">
          <div class="person-card">
            <h5>你</h5>
            <p class="person-mansion">{{ compatibility.person1.mansion }}</p>
            <span class="person-element">{{ compatibility.person1.element }}</span>
          </div>
          <div class="relation-arrow">
            <span class="relation-name term-link" @click="emit('navigate-knowledge', 'relations')">
              {{ compatibility.relation.name }}
              <template v-if="compatibility.relation.direction">（{{ compatibility.relation.direction }}）</template>
            </span>
            <span class="relation-reading">{{ compatibility.relation.reading }}</span>
            <span
              v-if="compatibility.relation.distance_type_name"
              class="distance-tag term-link"
              :class="compatibility.relation.distance_type"
              @click="emit('navigate-knowledge', 'relations')"
            >
              <ruby v-if="compatibility.relation.distance_type_reading">{{ compatibility.relation.distance_type_name }}<rp>(</rp><rt>{{ compatibility.relation.distance_type_reading }}</rt><rp>)</rp></ruby>
              <template v-else>{{ compatibility.relation.distance_type_name }}</template>
            </span>
          </div>
          <div class="person-card">
            <h5>對方</h5>
            <p class="person-mansion">{{ compatibility.person2.mansion }}</p>
            <span class="person-element">{{ compatibility.person2.element }}</span>
          </div>
        </div>

        <!-- 方向解釋 -->
        <div v-if="compatibility.relation.direction" class="direction-box">
          <div class="direction-row">
            <span class="direction-label">{{ compatibility.person1.mansion }}→{{ compatibility.person2.mansion }}</span>
            <span class="direction-value">{{ compatibility.relation.direction }}</span>
            <span class="direction-desc">{{ compatibility.person1.mansion }}{{ directionDesc[compatibility.relation.direction] || '' }}</span>
          </div>
          <div class="direction-row">
            <span class="direction-label">{{ compatibility.person2.mansion }}→{{ compatibility.person1.mansion }}</span>
            <span class="direction-value">{{ getInverseDirection(compatibility.relation.direction) }}</span>
            <span class="direction-desc">{{ compatibility.person2.mansion }}{{ directionDesc[getInverseDirection(compatibility.relation.direction)] || '' }}</span>
          </div>
        </div>

        <!-- 原典三九秘法 -->
        <div v-if="compatibility.classical_analysis" class="classical-analysis-box">
          <div class="classical-header">
            <h5>原典三九秘法</h5>
            <span class="classical-source">{{ compatibility.classical_analysis.source }}</span>
          </div>
          <div class="classical-directions">
            <div class="classical-direction">
              <div class="classical-direction-title">
                <span>{{ compatibility.person1.mansion }}→{{ compatibility.person2.mansion }}</span>
                <span class="classical-position-badge">{{ compatibility.classical_analysis.person1_to_person2.position.full_name }}</span>
              </div>
              <blockquote class="classical-sutra">
                {{ compatibility.classical_analysis.person1_to_person2.sutra.text }}
                <cite>{{ compatibility.classical_analysis.person1_to_person2.sutra.ref }}</cite>
              </blockquote>
              <p class="classical-interpretation">{{ compatibility.classical_analysis.person1_to_person2.interpretation }}</p>
            </div>
            <div class="classical-direction">
              <div class="classical-direction-title">
                <span>{{ compatibility.person2.mansion }}→{{ compatibility.person1.mansion }}</span>
                <span class="classical-position-badge">{{ compatibility.classical_analysis.person2_to_person1.position.full_name }}</span>
              </div>
              <blockquote class="classical-sutra">
                {{ compatibility.classical_analysis.person2_to_person1.sutra.text }}
                <cite>{{ compatibility.classical_analysis.person2_to_person1.sutra.ref }}</cite>
              </blockquote>
              <p class="classical-interpretation">{{ compatibility.classical_analysis.person2_to_person1.interpretation }}</p>
            </div>
          </div>
        </div>

        <!-- 元素關係 -->
        <div v-if="compatibility.calculation" class="element-relation-box">
          <span class="element-tag" :style="{ background: elementColors[compatibility.person1.element] }">{{ compatibility.person1.element }}</span>
          <span class="element-arrow">→</span>
          <span class="element-tag" :style="{ background: elementColors[compatibility.person2.element] }">{{ compatibility.person2.element }}</span>
          <span class="element-desc term-link" @click="emit('navigate-knowledge', 'elements')">{{ getElementDesc(compatibility.person1.element, compatibility.person2.element, compatibility.calculation.element_relation) }}</span>
        </div>

        <div class="compat-detail">
          <p>{{ compatibility.relation.description }}</p>
          <p>{{ compatibility.summary }}</p>
        </div>

        <!-- 適合場景 -->
        <div v-if="compatibility.relation.good_for?.length" class="good-for-section">
          <h5>適合場景</h5>
          <div class="good-for-tags">
            <span v-for="(gf, i) in compatibility.relation.good_for" :key="i" class="good-for-tag">{{ gf }}</span>
          </div>
        </div>

        <div v-if="compatibility.relation.love || compatibility.relation.career" class="compat-aspects">
          <div v-if="compatibility.relation.love" class="aspect-section">
            <h5>愛情面向</h5>
            <p>{{ compatibility.relation.love }}</p>
          </div>
          <div v-if="compatibility.relation.career" class="aspect-section">
            <h5>事業面向</h5>
            <p>{{ compatibility.relation.career }}</p>
          </div>
        </div>

        <div v-if="compatibility.relation.roles && Object.keys(compatibility.relation.roles).length" class="role-advice">
          <h5>角色別相處指南</h5>
          <div class="role-grid">
            <div
              v-for="(desc, role) in compatibility.relation.roles"
              :key="role"
              class="role-card"
            >
              <h6 class="role-label">{{ roleLabels[role] || role }}</h6>
              <p>{{ desc }}</p>
            </div>
          </div>
        </div>

        <div class="compat-advice">
          <h5>相處建議</h5>
          <p>{{ compatibility.relation.advice }}</p>
          <div v-if="compatibility.relation.tips?.length" class="tips">
            <h6>小技巧</h6>
            <ul>
              <li v-for="(tip, i) in compatibility.relation.tips" :key="i">{{ tip }}</li>
            </ul>
          </div>
          <div v-if="compatibility.relation.avoid?.length" class="avoid-list">
            <h6>避免事項</h6>
            <ul>
              <li v-for="(a, i) in compatibility.relation.avoid" :key="i">{{ a }}</li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- Company -->
    <div v-if="activeTab === 'company'" id="panel-match-company" class="match-content" role="tabpanel">
      <!-- 求職者頁籤 -->
      <div class="seeker-tabs">
        <button
          class="seeker-tab"
          :class="{ active: activeSeekerId === 'self' }"
          @click="switchSeeker('self')"
        >{{ userName || '我' }}</button>
        <button
          v-for="s in jobSeekers"
          :key="s.id"
          class="seeker-tab"
          :class="{ active: activeSeekerId === s.id }"
          @click="switchSeeker(s.id)"
        >
          {{ s.name }}
          <span
            v-if="confirmDeleteSeekerId === s.id"
            class="seeker-delete-confirm"
            @click.stop="executeRemoveSeeker(s.id)"
          >確認刪除</span>
          <span
            v-else
            class="seeker-delete"
            @click.stop="confirmRemoveSeeker(s.id)"
          >x</span>
        </button>
        <button class="seeker-tab seeker-add" @click="showAddSeekerDialog = true">+</button>
      </div>

      <!-- 新增求職者 Dialog -->
      <div v-if="showAddSeekerDialog" class="seeker-dialog-overlay" @click.self="showAddSeekerDialog = false">
        <div class="seeker-dialog">
          <h4>新增求職者</h4>
          <sl-input
            :value="newSeekerName"
            label="名稱"
            placeholder="例：正念"
            @sl-input="newSeekerName = ($event.target as HTMLInputElement).value"
          ></sl-input>
          <sl-input
            type="date"
            :value="newSeekerBirthDate"
            label="生日"
            @sl-input="newSeekerBirthDate = ($event.target as HTMLInputElement).value"
          ></sl-input>
          <div class="seeker-dialog-actions">
            <button class="btn-secondary" @click="showAddSeekerDialog = false">取消</button>
            <button
              class="btn-primary"
              :disabled="!newSeekerName.trim() || !newSeekerBirthDate"
              @click="submitAddSeeker"
            >確認</button>
          </div>
        </div>
      </div>

      <!-- 自動搜尋（僅在 self 模式顯示） -->
      <div v-if="isSelf" class="auto-search-section">
        <h4 class="section-title">自動搜尋 104 職缺</h4>
        <p class="section-desc">輸入關鍵字，自動搜尋 104 → 查設立日期 → 算相性</p>
        <div class="auto-search-form">
          <sl-input
            :value="searchKeywords"
            label="關鍵字"
            placeholder="例：MES 智慧製造"
            @sl-input="searchKeywords = ($event.target as HTMLInputElement).value"
          ></sl-input>
          <div class="form-row">
            <label class="form-label">地區</label>
            <sl-select
              :value="searchArea"
              @sl-change="searchArea = ($event.target as HTMLSelectElement).value"
            >
              <sl-option
                v-for="opt in areaOptions"
                :key="opt.value"
                :value="opt.value"
              >{{ opt.label }}</sl-option>
            </sl-select>
          </div>
          <button
            class="btn-primary btn-search"
            :disabled="!searchKeywords.trim() || companySearchLoading"
            @click="emit('searchCompanies', searchKeywords, searchArea)"
          >
            <sl-spinner v-if="companySearchLoading"></sl-spinner>
            <span v-else>搜尋推薦公司</span>
          </button>
        </div>

        <div v-if="companySearchError" class="error-msg">{{ companySearchError }}</div>

        <div v-if="companySearchLoading" class="search-progress">
          <sl-spinner></sl-spinner>
          <span>搜尋中，需爬取外部網站約 30-60 秒...</span>
        </div>

        <!-- 搜尋結果 -->
        <div v-if="companySearchResults.length > 0" class="search-results">
          <h5 class="results-title">搜尋結果 ({{ companySearchResults.length }} 間公司)</h5>
          <div class="partner-list">
            <div
              v-for="(result, idx) in companySearchResults"
              :key="idx"
              class="search-result-card"
              :class="result.verdict === '推薦' || result.verdict === '適合' ? 'recommend' : result.verdict === '避開' ? 'avoid' : 'caution'"
            >
              <div class="result-main">
                <div class="result-info">
                  <span class="result-name">{{ result.name }}</span>
                  <span class="result-job">{{ result.job_title }}</span>
                  <span class="result-location">{{ result.location }}</span>
                </div>
                <div class="result-compat">
                  <span class="result-relation">{{ result.relation_name }}</span>
                  <span
                    v-if="result.distance_type_name"
                    class="distance-tag"
                    :class="result.distance_type"
                  >{{ result.distance_type_name }}</span>
                  <span
                    class="verdict-badge-mini"
                    :class="result.verdict === '推薦' || result.verdict === '適合' ? 'recommend' : result.verdict === '避開' ? 'avoid' : 'caution'"
                  >{{ result.verdict }}</span>
                </div>
                <div class="result-score">
                  <span class="score-num">{{ result.score }}</span>
                </div>
              </div>
              <div class="result-actions">
                <span class="result-mansions">
                  {{ result.person2_mansion }}（{{ result.person2_element }}）
                  <template v-if="result.direction">| {{ result.direction }}</template>
                </span>
                <div class="result-btns">
                  <a
                    v-if="result.job_url"
                    :href="result.job_url"
                    target="_blank"
                    rel="noopener"
                    class="btn-link-sm"
                  >104 職缺</a>
                  <button
                    class="btn-save-sm"
                    @click="saveSearchResult(result)"
                  >收藏</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="isSelf" class="self-only-section">
      <hr class="section-divider" />

      <!-- 手動查詢 -->
      <div class="company-intro">
        <p>輸入公司名稱，自動從經濟部商工登記查詢設立日期。</p>
      </div>

      <div class="company-form">
        <div class="gcis-input-wrapper">
          <sl-input
            :value="companyName"
            label="公司名稱"
            placeholder="例：研華、台積電"
            @sl-input="handleCompanyNameInput(($event.target as HTMLInputElement).value)"
            @sl-blur="handleGcisBlur"
          ></sl-input>
          <sl-spinner v-if="gcisLoading" class="gcis-spinner"></sl-spinner>
          <div v-if="gcisDropdownOpen && gcisResults.length > 0" class="gcis-dropdown">
            <div
              v-for="company in gcisResults"
              :key="company.business_no"
              class="gcis-option"
              @mousedown.prevent="handleSelectGcis(company)"
            >
              <span class="gcis-name">{{ company.name }}</span>
              <span class="gcis-meta">{{ company.founding_date }} | {{ company.responsible }}</span>
            </div>
          </div>
          <div v-if="gcisDropdownOpen && !gcisLoading && gcisResults.length === 0 && companyName.trim().length >= 2" class="gcis-dropdown">
            <div class="gcis-empty">查無結果，可手動輸入設立日期</div>
          </div>
        </div>
        <sl-input
          type="date"
          :value="companyDate"
          label="設立日期"
          :max="getLocalDateStr()"
          @sl-input="emit('update:companyDate', ($event.target as HTMLInputElement).value)"
        ></sl-input>
        <button
          class="btn-primary"
          :disabled="!companyDate || companyCompatLoading"
          @click="emit('calculateCompanyCompatibility')"
        >
          <sl-spinner v-if="companyCompatLoading"></sl-spinner>
          <span v-else>查詢</span>
        </button>
      </div>

      <div v-if="companyCompatError" class="error-msg">{{ companyCompatError }}</div>

      <!-- Company Result -->
      <div v-if="companyCompat" class="compat-result company-result">
        <div class="company-verdict-header">
          <div class="compat-score" :class="getScoreLevel(companyCompat.score).class">
            <span class="score-num">{{ companyCompat.score }}</span>
            <span class="score-text">{{ getScoreLevel(companyCompat.score).text }}</span>
          </div>
          <div
            class="verdict-badge"
            :class="getCompanyVerdict(companyCompat.relation).level"
          >{{ getCompanyVerdict(companyCompat.relation).text }}</div>
        </div>

        <div class="verdict-detail">
          {{ getCompanyVerdict(companyCompat.relation).detail }}
        </div>

        <div class="compat-persons">
          <div class="person-card">
            <h5>你</h5>
            <p class="person-mansion">{{ companyCompat.person1.mansion }}</p>
            <span class="person-element">{{ companyCompat.person1.element }}</span>
          </div>
          <div class="relation-arrow">
            <span class="relation-name">
              {{ companyCompat.relation.name }}
              <template v-if="companyCompat.relation.direction">（{{ companyCompat.relation.direction }}）</template>
            </span>
            <span class="relation-reading">{{ companyCompat.relation.reading }}</span>
            <span
              v-if="companyCompat.relation.distance_type_name"
              class="distance-tag"
              :class="companyCompat.relation.distance_type"
            >{{ companyCompat.relation.distance_type_name }}</span>
          </div>
          <div class="person-card">
            <h5>{{ companyName || '公司' }}</h5>
            <p class="person-mansion">{{ companyCompat.person2.mansion }}</p>
            <span class="person-element">{{ companyCompat.person2.element }}</span>
          </div>
        </div>

        <!-- 方向解釋 -->
        <div v-if="companyCompat.relation.direction" class="direction-box">
          <div class="direction-row">
            <span class="direction-label">{{ companyCompat.person1.mansion }}→{{ companyCompat.person2.mansion }}</span>
            <span class="direction-value">{{ companyCompat.relation.direction }}</span>
            <span class="direction-desc">{{ companyCompat.person1.mansion }}{{ directionDesc[companyCompat.relation.direction] || '' }}</span>
          </div>
          <div class="direction-row">
            <span class="direction-label">{{ companyCompat.person2.mansion }}→{{ companyCompat.person1.mansion }}</span>
            <span class="direction-value">{{ getInverseDirection(companyCompat.relation.direction) }}</span>
            <span class="direction-desc">{{ companyCompat.person2.mansion }}{{ directionDesc[getInverseDirection(companyCompat.relation.direction)] || '' }}</span>
          </div>
        </div>

        <!-- 原典三九秘法 -->
        <div v-if="companyCompat.classical_analysis" class="classical-analysis-box">
          <div class="classical-header">
            <h5>原典三九秘法</h5>
            <span class="classical-source">{{ companyCompat.classical_analysis.source }}</span>
          </div>
          <div class="classical-directions">
            <div class="classical-direction">
              <div class="classical-direction-title">
                <span>{{ companyCompat.person1.mansion }}→{{ companyCompat.person2.mansion }}</span>
                <span class="classical-position-badge">{{ companyCompat.classical_analysis.person1_to_person2.position.full_name }}</span>
              </div>
              <blockquote class="classical-sutra">
                {{ companyCompat.classical_analysis.person1_to_person2.sutra.text }}
                <cite>{{ companyCompat.classical_analysis.person1_to_person2.sutra.ref }}</cite>
              </blockquote>
              <p class="classical-interpretation">{{ companyCompat.classical_analysis.person1_to_person2.interpretation }}</p>
            </div>
            <div class="classical-direction">
              <div class="classical-direction-title">
                <span>{{ companyCompat.person2.mansion }}→{{ companyCompat.person1.mansion }}</span>
                <span class="classical-position-badge">{{ companyCompat.classical_analysis.person2_to_person1.position.full_name }}</span>
              </div>
              <blockquote class="classical-sutra">
                {{ companyCompat.classical_analysis.person2_to_person1.sutra.text }}
                <cite>{{ companyCompat.classical_analysis.person2_to_person1.sutra.ref }}</cite>
              </blockquote>
              <p class="classical-interpretation">{{ companyCompat.classical_analysis.person2_to_person1.interpretation }}</p>
            </div>
          </div>
        </div>

        <!-- 元素關係 -->
        <div v-if="companyCompat.calculation" class="element-relation-box">
          <span class="element-tag" :style="{ background: elementColors[companyCompat.person1.element] }">{{ companyCompat.person1.element }}</span>
          <span class="element-arrow">→</span>
          <span class="element-tag" :style="{ background: elementColors[companyCompat.person2.element] }">{{ companyCompat.person2.element }}</span>
          <span class="element-desc">{{ getElementDesc(companyCompat.person1.element, companyCompat.person2.element, companyCompat.calculation.element_relation) }}</span>
        </div>

        <!-- 事業面向 -->
        <div v-if="companyCompat.relation.career" class="compat-aspects">
          <div class="aspect-section">
            <h5>事業面向</h5>
            <p>{{ companyCompat.relation.career }}</p>
          </div>
        </div>

        <div class="compat-detail">
          <p>{{ companyCompat.relation.description }}</p>
          <p>{{ companyCompat.summary }}</p>
        </div>

        <!-- 儲存按鈕 -->
        <button
          class="btn-save-company"
          @click="handleCurrentSaveCompany({ name: companyName || '未命名公司', foundingDate: companyDate })"
        >收藏此公司</button>
      </div>
      </div>

      <!-- 載入推薦清單 -->
      <div class="import-section">
        <button class="btn-import-companies" @click="handleCurrentImport">載入推薦清單</button>
        <span class="import-hint">{{ isSelf ? '從 companies.json 匯入' : `從 companies-${currentSeeker?.name?.toLowerCase() || ''}.json 匯入` }}</span>
      </div>

      <!-- Batch Analysis Loading -->
      <div v-if="currentBatchLoading" class="loading-state">
        <sl-spinner></sl-spinner>
        <span class="loading-text">分析公司流年與梯隊排名...</span>
      </div>

      <!-- Batch Analysis Results -->
      <div v-else-if="currentBatchResult && currentBatchResult.companies.length > 0" class="batch-analysis">
        <!-- 使用者流年橫幅 -->
        <div class="user-fortune-banner">
          <div class="banner-left">
            <span class="banner-label">{{ isSelf ? '你的流年' : currentSeeker?.name + ' 的流年' }}</span>
            <span class="kuyou-badge" :class="getKuyouLevelClass(currentBatchResult.user.yearly_fortune.kuyou_star.level)">
              {{ currentBatchResult.user.yearly_fortune.kuyou_star.name }}
              {{ currentBatchResult.user.yearly_fortune.kuyou_star.level }}
            </span>
          </div>
          <div class="banner-right">
            <span class="banner-score">整體 {{ currentBatchResult.user.yearly_fortune.overall }}</span>
            <span class="banner-score">事業 {{ currentBatchResult.user.yearly_fortune.career }}</span>
          </div>
        </div>

        <!-- 吉凶日曆面板 -->
        <div v-if="currentLuckyDates" class="lucky-dates-panel">
          <div v-if="currentLuckyDates.good_dates.length > 0" class="lucky-dates-section good-dates">
            <h5>投遞/面試吉日</h5>
            <div class="date-chips">
              <span
                v-for="d in currentLuckyDates.good_dates.slice(0, 5)"
                :key="d.date"
                class="date-chip good"
                :title="d.reason"
              >
                {{ formatShortDate(d.date) }} {{ d.weekday.replace('曜日','') }}
                <small>{{ d.career }}</small>
              </span>
            </div>
          </div>
          <div v-if="currentLuckyDates.bad_dates.length > 0" class="lucky-dates-section bad-dates">
            <h5>建議謹慎（需特別準備）</h5>
            <div class="date-chips">
              <span
                v-for="d in currentLuckyDates.bad_dates.slice(0, 5)"
                :key="d.date"
                class="date-chip bad"
                :title="d.reason"
              >
                {{ formatShortDate(d.date) }} {{ d.weekday.replace('曜日','') }}
                <small>{{ d.career }}</small>
              </span>
            </div>
          </div>
          <div v-if="currentLuckyDates.dark_weeks.length > 0" class="dark-week-warning">
            暗黒の一週間: {{ currentLuckyDates.dark_weeks.map(w =>
              formatShortDate(w.start) + '~' + formatShortDate(w.end)).join(', ') }}
          </div>
        </div>
        <div v-else-if="luckyDatesLoading" class="lucky-dates-panel loading">
          <sl-spinner></sl-spinner>
          <span>載入吉凶日期...</span>
        </div>

        <!-- 梯隊統計列 -->
        <div class="tier-summary-row">
          <span v-if="currentBatchResult.tier_summary.tier_1 > 0" class="tier-count tier-1">
            第一 {{ currentBatchResult.tier_summary.tier_1 }}
          </span>
          <span v-if="currentBatchResult.tier_summary.tier_2 > 0" class="tier-count tier-2">
            第二 {{ currentBatchResult.tier_summary.tier_2 }}
          </span>
          <span v-if="currentBatchResult.tier_summary.tier_3 > 0" class="tier-count tier-3">
            第三 {{ currentBatchResult.tier_summary.tier_3 }}
          </span>
          <span v-if="currentBatchResult.tier_summary.tier_4 > 0" class="tier-count tier-4">
            第四 {{ currentBatchResult.tier_summary.tier_4 }}
          </span>
        </div>

        <!-- 按梯隊分組顯示 -->
        <template v-for="tierNum in [1, 2, 3, 4]" :key="tierNum">
          <div v-if="getCompaniesByTier(tierNum).length > 0" class="tier-group">
            <h4 class="tier-group-title" :class="`tier-${tierNum}`">
              {{ ['', '第一梯隊', '第二梯隊', '第三梯隊', '第四梯隊'][tierNum] }}
              <span class="tier-group-count">{{ getCompaniesByTier(tierNum).length }}</span>
            </h4>
            <div class="partner-list">
              <div
                v-for="item in getCompaniesByTier(tierNum)"
                :key="item.id"
                class="partner-card-wrapper"
              >
                <button
                  class="partner-card"
                  :class="[getScoreClass(item.compatibility.score), { expanded: expandedCompanyId === item.id }]"
                  :aria-expanded="expandedCompanyId === item.id"
                  @click="toggleCompany(item.id)"
                >
                  <div class="partner-info">
                    <span class="partner-name">
                      <a
                        v-if="item.job_url"
                        :href="item.job_url"
                        target="_blank"
                        rel="noopener"
                        class="company-name-link"
                        title="開啟 104 職缺"
                        @click.stop
                      >{{ item.name }}</a>
                      <template v-else>{{ item.name }}</template>
                    </span>
                    <span class="partner-mansion">{{ item.compatibility.person2.mansion }}（{{ item.compatibility.person2.reading }}）</span>
                    <span v-if="item.memo" class="partner-memo">{{ item.memo }}</span>
                  </div>
                  <div class="partner-relation">
                    <span class="relation-name">{{ item.compatibility.relation.name }}</span>
                    <div class="batch-badges">
                      <span class="kuyou-badge-sm" :class="getKuyouLevelClass(item.company_fortune.kuyou_star.level)">
                        {{ item.company_fortune.kuyou_star.level }}
                      </span>
                      <span class="rc-badge-sm" :class="getRefCheckClass(item.ref_check.risk_level)">
                        RC{{ item.ref_check.risk_label }}
                      </span>
                    </div>
                  </div>
                  <div class="partner-score-area">
                    <span class="score-num">{{ item.compatibility.score }}</span>
                    <a
                      v-if="item.job_url"
                      :href="item.job_url"
                      target="_blank"
                      rel="noopener"
                      class="btn-104"
                      title="104 職缺"
                      @click.stop
                    >104</a>
                  </div>
                </button>

                <div v-if="expandedCompanyId === item.id" class="partner-detail company-detail">
                  <!-- 投遞建議 -->
                  <div class="recommendation-box">
                    <span class="rec-priority">#{{ item.recommendation.priority }}</span>
                    <span class="rec-summary">{{ item.recommendation.summary }}</span>
                  </div>

                  <!-- 公司流年面板 -->
                  <div class="company-fortune-panel">
                    <h5>公司流年</h5>
                    <div class="fortune-row">
                      <span class="kuyou-badge" :class="getKuyouLevelClass(item.company_fortune.kuyou_star.level)">
                        {{ item.company_fortune.kuyou_star.name }} {{ item.company_fortune.kuyou_star.level }}
                      </span>
                      <span class="fortune-score">整體 {{ item.company_fortune.overall }}</span>
                      <span class="fortune-score">事業 {{ item.company_fortune.career }}</span>
                    </div>
                  </div>

                  <!-- RC 風險說明 -->
                  <div class="rc-detail-box">
                    <h5>Reference Check</h5>
                    <span class="rc-badge" :class="getRefCheckClass(item.ref_check.risk_level)">
                      {{ item.ref_check.risk_label }}風險
                    </span>
                    <span class="rc-reason">{{ item.ref_check.reason }}</span>
                  </div>

                  <!-- Action Items -->
                  <div v-if="item.recommendation.action_items.length > 0" class="action-items">
                    <h5>行動建議</h5>
                    <ul>
                      <li v-for="(act, i) in item.recommendation.action_items" :key="i">{{ act }}</li>
                    </ul>
                  </div>

                  <!-- 方向解釋 -->
                  <div v-if="item.compatibility.relation.direction" class="direction-box">
                    <div class="direction-row">
                      <span class="direction-label">你→公司</span>
                      <span class="direction-value">{{ item.compatibility.relation.direction }}</span>
                      <span class="direction-desc">{{ directionDesc[item.compatibility.relation.direction] || '' }}</span>
                    </div>
                    <div class="direction-row">
                      <span class="direction-label">公司→你</span>
                      <span class="direction-value">{{ getInverseDirection(item.compatibility.relation.direction) }}</span>
                      <span class="direction-desc">{{ directionDesc[getInverseDirection(item.compatibility.relation.direction)] || '' }}</span>
                    </div>
                  </div>

                  <div v-if="item.memo" class="company-memo">
                    <p>{{ item.memo }}</p>
                  </div>

                  <div class="company-actions">
                    <a
                      v-if="item.job_url"
                      :href="item.job_url"
                      target="_blank"
                      rel="noopener"
                      class="btn-link-sm"
                    >104 職缺</a>
                  </div>
                  <div class="company-actions">
                    <button
                      v-if="confirmDeleteCompanyId !== item.id"
                      class="btn-delete-company"
                      @click.stop="confirmDeleteCompanyId = item.id"
                    >移除</button>
                    <button
                      v-else
                      class="btn-delete-company confirm"
                      @click.stop="deleteCompany(item.id)"
                    >確認移除</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- Fallback: 無批次資料時顯示原有的 companyCompatibilities (僅 self) -->
      <div v-else-if="isSelf && companyCompatibilities.length > 0 && !currentBatchLoading" class="saved-companies">
        <h4 class="saved-title">已收藏公司 ({{ companyCompatibilities.length }})</h4>
        <div class="partner-list">
          <div
            v-for="cc in companyCompatibilities"
            :key="cc.companyId"
            class="partner-card-wrapper"
          >
            <button
              class="partner-card"
              :class="[getScoreClass(cc.score), { expanded: expandedCompanyId === cc.companyId }]"
              :aria-expanded="expandedCompanyId === cc.companyId"
              @click="toggleCompany(cc.companyId)"
            >
              <div class="partner-info">
                <span class="partner-name">
                  <a
                    v-if="cc.jobUrl"
                    :href="cc.jobUrl"
                    target="_blank"
                    rel="noopener"
                    class="company-name-link"
                    title="開啟 104 職缺"
                    @click.stop
                  >{{ cc.companyName }}</a>
                  <template v-else>{{ cc.companyName }}</template>
                </span>
                <span class="partner-mansion">{{ cc.mansion.name_jp }}（{{ cc.mansion.reading }}）</span>
              </div>
              <div class="partner-relation">
                <span class="relation-name">{{ cc.relation.name }}</span>
                <div class="company-verdict-mini">
                  <span
                    class="verdict-badge-mini"
                    :class="getCompanyVerdict(cc.relation).level"
                  >{{ getCompanyVerdict(cc.relation).text }}</span>
                </div>
              </div>
              <div class="partner-score-area">
                <span class="score-num">{{ cc.score }}</span>
                <a
                  v-if="cc.jobUrl"
                  :href="cc.jobUrl"
                  target="_blank"
                  rel="noopener"
                  class="btn-104"
                  title="104 職缺"
                  @click.stop
                >104</a>
              </div>
            </button>

            <div v-if="expandedCompanyId === cc.companyId" class="partner-detail company-detail">
              <div class="verdict-detail">
                {{ getCompanyVerdict(cc.relation).detail }}
              </div>

              <div v-if="cc.relation.direction" class="direction-box">
                <div class="direction-row">
                  <span class="direction-label">你→公司</span>
                  <span class="direction-value">{{ cc.relation.direction }}</span>
                  <span class="direction-desc">{{ directionDesc[cc.relation.direction] || '' }}</span>
                </div>
                <div class="direction-row">
                  <span class="direction-label">公司→你</span>
                  <span class="direction-value">{{ getInverseDirection(cc.relation.direction) }}</span>
                  <span class="direction-desc">{{ directionDesc[getInverseDirection(cc.relation.direction)] || '' }}</span>
                </div>
              </div>

              <div v-if="cc.calculation" class="element-relation-box">
                <span class="element-tag" :style="{ background: elementColors[cc.calculation.person1_element || ''] }">{{ cc.calculation.person1_element || '' }}</span>
                <span class="element-arrow">→</span>
                <span class="element-tag" :style="{ background: elementColors[cc.calculation.person2_element || ''] }">{{ cc.calculation.person2_element || '' }}</span>
                <span class="element-desc">{{ getElementDesc(cc.calculation.person1_element || '', cc.calculation.person2_element || '', cc.calculation.element_relation || '') }}</span>
              </div>

              <div class="compat-detail">
                <p>{{ cc.relation.description }}</p>
                <p v-if="cc.summary">{{ cc.summary }}</p>
              </div>

              <div v-if="cc.companyMemo" class="company-memo">
                <p>{{ cc.companyMemo }}</p>
              </div>

              <div class="company-actions">
                <a
                  v-if="cc.jobUrl"
                  :href="cc.jobUrl"
                  target="_blank"
                  rel="noopener"
                  class="btn-link-sm"
                >104 職缺</a>
              </div>
              <div class="company-actions">
                <button
                  v-if="confirmDeleteCompanyId !== cc.companyId"
                  class="btn-delete-company"
                  @click.stop="confirmDeleteCompanyId = cc.companyId"
                >移除</button>
                <button
                  v-else
                  class="btn-delete-company confirm"
                  @click.stop="deleteCompany(cc.companyId)"
                >確認移除</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="companyCompatLoading2" class="loading-state">
        <sl-spinner></sl-spinner>
      </div>
    </div>

    <!-- Partners -->
    <div v-if="activeTab === 'partners'" id="panel-match-partners" class="match-content" role="tabpanel">
      <template v-if="partnersWithBirthDate.length === 0">
        <div class="empty-partners">
          <p>尚未設定收藏對象</p>
          <button class="btn-link" @click="emit('navigate-lucky')">前往設定</button>
        </div>
      </template>
      <template v-else-if="partnerCompatLoading">
        <div class="loading-state">
          <sl-spinner></sl-spinner>
        </div>
      </template>
      <template v-else>
        <div class="partner-list">
          <div
            v-for="pc in partnerCompatibilities"
            :key="pc.partnerId"
            class="partner-card-wrapper"
          >
            <button
              class="partner-card"
              :class="[getScoreClass(pc.score), { expanded: expandedPartnerId === pc.partnerId }]"
              :aria-expanded="expandedPartnerId === pc.partnerId"
              @click="togglePartner(pc.partnerId)"
            >
              <div class="partner-info">
                <span class="partner-name">{{ pc.nickname }}</span>
                <span class="partner-mansion">{{ pc.mansion.name_jp }}（{{ pc.mansion.reading }}）</span>
              </div>
              <div class="partner-relation">
                <span class="relation-name term-link" @click.stop="emit('navigate-knowledge', 'relations')">{{ pc.relation.name }}</span>
                <span v-if="pc.relation.distance_type_name" class="distance-tag term-link" :class="pc.relation.distance_type" @click.stop="emit('navigate-knowledge', 'relations')">{{ pc.relation.distance_type_name }}</span>
                <div v-if="pc.relation.direction" class="partner-directions">
                  <span class="dir-tag">你→{{ pc.relation.direction }}</span>
                  <span class="dir-tag">{{ pc.nickname.charAt(0) }}→{{ getInverseDirection(pc.relation.direction) }}</span>
                </div>
                <span v-if="pc.calculation?.element_relation" class="element-mini-tag">{{ pc.calculation.element_relation.replace(/[+\-]\d+\s*分/, '').trim() }}</span>
              </div>
              <div class="partner-score">
                <span class="score-num">{{ pc.score }}</span>
              </div>
            </button>

            <div v-if="expandedPartnerId === pc.partnerId" class="partner-detail">
              <!-- 方向解釋 -->
              <div v-if="pc.relation.direction" class="direction-box">
                <div class="direction-row">
                  <span class="direction-label">你→{{ pc.nickname }}</span>
                  <span class="direction-value">{{ pc.relation.direction }}</span>
                  <span class="direction-desc">{{ directionDesc[pc.relation.direction] || '' }}</span>
                </div>
                <div class="direction-row">
                  <span class="direction-label">{{ pc.nickname }}→你</span>
                  <span class="direction-value">{{ getInverseDirection(pc.relation.direction) }}</span>
                  <span class="direction-desc">{{ directionDesc[getInverseDirection(pc.relation.direction)] || '' }}</span>
                </div>
              </div>

              <!-- 元素關係 -->
              <div v-if="pc.calculation" class="element-relation-box">
                <span class="element-tag" :style="{ background: elementColors[pc.calculation.person1_element || ''] }">{{ pc.calculation.person1_element || '' }}</span>
                <span class="element-arrow">→</span>
                <span class="element-tag" :style="{ background: elementColors[pc.calculation.person2_element || ''] }">{{ pc.calculation.person2_element || '' }}</span>
                <span class="element-desc term-link" @click="emit('navigate-knowledge', 'elements')">{{ getElementDesc(pc.calculation.person1_element || '', pc.calculation.person2_element || '', pc.calculation.element_relation || '') }}</span>
              </div>

              <div class="compat-detail">
                <p>{{ pc.relation.description }}</p>
                <p v-if="pc.summary">{{ pc.summary }}</p>
              </div>

              <!-- 適合場景 -->
              <div v-if="pc.relation.good_for?.length" class="good-for-section">
                <h5>適合場景</h5>
                <div class="good-for-tags">
                  <span v-for="(gf, i) in pc.relation.good_for" :key="i" class="good-for-tag">{{ gf }}</span>
                </div>
              </div>

              <div v-if="pc.relation.love || pc.relation.career" class="compat-aspects">
                <div v-if="pc.relation.love" class="aspect-section">
                  <h5>愛情面向</h5>
                  <p>{{ pc.relation.love }}</p>
                </div>
                <div v-if="pc.relation.career" class="aspect-section">
                  <h5>事業面向</h5>
                  <p>{{ pc.relation.career }}</p>
                </div>
              </div>

              <div v-if="pc.relation.roles && Object.keys(pc.relation.roles).length" class="role-advice">
                <h5>角色別相處指南</h5>
                <div class="role-grid">
                  <div
                    v-for="(desc, role) in pc.relation.roles"
                    :key="role"
                    class="role-card"
                  >
                    <h6 class="role-label">{{ roleLabels[role] || role }}</h6>
                    <p>{{ desc }}</p>
                  </div>
                </div>
              </div>

              <div class="compat-advice">
                <h5>相處建議</h5>
                <p>{{ pc.relation.advice }}</p>
                <div v-if="pc.relation.tips?.length" class="tips">
                  <h6>小技巧</h6>
                  <ul>
                    <li v-for="(tip, i) in pc.relation.tips" :key="i">{{ tip }}</li>
                  </ul>
                </div>
                <div v-if="pc.relation.avoid?.length" class="avoid-list">
                  <h6>避免事項</h6>
                  <ul>
                    <li v-for="(a, i) in pc.relation.avoid" :key="i">{{ a }}</li>
                  </ul>
                </div>
              </div>

              <div class="partner-export-row">
                <button
                  class="export-btn"
                  :disabled="partnerPairedLoading === pc.partnerId || !birthDate || !mansion"
                  @click="handlePartnerPairedReport(pc)"
                >
                  <sl-spinner v-if="partnerPairedLoading === pc.partnerId"></sl-spinner>
                  <span v-else>匯出雙人流年</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </section>
</template>

<style scoped>
/* Seeker Tabs */
.seeker-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: var(--space-md);
  flex-wrap: wrap;
}

.seeker-tab {
  padding: 6px 16px;
  border-radius: var(--radius-full, 20px);
  border: 1px solid var(--border);
  background: var(--bg-surface);
  color: var(--text-secondary);
  font-size: var(--font-sm);
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 6px;
}

.seeker-tab:hover {
  border-color: var(--accent);
  color: var(--text-primary);
}

.seeker-tab.active {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}

.seeker-tab.seeker-add {
  padding: 6px 12px;
  font-weight: 600;
  font-size: var(--font-base);
}

.seeker-delete {
  font-size: 10px;
  opacity: 0.5;
  cursor: pointer;
  line-height: 1;
}

.seeker-delete:hover {
  opacity: 1;
}

.seeker-delete-confirm {
  font-size: 10px;
  color: var(--warning);
  cursor: pointer;
  font-weight: 600;
}

/* Add Seeker Dialog */
.seeker-dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.seeker-dialog {
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  width: min(90vw, 360px);
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.seeker-dialog h4 {
  margin: 0;
  font-size: var(--font-lg);
}

.seeker-dialog-actions {
  display: flex;
  gap: var(--space-sm);
  justify-content: flex-end;
}

.btn-secondary {
  padding: 8px 16px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border);
  background: var(--bg-surface);
  cursor: pointer;
  font-size: var(--font-sm);
}

.sub-tabs {
  display: flex;
  gap: var(--space-sm);
  margin-bottom: var(--space-lg);
}

.match-content {
  animation: fadeIn 0.3s ease;
}

.relation-grid {
  display: grid;
  gap: var(--space-md);
}

.relation-section {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: var(--space-md);
}

.relation-section.excellent { border-left: 3px solid var(--stellar); }
.relation-section.good { border-left: 3px solid var(--success); }
.relation-section.fair { border-left: 3px solid var(--info); }
.relation-section.neutral { border-left: 3px solid var(--text-secondary); }
.relation-section.caution { border-left: 3px solid var(--caution); }
.relation-section.warning { border-left: 3px solid var(--warning); }

.relation-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: var(--font-base);
  margin: 0 0 var(--space-xs);
}

.relation-score {
  font-size: var(--font-sm);
  color: var(--text-secondary);
}

.relation-desc {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  margin: 0 0 var(--space-sm);
}

.relation-detailed {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0 0 var(--space-md);
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-sm);
}

.mansion-chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.mansion-chip {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-xs) var(--space-sm);
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-full);
  color: var(--text-primary);
  font-size: var(--font-sm);
  cursor: pointer;
  transition: background-color 0.2s, border-color 0.2s;
}

.mansion-chip:hover {
  border-color: var(--accent);
}

.mansion-chip.active {
  background: var(--accent);
  border-color: var(--accent);
  color: var(--text-on-accent);
}

.mansion-chip:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.mansion-chip {
  min-height: 44px;
}

.chip-element {
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  font-size: var(--font-xs);
  color: var(--text-on-accent);
}

.mansion-detail {
  margin-top: var(--space-lg);
  padding: var(--space-lg);
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
}

/* Finder Intro */
.finder-intro {
  margin-bottom: var(--space-lg);
  padding: var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  border-left: 3px solid var(--accent);
}

.finder-intro p {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0;
}

.mansion-detail h4 {
  font-size: var(--font-lg);
  margin: 0 0 var(--space-sm);
}

.mansion-detail p {
  color: var(--text-secondary);
  font-size: var(--font-sm);
  margin: 0 0 var(--space-md);
}

.keywords {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
  margin-bottom: var(--space-md);
}

.keyword {
  padding: var(--space-xs) var(--space-sm);
  background: var(--bg-elevated);
  border-radius: var(--radius-sm);
  font-size: var(--font-xs);
  color: var(--text-secondary);
}

/* Lunar Dates */
.lunar-dates {
  margin-top: var(--space-md);
  padding-top: var(--space-md);
  border-top: 1px solid var(--border);
}

.lunar-dates h5 {
  font-size: var(--font-sm);
  color: var(--accent);
  margin: 0 0 var(--space-sm);
}

.lunar-date-chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.lunar-date-chip {
  padding: var(--space-xs) var(--space-sm);
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: var(--font-xs);
  color: var(--text-secondary);
}

/* Compatibility Form */
.compat-form {
  display: flex;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}

.compat-form sl-input {
  flex: 1;
  --sl-input-background-color: var(--bg-surface);
  --sl-input-border-color: var(--border);
  --sl-input-color: var(--text-primary);
  --sl-input-label-color: var(--text-secondary);
}

.btn-primary {
  padding: var(--space-sm) var(--space-lg);
  background: var(--accent);
  border: none;
  border-radius: var(--radius-md);
  color: var(--text-on-accent);
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-primary:hover {
  background: var(--accent-hover);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.error-msg {
  color: var(--warning);
  font-size: var(--font-sm);
  padding: var(--space-sm);
  background: rgba(197, 48, 48, 0.08);
  border-radius: var(--radius-sm);
  margin-bottom: var(--space-md);
}

.compat-result {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
}

.compat-result-header {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  position: relative;
  margin-bottom: var(--space-lg);
}

.compat-result-header .compat-score {
  margin-bottom: 0;
}

.export-btns {
  position: absolute;
  right: 0;
  top: 0;
  display: flex;
  gap: var(--space-xs);
}

.compat-result-header .export-btn {
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
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
}

.compat-result-header .export-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.compat-result-header .export-btn:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.compat-result-header .export-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.compat-score {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: var(--space-lg);
}

.compat-score .score-num {
  font-size: 64px;
  font-weight: 700;
  line-height: 1;
  font-variant-numeric: tabular-nums;
}

.compat-score .score-text {
  font-size: var(--font-lg);
  margin-top: var(--space-sm);
}

.compat-score.excellent .score-num,
.compat-score.excellent .score-text { color: var(--stellar); }
.compat-score.good .score-num,
.compat-score.good .score-text { color: var(--success); }
.compat-score.fair .score-num,
.compat-score.fair .score-text { color: var(--info); }
.compat-score.warning .score-num,
.compat-score.warning .score-text { color: var(--warning); }

.compat-persons {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: var(--space-lg);
  margin-bottom: var(--space-lg);
}

.person-card {
  text-align: center;
  padding: var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  min-width: 100px;
}

.person-card h5 {
  margin: 0 0 var(--space-xs);
  color: var(--text-secondary);
  font-size: var(--font-sm);
}

.person-mansion {
  font-size: var(--font-lg);
  font-weight: 600;
  margin: 0 0 var(--space-xs);
}

.person-element {
  padding: var(--space-xs) var(--space-sm);
  background: var(--accent);
  border-radius: var(--radius-sm);
  color: var(--text-on-accent);
  font-size: var(--font-xs);
}

.relation-arrow {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.relation-arrow .relation-name {
  font-size: var(--font-lg);
  font-weight: 600;
  color: var(--accent);
}

.relation-arrow .relation-reading {
  font-size: var(--font-sm);
  color: var(--text-secondary);
}

.distance-tag {
  display: inline-block;
  margin-top: var(--space-xs);
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-size: var(--font-xs);
  font-weight: 500;
}

.distance-tag.near {
  background: var(--success);
  color: var(--text-on-accent);
}

.distance-tag.mid {
  background: var(--info);
  color: var(--text-on-accent);
}

.distance-tag.far {
  background: var(--text-secondary);
  color: var(--text-on-accent);
}

/* Direction Box */
.direction-box {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  padding: var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-lg);
}

.direction-row {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

.direction-label {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  min-width: 80px;
}

.direction-value {
  font-weight: 600;
  font-size: var(--font-base);
  color: var(--accent);
  min-width: 24px;
}

.direction-desc {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  word-break: break-word;
}

/* Classical Analysis */
.classical-analysis-box {
  padding: var(--space-md);
  background: var(--bg-elevated);
  border: 1px solid var(--border-gold);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-lg);
}

.classical-header {
  display: flex;
  align-items: baseline;
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
}

.classical-header h5 {
  margin: 0;
  font-family: var(--font-display);
  font-size: var(--font-lg);
  color: var(--stellar-gold);
}

.classical-source {
  font-size: var(--font-xs);
  color: var(--text-muted);
}

.classical-directions {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.classical-direction {
  padding: var(--space-sm) 0;
}

.classical-direction + .classical-direction {
  border-top: 1px solid var(--border-subtle);
  padding-top: var(--space-md);
}

.classical-direction-title {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
  font-size: var(--font-sm);
  color: var(--text-secondary);
}

.classical-position-badge {
  display: inline-block;
  padding: 2px var(--space-sm);
  background: var(--stellar-gold);
  color: var(--text-on-accent);
  border-radius: var(--radius-full);
  font-size: var(--font-xs);
  font-weight: 600;
}

.classical-sutra {
  margin: var(--space-sm) 0;
  padding: var(--space-sm) var(--space-md);
  border-left: 3px solid var(--stellar-gold);
  background: var(--scroll-cream);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  font-family: var(--font-display);
  font-size: var(--font-sm);
  line-height: 1.8;
  color: var(--text-primary);
}

.classical-sutra cite {
  display: block;
  margin-top: var(--space-xs);
  font-size: var(--font-xs);
  color: var(--text-muted);
  font-style: normal;
}

.classical-interpretation {
  margin: var(--space-sm) 0 0;
  font-size: var(--font-sm);
  line-height: 1.7;
  color: var(--text-secondary);
}

@media (max-width: 767px) {
  .classical-header {
    flex-direction: column;
    gap: var(--space-xs);
  }
}

/* Element Relation */
.element-relation-box {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-lg);
  flex-wrap: wrap;
}

.element-tag {
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-size: var(--font-sm);
  font-weight: 500;
  color: var(--text-on-accent);
}

.element-arrow {
  color: var(--text-secondary);
  font-size: var(--font-sm);
}

.element-desc {
  font-size: var(--font-sm);
  color: var(--text-secondary);
}

/* Good For */
.good-for-section {
  margin-bottom: var(--space-lg);
}

.good-for-section h5 {
  font-size: var(--font-sm);
  color: var(--accent);
  margin: 0 0 var(--space-sm);
}

.good-for-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.good-for-tag {
  padding: var(--space-xs) var(--space-sm);
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-full);
  font-size: var(--font-xs);
  color: var(--text-secondary);
}

/* Avoid List */
.avoid-list {
  margin-top: var(--space-md);
}

.avoid-list h6 {
  color: var(--warning);
  font-size: var(--font-sm);
  margin: 0 0 var(--space-xs);
}

.avoid-list ul {
  margin: 0;
  padding-left: var(--space-lg);
}

.avoid-list li {
  color: var(--text-secondary);
  font-size: var(--font-sm);
  margin-bottom: var(--space-xs);
}

.compat-detail {
  margin-bottom: var(--space-lg);
}

.compat-detail p {
  color: var(--text-secondary);
  font-size: var(--font-sm);
  line-height: 1.6;
  margin: 0 0 var(--space-sm);
  word-break: break-word;
}

.compat-aspects {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
  padding: var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
}

.aspect-section h5 {
  font-size: var(--font-sm);
  color: var(--accent);
  margin: 0 0 var(--space-xs);
}

.aspect-section p {
  color: var(--text-secondary);
  font-size: var(--font-sm);
  line-height: 1.6;
  margin: 0;
}

.compat-advice h5 {
  color: var(--accent);
  font-size: var(--font-base);
  margin: 0 0 var(--space-sm);
}

.compat-advice p {
  color: var(--text-secondary);
  font-size: var(--font-sm);
  line-height: 1.6;
  margin: 0 0 var(--space-md);
}

/* Role Advice */
.role-advice {
  margin-bottom: var(--space-lg);
}

.role-advice > h5 {
  color: var(--accent);
  font-size: var(--font-base);
  margin: 0 0 var(--space-md);
}

.role-grid {
  display: grid;
  gap: var(--space-md);
}

.role-card {
  padding: var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  border-left: 3px solid var(--border);
}

.role-card h6.role-label {
  color: var(--text-primary);
  font-size: var(--font-sm);
  font-weight: 600;
  margin: 0 0 var(--space-sm);
}

.role-card p {
  color: var(--text-secondary);
  font-size: var(--font-sm);
  line-height: 1.6;
  margin: 0;
}

.tips h6 {
  color: var(--text-primary);
  font-size: var(--font-sm);
  margin: 0 0 var(--space-xs);
}

.tips ul {
  margin: 0;
  padding-left: var(--space-lg);
}

.tips li {
  color: var(--text-secondary);
  font-size: var(--font-sm);
  margin-bottom: var(--space-xs);
}

/* Partners */
.empty-partners {
  text-align: center;
  padding: var(--space-2xl);
}

.empty-partners p {
  color: var(--text-secondary);
  margin-bottom: var(--space-md);
}

.btn-link {
  color: var(--accent);
  text-decoration: none;
}

.btn-link:hover {
  text-decoration: underline;
}

.partner-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.partner-card-wrapper {
  display: flex;
  flex-direction: column;
}

.partner-card {
  display: flex;
  align-items: center;
  padding: var(--space-md);
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  cursor: pointer;
  font: inherit;
  color: inherit;
  text-align: left;
  width: 100%;
  transition: background-color 0.2s, border-color 0.2s;
}

.partner-card:hover {
  background: var(--bg-elevated);
  border-color: var(--accent);
}

.partner-card:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.partner-card.expanded {
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
  border-color: var(--accent);
  background: var(--bg-elevated);
}

.partner-card.excellent { border-left: 3px solid var(--stellar); }
.partner-card.good { border-left: 3px solid var(--success); }
.partner-card.fair { border-left: 3px solid var(--info); }
.partner-card.caution { border-left: 3px solid var(--caution); }
.partner-card.warning { border-left: 3px solid var(--warning); }

.partner-info {
  flex: 1;
}

.partner-name {
  display: block;
  font-weight: 600;
  margin-bottom: var(--space-xs);
}

.partner-mansion {
  font-size: var(--font-sm);
  color: var(--text-secondary);
}

.partner-relation {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-xs);
  padding: 0 var(--space-md);
}

.partner-relation .relation-name {
  color: var(--accent);
  font-size: var(--font-sm);
}

.partner-directions {
  display: flex;
  gap: 4px;
}

.dir-tag {
  font-size: var(--font-xs);
  color: var(--text-secondary);
  padding: 1px 6px;
  background: var(--bg-elevated);
  border-radius: var(--radius-sm);
  white-space: nowrap;
}

.element-mini-tag {
  font-size: var(--font-xs);
  color: var(--text-secondary);
  padding: 1px 6px;
  background: var(--bg-elevated);
  border-radius: var(--radius-sm);
  white-space: nowrap;
}

.partner-score .score-num,
.partner-score-area .score-num {
  font-size: var(--font-xl);
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.partner-score-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.btn-104 {
  display: inline-block;
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 600;
  color: var(--bg-surface);
  background: var(--accent);
  border-radius: var(--radius-sm);
  text-decoration: none;
  line-height: 1.4;
  white-space: nowrap;
}

.btn-104:hover {
  opacity: 0.85;
}

.company-name-link {
  color: inherit;
  text-decoration: underline;
  text-decoration-color: var(--accent);
  text-underline-offset: 2px;
}

.company-name-link:hover {
  color: var(--accent);
}

.partner-detail {
  padding: var(--space-md);
  background: var(--bg-surface);
  border: 1px solid var(--accent);
  border-top: none;
  border-radius: 0 0 var(--radius-md) var(--radius-md);
  animation: slideDown 0.2s ease;
}

.partner-detail .compat-detail {
  margin-bottom: var(--space-md);
}

.partner-detail .compat-aspects {
  margin-bottom: var(--space-md);
}

.partner-detail .compat-advice {
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  border-left: 3px solid var(--accent);
}

.partner-export-row {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--space-md);
}

.partner-export-row .export-btn {
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
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
}

.partner-export-row .export-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.partner-export-row .export-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}

.loading-state {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: var(--space-2xl);
}

@media (max-width: 767px) {
  .compat-result-header {
    flex-direction: column;
    gap: var(--space-sm);
  }

  .export-btns {
    position: static;
    justify-content: center;
  }

  .compat-form {
    flex-direction: column;
  }

  .compat-result {
    padding: var(--space-md);
  }

  .compat-score .score-num {
    font-size: 48px;
  }

  .compat-persons {
    flex-direction: column;
  }

  .relation-arrow {
    transform: rotate(90deg);
    margin: var(--space-sm) 0;
  }

  .mansion-detail {
    padding: var(--space-md);
  }

  .partner-card {
    padding: var(--space-sm) var(--space-md);
  }

  .partner-relation {
    padding: 0 var(--space-sm);
  }

  .partner-detail {
    padding: var(--space-sm);
  }

  .direction-label {
    min-width: 60px;
  }

  .relation-section {
    padding: var(--space-sm);
  }
}

/* Company */
.company-intro {
  margin-bottom: var(--space-lg);
  padding: var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  border-left: 3px solid var(--accent);
}

.company-intro p {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0;
}

.company-form {
  display: flex;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
  align-items: flex-end;
}

.company-form sl-input {
  flex: 1;
  --sl-input-background-color: var(--bg-surface);
  --sl-input-border-color: var(--border);
  --sl-input-color: var(--text-primary);
  --sl-input-label-color: var(--text-secondary);
}

.gcis-input-wrapper {
  position: relative;
  flex: 1;
}

.gcis-input-wrapper sl-input {
  width: 100%;
}

.gcis-spinner {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 16px;
  --indicator-color: var(--accent);
}

.gcis-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 10;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  max-height: 240px;
  overflow-y: auto;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  margin-top: 4px;
}

.gcis-option {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 12px;
  cursor: pointer;
  border-bottom: 1px solid var(--border);
  transition: background-color 0.15s;
}

.gcis-option:last-child {
  border-bottom: none;
}

.gcis-option:hover {
  background: var(--bg-elevated);
}

.gcis-name {
  font-weight: 600;
  color: var(--text-primary);
  font-size: var(--font-sm);
}

.gcis-meta {
  font-size: 12px;
  color: var(--text-secondary);
}

.gcis-empty {
  padding: 12px;
  font-size: var(--font-sm);
  color: var(--text-secondary);
  text-align: center;
}

.company-result {
  position: relative;
}

.company-verdict-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-lg);
  margin-bottom: var(--space-md);
}

.verdict-badge {
  padding: var(--space-xs) var(--space-md);
  border-radius: var(--radius-full);
  font-weight: 600;
  font-size: var(--font-base);
}

.verdict-badge.recommend {
  background: var(--success);
  color: var(--text-on-accent);
}

.verdict-badge.caution {
  background: var(--caution);
  color: var(--bg-primary);
}

.verdict-badge.avoid {
  background: var(--warning);
  color: var(--text-on-accent);
}

.verdict-detail {
  text-align: center;
  font-size: var(--font-sm);
  color: var(--text-secondary);
  margin-bottom: var(--space-lg);
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
}

.btn-save-company {
  width: 100%;
  padding: var(--space-sm);
  min-height: 44px;
  margin-top: var(--space-md);
  background: transparent;
  border: 1px dashed var(--accent);
  border-radius: var(--radius-md);
  color: var(--accent);
  font-size: var(--font-sm);
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-save-company:hover {
  background: rgba(139, 105, 20, 0.1);
}

.saved-companies {
  margin-top: var(--space-xl);
}

.saved-title {
  font-size: var(--font-base);
  color: var(--accent);
  margin: 0 0 var(--space-md);
}

.verdict-badge-mini {
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-size: var(--font-xs);
  font-weight: 600;
}

.verdict-badge-mini.recommend {
  background: var(--success);
  color: var(--text-on-accent);
}

.verdict-badge-mini.caution {
  background: var(--caution);
  color: var(--bg-primary);
}

.verdict-badge-mini.avoid {
  background: var(--warning);
  color: var(--text-on-accent);
}

.company-verdict-mini {
  margin-top: 2px;
}

.import-section {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin: var(--space-md) 0;
}

.btn-import-companies {
  padding: var(--space-xs) var(--space-md);
  background: var(--surface-c, #d4c5a9);
  color: var(--text-primary, #3d3425);
  border: none;
  border-radius: var(--radius-sm, 4px);
  cursor: pointer;
  font-size: 0.85rem;
}

.btn-import-companies:hover {
  background: var(--surface-d, #c4b599);
}

.import-hint {
  font-size: 0.8rem;
  color: var(--text-secondary, #6b5e4f);
}

.company-memo {
  margin-top: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  background: var(--surface-b, #f5f0e8);
  border-radius: var(--radius-sm, 4px);
  font-size: 0.85rem;
  color: var(--text-secondary, #6b5e4f);
  word-break: break-all;
}

.company-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--space-md);
}

.btn-delete-company {
  padding: var(--space-xs) var(--space-md);
  min-height: 36px;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius-full);
  color: var(--text-secondary);
  font-size: var(--font-sm);
  cursor: pointer;
  transition: background-color 0.2s, border-color 0.2s, color 0.2s;
}

.btn-delete-company:hover {
  border-color: var(--warning);
  color: var(--warning);
}

.btn-delete-company.confirm {
  border-color: var(--warning);
  background: var(--warning);
  color: var(--text-on-accent);
}

@media (max-width: 767px) {
  .company-form {
    flex-direction: column;
  }

  .company-verdict-header {
    flex-direction: column;
    gap: var(--space-sm);
  }
}

/* Auto Search */
.auto-search-section {
  margin-bottom: var(--space-lg);
}

.section-title {
  font-size: var(--font-base);
  color: var(--accent);
  margin: 0 0 var(--space-xs);
}

.section-desc {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  margin: 0 0 var(--space-md);
}

.auto-search-form {
  display: flex;
  gap: var(--space-md);
  align-items: flex-end;
  margin-bottom: var(--space-md);
}

.auto-search-form sl-input {
  flex: 1;
  --sl-input-background-color: var(--bg-surface);
  --sl-input-border-color: var(--border);
  --sl-input-color: var(--text-primary);
  --sl-input-label-color: var(--text-secondary);
}

.auto-search-form .form-row {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  min-width: 160px;
}

.auto-search-form .form-label {
  font-size: var(--font-sm);
  color: var(--text-secondary);
}

.btn-search {
  white-space: nowrap;
  min-width: 140px;
}

.search-progress {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  font-size: var(--font-sm);
  color: var(--text-secondary);
  margin-bottom: var(--space-md);
}

.results-title {
  font-size: var(--font-sm);
  color: var(--accent);
  margin: var(--space-md) 0 var(--space-sm);
}

.search-result-card {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: var(--space-md);
  transition: border-color 0.2s;
}

.search-result-card.recommend { border-left: 3px solid var(--success); }
.search-result-card.caution { border-left: 3px solid var(--caution); }
.search-result-card.avoid { border-left: 3px solid var(--warning); }

.result-main {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.result-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.result-name {
  font-weight: 600;
  font-size: var(--font-base);
}

.result-job {
  font-size: var(--font-sm);
  color: var(--text-secondary);
}

.result-location {
  font-size: var(--font-xs);
  color: var(--text-secondary);
}

.result-compat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-xs);
  padding: 0 var(--space-sm);
}

.result-compat .result-relation {
  font-size: var(--font-sm);
  color: var(--accent);
}

.result-score .score-num {
  font-size: var(--font-xl);
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.result-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: var(--space-sm);
  padding-top: var(--space-sm);
  border-top: 1px solid var(--border);
}

.result-mansions {
  font-size: var(--font-xs);
  color: var(--text-secondary);
}

.result-btns {
  display: flex;
  gap: var(--space-sm);
}

.btn-link-sm {
  padding: var(--space-xs) var(--space-sm);
  font-size: var(--font-xs);
  color: var(--text-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  text-decoration: none;
  transition: border-color 0.2s, color 0.2s;
}

.btn-link-sm:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.btn-save-sm {
  padding: var(--space-xs) var(--space-sm);
  font-size: var(--font-xs);
  background: transparent;
  color: var(--accent);
  border: 1px dashed var(--accent);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-save-sm:hover {
  background: rgba(139, 105, 20, 0.1);
}

.section-divider {
  border: none;
  border-top: 1px solid var(--border);
  margin: var(--space-xl) 0;
}

@media (max-width: 767px) {
  .auto-search-form {
    flex-direction: column;
  }

  .result-main {
    flex-wrap: wrap;
  }

  .result-compat {
    flex-direction: row;
    padding: 0;
    margin-top: var(--space-xs);
  }
}

/* Batch Analysis */
.batch-analysis {
  margin-top: var(--space-lg);
}

.user-fortune-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-md);
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-md);
}

.banner-left {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.banner-label {
  font-size: var(--font-sm);
  color: var(--text-secondary);
}

.banner-right {
  display: flex;
  gap: var(--space-md);
}

.banner-score {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  font-variant-numeric: tabular-nums;
}

.kuyou-badge {
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-size: var(--font-xs);
  font-weight: 600;
}

.kuyou-badge-sm {
  padding: 1px 6px;
  border-radius: var(--radius-full);
  font-size: 10px;
  font-weight: 600;
}

.kuyou-daikichi {
  background: var(--stellar);
  color: var(--text-on-accent);
}

.kuyou-hankichi {
  background: var(--success);
  color: var(--text-on-accent);
}

.kuyou-suekichi {
  background: var(--caution);
  color: var(--bg-primary);
}

.kuyou-daikyo {
  background: var(--warning);
  color: var(--text-on-accent);
}

.tier-summary-row {
  display: flex;
  gap: var(--space-sm);
  margin-bottom: var(--space-lg);
  flex-wrap: wrap;
}

.tier-count {
  padding: var(--space-xs) var(--space-md);
  border-radius: var(--radius-full);
  font-size: var(--font-sm);
  font-weight: 600;
}

.tier-count.tier-1 {
  background: var(--stellar);
  color: var(--text-on-accent);
}

.tier-count.tier-2 {
  background: var(--success);
  color: var(--text-on-accent);
}

.tier-count.tier-3 {
  background: var(--caution);
  color: var(--bg-primary);
}

.tier-count.tier-4 {
  background: var(--warning);
  color: var(--text-on-accent);
}

.tier-group {
  margin-bottom: var(--space-lg);
}

.tier-group-title {
  font-size: var(--font-base);
  margin: 0 0 var(--space-sm);
  padding-bottom: var(--space-xs);
  border-bottom: 2px solid var(--border);
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.tier-group-title.tier-1 { color: var(--stellar); border-bottom-color: var(--stellar); }
.tier-group-title.tier-2 { color: var(--success); border-bottom-color: var(--success); }
.tier-group-title.tier-3 { color: var(--caution); border-bottom-color: var(--caution); }
.tier-group-title.tier-4 { color: var(--warning); border-bottom-color: var(--warning); }

.tier-group-count {
  font-size: var(--font-xs);
  opacity: 0.7;
}

.batch-badges {
  display: flex;
  gap: 4px;
  margin-top: 2px;
}

.rc-badge-sm {
  padding: 1px 6px;
  border-radius: var(--radius-full);
  font-size: 10px;
  font-weight: 600;
}

.rc-high {
  background: var(--warning);
  color: var(--text-on-accent);
}

.rc-medium {
  background: var(--caution);
  color: var(--bg-primary);
}

.rc-low {
  background: var(--info);
  color: var(--text-on-accent);
}

.recommendation-box {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  border-left: 3px solid var(--accent);
  margin-bottom: var(--space-md);
}

.rec-priority {
  font-weight: 700;
  color: var(--accent);
  font-size: var(--font-lg);
  font-variant-numeric: tabular-nums;
}

.rec-summary {
  font-size: var(--font-sm);
  color: var(--text-secondary);
}

.company-fortune-panel {
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-md);
}

.company-fortune-panel h5 {
  font-size: var(--font-sm);
  color: var(--accent);
  margin: 0 0 var(--space-xs);
}

.fortune-row {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  flex-wrap: wrap;
}

.fortune-score {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  font-variant-numeric: tabular-nums;
}

.rc-detail-box {
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-md);
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

.rc-detail-box h5 {
  font-size: var(--font-sm);
  color: var(--accent);
  margin: 0;
  white-space: nowrap;
}

.rc-badge {
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-size: var(--font-xs);
  font-weight: 600;
  white-space: nowrap;
}

.rc-reason {
  font-size: var(--font-sm);
  color: var(--text-secondary);
}

.action-items {
  margin-bottom: var(--space-md);
}

.action-items h5 {
  font-size: var(--font-sm);
  color: var(--accent);
  margin: 0 0 var(--space-xs);
}

.action-items ul {
  margin: 0;
  padding-left: var(--space-lg);
}

.action-items li {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  margin-bottom: var(--space-xs);
}

.loading-text {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  margin-left: var(--space-sm);
}

@media (max-width: 767px) {
  .user-fortune-banner {
    flex-direction: column;
    gap: var(--space-sm);
    align-items: flex-start;
  }

  .batch-badges {
    flex-direction: row;
  }
}

/* Job Link Icon (104 連結) */
.job-link-icon {
  display: inline-flex;
  align-items: center;
  margin-left: 4px;
  color: var(--text-secondary);
  font-size: 12px;
  text-decoration: none;
  vertical-align: middle;
}

.job-link-icon:hover {
  color: var(--accent);
}

.job-link-icon .pi {
  font-size: 12px;
}

/* Partner Memo (卡片摘要) */
.partner-card .partner-memo {
  display: block;
  width: 100%;
  font-size: 12px;
  color: #888;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-top: 2px;
}

/* Lucky Dates Panel (吉凶日曆) */
.lucky-dates-panel {
  margin: 12px 0;
  padding: 12px 16px;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
}

.lucky-dates-panel.loading {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--font-sm);
  color: var(--text-secondary);
}

.lucky-dates-section {
  margin-bottom: 8px;
}

.lucky-dates-section:last-child {
  margin-bottom: 0;
}

.lucky-dates-section h5 {
  font-size: var(--font-sm);
  font-weight: 600;
  margin: 0 0 6px;
}

.good-dates h5 {
  color: var(--accent);
}

.bad-dates h5 {
  color: var(--warning, #c53030);
}

.date-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.date-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: var(--font-sm);
  cursor: default;
}

.date-chip.good {
  background: #f0e6d2;
  color: #5c4a1e;
}

.date-chip.bad {
  background: #f5e0e0;
  color: #8b2020;
}

.date-chip small {
  font-size: 11px;
  opacity: 0.7;
  font-variant-numeric: tabular-nums;
}

.dark-week-warning {
  margin-top: 8px;
  padding: 6px 12px;
  background: #333;
  color: #ffd700;
  border-radius: 4px;
  font-size: var(--font-sm);
}

@media (prefers-reduced-motion: reduce) {
  .match-content {
    animation: none;
  }
}
</style>
