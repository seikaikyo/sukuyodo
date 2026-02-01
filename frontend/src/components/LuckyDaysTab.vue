<script setup lang="ts">
import type { LuckyDaySummary } from '../composables/useSukuyodo'

const props = defineProps<{
  luckyDaySummary: LuckyDaySummary | null
  luckyDaySummaryLoading: boolean
}>()

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
</script>

<template>
  <section class="lucky-tab">
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

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-2xl);
  color: var(--text-secondary);
}

.section-title {
  font-size: var(--font-lg);
  margin: 0 0 var(--space-lg);
  color: var(--text-primary);
}

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

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: var(--space-2xl);
  color: var(--text-secondary);
}

@media (prefers-reduced-motion: reduce) {
  .lucky-tab {
    animation: none;
  }
}
</style>
