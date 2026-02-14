<script setup lang="ts">
import MansionWheel from './MansionWheel.vue'
import type { Mansion, WheelMansion, RelationType, ElementType, Metadata } from '../composables/useSukuyodo'

const props = defineProps<{
  activeTab: 'mansion' | 'wheel' | 'relations' | 'elements' | 'calendar' | 'history'
  mansion: Mansion | null
  mansionElementColor: string
  allMansions: WheelMansion[]
  selectedWheelMansion: WheelMansion | null
  allRelations: RelationType[]
  expandedRelation: string | null
  allElements: ElementType[]
  metadata: Metadata | null
  elementColors: Record<string, string>
}>()

const emit = defineEmits<{
  'update:activeTab': [value: 'mansion' | 'wheel' | 'relations' | 'elements' | 'calendar' | 'history']
  'update:selectedWheelMansion': [value: WheelMansion | null]
  toggleRelation: [type: string]
}>()

function handleWheelSelect(m: WheelMansion) {
  if (props.selectedWheelMansion?.index === m.index) {
    emit('update:selectedWheelMansion', null)
  } else {
    emit('update:selectedWheelMansion', m)
  }
}
</script>

<template>
  <section class="knowledge-tab">
    <div class="sub-tabs scrollable" role="tablist" aria-label="知識類別選擇">
      <button
        class="pill-btn"
        :class="{ active: activeTab === 'mansion' }"
        role="tab"
        :aria-selected="activeTab === 'mansion'"
        aria-controls="panel-knowledge-mansion"
        @click="emit('update:activeTab', 'mansion')"
      >本命宿</button>
      <button
        class="pill-btn"
        :class="{ active: activeTab === 'wheel' }"
        role="tab"
        :aria-selected="activeTab === 'wheel'"
        aria-controls="panel-knowledge-wheel"
        @click="emit('update:activeTab', 'wheel')"
      >二十七宿</button>
      <button
        class="pill-btn"
        :class="{ active: activeTab === 'relations' }"
        role="tab"
        :aria-selected="activeTab === 'relations'"
        aria-controls="panel-knowledge-relations"
        @click="emit('update:activeTab', 'relations')"
      >六種關係</button>
      <button
        class="pill-btn"
        :class="{ active: activeTab === 'elements' }"
        role="tab"
        :aria-selected="activeTab === 'elements'"
        aria-controls="panel-knowledge-elements"
        @click="emit('update:activeTab', 'elements')"
      >七曜</button>
      <button
        class="pill-btn"
        :class="{ active: activeTab === 'calendar' }"
        role="tab"
        :aria-selected="activeTab === 'calendar'"
        aria-controls="panel-knowledge-calendar"
        @click="emit('update:activeTab', 'calendar')"
      >傍通曆</button>
      <button
        class="pill-btn"
        :class="{ active: activeTab === 'history' }"
        role="tab"
        :aria-selected="activeTab === 'history'"
        aria-controls="panel-knowledge-history"
        @click="emit('update:activeTab', 'history')"
      >歷史</button>
    </div>

    <!-- My Mansion -->
    <div v-if="activeTab === 'mansion'" id="panel-knowledge-mansion" class="knowledge-content" role="tabpanel">
      <div class="mansion-info-card">
        <h3>{{ mansion?.name_jp }}（{{ mansion?.reading }}）</h3>
        <p class="mansion-element-text">
          <span class="element-badge" :style="{ background: mansionElementColor }">{{ mansion?.element }}</span>
          元素
        </p>
        <div class="mansion-sections">
          <div class="info-section">
            <h4>性格特質</h4>
            <p>{{ mansion?.personality }}</p>
          </div>
          <div class="info-section">
            <h4>關鍵字</h4>
            <div class="keywords">
              <span v-for="kw in mansion?.keywords" :key="kw" class="keyword">{{ kw }}</span>
            </div>
          </div>
          <div class="info-section">
            <h4>愛情運</h4>
            <p>{{ mansion?.love }}</p>
          </div>
          <div class="info-section">
            <h4>事業運</h4>
            <p>{{ mansion?.career }}</p>
          </div>
          <div class="info-section">
            <h4>健康運</h4>
            <p>{{ mansion?.health }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Wheel -->
    <div v-if="activeTab === 'wheel'" id="panel-knowledge-wheel" class="knowledge-content" role="tabpanel">
      <MansionWheel
        v-if="allMansions.length > 0"
        :mansions="allMansions"
        :selected-index="selectedWheelMansion?.index ?? -1"
        :highlight-index="mansion?.index ?? -1"
        @select="handleWheelSelect"
      />
      <div v-if="selectedWheelMansion" class="wheel-detail">
        <h4>{{ selectedWheelMansion.name_jp }}（{{ selectedWheelMansion.reading }}）</h4>
        <span class="element-badge" :style="{ background: elementColors[selectedWheelMansion.element] }">
          {{ selectedWheelMansion.element }}
        </span>
        <p>{{ selectedWheelMansion.personality }}</p>
      </div>
    </div>

    <!-- Relations -->
    <div v-if="activeTab === 'relations'" id="panel-knowledge-relations" class="knowledge-content" role="tabpanel">
      <div class="relations-list">
        <div
          v-for="rel in allRelations"
          :key="rel.type"
          class="relation-item"
          :class="{ expanded: expandedRelation === rel.type }"
        >
          <button
            class="relation-header"
            :aria-expanded="expandedRelation === rel.type"
            @click="emit('toggleRelation', rel.type)"
          >
            <span class="relation-name">{{ rel.name }}（{{ rel.reading }}）</span>
            <span class="relation-score">{{ rel.score }} 分</span>
            <sl-icon :name="expandedRelation === rel.type ? 'chevron-up' : 'chevron-down'" aria-hidden="true"></sl-icon>
          </button>
          <div v-if="expandedRelation === rel.type" class="relation-body">
            <p>{{ rel.description }}</p>
            <p>{{ rel.detailed }}</p>
            <div v-if="rel.good_for?.length" class="good-for">
              <h5>適合</h5>
              <ul>
                <li v-for="(g, i) in rel.good_for" :key="i">{{ g }}</li>
              </ul>
            </div>
            <div v-if="rel.avoid?.length" class="avoid-for">
              <h5>應避免</h5>
              <ul>
                <li v-for="(a, i) in rel.avoid" :key="i">{{ a }}</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Elements -->
    <div v-if="activeTab === 'elements'" id="panel-knowledge-elements" class="knowledge-content" role="tabpanel">
      <div class="elements-grid">
        <div
          v-for="el in allElements"
          :key="el.name"
          class="element-card"
          :style="{ borderColor: elementColors[el.name] }"
        >
          <div class="element-header" :style="{ background: elementColors[el.name] }">
            <span class="element-name">{{ el.name }}曜</span>
            <span class="element-reading">{{ el.reading }}</span>
          </div>
          <div class="element-body">
            <p class="planet">{{ el.planet }}</p>
            <p class="traits">{{ el.traits }}</p>
            <p class="energy-label">能量屬性：{{ el.energy }}</p>
            <p v-if="el.description" class="element-description">{{ el.description }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Calendar -->
    <div v-if="activeTab === 'calendar'" id="panel-knowledge-calendar" class="knowledge-content" role="tabpanel">
      <div class="calendar-info">
        <h3>月宿傍通曆</h3>
        <p v-if="metadata?.month_mansion_table?.calendar_description">{{ metadata.month_mansion_table.calendar_description }}</p>
        <template v-else>
          <p>宿曜道使用的是「月宿傍通曆」，根據農曆月份和日期來對應二十七宿。</p>
          <p>每個農曆日期對應一個特定的「宿」，這個對應關係是固定的，不會因年份而改變。</p>
        </template>
        <div class="calendar-table" v-if="metadata?.month_mansion_table?.months?.length">
          <table>
            <thead>
              <tr>
                <th>農曆月</th>
                <th>初一起始宿</th>
                <th>讀音</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="m in metadata.month_mansion_table.months" :key="m.month">
                <td>{{ m.name }}</td>
                <td>{{ m.start_mansion }}</td>
                <td>{{ m.reading }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p class="calendar-note">每月初一從起始宿開始，之後每天前進一宿，按二十七宿順序循環。</p>
      </div>
    </div>

    <!-- History -->
    <div v-if="activeTab === 'history'" id="panel-knowledge-history" class="knowledge-content" role="tabpanel">
      <div class="history-info" v-if="metadata">
        <h3>{{ metadata.name }}（{{ metadata.reading }}）</h3>
        <div class="history-meta">
          <div class="meta-row">
            <span class="meta-label">宗派</span>
            <span>{{ metadata.origin }}（{{ metadata.origin_reading }}）</span>
          </div>
          <div class="meta-row">
            <span class="meta-label">傳承者</span>
            <span>{{ metadata.founder }}（{{ metadata.founder_reading }}）</span>
          </div>
          <div class="meta-row">
            <span class="meta-label">典籍</span>
            <span>{{ metadata.scripture }}（{{ metadata.scripture_reading }}）</span>
          </div>
          <div class="meta-row">
            <span class="meta-label">核心方法</span>
            <span>{{ metadata.method }}（{{ metadata.method_reading }}）</span>
          </div>
        </div>
        <div v-if="metadata.history?.length" class="history-sections">
          <div v-for="(entry, i) in metadata.history" :key="i" class="history-item">
            <h4>{{ entry.title }}</h4>
            <p>{{ entry.content }}</p>
          </div>
        </div>
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

.sub-tabs.scrollable {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}

.sub-tabs.scrollable::-webkit-scrollbar {
  display: none;
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

.knowledge-content {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.mansion-info-card {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
}

.mansion-info-card h3 {
  font-size: var(--font-xl);
  color: var(--accent);
  margin: 0 0 var(--space-sm);
  text-wrap: balance;
}

.mansion-element-text {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  color: var(--text-secondary);
  margin: 0 0 var(--space-lg);
}

.element-badge {
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  color: var(--bg-primary);
  font-weight: 600;
}

.mansion-sections {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.info-section h4 {
  font-size: var(--font-sm);
  color: var(--accent);
  margin: 0 0 var(--space-sm);
}

.info-section p {
  color: var(--text-secondary);
  font-size: var(--font-sm);
  line-height: 1.6;
  margin: 0;
}

.keywords {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.keyword {
  padding: var(--space-xs) var(--space-sm);
  background: var(--bg-elevated);
  border-radius: var(--radius-sm);
  font-size: var(--font-xs);
  color: var(--text-secondary);
}

.wheel-detail {
  margin-top: var(--space-lg);
  padding: var(--space-lg);
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  text-align: center;
}

.wheel-detail h4 {
  margin: 0 0 var(--space-sm);
}

.wheel-detail p {
  color: var(--text-secondary);
  margin: var(--space-sm) 0 0;
}

.relations-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.relation-item {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.relation-header {
  display: flex;
  align-items: center;
  width: 100%;
  padding: var(--space-md);
  background: transparent;
  border: none;
  color: var(--text-primary);
  cursor: pointer;
  min-height: 44px;
}

.relation-header:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: -2px;
}

.relation-header .relation-name {
  flex: 1;
  text-align: left;
  font-weight: 600;
}

.relation-header .relation-score {
  color: var(--text-secondary);
  font-size: var(--font-sm);
  margin-right: var(--space-sm);
  font-variant-numeric: tabular-nums;
}

.relation-body {
  padding: var(--space-md);
  border-top: 1px solid var(--border);
  background: var(--bg-elevated);
}

.relation-body p {
  color: var(--text-secondary);
  font-size: var(--font-sm);
  line-height: 1.6;
  margin: 0 0 var(--space-sm);
}

.good-for h5,
.avoid-for h5 {
  font-size: var(--font-sm);
  margin: var(--space-md) 0 var(--space-xs);
}

.good-for h5 { color: var(--success); }
.avoid-for h5 { color: var(--warning); }

.good-for ul,
.avoid-for ul {
  margin: 0;
  padding-left: var(--space-lg);
}

.good-for li,
.avoid-for li {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  margin-bottom: var(--space-xs);
}

.elements-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--space-md);
}

.element-card {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.element-header {
  padding: var(--space-sm) var(--space-md);
  color: var(--bg-primary);
}

.element-name {
  font-weight: 600;
  margin-right: var(--space-sm);
}

.element-reading {
  font-size: var(--font-sm);
  opacity: 0.8;
}

.element-body {
  padding: var(--space-md);
}

.element-body .planet {
  font-weight: 600;
  margin: 0 0 var(--space-xs);
}

.element-body .traits,
.element-body .energy-label {
  color: var(--text-secondary);
  font-size: var(--font-sm);
  margin: 0 0 var(--space-xs);
}

.element-body .element-description {
  color: var(--text-secondary);
  font-size: var(--font-sm);
  line-height: 1.6;
  margin: var(--space-sm) 0 0;
  border-top: 1px solid var(--border);
  padding-top: var(--space-sm);
}

.calendar-info,
.history-info {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
}

.calendar-info h3,
.history-info h3 {
  color: var(--accent);
  margin: 0 0 var(--space-md);
  text-wrap: balance;
}

.calendar-info p,
.history-info p {
  color: var(--text-secondary);
  font-size: var(--font-sm);
  line-height: 1.6;
  margin: 0 0 var(--space-md);
}

.calendar-table {
  overflow-x: auto;
}

.calendar-table table {
  width: 100%;
  border-collapse: collapse;
}

.calendar-table th,
.calendar-table td {
  padding: var(--space-sm);
  border: 1px solid var(--border);
  text-align: center;
  font-size: var(--font-sm);
}

.calendar-table th {
  background: var(--bg-elevated);
  color: var(--text-secondary);
}

.history-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  margin-bottom: var(--space-lg);
  padding-bottom: var(--space-lg);
  border-bottom: 1px solid var(--border);
}

.meta-row {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: var(--font-sm);
  color: var(--text-secondary);
}

.meta-label {
  background: var(--bg-elevated);
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
}

.history-sections {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.history-item h4 {
  font-size: var(--font-sm);
  color: var(--accent);
  margin: 0 0 var(--space-xs);
}

.history-item p {
  margin: 0;
  line-height: 1.6;
}

.calendar-note {
  font-size: var(--font-xs);
  color: var(--text-tertiary, var(--text-secondary));
  font-style: italic;
  margin-top: var(--space-sm);
}

@media (max-width: 767px) {
  .elements-grid {
    grid-template-columns: 1fr;
  }
}

@media (prefers-reduced-motion: reduce) {
  .knowledge-content {
    animation: none;
  }
}
</style>
