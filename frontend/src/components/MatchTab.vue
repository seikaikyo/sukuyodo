<script setup lang="ts">
import { ref, nextTick } from 'vue'
import type {
  CompatibilityFinderResult,
  CompatibleMansion,
  CompatibilityResult,
  PartnerCompatibility,
  Relation
} from '../composables/useSukuyodo'
import { getScoreClass, getScoreLevel, getLocalDateStr } from '../utils/fortune-helpers'
import { generateCompatReport, generatePairedDecadeReport } from '../utils/report-generator'
import { getApiUrl } from '../config/api'

const expandedPartnerId = ref<string | null>(null)
const pairedReportLoading = ref(false)
const partnerPairedLoading = ref<string | null>(null)

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
        direction: c.relation.direction,
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
        direction: pc.relation.direction,
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

const emit = defineEmits<{
  'update:activeTab': [value: 'finder' | 'compat' | 'partners' | 'company']
  'update:selectedMansion': [value: CompatibleMansion | null]
  'update:date2': [value: string]
  'update:companyName': [value: string]
  'update:companyDate': [value: string]
  calculateCompatibility: []
  calculateCompanyCompatibility: []
  saveCompany: [data: { name: string; foundingDate: string; memo?: string }]
  removeCompany: [id: string]
  importCompanies: []
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
  '栄': '帶來好運和正能量的一方',
  '親': '親近感強、主動靠近的一方',
  '友': '主動給予、照顧的一方',
  '成': '被借力、提供價值的一方',
  '命': '本命共鳴',
  '衰': '被照顧、被影響的一方',
  '危': '帶來變化和風險的一方',
  '壊': '破壞既有模式的一方',
  '安': '被穩定、接受安撫的一方',
  '胎': '孕育可能性的一方',
  '業': '因果牽連深的一方'
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
  emit('removeCompany', id)
  confirmDeleteCompanyId.value = null
  if (expandedCompanyId.value === id) expandedCompanyId.value = null
}

interface CompanyVerdict {
  level: 'recommend' | 'caution' | 'avoid'
  text: string
  detail: string
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
      return { level: 'caution', text: '留意', detail: '你是危方，這間公司可能帶來不穩定因素' }
    }
    return { level: 'caution', text: '可考慮', detail: '你是成方（被借力），能發揮價值但留意風險' }
  }
  // 安壊
  if (type === 'ankai') {
    if (dir === '壊') {
      return { level: 'avoid', text: '避開', detail: '你是壊方，容易與這間公司產生破壞性衝突' }
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
            <span class="direction-label">你→對方</span>
            <span class="direction-value">{{ compatibility.relation.direction }}</span>
            <span class="direction-desc">{{ directionDesc[compatibility.relation.direction] || '' }}</span>
          </div>
          <div class="direction-row">
            <span class="direction-label">對方→你</span>
            <span class="direction-value">{{ getInverseDirection(compatibility.relation.direction) }}</span>
            <span class="direction-desc">{{ directionDesc[getInverseDirection(compatibility.relation.direction)] || '' }}</span>
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
      <div class="company-intro">
        <p>輸入公司設立日期，查看與你的宿曜相性。設立日期可至經濟部商業司查詢。</p>
      </div>

      <div class="company-form">
        <sl-input
          :value="companyName"
          label="公司名稱"
          placeholder="例：台積電"
          @sl-input="emit('update:companyName', ($event.target as HTMLInputElement).value)"
        ></sl-input>
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
            <span class="direction-label">你→公司</span>
            <span class="direction-value">{{ companyCompat.relation.direction }}</span>
            <span class="direction-desc">{{ directionDesc[companyCompat.relation.direction] || '' }}</span>
          </div>
          <div class="direction-row">
            <span class="direction-label">公司→你</span>
            <span class="direction-value">{{ getInverseDirection(companyCompat.relation.direction) }}</span>
            <span class="direction-desc">{{ directionDesc[getInverseDirection(companyCompat.relation.direction)] || '' }}</span>
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
          @click="emit('saveCompany', { name: companyName || '未命名公司', foundingDate: companyDate })"
        >收藏此公司</button>
      </div>

      <!-- 載入推薦清單 -->
      <div class="import-section">
        <button class="btn-import-companies" @click="emit('importCompanies')">載入推薦清單</button>
        <span class="import-hint">從 companies.json 匯入</span>
      </div>

      <!-- Saved Companies -->
      <div v-if="companyCompatibilities.length > 0" class="saved-companies">
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
                <span class="partner-name">{{ cc.companyName }}</span>
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
              <div class="partner-score">
                <span class="score-num">{{ cc.score }}</span>
              </div>
            </button>

            <div v-if="expandedCompanyId === cc.companyId" class="partner-detail company-detail">
              <div class="verdict-detail">
                {{ getCompanyVerdict(cc.relation).detail }}
              </div>

              <!-- 方向解釋 -->
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

              <!-- 元素關係 -->
              <div v-if="cc.calculation" class="element-relation-box">
                <span class="element-tag" :style="{ background: elementColors[cc.calculation.person1_element || ''] }">{{ cc.calculation.person1_element || '' }}</span>
                <span class="element-arrow">→</span>
                <span class="element-tag" :style="{ background: elementColors[cc.calculation.person2_element || ''] }">{{ cc.calculation.person2_element || '' }}</span>
                <span class="element-desc">{{ getElementDesc(cc.calculation.person1_element || '', cc.calculation.person2_element || '', cc.calculation.element_relation || '') }}</span>
              </div>

              <!-- 事業面向 -->
              <div v-if="cc.relation.career" class="compat-aspects">
                <div class="aspect-section">
                  <h5>事業面向</h5>
                  <p>{{ cc.relation.career }}</p>
                </div>
              </div>

              <div class="compat-detail">
                <p>{{ cc.relation.description }}</p>
                <p v-if="cc.summary">{{ cc.summary }}</p>
              </div>

              <div v-if="cc.companyMemo" class="company-memo">
                <p>{{ cc.companyMemo }}</p>
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

.partner-score .score-num {
  font-size: var(--font-xl);
  font-weight: 700;
  font-variant-numeric: tabular-nums;
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

@media (prefers-reduced-motion: reduce) {
  .match-content {
    animation: none;
  }
}
</style>
