<script setup lang="ts">
import type { Mansion, DailyFortune } from '../composables/useSukuyodo'

const props = defineProps<{
  mansion: Mansion
  dailyFortune: DailyFortune | null
  elementColor: string
}>()

const emit = defineEmits<{
  query: []
}>()

function getFortuneLevel(score: number) {
  if (score >= 90) return { text: '大吉', class: 'excellent' }
  if (score >= 75) return { text: '吉', class: 'good' }
  if (score >= 60) return { text: '中吉', class: 'fair' }
  if (score >= 45) return { text: '小吉', class: 'caution' }
  return { text: '凶', class: 'warning' }
}

function getMansionRelationClass(relationType: string) {
  const classMap: Record<string, string> = {
    'eishin': 'excellent',
    'gyotai': 'good',
    'mei': 'fair',
    'yusui': 'neutral',
    'kisei': 'caution',
    'ankai': 'warning'
  }
  return classMap[relationType] || 'neutral'
}
</script>

<template>
  <section class="summary-card">
    <div class="summary-main">
      <div class="summary-mansion">
        <span class="mansion-star">&#9733;</span>
        <ruby class="mansion-name">
          {{ mansion.name_jp }}<rp>(</rp><rt>{{ mansion.reading }}</rt><rp>)</rp>
        </ruby>
        <span class="mansion-element" :style="{ background: elementColor }">
          {{ mansion.element }}
        </span>
      </div>
      <p class="mansion-desc">{{ mansion.personality }}</p>
      <div
        v-if="dailyFortune?.mansion_relation"
        class="mansion-relation"
        :class="getMansionRelationClass(dailyFortune.mansion_relation.type)"
      >
        <span class="relation-title">今日與本命宿關係：<strong>{{ dailyFortune.mansion_relation.name }}（{{ dailyFortune.mansion_relation.reading }}）</strong></span>
        <span class="relation-desc">{{ dailyFortune.mansion_relation.description }}</span>
      </div>
    </div>
    <div class="summary-fortune">
      <template v-if="dailyFortune">
        <div class="fortune-score" :class="getFortuneLevel(dailyFortune.fortune.overall).class">
          {{ dailyFortune.fortune.overall }}
        </div>
        <div class="fortune-label">今日運勢</div>
        <div class="fortune-level" :class="getFortuneLevel(dailyFortune.fortune.overall).class">
          {{ getFortuneLevel(dailyFortune.fortune.overall).text }}
        </div>
      </template>
      <sl-spinner v-else></sl-spinner>
    </div>
  </section>
</template>

<style scoped>
.summary-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-lg);
  background: linear-gradient(135deg, var(--bg-surface) 0%, var(--bg-primary) 100%);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-lg);
}

.summary-main {
  flex: 1;
}

.summary-mansion {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
}

.mansion-star {
  color: var(--accent);
  font-size: var(--font-xl);
}

.mansion-name {
  font-size: var(--font-xl);
  font-weight: 700;
  color: var(--accent);
}

.mansion-name rt {
  font-size: var(--font-xs);
  color: var(--text-secondary);
}

.mansion-element {
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  color: var(--bg-primary);
  font-size: var(--font-sm);
  font-weight: 600;
}

.mansion-desc {
  color: var(--text-secondary);
  font-size: var(--font-sm);
  margin: 0 0 var(--space-sm);
}

.mansion-relation {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: var(--font-sm);
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  background: var(--bg-elevated);
}

.relation-title {
  line-height: 1.4;
}

.relation-desc {
  color: var(--text-secondary);
  font-size: var(--font-xs);
  line-height: 1.4;
}

.mansion-relation.excellent { border-left: 3px solid var(--stellar); }
.mansion-relation.good { border-left: 3px solid var(--success); }
.mansion-relation.fair { border-left: 3px solid var(--info); }
.mansion-relation.neutral { border-left: 3px solid var(--text-secondary); }
.mansion-relation.caution { border-left: 3px solid #eab308; }
.mansion-relation.warning { border-left: 3px solid var(--warning); }

.summary-fortune {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-xs);
  min-width: 80px;
}

.fortune-score {
  font-size: 48px;
  font-weight: 700;
  line-height: 1;
  font-variant-numeric: tabular-nums;
}

.fortune-score.excellent { color: var(--stellar); }
.fortune-score.good { color: var(--success); }
.fortune-score.fair { color: var(--info); }
.fortune-score.caution { color: #eab308; }
.fortune-score.warning { color: var(--warning); }

.fortune-label {
  color: var(--text-secondary);
  font-size: var(--font-xs);
}

.fortune-level {
  font-size: var(--font-sm);
  font-weight: 600;
}

.fortune-level.excellent { color: var(--stellar); }
.fortune-level.good { color: var(--success); }
.fortune-level.fair { color: var(--info); }
.fortune-level.caution { color: #eab308; }
.fortune-level.warning { color: var(--warning); }

@media (max-width: 767px) {
  .summary-card {
    flex-direction: column;
    text-align: center;
    gap: var(--space-md);
  }

  .summary-mansion {
    justify-content: center;
  }

  .mansion-relation {
    text-align: left;
  }
}

@media (prefers-reduced-motion: reduce) {
  * {
    transition: none !important;
  }
}
</style>
