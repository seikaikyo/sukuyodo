<script setup lang="ts">
import { ref, computed } from 'vue'
import { getApiUrl } from '../config/api'
import { generateMultiPersonReport } from '../utils/report-generator'
import type { ReportPerson, ReportEvent } from '../utils/report-generator'
import { useProfile } from '../stores/profile'
import { getLocalDateStr } from '../utils/fortune-helpers'

const { profile, myBirthDate } = useProfile()

// People
const people = ref<ReportPerson[]>([
  { name: '', birthDate: '', role: '' },
  { name: '', birthDate: '', role: '' }
])

// Year range
const currentYear = new Date().getFullYear()
const startYear = ref(currentYear - 2)
const endYear = ref(currentYear + 5)

// Events
const showEvents = ref(false)
const events = ref<ReportEvent[]>([])

// Title
const reportTitle = ref('')

// Progress
const generating = ref(false)
const progressStep = ref('')
const progressCurrent = ref(0)
const progressTotal = ref(0)
const error = ref('')

const canGenerate = computed(() => {
  const validPeople = people.value.filter(p => p.name.trim() && p.birthDate)
  return validPeople.length >= 2 && !generating.value
})

function addPerson() {
  if (people.value.length >= 8) return
  people.value.push({ name: '', birthDate: '', role: '' })
}

function removePerson(index: number) {
  if (people.value.length <= 2) return
  people.value.splice(index, 1)
}

function addEvent() {
  events.value.push({ date: '', label: '', description: '' })
}

function removeEvent(index: number) {
  events.value.splice(index, 1)
}

function importFromProfile() {
  const existing = people.value.filter(p => p.name.trim() && p.birthDate)
  const myDate = myBirthDate.value
  if (myDate && !existing.some(p => p.birthDate === myDate)) {
    people.value.push({ name: '我', birthDate: myDate, role: '' })
  }
  for (const partner of profile.value.partners) {
    if (partner.birthDate && !existing.some(p => p.birthDate === partner.birthDate)) {
      people.value.push({
        name: partner.nickname,
        birthDate: partner.birthDate,
        role: ''
      })
    }
  }
  // Remove empty rows
  people.value = people.value.filter(p => p.name.trim() || p.birthDate)
  if (people.value.length < 2) {
    while (people.value.length < 2) {
      people.value.push({ name: '', birthDate: '', role: '' })
    }
  }
}

async function generate() {
  const validPeople = people.value.filter(p => p.name.trim() && p.birthDate)
  if (validPeople.length < 2) return

  generating.value = true
  error.value = ''
  progressStep.value = ''
  progressCurrent.value = 0
  progressTotal.value = 0

  try {
    const validEvents = showEvents.value
      ? events.value.filter(e => e.date && e.label.trim())
      : undefined

    await generateMultiPersonReport({
      people: validPeople,
      yearRange: [startYear.value, endYear.value],
      events: validEvents?.length ? validEvents : undefined,
      title: reportTitle.value.trim() || undefined,
      apiUrl: getApiUrl(''),
      onProgress: (step, current, total) => {
        progressStep.value = step
        progressCurrent.value = current
        progressTotal.value = total
      }
    })
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '報告產生失敗'
  } finally {
    generating.value = false
  }
}
</script>

<template>
  <div class="report-tab">
    <h2 class="section-title">多人關係分析報告</h2>

    <!-- Title -->
    <div class="form-group">
      <label class="form-label">報告標題（選填）</label>
      <sl-input
        :value="reportTitle"
        placeholder="例：2026 年度關係分析"
        @sl-input="reportTitle = ($event.target as HTMLInputElement).value"
      ></sl-input>
    </div>

    <!-- People -->
    <div class="form-group">
      <div class="form-header">
        <label class="form-label">分析對象（2-8 人）</label>
        <div class="form-header-actions">
          <button
            v-if="myBirthDate || profile.partners.length > 0"
            class="btn-import"
            @click="importFromProfile"
          >匯入收藏</button>
          <button class="btn-add" @click="addPerson" :disabled="people.length >= 8">+ 新增</button>
        </div>
      </div>
      <div class="people-list">
        <div v-for="(p, idx) in people" :key="idx" class="person-row">
          <span class="row-number">{{ idx + 1 }}</span>
          <sl-input
            :value="p.name"
            placeholder="姓名"
            class="input-name"
            @sl-input="p.name = ($event.target as HTMLInputElement).value"
          ></sl-input>
          <sl-input
            type="date"
            :value="p.birthDate"
            :max="getLocalDateStr()"
            class="input-date"
            @sl-input="p.birthDate = ($event.target as HTMLInputElement).value"
          ></sl-input>
          <sl-input
            :value="p.role || ''"
            placeholder="角色（選填）"
            class="input-role"
            @sl-input="p.role = ($event.target as HTMLInputElement).value"
          ></sl-input>
          <button class="btn-remove" @click="removePerson(idx)" :disabled="people.length <= 2" aria-label="移除">
            <sl-icon name="x-lg"></sl-icon>
          </button>
        </div>
      </div>
    </div>

    <!-- Year Range -->
    <div class="form-group">
      <label class="form-label">年份範圍</label>
      <div class="year-range-row">
        <sl-input
          type="number"
          :value="String(startYear)"
          :min="String(currentYear - 10)"
          :max="String(endYear)"
          @sl-input="startYear = parseInt(($event.target as HTMLInputElement).value) || startYear"
        ></sl-input>
        <span class="range-sep">~</span>
        <sl-input
          type="number"
          :value="String(endYear)"
          :min="String(startYear)"
          :max="String(currentYear + 15)"
          @sl-input="endYear = parseInt(($event.target as HTMLInputElement).value) || endYear"
        ></sl-input>
      </div>
    </div>

    <!-- Events (collapsible) -->
    <div class="form-group">
      <button class="btn-toggle" @click="showEvents = !showEvents">
        <sl-icon :name="showEvents ? 'chevron-down' : 'chevron-right'" aria-hidden="true"></sl-icon>
        關鍵事件（選填）
      </button>
      <div v-if="showEvents" class="events-section">
        <div v-for="(evt, idx) in events" :key="idx" class="event-row">
          <sl-input
            type="date"
            :value="evt.date"
            class="input-date"
            @sl-input="evt.date = ($event.target as HTMLInputElement).value"
          ></sl-input>
          <sl-input
            :value="evt.label"
            placeholder="事件名稱"
            class="input-name"
            @sl-input="evt.label = ($event.target as HTMLInputElement).value"
          ></sl-input>
          <sl-input
            :value="evt.description || ''"
            placeholder="說明（選填）"
            class="input-role"
            @sl-input="evt.description = ($event.target as HTMLInputElement).value"
          ></sl-input>
          <button class="btn-remove" @click="removeEvent(idx)" aria-label="移除">
            <sl-icon name="x-lg"></sl-icon>
          </button>
        </div>
        <button class="btn-add" @click="addEvent">+ 新增事件</button>
      </div>
    </div>

    <!-- Generate -->
    <div class="generate-section">
      <button class="btn-generate" :disabled="!canGenerate" @click="generate">
        {{ generating ? '產生中...' : '產生報告' }}
      </button>
      <p class="generate-hint">
        產生 HTML 報告並下載，含相性矩陣、九曜流年、月度明細、勢力結構等分析
      </p>
      <div v-if="generating" class="progress-info">
        <div class="progress-bar">
          <div
            class="progress-fill"
            :style="{ width: progressTotal ? `${(progressCurrent / progressTotal) * 100}%` : '0%' }"
          ></div>
        </div>
        <span class="progress-text">{{ progressStep }} ({{ progressCurrent }}/{{ progressTotal }})</span>
      </div>
      <div v-if="error" class="error-msg">{{ error }}</div>
    </div>
  </div>
</template>

<style scoped>
.report-tab {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.section-title {
  font-size: var(--font-lg);
  color: var(--accent);
  margin: 0;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-header-actions {
  display: flex;
  gap: var(--space-sm);
}

.form-label {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  font-weight: 600;
}

.people-list, .events-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.person-row, .event-row {
  display: flex;
  gap: var(--space-sm);
  align-items: center;
}

.row-number {
  width: 24px;
  text-align: center;
  color: var(--text-secondary);
  font-size: var(--font-sm);
  flex-shrink: 0;
}

.input-name { flex: 2; }
.input-date { flex: 2; }
.input-role { flex: 2; }

.btn-add, .btn-import {
  padding: var(--space-xs) var(--space-md);
  min-height: 36px;
  background: transparent;
  border: 1px dashed var(--accent);
  border-radius: var(--radius-md);
  color: var(--accent);
  font-size: var(--font-sm);
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-import {
  border-style: solid;
}

.btn-add:hover:not(:disabled),
.btn-import:hover {
  background: rgba(245, 158, 11, 0.1);
}

.btn-add:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-remove {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  min-height: 44px;
  min-width: 44px;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  cursor: pointer;
  flex-shrink: 0;
  transition: color 0.2s;
}

.btn-remove:hover:not(:disabled) {
  color: var(--warning);
}

.btn-remove:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.year-range-row {
  display: flex;
  gap: var(--space-sm);
  align-items: center;
  max-width: 300px;
}

.range-sep {
  color: var(--text-secondary);
  font-size: var(--font-lg);
}

.btn-toggle {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  min-height: 36px;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: var(--font-sm);
  cursor: pointer;
  text-align: left;
  transition: color 0.2s, border-color 0.2s;
}

.btn-toggle:hover {
  color: var(--text-primary);
  border-color: var(--accent);
}

.generate-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  align-items: flex-start;
}

.btn-generate {
  padding: var(--space-sm) var(--space-xl);
  min-height: 44px;
  background: var(--accent);
  border: none;
  border-radius: var(--radius-md);
  color: var(--bg-primary);
  font-size: var(--font-base);
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-generate:hover:not(:disabled) {
  background: var(--accent-hover);
}

.btn-generate:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.generate-hint {
  font-size: var(--font-xs);
  color: var(--text-secondary);
  margin: 0;
}

.progress-info {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  width: 100%;
}

.progress-bar {
  width: 100%;
  height: 6px;
  background: var(--bg-elevated);
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--accent);
  border-radius: 3px;
  transition: width 0.3s;
}

.progress-text {
  font-size: var(--font-xs);
  color: var(--text-secondary);
}

.error-msg {
  color: var(--warning);
  font-size: var(--font-sm);
  padding: var(--space-sm);
  background: rgba(239, 68, 68, 0.1);
  border-radius: var(--radius-sm);
}

@media (max-width: 767px) {
  .person-row, .event-row {
    flex-wrap: wrap;
  }

  .input-name, .input-date, .input-role {
    flex-basis: calc(50% - var(--space-sm));
  }

  .row-number {
    display: none;
  }
}
</style>
