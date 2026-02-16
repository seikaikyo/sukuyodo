import type { YearlyFortune, CompatibilityResult } from '../composables/useSukuyodo'
import { getScoreClass, getScoreLevel } from './fortune-helpers'

// --- 共用工具 ---

function downloadHtml(html: string, filename: string) {
  const blob = new Blob([html], { type: 'text/html;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

function escHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function scoreColor(score: number): string {
  const cls = getScoreClass(score)
  const map: Record<string, string> = {
    excellent: '#d4a017',
    good: '#4a9b6b',
    fair: '#3b82f6',
    caution: '#eab308',
    warning: '#ef4444'
  }
  return map[cls] || '#a8a29e'
}

function scoreLevelText(score: number): string {
  if (score >= 90) return '大吉'
  if (score >= 75) return '吉'
  if (score >= 60) return '中吉'
  if (score >= 45) return '小吉'
  return '凶'
}

function kuyouLevelColor(level: string): string {
  if (level === '大吉') return '#d4a017'
  if (level === '吉') return '#4a9b6b'
  if (level === '半吉') return '#3b82f6'
  return '#ef4444'
}

function practiceLevelColor(level: string): string {
  if (level === '弘法') return '#d4a017'
  if (level === '增上') return '#4a9b6b'
  if (level === '調和') return '#3b82f6'
  return '#9333ea'
}

function todayStr(): string {
  const d = new Date()
  return `${d.getFullYear()}/${String(d.getMonth() + 1).padStart(2, '0')}/${String(d.getDate()).padStart(2, '0')}`
}

// --- 共用 CSS ---

function getReportCSS(): string {
  return `
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: "Hiragino Sans", "Noto Sans TC", "Noto Sans JP", sans-serif;
      background: #1c1917; color: #fafaf9;
      line-height: 1.7; padding: 24px; max-width: 800px; margin: 0 auto;
    }
    h1, h2, h3, h4, h5 { color: #fafaf9; line-height: 1.4; }
    h1 { font-size: 24px; margin-bottom: 8px; }
    h2 { font-size: 20px; margin: 32px 0 12px; border-bottom: 1px solid #57534e; padding-bottom: 8px; }
    h3 { font-size: 18px; margin: 24px 0 8px; }
    h4 { font-size: 16px; margin: 16px 0 6px; color: #f59e0b; }
    h5 { font-size: 14px; margin: 12px 0 4px; color: #a8a29e; }
    p { margin: 6px 0; }
    ul { padding-left: 20px; margin: 6px 0; }
    li { margin: 4px 0; }

    .cover { text-align: center; padding: 48px 0 32px; border-bottom: 2px solid #f59e0b; margin-bottom: 32px; }
    .cover h1 { font-size: 28px; color: #f59e0b; }
    .cover .subtitle { color: #a8a29e; font-size: 14px; margin-top: 8px; }
    .cover .mansion-name { font-size: 20px; margin-top: 16px; }
    .cover .mansion-reading { color: #a8a29e; font-size: 14px; }

    .card {
      background: #292524; border: 1px solid #57534e; border-radius: 12px;
      padding: 16px; margin-bottom: 16px;
    }
    .card-header {
      display: flex; justify-content: space-between; align-items: center;
      margin-bottom: 12px;
    }
    .card-year { font-size: 18px; font-weight: 700; }
    .card-star { margin-left: 8px; }
    .level-badge {
      display: inline-block; padding: 2px 10px; border-radius: 9999px;
      font-size: 12px; font-weight: 700;
    }
    .score-big {
      font-size: 28px; font-weight: 700; text-align: center; margin: 8px 0;
    }

    .score-bar-row { display: flex; align-items: center; gap: 8px; margin: 4px 0; }
    .score-bar-label { width: 48px; font-size: 13px; color: #a8a29e; text-align: right; flex-shrink: 0; }
    .score-bar { flex: 1; height: 8px; background: #44403c; border-radius: 4px; overflow: hidden; }
    .score-bar-fill { height: 100%; border-radius: 4px; }
    .score-bar-value { width: 32px; font-size: 13px; text-align: right; flex-shrink: 0; }

    .kuyou-grid {
      display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; margin: 12px 0;
    }
    .kuyou-cell {
      background: #292524; border: 1px solid #57534e; border-radius: 8px;
      padding: 8px; text-align: center; font-size: 13px;
    }
    .kuyou-cell .cell-year { display: block; color: #a8a29e; font-size: 12px; }
    .kuyou-cell .cell-star { display: block; font-weight: 600; margin: 2px 0; }
    .kuyou-cell .cell-level { display: block; font-size: 11px; font-weight: 700; }

    .chart-container { margin: 16px 0; text-align: center; }
    .chart-container svg { max-width: 100%; height: auto; }

    .section-divider { border: none; border-top: 1px solid #57534e; margin: 24px 0; }

    .mantra-box {
      background: #1c1917; border: 1px solid #57534e; border-radius: 8px;
      padding: 12px; margin: 8px 0; text-align: center;
    }
    .mantra-text { font-size: 16px; letter-spacing: 2px; word-break: break-all; }
    .mantra-reading { color: #a8a29e; font-size: 13px; margin-top: 4px; }

    .homa-box {
      display: flex; gap: 8px; align-items: baseline; margin: 8px 0;
      font-size: 14px;
    }
    .homa-type { font-weight: 700; color: #f59e0b; }

    .tag { display: inline-block; background: #44403c; border-radius: 9999px; padding: 2px 10px; font-size: 12px; margin: 2px 4px 2px 0; }

    .monthly-grid {
      display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; margin: 8px 0;
    }
    .monthly-cell {
      background: #1c1917; border: 1px solid #57534e; border-radius: 6px;
      padding: 6px; font-size: 12px;
    }
    .monthly-cell .cell-month { font-weight: 600; }
    .monthly-cell .cell-tip { color: #a8a29e; font-size: 11px; margin-top: 2px; }

    .persons-row { display: flex; gap: 16px; justify-content: center; align-items: center; margin: 16px 0; flex-wrap: wrap; }
    .person-box {
      background: #292524; border: 1px solid #57534e; border-radius: 12px;
      padding: 16px; text-align: center; min-width: 120px;
    }
    .person-box h5 { color: #a8a29e; margin-bottom: 4px; }
    .person-box .mansion { font-size: 18px; font-weight: 700; }
    .relation-box { text-align: center; }
    .relation-name { font-size: 18px; font-weight: 700; color: #f59e0b; }
    .relation-reading { color: #a8a29e; font-size: 13px; display: block; }
    .distance-tag { font-size: 12px; background: #44403c; padding: 2px 8px; border-radius: 9999px; }

    .direction-table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 14px; }
    .direction-table td { padding: 6px 12px; border: 1px solid #57534e; }
    .direction-table .label { color: #a8a29e; width: 80px; }

    .tips-list, .avoid-list { margin: 8px 0; }
    .tips-list h5 { color: #4a9b6b; }
    .avoid-list h5 { color: #ef4444; }

    .good-for-tags { display: flex; flex-wrap: wrap; gap: 6px; margin: 8px 0; }

    .footer { text-align: center; color: #57534e; font-size: 12px; margin-top: 48px; padding-top: 16px; border-top: 1px solid #57534e; }

    @media print {
      body { background: #fff; color: #1c1917; padding: 12px; }
      h1, h2, h3, h4, h5, p, li, span, td { color: #1c1917 !important; }
      h4 { color: #92400e !important; }
      .cover h1 { color: #92400e !important; }
      .cover { border-bottom-color: #92400e; }
      .card { background: #fff; border-color: #d6d3d1; }
      .kuyou-cell { background: #fff; border-color: #d6d3d1; }
      .mantra-box { background: #f5f5f4; border-color: #d6d3d1; }
      .monthly-cell { background: #f5f5f4; border-color: #d6d3d1; }
      .person-box { background: #fff; border-color: #d6d3d1; }
      .score-bar { background: #e7e5e4; }
      .tag { background: #e7e5e4; }
      .distance-tag { background: #e7e5e4; }
      .footer { color: #a8a29e !important; border-top-color: #d6d3d1; }
      .card { page-break-inside: avoid; }
      h2 { page-break-before: auto; page-break-after: avoid; }
    }
  `
}

// --- 流年報告 ---

interface DecadeReportOptions {
  yearlyRange: YearlyFortune[]
  mansionName: string
  mansionReading: string
  mansionElement: string
  birthDate: string
  perspective: 'secular' | 'practitioner'
}

function buildScoreBars(fortune: YearlyFortune['fortune'], labels?: { career: string; love: string; health: string; wealth: string }): string {
  const rows = [
    { label: '整體', score: fortune.overall },
    { label: labels?.career || '事業', score: fortune.career },
    { label: labels?.love || '感情', score: fortune.love },
    { label: labels?.health || '健康', score: fortune.health },
    { label: labels?.wealth || '財運', score: fortune.wealth },
  ]
  return rows.map(r => `
    <div class="score-bar-row">
      <span class="score-bar-label">${escHtml(r.label)}</span>
      <div class="score-bar"><div class="score-bar-fill" style="width:${r.score}%;background:${scoreColor(r.score)}"></div></div>
      <span class="score-bar-value">${r.score}</span>
    </div>
  `).join('')
}

function buildSvgChart(yearlyRange: YearlyFortune[], isPractitioner: boolean): string {
  if (yearlyRange.length < 2) return ''
  const w = 620, h = 220
  const pl = 55, pr = 35, pt = 25, pb = 25
  const cw = w - pl - pr, ch = h - pt - pb
  const minS = 30, maxS = 100
  const toY = (s: number) => pt + ch - ((s - minS) / (maxS - minS)) * ch
  const toX = (i: number) => pl + (i / (yearlyRange.length - 1)) * cw

  const gridLines = [40, 50, 60, 70, 80, 90, 100].map(s => {
    const y = toY(s).toFixed(1)
    return `<line x1="${pl}" y1="${y}" x2="${w - pr}" y2="${y}" stroke="#57534e" stroke-width="0.5" stroke-dasharray="${s % 20 === 0 ? '0' : '3,3'}"/>
      <text x="${pl - 6}" y="${y}" text-anchor="end" fill="#a8a29e" font-size="11" dominant-baseline="middle">${s}</text>`
  }).join('')

  const path = yearlyRange
    .map((y, i) => `${i === 0 ? 'M' : 'L'}${toX(i).toFixed(1)},${toY(y.fortune.overall).toFixed(1)}`)
    .join(' ')

  const dots = yearlyRange.map((y, i) => {
    const x = toX(i).toFixed(1)
    const yPos = toY(y.fortune.overall).toFixed(1)
    const color = scoreColor(y.fortune.overall)
    return `<circle cx="${x}" cy="${yPos}" r="4" fill="${color}" stroke="#1c1917" stroke-width="2"/>
      <text x="${x}" y="${(parseFloat(yPos) - 10).toFixed(1)}" text-anchor="middle" fill="${color}" font-size="11" font-weight="600">${y.fortune.overall}</text>
      <text x="${x}" y="${h - 4}" text-anchor="middle" fill="#a8a29e" font-size="11">${String(y.year).slice(-2)}</text>`
  }).join('')

  const bgTop = `<rect x="${pl}" y="${toY(100).toFixed(1)}" width="${cw}" height="${(toY(75) - toY(100)).toFixed(1)}" fill="rgba(80,180,80,0.08)"/>`
  const bgBot = `<rect x="${pl}" y="${toY(55).toFixed(1)}" width="${cw}" height="${(toY(minS) - toY(55)).toFixed(1)}" fill="${isPractitioner ? 'rgba(123,31,162,0.08)' : 'rgba(220,80,80,0.08)'}"/>`

  return `<div class="chart-container">
    <svg viewBox="0 0 ${w} ${h}" xmlns="http://www.w3.org/2000/svg">
      ${bgTop}${bgBot}${gridLines}
      <path d="${path}" fill="none" stroke="#f59e0b" stroke-width="2"/>
      ${dots}
    </svg>
  </div>`
}

function buildYearCardSecular(y: YearlyFortune): string {
  const levelColor = kuyouLevelColor(y.kuyou_star.level)
  let html = `<div class="card">
    <div class="card-header">
      <div>
        <span class="card-year">${y.year}</span>
        <span class="card-star">${escHtml(y.kuyou_star.name)}</span>
        <span class="level-badge" style="background:${levelColor}22;color:${levelColor}">${escHtml(y.kuyou_star.level)}</span>
      </div>
      <div class="score-big" style="color:${scoreColor(y.fortune.overall)}">${y.fortune.overall}</div>
    </div>
    ${buildScoreBars(y.fortune)}
    <p style="color:#a8a29e;font-size:14px">守護佛：${escHtml(y.kuyou_star.buddha)}</p>`

  if (y.theme) {
    html += `<h4>${escHtml(y.theme.title)}</h4><p>${escHtml(y.theme.description)}</p>`
  }
  if (y.category_descriptions) {
    const cd = y.category_descriptions
    if (cd.career) html += `<h5>事業</h5><p>${escHtml(cd.career)}</p>`
    if (cd.love) html += `<h5>感情</h5><p>${escHtml(cd.love)}</p>`
    if (cd.health) html += `<h5>健康</h5><p>${escHtml(cd.health)}</p>`
    if (cd.wealth) html += `<h5>財運</h5><p>${escHtml(cd.wealth)}</p>`
  }
  if (y.advice) {
    html += `<h5>建議</h5><p>${escHtml(y.advice)}</p>`
  }
  html += '</div>'
  return html
}

function buildYearCardPractitioner(y: YearlyFortune): string {
  const s = y.shingon
  if (!s) return buildYearCardSecular(y)

  const levelColor = practiceLevelColor(s.practice_level)
  let html = `<div class="card">
    <div class="card-header">
      <div>
        <span class="card-year">${y.year}</span>
        <span class="card-star">${escHtml(y.kuyou_star.name)}</span>
        <span class="level-badge" style="background:${levelColor}22;color:${levelColor}">${escHtml(s.practice_name)}</span>
      </div>
      <div class="score-big" style="color:${scoreColor(y.fortune.overall)}">${y.fortune.overall}</div>
    </div>
    ${buildScoreBars(y.fortune, s.category_labels)}
    <p style="color:#a8a29e;font-size:14px">本尊：${escHtml(s.mantra.buddha)}</p>
    <div class="mantra-box">
      <p style="color:#a8a29e;font-size:12px">真言</p>
      <p class="mantra-text">${escHtml(s.mantra.text)}</p>
      <p class="mantra-reading">${escHtml(s.mantra.reading)}</p>
    </div>
    <div class="homa-box">
      <span class="homa-type">${escHtml(s.homa_type)}</span>
      <span>${escHtml(s.homa_description)}</span>
    </div>
    <p style="font-size:14px">修行重心：${escHtml(s.practice_focus)}</p>`

  if (s.theme) {
    html += `<h4>${escHtml(s.theme.title)}</h4><p>${escHtml(s.theme.description)}</p>`
  }
  if (s.core_teaching) {
    html += `<div class="card" style="margin:12px 0;background:#1c1917"><p>${escHtml(s.core_teaching)}</p></div>`
  }
  if (s.recommended_practices?.length) {
    html += `<h5>推薦修法</h5><div>${s.recommended_practices.map(p => `<span class="tag">${escHtml(p)}</span>`).join('')}</div>`
  }
  if (s.category_practice) {
    const cp = s.category_practice
    const cl = s.category_labels
    if (cp.career) html += `<h5>${escHtml(cl.career)}</h5><p>${escHtml(cp.career)}</p>`
    if (cp.love) html += `<h5>${escHtml(cl.love)}</h5><p>${escHtml(cp.love)}</p>`
    if (cp.health) html += `<h5>${escHtml(cl.health)}</h5><p>${escHtml(cp.health)}</p>`
    if (cp.wealth) html += `<h5>${escHtml(cl.wealth)}</h5><p>${escHtml(cp.wealth)}</p>`
  }

  // 月度修行提示
  if (s.monthly_tips && Object.keys(s.monthly_tips).length > 0) {
    html += `<h5>月度修行提示</h5><div class="monthly-grid">`
    for (let m = 1; m <= 12; m++) {
      const tip = s.monthly_tips[String(m)] || ''
      if (tip) {
        html += `<div class="monthly-cell"><span class="cell-month">${m}月</span><p class="cell-tip">${escHtml(tip)}</p></div>`
      }
    }
    html += '</div>'
  }

  if (s.opportunities?.length) {
    html += `<h5>修行好時機</h5><ul>${s.opportunities.map(o => `<li>${escHtml(o)}</li>`).join('')}</ul>`
  }
  if (s.warnings?.length) {
    html += `<h5>修行注意事項</h5><ul>${s.warnings.map(w => `<li>${escHtml(w)}</li>`).join('')}</ul>`
  }
  if (s.advice) {
    html += `<h5>教言</h5><p>${escHtml(s.advice)}</p>`
  }

  html += '</div>'
  return html
}

export function generateDecadeReport(options: DecadeReportOptions): void {
  const { yearlyRange, mansionName, mansionReading, mansionElement, birthDate, perspective } = options
  if (yearlyRange.length === 0) return

  const isPrac = perspective === 'practitioner'
  const startYear = yearlyRange[0].year
  const endYear = yearlyRange[yearlyRange.length - 1].year
  const perspLabel = isPrac ? '修行者觀' : '世俗觀'

  // 封面
  const cover = `<div class="cover">
    <h1>宿曜道 十年流年報告</h1>
    <p class="subtitle">${startYear} - ${endYear} | ${escHtml(perspLabel)}</p>
    <p class="mansion-name">${escHtml(mansionName)}（${escHtml(mansionElement)}）</p>
    <p class="mansion-reading">${escHtml(mansionReading)}</p>
    <p class="subtitle">出生日期：${escHtml(birthDate)} | 生成日期：${todayStr()}</p>
  </div>`

  // 九曜循環總覽
  const cycleGrid = yearlyRange.map(y => {
    const levelLabel = isPrac && y.shingon ? y.shingon.practice_name.replace('期', '') : y.kuyou_star.level
    const levelColor = isPrac && y.shingon ? practiceLevelColor(y.shingon.practice_level) : kuyouLevelColor(y.kuyou_star.level)
    const starShort = y.kuyou_star.name.replace('曜星', '').replace('星', '')
    return `<div class="kuyou-cell">
      <span class="cell-year">'${String(y.year).slice(-2)}</span>
      <span class="cell-star">${escHtml(starShort)}</span>
      <span class="cell-level" style="color:${levelColor}">${escHtml(levelLabel)}</span>
    </div>`
  }).join('')

  const chart = buildSvgChart(yearlyRange, isPrac)

  // 逐年卡片
  const yearCards = yearlyRange.map(y =>
    isPrac ? buildYearCardPractitioner(y) : buildYearCardSecular(y)
  ).join('')

  const html = `<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>宿曜道流年報告 ${startYear}-${endYear}</title>
<style>${getReportCSS()}</style>
</head>
<body>
${cover}
<h2>九曜循環總覽</h2>
<div class="kuyou-grid">${cycleGrid}</div>
${chart}
<hr class="section-divider">
<h2>逐年詳情</h2>
${yearCards}
<div class="footer">宿曜道 | ${todayStr()} 生成</div>
</body>
</html>`

  downloadHtml(html, `report-decade-${startYear}-${endYear}.html`)
}

// --- 相性報告 ---

const directionDesc: Record<string, string> = {
  '栄': '帶來好運和正能量的一方',
  '親': '親近感強、主動靠近的一方',
  '友': '主動給予、照顧的一方',
  '成': '被借力、提供價值的一方',
  '命': '本命共鳴',
  '衰': '被照顧、被影響的一方',
  '危': '帶來變化和風險的一方',
  '壊': '破壞既有模式的一方',
  '安': '被穩定、接受安撫的一方',
  '胎': '孕育可能性的一方',
  '業': '因果牽連深的一方'
}

const directionPairs: Record<string, string> = {
  '栄': '親', '親': '栄',
  '友': '衰', '衰': '友',
  '安': '壊', '壊': '安',
  '危': '成', '成': '危',
  '命': '命',
  '業': '胎', '胎': '業'
}

function getElementDescReport(el1: string, el2: string, calcRelation: string): string {
  if (el1 === el2) return `同為${el1}元素，能量共鳴互相增強`
  const genMap: Record<string, string> = { '木': '火', '火': '土', '土': '金', '金': '水', '水': '木' }
  if (calcRelation.includes('生')) {
    if (genMap[el2] === el1) return `${el2}生${el1} — 對方的能量自然滋養你`
    if (genMap[el1] === el2) return `${el1}生${el2} — 你的能量自然滋養對方`
  }
  const keMap: Record<string, string> = { '木': '土', '火': '金', '土': '水', '金': '木', '水': '火' }
  if (calcRelation.includes('剋')) {
    if (keMap[el1] === el2) return `${el1}剋${el2} — 你的能量壓制對方`
    if (keMap[el2] === el1) return `${el2}剋${el1} — 對方的能量壓制你`
  }
  return calcRelation
}

const elementColorMap: Record<string, string> = {
  '日': '#C4A052', '月': '#8B7355', '火': '#E85D4C',
  '水': '#5B8FA8', '木': '#7CB3D9', '金': '#E89B3C', '土': '#a8a29e'
}

export function generateCompatReport(compat: CompatibilityResult): void {
  const { person1, person2, relation, calculation, score, summary } = compat
  const sl = getScoreLevel(score)
  const inverseDir = relation.direction ? (directionPairs[relation.direction] || relation.direction) : null

  // 封面
  const cover = `<div class="cover">
    <h1>宿曜道 相性診斷報告</h1>
    <p class="subtitle">生成日期：${todayStr()}</p>
  </div>`

  // 雙方資料
  const personsSection = `<div class="persons-row">
    <div class="person-box">
      <h5>你</h5>
      <p class="mansion">${escHtml(person1.mansion)}</p>
      <span class="tag" style="background:${elementColorMap[person1.element] || '#a8a29e'}33;color:${elementColorMap[person1.element] || '#a8a29e'}">${escHtml(person1.element)}</span>
    </div>
    <div class="relation-box">
      <p class="relation-name">${escHtml(relation.name)}</p>
      <span class="relation-reading">${escHtml(relation.reading)}</span>
      ${relation.distance_type_name ? `<br><span class="distance-tag">${escHtml(relation.distance_type_name)}</span>` : ''}
    </div>
    <div class="person-box">
      <h5>對方</h5>
      <p class="mansion">${escHtml(person2.mansion)}</p>
      <span class="tag" style="background:${elementColorMap[person2.element] || '#a8a29e'}33;color:${elementColorMap[person2.element] || '#a8a29e'}">${escHtml(person2.element)}</span>
    </div>
  </div>`

  // 分數
  const scoreSection = `<div class="score-big" style="color:${scoreColor(score)};font-size:36px">${score}<span style="font-size:16px;margin-left:4px">${escHtml(sl.text)}</span></div>`

  // 方向
  let directionSection = ''
  if (relation.direction) {
    directionSection = `<h3>方向性</h3>
    <table class="direction-table">
      <tr><td class="label">你 → 對方</td><td>${escHtml(relation.direction)}</td><td>${escHtml(directionDesc[relation.direction] || '')}</td></tr>
      <tr><td class="label">對方 → 你</td><td>${escHtml(inverseDir || '')}</td><td>${escHtml(directionDesc[inverseDir || ''] || '')}</td></tr>
    </table>`
  }

  // 元素關係
  let elementSection = ''
  if (calculation) {
    const elDesc = getElementDescReport(person1.element, person2.element, calculation.element_relation)
    elementSection = `<h3>元素關係</h3>
    <p><span class="tag" style="background:${elementColorMap[person1.element] || '#a8a29e'}33;color:${elementColorMap[person1.element] || '#a8a29e'}">${escHtml(person1.element)}</span>
    → <span class="tag" style="background:${elementColorMap[person2.element] || '#a8a29e'}33;color:${elementColorMap[person2.element] || '#a8a29e'}">${escHtml(person2.element)}</span>
    ${escHtml(elDesc)}</p>`
  }

  // 詳細分析
  let detailSection = `<h2>分析</h2>
    <p>${escHtml(relation.description)}</p>
    <p>${escHtml(summary)}</p>`
  if (relation.detailed) {
    detailSection += `<p>${escHtml(relation.detailed)}</p>`
  }

  // 適合場景
  let goodForSection = ''
  if (relation.good_for?.length) {
    goodForSection = `<h3>適合場景</h3><div class="good-for-tags">${relation.good_for.map(g => `<span class="tag">${escHtml(g)}</span>`).join('')}</div>`
  }

  // 愛情 / 事業
  let aspectsSection = ''
  if (relation.love) aspectsSection += `<h3>愛情面向</h3><p>${escHtml(relation.love)}</p>`
  if (relation.career) aspectsSection += `<h3>事業面向</h3><p>${escHtml(relation.career)}</p>`

  // 角色指南
  let rolesSection = ''
  if (relation.roles && Object.keys(relation.roles).length) {
    const roleLabels: Record<string, string> = {
      colleague: '同事/工作夥伴', friend: '朋友', lover: '戀人/配偶', family: '家人'
    }
    rolesSection = `<h3>角色別相處指南</h3>` +
      Object.entries(relation.roles).map(([role, desc]) =>
        `<div class="card"><h4>${escHtml(roleLabels[role] || role)}</h4><p>${escHtml(desc)}</p></div>`
      ).join('')
  }

  // 建議 / tips / avoid
  let adviceSection = `<h2>相處建議</h2><p>${escHtml(relation.advice)}</p>`
  if (relation.tips?.length) {
    adviceSection += `<div class="tips-list"><h5>小技巧</h5><ul>${relation.tips.map(t => `<li>${escHtml(t)}</li>`).join('')}</ul></div>`
  }
  if (relation.avoid?.length) {
    adviceSection += `<div class="avoid-list"><h5>避免事項</h5><ul>${relation.avoid.map(a => `<li>${escHtml(a)}</li>`).join('')}</ul></div>`
  }

  const html = `<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>宿曜道相性報告 ${person1.mansion} x ${person2.mansion}</title>
<style>${getReportCSS()}</style>
</head>
<body>
${cover}
<h2>關係總覽</h2>
${personsSection}
${scoreSection}
${directionSection}
${elementSection}
<hr class="section-divider">
${detailSection}
${goodForSection}
${aspectsSection}
${rolesSection}
<hr class="section-divider">
${adviceSection}
<div class="footer">宿曜道 | ${todayStr()} 生成</div>
</body>
</html>`

  downloadHtml(html, `report-compat-${person1.mansion}-${person2.mansion}.html`)
}
