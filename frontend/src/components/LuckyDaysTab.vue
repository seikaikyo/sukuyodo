<script setup lang="ts">
import type { LuckyDayCategory, LuckyDayAction, LuckyDayResult } from '../composables/useSukuyodo'

const props = defineProps<{
  luckyDayCategories: LuckyDayCategory[]
  selectedLuckyCategory: string | null
  selectedLuckyAction: string | null
  currentCategoryActions: LuckyDayAction[]
  luckyDayResult: LuckyDayResult | null
  luckyDayLoading: boolean
}>()

const emit = defineEmits<{
  selectCategory: [categoryKey: string]
  selectAction: [actionKey: string]
}>()

function getFortuneLevel(score: number) {
  if (score >= 90) return { text: '大吉', class: 'excellent' }
  if (score >= 75) return { text: '吉', class: 'good' }
  if (score >= 60) return { text: '中吉', class: 'fair' }
  if (score >= 45) return { text: '小吉', class: 'caution' }
  return { text: '凶', class: 'warning' }
}

function getScoreClass(score: number) {
  if (score >= 90) return 'excellent'
  if (score >= 75) return 'good'
  if (score >= 60) return 'fair'
  if (score >= 45) return 'caution'
  return 'warning'
}

function formatDate(dateStr: string) {
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}/${d.getDate()}`
}
</script>

<template>
  <section class="lucky-tab">
    <div class="lucky-layout">
      <!-- Category Sidebar -->
      <aside class="lucky-sidebar" role="tablist" aria-label="吉日類別選擇">
        <button
          v-for="cat in luckyDayCategories"
          :key="cat.key"
          class="category-btn"
          :class="{ active: selectedLuckyCategory === cat.key }"
          role="tab"
          :aria-selected="selectedLuckyCategory === cat.key"
          aria-controls="panel-lucky-main"
          @click="emit('selectCategory', cat.key)"
        >
          <sl-icon :name="cat.icon" aria-hidden="true"></sl-icon>
          <span>{{ cat.name }}</span>
        </button>
      </aside>

      <!-- Main Content -->
      <div class="lucky-main">
        <template v-if="selectedLuckyCategory">
          <!-- Action Buttons -->
          <div class="action-btns" role="tablist" aria-label="項目選擇">
            <button
              v-for="act in currentCategoryActions"
              :key="act.key"
              class="action-btn"
              :class="{ active: selectedLuckyAction === act.key }"
              role="tab"
              :aria-selected="selectedLuckyAction === act.key"
              aria-controls="panel-lucky-results"
              @click="emit('selectAction', act.key)"
            >{{ act.name }}</button>
          </div>

          <!-- Results -->
          <div v-if="luckyDayLoading" class="loading-state">
            <sl-spinner></sl-spinner>
          </div>
          <div v-else-if="luckyDayResult" id="panel-lucky-results" class="lucky-results" role="tabpanel">
            <div class="results-grid">
              <div class="result-col good">
                <h4>近 30 天吉日</h4>
                <div class="day-list">
                  <div
                    v-for="day in luckyDayResult.lucky_days"
                    :key="day.date"
                    class="day-item"
                    :class="getScoreClass(day.score)"
                  >
                    <span class="day-date">{{ formatDate(day.date) }}</span>
                    <span class="day-weekday">{{ day.weekday }}</span>
                    <span class="day-rating">{{ day.rating || getFortuneLevel(day.score).text }}</span>
                  </div>
                </div>
              </div>
              <div class="result-col avoid">
                <h4>應避開的日期</h4>
                <div class="day-list">
                  <div
                    v-for="day in luckyDayResult.avoid_days"
                    :key="day.date"
                    class="day-item warning"
                  >
                    <span class="day-date">{{ formatDate(day.date) }}</span>
                    <span class="day-weekday">{{ day.weekday }}</span>
                    <span class="day-reason">{{ day.reason }}</span>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="luckyDayResult.advice" class="advice-box">
              <h4>建議</h4>
              <p>{{ luckyDayResult.advice }}</p>
            </div>
          </div>
          <div v-else class="select-prompt">
            <p>請選擇要查詢的項目</p>
          </div>
        </template>
        <template v-else>
          <div class="select-prompt">
            <p>請先選擇類別</p>
          </div>
        </template>
      </div>
    </div>
  </section>
</template>

<style scoped>
.lucky-layout {
  display: flex;
  gap: var(--space-lg);
}

.lucky-sidebar {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  min-width: 160px;
}

.category-btn {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-surface);
  border: none;
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: var(--font-sm);
  cursor: pointer;
  transition: background-color 0.2s, color 0.2s;
  text-align: left;
}

.category-btn:hover {
  background: var(--bg-elevated);
  color: var(--text-primary);
}

.category-btn.active {
  background: var(--accent);
  color: var(--bg-primary);
}

.category-btn:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.category-btn {
  min-height: 44px;
}

.lucky-main {
  flex: 1;
}

.action-btns {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  margin-bottom: var(--space-lg);
}

.action-btn {
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-full);
  color: var(--text-secondary);
  font-size: var(--font-sm);
  cursor: pointer;
  transition: background-color 0.2s, border-color 0.2s, color 0.2s;
}

.action-btn:hover {
  border-color: var(--accent);
  color: var(--text-primary);
}

.action-btn.active {
  background: var(--accent);
  border-color: var(--accent);
  color: var(--bg-primary);
}

.action-btn:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.action-btn {
  min-height: 44px;
}

.lucky-results {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.results-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-lg);
  margin-bottom: var(--space-lg);
}

.result-col h4 {
  font-size: var(--font-sm);
  margin: 0 0 var(--space-sm);
}

.result-col.good h4 { color: var(--success); }
.result-col.avoid h4 { color: var(--warning); }

.day-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.day-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm);
  background: var(--bg-surface);
  border-radius: var(--radius-sm);
}

.day-item.excellent { border-left: 3px solid var(--success); }
.day-item.good { border-left: 3px solid var(--accent); }
.day-item.fair { border-left: 3px solid var(--info); }
.day-item.caution { border-left: 3px solid #eab308; }
.day-item.warning { border-left: 3px solid var(--warning); }

.day-date {
  font-size: var(--font-sm);
  font-variant-numeric: tabular-nums;
}

.day-weekday {
  font-size: var(--font-sm);
  color: var(--text-secondary);
}

.day-rating {
  margin-left: auto;
  font-size: var(--font-sm);
  color: var(--success);
}

.day-reason {
  margin-left: auto;
  font-size: var(--font-sm);
  color: var(--warning);
}

.advice-box {
  padding: var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  border-left: 3px solid var(--accent);
}

.advice-box h4 {
  font-size: var(--font-sm);
  color: var(--accent);
  margin: 0 0 var(--space-sm);
}

.advice-box p {
  margin: 0;
  font-size: var(--font-sm);
  color: var(--text-secondary);
  line-height: 1.6;
}

.select-prompt {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: var(--space-2xl);
  color: var(--text-secondary);
}

.loading-state {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: var(--space-2xl);
}

@media (max-width: 767px) {
  .lucky-layout {
    flex-direction: column;
  }

  .lucky-sidebar {
    flex-direction: row;
    overflow-x: auto;
    min-width: auto;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
  }

  .lucky-sidebar::-webkit-scrollbar {
    display: none;
  }

  .category-btn {
    white-space: nowrap;
  }

  .results-grid {
    grid-template-columns: 1fr;
  }
}

@media (prefers-reduced-motion: reduce) {
  .lucky-results {
    animation: none;
  }
}
</style>
