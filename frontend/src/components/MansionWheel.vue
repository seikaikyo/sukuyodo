<script setup lang="ts">
import { computed, ref } from 'vue'

interface Mansion {
  index: number
  name_jp: string
  name_zh: string
  reading: string
  element: string
}

interface Props {
  mansions: Mansion[]
  selectedIndex?: number
  highlightIndex?: number
  mode?: 'compat' | 'fortune'
  dayMansionIndex?: number
  sankiPeriodIndex?: number
  rokugaiIndices?: number[]
  isRyouhan?: boolean
  showRelationOverview?: boolean
  focusedRelationType?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  selectedIndex: -1,
  highlightIndex: -1,
  mode: 'compat',
  dayMansionIndex: -1,
  sankiPeriodIndex: 0,
  isRyouhan: false,
  showRelationOverview: false,
  focusedRelationType: null,
})

interface RelationInfo {
  type: string
  name: string
  distance: number
  distanceCategory: 'near' | 'mid' | 'far'
}

const emit = defineEmits<{
  (e: 'select', mansion: Mansion): void
  (e: 'relation-detail', data: { mansion: Mansion, relation: RelationInfo } | null): void
  (e: 'update:focusedRelationType', value: string | null): void
}>()

// SVG 配置
const svgSize = 400
const centerX = svgSize / 2
const centerY = svgSize / 2
const outerRadius = 170
const innerRadius = 100
const textRadius = 140
const sankiOuterR = outerRadius + 14
const sankiInnerR = outerRadius + 8
const sevenDayOuterR = outerRadius + 8
const sevenDayInnerR = outerRadius + 1

// 七曜歸屬（27 宿按 index 順序的七曜名）
const SEVEN_DAY_CYCLE = ['日', '月', '火', '水', '木', '金', '土']

// 關係距離表
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

const RELATION_COLORS: Record<string, string> = {
  eishin: 'var(--stellar-gold)',
  gyotai: 'var(--astral-medium)',
  mei: 'var(--stellar-soft)',
  yusui: 'var(--astral-light)',
  kisei: 'var(--caution)',
  ankai: 'var(--warning)',
}

// 七曜色
const sevenDayColors: Record<string, string> = {
  '日': '#E89B3C',
  '月': '#7CB3D9',
  '火': '#E85D4C',
  '水': '#4A7A90',
  '木': '#4A9B5A',
  '金': '#C4A052',
  '土': '#8B7355',
}

// 旋轉狀態
const rotation = ref(0)
const isDragging = ref(false)
const dragStartAngle = ref(0)
const rotationStart = ref(0)
const svgEl = ref<SVGSVGElement | null>(null)

// 元素顏色
const elementColors: Record<string, string> = {
  '木': '#4A9B5A',
  '金': '#C4A052',
  '土': '#8B7355',
  '日': '#E89B3C',
  '月': '#7CB3D9',
  '火': '#E85D4C',
  '水': '#4A7A90'
}

function getAngleFromEvent(e: MouseEvent | Touch): number {
  if (!svgEl.value) return 0
  const rect = svgEl.value.getBoundingClientRect()
  const cx = rect.left + rect.width / 2
  const cy = rect.top + rect.height / 2
  return Math.atan2(e.clientY - cy, e.clientX - cx) * 180 / Math.PI
}

function onPointerDown(e: PointerEvent) {
  isDragging.value = true
  dragStartAngle.value = getAngleFromEvent(e)
  rotationStart.value = rotation.value
  ;(e.target as Element)?.setPointerCapture?.(e.pointerId)
}

function onPointerMove(e: PointerEvent) {
  if (!isDragging.value) return
  const currentAngle = getAngleFromEvent(e)
  rotation.value = rotationStart.value + (currentAngle - dragStartAngle.value)
}

function onPointerUp() {
  isDragging.value = false
}

// 計算每個宿的位置
const mansionSegments = computed(() => {
  if (!props.mansions || props.mansions.length === 0) return []

  const anglePerMansion = 360 / props.mansions.length

  return props.mansions.map((mansion, i) => {
    const startAngle = -90 + i * anglePerMansion
    const endAngle = startAngle + anglePerMansion
    const midAngle = startAngle + anglePerMansion / 2

    const startRad = (startAngle * Math.PI) / 180
    const endRad = (endAngle * Math.PI) / 180
    const midRad = (midAngle * Math.PI) / 180

    const x1 = centerX + outerRadius * Math.cos(startRad)
    const y1 = centerY + outerRadius * Math.sin(startRad)
    const x2 = centerX + outerRadius * Math.cos(endRad)
    const y2 = centerY + outerRadius * Math.sin(endRad)
    const x3 = centerX + innerRadius * Math.cos(endRad)
    const y3 = centerY + innerRadius * Math.sin(endRad)
    const x4 = centerX + innerRadius * Math.cos(startRad)
    const y4 = centerY + innerRadius * Math.sin(startRad)

    const textX = centerX + textRadius * Math.cos(midRad)
    const textY = centerY + textRadius * Math.sin(midRad)

    const largeArc = anglePerMansion > 180 ? 1 : 0

    const path = `
      M ${x1} ${y1}
      A ${outerRadius} ${outerRadius} 0 ${largeArc} 1 ${x2} ${y2}
      L ${x3} ${y3}
      A ${innerRadius} ${innerRadius} 0 ${largeArc} 0 ${x4} ${y4}
      Z
    `

    const isSelected = props.selectedIndex === i
    const isHighlight = props.highlightIndex === i
    const isDayMansion = props.mode === 'fortune' && props.dayMansionIndex === i
    const isRokugai = props.isRyouhan && (props.rokugaiIndices || []).includes(i)

    return {
      ...mansion,
      path,
      textX,
      textY,
      midAngle,
      color: elementColors[mansion.element] || '#666',
      isSelected,
      isHighlight,
      isDayMansion,
      isRokugai,
    }
  })
})

// 三期弧形色帶
const sankiArcs = computed(() => {
  if (props.highlightIndex < 0 || !props.mansions || props.mansions.length === 0) return []

  const count = props.mansions.length
  const anglePerMansion = 360 / count
  const colors = ['var(--kanro-color)', 'var(--rasetsu-color)', '#5C8FA8']

  return [0, 1, 2].map(period => {
    const startIdx = (props.highlightIndex + period * 9) % count
    const segStart = -90 + startIdx * anglePerMansion
    const segEnd = segStart + 9 * anglePerMansion

    const startRad = (segStart * Math.PI) / 180
    const endRad = (segEnd * Math.PI) / 180

    const x1 = centerX + sankiOuterR * Math.cos(startRad)
    const y1 = centerY + sankiOuterR * Math.sin(startRad)
    const x2 = centerX + sankiOuterR * Math.cos(endRad)
    const y2 = centerY + sankiOuterR * Math.sin(endRad)
    const x3 = centerX + sankiInnerR * Math.cos(endRad)
    const y3 = centerY + sankiInnerR * Math.sin(endRad)
    const x4 = centerX + sankiInnerR * Math.cos(startRad)
    const y4 = centerY + sankiInnerR * Math.sin(startRad)

    const large = 9 * anglePerMansion > 180 ? 1 : 0

    return {
      path: `M ${x1} ${y1} A ${sankiOuterR} ${sankiOuterR} 0 ${large} 1 ${x2} ${y2} L ${x3} ${y3} A ${sankiInnerR} ${sankiInnerR} 0 ${large} 0 ${x4} ${y4} Z`,
      color: colors[period],
    }
  })
})

const hoveredIndex = ref<number | null>(null)

const hoveredMansion = computed(() => {
  if (hoveredIndex.value === null) return null
  return mansionSegments.value[hoveredIndex.value] ?? null
})

// 七曜環 segments
const sevenDayRingSegments = computed(() => {
  if (!props.mansions || props.mansions.length === 0) return []
  const count = props.mansions.length
  const anglePerMansion = 360 / count
  return props.mansions.map((_m, i) => {
    const dayIdx = i % 7
    const dayName = SEVEN_DAY_CYCLE[dayIdx]!
    const startAngle = -90 + i * anglePerMansion
    const endAngle = startAngle + anglePerMansion
    const startRad = (startAngle * Math.PI) / 180
    const endRad = (endAngle * Math.PI) / 180
    const x1 = centerX + sevenDayOuterR * Math.cos(startRad)
    const y1 = centerY + sevenDayOuterR * Math.sin(startRad)
    const x2 = centerX + sevenDayOuterR * Math.cos(endRad)
    const y2 = centerY + sevenDayOuterR * Math.sin(endRad)
    const x3 = centerX + sevenDayInnerR * Math.cos(endRad)
    const y3 = centerY + sevenDayInnerR * Math.sin(endRad)
    const x4 = centerX + sevenDayInnerR * Math.cos(startRad)
    const y4 = centerY + sevenDayInnerR * Math.sin(startRad)
    const largeArc = anglePerMansion > 180 ? 1 : 0
    return {
      path: `M ${x1} ${y1} A ${sevenDayOuterR} ${sevenDayOuterR} 0 ${largeArc} 1 ${x2} ${y2} L ${x3} ${y3} A ${sevenDayInnerR} ${sevenDayInnerR} 0 ${largeArc} 0 ${x4} ${y4} Z`,
      color: sevenDayColors[dayName] || '#666',
      dayName,
    }
  })
})

// 選中宿與本命宿的關係
function getRelationForDistance(dist: number): RelationInfo | null {
  const d = ((dist % 27) + 27) % 27
  for (const [type, distances] of Object.entries(RELATION_DISTANCES)) {
    if (distances.includes(d)) {
      const absDist = Math.min(d, 27 - d)
      let category: 'near' | 'mid' | 'far' = 'mid'
      if (absDist <= 4 || d === 9 || d === 18) category = 'near'
      else if (absDist >= 10 && absDist <= 13) category = 'far'
      else category = 'mid'
      return { type, name: RELATION_NAMES[type] || type, distance: d, distanceCategory: category }
    }
  }
  return null
}

// 全覽模式：每宿的關係映射
const mansionRelationMap = computed(() => {
  if (props.highlightIndex < 0) return new Map<number, RelationInfo>()
  const map = new Map<number, RelationInfo>()
  for (let i = 0; i < 27; i++) {
    const dist = ((i - props.highlightIndex) % 27 + 27) % 27
    const rel = getRelationForDistance(dist)
    if (rel) map.set(i, rel)
  }
  return map
})

// 連線資料（本命宿到選中宿 / 全覽模式到全部宿）
const connectionLines = computed(() => {
  if (props.highlightIndex < 0 || !props.mansions.length) return []
  const count = props.mansions.length
  const anglePerMansion = 360 / count
  const connR = innerRadius - 5

  function getPoint(idx: number) {
    const angle = -90 + idx * anglePerMansion + anglePerMansion / 2
    const rad = (angle * Math.PI) / 180
    return { x: centerX + connR * Math.cos(rad), y: centerY + connR * Math.sin(rad) }
  }

  const lines: Array<{
    path: string
    color: string
    dashArray: string
    opacity: number
    targetIndex: number
    relation: RelationInfo
  }> = []

  // 全覽模式不畫連線，只靠填色區分
  const indices = props.showRelationOverview
    ? []
    : (props.selectedIndex >= 0 && props.selectedIndex !== props.highlightIndex ? [props.selectedIndex] : [])

  const from = getPoint(props.highlightIndex)

  for (const idx of indices) {
    const rel = mansionRelationMap.value.get(idx)
    if (!rel) continue
    const to = getPoint(idx)
    const mx = (from.x + to.x) / 2
    const my = (from.y + to.y) / 2
    const dx = mx - centerX
    const dy = my - centerY
    const len = Math.sqrt(dx * dx + dy * dy) || 1
    const pull = connR * 0.3
    const cx = mx - (dx / len) * pull
    const cy = my - (dy / len) * pull
    const dashMap: Record<string, string> = { near: 'none', mid: '8 4', far: '3 3' }
    lines.push({
      path: `M ${from.x} ${from.y} Q ${cx} ${cy} ${to.x} ${to.y}`,
      color: RELATION_COLORS[rel.type] || 'var(--text-secondary)',
      dashArray: dashMap[rel.distanceCategory] || 'none',
      opacity: props.showRelationOverview ? 0.35 : 0.8,
      targetIndex: idx,
      relation: rel,
    })
  }
  return lines
})

// 中心資訊（三種狀態）
const centerInfo = computed(() => {
  // 有選中宿且有關係
  if (props.selectedIndex >= 0 && props.highlightIndex >= 0 && props.selectedIndex !== props.highlightIndex) {
    const rel = mansionRelationMap.value.get(props.selectedIndex)
    if (rel) {
      const m = props.mansions[props.selectedIndex]
      return { title: m?.name_zh?.replace('宿', '') || '', sub: rel.name, tertiary: `距離 ${rel.distance}` }
    }
  }
  // 全覽模式
  if (props.showRelationOverview && props.highlightIndex >= 0) {
    if (props.focusedRelationType) {
      const name = RELATION_NAMES[props.focusedRelationType] || ''
      const count = RELATION_DISTANCES[props.focusedRelationType]?.length || 0
      return { title: name, sub: `${count} 宿`, tertiary: '' }
    }
    return { title: '關係全覽', sub: '點擊圖例篩選', tertiary: '' }
  }
  // 運勢模式
  if (props.mode === 'fortune') {
    if (props.dayMansionIndex >= 0 && props.mansions[props.dayMansionIndex]) {
      return { title: props.mansions[props.dayMansionIndex]!.name_jp, sub: '當日宿', tertiary: '' }
    }
    return { title: '運勢', sub: '模式', tertiary: '' }
  }
  return { title: '二十七宿', sub: '輪盤', tertiary: '' }
})

function handleClick(mansion: Mansion & { path: string }) {
  emit('select', mansion)
  // 計算關係並 emit
  if (props.highlightIndex >= 0 && mansion.index !== props.highlightIndex) {
    const rel = mansionRelationMap.value.get(mansion.index)
    if (rel) {
      emit('relation-detail', { mansion, relation: rel })
    }
  } else {
    emit('relation-detail', null)
  }
}

function getSegmentFill(seg: typeof mansionSegments.value[0]): string {
  if (seg.isDayMansion) return 'var(--accent)'
  if (seg.isHighlight) return 'var(--kongou-color)'
  // 全覽模式：有聚焦才用關係色，無聚焦用元素色
  if (props.showRelationOverview && props.focusedRelationType && props.highlightIndex >= 0) {
    const rel = mansionRelationMap.value.get(seg.index)
    if (rel && rel.type === props.focusedRelationType) return RELATION_COLORS[rel.type] || seg.color
  }
  if (seg.isSelected) return 'rgba(139, 105, 20, 0.6)'
  return seg.color
}

function getSegmentOpacity(seg: typeof mansionSegments.value[0]): number {
  if (seg.isDayMansion || seg.isHighlight) return 1
  if (seg.isSelected) return 0.9
  // 全覽聚焦模式：匹配的關係 1.0，其他 0.25
  if (props.showRelationOverview && props.focusedRelationType && props.highlightIndex >= 0) {
    const rel = mansionRelationMap.value.get(seg.index)
    if (rel && rel.type === props.focusedRelationType) return 1.0
    return 0.25
  }
  return 0.7
}

function getSegmentStroke(seg: typeof mansionSegments.value[0]): string {
  if (seg.isRokugai) return 'var(--rasetsu-color)'
  if (hoveredIndex.value === seg.index) return 'var(--accent)'
  return 'var(--cosmos-void)'
}

function getSegmentStrokeWidth(seg: typeof mansionSegments.value[0]): number {
  if (seg.isRokugai) return 2
  if (hoveredIndex.value === seg.index || seg.isHighlight || seg.isDayMansion) return 2
  return 1
}

function getSegmentStrokeDash(seg: typeof mansionSegments.value[0]): string {
  if (seg.isRokugai) return '3 2'
  return 'none'
}

// 全覽 hover 時的關係資訊
const hoveredRelation = computed(() => {
  if (!props.showRelationOverview || hoveredIndex.value === null) return null
  return mansionRelationMap.value.get(hoveredIndex.value) ?? null
})

// 圖例切換：全覽模式用關係圖例，否則用五行圖例
const RELATION_LEGEND_ITEMS = [
  { key: 'eishin', label: '栄親', color: '#B8860B' },
  { key: 'yusui', label: '友衰', color: '#7B9CC5' },
  { key: 'ankai', label: '安壊', color: '#C53030' },
  { key: 'kisei', label: '危成', color: '#9B7B1C' },
  { key: 'mei', label: '命', color: '#A08050' },
  { key: 'gyotai', label: '業胎', color: '#5A7FA5' },
]

const activeLegend = computed(() => {
  if (props.showRelationOverview) {
    return RELATION_LEGEND_ITEMS.map(item => ({
      ...item,
      clickable: true,
      active: props.focusedRelationType === item.key,
    }))
  }
  return Object.entries(elementColors).map(([element, color]) => ({
    key: element,
    label: element,
    color,
    clickable: false,
    active: false,
  }))
})

function toggleRelationFocus(type: string) {
  const newVal = props.focusedRelationType === type ? null : type
  emit('update:focusedRelationType', newVal)
}
</script>

<template>
  <div class="mansion-wheel" :class="{ dragging: isDragging }">
    <svg
      ref="svgEl"
      :viewBox="`0 0 ${svgSize} ${svgSize}`"
      class="wheel-svg"
      @pointerdown="onPointerDown"
      @pointermove="onPointerMove"
      @pointerup="onPointerUp"
      @pointercancel="onPointerUp"
    >
      <!-- 三期弧形色帶（全覽模式隱藏） -->
      <g v-if="sankiArcs.length && !showRelationOverview" :transform="`rotate(${rotation}, ${centerX}, ${centerY})`">
        <path
          v-for="(arc, idx) in sankiArcs"
          :key="`sanki-${idx}`"
          :d="arc.path"
          :fill="arc.color"
          opacity="0.5"
        />
      </g>

      <!-- 七曜環（全覽模式隱藏） -->
      <g v-if="sevenDayRingSegments.length && !showRelationOverview" :transform="`rotate(${rotation}, ${centerX}, ${centerY})`">
        <path
          v-for="(seg, idx) in sevenDayRingSegments"
          :key="`sd-${idx}`"
          :d="seg.path"
          :fill="seg.color"
          opacity="0.7"
        />
      </g>

      <!-- 外圈 -->
      <circle
        :cx="centerX"
        :cy="centerY"
        :r="outerRadius + 5"
        fill="none"
        stroke="var(--border)"
        stroke-width="1"
      />

      <!-- 內圈 -->
      <circle
        :cx="centerX"
        :cy="centerY"
        :r="innerRadius - 5"
        fill="var(--bg-primary)"
        stroke="var(--border)"
        stroke-width="1"
      />

      <!-- 關係連線 L5 -->
      <g v-if="connectionLines.length" :transform="`rotate(${rotation}, ${centerX}, ${centerY})`">
        <path
          v-for="(line, idx) in connectionLines"
          :key="`conn-${idx}`"
          :d="line.path"
          :stroke="line.color"
          stroke-width="2.5"
          fill="none"
          :stroke-dasharray="line.dashArray"
          :opacity="line.opacity"
          class="connection-line"
        />
      </g>

      <!-- 中心面板 L6 -->
      <text
        :x="centerX"
        :y="centerInfo.tertiary ? centerY - 20 : centerY - 15"
        text-anchor="middle"
        class="center-title"
      >{{ centerInfo.title }}</text>
      <text
        :x="centerX"
        :y="centerInfo.tertiary ? centerY + 5 : centerY + 10"
        text-anchor="middle"
        class="center-subtitle"
      >{{ centerInfo.sub }}</text>
      <text
        v-if="centerInfo.tertiary"
        :x="centerX"
        :y="centerY + 25"
        text-anchor="middle"
        class="center-tertiary"
      >{{ centerInfo.tertiary }}</text>

      <!-- 宿位 segments -->
      <g :transform="`rotate(${rotation}, ${centerX}, ${centerY})`">
        <g v-for="segment in mansionSegments" :key="segment.index">
          <path
            :d="segment.path"
            :fill="getSegmentFill(segment)"
            :stroke="getSegmentStroke(segment)"
            :stroke-width="getSegmentStrokeWidth(segment)"
            :stroke-dasharray="getSegmentStrokeDash(segment)"
            :opacity="getSegmentOpacity(segment)"
            class="mansion-segment"
            @mouseenter="hoveredIndex = segment.index"
            @mouseleave="hoveredIndex = null"
            @click="handleClick(segment)"
          />

          <text
            :x="segment.textX"
            :y="segment.textY"
            text-anchor="middle"
            dominant-baseline="middle"
            class="mansion-name"
            :class="{
              'highlight': segment.isHighlight,
              'selected': segment.isSelected,
              'day-mansion': segment.isDayMansion,
            }"
            :transform="`rotate(${segment.midAngle + 90}, ${segment.textX}, ${segment.textY})`"
            @click="handleClick(segment)"
          >{{ segment.name_zh.replace('宿', '') }}</text>
        </g>
      </g>
    </svg>

    <div class="wheel-legend">
      <div
        v-for="item in activeLegend"
        :key="item.key"
        class="legend-item"
        :class="{ clickable: item.clickable, active: item.active }"
        @click="item.clickable ? toggleRelationFocus(item.key) : undefined"
      >
        <span class="legend-dot" :style="{ background: item.color }"></span>
        <span class="legend-text">{{ item.label }}</span>
      </div>
      <span v-if="showRelationOverview && !focusedRelationType" class="legend-hint">
        點擊篩選
      </span>
    </div>

    <div v-if="hoveredMansion" class="hover-tooltip">
      <strong>{{ hoveredMansion.name_jp }}</strong>
      <ruby>
        {{ hoveredMansion.name_zh }}
        <rp>(</rp><rt>{{ hoveredMansion.reading }}</rt><rp>)</rp>
      </ruby>
      <span class="tooltip-element" :style="{ color: elementColors[hoveredMansion.element] }">
        {{ hoveredMansion.element }}
      </span>
      <span v-if="hoveredMansion.isDayMansion" class="tooltip-tag day">當日宿</span>
      <span v-if="hoveredMansion.isRokugai" class="tooltip-tag rokugai">六害宿</span>
      <span v-if="hoveredRelation" class="tooltip-tag relation">{{ hoveredRelation.name }}</span>
    </div>
  </div>
</template>

<style scoped>
.mansion-wheel {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-md);
}

.mansion-wheel.dragging {
  cursor: grabbing;
}

.wheel-svg {
  width: 100%;
  max-width: 560px;
  height: auto;
  cursor: grab;
  touch-action: none;
}

.mansion-wheel.dragging .wheel-svg {
  cursor: grabbing;
}

.mansion-segment {
  cursor: pointer;
  transition: opacity 0.2s ease;
}

.mansion-segment:hover {
  opacity: 1 !important;
}

.mansion-name {
  font-size: 10px;
  fill: var(--text-on-accent);
  font-weight: 600;
  pointer-events: none;
  user-select: none;
}

.mansion-name.highlight {
  fill: var(--text-on-accent);
  font-weight: 700;
}

.mansion-name.selected {
  fill: var(--text-on-accent);
}

.mansion-name.day-mansion {
  fill: var(--text-on-accent);
  font-weight: 700;
}

.center-title {
  font-size: 18px;
  fill: var(--accent);
  font-weight: 600;
}

.center-subtitle {
  font-size: 14px;
  fill: var(--text-secondary);
}

.center-tertiary {
  font-size: 12px;
  fill: var(--text-muted, var(--text-secondary));
  opacity: 0.7;
}

.connection-line {
  pointer-events: none;
  transition: opacity 0.2s ease;
}

.wheel-legend {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-surface);
  border-radius: var(--radius-md);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.legend-text {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.legend-item.clickable {
  cursor: pointer;
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  transition: background-color 0.2s, opacity 0.2s;
}

.legend-item.clickable:hover {
  background: var(--bg-elevated);
}

.legend-item.clickable.active {
  background: var(--bg-elevated);
  outline: 1.5px solid var(--accent);
}

.legend-hint {
  width: 100%;
  text-align: center;
  font-size: 0.7rem;
  color: var(--text-muted, var(--text-secondary));
  opacity: 0.6;
}

.hover-tooltip {
  position: absolute;
  bottom: -60px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  font-size: 0.9rem;
  white-space: nowrap;
  z-index: 10;
}

.hover-tooltip strong {
  color: var(--accent);
}

.hover-tooltip ruby rt {
  font-size: 0.6em;
}

.tooltip-element {
  font-weight: 600;
}

.tooltip-tag {
  font-size: 0.7rem;
  padding: 1px 6px;
  border-radius: var(--radius-full);
  font-weight: 600;
}

.tooltip-tag.day {
  background: rgba(139, 105, 20, 0.15);
  color: var(--accent);
}

.tooltip-tag.rokugai {
  background: rgba(197, 48, 48, 0.15);
  color: var(--rasetsu-color);
}

.tooltip-tag.relation {
  background: rgba(139, 105, 20, 0.15);
  color: var(--accent);
}

@media (max-width: 500px) {
  .wheel-svg {
    max-width: 360px;
  }

  .mansion-name {
    font-size: 8px;
  }

  .center-title {
    font-size: 14px;
  }

  .center-subtitle {
    font-size: 12px;
  }

  .hover-tooltip {
    font-size: 0.8rem;
    max-width: 90vw;
  }
}

@media (max-width: 479px) {
  .wheel-svg {
    max-width: 320px;
  }
}
</style>
