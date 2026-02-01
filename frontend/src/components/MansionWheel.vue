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
}

const props = withDefaults(defineProps<Props>(), {
  selectedIndex: -1,
  highlightIndex: -1
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

// 元素顏色
const elementColors: Record<string, string> = {
  '木': '#4A9B5A',
  '金': '#C4A052',
  '土': '#8B7355',
  '日': '#E89B3C',
  '月': '#7CB3D9',
  '火': '#E85D4C',
  '水': '#2D3436'
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

    return {
      ...mansion,
      path,
      textX,
      textY,
      midAngle,
      color: elementColors[mansion.element] || '#666',
      isSelected,
      isHighlight
    }
  })
})

const hoveredIndex = ref<number | null>(null)

const hoveredMansion = computed(() => {
  if (hoveredIndex.value === null) return null
  return mansionSegments.value[hoveredIndex.value] ?? null
})

function handleClick(mansion: Mansion & { path: string }) {
  emit('select', mansion)
}
</script>

<template>
  <div class="mansion-wheel">
    <svg :viewBox="`0 0 ${svgSize} ${svgSize}`" class="wheel-svg">
      <circle
        :cx="centerX"
        :cy="centerY"
        :r="outerRadius + 5"
        fill="none"
        stroke="var(--border)"
        stroke-width="1"
      />

      <circle
        :cx="centerX"
        :cy="centerY"
        :r="innerRadius - 5"
        fill="var(--bg-primary)"
        stroke="var(--border)"
        stroke-width="1"
      />

      <text
        :x="centerX"
        :y="centerY - 15"
        text-anchor="middle"
        class="center-title"
      >二十七宿</text>
      <text
        :x="centerX"
        :y="centerY + 10"
        text-anchor="middle"
        class="center-subtitle"
      >輪盤</text>

      <g v-for="segment in mansionSegments" :key="segment.index">
        <path
          :d="segment.path"
          :fill="segment.isHighlight ? 'var(--accent)' : segment.isSelected ? 'rgba(245, 158, 11, 0.5)' : segment.color"
          :stroke="hoveredIndex === segment.index ? 'var(--accent)' : 'var(--bg-primary)'"
          :stroke-width="hoveredIndex === segment.index || segment.isHighlight ? 2 : 1"
          :opacity="segment.isHighlight ? 1 : segment.isSelected ? 0.9 : 0.7"
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
          :class="{ 'highlight': segment.isHighlight, 'selected': segment.isSelected }"
          :transform="`rotate(${segment.midAngle + 90}, ${segment.textX}, ${segment.textY})`"
          @click="handleClick(segment)"
        >{{ segment.name_zh.replace('宿', '') }}</text>
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

.wheel-svg {
  width: 100%;
  max-width: 400px;
  height: auto;
}

.mansion-segment {
  cursor: pointer;
  transition: all 0.2s ease;
}

.mansion-segment:hover {
  opacity: 1 !important;
}

.mansion-name {
  font-size: 10px;
  fill: var(--bg-primary);
  font-weight: 600;
  pointer-events: none;
  user-select: none;
}

.mansion-name.highlight {
  fill: var(--bg-primary);
  font-weight: 700;
}

.mansion-name.selected {
  fill: var(--bg-primary);
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
  }
}
</style>
