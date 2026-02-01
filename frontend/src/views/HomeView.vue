<script setup lang="ts">
import { onMounted } from 'vue'
import { useSukuyodo } from '../composables/useSukuyodo'
import SummaryCard from '../components/SummaryCard.vue'
import FortuneTab from '../components/FortuneTab.vue'
import MatchTab from '../components/MatchTab.vue'
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
  expandedMonthlyWeek,
  currentWeekNumber,

  // Compatibility
  compatFinder,
  finderLoading,
  selectedMansion,
  expandedLunarDates,

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
  activeLuckyTab,
  selectedPartnerId,
  pairLuckyDays,
  pairLuckyDaysLoading,

  // Knowledge
  expandedRelation,

  // Computed
  elementColors,
  mansionElementColor,

  // API Functions
  lookupMansion,
  calculateCompatibility,
  fetchPairLuckyDays,
  clearPairSelection,
  fetchDailyFortuneForDate,

  // Event Handlers
  toggleRelation,
  toggleLunarDate,
  quickSelect,
  toggleMonthlyWeek,

  // Init
  init
} = useSukuyodo()

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
      @sl-hide="showQueryDialog = false"
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
            :max="new Date().toISOString().split('T')[0]"
            @sl-input="birthDate = ($event.target as HTMLInputElement).value"
          ></sl-input>
        </div>

        <div v-if="lookupError" class="error-msg">{{ lookupError }}</div>
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
    />

    <!-- Empty State -->
    <section v-if="!mansion" class="empty-state">
      <sl-icon name="stars" aria-hidden="true"></sl-icon>
      <h2>探索你的本命宿</h2>
      <p>了解你的命宿特質與每日運勢</p>
      <button class="btn-primary" @click="showQueryDialog = true">開始查詢</button>
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
        :expanded-monthly-week="expandedMonthlyWeek"
        :current-week-number="currentWeekNumber"
        @toggle-week="toggleMonthlyWeek"
        @select-day="fetchDailyFortuneForDate"
      />

      <MatchTab
        v-if="activeMainTab === 'match'"
        v-model:active-tab="activeMatchTab"
        :compat-finder="compatFinder"
        :finder-loading="finderLoading"
        :selected-mansion="selectedMansion"
        :expanded-lunar-dates="expandedLunarDates"
        :date2="date2"
        :compatibility="compatibility"
        :compat-loading="compatLoading"
        :compat-error="compatError"
        :partner-compatibilities="partnerCompatibilities"
        :partner-compat-loading="partnerCompatLoading"
        :partners-with-birth-date="partnersWithBirthDate"
        :element-colors="elementColors"
        @update:selected-mansion="selectedMansion = $event"
        @update:date2="date2 = $event"
        @toggle-lunar-date="toggleLunarDate"
        @calculate-compatibility="calculateCompatibility"
      />

      <LuckyDaysTab
        v-if="activeMainTab === 'lucky'"
        :lucky-day-summary="luckyDaySummary"
        :lucky-day-summary-loading="luckyDaySummaryLoading"
        :active-lucky-tab="activeLuckyTab"
        :selected-partner-id="selectedPartnerId"
        :pair-lucky-days="pairLuckyDays"
        :pair-lucky-days-loading="pairLuckyDaysLoading"
        @update:active-lucky-tab="activeLuckyTab = $event"
        @select-partner="fetchPairLuckyDays"
        @clear-partner="clearPairSelection"
        @refresh-partner="fetchPairLuckyDays"
      />

      <KnowledgeTab
        v-if="activeMainTab === 'knowledge'"
        v-model:active-tab="activeKnowledgeTab"
        :mansion="mansion"
        :mansion-element-color="mansionElementColor"
        :all-mansions="allMansions"
        :selected-wheel-mansion="selectedWheelMansion"
        :all-relations="allRelations"
        :expanded-relation="expandedRelation"
        :all-elements="allElements"
        :metadata="metadata"
        :element-colors="elementColors"
        @update:selected-wheel-mansion="selectedWheelMansion = $event"
        @toggle-relation="toggleRelation"
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
  --success: #22c55e;
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

/* Query Dialog */
.query-dialog::part(panel) {
  background: var(--bg-surface);
  border: 1px solid var(--border);
}

.query-dialog::part(title) {
  color: var(--accent);
}

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
  padding: var(--space-xs) var(--space-sm);
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
  margin: 0 0 var(--space-lg);
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
