<script setup lang="ts">
import type { Mansion, DailyFortune } from '../composables/useSukuyodo'
import { getFortuneLevel, getMansionRelationClass } from '../utils/fortune-helpers'

const props = defineProps<{
  mansion: Mansion
  dailyFortune: DailyFortune | null
  elementColor: string
}>()

const emit = defineEmits<{
  query: []
  'navigate-fortune': []
  'navigate-knowledge': [tab: string]
}>()
</script>

<template>
  <section class="summary-card">
    <div class="summary-main">
      <div class="summary-mansion">
        <span class="mansion-star">&#9733;</span>
        <ruby class="mansion-name">
          {{ mansion.name_jp }}<rp>(</rp><rt>{{ mansion.reading }}</rt><rp>)</rp>
        </ruby>
        <span class="mansion-element term-link" :style="{ background: elementColor }" @click="emit('navigate-knowledge', 'elements')">
          {{ mansion.element }}
        </span>
      </div>
      <p class="mansion-desc">{{ mansion.personality }}</p>
      <div
        v-if="dailyFortune?.mansion_relation"
        class="mansion-relation"
        :class="getMansionRelationClass(dailyFortune.mansion_relation.type)"
      >
        <span class="relation-title">今日與本命宿關係：<strong class="term-link" @click.stop="emit('navigate-knowledge', 'relations')">{{ dailyFortune.mansion_relation.name }}（{{ dailyFortune.mansion_relation.reading }}）</strong></span>
        <span class="relation-desc">{{ dailyFortune.mansion_relation.description }}</span>
      </div>
    </div>
    <button
      class="summary-fortune"
      :disabled="!dailyFortune"
      aria-label="查看今日運勢詳情"
      @click="dailyFortune && emit('navigate-fortune')"
    >
      <template v-if="dailyFortune">
        <div class="fortune-score" :class="getFortuneLevel(dailyFortune.fortune.overall, dailyFortune.fortune.level).class">
          {{ dailyFortune.fortune.overall }}
        </div>
        <div class="fortune-label">今日運勢</div>
        <div class="fortune-level" :class="getFortuneLevel(dailyFortune.fortune.overall, dailyFortune.fortune.level).class">
          <ruby v-if="dailyFortune.fortune.level_reading">{{ dailyFortune.fortune.level_name || getFortuneLevel(dailyFortune.fortune.overall, dailyFortune.fortune.level).text }}<rp>(</rp><rt>{{ dailyFortune.fortune.level_reading }}</rt><rp>)</rp></ruby>
          <template v-else>{{ dailyFortune.fortune.level_name || getFortuneLevel(dailyFortune.fortune.overall, dailyFortune.fortune.level).text }}</template>
        </div>
      </template>
      <sl-spinner v-else></sl-spinner>
    </button>
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
  color: var(--text-on-accent);
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
.mansion-relation.caution { border-left: 3px solid var(--caution); }
.mansion-relation.warning { border-left: 3px solid var(--warning); }

.summary-fortune {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-xs);
  min-width: 80px;
  background: none;
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  padding: var(--space-sm);
  cursor: pointer;
  transition: border-color 0.2s, background-color 0.2s;
  font: inherit;
  color: inherit;
}

.summary-fortune:not(:disabled):hover {
  border-color: var(--accent);
  background: var(--bg-elevated);
}

.summary-fortune:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.summary-fortune:disabled {
  cursor: default;
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
.fortune-score.caution { color: var(--caution); }
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
.fortune-level.caution { color: var(--caution); }
.fortune-level.warning { color: var(--warning); }

@media (max-width: 767px) {
  .summary-card {
    flex-direction: column;
    text-align: center;
    gap: var(--space-md);
    padding: var(--space-md);
  }

  .summary-mansion {
    justify-content: center;
  }

  .fortune-score {
    font-size: 36px;
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
