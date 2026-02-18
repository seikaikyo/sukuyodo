<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useSukuyodo } from '../composables/useSukuyodo'
import { useProfile, RELATION_TYPES } from '../stores/profile'
import type { RelationType } from '../stores/profile'
import { getLocalDateStr } from '../utils/fortune-helpers'
import SummaryCard from '../components/SummaryCard.vue'
import FortuneTab from '../components/FortuneTab.vue'
import MatchTab from '../components/MatchTab.vue'
import FortuneCalendar from '../components/FortuneCalendar.vue'
import LuckyDaysTab from '../components/LuckyDaysTab.vue'
import KnowledgeTab from '../components/KnowledgeTab.vue'

const {
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
  yearlyRange,
  yearlyRangeLoading,
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

  // Calendar
  calendarData,
  calendarLoading,

  // Computed
  elementColors,
  mansionElementColor,

  // API Functions
  lookupMansion,
  calculateCompatibility,
  fetchPairLuckyDays,
  clearPairSelection,
  fetchDailyFortuneForDate,
  fetchYearlyRange,
  fetchSpecialDays,
  fetchCalendarMonth,
  changeCalendarMonth,

  // Event Handlers
  quickSelect,
  toggleMonthlyWeek,

  // Init
  init
} = useSukuyodo()

const { addPartner, updatePartner, removePartner, profile } = useProfile()

// Partner management state
const showPartnerForm = ref(false)
const editingPartnerId = ref<string | null>(null)
const partnerNickname = ref('')
const partnerBirthDate = ref('')
const partnerRelation = ref<RelationType>('friend')
const confirmDeleteId = ref<string | null>(null)

function startAddPartner() {
  editingPartnerId.value = null
  partnerNickname.value = ''
  partnerBirthDate.value = ''
  partnerRelation.value = 'friend'
  showPartnerForm.value = true
}

function startEditPartner(id: string) {
  const p = profile.value.partners.find(x => x.id === id)
  if (!p) return
  editingPartnerId.value = id
  partnerNickname.value = p.nickname
  partnerBirthDate.value = p.birthDate
  partnerRelation.value = p.relation
  showPartnerForm.value = true
}

function savePartner() {
  if (!partnerNickname.value.trim() || !partnerBirthDate.value) return
  if (editingPartnerId.value) {
    updatePartner(editingPartnerId.value, {
      nickname: partnerNickname.value.trim(),
      birthDate: partnerBirthDate.value,
      relation: partnerRelation.value,
    })
  } else {
    addPartner({
      nickname: partnerNickname.value.trim(),
      birthDate: partnerBirthDate.value,
      relation: partnerRelation.value,
    })
  }
  showPartnerForm.value = false
}

function deletePartner(id: string) {
  removePartner(id)
  confirmDeleteId.value = null
}

onMounted(() => {
  init()
})
</script>

<template>
  <div class="sukuyodo-v2">
    <!-- Header -->
    <header class="header">
      <h1 class="header-title">
        <ruby>宿曜道<rp>(</rp><rt>しゅくようどう</rt><rp>)</rp></ruby>
      </h1>
      <button class="btn-query" @click="showQueryDialog = true">
        <sl-icon name="search" aria-hidden="true"></sl-icon>
        <span>查詢本命宿</span>
      </button>
    </header>

    <!-- Query Dialog -->
    <sl-dialog
      :open.prop="showQueryDialog"
      label="查詢本命宿"
      class="query-dialog"
      @sl-after-hide="showQueryDialog = false; showPartnerForm = false"
    >
      <div class="query-content">
        <p class="query-desc">輸入西曆生日，系統會自動轉換為農曆並計算你的本命宿</p>

        <!-- Quick Select -->
        <div v-if="myBirthDate || partnersWithBirthDate.length > 0" class="quick-select">
          <span class="quick-label">快速選擇：</span>
          <div class="quick-btns">
            <button
              v-if="myBirthDate"
              class="quick-btn"
              :class="{ active: birthDate === myBirthDate }"
              @click="quickSelect(myBirthDate)"
            >我</button>
            <button
              v-for="p in partnersWithBirthDate"
              :key="p.id"
              class="quick-btn"
              :class="{ active: birthDate === p.birthDate }"
              @click="quickSelect(p.birthDate)"
            >{{ p.nickname }}</button>
          </div>
        </div>

        <div class="query-form">
          <sl-input
            type="date"
            :value="birthDate"
            label="西曆生日"
            :max="getLocalDateStr()"
            @sl-input="birthDate = ($event.target as HTMLInputElement).value"
          ></sl-input>
        </div>

        <div v-if="lookupError" class="error-msg">{{ lookupError }}</div>

        <!-- 收藏對象管理 -->
        <div class="partner-section">
          <div class="partner-header">
            <span class="partner-title">收藏對象</span>
            <button
              class="btn-add-partner"
              @click="startAddPartner"
              :disabled="profile.partners.length >= 10"
            >+ 新增</button>
          </div>

          <!-- Partner List -->
          <div v-if="profile.partners.length > 0" class="partner-list">
            <div v-for="p in profile.partners" :key="p.id" class="partner-item">
              <div class="partner-info">
                <span class="partner-name">{{ p.nickname }}</span>
                <span class="partner-date">{{ p.birthDate }}</span>
                <span class="partner-rel">{{ RELATION_TYPES.find(r => r.value === p.relation)?.label }}</span>
              </div>
              <div class="partner-actions">
                <button class="btn-icon" @click="startEditPartner(p.id)" title="編輯" aria-label="編輯">
                  <sl-icon name="pencil" aria-hidden="true"></sl-icon>
                </button>
                <button
                  v-if="confirmDeleteId !== p.id"
                  class="btn-icon btn-danger"
                  @click="confirmDeleteId = p.id"
                  title="刪除"
                  aria-label="刪除"
                >
                  <sl-icon name="trash" aria-hidden="true"></sl-icon>
                </button>
                <button
                  v-else
                  class="btn-icon btn-danger confirm"
                  @click="deletePartner(p.id)"
                >確認</button>
              </div>
            </div>
          </div>
          <p v-else class="partner-empty">尚未新增收藏對象</p>

          <!-- Add/Edit Form -->
          <div v-if="showPartnerForm" class="partner-form">
            <div class="form-row">
              <sl-input
                :value="partnerNickname"
                label="暱稱"
                placeholder="例：太太、爸爸"
                @sl-input="partnerNickname = ($event.target as HTMLInputElement).value"
              ></sl-input>
            </div>
            <div class="form-row">
              <sl-input
                type="date"
                :value="partnerBirthDate"
                label="西曆生日"
                :max="getLocalDateStr()"
                @sl-input="partnerBirthDate = ($event.target as HTMLInputElement).value"
              ></sl-input>
            </div>
            <div class="form-row">
              <label class="form-label">關係</label>
              <sl-select
                :value="partnerRelation"
                @sl-change="partnerRelation = ($event.target as HTMLSelectElement).value as RelationType"
              >
                <sl-option
                  v-for="rt in RELATION_TYPES"
                  :key="rt.value"
                  :value="rt.value"
                >{{ rt.label }}</sl-option>
              </sl-select>
            </div>
            <div class="form-actions">
              <button class="btn-cancel" @click="showPartnerForm = false">取消</button>
              <button
                class="btn-save"
                :disabled="!partnerNickname.trim() || !partnerBirthDate"
                @click="savePartner"
              >{{ editingPartnerId ? '更新' : '新增' }}</button>
            </div>
          </div>
        </div>
      </div>

      <div slot="footer" class="dialog-footer">
        <sl-button variant="default" @click="showQueryDialog = false">取消</sl-button>
        <sl-button
          variant="primary"
          :loading.prop="lookupLoading"
          :disabled.prop="!birthDate"
          @click="lookupMansion"
        >查詢</sl-button>
      </div>
    </sl-dialog>

    <!-- Summary Card -->
    <SummaryCard
      v-if="mansion"
      :mansion="mansion"
      :daily-fortune="dailyFortune"
      :element-color="mansionElementColor"
      @query="showQueryDialog = true"
      @navigate-fortune="activeMainTab = 'fortune'; activeFortuneTab = 'daily'"
      @navigate-knowledge="activeMainTab = 'knowledge'; activeKnowledgeTab = $event"
    />

    <!-- Empty State -->
    <section v-if="!mansion" class="empty-state">
      <sl-icon name="stars" aria-hidden="true"></sl-icon>
      <h2>探索你的本命宿</h2>
      <p>宿曜道源自密教經典《宿曜經》，以農曆生日對應二十七宿，分析個人特質、每日運勢、人際相性與吉凶擇日。</p>
      <p class="empty-sub">輸入西曆生日即可開始</p>
      <button class="btn-primary" @click="showQueryDialog = true">查詢本命宿</button>
    </section>

    <!-- Main Tabs -->
    <nav v-if="mansion" class="main-tabs" role="tablist" aria-label="主要功能選擇">
      <button
        class="tab-btn"
        :class="{ active: activeMainTab === 'fortune' }"
        role="tab"
        :aria-selected="activeMainTab === 'fortune'"
        @click="activeMainTab = 'fortune'"
      >運勢</button>
      <button
        class="tab-btn"
        :class="{ active: activeMainTab === 'match' }"
        role="tab"
        :aria-selected="activeMainTab === 'match'"
        @click="activeMainTab = 'match'"
      >配對</button>
      <button
        class="tab-btn"
        :class="{ active: activeMainTab === 'calendar' }"
        role="tab"
        :aria-selected="activeMainTab === 'calendar'"
        @click="activeMainTab = 'calendar'; if (!calendarData) fetchCalendarMonth()"
      >月曆</button>
      <button
        class="tab-btn"
        :class="{ active: activeMainTab === 'lucky' }"
        role="tab"
        :aria-selected="activeMainTab === 'lucky'"
        @click="activeMainTab = 'lucky'"
      >吉日</button>
      <button
        class="tab-btn"
        :class="{ active: activeMainTab === 'knowledge' }"
        role="tab"
        :aria-selected="activeMainTab === 'knowledge'"
        @click="activeMainTab = 'knowledge'"
      >知識</button>
    </nav>

    <!-- Tab Content -->
    <main v-if="mansion" class="tab-content">
      <FortuneTab
        v-if="activeMainTab === 'fortune'"
        v-model:active-tab="activeFortuneTab"
        :daily-fortune="dailyFortune"
        :weekly-fortune="weeklyFortune"
        :monthly-fortune="monthlyFortune"
        :yearly-fortune="yearlyFortune"
        :yearly-range="yearlyRange"
        :yearly-range-loading="yearlyRangeLoading"
        :expanded-monthly-week="expandedMonthlyWeek"
        :current-week-number="currentWeekNumber"
        :mansion="mansion"
        :birth-date="birthDate"
        @toggle-week="toggleMonthlyWeek"
        @select-day="fetchDailyFortuneForDate"
        @fetch-yearly-range="(s: number, e: number) => fetchYearlyRange(s, e)"
        @navigate-knowledge="activeMainTab = 'knowledge'; activeKnowledgeTab = $event"
      />

      <MatchTab
        v-if="activeMainTab === 'match'"
        v-model:active-tab="activeMatchTab"
        :compat-finder="compatFinder"
        :finder-loading="finderLoading"
        :selected-mansion="selectedMansion"
        :date2="date2"
        :compatibility="compatibility"
        :compat-loading="compatLoading"
        :compat-error="compatError"
        :partner-compatibilities="partnerCompatibilities"
        :partner-compat-loading="partnerCompatLoading"
        :partners-with-birth-date="partnersWithBirthDate"
        :element-colors="elementColors"
        :birth-date="birthDate"
        :mansion="mansion"
        @update:selected-mansion="selectedMansion = $event"
        @update:date2="date2 = $event"
        @calculate-compatibility="calculateCompatibility"
        @navigate-knowledge="activeMainTab = 'knowledge'; activeKnowledgeTab = $event"
        @navigate-lucky="activeMainTab = 'lucky'; activeLuckyTab = 'pair'"
      />

      <FortuneCalendar
        v-if="activeMainTab === 'calendar'"
        :calendar-data="calendarData"
        :loading="calendarLoading"
        :has-birth-date="!!birthDate"
        @change-month="changeCalendarMonth"
        @select-day="(d: string) => { fetchDailyFortuneForDate(d); activeMainTab = 'fortune' }"
      />

      <LuckyDaysTab
        v-if="activeMainTab === 'lucky'"
        :lucky-day-summary="luckyDaySummary"
        :lucky-day-summary-loading="luckyDaySummaryLoading"
        :japanese-calendar="japaneseCalendar"
        :japanese-calendar-loading="japaneseCalendarLoading"
        :special-days="specialDays"
        :special-days-loading="specialDaysLoading"
        :active-lucky-tab="activeLuckyTab"
        :selected-partner-id="selectedPartnerId"
        :pair-lucky-days="pairLuckyDays"
        :pair-lucky-days-loading="pairLuckyDaysLoading"
        @update:active-lucky-tab="activeLuckyTab = $event"
        @select-partner="fetchPairLuckyDays"
        @clear-partner="clearPairSelection"
        @refresh-partner="fetchPairLuckyDays"
        @fetch-special-days="fetchSpecialDays"
        @navigate-knowledge="activeMainTab = 'knowledge'; activeKnowledgeTab = $event"
      />

      <KnowledgeTab
        v-if="activeMainTab === 'knowledge'"
        v-model:active-tab="activeKnowledgeTab"
        :mansion="mansion"
        :mansion-element-color="mansionElementColor"
        :all-mansions="allMansions"
        :selected-wheel-mansion="selectedWheelMansion"
        :all-relations="allRelations"
        :all-elements="allElements"
        :metadata="metadata"
        :element-colors="elementColors"
        @update:selected-wheel-mansion="selectedWheelMansion = $event"
      />
    </main>
  </div>
</template>

<style scoped>
/* Design System - CSS Variables */
.sukuyodo-v2 {
  --bg-primary: #1c1917;
  --bg-surface: #292524;
  --bg-elevated: #44403c;
  --border: #57534e;
  --text-primary: #fafaf9;
  --text-secondary: #a8a29e;
  --accent: #f59e0b;
  --accent-hover: #d97706;
  --stellar: #d4a017;
  --success: #4a9b6b;
  --warning: #ef4444;
  --info: #3b82f6;

  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;
  --space-2xl: 48px;

  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-full: 9999px;

  --font-xs: 12px;
  --font-sm: 14px;
  --font-base: 16px;
  --font-lg: 18px;
  --font-xl: 24px;

  background: var(--bg-primary);
  color: var(--text-primary);
  min-height: 100vh;
  padding: var(--space-md);
}

/* Header */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-md) 0;
  border-bottom: 1px solid var(--border);
  margin-bottom: var(--space-lg);
}

.header-title {
  font-size: var(--font-xl);
  font-weight: 700;
  color: var(--accent);
  margin: 0;
}

.header-title rt {
  font-size: var(--font-xs);
  color: var(--text-secondary);
}

.btn-query {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  min-height: 44px;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  cursor: pointer;
  transition: background-color 0.2s, border-color 0.2s;
}

.btn-query:hover {
  background: var(--bg-elevated);
  border-color: var(--accent);
}

.btn-query:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

/* Query Dialog - scoped styles */

.query-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.query-desc {
  color: var(--text-secondary);
  font-size: var(--font-sm);
  margin: 0;
}

.quick-select {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-sm);
}

.quick-label {
  color: var(--text-secondary);
  font-size: var(--font-sm);
}

.quick-btns {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.quick-btn {
  padding: var(--space-sm) var(--space-md);
  min-height: 44px;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-full);
  color: var(--text-secondary);
  font-size: var(--font-sm);
  cursor: pointer;
  transition: background-color 0.2s, border-color 0.2s, color 0.2s;
}

.quick-btn:hover,
.quick-btn.active {
  background: var(--accent);
  color: var(--bg-primary);
  border-color: var(--accent);
}

.quick-btn:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.query-form sl-input {
  --sl-input-background-color: var(--bg-elevated);
  --sl-input-border-color: var(--border);
  --sl-input-color: var(--text-primary);
  --sl-input-label-color: var(--text-secondary);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-sm);
}

.error-msg {
  color: var(--warning);
  font-size: var(--font-sm);
  padding: var(--space-sm);
  background: rgba(239, 68, 68, 0.1);
  border-radius: var(--radius-sm);
}

/* Partner Management */
.partner-section {
  border-top: 1px solid var(--border);
  padding-top: var(--space-md);
}

.partner-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-sm);
}

.partner-title {
  font-size: var(--font-sm);
  font-weight: 600;
  color: var(--text-primary);
}

.btn-add-partner {
  padding: var(--space-xs) var(--space-sm);
  min-height: 32px;
  background: transparent;
  border: 1px solid var(--accent);
  border-radius: var(--radius-md);
  color: var(--accent);
  font-size: var(--font-xs);
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-add-partner:hover:not(:disabled) {
  background: rgba(245, 158, 11, 0.1);
}

.btn-add-partner:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.partner-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.partner-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-sm);
  background: var(--bg-elevated);
  border-radius: var(--radius-sm);
  gap: var(--space-sm);
}

.partner-info {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
  min-width: 0;
}

.partner-name {
  font-size: var(--font-sm);
  font-weight: 600;
  color: var(--text-primary);
}

.partner-date {
  font-size: var(--font-xs);
  color: var(--text-secondary);
}

.partner-rel {
  font-size: 10px;
  padding: 1px 6px;
  background: rgba(245, 158, 11, 0.15);
  color: var(--accent);
  border-radius: var(--radius-full);
}

.partner-actions {
  display: flex;
  gap: var(--space-xs);
  flex-shrink: 0;
}

.btn-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  min-height: 44px;
  min-width: 44px;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  cursor: pointer;
  transition: color 0.2s, background-color 0.2s;
}

.btn-icon:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.05);
}

.btn-icon.btn-danger:hover,
.btn-icon.btn-danger.confirm {
  color: var(--warning);
}

.btn-icon.btn-danger.confirm {
  width: auto;
  padding: 0 var(--space-sm);
  font-size: var(--font-xs);
  font-weight: 600;
}

.partner-empty {
  font-size: var(--font-xs);
  color: var(--text-secondary);
  text-align: center;
  padding: var(--space-sm);
  margin: 0;
}

.partner-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  padding: var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  margin-top: var(--space-sm);
}

.partner-form sl-input,
.partner-form sl-select {
  --sl-input-background-color: var(--bg-surface);
  --sl-input-border-color: var(--border);
  --sl-input-color: var(--text-primary);
  --sl-input-label-color: var(--text-secondary);
}

.form-row {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.form-label {
  font-size: var(--font-sm);
  color: var(--text-secondary);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-sm);
  margin-top: var(--space-xs);
}

.btn-cancel,
.btn-save {
  padding: var(--space-xs) var(--space-md);
  min-height: 36px;
  border-radius: var(--radius-md);
  font-size: var(--font-sm);
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-cancel {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-secondary);
}

.btn-cancel:hover {
  background: rgba(255, 255, 255, 0.05);
}

.btn-save {
  background: var(--accent);
  border: none;
  color: var(--bg-primary);
  font-weight: 600;
}

.btn-save:hover:not(:disabled) {
  background: var(--accent-hover);
}

.btn-save:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-2xl);
  text-align: center;
}

.empty-state sl-icon {
  font-size: 64px;
  color: var(--accent);
  margin-bottom: var(--space-lg);
}

.empty-state h2 {
  font-size: var(--font-lg);
  margin: 0 0 var(--space-sm);
}

.empty-state p {
  color: var(--text-secondary);
  margin: 0 0 var(--space-sm);
  max-width: 400px;
  line-height: 1.6;
}

.empty-state .empty-sub {
  font-size: var(--font-sm);
  margin-bottom: var(--space-lg);
}

.btn-primary {
  padding: var(--space-sm) var(--space-lg);
  min-height: 44px;
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

.btn-primary:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

/* Main Tabs */
.main-tabs {
  display: flex;
  gap: var(--space-sm);
  border-bottom: 1px solid var(--border);
  margin-bottom: var(--space-lg);
}

.tab-btn {
  padding: var(--space-sm) var(--space-md);
  min-height: 44px;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--text-secondary);
  font-size: var(--font-base);
  cursor: pointer;
  transition: color 0.2s, border-color 0.2s;
}

.tab-btn:hover {
  color: var(--text-primary);
}

.tab-btn.active {
  color: var(--accent);
  border-bottom-color: var(--accent);
}

.tab-btn:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

/* Responsive */
@media (max-width: 767px) {
  .sukuyodo-v2 {
    padding: var(--space-sm);
  }

  .header {
    flex-direction: column;
    gap: var(--space-md);
    text-align: center;
  }

  .main-tabs {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
  }

  .main-tabs::-webkit-scrollbar {
    display: none;
  }
}

@media (prefers-reduced-motion: reduce) {
  * {
    transition: none !important;
  }
}
</style>

<!-- Non-scoped: Shoelace shadow DOM ::part() 必須在非 scoped 才能生效 -->
<style>
.query-dialog::part(overlay) {
  background: rgba(0, 0, 0, 0.7);
}

.query-dialog::part(panel) {
  background: #292524;
  border: 1px solid #57534e;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
}

.query-dialog::part(body) {
  overflow-y: auto;
  flex: 1;
  min-height: 0;
}

.query-dialog::part(footer) {
  flex-shrink: 0;
}

.query-dialog::part(title) {
  color: #f59e0b;
}
</style>
