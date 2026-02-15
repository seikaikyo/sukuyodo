<script setup lang="ts">
import type { DailyFortune, WeeklyFortune, MonthlyFortune, YearlyFortune } from '../composables/useSukuyodo'

const props = defineProps<{
  activeTab: 'daily' | 'weekly' | 'monthly' | 'yearly'
  dailyFortune: DailyFortune | null
  weeklyFortune: WeeklyFortune | null
  monthlyFortune: MonthlyFortune | null
  yearlyFortune: YearlyFortune | null
  expandedMonthlyWeek: number | null
  currentWeekNumber: number
}>()

const emit = defineEmits<{
  'update:activeTab': [value: 'daily' | 'weekly' | 'monthly' | 'yearly']
  'toggleWeek': [week: number]
  'selectDay': [date: string]
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
            <div class="score-row overall-row">
              <span class="score-label">整體</span>
              <div class="score-bar">
                <div class="score-fill" :class="getScoreClass(dailyFortune.fortune.overall)" :style="{ width: dailyFortune.fortune.overall + '%' }"></div>
              </div>
              <span class="score-value" :class="getScoreClass(dailyFortune.fortune.overall)">{{ dailyFortune.fortune.overall }}</span>
            </div>
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
            本週運勢
            <span class="date-range">({{ formatDate(weeklyFortune.week_start) }} ~ {{ formatDate(weeklyFortune.week_end) }})</span>
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
            <h4>每日概覽（點擊查看詳情）</h4>
            <div class="daily-list">
              <button
                v-for="day in weeklyFortune.daily_overview"
                :key="day.date"
                class="daily-item"
                :class="[getScoreClass(day.score), { 'is-today': day.is_today, 'is-yesterday': day.is_yesterday }]"
                :aria-label="`查看 ${formatDate(day.date)} ${day.weekday} 詳細運勢`"
                @click="emit('selectDay', day.date)"
              >
                <span class="day-label" v-if="day.is_today">今日</span>
                <span class="day-label yesterday" v-else-if="day.is_yesterday">昨日</span>
                <span class="day-date">{{ formatDate(day.date) }}</span>
                <span class="day-weekday">{{ day.weekday }}</span>
                <span class="day-score">{{ day.score }}</span>
              </button>
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
            <p class="theme-focus">{{ monthlyFortune.theme.focus }}</p>
            <p v-if="monthlyFortune.theme.description" class="theme-desc">{{ monthlyFortune.theme.description }}</p>
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
                class="weekly-item-wrapper"
              >
                <button
                  class="weekly-item"
                  :class="{ expanded: expandedMonthlyWeek === w.week }"
                  :aria-expanded="expandedMonthlyWeek === w.week"
                  :aria-controls="`week-detail-${w.week}`"
                  @click="emit('toggleWeek', w.week)"
                  @keydown.enter="emit('toggleWeek', w.week)"
                  @keydown.space.prevent="emit('toggleWeek', w.week)"
                >
                  <span class="week-toggle" aria-hidden="true">{{ expandedMonthlyWeek === w.week ? '▼' : '▶' }}</span>
                  <span class="week-num">第 {{ w.week }} 週</span>
                  <span v-if="w.week === currentWeekNumber" class="week-current-tag">本週</span>
                  <div class="week-bar">
                    <div class="week-fill" :class="getScoreClass(w.score)" :style="{ width: w.score + '%' }"></div>
                  </div>
                  <span class="week-score">{{ w.score }}</span>
                </button>

                <!-- 展開的週詳細內容 -->
                <div
                  v-if="expandedMonthlyWeek === w.week"
                  :id="`week-detail-${w.week}`"
                  class="week-detail"
                >
                  <div class="week-detail-content">
                    <div class="week-date-range">
                      {{ formatDate(w.week_start) }} ~ {{ formatDate(w.week_end) }}
                    </div>

                    <div class="week-detail-daily">
                      <span class="daily-label">每日：</span>
                      <div class="daily-chips">
                        <button
                          v-for="day in w.daily_overview"
                          :key="day.date"
                          class="daily-chip clickable"
                          :class="getScoreClass(day.score)"
                          @click="emit('selectDay', day.date)"
                        >
                          {{ formatDate(day.date) }} {{ day.weekday?.replace('曜日', '') }} {{ day.score }}
                        </button>
                      </div>
                    </div>

                    <div class="week-detail-focus">
                      <span class="focus-label">重點：</span>
                      <span class="focus-text">{{ w.focus }}</span>
                    </div>
                  </div>
                </div>
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
  margin-bottom: var(--space-md);
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
  padding: var(--space-md);
}

.fortune-title {
  font-size: var(--font-lg);
  margin: 0 0 var(--space-md);
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
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
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

.score-value.excellent { color: var(--success); font-weight: 600; }
.score-value.good { color: var(--accent); font-weight: 600; }
.score-value.fair { color: var(--info); font-weight: 600; }
.score-value.caution { color: #eab308; font-weight: 600; }
.score-value.warning { color: var(--warning); font-weight: 600; }

.overall-row {
  padding-bottom: var(--space-sm);
  margin-bottom: var(--space-xs);
  border-bottom: 1px solid var(--border);
}

.overall-row .score-label {
  font-weight: 600;
  color: var(--text-primary);
}

.overall-row .score-bar {
  height: 10px;
}

.lucky-info {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-md);
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-md);
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
  padding: var(--space-sm) var(--space-md);
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
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-md);
}

.theme-box h4 {
  color: var(--accent);
  margin: 0 0 var(--space-xs);
}

.theme-box .theme-focus {
  color: var(--text-secondary);
  font-size: var(--font-sm);
  margin: 0;
}

.theme-box .theme-desc {
  color: var(--text-secondary);
  font-size: var(--font-sm);
  line-height: 1.6;
  margin: var(--space-sm) 0 0;
}

.daily-overview,
.weekly-overview {
  margin-bottom: var(--space-md);
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
  gap: 2px;
  padding: var(--space-xs) var(--space-sm);
  background: var(--bg-elevated);
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  min-width: 52px;
  cursor: pointer;
  font: inherit;
  color: inherit;
  transition: background-color 0.2s, border-color 0.2s, transform 0.15s;
}

.daily-item:hover {
  background: var(--bg-primary);
  border-color: var(--border);
  transform: translateY(-2px);
}

.daily-item:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.daily-item.excellent { border-bottom: 2px solid var(--success); }
.daily-item.good { border-bottom: 2px solid var(--accent); }
.daily-item.fair { border-bottom: 2px solid var(--info); }
.daily-item.caution { border-bottom: 2px solid #eab308; }
.daily-item.warning { border-bottom: 2px solid var(--warning); }

.daily-item.is-today {
  background: var(--accent);
  color: var(--bg-primary);
  border-color: var(--accent);
}

.daily-item.is-today:hover {
  background: var(--accent);
  opacity: 0.9;
}

.daily-item.is-today .day-date,
.daily-item.is-today .day-weekday {
  color: var(--bg-primary);
}

.daily-item.is-yesterday {
  opacity: 0.7;
}

.day-label {
  font-size: var(--font-xs);
  font-weight: 600;
  color: var(--accent);
  background: rgba(245, 158, 11, 0.15);
  padding: 1px 6px;
  border-radius: var(--radius-sm);
  margin-bottom: 2px;
}

.daily-item.is-today .day-label {
  color: var(--bg-primary);
  background: rgba(255, 255, 255, 0.3);
}

.day-label.yesterday {
  color: var(--text-secondary);
  background: var(--bg-elevated);
}

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
  gap: var(--space-xs);
}

.weekly-item-wrapper {
  display: flex;
  flex-direction: column;
}

.weekly-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  width: 100%;
  padding: var(--space-sm) var(--space-md);
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background-color 0.2s, border-color 0.2s;
  font: inherit;
  color: inherit;
  text-align: left;
}

.weekly-item:hover {
  background: var(--bg-elevated);
  border-color: var(--border);
}

.weekly-item:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.weekly-item.expanded {
  background: var(--bg-elevated);
  border-color: var(--accent);
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
}

.week-toggle {
  width: 16px;
  font-size: var(--font-xs);
  color: var(--text-secondary);
  flex-shrink: 0;
}

.week-num {
  width: 56px;
  font-size: var(--font-sm);
  color: var(--text-secondary);
  flex-shrink: 0;
}

.week-current-tag {
  font-size: var(--font-xs);
  color: var(--accent);
  background: rgba(245, 158, 11, 0.15);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
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
  flex-shrink: 0;
}

/* Week Detail Expansion */
.week-detail {
  background: var(--bg-elevated);
  border: 1px solid var(--accent);
  border-top: none;
  border-radius: 0 0 var(--radius-md) var(--radius-md);
  padding: var(--space-md);
  animation: slideDown 0.2s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.week-detail-loading {
  display: flex;
  justify-content: center;
  padding: var(--space-md);
}

.week-detail-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.week-detail-scores {
  display: flex;
  gap: var(--space-lg);
  flex-wrap: wrap;
}

.detail-score-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.detail-label {
  font-size: var(--font-sm);
  color: var(--text-secondary);
}

.detail-value {
  font-size: var(--font-md);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.detail-value.excellent { color: var(--success); }
.detail-value.good { color: var(--accent); }
.detail-value.fair { color: var(--info); }
.detail-value.caution { color: #eab308; }
.detail-value.warning { color: var(--warning); }

.week-detail-daily {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

.daily-label {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  flex-shrink: 0;
}

.daily-chips {
  display: flex;
  gap: var(--space-xs);
  flex-wrap: wrap;
}

.daily-chip {
  font-size: var(--font-xs);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  background: var(--bg-primary);
  font-variant-numeric: tabular-nums;
}

.daily-chip.excellent { border-left: 2px solid var(--success); }
.daily-chip.good { border-left: 2px solid var(--accent); }
.daily-chip.fair { border-left: 2px solid var(--info); }
.daily-chip.caution { border-left: 2px solid #eab308; }
.daily-chip.warning { border-left: 2px solid var(--warning); }

.daily-chip.clickable {
  cursor: pointer;
  border: none;
  font: inherit;
  transition: background-color 0.2s, transform 0.15s;
}

.daily-chip.clickable:hover {
  background: var(--bg-elevated);
  transform: translateY(-1px);
}

.daily-chip.clickable:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.week-date-range {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  margin-bottom: var(--space-sm);
}

.week-detail-focus {
  font-size: var(--font-sm);
  line-height: 1.5;
}

.focus-label {
  color: var(--accent);
  margin-right: var(--space-xs);
}

.focus-text {
  color: var(--text-secondary);
}

.week-detail-advice {
  font-size: var(--font-sm);
  line-height: 1.5;
}

.advice-label {
  color: var(--accent);
  margin-right: var(--space-xs);
}

.advice-text {
  color: var(--text-secondary);
}

@media (prefers-reduced-motion: reduce) {
  .week-detail {
    animation: none;
  }
}

.opportunities,
.warnings {
  margin-bottom: var(--space-md);
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
