<script setup lang="ts">
import { ref, computed } from 'vue'
import type { LuckyDaySummary, PairLuckyDaysResult, JapaneseCalendarResult, SpecialDaysResult } from '../composables/useSukuyodo'
import { useProfile, RELATION_TYPES, type Partner, type RelationType } from '../stores/profile'

const props = defineProps<{
  luckyDaySummary: LuckyDaySummary | null
  luckyDaySummaryLoading: boolean
  japaneseCalendar: JapaneseCalendarResult | null
  japaneseCalendarLoading: boolean
  specialDays: SpecialDaysResult | null
  specialDaysLoading: boolean
  activeLuckyTab: 'personal' | 'pair'
  selectedPartnerId: string | null
  pairLuckyDays: PairLuckyDaysResult | null
  pairLuckyDaysLoading: boolean
}>()

const emit = defineEmits<{
  (e: 'update:activeLuckyTab', tab: 'personal' | 'pair'): void
  (e: 'selectPartner', partnerId: string): void
  (e: 'clearPartner'): void
  (e: 'refreshPartner', partnerId: string): void
  (e: 'fetchSpecialDays', year: number, month: number): void
}>()

const { profile, addPartner, updatePartner, removePartner } = useProfile()

// 收藏對象管理
const showAddDialog = ref(false)
const showEditDialog = ref(false)
const editingPartner = ref<Partner | null>(null)

// 表單狀態
const formNickname = ref('')
const formBirthDate = ref('')
const formRelation = ref<RelationType>('friend')

function openAddDialog() {
  formNickname.value = ''
  formBirthDate.value = ''
  formRelation.value = 'friend'
  showAddDialog.value = true
}

function openEditDialog(partner: Partner) {
  editingPartner.value = partner
  formNickname.value = partner.nickname
  formBirthDate.value = partner.birthDate
  formRelation.value = partner.relation
  showEditDialog.value = true
}

function handleAdd() {
  if (!formNickname.value || !formBirthDate.value) return

  try {
    addPartner({
      nickname: formNickname.value,
      birthDate: formBirthDate.value,
      relation: formRelation.value
    })
    showAddDialog.value = false
  } catch (err) {
    alert((err as Error).message)
  }
}

function handleEdit() {
  if (!editingPartner.value || !formNickname.value || !formBirthDate.value) return

  const partnerId = editingPartner.value.id
  const isCurrentlySelected = props.selectedPartnerId === partnerId

  updatePartner(partnerId, {
    nickname: formNickname.value,
    birthDate: formBirthDate.value,
    relation: formRelation.value
  })
  showEditDialog.value = false
  editingPartner.value = null

  // 如果正在查看這個對象，立即重新查詢吉日資料
  if (isCurrentlySelected) {
    emit('refreshPartner', partnerId)
  }
}

function handleDelete(partner: Partner) {
  if (confirm(`確定要刪除「${partner.nickname}」嗎？`)) {
    removePartner(partner.id)
    if (props.selectedPartnerId === partner.id) {
      emit('clearPartner')
    }
  }
}

function getRelationLabel(relation: RelationType): string {
  return RELATION_TYPES.find(r => r.value === relation)?.label || relation
}

function getScoreClass(score: number) {
  if (score >= 90) return 'excellent'
  if (score >= 75) return 'good'
  if (score >= 60) return 'fair'
  if (score >= 45) return 'caution'
  return 'warning'
}

function getRating(score: number) {
  if (score >= 90) return '大吉'
  if (score >= 75) return '吉'
  if (score >= 60) return '中吉'
  return '小吉'
}

function formatDate(dateStr: string) {
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}/${d.getDate()}`
}

function getLabelClass(label: string) {
  const classMap: Record<string, string> = {
    '天赦日': 'tensya',
    '一粒萬倍日': 'ichiryumanbai',
    '寅の日': 'tora',
    '巳の日': 'mi',
    '己巳の日': 'tsuchinoto-mi'
  }
  return classMap[label] || ''
}

// 圖例展開狀態
const expandedLegend = ref<string | null>(null)

function toggleLegend(type: string) {
  expandedLegend.value = expandedLegend.value === type ? null : type
}

const legendItems = computed(() => {
  const descs = props.japaneseCalendar?.day_type_descriptions
  return [
    {
      type: 'tensya',
      dotClass: 'tensya',
      name: descs?.tensya?.name || '天赦日',
      short: descs?.tensya?.short || '年間最大吉日',
      description: descs?.tensya?.description || ''
    },
    {
      type: 'ichiryumanbai',
      dotClass: 'ichiryumanbai',
      name: descs?.ichiryumanbai?.name || '一粒萬倍日',
      short: descs?.ichiryumanbai?.short || '開始新事物吉',
      description: descs?.ichiryumanbai?.description || ''
    },
    {
      type: 'tora_no_hi',
      dotClass: 'tora',
      name: descs?.tora_no_hi?.name || '寅の日',
      short: descs?.tora_no_hi?.short || '財運、旅行吉',
      description: descs?.tora_no_hi?.description || ''
    },
    {
      type: 'mi_no_hi',
      dotClass: 'mi',
      name: descs?.mi_no_hi?.name || '巳の日',
      short: descs?.mi_no_hi?.short || '金運、藝術吉',
      description: descs?.mi_no_hi?.description || ''
    },
    {
      type: 'tsuchinoto_mi',
      dotClass: 'tsuchinoto-mi',
      name: descs?.tsuchinoto_mi?.name || '己巳の日',
      short: descs?.tsuchinoto_mi?.short || '最強金運日',
      description: descs?.tsuchinoto_mi?.description || ''
    },
    {
      type: 'fujoubyou',
      dotClass: 'fujoubyou',
      name: descs?.fujoubyou?.name || '不成就日',
      short: descs?.fujoubyou?.short || '萬事不成之日',
      description: descs?.fujoubyou?.description || ''
    }
  ]
})

const selectedPartner = computed(() => {
  if (!props.selectedPartnerId) return null
  return profile.value.partners.find(p => p.id === props.selectedPartnerId) || null
})

// 特殊日月份切換
const specialDaysMonth = ref<{ year: number; month: number }>({
  year: new Date().getFullYear(),
  month: new Date().getMonth() + 1
})

const specialDaysMonthLabel = computed(() => {
  return `${specialDaysMonth.value.year} 年 ${specialDaysMonth.value.month} 月`
})

function changeSpecialDaysMonth(delta: number) {
  let { year, month } = specialDaysMonth.value
  month += delta
  if (month > 12) { month = 1; year++ }
  if (month < 1) { month = 12; year-- }
  specialDaysMonth.value = { year, month }
  emit('fetchSpecialDays', year, month)
}

function getSpecialDayTypeClass(type: string) {
  const classMap: Record<string, string> = {
    kanro: 'kanro',
    kongou: 'kongou',
    rasetsu: 'rasetsu'
  }
  return classMap[type] || ''
}

function formatSpecialDate(dateStr: string) {
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}/${d.getDate()}`
}

function getSpecialDayAdvice(type: string): string {
  const adviceMap: Record<string, string> = {
    kanro: '適合護摩供養、灌頂、開眼、簽約、結婚、搬遷、開業',
    kongou: '適合修法、寫經、授戒、出家、面試、考試',
    rasetsu: '避免護摩、灌頂、簽約、遠行。適合靜坐、誦經、閉關'
  }
  return adviceMap[type] || ''
}
</script>

<template>
  <section class="lucky-tab">
    <!-- 子分頁切換 -->
    <div class="sub-tabs">
      <button
        class="sub-tab"
        :class="{ active: activeLuckyTab === 'personal' }"
        @click="emit('update:activeLuckyTab', 'personal')"
      >
        我的吉日
      </button>
      <button
        class="sub-tab"
        :class="{ active: activeLuckyTab === 'pair' }"
        @click="emit('update:activeLuckyTab', 'pair')"
      >
        雙人吉日
      </button>
    </div>

    <!-- 我的吉日 -->
    <div v-if="activeLuckyTab === 'personal'" class="personal-section">
      <div v-if="luckyDaySummaryLoading && japaneseCalendarLoading" class="loading-state">
        <sl-spinner></sl-spinner>
        <span>載入吉日資料...</span>
      </div>

      <template v-else>
        <!-- 本月特殊日區塊 -->
        <div class="special-days-section">
          <h3 class="section-title">
            <sl-icon name="calendar2-check"></sl-icon>
            本月特殊日
          </h3>
          <p class="section-desc">不分本命宿，所有人共通的宿曜吉凶日。可用來安排重要行程或避開不利日期。</p>

          <div class="special-days-nav">
            <button class="nav-btn" @click="changeSpecialDaysMonth(-1)">
              <sl-icon name="chevron-left"></sl-icon>
            </button>
            <span class="nav-label">{{ specialDaysMonthLabel }}</span>
            <button class="nav-btn" @click="changeSpecialDaysMonth(1)">
              <sl-icon name="chevron-right"></sl-icon>
            </button>
          </div>

          <div v-if="specialDaysLoading" class="loading-state">
            <sl-spinner></sl-spinner>
          </div>
          <div v-else-if="specialDays && specialDays.days.length > 0" class="special-days-list">
            <div
              v-for="day in specialDays.days"
              :key="day.date"
              class="special-day-card"
              :class="getSpecialDayTypeClass(day.type)"
            >
              <div class="special-day-header">
                <span class="special-day-date">{{ formatSpecialDate(day.date) }}</span>
                <span class="special-day-weekday">{{ day.weekday }}</span>
                <span class="special-day-type-badge" :class="getSpecialDayTypeClass(day.type)">{{ day.name }}</span>
                <span class="special-day-level" :class="getSpecialDayTypeClass(day.type)">{{ day.level }}</span>
                <span v-if="day.ryouhan_reversed" class="ryouhan-tag">凌犯</span>
              </div>
              <p class="special-day-advice">{{ getSpecialDayAdvice(day.type) }}</p>
              <p v-if="day.ryouhan_reversed" class="ryouhan-note">凌犯期間中のため吉凶が逆轉しています</p>
            </div>
          </div>
          <div v-else class="no-lucky-days">
            <span>本月無特殊日</span>
          </div>
        </div>

        <!-- 宿曜吉日區塊 -->
        <div v-if="luckyDaySummary" class="lucky-summary sukuyodo-section">
          <h3 class="section-title">
            <sl-icon name="stars"></sl-icon>
            宿曜吉日
          </h3>
          <p class="section-desc">根據您的本命宿計算的個人吉日</p>

          <div class="category-list">
            <div
              v-for="item in luckyDaySummary.summary"
              :key="item.name"
              class="category-section"
            >
              <h4 class="category-name">{{ item.name }}</h4>

              <div v-if="item.lucky_days.length > 0" class="day-cards">
                <div
                  v-for="day in item.lucky_days"
                  :key="day.date"
                  class="day-card"
                  :class="getScoreClass(day.score)"
                >
                  <div class="day-card-header">
                    <span class="chip-date">{{ formatDate(day.date) }}</span>
                    <span class="chip-weekday">{{ day.weekday?.replace('曜日', '') }}</span>
                    <span class="chip-rating">{{ day.rating || getRating(day.score) }}</span>
                  </div>
                  <p v-if="day.reason" class="day-reason">{{ day.reason }}</p>
                  <div v-if="day.best_time || day.avoid_time" class="day-times">
                    <div v-if="day.best_time" class="time-row best">
                      <span class="time-label">推薦時段</span>
                      <span class="time-value">{{ day.best_time }}</span>
                    </div>
                    <div v-if="day.avoid_time" class="time-row avoid">
                      <span class="time-label">留意事項</span>
                      <span class="time-value">{{ day.avoid_time }}</span>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="no-lucky-days">
                <span>近期無特別吉日</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 選日曆注區塊 -->
        <div v-if="japaneseCalendar" class="senjitsu-section">
          <h3 class="section-title">
            <sl-icon name="calendar-event"></sl-icon>
            選日曆注
          </h3>
          <p class="section-desc">日本傳統擇日系統，通用於所有人</p>

          <!-- 吉日列表 -->
          <div v-if="japaneseCalendar.days.length > 0" class="senjitsu-categories">
            <div class="senjitsu-group">
              <h4 class="senjitsu-group-title">本月吉日</h4>
              <div class="senjitsu-chips">
                <div
                  v-for="day in japaneseCalendar.days"
                  :key="day.date"
                  class="senjitsu-chip"
                  :class="{ 'super-lucky': day.is_super_lucky }"
                >
                  <div class="senjitsu-date-row">
                    <span class="senjitsu-date">{{ formatDate(day.date) }}</span>
                    <span class="senjitsu-weekday">{{ day.weekday?.replace('曜日', '') }}</span>
                    <span v-if="day.is_super_lucky" class="super-mark">★</span>
                  </div>
                  <div class="senjitsu-labels">
                    <span
                      v-for="label in day.labels"
                      :key="label"
                      class="senjitsu-label"
                      :class="getLabelClass(label)"
                    >{{ label }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="no-lucky-days">
            <span>本月無特別吉日</span>
          </div>

          <!-- 凶日警示 -->
          <div v-if="japaneseCalendar.unlucky_days.length > 0" class="unlucky-section">
            <h4 class="unlucky-title">
              <sl-icon name="exclamation-triangle"></sl-icon>
              需注意日期
            </h4>
            <div class="unlucky-chips">
              <div
                v-for="day in japaneseCalendar.unlucky_days"
                :key="day.date"
                class="unlucky-chip"
              >
                <span class="unlucky-date">{{ formatDate(day.date) }}</span>
                <span class="unlucky-label">{{ day.label }}</span>
              </div>
            </div>
          </div>

          <!-- 圖例說明 -->
          <div class="senjitsu-legend">
            <button
              v-for="item in legendItems"
              :key="item.type"
              class="legend-card"
              :class="{ expanded: expandedLegend === item.type }"
              @click="toggleLegend(item.type)"
            >
              <div class="legend-card-header">
                <span class="legend-dot" :class="item.dotClass"></span>
                <span class="legend-card-title">{{ item.name }}</span>
                <span class="legend-card-short">{{ item.short }}</span>
                <span class="legend-toggle" aria-hidden="true">{{ expandedLegend === item.type ? '▲' : '▼' }}</span>
              </div>
              <div v-if="expandedLegend === item.type && item.description" class="legend-card-body">
                <p>{{ item.description }}</p>
              </div>
            </button>
          </div>
        </div>
        <div v-else-if="japaneseCalendarLoading" class="loading-state small">
          <sl-spinner></sl-spinner>
          <span>載入選日資料...</span>
        </div>

        <div v-if="!luckyDaySummary && !japaneseCalendar" class="empty-state">
          <p>請先查詢本命宿</p>
        </div>
      </template>
    </div>

    <!-- 雙人吉日 -->
    <div v-else class="pair-section">
      <div class="favorites-header">
        <h3 class="section-title">我的收藏</h3>
        <sl-button size="small" @click="openAddDialog">
          <sl-icon slot="prefix" name="plus-lg"></sl-icon>
          新增
        </sl-button>
      </div>

      <!-- 收藏對象列表 -->
      <div v-if="profile.partners.length > 0" class="partner-chips">
        <button
          v-for="partner in profile.partners"
          :key="partner.id"
          class="partner-chip"
          :class="{ selected: selectedPartnerId === partner.id }"
          @click="emit('selectPartner', partner.id)"
        >
          <span class="partner-name">{{ partner.nickname }}</span>
          <span class="partner-relation">{{ getRelationLabel(partner.relation) }}</span>
        </button>
      </div>
      <div v-else class="empty-partners">
        <p>尚無收藏對象</p>
        <p class="hint">點擊「新增」來加入收藏</p>
      </div>

      <!-- 選中對象的資訊與吉日 -->
      <div v-if="selectedPartner" class="pair-detail">
        <div class="partner-info-card">
          <div class="partner-header">
            <div class="partner-main">
              <h4>{{ selectedPartner.nickname }}</h4>
              <span class="relation-badge">{{ getRelationLabel(selectedPartner.relation) }}</span>
            </div>
            <div class="partner-actions">
              <sl-icon-button
                name="pencil"
                label="編輯"
                @click="openEditDialog(selectedPartner)"
              ></sl-icon-button>
              <sl-icon-button
                name="trash"
                label="刪除"
                @click="handleDelete(selectedPartner)"
              ></sl-icon-button>
            </div>
          </div>

          <div v-if="pairLuckyDaysLoading" class="loading-state small">
            <sl-spinner></sl-spinner>
            <span>分析中...</span>
          </div>

          <template v-else-if="pairLuckyDays">
            <div class="compatibility-row">
              <div class="mansion-info">
                <span class="mansion-name">{{ pairLuckyDays.person2.mansion }}</span>
                <span class="mansion-element">{{ pairLuckyDays.person2.element }}曜</span>
              </div>
              <div class="compat-score" :class="getScoreClass(pairLuckyDays.compatibility.score)">
                <span class="score-label">{{ pairLuckyDays.compatibility.relation }}</span>
                <span class="score-value">{{ pairLuckyDays.compatibility.score }}分</span>
              </div>
            </div>

            <!-- 各項吉日 -->
            <div class="pair-actions">
              <div
                v-for="action in pairLuckyDays.actions"
                :key="action.action"
                class="action-section"
              >
                <h5 class="action-name">{{ action.name }}</h5>
                <div v-if="action.lucky_days.length > 0" class="day-cards">
                  <div
                    v-for="day in action.lucky_days"
                    :key="day.date"
                    class="day-card"
                    :class="getScoreClass(day.score)"
                  >
                    <div class="day-card-header">
                      <span class="chip-date">{{ formatDate(day.date) }}</span>
                      <span class="chip-weekday">{{ day.weekday?.replace('曜日', '') }}</span>
                      <span class="pair-day-rating" :class="day.rating === '大吉' ? 'top' : day.rating === '吉' ? 'good' : 'mid'">{{ day.rating || getRating(day.score) }}</span>
                    </div>
                    <p v-if="day.reason" class="day-reason">{{ day.reason }}</p>
                    <div v-if="day.best_time || day.avoid_time" class="day-times">
                      <div v-if="day.best_time" class="time-row best">
                        <span class="time-label">推薦時段</span>
                        <span class="time-value">{{ day.best_time }}</span>
                      </div>
                      <div v-if="day.avoid_time" class="time-row avoid">
                        <span class="time-label">留意事項</span>
                        <span class="time-value">{{ day.avoid_time }}</span>
                      </div>
                    </div>
                    <p v-if="day.tip" class="pair-day-tip">{{ day.tip }}</p>
                  </div>
                </div>
                <div v-else class="no-lucky-days">
                  <span>近期無特別吉日</span>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- 新增對象對話框 -->
    <sl-dialog
      :open="showAddDialog"
      label="新增收藏對象"
      @sl-request-close="showAddDialog = false"
    >
      <form class="partner-form" @submit.prevent="handleAdd">
        <sl-input
          label="暱稱"
          placeholder="輸入暱稱"
          :value="formNickname"
          @sl-input="formNickname = ($event.target as HTMLInputElement).value"
          required
        ></sl-input>

        <sl-input
          type="date"
          label="生日"
          :value="formBirthDate"
          @sl-input="formBirthDate = ($event.target as HTMLInputElement).value"
          :max="new Date().toISOString().split('T')[0]"
          required
        ></sl-input>

        <fieldset class="relation-fieldset">
          <legend class="relation-legend">關係</legend>
          <div class="relation-options">
            <label
              v-for="rt in RELATION_TYPES"
              :key="rt.value"
              class="relation-option"
              :class="{ selected: formRelation === rt.value }"
            >
              <input
                type="radio"
                name="add-relation"
                :value="rt.value"
                :checked="formRelation === rt.value"
                @change="formRelation = rt.value"
              />
              <span class="relation-label">{{ rt.label }}</span>
            </label>
          </div>
        </fieldset>

        <div class="dialog-actions">
          <sl-button variant="default" @click="showAddDialog = false">取消</sl-button>
          <sl-button variant="primary" type="submit">新增</sl-button>
        </div>
      </form>
    </sl-dialog>

    <!-- 編輯對象對話框 -->
    <sl-dialog
      :open="showEditDialog"
      label="編輯收藏對象"
      @sl-request-close="showEditDialog = false"
    >
      <form class="partner-form" @submit.prevent="handleEdit">
        <sl-input
          label="暱稱"
          placeholder="輸入暱稱"
          :value="formNickname"
          @sl-input="formNickname = ($event.target as HTMLInputElement).value"
          required
        ></sl-input>

        <sl-input
          type="date"
          label="生日"
          :value="formBirthDate"
          @sl-input="formBirthDate = ($event.target as HTMLInputElement).value"
          :max="new Date().toISOString().split('T')[0]"
          required
        ></sl-input>

        <fieldset class="relation-fieldset">
          <legend class="relation-legend">關係</legend>
          <div class="relation-options">
            <label
              v-for="rt in RELATION_TYPES"
              :key="rt.value"
              class="relation-option"
              :class="{ selected: formRelation === rt.value }"
            >
              <input
                type="radio"
                name="edit-relation"
                :value="rt.value"
                :checked="formRelation === rt.value"
                @change="formRelation = rt.value"
              />
              <span class="relation-label">{{ rt.label }}</span>
            </label>
          </div>
        </fieldset>

        <div class="dialog-actions">
          <sl-button variant="default" @click="showEditDialog = false">取消</sl-button>
          <sl-button variant="primary" type="submit">儲存</sl-button>
        </div>
      </form>
    </sl-dialog>
  </section>
</template>

<style scoped>
.lucky-tab {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 子分頁 */
.sub-tabs {
  display: flex;
  gap: var(--space-xs);
  margin-bottom: var(--space-lg);
  border-bottom: 1px solid var(--border);
  padding-bottom: var(--space-sm);
}

.sub-tab {
  padding: var(--space-sm) var(--space-md);
  background: none;
  border: none;
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: var(--font-sm);
  transition: all 0.2s;
}

.sub-tab:hover {
  color: var(--text-primary);
  background: var(--bg-elevated);
}

.sub-tab.active {
  color: var(--accent);
  border-bottom: 2px solid var(--accent);
  margin-bottom: -1px;
}

/* 通用 */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-2xl);
  color: var(--text-secondary);
}

.loading-state.small {
  padding: var(--space-lg);
}

.section-title {
  font-size: var(--font-lg);
  margin: 0 0 var(--space-lg);
  color: var(--text-primary);
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: var(--space-2xl);
  color: var(--text-secondary);
}

/* 區塊區隔 */
.sukuyodo-section {
  border-left: 4px solid #8b5cf6;
  background: rgba(139, 92, 246, 0.05);
  padding: var(--space-md);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-xl);
}

.senjitsu-section {
  border-left: 4px solid #dc2626;
  background: rgba(220, 38, 38, 0.05);
  padding: var(--space-md);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-lg);
}

.section-title {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.section-title sl-icon {
  font-size: 1.2em;
}

.sukuyodo-section .section-title {
  color: #8b5cf6;
}

.senjitsu-section .section-title {
  color: #dc2626;
}

.section-desc {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  margin: var(--space-xs) 0 var(--space-md);
}

/* 個人吉日 */
.category-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.category-section {
  padding: var(--space-md);
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
}

.category-name {
  font-size: var(--font-md);
  font-weight: 600;
  margin: 0 0 var(--space-sm);
  color: var(--accent);
}

.day-chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.day-chip {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-xs) var(--space-sm);
  background: var(--bg-elevated);
  border-radius: var(--radius-sm);
  font-size: var(--font-sm);
}

.day-chip.excellent { border-left: 3px solid var(--success); }
.day-chip.good { border-left: 3px solid var(--accent); }
.day-chip.fair { border-left: 3px solid var(--info); }
.day-chip.caution { border-left: 3px solid #eab308; }

.day-cards {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.day-card {
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-sm);
}

.day-card.excellent { border-left: 3px solid var(--success); }
.day-card.good { border-left: 3px solid var(--accent); }
.day-card.fair { border-left: 3px solid var(--info); }
.day-card.caution { border-left: 3px solid #eab308; }

.day-card-header {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: var(--font-sm);
}

.day-reason {
  margin: var(--space-xs) 0 0;
  font-size: var(--font-xs);
  color: var(--text-secondary);
  line-height: 1.5;
}

.day-times {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  margin-top: var(--space-xs);
}

.chip-date {
  font-variant-numeric: tabular-nums;
  color: var(--text-primary);
}

.chip-weekday {
  color: var(--text-secondary);
}

.chip-rating {
  padding: 1px 6px;
  border-radius: var(--radius-xs);
  font-size: var(--font-xs);
  font-weight: 500;
}

.day-chip.excellent .chip-rating {
  background: rgba(34, 197, 94, 0.15);
  color: var(--success);
}

.day-chip.good .chip-rating {
  background: rgba(245, 158, 11, 0.15);
  color: var(--accent);
}

.day-chip.fair .chip-rating {
  background: rgba(59, 130, 246, 0.15);
  color: var(--info);
}

.day-chip.caution .chip-rating {
  background: rgba(234, 179, 8, 0.15);
  color: #eab308;
}

.no-lucky-days {
  color: var(--text-secondary);
  font-size: var(--font-sm);
  padding: var(--space-sm) 0;
}

/* 選日曆注區塊 */
.senjitsu-categories {
  margin-bottom: var(--space-lg);
}

.senjitsu-group-title {
  font-size: var(--font-md);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--space-sm);
}

.senjitsu-chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.senjitsu-chip {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  min-width: 100px;
}

.senjitsu-chip.super-lucky {
  background: linear-gradient(135deg,
    rgba(234, 179, 8, 0.15),
    rgba(220, 38, 38, 0.1));
  border-color: #eab308;
}

.senjitsu-date-row {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.senjitsu-date {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: var(--text-primary);
}

.senjitsu-weekday {
  font-size: var(--font-sm);
  color: var(--text-secondary);
}

.super-mark {
  color: #eab308;
  font-size: var(--font-sm);
}

.senjitsu-labels {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.senjitsu-label {
  display: inline-block;
  padding: 2px 6px;
  border-radius: var(--radius-xs);
  font-size: var(--font-xs);
  font-weight: 500;
}

.senjitsu-label.tensya {
  background: rgba(234, 179, 8, 0.2);
  color: #b45309;
}

.senjitsu-label.ichiryumanbai {
  background: rgba(220, 38, 38, 0.15);
  color: #dc2626;
}

.senjitsu-label.tora {
  background: rgba(245, 158, 11, 0.15);
  color: #d97706;
}

.senjitsu-label.mi,
.senjitsu-label.tsuchinoto-mi {
  background: rgba(34, 197, 94, 0.15);
  color: #16a34a;
}

/* 凶日警示 */
.unlucky-section {
  margin-top: var(--space-lg);
  padding-top: var(--space-md);
  border-top: 1px solid var(--border);
}

.unlucky-title {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: var(--font-sm);
  font-weight: 600;
  color: var(--text-secondary);
  margin: 0 0 var(--space-sm);
}

.unlucky-title sl-icon {
  color: #eab308;
}

.unlucky-chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.unlucky-chip {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-xs) var(--space-sm);
  background: rgba(234, 179, 8, 0.1);
  border: 1px solid rgba(234, 179, 8, 0.3);
  border-radius: var(--radius-sm);
  font-size: var(--font-sm);
}

.unlucky-date {
  font-variant-numeric: tabular-nums;
  color: var(--text-primary);
}

.unlucky-label {
  color: #b45309;
  font-size: var(--font-xs);
}

/* 圖例說明 */
.senjitsu-legend {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  margin-top: var(--space-lg);
  padding-top: var(--space-md);
  border-top: 1px solid var(--border);
}

.legend-card {
  display: block;
  width: 100%;
  text-align: left;
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background-color 0.2s;
}

.legend-card:hover {
  background: var(--bg-hover);
}

.legend-card.expanded {
  background: var(--bg-elevated);
}

.legend-card-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.legend-card-title {
  font-size: var(--font-sm);
  font-weight: 600;
  color: var(--text-primary);
}

.legend-card-short {
  font-size: var(--font-xs);
  color: var(--text-secondary);
  flex: 1;
}

.legend-toggle {
  font-size: var(--font-xs);
  color: var(--text-tertiary);
}

.legend-card-body {
  margin-top: var(--space-sm);
  padding-top: var(--space-sm);
  border-top: 1px solid var(--border);
}

.legend-card-body p {
  font-size: var(--font-xs);
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.legend-dot.tensya {
  background: #eab308;
}

.legend-dot.ichiryumanbai {
  background: #dc2626;
}

.legend-dot.tora {
  background: #f59e0b;
}

.legend-dot.mi {
  background: #22c55e;
}

.legend-dot.tsuchinoto-mi {
  background: linear-gradient(135deg, #22c55e, #eab308);
}

.legend-dot.fujoubyou {
  background: #6b7280;
}

/* 雙人吉日 */
.favorites-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-md);
}

.favorites-header .section-title {
  margin: 0;
}

.partner-chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  margin-bottom: var(--space-lg);
}

.partner-chip {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s;
}

.partner-chip:hover {
  border-color: var(--accent);
  background: var(--bg-elevated);
}

.partner-chip.selected {
  border-color: var(--accent);
  background: rgba(245, 158, 11, 0.1);
}

.partner-name {
  font-weight: 500;
  color: var(--text-primary);
}

.partner-relation {
  font-size: var(--font-xs);
  color: var(--text-secondary);
}

.empty-partners {
  text-align: center;
  padding: var(--space-xl);
  color: var(--text-secondary);
}

.empty-partners .hint {
  font-size: var(--font-sm);
  margin-top: var(--space-xs);
}

/* 對象詳情 */
.partner-info-card {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: var(--space-md);
}

.partner-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-md);
  padding-bottom: var(--space-md);
  border-bottom: 1px solid var(--border);
}

.partner-main h4 {
  margin: 0;
  font-size: var(--font-lg);
  color: var(--text-primary);
}

.relation-badge {
  display: inline-block;
  margin-top: var(--space-xs);
  padding: 2px 8px;
  background: var(--bg-elevated);
  border-radius: var(--radius-sm);
  font-size: var(--font-xs);
  color: var(--text-secondary);
}

.partner-actions {
  display: flex;
  gap: var(--space-xs);
}

.compatibility-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-sm);
  margin-bottom: var(--space-md);
}

.mansion-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.mansion-name {
  font-weight: 500;
  color: var(--text-primary);
}

.mansion-element {
  font-size: var(--font-xs);
  color: var(--text-secondary);
}

.compat-score {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}

.score-label {
  font-weight: 500;
}

.score-value {
  font-size: var(--font-sm);
}

.compat-score.excellent { color: var(--success); }
.compat-score.good { color: var(--accent); }
.compat-score.fair { color: var(--info); }
.compat-score.caution { color: #eab308; }

.pair-actions {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.action-section {
  padding: var(--space-sm);
  background: var(--bg-elevated);
  border-radius: var(--radius-sm);
}

.action-name {
  font-size: var(--font-sm);
  font-weight: 600;
  color: var(--accent);
  margin: 0 0 var(--space-sm);
}

/* 配對吉日評級標籤 */
.pair-day-rating {
  padding: 2px 8px;
  border-radius: var(--radius-xs);
  font-size: var(--font-xs);
  font-weight: 700;
  letter-spacing: 0.5px;
}

.pair-day-rating.top {
  background: linear-gradient(135deg, #b45309, #d97706);
  color: #fff;
}

.pair-day-rating.good {
  background: #16a34a;
  color: #fff;
}

.pair-day-rating.mid {
  background: rgba(59, 130, 246, 0.15);
  color: var(--info);
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

.time-row.best .time-label {
  color: #16a34a;
}

.time-row.avoid .time-label {
  color: #b45309;
}

.time-value {
  color: var(--text-secondary);
  line-height: 1.5;
}

.pair-day-tip {
  margin: 0;
  font-size: var(--font-xs);
  color: var(--text-secondary);
  font-style: italic;
  line-height: 1.5;
}

/* 對話框表單 */
.partner-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

/* 關係選擇 - 單選按鈕組 */
.relation-fieldset {
  border: none;
  padding: 0;
  margin: 0;
}

.relation-legend {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  margin-bottom: var(--space-sm);
}

.relation-options {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.relation-option {
  display: flex;
  align-items: center;
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s;
}

.relation-option:hover {
  border-color: var(--accent);
}

.relation-option.selected {
  background: rgba(245, 158, 11, 0.15);
  border-color: var(--accent);
}

.relation-option input[type="radio"] {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.relation-label {
  font-size: var(--font-sm);
  color: var(--text-primary);
}

.relation-option.selected .relation-label {
  color: var(--accent);
  font-weight: 500;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-sm);
  margin-top: var(--space-md);
}

/* 特殊日區塊 */
.special-days-section {
  margin-bottom: var(--space-xl);
}

.special-days-nav {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-md);
  margin: var(--space-md) 0;
}

.nav-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg-surface);
  color: var(--text-secondary);
  cursor: pointer;
  transition: border-color 0.2s, color 0.2s;
}

.nav-btn:hover {
  border-color: var(--accent);
  color: var(--text-primary);
}

.nav-label {
  font-size: var(--font-sm);
  font-weight: 600;
  color: var(--text-primary);
  min-width: 100px;
  text-align: center;
}

.special-days-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.special-day-card {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: var(--space-sm) var(--space-md);
  transition: border-color 0.2s;
}

.special-day-card.kanro {
  border-left: 3px solid #C4A052;
}

.special-day-card.kongou {
  border-left: 3px solid #5B8FA8;
}

.special-day-card.rasetsu {
  border-left: 3px solid #E85D4C;
}

.special-day-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

.special-day-date {
  font-weight: 600;
  font-size: var(--font-sm);
  font-variant-numeric: tabular-nums;
}

.special-day-weekday {
  font-size: var(--font-xs);
  color: var(--text-secondary);
}

.special-day-type-badge {
  font-size: var(--font-xs);
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-weight: 600;
}

.special-day-type-badge.kanro {
  background: rgba(196, 160, 82, 0.2);
  color: #C4A052;
}

.special-day-type-badge.kongou {
  background: rgba(91, 143, 168, 0.2);
  color: #5B8FA8;
}

.special-day-type-badge.rasetsu {
  background: rgba(232, 93, 76, 0.2);
  color: #E85D4C;
}

.special-day-level {
  font-size: var(--font-xs);
  font-weight: 600;
  margin-left: auto;
}

.special-day-level.kanro { color: #C4A052; }
.special-day-level.kongou { color: #5B8FA8; }
.special-day-level.rasetsu { color: #E85D4C; }

.special-day-advice {
  font-size: var(--font-xs);
  color: var(--text-secondary);
  margin: var(--space-xs) 0 0;
  line-height: 1.5;
}

.ryouhan-tag {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: var(--radius-full);
  background: rgba(128, 0, 128, 0.15);
  color: #7b1fa2;
  font-weight: 600;
}

.ryouhan-note {
  font-size: var(--font-xs);
  color: #7b1fa2;
  margin: 2px 0 0;
  font-weight: 500;
}

@media (prefers-reduced-motion: reduce) {
  .lucky-tab {
    animation: none;
  }
}
</style>
