<script setup lang="ts">
import type { DailyFortune, WeeklyFortune, MonthlyFortune, YearlyFortune } from '../composables/useSukuyodo'
import { getScoreClass, formatDate } from '../utils/fortune-helpers'

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

function getKuyouLevelClass(level: string) {
  if (level === '大吉') return 'level-great'
  if (level === '吉') return 'level-good'
  if (level === '半吉') return 'level-half'
  return 'level-bad'
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
            <div class="score-group">
              <div class="score-row">
                <span class="score-label">事業</span>
                <div class="score-bar">
                  <div class="score-fill" :class="getScoreClass(dailyFortune.fortune.career)" :style="{ width: dailyFortune.fortune.career + '%' }"></div>
                </div>
                <span class="score-value">{{ dailyFortune.fortune.career }}</span>
              </div>
              <p v-if="dailyFortune.fortune.career_desc" class="score-desc">{{ dailyFortune.fortune.career_desc }}</p>
            </div>
            <div class="score-group">
              <div class="score-row">
                <span class="score-label">感情</span>
                <div class="score-bar">
                  <div class="score-fill" :class="getScoreClass(dailyFortune.fortune.love)" :style="{ width: dailyFortune.fortune.love + '%' }"></div>
                </div>
                <span class="score-value">{{ dailyFortune.fortune.love }}</span>
              </div>
              <p v-if="dailyFortune.fortune.love_desc" class="score-desc">{{ dailyFortune.fortune.love_desc }}</p>
            </div>
            <div class="score-group">
              <div class="score-row">
                <span class="score-label">健康</span>
                <div class="score-bar">
                  <div class="score-fill" :class="getScoreClass(dailyFortune.fortune.health)" :style="{ width: dailyFortune.fortune.health + '%' }"></div>
                </div>
                <span class="score-value">{{ dailyFortune.fortune.health }}</span>
              </div>
              <p v-if="dailyFortune.fortune.health_desc" class="score-desc">{{ dailyFortune.fortune.health_desc }}</p>
            </div>
            <div class="score-group">
              <div class="score-row">
                <span class="score-label">財運</span>
                <div class="score-bar">
                  <div class="score-fill" :class="getScoreClass(dailyFortune.fortune.wealth)" :style="{ width: dailyFortune.fortune.wealth + '%' }"></div>
                </div>
                <span class="score-value">{{ dailyFortune.fortune.wealth }}</span>
              </div>
              <p v-if="dailyFortune.fortune.wealth_desc" class="score-desc">{{ dailyFortune.fortune.wealth_desc }}</p>
            </div>
          </div>

          <div class="score-legend">
            <span class="legend-item"><span class="legend-dot excellent"></span>90+ 大吉</span>
            <span class="legend-item"><span class="legend-dot good"></span>75+ 吉</span>
            <span class="legend-item"><span class="legend-dot fair"></span>60+ 中吉</span>
            <span class="legend-item"><span class="legend-dot caution"></span>45+ 小吉</span>
            <span class="legend-item"><span class="legend-dot warning"></span>&lt;45 注意</span>
          </div>

          <div v-if="dailyFortune.special_day" class="special-day-banner" :class="[dailyFortune.special_day.type, { reversed: dailyFortune.special_day.ryouhan_reversed }]">
            <span class="special-day-level">{{ dailyFortune.special_day.level }}</span>
            <span class="special-day-name">{{ dailyFortune.special_day.name }}</span>
            <p class="special-day-desc">{{ dailyFortune.special_day.description }}</p>
            <p v-if="dailyFortune.special_day.ryouhan_reversed" class="special-day-reversed">
              凌犯期間，吉凶逆轉（凌犯期間中のため吉凶が逆轉しています）
            </p>
          </div>

          <div v-if="dailyFortune.ryouhan" class="ryouhan-banner">
            <span class="ryouhan-label">凌犯期間</span>
            <p class="ryouhan-desc">{{ dailyFortune.ryouhan.description }}</p>
          </div>

          <div v-if="dailyFortune.rokugai" class="rokugai-banner">
            <span class="rokugai-label">六害宿「{{ dailyFortune.rokugai.name }}」</span>
            <p class="rokugai-desc">{{ dailyFortune.rokugai.description }}</p>
          </div>

          <div v-if="dailyFortune.sanki" class="sanki-box" :class="{ 'dark-week': dailyFortune.sanki.is_dark_week }">
            <div class="sanki-header">
              <span class="sanki-period" :class="'sanki-' + dailyFortune.sanki.period_index">
                <ruby v-if="dailyFortune.sanki.period_reading">{{ dailyFortune.sanki.period }}<rp>(</rp><rt>{{ dailyFortune.sanki.period_reading }}</rt><rp>)</rp></ruby>
                <template v-else>{{ dailyFortune.sanki.period }}</template>
              </span>
              <span class="sanki-day-type">
                <ruby v-if="dailyFortune.sanki.day_type_reading">{{ dailyFortune.sanki.day_type }}<rp>(</rp><rt>{{ dailyFortune.sanki.day_type_reading }}</rt><rp>)</rp></ruby>
                <template v-else>{{ dailyFortune.sanki.day_type }}</template>
              </span>
              <span v-if="dailyFortune.sanki.is_dark_week" class="dark-week-label">暗黑週（暗黒の一週間）</span>
            </div>
            <p class="sanki-day-desc">{{ dailyFortune.sanki.day_description }}</p>
            <p class="sanki-period-desc">{{ dailyFortune.sanki.period_description }}</p>
          </div>

          <div class="lucky-info">
            <div class="lucky-item">
              <span class="lucky-label">幸運色</span>
              <span class="lucky-value">
                <span class="color-dot" :style="{ background: dailyFortune.lucky.color_hex }"></span>
                <ruby v-if="dailyFortune.lucky.color_reading">{{ dailyFortune.lucky.color }}<rp>(</rp><rt>{{ dailyFortune.lucky.color_reading }}</rt><rp>)</rp></ruby>
                <template v-else>{{ dailyFortune.lucky.color }}</template>
              </span>
            </div>
            <div class="lucky-item">
              <span class="lucky-label">幸運方位</span>
              <span class="lucky-value">
                <ruby v-if="dailyFortune.lucky.direction_reading">{{ dailyFortune.lucky.direction }}<rp>(</rp><rt>{{ dailyFortune.lucky.direction_reading }}</rt><rp>)</rp></ruby>
                <template v-else>{{ dailyFortune.lucky.direction }}</template>
              </span>
            </div>
            <div class="lucky-item">
              <span class="lucky-label">幸運數字</span>
              <span class="lucky-value">{{ dailyFortune.lucky.numbers.join(', ') }}</span>
            </div>
          </div>

          <div class="mansion-hint">
            <h4>
              今日宿曜提示
              <span class="hint-relation" :class="dailyFortune.mansion_relation.type">{{ dailyFortune.mansion_relation.name }}</span>
            </h4>
            <p class="hint-mansions">
              本命宿 <strong>{{ dailyFortune.your_mansion.name_jp }}</strong>（{{ dailyFortune.your_mansion.element }}）
              ／當日宿 <strong>{{ dailyFortune.day_mansion.name_jp }}</strong>（{{ dailyFortune.day_mansion.element }}）
            </p>
            <p>{{ dailyFortune.mansion_relation.description }}</p>
            <p v-if="dailyFortune.element_relation" class="hint-element">
              {{ dailyFortune.element_relation.description }}
            </p>
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
            <div class="score-row">
              <span class="score-label">健康</span>
              <div class="score-bar">
                <div class="score-fill" :class="getScoreClass(weeklyFortune.fortune.health)" :style="{ width: weeklyFortune.fortune.health + '%' }"></div>
              </div>
              <span class="score-value">{{ weeklyFortune.fortune.health }}</span>
            </div>
            <div class="score-row">
              <span class="score-label">財運</span>
              <div class="score-bar">
                <div class="score-fill" :class="getScoreClass(weeklyFortune.fortune.wealth)" :style="{ width: weeklyFortune.fortune.wealth + '%' }"></div>
              </div>
              <span class="score-value">{{ weeklyFortune.fortune.wealth }}</span>
            </div>
          </div>

          <div class="score-legend">
            <span class="legend-item"><span class="legend-dot excellent"></span>90+ 大吉</span>
            <span class="legend-item"><span class="legend-dot good"></span>75+ 吉</span>
            <span class="legend-item"><span class="legend-dot fair"></span>60+ 中吉</span>
            <span class="legend-item"><span class="legend-dot caution"></span>45+ 小吉</span>
            <span class="legend-item"><span class="legend-dot warning"></span>&lt;45 注意</span>
          </div>

          <div v-if="weeklyFortune.lucky" class="lucky-info">
            <div class="lucky-item">
              <span class="lucky-label">幸運色</span>
              <span class="lucky-value">
                <span class="color-dot" :style="{ background: weeklyFortune.lucky.color_hex }"></span>
                <ruby v-if="weeklyFortune.lucky.color_reading">{{ weeklyFortune.lucky.color }}<rp>(</rp><rt>{{ weeklyFortune.lucky.color_reading }}</rt><rp>)</rp></ruby>
                <template v-else>{{ weeklyFortune.lucky.color }}</template>
              </span>
            </div>
            <div class="lucky-item">
              <span class="lucky-label">幸運方位</span>
              <span class="lucky-value">
                <ruby v-if="weeklyFortune.lucky.direction_reading">{{ weeklyFortune.lucky.direction }}<rp>(</rp><rt>{{ weeklyFortune.lucky.direction_reading }}</rt><rp>)</rp></ruby>
                <template v-else>{{ weeklyFortune.lucky.direction }}</template>
              </span>
            </div>
          </div>

          <div v-if="weeklyFortune.focus" class="weekly-focus">
            <h4>本週焦點</h4>
            <p>{{ weeklyFortune.focus }}</p>
          </div>

          <div v-if="weeklyFortune.category_tips" class="category-descriptions">
            <div v-if="weeklyFortune.category_tips.career" class="category-desc-item">
              <h4>事業</h4>
              <p>{{ weeklyFortune.category_tips.career }}</p>
            </div>
            <div v-if="weeklyFortune.category_tips.love" class="category-desc-item">
              <h4>感情</h4>
              <p>{{ weeklyFortune.category_tips.love }}</p>
            </div>
            <div v-if="weeklyFortune.category_tips.health" class="category-desc-item">
              <h4>健康</h4>
              <p>{{ weeklyFortune.category_tips.health }}</p>
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

          <div v-if="monthlyFortune.month_mansion || monthlyFortune.lunar_month" class="month-mansion-info">
            <span v-if="monthlyFortune.lunar_month" class="lunar-month">農曆{{ monthlyFortune.lunar_month }}月</span>
            <span v-if="monthlyFortune.month_mansion" class="month-mansion">
              當月宿：<strong>{{ monthlyFortune.month_mansion.name_jp }}</strong>（{{ monthlyFortune.month_mansion.element }}）
            </span>
            <span v-if="monthlyFortune.relation" class="month-relation hint-relation" :class="monthlyFortune.relation.type">
              <ruby v-if="monthlyFortune.relation.reading">{{ monthlyFortune.relation.name }}<rp>(</rp><rt>{{ monthlyFortune.relation.reading }}</rt><rp>)</rp></ruby>
              <template v-else>{{ monthlyFortune.relation.name }}</template>
            </span>
          </div>
          <p v-if="monthlyFortune.relation?.description" class="month-relation-desc">{{ monthlyFortune.relation.description }}</p>

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
            <div class="score-row">
              <span class="score-label">健康</span>
              <div class="score-bar">
                <div class="score-fill" :class="getScoreClass(monthlyFortune.fortune.health)" :style="{ width: monthlyFortune.fortune.health + '%' }"></div>
              </div>
              <span class="score-value">{{ monthlyFortune.fortune.health }}</span>
            </div>
            <div class="score-row">
              <span class="score-label">財運</span>
              <div class="score-bar">
                <div class="score-fill" :class="getScoreClass(monthlyFortune.fortune.wealth)" :style="{ width: monthlyFortune.fortune.wealth + '%' }"></div>
              </div>
              <span class="score-value">{{ monthlyFortune.fortune.wealth }}</span>
            </div>
          </div>

          <div class="score-legend">
            <span class="legend-item"><span class="legend-dot excellent"></span>90+ 大吉</span>
            <span class="legend-item"><span class="legend-dot good"></span>75+ 吉</span>
            <span class="legend-item"><span class="legend-dot fair"></span>60+ 中吉</span>
            <span class="legend-item"><span class="legend-dot caution"></span>45+ 小吉</span>
            <span class="legend-item"><span class="legend-dot warning"></span>&lt;45 注意</span>
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
                          :aria-label="`${formatDate(day.date)} ${day.weekday} 運勢 ${day.score} 分，點擊查看詳情`"
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
          </h3>

          <div v-if="yearlyFortune.kuyou_star" class="kuyou-star-box">
            <div class="kuyou-header">
              <span class="kuyou-name">{{ yearlyFortune.kuyou_star.name }}</span>
              <span class="kuyou-level" :class="getKuyouLevelClass(yearlyFortune.kuyou_star.level)">{{ yearlyFortune.kuyou_star.level }}</span>
              <span class="kuyou-fortune-name">{{ yearlyFortune.kuyou_star.fortune_name }}</span>
            </div>
            <p class="kuyou-age">數え年 {{ yearlyFortune.kuyou_star.kazoe_age }} 歲</p>
            <p class="kuyou-desc">{{ yearlyFortune.kuyou_star.description }}</p>
            <p class="kuyou-buddha">守護佛：{{ yearlyFortune.kuyou_star.buddha }}</p>
            <p class="kuyou-buddha-note">九曜星各自對應的佛菩薩，為今年的守護力量</p>
          </div>

          <div v-if="yearlyFortune.theme" class="theme-box">
            <h4>{{ yearlyFortune.theme.title }}</h4>
            <p class="theme-desc">{{ yearlyFortune.theme.description }}</p>
          </div>

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

          <div class="score-legend">
            <span class="legend-item"><span class="legend-dot excellent"></span>90+ 大吉</span>
            <span class="legend-item"><span class="legend-dot good"></span>75+ 吉</span>
            <span class="legend-item"><span class="legend-dot fair"></span>60+ 中吉</span>
            <span class="legend-item"><span class="legend-dot caution"></span>45+ 小吉</span>
            <span class="legend-item"><span class="legend-dot warning"></span>&lt;45 注意</span>
          </div>

          <div v-if="yearlyFortune.monthly_trend?.length" class="monthly-trend">
            <h4>每月趨勢</h4>
            <div class="trend-list">
              <div
                v-for="m in yearlyFortune.monthly_trend"
                :key="m.month"
                class="trend-item"
              >
                <span class="trend-month">{{ m.month }}月</span>
                <div class="trend-bar">
                  <div class="trend-fill" :class="getScoreClass(m.score)" :style="{ width: m.score + '%' }"></div>
                </div>
                <span class="trend-score" :class="getScoreClass(m.score)">{{ m.score }}</span>
              </div>
            </div>
          </div>

          <div v-if="yearlyFortune.category_descriptions" class="category-descriptions">
            <div v-if="yearlyFortune.category_descriptions.career" class="category-desc-item">
              <h4>事業</h4>
              <p>{{ yearlyFortune.category_descriptions.career }}</p>
            </div>
            <div v-if="yearlyFortune.category_descriptions.love" class="category-desc-item">
              <h4>感情</h4>
              <p>{{ yearlyFortune.category_descriptions.love }}</p>
            </div>
            <div v-if="yearlyFortune.category_descriptions.health" class="category-desc-item">
              <h4>健康</h4>
              <p>{{ yearlyFortune.category_descriptions.health }}</p>
            </div>
            <div v-if="yearlyFortune.category_descriptions.wealth" class="category-desc-item">
              <h4>財運</h4>
              <p>{{ yearlyFortune.category_descriptions.wealth }}</p>
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
  min-height: 44px;
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

.score-fill.excellent { background: var(--stellar); }
.score-fill.good { background: var(--success); }
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

.score-value.excellent { color: var(--stellar); font-weight: 600; }
.score-value.good { color: var(--success); font-weight: 600; }
.score-value.fair { color: var(--info); font-weight: 600; }
.score-value.caution { color: #eab308; font-weight: 600; }
.score-value.warning { color: var(--warning); font-weight: 600; }

.score-group {
  display: flex;
  flex-direction: column;
}

.score-desc {
  margin: 2px 0 var(--space-xs);
  padding-left: calc(48px + var(--space-md));
  font-size: var(--font-xs);
  color: var(--text-secondary);
  line-height: 1.5;
  opacity: 0.85;
}

.score-legend {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  padding: var(--space-xs) 0;
  margin-bottom: var(--space-md);
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--text-secondary);
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 2px;
}

.legend-dot.excellent { background: var(--stellar); }
.legend-dot.good { background: var(--success); }
.legend-dot.fair { background: var(--info); }
.legend-dot.caution { background: #eab308; }
.legend-dot.warning { background: var(--warning); }

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

.special-day-banner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-md);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-md);
  border: 1px solid var(--border);
}

.special-day-banner.kanro {
  background: linear-gradient(135deg, rgba(255, 215, 0, 0.12), rgba(255, 183, 0, 0.08));
  border-color: rgba(255, 183, 0, 0.4);
}

.special-day-banner.kongou {
  background: linear-gradient(135deg, rgba(100, 200, 100, 0.12), rgba(80, 180, 80, 0.08));
  border-color: rgba(80, 180, 80, 0.4);
}

.special-day-banner.rasetsu {
  background: linear-gradient(135deg, rgba(220, 80, 80, 0.12), rgba(200, 60, 60, 0.08));
  border-color: rgba(200, 60, 60, 0.4);
}

.special-day-level {
  font-size: var(--font-xs);
  font-weight: 700;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  white-space: nowrap;
}

.kanro .special-day-level {
  background: rgba(255, 183, 0, 0.25);
  color: #b8860b;
}

.kongou .special-day-level {
  background: rgba(80, 180, 80, 0.25);
  color: #2e7d32;
}

.rasetsu .special-day-level {
  background: rgba(200, 60, 60, 0.25);
  color: #c62828;
}

.special-day-name {
  font-weight: 600;
  font-size: var(--font-base);
}

.special-day-desc {
  width: 100%;
  margin: var(--space-xs) 0 0;
  font-size: var(--font-sm);
  color: var(--text-secondary);
  line-height: 1.5;
}

.special-day-reversed {
  width: 100%;
  margin: var(--space-xs) 0 0;
  font-size: var(--font-xs);
  color: #b8860b;
  font-weight: 600;
}

.special-day-banner.reversed {
  border-style: dashed;
}

.ryouhan-banner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-md);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-md);
  background: linear-gradient(135deg, rgba(128, 0, 128, 0.10), rgba(100, 0, 100, 0.06));
  border: 1px dashed rgba(128, 0, 128, 0.4);
}

.ryouhan-label {
  font-size: var(--font-xs);
  font-weight: 700;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  background: rgba(128, 0, 128, 0.2);
  color: #7b1fa2;
  white-space: nowrap;
}

.ryouhan-desc {
  width: 100%;
  margin: var(--space-xs) 0 0;
  font-size: var(--font-sm);
  color: var(--text-secondary);
  line-height: 1.5;
}

.rokugai-banner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-md);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-md);
  background: linear-gradient(135deg, rgba(180, 0, 0, 0.12), rgba(150, 0, 0, 0.06));
  border: 1px solid rgba(180, 0, 0, 0.5);
}

.rokugai-label {
  font-size: var(--font-xs);
  font-weight: 700;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  background: rgba(180, 0, 0, 0.25);
  color: #b71c1c;
  white-space: nowrap;
}

.rokugai-desc {
  width: 100%;
  margin: var(--space-xs) 0 0;
  font-size: var(--font-sm);
  color: var(--text-secondary);
  line-height: 1.5;
}

.sanki-box {
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-md);
}

.sanki-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
  margin-bottom: var(--space-xs);
}

.sanki-period {
  font-size: var(--font-sm);
  font-weight: 600;
}

.sanki-1 { color: #2196f3; }
.sanki-2 { color: #f44336; }
.sanki-3 { color: #4caf50; }

.sanki-day-type {
  font-size: var(--font-sm);
  font-weight: 600;
  color: var(--text-primary);
}

.sanki-day-desc {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0 0 var(--space-xs);
}

.sanki-period-desc {
  font-size: var(--font-xs);
  color: var(--text-secondary);
  opacity: 0.7;
  line-height: 1.5;
  margin: 0;
}

.sanki-box.dark-week {
  background: linear-gradient(135deg, rgba(180, 0, 0, 0.08), rgba(100, 0, 0, 0.04));
  border-color: rgba(180, 0, 0, 0.3);
}

.dark-week-label {
  font-size: var(--font-xs);
  font-weight: 600;
  color: #c62828;
  padding: 1px 6px;
  background: rgba(200, 60, 60, 0.15);
  border-radius: var(--radius-sm);
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

/* Mansion Hint */
.mansion-hint {
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-md);
}

.mansion-hint h4 {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: var(--font-sm);
  color: var(--text-primary);
  margin: 0 0 var(--space-sm);
}

.hint-relation {
  font-size: var(--font-xs);
  font-weight: 600;
  padding: 2px 8px;
  border-radius: var(--radius-full);
}

.hint-relation.eishin { background: var(--stellar); color: var(--bg-primary); }
.hint-relation.gyotai { background: var(--success); color: var(--bg-primary); }
.hint-relation.mei { background: var(--info); color: var(--bg-primary); }
.hint-relation.yusui { background: var(--text-secondary); color: var(--bg-primary); }
.hint-relation.kisei { background: #eab308; color: var(--bg-primary); }
.hint-relation.ankai { background: var(--warning); color: var(--bg-primary); }

.hint-mansions {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  margin: 0 0 var(--space-sm);
}

.hint-mansions strong {
  color: var(--text-primary);
}

.mansion-hint p {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0 0 var(--space-xs);
}

.mansion-hint p:last-child {
  margin-bottom: 0;
}

.hint-element {
  font-style: italic;
  opacity: 0.85;
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

.kuyou-star-box {
  padding: var(--space-md);
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-md);
}

.kuyou-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

.kuyou-name {
  font-size: var(--font-lg);
  font-weight: 700;
}

.kuyou-level {
  font-size: var(--font-xs);
  font-weight: 700;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
}

.kuyou-level.level-great {
  background: rgba(255, 183, 0, 0.2);
  color: #b8860b;
}

.kuyou-level.level-good {
  background: rgba(80, 180, 80, 0.2);
  color: #2e7d32;
}

.kuyou-level.level-half {
  background: rgba(100, 150, 220, 0.2);
  color: #1565c0;
}

.kuyou-level.level-bad {
  background: rgba(200, 60, 60, 0.2);
  color: #c62828;
}

.kuyou-fortune-name {
  font-size: var(--font-sm);
  color: var(--text-secondary);
}

.kuyou-age {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  margin: var(--space-xs) 0 0;
}

.kuyou-desc {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  line-height: 1.6;
  margin: var(--space-sm) 0 0;
}

.kuyou-buddha {
  font-size: var(--font-xs);
  color: var(--text-secondary);
  margin: var(--space-sm) 0 0;
  font-style: italic;
}

.kuyou-buddha-note {
  font-size: 11px;
  color: var(--text-tertiary, var(--text-secondary));
  margin: 2px 0 0;
  opacity: 0.7;
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

/* Weekly Focus */
.weekly-focus {
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-md);
}

.weekly-focus h4 {
  font-size: var(--font-sm);
  color: var(--accent);
  margin: 0 0 var(--space-sm);
}

.weekly-focus p {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0;
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
  -webkit-overflow-scrolling: touch;
  scrollbar-width: thin;
  mask-image: linear-gradient(to right, transparent, black 8px, black calc(100% - 24px), transparent);
  -webkit-mask-image: linear-gradient(to right, transparent, black 8px, black calc(100% - 24px), transparent);
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

.daily-item.excellent { border-bottom: 2px solid var(--stellar); }
.daily-item.good { border-bottom: 2px solid var(--success); }
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

.week-fill.excellent { background: var(--stellar); }
.week-fill.good { background: var(--success); }
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

.detail-value.excellent { color: var(--stellar); }
.detail-value.good { color: var(--success); }
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

.daily-chip.excellent { border-left: 2px solid var(--stellar); }
.daily-chip.good { border-left: 2px solid var(--success); }
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

/* Monthly Trend */
.monthly-trend {
  margin-bottom: var(--space-md);
}

.monthly-trend h4 {
  font-size: var(--font-sm);
  color: var(--accent);
  margin: 0 0 var(--space-sm);
}

.trend-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.trend-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.trend-month {
  width: 36px;
  font-size: var(--font-xs);
  color: var(--text-secondary);
  text-align: right;
  flex-shrink: 0;
}

.trend-bar {
  flex: 1;
  height: 6px;
  background: var(--bg-elevated);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.trend-fill {
  height: 100%;
  border-radius: var(--radius-sm);
  transition: width 0.5s ease;
}

.trend-fill.excellent { background: var(--stellar); }
.trend-fill.good { background: var(--success); }
.trend-fill.fair { background: var(--info); }
.trend-fill.caution { background: #eab308; }
.trend-fill.warning { background: var(--warning); }

.trend-score {
  width: 28px;
  text-align: right;
  font-size: var(--font-xs);
  font-variant-numeric: tabular-nums;
  flex-shrink: 0;
}

.trend-score.excellent { color: var(--stellar); font-weight: 600; }
.trend-score.good { color: var(--success); font-weight: 600; }
.trend-score.fair { color: var(--info); }
.trend-score.caution { color: #eab308; }
.trend-score.warning { color: var(--warning); }

/* Month Mansion Info */
.month-mansion-info {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
  margin-bottom: var(--space-md);
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  font-size: var(--font-sm);
  color: var(--text-secondary);
}

.month-mansion-info strong {
  color: var(--text-primary);
}

.lunar-month {
  padding: 2px 8px;
  background: rgba(245, 158, 11, 0.1);
  border-radius: var(--radius-sm);
  font-size: var(--font-xs);
  color: var(--accent);
  font-weight: 500;
}

.month-relation-desc {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  margin: 0 0 var(--space-md);
  line-height: 1.6;
}

.opportunities,
.warnings {
  margin-bottom: var(--space-md);
}

.opportunities h4 {
  color: var(--stellar);
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

.category-descriptions {
  margin-bottom: var(--space-md);
}

.category-desc-item {
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-sm);
}

.category-desc-item h4 {
  color: var(--accent);
  font-size: var(--font-sm);
  margin: 0 0 var(--space-xs);
}

.category-desc-item p {
  color: var(--text-secondary);
  font-size: var(--font-sm);
  line-height: 1.6;
  margin: 0;
}

.loading-state {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: var(--space-2xl);
}

@media (max-width: 767px) {
  .fortune-card {
    padding: var(--space-sm);
  }

  .score-desc {
    padding-left: calc(40px + var(--space-sm));
  }

  .score-label {
    width: 40px;
  }

  .lucky-info {
    gap: var(--space-sm);
  }

  .lucky-item {
    min-width: calc(50% - var(--space-sm));
  }

  .daily-item {
    min-width: 48px;
    padding: var(--space-xs);
  }

  .day-score {
    font-size: var(--font-base);
  }

  .weekly-item {
    padding: var(--space-sm);
    gap: var(--space-xs);
  }

  .week-num {
    width: 48px;
    font-size: var(--font-xs);
  }

  .trend-month {
    width: 28px;
  }

  .kuyou-star-box {
    padding: var(--space-sm);
  }
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
