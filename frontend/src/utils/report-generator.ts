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
    excellent: '#9B7B1C',
    good: '#4a9b6b',
    fair: '#3b82f6',
    caution: '#9B7B1C',
    warning: '#ef4444'
  }
  return map[cls] || '#6B6560'
}

function kuyouLevelColor(level: string): string {
  if (level === '大吉') return '#9B7B1C'
  if (level === '吉') return '#4a9b6b'
  if (level === '半吉') return '#3b82f6'
  return '#ef4444'
}

function practiceLevelColor(level: string): string {
  if (level === '弘法') return '#9B7B1C'
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
      background: #F8F6F0; color: #2C2520;
      line-height: 1.7; padding: 24px; max-width: 800px; margin: 0 auto;
    }
    h1, h2, h3, h4, h5 { color: #2C2520; line-height: 1.4; }
    h1 { font-size: 24px; margin-bottom: 8px; }
    h2 { font-size: 20px; margin: 32px 0 12px; border-bottom: 1px solid #D5CFC5; padding-bottom: 8px; }
    h3 { font-size: 18px; margin: 24px 0 8px; }
    h4 { font-size: 16px; margin: 16px 0 6px; color: #8B6914; }
    h5 { font-size: 14px; margin: 12px 0 4px; color: #6B6560; }
    p { margin: 6px 0; }
    ul { padding-left: 20px; margin: 6px 0; }
    li { margin: 4px 0; }

    .cover { text-align: center; padding: 48px 0 32px; border-bottom: 2px solid #8B6914; margin-bottom: 32px; }
    .cover h1 { font-size: 28px; color: #8B6914; }
    .cover .subtitle { color: #6B6560; font-size: 14px; margin-top: 8px; }
    .cover .mansion-name { font-size: 20px; margin-top: 16px; }
    .cover .mansion-reading { color: #6B6560; font-size: 14px; }

    .card {
      background: #FFFFFF; border: 1px solid #D5CFC5; border-radius: 12px;
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
    .score-bar-label { width: 48px; font-size: 13px; color: #6B6560; text-align: right; flex-shrink: 0; }
    .score-bar { flex: 1; height: 8px; background: #F0EDE5; border-radius: 4px; overflow: hidden; }
    .score-bar-fill { height: 100%; border-radius: 4px; }
    .score-bar-value { width: 32px; font-size: 13px; text-align: right; flex-shrink: 0; }

    .kuyou-grid {
      display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; margin: 12px 0;
    }
    .kuyou-cell {
      background: #FFFFFF; border: 1px solid #D5CFC5; border-radius: 8px;
      padding: 8px; text-align: center; font-size: 13px;
    }
    .kuyou-cell .cell-year { display: block; color: #6B6560; font-size: 12px; }
    .kuyou-cell .cell-star { display: block; font-weight: 600; margin: 2px 0; }
    .kuyou-cell .cell-level { display: block; font-size: 11px; font-weight: 700; }

    .chart-container { margin: 16px 0; text-align: center; }
    .chart-container svg { max-width: 100%; height: auto; }

    .section-divider { border: none; border-top: 1px solid #D5CFC5; margin: 24px 0; }

    .mantra-box {
      background: #F8F6F0; border: 1px solid #D5CFC5; border-radius: 8px;
      margin: 8px 0; overflow: hidden;
    }
    .mantra-bija-section {
      display: flex; flex-direction: column; align-items: center; gap: 2px;
      padding: 16px 12px 8px; border-bottom: 1px solid #D5CFC5;
    }
    .bija-iast { font-size: 14px; color: #6B6560; font-style: italic; }
    .bija-reading { font-size: 12px; color: #6B6560; }
    .bija-buddha { font-size: 14px; font-weight: 700; color: #2C2520; }
    .mantra-text-section { padding: 8px 12px; text-align: center; }
    .mantra-text { font-size: 16px; letter-spacing: 2px; word-break: break-all; }
    .mantra-reading { color: #6B6560; font-size: 13px; margin-top: 4px; }

    .homa-box {
      display: flex; gap: 8px; align-items: baseline; margin: 8px 0;
      font-size: 14px;
    }
    .homa-type { font-weight: 700; color: #8B6914; }

    .tag { display: inline-block; background: #F0EDE5; border-radius: 9999px; padding: 2px 10px; font-size: 12px; margin: 2px 4px 2px 0; }

    .monthly-grid {
      display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; margin: 8px 0;
    }
    .monthly-cell {
      background: #F8F6F0; border: 1px solid #D5CFC5; border-radius: 6px;
      padding: 6px; font-size: 12px;
    }
    .monthly-cell .cell-month { font-weight: 600; }
    .monthly-cell .cell-tip { color: #6B6560; font-size: 11px; margin-top: 2px; }

    .persons-row { display: flex; gap: 16px; justify-content: center; align-items: center; margin: 16px 0; flex-wrap: wrap; }
    .person-box {
      background: #FFFFFF; border: 1px solid #D5CFC5; border-radius: 12px;
      padding: 16px; text-align: center; min-width: 120px;
    }
    .person-box h5 { color: #6B6560; margin-bottom: 4px; }
    .person-box .mansion { font-size: 18px; font-weight: 700; }
    .relation-box { text-align: center; }
    .relation-name { font-size: 18px; font-weight: 700; color: #8B6914; }
    .relation-reading { color: #6B6560; font-size: 13px; display: block; }
    .distance-tag { font-size: 12px; background: #F0EDE5; padding: 2px 8px; border-radius: 9999px; }

    .direction-table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 14px; }
    .direction-table td { padding: 6px 12px; border: 1px solid #D5CFC5; }
    .direction-table .label { color: #6B6560; width: 80px; }

    .tips-list, .avoid-list { margin: 8px 0; }
    .tips-list h5 { color: #4a9b6b; }
    .avoid-list h5 { color: #ef4444; }

    .good-for-tags { display: flex; flex-wrap: wrap; gap: 6px; margin: 8px 0; }

    .footer { text-align: center; color: #D5CFC5; font-size: 12px; margin-top: 48px; padding-top: 16px; border-top: 1px solid #D5CFC5; }

    @media print {
      body { background: #fff; color: #2C2520; padding: 12px; }
      h1, h2, h3, h4, h5, p, li, span, td { color: #2C2520 !important; }
      h4 { color: #92400e !important; }
      .cover h1 { color: #92400e !important; }
      .cover { border-bottom-color: #92400e; }
      .card { background: #fff; border-color: #D5CFC5; }
      .kuyou-cell { background: #fff; border-color: #D5CFC5; }
      .mantra-box { background: #f5f5f4; border-color: #D5CFC5; }
      .monthly-cell { background: #f5f5f4; border-color: #D5CFC5; }
      .person-box { background: #fff; border-color: #D5CFC5; }
      .score-bar { background: #e7e5e4; }
      .tag { background: #e7e5e4; }
      .distance-tag { background: #e7e5e4; }
      .footer { color: #6B6560 !important; border-top-color: #D5CFC5; }
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
    return `<line x1="${pl}" y1="${y}" x2="${w - pr}" y2="${y}" stroke="#D5CFC5" stroke-width="0.5" stroke-dasharray="${s % 20 === 0 ? '0' : '3,3'}"/>
      <text x="${pl - 6}" y="${y}" text-anchor="end" fill="#6B6560" font-size="11" dominant-baseline="middle">${s}</text>`
  }).join('')

  const path = yearlyRange
    .map((y, i) => `${i === 0 ? 'M' : 'L'}${toX(i).toFixed(1)},${toY(y.fortune.overall).toFixed(1)}`)
    .join(' ')

  const dots = yearlyRange.map((y, i) => {
    const x = toX(i).toFixed(1)
    const yPos = toY(y.fortune.overall).toFixed(1)
    const color = scoreColor(y.fortune.overall)
    return `<circle cx="${x}" cy="${yPos}" r="4" fill="${color}" stroke="#F8F6F0" stroke-width="2"/>
      <text x="${x}" y="${(parseFloat(yPos) - 10).toFixed(1)}" text-anchor="middle" fill="${color}" font-size="11" font-weight="600">${y.fortune.overall}</text>
      <text x="${x}" y="${h - 4}" text-anchor="middle" fill="#6B6560" font-size="11">${String(y.year).slice(-2)}</text>`
  }).join('')

  const bgTop = `<rect x="${pl}" y="${toY(100).toFixed(1)}" width="${cw}" height="${(toY(75) - toY(100)).toFixed(1)}" fill="rgba(80,180,80,0.08)"/>`
  const bgBot = `<rect x="${pl}" y="${toY(55).toFixed(1)}" width="${cw}" height="${(toY(minS) - toY(55)).toFixed(1)}" fill="${isPractitioner ? 'rgba(123,31,162,0.08)' : 'rgba(220,80,80,0.08)'}"/>`

  return `<div class="chart-container">
    <svg viewBox="0 0 ${w} ${h}" xmlns="http://www.w3.org/2000/svg">
      ${bgTop}${bgBot}${gridLines}
      <path d="${path}" fill="none" stroke="#8B6914" stroke-width="2"/>
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
    <p style="color:#6B6560;font-size:14px">守護佛：${escHtml(y.kuyou_star.buddha)}</p>`

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
    <div class="mantra-box">
      <div class="mantra-bija-section">
        ${s.mantra.siddham_roman ? `<span class="bija-iast">${escHtml(s.mantra.siddham_roman)}</span>` : ''}
        ${s.mantra.siddham_bija ? `<span class="bija-reading">${escHtml(s.mantra.siddham_bija)}</span>` : ''}
        <span class="bija-buddha">${escHtml(s.mantra.buddha)}</span>
      </div>
      <div class="mantra-text-section">
        <p style="color:#7b1fa2;font-size:12px;font-weight:600">真言</p>
        <p class="mantra-text">${escHtml(s.mantra.text)}</p>
        <p class="mantra-reading">${escHtml(s.mantra.reading)}</p>
      </div>
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
    html += `<div class="card" style="margin:12px 0;background:#F8F6F0"><p>${escHtml(s.core_teaching)}</p></div>`
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
  const startYear = yearlyRange[0]!.year
  const endYear = yearlyRange[yearlyRange.length - 1]!.year
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
  '壊': '破壊既有模式的一方',
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
  '水': '#5B8FA8', '木': '#7CB3D9', '金': '#E89B3C', '土': '#6B6560'
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
      <span class="tag" style="background:${elementColorMap[person1.element] || '#6B6560'}33;color:${elementColorMap[person1.element] || '#6B6560'}">${escHtml(person1.element)}</span>
    </div>
    <div class="relation-box">
      <p class="relation-name">${escHtml(relation.name)}</p>
      <span class="relation-reading">${escHtml(relation.reading)}</span>
      ${relation.distance_type_name ? `<br><span class="distance-tag">${escHtml(relation.distance_type_name)}</span>` : ''}
    </div>
    <div class="person-box">
      <h5>對方</h5>
      <p class="mansion">${escHtml(person2.mansion)}</p>
      <span class="tag" style="background:${elementColorMap[person2.element] || '#6B6560'}33;color:${elementColorMap[person2.element] || '#6B6560'}">${escHtml(person2.element)}</span>
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
    <p><span class="tag" style="background:${elementColorMap[person1.element] || '#6B6560'}33;color:${elementColorMap[person1.element] || '#6B6560'}">${escHtml(person1.element)}</span>
    → <span class="tag" style="background:${elementColorMap[person2.element] || '#6B6560'}33;color:${elementColorMap[person2.element] || '#6B6560'}">${escHtml(person2.element)}</span>
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

// --- 雙人流年報告 ---

interface PairedDecadeReportOptions {
  person1: { mansion: string; reading: string; element: string; date: string; name: string }
  person2: { mansion: string; reading: string; element: string; date: string; name: string }
  compat: {
    score: number
    relationName: string
    reading: string
    distanceTypeName?: string
    elementRelation: string
    direction?: string
    summary: string
  }
  apiUrl: string
}

function buildDualLineSvg(
  p1Data: YearlyFortune[],
  p2Data: YearlyFortune[],
  _p1Name: string,
  _p2Name: string,
  field: 'overall' | 'career' | 'wealth' = 'overall'
): string {
  if (p1Data.length < 2) return ''
  const w = 700, h = 240
  const pl = 55, pr = 35, pt = 30, pb = 28
  const cw = w - pl - pr, ch = h - pt - pb
  const minS = 30, maxS = 100
  const toY = (s: number) => pt + ch - ((s - minS) / (maxS - minS)) * ch
  const toX = (i: number) => pl + (i / (p1Data.length - 1)) * cw

  const gridLines = [40, 55, 70, 85, 100].map(s => {
    const y = toY(s).toFixed(1)
    return `<line x1="${pl}" y1="${y}" x2="${w - pr}" y2="${y}" stroke="#D5CFC5" stroke-width="0.5" stroke-dasharray="${s === 55 || s === 70 ? '0' : '3,3'}"/>
      <text x="${pl - 6}" y="${y}" text-anchor="end" fill="#6B6560" font-size="10" dominant-baseline="middle">${s}</text>`
  }).join('')

  const bgTop = `<rect x="${pl}" y="${toY(100).toFixed(1)}" width="${cw}" height="${(toY(75) - toY(100)).toFixed(1)}" fill="rgba(74,155,107,0.06)" rx="2"/>`
  const bgBot = `<rect x="${pl}" y="${toY(55).toFixed(1)}" width="${cw}" height="${(toY(minS) - toY(55)).toFixed(1)}" fill="rgba(239,68,68,0.06)" rx="2"/>`

  const getScore = (y: YearlyFortune) => {
    if (field === 'career') return y.fortune.career
    if (field === 'wealth') return y.fortune.wealth
    return y.fortune.overall
  }

  const path1 = p1Data.map((y, i) => `${i === 0 ? 'M' : 'L'}${toX(i).toFixed(1)},${toY(getScore(y)).toFixed(1)}`).join(' ')
  const path2 = p2Data.map((y, i) => `${i === 0 ? 'M' : 'L'}${toX(i).toFixed(1)},${toY(getScore(y)).toFixed(1)}`).join(' ')

  const dots1 = p1Data.map((y, i) => {
    const x = toX(i).toFixed(1), yp = toY(getScore(y)).toFixed(1)
    return `<circle cx="${x}" cy="${yp}" r="4" fill="#8B6914" stroke="#F8F6F0" stroke-width="2"/>
      <text x="${x}" y="${(parseFloat(yp) - 10).toFixed(1)}" text-anchor="middle" fill="#8B6914" font-size="11" font-weight="600">${getScore(y)}</text>`
  }).join('')

  const dots2 = p2Data.map((y, i) => {
    const x = toX(i).toFixed(1), yp = toY(getScore(y)).toFixed(1)
    return `<circle cx="${x}" cy="${yp}" r="4" fill="#7CB3D9" stroke="#F8F6F0" stroke-width="2"/>
      <text x="${x}" y="${(parseFloat(yp) + 18).toFixed(1)}" text-anchor="middle" fill="#7CB3D9" font-size="11" font-weight="600">${getScore(y)}</text>`
  }).join('')

  const xLabels = p1Data.map((y, i) =>
    `<text x="${toX(i).toFixed(1)}" y="${h - 4}" text-anchor="middle" fill="#6B6560" font-size="11">${y.year}</text>`
  ).join('')

  return `<div class="chart-container">
    <svg viewBox="0 0 ${w} ${h}" xmlns="http://www.w3.org/2000/svg">
      ${bgTop}${bgBot}${gridLines}
      <path d="${path1}" fill="none" stroke="#8B6914" stroke-width="2.5" stroke-linejoin="round"/>
      <path d="${path2}" fill="none" stroke="#7CB3D9" stroke-width="2.5" stroke-linejoin="round"/>
      ${dots1}${dots2}${xLabels}
    </svg>
  </div>`
}

function buildDualMonthlyChart(p1Monthly: { month: number; score: number }[], p2Monthly: { month: number; score: number }[]): string {
  const w = 700, h = 180
  const pl = 55, pr = 35, pt = 25, pb = 28
  const cw = w - pl - pr, ch = h - pt - pb
  const minS = 30, maxS = 100
  const toY = (s: number) => pt + ch - ((s - minS) / (maxS - minS)) * ch
  const toX = (i: number) => pl + (i / 11) * cw

  const gridLines = [40, 60, 80, 100].map(s => {
    const y = toY(s).toFixed(1)
    return `<line x1="${pl}" y1="${y}" x2="${w - pr}" y2="${y}" stroke="#D5CFC5" stroke-width="0.5" stroke-dasharray="3,3"/>
      <text x="${pl - 6}" y="${y}" text-anchor="end" fill="#6B6560" font-size="9" dominant-baseline="middle">${s}</text>`
  }).join('')

  const path1 = p1Monthly.map((m, i) => `${i === 0 ? 'M' : 'L'}${toX(i).toFixed(1)},${toY(m.score).toFixed(1)}`).join(' ')
  const path2 = p2Monthly.map((m, i) => `${i === 0 ? 'M' : 'L'}${toX(i).toFixed(1)},${toY(m.score).toFixed(1)}`).join(' ')

  const xLabels = p1Monthly.map((m, i) =>
    `<text x="${toX(i).toFixed(1)}" y="${h - 4}" text-anchor="middle" fill="#6B6560" font-size="10">${m.month}月</text>`
  ).join('')

  return `<div class="chart-container">
    <svg viewBox="0 0 ${w} ${h}" xmlns="http://www.w3.org/2000/svg">
      ${gridLines}
      <path d="${path1}" fill="none" stroke="#8B6914" stroke-width="2" stroke-linejoin="round"/>
      <path d="${path2}" fill="none" stroke="#7CB3D9" stroke-width="2" stroke-linejoin="round"/>
      ${xLabels}
    </svg>
  </div>`
}

function getPairedReportCSS(): string {
  return `
    .profile-row { display: flex; gap: 16px; margin-bottom: 24px; }
    .profile-card {
      flex: 1; padding: 16px; background: #FFFFFF; border: 1px solid #D5CFC5;
      border-radius: 12px; text-align: center;
    }
    .profile-card .name { font-size: 18px; font-weight: 700; }
    .profile-card .mansion { font-size: 24px; font-weight: 700; margin: 8px 0 4px; }
    .profile-card .detail { font-size: 13px; color: #6B6560; }
    .profile-card .element-badge {
      display: inline-block; padding: 2px 10px; border-radius: 4px;
      color: #2C2520; font-weight: 600; font-size: 13px; margin-top: 4px;
    }
    .compat-box {
      background: #FFFFFF; border: 1px solid #D5CFC5; border-radius: 12px;
      padding: 16px; text-align: center; margin-bottom: 24px;
    }
    .compat-score-big { font-size: 48px; font-weight: 700; }
    .compat-label { font-size: 14px; color: #6B6560; }
    .legend {
      display: flex; gap: 24px; justify-content: center; margin: 12px 0 20px;
      font-size: 13px; color: #6B6560; flex-wrap: wrap;
    }
    .legend-item { display: flex; align-items: center; gap: 6px; }
    .legend-line { display: inline-block; width: 24px; height: 3px; border-radius: 2px; }
    .insight-box {
      background: #FFFFFF; border: 1px solid #D5CFC5; border-radius: 12px;
      padding: 20px; margin: 20px 0;
    }
    .insight-box h3 { margin-top: 0; color: #8B6914; }
    .insight-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 12px; }
    .insight-card { background: #F0EDE5; border-radius: 8px; padding: 12px; text-align: center; }
    .insight-card .ic-label { font-size: 12px; color: #6B6560; }
    .insight-card .ic-value { font-size: 20px; font-weight: 700; margin: 4px 0; }
    .insight-card .ic-desc { font-size: 12px; color: #D5CFC5; }
    .year-section {
      background: #FFFFFF; border: 1px solid #D5CFC5; border-radius: 12px;
      padding: 20px; margin-bottom: 20px;
    }
    .year-header {
      display: flex; justify-content: space-between; align-items: center;
      margin-bottom: 8px; flex-wrap: wrap; gap: 8px;
    }
    .year-title { font-size: 18px; font-weight: 700; }
    .year-tags { display: flex; gap: 8px; flex-wrap: wrap; }
    .tag-gold { background: #9B7B1C; color: #FFFFFF; }
    .tag-green { background: #2D7A4F; color: #FFFFFF; }
    .tag-blue { background: #3b82f6; color: #fff; }
    .tag-red { background: #ef4444; color: #fff; }
    .tag-gray { background: #D5CFC5; color: #2C2520; }
    table { width: 100%; border-collapse: collapse; margin-bottom: 16px; font-size: 13px; }
    th, td { padding: 8px 10px; text-align: center; border-bottom: 1px solid #F0EDE5; }
    th { color: #6B6560; font-weight: 600; font-size: 12px; }
    td { color: #D5CFC5; }
    .score-great { color: #9B7B1C; font-weight: 700; }
    .score-good { color: #4a9b6b; font-weight: 600; }
    .score-fair { color: #3b82f6; }
    .score-bad { color: #ef4444; font-weight: 700; }
    .row-highlight { background: rgba(139, 105, 20, 0.06); }
    .year-advice {
      margin-top: 12px; padding: 12px 16px;
      background: #F0EDE5; border-radius: 8px; border-left: 3px solid #D5CFC5;
    }
    .year-advice p { margin-bottom: 4px; }
    @media (max-width: 600px) {
      .profile-row { flex-direction: column; }
      .compat-score-big { font-size: 36px; }
      table { font-size: 11px; }
      th, td { padding: 6px 4px; }
      .year-header { flex-direction: column; align-items: flex-start; }
      .insight-grid { grid-template-columns: 1fr; }
    }
    @media print {
      .profile-card { background: #fff; border-color: #D5CFC5; }
      .compat-box { background: #fff; border-color: #D5CFC5; }
      .insight-box { background: #fff; border-color: #D5CFC5; }
      .insight-card { background: #f5f5f4; }
      .year-section { background: #fff; border-color: #D5CFC5; page-break-inside: avoid; }
      .year-advice { background: #f5f5f4; }
      th { border-bottom-color: #D5CFC5; }
      td { border-bottom-color: #e7e5e4; }
    }
  `
}

function kuyouTagClass(level: string): string {
  if (level === '大吉') return 'tag-gold'
  if (level === '吉') return 'tag-green'
  if (level === '半吉') return 'tag-blue'
  return 'tag-red'
}

function tableScoreClass(score: number): string {
  if (score >= 90) return 'score-great'
  if (score >= 70) return 'score-good'
  if (score >= 55) return 'score-fair'
  return 'score-bad'
}

export async function generatePairedDecadeReport(options: PairedDecadeReportOptions): Promise<void> {
  const { person1, person2, compat, apiUrl } = options

  const currentYear = new Date().getFullYear()
  const startYear = currentYear - 2
  const endYear = currentYear + 7

  // 平行呼叫兩人 yearly-range API
  const [res1, res2] = await Promise.all([
    fetch(`${apiUrl}/fortune/yearly-range?birth_date=${person1.date}&start_year=${startYear}&end_year=${endYear}`),
    fetch(`${apiUrl}/fortune/yearly-range?birth_date=${person2.date}&start_year=${startYear}&end_year=${endYear}`)
  ])
  if (!res1.ok || !res2.ok) throw new Error('API 呼叫失敗')
  const p1Raw = await res1.json()
  const p2Raw = await res2.json()
  const p1Data: YearlyFortune[] = p1Raw.data ?? p1Raw
  const p2Data: YearlyFortune[] = p2Raw.data ?? p2Raw

  // 互補分析
  const lowThreshold = 55
  const highThreshold = 70
  const p1LowYears = p1Data.filter(y => y.fortune.overall < lowThreshold).map(y => y.year)
  const p2LowYears = p2Data.filter(y => y.fortune.overall < lowThreshold).map(y => y.year)
  const bothLowYears = p1LowYears.filter(y => p2LowYears.includes(y))
  const p1CarriedYears: number[] = []
  const p2CarriedYears: number[] = []
  p1Data.forEach((y1, i) => {
    const y2 = p2Data[i]
    if (!y2) return
    if (y1.fortune.overall < lowThreshold && y2.fortune.overall >= highThreshold) p2CarriedYears.push(y1.year)
    if (y2.fortune.overall < lowThreshold && y1.fortune.overall >= highThreshold) p1CarriedYears.push(y1.year)
  })

  // 封面
  const cover = `<div class="cover">
    <h1>宿曜道 雙人十年流年報告</h1>
    <p class="subtitle">${startYear} - ${endYear} | 生成日期：${todayStr()}</p>
  </div>`

  // 雙方 profile
  const profiles = `<div class="profile-row">
    <div class="profile-card">
      <div class="name" style="color:#8B6914;">${escHtml(person1.name)}</div>
      <div class="mansion">${escHtml(person1.mansion)}</div>
      <div class="detail">${escHtml(person1.reading)} | ${escHtml(person1.date)}</div>
      <span class="element-badge" style="background:${elementColorMap[person1.element] || '#6B6560'}">${escHtml(person1.element)}</span>
    </div>
    <div class="profile-card">
      <div class="name" style="color:#7CB3D9;">${escHtml(person2.name)}</div>
      <div class="mansion">${escHtml(person2.mansion)}</div>
      <div class="detail">${escHtml(person2.reading)} | ${escHtml(person2.date)}</div>
      <span class="element-badge" style="background:${elementColorMap[person2.element] || '#6B6560'}">${escHtml(person2.element)}</span>
    </div>
  </div>`

  // 相性摘要
  const compatBox = `<div class="compat-box">
    <div class="compat-score-big" style="color:${scoreColor(compat.score)}">${compat.score}</div>
    <div class="compat-label">${escHtml(compat.relationName)}（${escHtml(compat.reading)}）${compat.distanceTypeName ? ' | ' + escHtml(compat.distanceTypeName) : ''}</div>
    <div style="margin-top:8px;">
      <span class="tag ${compat.elementRelation.includes('生') ? 'tag-green' : compat.elementRelation.includes('剋') ? 'tag-red' : 'tag-gray'}">${escHtml(compat.elementRelation)}</span>
      ${compat.direction ? `<span class="tag tag-blue">${escHtml(person1.name)}→${escHtml(person2.name)}: ${escHtml(compat.direction)}</span>` : ''}
    </div>
    <p style="margin-top:12px; font-size:13px;">${escHtml(compat.summary)}</p>
  </div>`

  // 雙線走勢圖
  const legend = `<div class="legend">
    <span class="legend-item"><span class="legend-line" style="background:#8B6914;"></span> ${escHtml(person1.name)}（${escHtml(person1.mansion)}）</span>
    <span class="legend-item"><span class="legend-line" style="background:#7CB3D9;"></span> ${escHtml(person2.name)}（${escHtml(person2.mansion)}）</span>
    <span class="legend-item" style="font-size:11px; color:#78716c;">綠底 = 順運區(>75) | 紅底 = 警戒區(<55)</span>
  </div>`
  const mainChart = buildDualLineSvg(p1Data, p2Data, person1.name, person2.name)

  // 分數對照表
  let tableRows = ''
  p1Data.forEach((y1, i) => {
    const y2 = p2Data[i]
    if (!y2) return
    const isHighlight = y1.fortune.overall >= 75 || y2.fortune.overall >= 75 || bothLowYears.includes(y1.year)
    tableRows += `<tr${isHighlight ? ' class="row-highlight"' : ''}>
      <td><strong>${y1.year}</strong></td>
      <td><span class="tag ${kuyouTagClass(y1.kuyou_star.level)}">${escHtml(y1.kuyou_star.name.replace('曜星', ''))}</span></td>
      <td class="${tableScoreClass(y1.fortune.overall)}">${y1.fortune.overall}</td>
      <td class="${tableScoreClass(y1.fortune.career)}">${y1.fortune.career}</td>
      <td class="${tableScoreClass(y1.fortune.wealth)}">${y1.fortune.wealth}</td>
      <td><span class="tag ${kuyouTagClass(y2.kuyou_star.level)}">${escHtml(y2.kuyou_star.name.replace('曜星', ''))}</span></td>
      <td class="${tableScoreClass(y2.fortune.overall)}">${y2.fortune.overall}</td>
      <td class="${tableScoreClass(y2.fortune.career)}">${y2.fortune.career}</td>
      <td class="${tableScoreClass(y2.fortune.wealth)}">${y2.fortune.wealth}</td>
    </tr>`
  })
  const scoreTable = `<table>
    <thead><tr>
      <th>年</th>
      <th>${escHtml(person1.name)} / 九曜</th><th>總運</th><th>事業</th><th>財運</th>
      <th>${escHtml(person2.name)} / 九曜</th><th>總運</th><th>事業</th><th>財運</th>
    </tr></thead>
    <tbody>${tableRows}</tbody>
  </table>`

  // 互補分析
  const insightBox = `<div class="insight-box">
    <h3>互補結構分析</h3>
    <div class="insight-grid">
      <div class="insight-card">
        <div class="ic-label">${escHtml(person1.name)} 扛 ${escHtml(person2.name)}</div>
        <div class="ic-value" style="color:#8B6914;">${p1CarriedYears.length} 年</div>
        <div class="ic-desc">${p1CarriedYears.length > 0 ? p1CarriedYears.join(', ') : '無'}</div>
      </div>
      <div class="insight-card">
        <div class="ic-label">${escHtml(person2.name)} 扛 ${escHtml(person1.name)}</div>
        <div class="ic-value" style="color:#7CB3D9;">${p2CarriedYears.length} 年</div>
        <div class="ic-desc">${p2CarriedYears.length > 0 ? p2CarriedYears.join(', ') : '無'}</div>
      </div>
      <div class="insight-card">
        <div class="ic-label">同時低谷</div>
        <div class="ic-value" style="color:${bothLowYears.length > 0 ? '#ef4444' : '#4a9b6b'};">${bothLowYears.length} 年</div>
        <div class="ic-desc">${bothLowYears.length > 0 ? bothLowYears.join(', ') : '無'}</div>
      </div>
    </div>
  </div>`

  // 逐年區塊
  const yearSections = p1Data.map((y1, i) => {
    const y2 = p2Data[i]
    if (!y2) return ''

    const monthlyChart = buildDualMonthlyChart(
      y1.monthly_trend,
      y2.monthly_trend
    )

    let adviceHtml = ''
    if (y1.theme || y2.theme) {
      adviceHtml = '<div class="year-advice">'
      if (y1.theme) adviceHtml += `<p><strong style="color:#8B6914;">${escHtml(person1.name)}</strong>：${escHtml(y1.theme.title)} — ${escHtml(y1.theme.description)}</p>`
      if (y2.theme) adviceHtml += `<p><strong style="color:#7CB3D9;">${escHtml(person2.name)}</strong>：${escHtml(y2.theme.title)} — ${escHtml(y2.theme.description)}</p>`
      adviceHtml += '</div>'
    }

    let yearAdvice = ''
    if (y1.advice || y2.advice) {
      yearAdvice = '<div class="year-advice" style="border-left-color:#4a9b6b;">'
      if (y1.advice) yearAdvice += `<p><strong style="color:#8B6914;">${escHtml(person1.name)}</strong>：${escHtml(y1.advice)}</p>`
      if (y2.advice) yearAdvice += `<p><strong style="color:#7CB3D9;">${escHtml(person2.name)}</strong>：${escHtml(y2.advice)}</p>`
      yearAdvice += '</div>'
    }

    return `<div class="year-section">
      <div class="year-header">
        <span class="year-title">${y1.year}</span>
        <div class="year-tags">
          <span class="tag ${kuyouTagClass(y1.kuyou_star.level)}">${escHtml(person1.name)}: ${escHtml(y1.kuyou_star.name)} (${escHtml(y1.kuyou_star.level)})</span>
          <span class="tag ${kuyouTagClass(y2.kuyou_star.level)}">${escHtml(person2.name)}: ${escHtml(y2.kuyou_star.name)} (${escHtml(y2.kuyou_star.level)})</span>
        </div>
      </div>
      <h4 style="color:#6B6560; font-size:13px;">月運走勢</h4>
      ${monthlyChart}
      ${adviceHtml}
      ${yearAdvice}
    </div>`
  }).join('')

  const html = `<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>宿曜道雙人流年報告 ${startYear}-${endYear}</title>
<style>${getReportCSS()}${getPairedReportCSS()}</style>
</head>
<body>
${cover}
${profiles}
${compatBox}
<h2>十年總運走勢</h2>
${legend}
${mainChart}
${scoreTable}
${insightBox}
<hr class="section-divider">
<h2>逐年詳情</h2>
${yearSections}
<div class="footer">宿曜道 | ${todayStr()} 生成</div>
</body>
</html>`

  downloadHtml(html, `report-paired-${startYear}-${endYear}.html`)
}

