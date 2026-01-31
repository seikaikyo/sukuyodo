<script setup lang="ts">
import type {
  CompatibilityFinderResult,
  CompatibleMansion,
  CompatibilityResult,
  PartnerCompatibility,
  LunarDate
} from '../composables/useSukuyodo'

const props = defineProps<{
  activeTab: 'finder' | 'compat' | 'partners'
  compatFinder: CompatibilityFinderResult | null
  finderLoading: boolean
  selectedMansion: CompatibleMansion | null
  expandedLunarDates: number[]
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
  toggleLunarDate: [ld: LunarDate]
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
            <div class="mansion-chips">
              <button
                v-for="m in (compatFinder as any)[rk.key]?.mansions"
                :key="m.index"
                class="mansion-chip"
                :class="{ active: selectedMansion?.index === m.index }"
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
          <div class="lunar-dates">
            <h5>農曆日期對照</h5>
            <div v-for="ld in selectedMansion.lunar_dates" :key="ld.lunar_month" class="lunar-date">
              <button class="lunar-toggle" :aria-expanded="expandedLunarDates.includes(ld.lunar_month)" @click="emit('toggleLunarDate', ld)">
                {{ ld.display }}
                <sl-icon :name="expandedLunarDates.includes(ld.lunar_month) ? 'chevron-up' : 'chevron-down'" aria-hidden="true"></sl-icon>
              </button>
              <div v-if="expandedLunarDates.includes(ld.lunar_month) && ld.solar_dates" class="solar-dates">
                <span v-for="sd in ld.solar_dates" :key="sd.solar_date" class="solar-date">
                  {{ sd.display }}
                </span>
              </div>
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

        <div class="compat-detail">
          <p>{{ compatibility.relation.description }}</p>
          <p>{{ compatibility.summary }}</p>
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
            class="partner-card"
            :class="getScoreClass(pc.score)"
          >
            <div class="partner-info">
              <span class="partner-name">{{ pc.nickname }}</span>
              <span class="partner-mansion">{{ pc.mansion.name_jp }}</span>
            </div>
            <div class="partner-relation">
              <span class="relation-name">{{ pc.relation.name }}</span>
            </div>
            <div class="partner-score">
              <span class="score-num">{{ pc.score }}</span>
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

.relation-section.excellent { border-left: 3px solid var(--success); }
.relation-section.good { border-left: 3px solid var(--accent); }
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

.lunar-dates h5 {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  margin: 0 0 var(--space-sm);
}

.lunar-date {
  margin-bottom: var(--space-xs);
}

.lunar-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: var(--space-sm);
  background: var(--bg-elevated);
  border: none;
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: var(--font-sm);
  cursor: pointer;
  min-height: 44px;
}

.lunar-toggle:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.solar-dates {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
  padding: var(--space-sm);
  background: var(--bg-primary);
  border-radius: var(--radius-sm);
  margin-top: var(--space-xs);
}

.solar-date {
  padding: var(--space-xs) var(--space-sm);
  background: var(--bg-surface);
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
.compat-score.excellent .score-text { color: var(--success); }
.compat-score.good .score-num,
.compat-score.good .score-text { color: var(--accent); }
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

.compat-detail {
  margin-bottom: var(--space-lg);
}

.compat-detail p {
  color: var(--text-secondary);
  font-size: var(--font-sm);
  line-height: 1.6;
  margin: 0 0 var(--space-sm);
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

.partner-card {
  display: flex;
  align-items: center;
  padding: var(--space-md);
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
}

.partner-card.excellent { border-left: 3px solid var(--success); }
.partner-card.good { border-left: 3px solid var(--accent); }
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
