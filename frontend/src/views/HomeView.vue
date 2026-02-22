<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useSukuyodo } from '../composables/useSukuyodo'
import { useProfile, RELATION_TYPES, PRACTITIONER_LEVELS } from '../stores/profile'
import type { RelationType, PractitionerLevel } from '../stores/profile'
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
  expandedYearlyMonth,
  yearlyMonthDetail,
  yearlyMonthLoading,
  expandedYearlyWeek,

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

  // Company Compatibility
  companyName,
  companyDate,
  companyCompat,
  companyCompatLoading,
  companyCompatError,
  companyCompatibilities,
  companyCompatLoading2,

  // Company Auto Search
  companySearchResults,
  companySearchLoading,
  companySearchError,

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
  calculateCompanyCompatibility,
  fetchCompanyCompatibilities,
  searchCompanies,
  fetchPairLuckyDays,
  clearPairSelection,
  fetchDailyFortuneForDate,
  fetchYearlyRange,
  fetchSpecialDays,
  fetchCalendarMonth,
  changeCalendarMonth,
  fetchFullYearCalendar,

  // Event Handlers
  quickSelect,
  toggleMonthlyWeek,
  toggleYearlyMonth,
  toggleYearlyWeek,

  // Init
  init
} = useSukuyodo()

const { addPartner, updatePartner, removePartner, addCompany, removeCompany, importCompaniesFromJson, profile } = useProfile()

// Profile & Partner management state
const showProfilePanel = ref(false)
const showPartnerDialog = ref(false)
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
  showPartnerDialog.value = true
}

function startEditPartner(id: string) {
  const p = profile.value.partners.find(x => x.id === id)
  if (!p) return
  editingPartnerId.value = id
  partnerNickname.value = p.nickname
  partnerBirthDate.value = p.birthDate
  partnerRelation.value = p.relation
  showPartnerDialog.value = true
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
  showPartnerDialog.value = false
}

function deletePartner(id: string) {
  removePartner(id)
  confirmDeleteId.value = null
}

function handleSaveCompany(data: { name: string; foundingDate: string; memo?: string; jobUrl?: string }) {
  addCompany(data)
  fetchCompanyCompatibilities()
}

function handleRemoveCompany(id: string) {
  removeCompany(id)
  fetchCompanyCompatibilities()
}

async function handleImportCompanies() {
  try {
    const added = await importCompaniesFromJson()
    if (added > 0) fetchCompanyCompatibilities()
  } catch (e) {
    console.error('載入推薦清單失敗', e)
  }
}

function handleEscape(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    if (showPartnerDialog.value) {
      showPartnerDialog.value = false
    } else if (showProfilePanel.value) {
      showProfilePanel.value = false
    } else if (showQueryDialog.value) {
      showQueryDialog.value = false
    }
  }
}

watch([showQueryDialog, showProfilePanel], ([query, profile]) => {
  document.body.style.overflow = (query || profile) ? 'hidden' : ''
})

watch(showProfilePanel, (open) => {
  if (!open) showPartnerDialog.value = false
})

onMounted(() => {
  document.addEventListener('keydown', handleEscape)
  init()
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleEscape)
  document.body.style.overflow = ''
})
</script>

<template>
  <div class="sukuyodo-v2">
    <!-- Header -->
    <header class="header">
      <h1 class="header-title">
        <ruby>宿曜道<rp>(</rp><rt>しゅくようどう</rt><rp>)</rp></ruby>
      </h1>
      <div class="header-actions">
        <button class="btn-header-icon" @click="showProfilePanel = true" aria-label="檔案管理">
          <sl-icon name="person" aria-hidden="true"></sl-icon>
        </button>
        <button class="btn-query" @click="showQueryDialog = true">
          <sl-icon name="search" aria-hidden="true"></sl-icon>
          <span>查詢本命宿</span>
        </button>
      </div>
    </header>

    <!-- Query Panel（取代 sl-dialog，實色背景避免文字穿透） -->
    <Transition name="panel">
      <div v-if="showQueryDialog" class="query-panel" role="dialog" aria-modal="true">
        <header class="panel-header">
          <h2 class="panel-title">查詢本命宿</h2>
          <button class="panel-close" @click="showQueryDialog = false" aria-label="關閉">
            <sl-icon name="x-lg"></sl-icon>
          </button>
        </header>
        <div class="panel-body">
          <div class="query-content">
            <!-- 日期輸入（主角） -->
            <sl-input
              type="date"
              :value="birthDate"
              label="西曆生日"
              :max="getLocalDateStr()"
              @sl-input="birthDate = ($event.target as HTMLInputElement).value"
            ></sl-input>

            <div v-if="lookupError" class="error-msg">{{ lookupError }}</div>

            <!-- 快速選擇 chip -->
            <div v-if="myBirthDate || partnersWithBirthDate.length > 0" class="quick-chips">
              <button
                v-if="myBirthDate"
                class="quick-chip"
                :class="{ active: birthDate === myBirthDate }"
                @click="quickSelect(myBirthDate)"
              >我</button>
              <button
                v-for="p in partnersWithBirthDate"
                :key="p.id"
                class="quick-chip"
                :class="{ active: birthDate === p.birthDate }"
                @click="quickSelect(p.birthDate)"
              >{{ p.nickname }}</button>
            </div>

          </div>
        </div>
        <footer class="panel-footer">
          <sl-button variant="default" @click="showQueryDialog = false">取消</sl-button>
          <sl-button
            variant="primary"
            :loading.prop="lookupLoading"
            :disabled.prop="!birthDate"
            @click="lookupMansion"
          >查詢</sl-button>
        </footer>
      </div>
    </Transition>

    <!-- Partner Panel（子面板） -->
    <Transition name="panel">
      <div v-if="showPartnerDialog" class="partner-panel" role="dialog" aria-modal="true">
        <header class="panel-header">
          <h2 class="panel-title">{{ editingPartnerId ? '編輯收藏對象' : '新增收藏對象' }}</h2>
          <button class="panel-close" @click="showPartnerDialog = false" aria-label="關閉">
            <sl-icon name="x-lg"></sl-icon>
          </button>
        </header>
        <div class="panel-body">
          <div class="partner-form-content">
            <sl-input
              :value="partnerNickname"
              label="暱稱"
              placeholder="例：太太、爸爸"
              @sl-input="partnerNickname = ($event.target as HTMLInputElement).value"
            ></sl-input>
            <sl-input
              type="date"
              :value="partnerBirthDate"
              label="西曆生日"
              :max="getLocalDateStr()"
              @sl-input="partnerBirthDate = ($event.target as HTMLInputElement).value"
            ></sl-input>
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
          </div>
        </div>
        <footer class="panel-footer">
          <sl-button variant="default" @click="showPartnerDialog = false">取消</sl-button>
          <sl-button
            variant="primary"
            :disabled.prop="!partnerNickname.trim() || !partnerBirthDate"
            @click="savePartner"
          >{{ editingPartnerId ? '更新' : '新增' }}</sl-button>
        </footer>
      </div>
    </Transition>

    <!-- Profile Panel（檔案管理面板） -->
    <Transition name="panel">
      <div v-if="showProfilePanel" class="profile-panel" role="dialog" aria-modal="true">
        <header class="panel-header">
          <h2 class="panel-title">檔案管理</h2>
          <button class="panel-close" @click="showProfilePanel = false" aria-label="關閉">
            <sl-icon name="x-lg"></sl-icon>
          </button>
        </header>
        <div class="panel-body">
          <div class="profile-content">
            <!-- 我的生日 -->
            <div class="profile-section">
              <h3 class="profile-section-title">我的生日</h3>
              <p v-if="myBirthDate" class="my-birthday">{{ myBirthDate }}</p>
              <p v-else class="my-birthday-empty">尚未設定（查詢本命宿時自動儲存）</p>
            </div>

            <!-- 修行背景 -->
            <div class="profile-section">
              <h3 class="profile-section-title">修行背景</h3>
              <div class="practitioner-select">
                <button
                  v-for="lvl in PRACTITIONER_LEVELS"
                  :key="lvl.value"
                  class="practitioner-btn"
                  :class="{ active: profile.practitionerLevel === lvl.value }"
                  @click="profile.practitionerLevel = lvl.value"
                >{{ lvl.label }}</button>
              </div>
            </div>

            <!-- 收藏對象 -->
            <div class="profile-section">
              <h3 class="profile-section-title">收藏對象 ({{ profile.partners.length }})</h3>
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
              <button
                class="btn-add-partner"
                @click="startAddPartner"
                :disabled="profile.partners.length >= 10"
              >+ 新增對象</button>
            </div>
          </div>
        </div>
      </div>
    </Transition>

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
        :expanded-yearly-month="expandedYearlyMonth"
        :yearly-month-detail="yearlyMonthDetail"
        :yearly-month-loading="yearlyMonthLoading"
        :expanded-yearly-week="expandedYearlyWeek"
        :fetch-full-year-calendar="fetchFullYearCalendar"
        @toggle-week="toggleMonthlyWeek"
        @select-day="fetchDailyFortuneForDate"
        @toggle-yearly-month="toggleYearlyMonth"
        @toggle-yearly-week="toggleYearlyWeek"
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
        :company-name="companyName"
        :company-date="companyDate"
        :company-compat="companyCompat"
        :company-compat-loading="companyCompatLoading"
        :company-compat-error="companyCompatError"
        :company-compatibilities="companyCompatibilities"
        :company-compat-loading2="companyCompatLoading2"
        :company-search-results="companySearchResults"
        :company-search-loading="companySearchLoading"
        :company-search-error="companySearchError"
        @update:selected-mansion="selectedMansion = $event"
        @update:date2="date2 = $event"
        @update:company-name="companyName = $event"
        @update:company-date="companyDate = $event"
        @calculate-compatibility="calculateCompatibility"
        @calculate-company-compatibility="calculateCompanyCompatibility"
        @save-company="handleSaveCompany"
        @remove-company="handleRemoveCompany"
        @import-companies="handleImportCompanies"
        @search-companies="(kw: string, area: string) => searchCompanies(kw, area)"
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
/* Layout */
.sukuyodo-v2 {
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

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.btn-header-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  cursor: pointer;
  transition: background-color 0.2s, border-color 0.2s, color 0.2s;
  font-size: var(--font-lg);
}

.btn-header-icon:hover {
  background: var(--bg-elevated);
  border-color: var(--accent);
  color: var(--text-primary);
}

.btn-header-icon:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
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

/* Full-screen Panel (取代 sl-dialog，實色背景) */

.query-panel,
.partner-panel,
.profile-panel {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: var(--bg-primary);
  display: flex;
  flex-direction: column;
  --sl-input-background-color: var(--bg-elevated);
  --sl-input-border-color: var(--border);
  --sl-input-color: var(--text-primary);
  --sl-input-label-color: var(--text-secondary);
}

.partner-panel {
  z-index: 1002;
}

.profile-panel {
  z-index: 1001;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-md) var(--space-lg);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.panel-title {
  font-size: var(--font-lg);
  font-weight: 600;
  color: var(--accent);
  margin: 0;
}

.panel-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  cursor: pointer;
  transition: color 0.2s, background-color 0.2s;
}

.panel-close:hover {
  color: var(--text-primary);
  background: rgba(0, 0, 0, 0.05);
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-lg);
}

.panel-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-sm);
  padding: var(--space-md) var(--space-lg);
  border-top: 1px solid var(--border);
  flex-shrink: 0;
}

/* Panel Transition */
.panel-enter-active {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.panel-leave-active {
  transition: transform 0.2s cubic-bezier(0.4, 0, 1, 1);
}

.panel-enter-from,
.panel-leave-to {
  transform: translateY(100%);
}

/* Query Content */
.query-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.error-msg {
  color: var(--warning);
  font-size: var(--font-sm);
  padding: var(--space-sm);
  background: rgba(197, 48, 48, 0.08);
  border-radius: var(--radius-sm);
}

/* Quick Chips */
.quick-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.quick-chip {
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

.quick-chip:hover,
.quick-chip.active {
  background: var(--accent);
  color: var(--text-on-accent);
  border-color: var(--accent);
}

.quick-chip:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

/* Partner Management (inside sl-details) */
.btn-add-partner {
  width: 100%;
  padding: var(--space-sm);
  min-height: 36px;
  margin-top: var(--space-sm);
  background: transparent;
  border: 1px dashed var(--accent);
  border-radius: var(--radius-md);
  color: var(--accent);
  font-size: var(--font-sm);
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-add-partner:hover:not(:disabled) {
  background: rgba(139, 105, 20, 0.1);
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
  background: rgba(139, 105, 20, 0.12);
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
  width: 44px;
  height: 44px;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  cursor: pointer;
  transition: color var(--transition-fast), background-color var(--transition-fast);
}

.btn-icon:hover {
  color: var(--text-primary);
  background: rgba(0, 0, 0, 0.05);
}

.btn-icon:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
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

/* Partner Form Content */
.partner-form-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
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
  color: var(--text-on-accent);
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

/* Profile Panel */
.profile-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.profile-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.profile-section-title {
  font-size: var(--font-sm);
  font-weight: 600;
  color: var(--accent);
  margin: 0;
}

.my-birthday {
  font-size: var(--font-base);
  color: var(--text-primary);
  margin: 0;
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
}

.my-birthday-empty {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  margin: 0;
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
}

.practitioner-select {
  display: flex;
  gap: var(--space-xs);
}

.practitioner-btn {
  flex: 1;
  padding: var(--space-sm) var(--space-md);
  min-height: 44px;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: var(--font-sm);
  cursor: pointer;
  transition: background-color 0.2s, border-color 0.2s, color 0.2s;
}

.practitioner-btn:hover {
  border-color: var(--accent);
  color: var(--text-primary);
}

.practitioner-btn.active {
  background: var(--accent);
  border-color: var(--accent);
  color: var(--text-on-accent);
  font-weight: 600;
}

.practitioner-btn:focus-visible {
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

