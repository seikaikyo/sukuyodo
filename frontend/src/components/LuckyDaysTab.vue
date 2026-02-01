<script setup lang="ts">
import { ref, computed } from 'vue'
import type { LuckyDaySummary, PairLuckyDaysResult } from '../composables/useSukuyodo'
import { useProfile, RELATION_TYPES, type Partner, type RelationType } from '../stores/profile'

const props = defineProps<{
  luckyDaySummary: LuckyDaySummary | null
  luckyDaySummaryLoading: boolean
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

const selectedPartner = computed(() => {
  if (!props.selectedPartnerId) return null
  return profile.value.partners.find(p => p.id === props.selectedPartnerId) || null
})
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
      <div v-if="luckyDaySummaryLoading" class="loading-state">
        <sl-spinner></sl-spinner>
        <span>載入吉日資料...</span>
      </div>

      <div v-else-if="luckyDaySummary" class="lucky-summary">
        <h3 class="section-title">未來 30 天吉日一覽</h3>

        <div class="category-list">
          <div
            v-for="item in luckyDaySummary.summary"
            :key="item.name"
            class="category-section"
          >
            <h4 class="category-name">{{ item.name }}</h4>

            <div v-if="item.lucky_days.length > 0" class="day-chips">
              <div
                v-for="day in item.lucky_days"
                :key="day.date"
                class="day-chip"
                :class="getScoreClass(day.score)"
              >
                <span class="chip-date">{{ formatDate(day.date) }}</span>
                <span class="chip-weekday">{{ day.weekday?.replace('曜日', '') }}</span>
                <span class="chip-rating">{{ day.rating || getRating(day.score) }}</span>
              </div>
            </div>
            <div v-else class="no-lucky-days">
              <span>近期無特別吉日</span>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="empty-state">
        <p>請先查詢本命宿</p>
      </div>
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
                <div v-if="action.lucky_days.length > 0" class="day-chips">
                  <div
                    v-for="day in action.lucky_days"
                    :key="day.date"
                    class="day-chip"
                    :class="getScoreClass(day.score)"
                  >
                    <span class="chip-date">{{ formatDate(day.date) }}</span>
                    <span class="chip-weekday">{{ day.weekday?.replace('曜日', '') }}</span>
                    <span class="chip-rating">{{ day.rating || getRating(day.score) }}</span>
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

@media (prefers-reduced-motion: reduce) {
  .lucky-tab {
    animation: none;
  }
}
</style>
