<script setup lang="ts">
import type { DailyFortune, WeeklyFortune, MonthlyFortune, YearlyFortune } from '../composables/useSukuyodo'

const props = defineProps<{
  activeTab: 'daily' | 'weekly' | 'monthly' | 'yearly'
  dailyFortune: DailyFortune | null
  weeklyFortune: WeeklyFortune | null
  monthlyFortune: MonthlyFortune | null
  yearlyFortune: YearlyFortune | null
}>()

const emit = defineEmits<{
  'update:activeTab': [value: 'daily' | 'weekly' | 'monthly' | 'yearly']
}>()

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
  <section class="fortune-tab">
    <div class="sub-tabs" role="tablist" aria-label="運勢週期選擇">
      <button
        class="pill-btn"
        :class="{ active: activeTab === 'daily' }"
        role="tab"
        :aria-selected="activeTab === 'daily'"
        aria-controls="panel-fortune-daily"
        @click="emit('update:activeTab', 'daily')"
      >今日</button>
      <button
        class="pill-btn"
        :class="{ active: activeTab === 'weekly' }"
        role="tab"
        :aria-selected="activeTab === 'weekly'"
        aria-controls="panel-fortune-weekly"
        @click="emit('update:activeTab', 'weekly')"
      >本週</button>
      <button
        class="pill-btn"
        :class="{ active: activeTab === 'monthly' }"
        role="tab"
        :aria-selected="activeTab === 'monthly'"
        aria-controls="panel-fortune-monthly"
        @click="emit('update:activeTab', 'monthly')"
      >本月</button>
      <button
        class="pill-btn"
        :class="{ active: activeTab === 'yearly' }"
        role="tab"
        :aria-selected="activeTab === 'yearly'"
        aria-controls="panel-fortune-yearly"
        @click="emit('update:activeTab', 'yearly')"
      >本年</button>
    </div>

    <!-- Daily Fortune -->
    <div v-if="activeTab === 'daily'" id="panel-fortune-daily" class="fortune-content" role="tabpanel">
      <template v-if="dailyFortune">
        <div class="fortune-card">
          <h3 class="fortune-title">
            {{ dailyFortune.date }} {{ dailyFortune.weekday.name }}
            <span class="weekday-element">({{ dailyFortune.weekday.element }}曜)</span>
          </h3>

          <div class="score-bars">
            <div class="score-row">
              <span class="score-label">事業</span>
              <div class="score-bar">
                <div class="score-fill" :class="getScoreClass(dailyFortune.fortune.career)" :style="{ width: dailyFortune.fortune.career + '%' }"></div>
              </div>
              <span class="score-value">{{ dailyFortune.fortune.career }}</span>
            </div>
            <div class="score-row">
              <span class="score-label">感情</span>
              <div class="score-bar">
                <div class="score-fill" :class="getScoreClass(dailyFortune.fortune.love)" :style="{ width: dailyFortune.fortune.love + '%' }"></div>
              </div>
              <span class="score-value">{{ dailyFortune.fortune.love }}</span>
            </div>
            <div class="score-row">
              <span class="score-label">健康</span>
              <div class="score-bar">
                <div class="score-fill" :class="getScoreClass(dailyFortune.fortune.health)" :style="{ width: dailyFortune.fortune.health + '%' }"></div>
              </div>
              <span class="score-value">{{ dailyFortune.fortune.health }}</span>
            </div>
            <div class="score-row">
              <span class="score-label">財運</span>
              <div class="score-bar">
                <div class="score-fill" :class="getScoreClass(dailyFortune.fortune.wealth)" :style="{ width: dailyFortune.fortune.wealth + '%' }"></div>
              </div>
              <span class="score-value">{{ dailyFortune.fortune.wealth }}</span>
            </div>
          </div>

          <div class="lucky-info">
            <div class="lucky-item">
              <span class="lucky-label">幸運色</span>
              <span class="lucky-value">
                <span class="color-dot" :style="{ background: dailyFortune.lucky.color_hex }"></span>
                {{ dailyFortune.lucky.color }}
              </span>
            </div>
            <div class="lucky-item">
              <span class="lucky-label">幸運方位</span>
              <span class="lucky-value">{{ dailyFortune.lucky.direction }}</span>
            </div>
            <div class="lucky-item">
              <span class="lucky-label">幸運數字</span>
              <span class="lucky-value">{{ dailyFortune.lucky.numbers.join(', ') }}</span>
            </div>
          </div>

          <div class="advice-box">
            <h4>今日建議</h4>
            <p>{{ dailyFortune.advice }}</p>
          </div>
        </div>
      </template>
      <div v-else class="loading-state">
        <sl-spinner></sl-spinner>
      </div>
    </div>

    <!-- Weekly Fortune -->
    <div v-if="activeTab === 'weekly'" id="panel-fortune-weekly" class="fortune-content" role="tabpanel">
      <template v-if="weeklyFortune">
        <div class="fortune-card">
          <h3 class="fortune-title">
            第 {{ weeklyFortune.week }} 週
            <span class="date-range">({{ weeklyFortune.week_start }} ~ {{ weeklyFortune.week_end }})</span>
          </h3>

          <div class="score-bars">
            <div class="score-row">
              <span class="score-label">整體</span>
              <div class="score-bar">
                <div class="score-fill" :class="getScoreClass(weeklyFortune.fortune.overall)" :style="{ width: weeklyFortune.fortune.overall + '%' }"></div>
              </div>
              <span class="score-value">{{ weeklyFortune.fortune.overall }}</span>
            </div>
            <div class="score-row">
              <span class="score-label">事業</span>
              <div class="score-bar">
                <div class="score-fill" :class="getScoreClass(weeklyFortune.fortune.career)" :style="{ width: weeklyFortune.fortune.career + '%' }"></div>
              </div>
              <span class="score-value">{{ weeklyFortune.fortune.career }}</span>
            </div>
            <div class="score-row">
              <span class="score-label">感情</span>
              <div class="score-bar">
                <div class="score-fill" :class="getScoreClass(weeklyFortune.fortune.love)" :style="{ width: weeklyFortune.fortune.love + '%' }"></div>
              </div>
              <span class="score-value">{{ weeklyFortune.fortune.love }}</span>
            </div>
          </div>

          <div class="daily-overview">
            <h4>每日概覽</h4>
            <div class="daily-list">
              <div
                v-for="day in weeklyFortune.daily_overview"
                :key="day.date"
                class="daily-item"
                :class="getScoreClass(day.score)"
              >
                <span class="day-date">{{ formatDate(day.date) }}</span>
                <span class="day-weekday">{{ day.weekday }}</span>
                <span class="day-score">{{ day.score }}</span>
              </div>
            </div>
          </div>

          <div class="advice-box">
            <h4>本週建議</h4>
            <p>{{ weeklyFortune.advice }}</p>
          </div>
        </div>
      </template>
      <div v-else class="loading-state">
        <sl-spinner></sl-spinner>
      </div>
    </div>

    <!-- Monthly Fortune -->
    <div v-if="activeTab === 'monthly'" id="panel-fortune-monthly" class="fortune-content" role="tabpanel">
      <template v-if="monthlyFortune">
        <div class="fortune-card">
          <h3 class="fortune-title">
            {{ monthlyFortune.year }} 年 {{ monthlyFortune.month }} 月
          </h3>

          <div v-if="monthlyFortune.theme" class="theme-box">
            <h4>{{ monthlyFortune.theme.title }}</h4>
            <p>{{ monthlyFortune.theme.focus }}</p>
          </div>

          <div class="score-bars">
            <div class="score-row">
              <span class="score-label">整體</span>
              <div class="score-bar">
                <div class="score-fill" :class="getScoreClass(monthlyFortune.fortune.overall)" :style="{ width: monthlyFortune.fortune.overall + '%' }"></div>
              </div>
              <span class="score-value">{{ monthlyFortune.fortune.overall }}</span>
            </div>
            <div class="score-row">
              <span class="score-label">事業</span>
              <div class="score-bar">
                <div class="score-fill" :class="getScoreClass(monthlyFortune.fortune.career)" :style="{ width: monthlyFortune.fortune.career + '%' }"></div>
              </div>
              <span class="score-value">{{ monthlyFortune.fortune.career }}</span>
            </div>
            <div class="score-row">
              <span class="score-label">感情</span>
              <div class="score-bar">
                <div class="score-fill" :class="getScoreClass(monthlyFortune.fortune.love)" :style="{ width: monthlyFortune.fortune.love + '%' }"></div>
              </div>
              <span class="score-value">{{ monthlyFortune.fortune.love }}</span>
            </div>
          </div>

          <div class="weekly-overview">
            <h4>每週概覽</h4>
            <div class="weekly-list">
              <div
                v-for="w in monthlyFortune.weekly"
                :key="w.week"
                class="weekly-item"
              >
                <span class="week-num">第 {{ w.week }} 週</span>
                <div class="week-bar">
                  <div class="week-fill" :class="getScoreClass(w.score)" :style="{ width: w.score + '%' }"></div>
                </div>
                <span class="week-score">{{ w.score }}</span>
              </div>
            </div>
          </div>

          <div class="advice-box">
            <h4>本月建議</h4>
            <p>{{ monthlyFortune.advice }}</p>
          </div>
        </div>
      </template>
      <div v-else class="loading-state">
        <sl-spinner></sl-spinner>
      </div>
    </div>

    <!-- Yearly Fortune -->
    <div v-if="activeTab === 'yearly'" id="panel-fortune-yearly" class="fortune-content" role="tabpanel">
      <template v-if="yearlyFortune">
        <div class="fortune-card">
          <h3 class="fortune-title">
            {{ yearlyFortune.year }} 年運勢
            <span class="year-info">({{ yearlyFortune.stem.character }}{{ yearlyFortune.branch.character }}年)</span>
          </h3>

          <div class="score-bars">
            <div class="score-row">
              <span class="score-label">整體</span>
              <div class="score-bar">
                <div class="score-fill" :class="getScoreClass(yearlyFortune.fortune.overall)" :style="{ width: yearlyFortune.fortune.overall + '%' }"></div>
              </div>
              <span class="score-value">{{ yearlyFortune.fortune.overall }}</span>
            </div>
            <div class="score-row">
              <span class="score-label">事業</span>
              <div class="score-bar">
                <div class="score-fill" :class="getScoreClass(yearlyFortune.fortune.career)" :style="{ width: yearlyFortune.fortune.career + '%' }"></div>
              </div>
              <span class="score-value">{{ yearlyFortune.fortune.career }}</span>
            </div>
            <div class="score-row">
              <span class="score-label">感情</span>
              <div class="score-bar">
                <div class="score-fill" :class="getScoreClass(yearlyFortune.fortune.love)" :style="{ width: yearlyFortune.fortune.love + '%' }"></div>
              </div>
              <span class="score-value">{{ yearlyFortune.fortune.love }}</span>
            </div>
            <div class="score-row">
              <span class="score-label">健康</span>
              <div class="score-bar">
                <div class="score-fill" :class="getScoreClass(yearlyFortune.fortune.health)" :style="{ width: yearlyFortune.fortune.health + '%' }"></div>
              </div>
              <span class="score-value">{{ yearlyFortune.fortune.health }}</span>
            </div>
            <div class="score-row">
              <span class="score-label">財運</span>
              <div class="score-bar">
                <div class="score-fill" :class="getScoreClass(yearlyFortune.fortune.wealth)" :style="{ width: yearlyFortune.fortune.wealth + '%' }"></div>
              </div>
              <span class="score-value">{{ yearlyFortune.fortune.wealth }}</span>
            </div>
          </div>

          <div v-if="yearlyFortune.opportunities?.length" class="opportunities">
            <h4>機會提示</h4>
            <ul>
              <li v-for="(opp, i) in yearlyFortune.opportunities" :key="i">{{ opp }}</li>
            </ul>
          </div>

          <div v-if="yearlyFortune.warnings?.length" class="warnings">
            <h4>注意事項</h4>
            <ul>
              <li v-for="(warn, i) in yearlyFortune.warnings" :key="i">{{ warn }}</li>
            </ul>
          </div>

          <div class="advice-box">
            <h4>年度建議</h4>
            <p>{{ yearlyFortune.advice }}</p>
          </div>
        </div>
      </template>
      <div v-else class="loading-state">
        <sl-spinner></sl-spinner>
      </div>
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

.fortune-content {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.fortune-card {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
}

.fortune-title {
  font-size: var(--font-lg);
  margin: 0 0 var(--space-lg);
  color: var(--text-primary);
  text-wrap: balance;
}

.weekday-element,
.date-range,
.year-info {
  color: var(--text-secondary);
  font-size: var(--font-sm);
  font-weight: 400;
}

.score-bars {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}

.score-row {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.score-label {
  width: 48px;
  color: var(--text-secondary);
  font-size: var(--font-sm);
}

.score-bar {
  flex: 1;
  height: 8px;
  background: var(--bg-elevated);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.score-fill {
  height: 100%;
  border-radius: var(--radius-sm);
  transition: width 0.5s ease;
}

.score-fill.excellent { background: var(--success); }
.score-fill.good { background: var(--accent); }
.score-fill.fair { background: var(--info); }
.score-fill.caution { background: #eab308; }
.score-fill.warning { background: var(--warning); }

.score-value {
  width: 32px;
  text-align: right;
  font-size: var(--font-sm);
  font-variant-numeric: tabular-nums;
  color: var(--text-secondary);
}

.lucky-info {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-lg);
  padding: var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-lg);
}

.lucky-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.lucky-label {
  color: var(--text-secondary);
  font-size: var(--font-xs);
}

.lucky-value {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: var(--font-sm);
}

.color-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
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

.theme-box {
  padding: var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-lg);
}

.theme-box h4 {
  color: var(--accent);
  margin: 0 0 var(--space-xs);
}

.theme-box p {
  color: var(--text-secondary);
  font-size: var(--font-sm);
  margin: 0;
}

.daily-overview,
.weekly-overview {
  margin-bottom: var(--space-lg);
}

.daily-overview h4,
.weekly-overview h4 {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  margin: 0 0 var(--space-sm);
}

.daily-list {
  display: flex;
  gap: var(--space-sm);
  overflow-x: auto;
  padding-bottom: var(--space-sm);
}

.daily-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-sm);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  min-width: 60px;
}

.daily-item.excellent { border-bottom: 2px solid var(--success); }
.daily-item.good { border-bottom: 2px solid var(--accent); }
.daily-item.fair { border-bottom: 2px solid var(--info); }
.daily-item.caution { border-bottom: 2px solid #eab308; }
.daily-item.warning { border-bottom: 2px solid var(--warning); }

.day-date {
  font-size: var(--font-xs);
  color: var(--text-secondary);
}

.day-weekday {
  font-size: var(--font-sm);
}

.day-score {
  font-size: var(--font-lg);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.weekly-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.weekly-item {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.week-num {
  width: 60px;
  font-size: var(--font-sm);
  color: var(--text-secondary);
}

.week-bar {
  flex: 1;
  height: 8px;
  background: var(--bg-elevated);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.week-fill {
  height: 100%;
  border-radius: var(--radius-sm);
}

.week-fill.excellent { background: var(--success); }
.week-fill.good { background: var(--accent); }
.week-fill.fair { background: var(--info); }
.week-fill.caution { background: #eab308; }
.week-fill.warning { background: var(--warning); }

.week-score {
  width: 32px;
  text-align: right;
  font-size: var(--font-sm);
  font-variant-numeric: tabular-nums;
  color: var(--text-secondary);
}

.opportunities,
.warnings {
  margin-bottom: var(--space-lg);
}

.opportunities h4 {
  color: var(--success);
  font-size: var(--font-sm);
  margin: 0 0 var(--space-sm);
}

.warnings h4 {
  color: var(--warning);
  font-size: var(--font-sm);
  margin: 0 0 var(--space-sm);
}

.opportunities ul,
.warnings ul {
  margin: 0;
  padding-left: var(--space-lg);
}

.opportunities li,
.warnings li {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  margin-bottom: var(--space-xs);
}

.loading-state {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: var(--space-2xl);
}

@media (prefers-reduced-motion: reduce) {
  .fortune-content {
    animation: none;
  }

  .score-fill {
    transition: none;
  }
}
</style>
