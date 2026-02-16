<script setup lang="ts">
import { ref, nextTick } from 'vue'
import type {
  CompatibilityFinderResult,
  CompatibleMansion,
  CompatibilityResult,
  PartnerCompatibility
} from '../composables/useSukuyodo'
import { getScoreClass, getScoreLevel } from '../utils/fortune-helpers'

const expandedPartnerId = ref<string | null>(null)

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

const props = defineProps<{
  activeTab: 'finder' | 'compat' | 'partners'
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
}>()

const emit = defineEmits<{
  'update:activeTab': [value: 'finder' | 'compat' | 'partners']
  'update:selectedMansion': [value: CompatibleMansion | null]
  'update:date2': [value: string]
  calculateCompatibility: []
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
          :max="new Date().toISOString().split('T')[0]"
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
        <div class="compat-score" :class="getScoreLevel(compatibility.score).class">
          <span class="score-num">{{ compatibility.score }}</span>
          <span class="score-text">{{ getScoreLevel(compatibility.score).text }}</span>
        </div>

        <div class="compat-persons">
          <div class="person-card">
            <h5>你</h5>
            <p class="person-mansion">{{ compatibility.person1.mansion }}</p>
            <span class="person-element">{{ compatibility.person1.element }}</span>
          </div>
          <div class="relation-arrow">
            <span class="relation-name">
              {{ compatibility.relation.name }}
              <template v-if="compatibility.relation.direction">（{{ compatibility.relation.direction }}）</template>
            </span>
            <span class="relation-reading">{{ compatibility.relation.reading }}</span>
            <span
              v-if="compatibility.relation.distance_type_name"
              class="distance-tag"
              :class="compatibility.relation.distance_type"
            >
              {{ compatibility.relation.distance_type_name }}
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
          <span class="element-desc">{{ getElementDesc(compatibility.person1.element, compatibility.person2.element, compatibility.calculation.element_relation) }}</span>
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

    <!-- Partners -->
    <div v-if="activeTab === 'partners'" id="panel-match-partners" class="match-content" role="tabpanel">
      <template v-if="partnersWithBirthDate.length === 0">
        <div class="empty-partners">
          <p>尚未設定收藏對象</p>
          <router-link to="/profile" class="btn-link">前往設定</router-link>
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
                <span class="relation-name">{{ pc.relation.name }}</span>
                <span v-if="pc.relation.distance_type_name" class="distance-tag" :class="pc.relation.distance_type">{{ pc.relation.distance_type_name }}</span>
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
                <span class="element-desc">{{ getElementDesc(pc.calculation.person1_element || '', pc.calculation.person2_element || '', pc.calculation.element_relation || '') }}</span>
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

.pill-btn {
  padding: var(--space-sm) var(--space-md);
  min-height: 44px;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius-full);
  color: var(--text-secondary);
  font-size: var(--font-sm);
  white-space: nowrap;
  cursor: pointer;
  transition: background-color 0.2s, border-color 0.2s, color 0.2s;
}

.pill-btn:hover {
  border-color: var(--accent);
  color: var(--text-primary);
}

.pill-btn.active {
  background: var(--accent);
  border-color: var(--accent);
  color: var(--bg-primary);
}

.pill-btn:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.match-content {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
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
.relation-section.caution { border-left: 3px solid #eab308; }
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
  color: var(--bg-primary);
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
  color: var(--bg-primary);
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
  color: var(--bg-primary);
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
  background: rgba(239, 68, 68, 0.1);
  border-radius: var(--radius-sm);
  margin-bottom: var(--space-md);
}

.compat-result {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
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
  color: var(--bg-primary);
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
  color: var(--bg-primary);
}

.distance-tag.mid {
  background: var(--info);
  color: var(--bg-primary);
}

.distance-tag.far {
  background: var(--text-secondary);
  color: var(--bg-primary);
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
  color: var(--bg-primary);
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
.partner-card.caution { border-left: 3px solid #eab308; }
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
  .compat-persons {
    flex-direction: column;
  }

  .relation-arrow {
    transform: rotate(90deg);
    margin: var(--space-sm) 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .match-content {
    animation: none;
  }
}
</style>
