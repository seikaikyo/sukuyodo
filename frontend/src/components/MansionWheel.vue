<script setup lang="ts">
import { computed, ref, onMounted, onBeforeUnmount } from 'vue'

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
}

const props = withDefaults(defineProps<Props>(), {
  selectedIndex: -1,
  highlightIndex: -1,
  mode: 'compat',
  dayMansionIndex: -1,
  sankiPeriodIndex: 0,
  isRyouhan: false,
})

const emit = defineEmits<{
  (e: 'select', mansion: Mansion): void
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

// 關係名稱對照
const RELATION_NAMES: Record<string, string> = {
  eishin: '榮親',
  gyotai: '業胎',
  mei: '命',
  yusui: '友衰',
  ankai: '安壊',
  kisei: '危成',
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

// 中心文字
const centerText = computed(() => {
  if (props.mode === 'fortune') {
    if (props.dayMansionIndex >= 0 && props.mansions[props.dayMansionIndex]) {
      return { title: props.mansions[props.dayMansionIndex].name_jp, sub: '當日宿' }
    }
    return { title: '運勢', sub: '模式' }
  }
  return { title: '二十七宿', sub: '輪盤' }
})

function handleClick(mansion: Mansion & { path: string }) {
  emit('select', mansion)
}

function getSegmentFill(seg: typeof mansionSegments.value[0]): string {
  if (seg.isDayMansion) return 'var(--accent)'
  if (seg.isHighlight) return 'var(--kongou-color)'
  if (seg.isSelected) return 'rgba(139, 105, 20, 0.6)'
  return seg.color
}

function getSegmentOpacity(seg: typeof mansionSegments.value[0]): number {
  if (seg.isDayMansion || seg.isHighlight) return 1
  if (seg.isSelected) return 0.9
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
      <!-- 三期弧形色帶 -->
      <g v-if="sankiArcs.length" :transform="`rotate(${rotation}, ${centerX}, ${centerY})`">
        <path
          v-for="(arc, idx) in sankiArcs"
          :key="`sanki-${idx}`"
          :d="arc.path"
          :fill="arc.color"
          opacity="0.5"
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

      <!-- 中心文字 -->
      <text
        :x="centerX"
        :y="centerY - 15"
        text-anchor="middle"
        class="center-title"
      >{{ centerText.title }}</text>
      <text
        :x="centerX"
        :y="centerY + 10"
        text-anchor="middle"
        class="center-subtitle"
      >{{ centerText.sub }}</text>

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
      <div class="legend-item" v-for="(color, element) in elementColors" :key="element">
        <span class="legend-dot" :style="{ background: color }"></span>
        <span class="legend-text">{{ element }}</span>
      </div>
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
  max-width: 400px;
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
  font-size: 14px;
  fill: var(--accent);
  font-weight: 600;
}

.center-subtitle {
  font-size: 12px;
  fill: var(--text-secondary);
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

@media (max-width: 500px) {
  .wheel-svg {
    max-width: 320px;
  }

  .mansion-name {
    font-size: 8px;
  }

  .center-title {
    font-size: 12px;
  }

  .center-subtitle {
    font-size: 10px;
  }

  .hover-tooltip {
    font-size: 0.8rem;
    max-width: 90vw;
  }
}

@media (max-width: 479px) {
  .wheel-svg {
    max-width: 280px;
  }
}
</style>
