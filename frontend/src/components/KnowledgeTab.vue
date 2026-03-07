<script setup lang="ts">
import { ref, computed } from 'vue'
import MansionWheel from './MansionWheel.vue'
import type { Mansion, WheelMansion, RelationType, ElementType, Metadata } from '../composables/useSukuyodo'

type KnowledgeActiveTab = 'mansion' | 'wheel' | 'relations' | 'elements' | 'nature-types' | 'special-days' | 'kuyou' | 'ryouhan' | 'sanki' | 'calendar' | 'history'

const props = defineProps<{
  activeTab: KnowledgeActiveTab
  mansion: Mansion | null
  mansionElementColor: string
  allMansions: WheelMansion[]
  selectedWheelMansion: WheelMansion | null
  allRelations: RelationType[]
  allElements: ElementType[]
  metadata: Metadata | null
  elementColors: Record<string, string>
}>()

const emit = defineEmits<{
  'update:activeTab': [value: KnowledgeActiveTab]
  'update:selectedWheelMansion': [value: WheelMansion | null]
}>()

// 全覽模式
const showRelationOverview = ref(false)

// 選中宿的關係資訊
interface RelationInfo {
  type: string
  name: string
  distance: number
  distanceCategory: 'near' | 'mid' | 'far'
}
const selectedRelation = ref<{ mansion: WheelMansion, relation: RelationInfo } | null>(null)
const focusedRelationType = ref<string | null>(null)

function handleRelationDetail(data: { mansion: WheelMansion, relation: RelationInfo } | null) {
  selectedRelation.value = data
}

// 關係距離表（前端常數，與 MansionWheel 一致）
const RELATION_DISTANCES: Record<string, number[]> = {
  eishin: [1, 8, 10, 17, 19, 26],
  yusui: [2, 7, 11, 16, 20, 25],
  ankai: [3, 6, 12, 15, 21, 24],
  kisei: [4, 5, 13, 14, 22, 23],
  mei: [0],
  gyotai: [9, 18],
}

const RELATION_NAMES: Record<string, string> = {
  eishin: '栄親',
  yusui: '友衰',
  ankai: '安壊',
  kisei: '危成',
  mei: '命',
  gyotai: '業胎',
}

const RELATION_COLORS_HEX: Record<string, string> = {
  eishin: '#B8860B',
  gyotai: '#5A7FA5',
  mei: '#A08050',
  yusui: '#7B9CC5',
  kisei: '#9B7B1C',
  ankai: '#C53030',
}

const DISTANCE_CATEGORY_LABELS: Record<string, string> = {
  near: '近距離',
  mid: '中距離',
  far: '遠距離',
}

// 全覽模式統計
const overviewStats = computed(() => {
  if (props.mansion?.index === undefined) return []
  const baseIdx = props.mansion.index
  const stats: Array<{ type: string, name: string, color: string, mansions: Array<{ name: string, distance: number }> }> = []

  for (const [type, distances] of Object.entries(RELATION_DISTANCES)) {
    const mansions: Array<{ name: string, distance: number }> = []
    for (const d of distances) {
      const idx = (baseIdx + d) % 27
      const m = props.allMansions[idx]
      if (m) mansions.push({ name: m.name_zh, distance: d })
    }
    stats.push({
      type,
      name: RELATION_NAMES[type] || type,
      color: RELATION_COLORS_HEX[type] || '#666',
      mansions,
    })
  }
  return stats
})

// 選中宿的五行互動描述
const elementInteraction = computed(() => {
  if (!selectedRelation.value || !props.mansion) return null
  const myEl = props.mansion.element
  const theirEl = selectedRelation.value.mansion.element
  if (myEl === theirEl) return { label: '同元素', desc: `兩宿同屬${myEl}，能量共振` }
  const generating: Record<string, string> = { '木': '火', '火': '土', '土': '金', '金': '水', '水': '木' }
  const specialGen: Record<string, string> = { '日': '火', '月': '水' }
  if (generating[myEl] === theirEl || specialGen[myEl] === theirEl) return { label: '相生', desc: `${myEl}生${theirEl}，有助益關係` }
  if (generating[theirEl] === myEl || specialGen[theirEl] === myEl) return { label: '被生', desc: `${theirEl}生${myEl}，受惠關係` }
  const overcoming: Record<string, string> = { '木': '土', '火': '金', '土': '水', '金': '木', '水': '火' }
  if (overcoming[myEl] === theirEl) return { label: '相剋', desc: `${myEl}剋${theirEl}，制約關係` }
  if (overcoming[theirEl] === myEl) return { label: '被剋', desc: `${theirEl}剋${myEl}，受制關係` }
  return null
})

// 從 allRelations 取出對應的關係描述
const matchedRelationDetail = computed(() => {
  if (!selectedRelation.value) return null
  return props.allRelations.find(r => r.type === selectedRelation.value!.relation.type) || null
})

// 六種關係手風琴
const expandedRelation = ref<string | null>(null)

function toggleRelation(type: string) {
  expandedRelation.value = expandedRelation.value === type ? null : type
}

const tabGroups = [
  {
    label: '基礎',
    tabs: [
      { key: 'mansion' as KnowledgeActiveTab, name: '本命宿' },
      { key: 'wheel' as KnowledgeActiveTab, name: '二十七宿' },
      { key: 'relations' as KnowledgeActiveTab, name: '六種關係' },
      { key: 'elements' as KnowledgeActiveTab, name: '五行七曜' },
      { key: 'nature-types' as KnowledgeActiveTab, name: '七科分宿' }
    ]
  },
  {
    label: '曆法',
    tabs: [
      { key: 'special-days' as KnowledgeActiveTab, name: '特殊日' },
      { key: 'kuyou' as KnowledgeActiveTab, name: '九曜' },
      { key: 'ryouhan' as KnowledgeActiveTab, name: '凌犯逆轉' },
      { key: 'sanki' as KnowledgeActiveTab, name: '三九秘曆' },
      { key: 'calendar' as KnowledgeActiveTab, name: '傍通曆' }
    ]
  },
  {
    label: '背景',
    tabs: [
      { key: 'history' as KnowledgeActiveTab, name: '歷史' }
    ]
  }
]

function handleWheelSelect(m: WheelMansion) {
  if (props.selectedWheelMansion?.index === m.index) {
    emit('update:selectedWheelMansion', null)
  } else {
    emit('update:selectedWheelMansion', m)
  }
}

function toggleOverview() {
  showRelationOverview.value = !showRelationOverview.value
  if (!showRelationOverview.value) focusedRelationType.value = null
}

function setFocusedRelation(type: string) {
  focusedRelationType.value = focusedRelationType.value === type ? null : type
}

const natureTypeColors: Record<string, string> = {
  '安住宿': '#6B8E6B',
  '和善宿': '#7BA7C9',
  '急速宿': '#C4A052',
  '悪害宿': '#C96B5B',
  '猛悪宿': '#9B5B7A',
  '軽燥宿': '#6BB3A0',
  '剛柔宿': '#8B7D6B'
}

function getKuyouRowClass(level?: string) {
  const classMap: Record<string, string> = {
    '大吉': 'kuyou-row-great',
    '吉': 'kuyou-row-good',
    '半吉': 'kuyou-row-half',
    '大凶': 'kuyou-row-bad'
  }
  return (level && classMap[level]) || ''
}

const TAB_INTROS: Record<string, string> = {
  relations: '27宿間的位置關係分為六種，距離不同，吉凶各異。',
  elements: '每宿歸屬七曜之一，七曜對應五行，相生相剋影響相性加成。',
  'nature-types': '27宿按性質分為七科，反映行動適性與處事風格。',
  'special-days': '甘露日、金剛峯日、羅刹日 — 由當日宿與曜日組合決定。',
  kuyou: '九星按數え年循環，每年主星不同，影響整年運勢基調。',
  ryouhan: '特定月份本命宿受凌犯，吉凶逆轉，全面影響運勢判定。',
  sanki: '以本命宿為起點，27日一週期分三段，含暗黒の一週間。',
  calendar: '農曆每月初一對應固定起始宿，逐日推進，27日一循環。',
}
</script>

<template>
  <section class="knowledge-tab">
    <div class="sub-tabs-grouped" role="tablist" aria-label="知識類別選擇">
      <div v-for="group in tabGroups" :key="group.label" class="tab-group">
        <span class="tab-group-label">{{ group.label }}</span>
        <div class="tab-group-pills">
          <button
            v-for="tab in group.tabs"
            :key="tab.key"
            class="pill-btn"
            :class="{ active: activeTab === tab.key }"
            role="tab"
            :aria-selected="activeTab === tab.key"
            :aria-controls="`panel-knowledge-${tab.key}`"
            @click="emit('update:activeTab', tab.key)"
          >{{ tab.name }}</button>
        </div>
      </div>
    </div>

    <p v-if="TAB_INTROS[activeTab]" class="tab-intro">{{ TAB_INTROS[activeTab] }}</p>

    <!-- My Mansion -->
    <div v-if="activeTab === 'mansion'" id="panel-knowledge-mansion" class="knowledge-content" role="tabpanel">
      <div class="mansion-info-card">
        <h3>{{ mansion?.name_jp }}（{{ mansion?.reading }}）</h3>
        <p class="mansion-element-text">
          <span class="element-badge term-link" :style="{ background: mansionElementColor }" @click="emit('update:activeTab', 'elements')">{{ mansion?.element }}</span>
          <span v-if="mansion?.nature_type" class="nature-badge term-link" @click="emit('update:activeTab', 'nature-types')">{{ mansion.nature_type }}</span>
        </p>
        <div class="mansion-sections">
          <div class="info-section">
            <h4>性格特質</h4>
            <div v-if="mansion?.personality_classic" class="classic-quote">
              {{ mansion.personality_classic }}
              <div v-if="mansion?.classic_source" class="classic-source">
                — {{ mansion.classic_source }}
              </div>
            </div>
            <div v-if="mansion?.personality_ja" class="ja-text">
              {{ mansion.personality_ja }}
            </div>
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
            <div v-if="mansion?.love_classic" class="classic-quote">{{ mansion.love_classic }}</div>
            <div v-if="mansion?.love_ja" class="ja-text">{{ mansion.love_ja }}</div>
            <p>{{ mansion?.love }}</p>
          </div>
          <div class="info-section">
            <h4>事業運</h4>
            <div v-if="mansion?.career_classic" class="classic-quote">{{ mansion.career_classic }}</div>
            <div v-if="mansion?.career_ja" class="ja-text">{{ mansion.career_ja }}</div>
            <p>{{ mansion?.career }}</p>
          </div>
          <div class="info-section">
            <h4>健康運</h4>
            <div v-if="mansion?.health_classic" class="classic-quote">{{ mansion.health_classic }}</div>
            <div v-if="mansion?.health_ja" class="ja-text">{{ mansion.health_ja }}</div>
            <p>{{ mansion?.health }}</p>
          </div>
          <div v-if="mansion?.life_stages" class="info-section">
            <h4>人生階段</h4>
            <div class="life-stages">
              <div class="stage-item">
                <span class="stage-label">20 代</span>
                <div v-if="mansion.life_stages_classic?.twenties" class="classic-quote stage-quote">{{ mansion.life_stages_classic.twenties }}</div>
                <div v-if="mansion.life_stages_ja?.twenties" class="ja-text stage-quote">{{ mansion.life_stages_ja.twenties }}</div>
                <p>{{ mansion.life_stages.twenties }}</p>
              </div>
              <div class="stage-item">
                <span class="stage-label">30 代</span>
                <div v-if="mansion.life_stages_classic?.thirties" class="classic-quote stage-quote">{{ mansion.life_stages_classic.thirties }}</div>
                <div v-if="mansion.life_stages_ja?.thirties" class="ja-text stage-quote">{{ mansion.life_stages_ja.thirties }}</div>
                <p>{{ mansion.life_stages.thirties }}</p>
              </div>
              <div class="stage-item">
                <span class="stage-label">40 代</span>
                <div v-if="mansion.life_stages_classic?.forties" class="classic-quote stage-quote">{{ mansion.life_stages_classic.forties }}</div>
                <div v-if="mansion.life_stages_ja?.forties" class="ja-text stage-quote">{{ mansion.life_stages_ja.forties }}</div>
                <p>{{ mansion.life_stages.forties }}</p>
              </div>
              <div class="stage-item">
                <span class="stage-label">50 代+</span>
                <div v-if="mansion.life_stages_classic?.fifties_plus" class="classic-quote stage-quote">{{ mansion.life_stages_classic.fifties_plus }}</div>
                <div v-if="mansion.life_stages_ja?.fifties_plus" class="ja-text stage-quote">{{ mansion.life_stages_ja.fifties_plus }}</div>
                <p>{{ mansion.life_stages.fifties_plus }}</p>
              </div>
            </div>
          </div>
          <div v-if="mansion?.seasonal" class="info-section">
            <h4>四季能量</h4>
            <p>{{ mansion.seasonal }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Wheel -->
    <div v-if="activeTab === 'wheel'" id="panel-knowledge-wheel" class="knowledge-content" role="tabpanel">
      <!-- 全覽切換 -->
      <div v-if="mansion" class="wheel-controls">
        <button
          class="pill-btn"
          :class="{ active: showRelationOverview }"
          @click="toggleOverview"
        >{{ showRelationOverview ? '關係全覽 ON' : '關係全覽' }}</button>
      </div>

      <MansionWheel
        v-if="allMansions.length > 0"
        :mansions="allMansions"
        :selected-index="selectedWheelMansion?.index ?? -1"
        :highlight-index="mansion?.index ?? -1"
        :show-relation-overview="showRelationOverview"
        :focused-relation-type="focusedRelationType"
        @select="handleWheelSelect"
        @relation-detail="handleRelationDetail"
        @update:focused-relation-type="focusedRelationType = $event"
      />

      <!-- 關係詳情面板（選中單一宿時） -->
      <div v-if="selectedRelation && !showRelationOverview" class="wheel-detail relation-detail-panel">
        <div class="relation-detail-header">
          <h4>{{ selectedRelation.mansion.name_jp }}（{{ selectedRelation.mansion.reading }}）</h4>
          <span class="element-badge" :style="{ background: elementColors[selectedRelation.mansion.element] }">
            {{ selectedRelation.mansion.element }}
          </span>
        </div>
        <div class="relation-type-row">
          <span class="relation-color-dot" :style="{ background: RELATION_COLORS_HEX[selectedRelation.relation.type] }"></span>
          <span class="relation-type-name">{{ selectedRelation.relation.name }}</span>
          <span class="relation-distance-tag">{{ DISTANCE_CATEGORY_LABELS[selectedRelation.relation.distanceCategory] }}</span>
          <span class="relation-distance-num">距離 {{ selectedRelation.relation.distance }}</span>
        </div>
        <p v-if="matchedRelationDetail">{{ matchedRelationDetail.description }}</p>
        <div v-if="elementInteraction" class="element-interaction">
          <span class="interaction-label">{{ elementInteraction.label }}</span>
          <span>{{ elementInteraction.desc }}</span>
        </div>
      </div>

      <!-- 全覽面板 -->
      <div v-else-if="showRelationOverview && mansion" class="wheel-detail overview-panel">
        <h4>{{ mansion.name_jp }} 的關係分佈</h4>
        <p class="overview-intro">以本命宿為中心，27宿分佈六種關係。點擊篩選特定關係。</p>
        <div class="overview-grid">
          <div v-for="stat in overviewStats" :key="stat.type" class="overview-item">
            <div
              class="overview-item-header"
              :class="{ active: focusedRelationType === stat.type }"
              :style="focusedRelationType === stat.type ? { borderLeftColor: stat.color } : undefined"
              @click="setFocusedRelation(stat.type)"
            >
              <span class="relation-color-dot" :style="{ background: stat.color }"></span>
              <span class="overview-type-name">{{ stat.name }}</span>
              <span class="overview-count">{{ stat.mansions.length }} 宿</span>
            </div>
            <div class="overview-mansions">
              <span
                v-for="m in stat.mansions"
                :key="m.distance"
                class="overview-mansion-tag"
                @click.stop="allMansions[(mansion!.index + m.distance) % 27] && handleWheelSelect(allMansions[(mansion!.index + m.distance) % 27]!)"
              >{{ m.name }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 預設面板（無選擇時） -->
      <div v-else-if="selectedWheelMansion && !selectedRelation" class="wheel-detail">
        <h4>{{ selectedWheelMansion.name_jp }}（{{ selectedWheelMansion.reading }}）</h4>
        <span class="element-badge term-link" :style="{ background: elementColors[selectedWheelMansion.element] }" @click="emit('update:activeTab', 'elements')">
          {{ selectedWheelMansion.element }}
        </span>
        <p>{{ selectedWheelMansion.personality }}</p>
      </div>

      <!-- 輪盤視覺指南（預設狀態） -->
      <div v-else class="wheel-guide">
        <div class="guide-item" @click="emit('update:activeTab', 'elements')">
          <div class="guide-dots">
            <span v-for="c in ['#4A9B5A','#C4A052','#8B7355','#E89B3C','#7CB3D9','#E85D4C','#4A7A90']"
              :key="c" class="guide-dot" :style="{ background: c }"></span>
          </div>
          <div class="guide-text">
            <strong>五行元素</strong>
            <span>底色代表宿的元素屬性</span>
          </div>
        </div>
        <div class="guide-item" @click="emit('update:activeTab', 'elements')">
          <div class="guide-dots bar">
            <span v-for="c in ['#E89B3C','#7CB3D9','#E85D4C','#4A7A90','#4A9B5A','#C4A052','#8B7355']"
              :key="c" class="guide-bar" :style="{ background: c }"></span>
          </div>
          <div class="guide-text">
            <strong>七曜環</strong>
            <span>外圈環帶，27宿依七曜循環歸屬</span>
          </div>
        </div>
        <div class="guide-item" @click="emit('update:activeTab', 'sanki')">
          <div class="guide-dots bar">
            <span class="guide-bar" style="background: var(--kanro-color, #C4A052)"></span>
            <span class="guide-bar" style="background: var(--rasetsu-color, #E85D4C)"></span>
            <span class="guide-bar" style="background: #5C8FA8"></span>
          </div>
          <div class="guide-text">
            <strong>三期週期</strong>
            <span>最外弧形，依曜日判定甘露/羅刹/中性</span>
          </div>
        </div>
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
            :aria-controls="`relation-body-${rel.type}`"
            @click="toggleRelation(rel.type)"
          >
            <span class="relation-name">{{ rel.name }}（{{ rel.reading }}）</span>
            <span class="relation-score">{{ rel.score }} 分</span>
            <span class="relation-toggle" aria-hidden="true">{{ expandedRelation === rel.type ? '▲' : '▼' }}</span>
          </button>
          <div v-if="expandedRelation === rel.type" :id="`relation-body-${rel.type}`" class="relation-body" role="region">
            <div v-if="rel.description_classic" class="classic-quote">
              {{ rel.description_classic }}
            </div>
            <div v-if="rel.description_ja" class="ja-text">
              {{ rel.description_ja }}
            </div>
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
          :class="{ 'my-element': mansion?.element === el.name }"
          :style="{ borderColor: elementColors[el.name] }"
        >
          <div class="element-header" :style="{ background: elementColors[el.name] }">
            <span class="element-name">{{ el.name }}曜</span>
            <span class="element-reading">{{ el.reading }}</span>
            <span v-if="mansion?.element === el.name" class="my-element-tag">你的元素</span>
          </div>
          <div class="element-body">
            <p class="planet">{{ el.planet }}</p>
            <p class="traits">{{ el.traits }}</p>
            <p class="energy-label">能量屬性：{{ el.energy }}</p>
            <p v-if="el.description" class="element-description">{{ el.description }}</p>
            <p v-if="el.detailed_traits" class="element-extra">{{ el.detailed_traits }}</p>
            <p v-if="el.interactions" class="element-extra">{{ el.interactions }}</p>
            <p v-if="el.life_advice" class="element-extra element-advice">{{ el.life_advice }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Nature Types (七科分宿) -->
    <div v-if="activeTab === 'nature-types'" id="panel-knowledge-nature-types" class="knowledge-content" role="tabpanel">
      <div class="calendar-info" v-if="metadata?.nature_types_knowledge">
        <h3>{{ metadata.nature_types_knowledge.title }}</h3>
        <div class="history-sections">
          <div v-for="(section, i) in metadata.nature_types_knowledge.sections" :key="'nt-' + i" class="history-item">
            <h4>{{ section.title }}</h4>
            <p>{{ section.content }}</p>
          </div>
        </div>
      </div>
      <div class="nature-types-grid" v-if="metadata?.nature_types_knowledge?.nature_types_table">
        <div
          v-for="nt in metadata.nature_types_knowledge.nature_types_table.types"
          :key="nt.name"
          class="element-card"
          :class="{ 'my-element': mansion?.nature_type === nt.name }"
          :style="{ borderColor: natureTypeColors[nt.name] }"
        >
          <div class="element-header" :style="{ background: natureTypeColors[nt.name] }">
            <span class="element-name">{{ nt.name }}</span>
            <span class="element-reading">{{ nt.reading }}</span>
            <span v-if="mansion?.nature_type === nt.name" class="my-element-tag">你的分類</span>
          </div>
          <div class="element-body">
            <p class="planet">{{ nt.sanskrit }}</p>
            <p class="traits">所屬宿：{{ nt.mansions.join('、') }}</p>
            <p class="element-description">{{ nt.description }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Special Days -->
    <div v-if="activeTab === 'special-days'" id="panel-knowledge-special-days" class="knowledge-content" role="tabpanel">
      <div class="calendar-info" v-if="metadata?.special_days_knowledge">
        <h3>{{ metadata.special_days_knowledge.title }}</h3>
        <div class="history-sections">
          <div v-for="(section, i) in metadata.special_days_knowledge.sections" :key="'sd-' + i" class="history-item">
            <h4>{{ section.title }}</h4>
            <div v-if="section.content_classic" class="classic-quote">{{ section.content_classic }}</div>
            <div v-if="section.content_ja" class="ja-text">{{ section.content_ja }}</div>
            <p>{{ section.content }}</p>
          </div>
        </div>
        <div v-if="metadata.special_days_knowledge.day_map_table" class="knowledge-table-section">
          <h4 class="table-subtitle">{{ metadata.special_days_knowledge.day_map_table.description }}</h4>
          <div class="calendar-table">
            <table>
              <thead>
                <tr>
                  <th v-for="h in metadata.special_days_knowledge.day_map_table.headers" :key="h">{{ h }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in metadata.special_days_knowledge.day_map_table.rows" :key="'sdrow-' + i">
                  <td v-for="(cell, j) in row" :key="'sdcell-' + j" :class="{ 'cell-kanro': j === 1, 'cell-kongou': j === 2, 'cell-rasetsu': j === 3 }">{{ cell }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div v-if="metadata.special_days_knowledge.source" class="source-citation">{{ metadata.special_days_knowledge.source }}</div>
      </div>
    </div>

    <!-- Kuyou -->
    <div v-if="activeTab === 'kuyou'" id="panel-knowledge-kuyou" class="knowledge-content" role="tabpanel">
      <div class="calendar-info" v-if="metadata?.kuyou_knowledge">
        <h3>{{ metadata.kuyou_knowledge.title }}</h3>
        <div class="history-sections">
          <div v-for="(section, i) in metadata.kuyou_knowledge.sections" :key="'ky-' + i" class="history-item">
            <h4>{{ section.title }}</h4>
            <div v-if="section.content_classic" class="classic-quote">{{ section.content_classic }}</div>
            <div v-if="section.content_ja" class="ja-text">{{ section.content_ja }}</div>
            <p>{{ section.content }}</p>
          </div>
        </div>
        <div v-if="metadata.kuyou_knowledge.stars_table" class="knowledge-table-section">
          <h4 class="table-subtitle">{{ metadata.kuyou_knowledge.stars_table.description }}</h4>
          <div class="calendar-table">
            <table>
              <thead>
                <tr>
                  <th v-for="h in metadata.kuyou_knowledge.stars_table.headers" :key="h">{{ h }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in metadata.kuyou_knowledge.stars_table.rows" :key="'kyrow-' + i"
                  :class="getKuyouRowClass(row[2])">
                  <td v-for="(cell, j) in row" :key="'kycell-' + j">{{ cell }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- Ryouhan -->
    <div v-if="activeTab === 'ryouhan'" id="panel-knowledge-ryouhan" class="knowledge-content" role="tabpanel">
      <div class="calendar-info" v-if="metadata?.ryouhan_knowledge">
        <h3>{{ metadata.ryouhan_knowledge.title }}</h3>
        <div class="history-sections">
          <div v-for="(section, i) in metadata.ryouhan_knowledge.sections" :key="'rh-' + i" class="history-item">
            <h4>{{ section.title }}</h4>
            <div v-if="section.content_classic" class="classic-quote">{{ section.content_classic }}</div>
            <div v-if="section.content_ja" class="ja-text">{{ section.content_ja }}</div>
            <p>{{ section.content }}</p>
          </div>
        </div>
        <div v-if="metadata.ryouhan_knowledge.ryouhan_table" class="knowledge-table-section">
          <h4 class="table-subtitle">{{ metadata.ryouhan_knowledge.ryouhan_table.description }}</h4>
          <div class="calendar-table">
            <table>
              <thead>
                <tr>
                  <th v-for="h in metadata.ryouhan_knowledge.ryouhan_table.headers" :key="h">{{ h }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in metadata.ryouhan_knowledge.ryouhan_table.rows" :key="'rhrow-' + i">
                  <td v-for="(cell, j) in row" :key="'rhcell-' + j">{{ cell }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div v-if="metadata.ryouhan_knowledge.source" class="source-citation">{{ metadata.ryouhan_knowledge.source }}</div>
      </div>
    </div>

    <!-- Sanki -->
    <div v-if="activeTab === 'sanki'" id="panel-knowledge-sanki" class="knowledge-content" role="tabpanel">
      <div class="calendar-info" v-if="metadata?.sanki_knowledge">
        <h3>{{ metadata.sanki_knowledge.title }}</h3>
        <div class="history-sections">
          <div v-for="(section, i) in metadata.sanki_knowledge.sections" :key="'sk-' + i" class="history-item">
            <h4>{{ section.title }}</h4>
            <div v-if="section.content_classic" class="classic-quote">{{ section.content_classic }}</div>
            <div v-if="section.content_ja" class="ja-text">{{ section.content_ja }}</div>
            <p>{{ section.content }}</p>
          </div>
        </div>
        <div v-if="metadata.sanki_knowledge.source" class="source-citation">{{ metadata.sanki_knowledge.source }}</div>
      </div>
    </div>

    <!-- Calendar -->
    <div v-if="activeTab === 'calendar'" id="panel-knowledge-calendar" class="knowledge-content" role="tabpanel">
      <div class="calendar-info">
        <h3>月宿傍通曆</h3>
        <div v-if="metadata?.month_mansion_table?.source_classic" class="classic-quote">
          {{ metadata.month_mansion_table.source_classic }}
          <div class="classic-source">{{ metadata.month_mansion_table.source_ref }}</div>
        </div>
        <div v-if="metadata?.month_mansion_table?.source_ja" class="ja-text">{{ metadata.month_mansion_table.source_ja }}</div>
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
        <div v-if="metadata.key_concepts?.length" class="history-sections">
          <h3 class="section-subtitle">核心概念</h3>
          <div v-for="(concept, i) in metadata.key_concepts" :key="'kc-' + i" class="history-item">
            <h4>{{ concept.title }}</h4>
            <div v-if="concept.content_classic" class="classic-quote">{{ concept.content_classic }}</div>
            <div v-if="concept.content_ja" class="ja-text">{{ concept.content_ja }}</div>
            <p>{{ concept.content }}</p>
            <div v-if="concept.source" class="source-citation">{{ concept.source }}</div>
          </div>
        </div>
        <div v-if="metadata.practical_guide?.length" class="history-sections">
          <h3 class="section-subtitle">實用指南</h3>
          <div v-for="(guide, i) in metadata.practical_guide" :key="'pg-' + i" class="history-item">
            <h4>{{ guide.title }}</h4>
            <p>{{ guide.content }}</p>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.sub-tabs-grouped {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  margin-bottom: var(--space-lg);
}

.tab-group {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.tab-group-label {
  font-size: var(--font-xs);
  color: var(--text-secondary);
  min-width: 36px;
  flex-shrink: 0;
  opacity: 0.7;
}

.tab-group-pills {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.knowledge-content {
  animation: fadeIn 0.3s ease;
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
  color: var(--text-on-accent);
  font-weight: 600;
}

.nature-badge {
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  background: var(--text-muted);
  color: var(--text-on-accent);
  font-size: var(--font-xs);
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

.wheel-controls {
  display: flex;
  justify-content: flex-end;
  margin-bottom: var(--space-sm);
}

.wheel-detail h4 {
  margin: 0 0 var(--space-sm);
}

.wheel-detail p {
  color: var(--text-secondary);
  margin: var(--space-sm) 0 0;
  font-size: var(--font-sm);
  line-height: 1.6;
}

.relation-detail-panel .relation-detail-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
}

.relation-detail-panel .relation-detail-header h4 {
  margin: 0;
}

.relation-type-row {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
  margin-bottom: var(--space-sm);
}

.relation-color-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}

.relation-type-name {
  font-weight: 600;
  color: var(--text-primary);
}

.relation-distance-tag {
  font-size: var(--font-xs);
  padding: 2px 8px;
  background: var(--bg-elevated);
  border-radius: var(--radius-full);
  color: var(--text-secondary);
}

.relation-distance-num {
  font-size: var(--font-xs);
  color: var(--text-muted, var(--text-secondary));
  font-variant-numeric: tabular-nums;
}

.element-interaction {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-top: var(--space-sm);
  padding: var(--space-sm);
  background: var(--bg-elevated);
  border-radius: var(--radius-sm);
  font-size: var(--font-sm);
  color: var(--text-secondary);
}

.interaction-label {
  font-weight: 600;
  color: var(--accent);
  white-space: nowrap;
}

.overview-panel h4 {
  color: var(--accent);
}

.overview-grid {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  margin-top: var(--space-sm);
}

.overview-item-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-xs);
  cursor: pointer;
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  border-left: 3px solid transparent;
  transition: background-color 0.2s;
}

.overview-item-header:hover {
  background: var(--bg-elevated);
}

.overview-item-header.active {
  background: var(--bg-elevated);
}

.overview-type-name {
  font-weight: 600;
  font-size: var(--font-sm);
}

.overview-count {
  font-size: var(--font-xs);
  color: var(--text-secondary);
  margin-left: auto;
}

.overview-mansions {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding-left: 20px;
}

.overview-mansion-tag {
  font-size: var(--font-xs);
  padding: 2px 8px;
  background: var(--bg-elevated);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  cursor: pointer;
  transition: background-color 0.2s, color 0.2s;
}

.overview-mansion-tag:hover {
  background: var(--bg-surface);
  color: var(--accent);
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
  padding: var(--space-md);
  width: 100%;
  background: none;
  border: none;
  cursor: pointer;
  font: inherit;
  color: inherit;
  text-align: left;
  transition: background-color 0.2s;
}

.relation-header:hover {
  background: var(--bg-elevated);
}

.relation-header:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.relation-header .relation-name {
  flex: 1;
  font-weight: 600;
}

.relation-header .relation-score {
  color: var(--text-secondary);
  font-size: var(--font-sm);
  font-variant-numeric: tabular-nums;
  margin-right: var(--space-sm);
}

.relation-toggle {
  font-size: var(--font-xs);
  color: var(--text-secondary);
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
  transition: box-shadow 0.2s;
}

.element-card.my-element {
  border-width: 2px;
  box-shadow: 0 0 12px rgba(var(--accent-rgb, 100, 100, 255), 0.3);
}

.element-header {
  padding: var(--space-sm) var(--space-md);
  color: var(--text-on-accent);
}

.element-name {
  font-weight: 600;
  margin-right: var(--space-sm);
}

.element-reading {
  font-size: var(--font-sm);
  opacity: 0.8;
}

.my-element-tag {
  margin-left: auto;
  font-size: var(--font-xs);
  background: rgba(0, 0, 0, 0.15);
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-weight: 600;
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

.element-body .element-extra {
  color: var(--text-secondary);
  font-size: var(--font-sm);
  line-height: 1.6;
  margin: var(--space-sm) 0 0;
}

.element-body .element-advice {
  font-style: italic;
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
  -webkit-overflow-scrolling: touch;
  scrollbar-width: thin;
  mask-image: linear-gradient(to right, transparent, black 8px, black calc(100% - 24px), transparent);
  -webkit-mask-image: linear-gradient(to right, transparent, black 8px, black calc(100% - 24px), transparent);
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

.life-stages {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.stage-item {
  padding-left: var(--space-md);
  border-left: 2px solid var(--accent);
}

.stage-label {
  display: inline-block;
  font-size: var(--font-xs);
  font-weight: 600;
  color: var(--accent);
  background: var(--bg-elevated);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  margin-bottom: var(--space-xs);
}

.stage-item p {
  color: var(--text-secondary);
  font-size: var(--font-sm);
  line-height: 1.6;
  margin: 0;
}

.section-subtitle {
  color: var(--accent);
  font-size: var(--font-base);
  margin: 0 0 var(--space-md);
  padding-top: var(--space-lg);
  border-top: 1px solid var(--border);
}

.calendar-note {
  font-size: var(--font-xs);
  color: var(--text-tertiary, var(--text-secondary));
  font-style: italic;
  margin-top: var(--space-sm);
}

.knowledge-table-section {
  margin-top: var(--space-lg);
  padding-top: var(--space-lg);
  border-top: 1px solid var(--border);
}

.table-subtitle {
  font-size: var(--font-sm);
  color: var(--accent);
  margin: 0 0 var(--space-md);
}

.cell-kanro { color: #C4A052; font-weight: 600; }
.cell-kongou { color: #5B8FA8; font-weight: 600; }
.cell-rasetsu { color: #E85D4C; font-weight: 600; }

.kuyou-row-great td { background: rgba(196, 160, 82, 0.15); }
.kuyou-row-good td { background: rgba(91, 143, 168, 0.15); }
.kuyou-row-half td { background: rgba(168, 162, 158, 0.12); }
.kuyou-row-bad td { background: rgba(232, 93, 76, 0.15); }

.nature-types-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-md);
  margin-top: var(--space-md);
}

@media (max-width: 767px) {
  .elements-grid,
  .nature-types-grid {
    grid-template-columns: 1fr;
  }
}

/* 漢文原典 - 金色左邊框 + 經卷風格 */
.classic-quote {
  border-left: 3px solid var(--stellar-gold);
  padding: var(--space-3) var(--space-4);
  margin: var(--space-2) 0;
  background: rgba(184, 134, 11, 0.06);
  font-family: var(--font-display);
  font-style: italic;
  color: var(--stellar-soft);
  font-size: 0.9rem;
  line-height: 1.8;
}

/* 日文詮釋 - 銀色左邊框 */
.ja-text {
  border-left: 3px solid var(--moon-silver);
  padding: var(--space-2) var(--space-4);
  margin: var(--space-2) 0;
  background: rgba(0, 0, 0, 0.03);
  font-size: 0.85rem;
  color: var(--text-secondary);
  line-height: 1.7;
}

/* 出處標記 */
.classic-source {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: var(--space-1);
  font-style: normal;
}

/* 區塊出處引用 */
.source-citation {
  margin-top: var(--space-4);
  padding: var(--space-2) var(--space-3);
  font-size: 0.75rem;
  color: var(--text-muted);
  border-top: 1px solid var(--border-subtle);
  line-height: 1.6;
}

.stage-quote {
  padding: var(--space-2) var(--space-3);
  font-size: 0.8rem;
}

.tab-intro {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  margin: 0 0 var(--space-md);
  line-height: 1.5;
}

.overview-intro {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  margin: 0 0 var(--space-sm);
}

.wheel-guide {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  margin-top: var(--space-md);
  padding: var(--space-md);
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
}

.guide-item {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-sm);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background-color 0.2s;
}

.guide-item:hover {
  background: var(--bg-elevated);
}

.guide-dots {
  display: flex;
  gap: 3px;
  flex-shrink: 0;
}

.guide-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.guide-dots.bar {
  gap: 2px;
}

.guide-bar {
  width: 6px;
  height: 14px;
  border-radius: 2px;
}

.guide-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.guide-text strong {
  font-size: var(--font-sm);
  color: var(--text-primary);
}

.guide-text span {
  font-size: var(--font-xs);
  color: var(--text-secondary);
}

@media (prefers-reduced-motion: reduce) {
  .knowledge-content {
    animation: none;
  }
}
</style>
