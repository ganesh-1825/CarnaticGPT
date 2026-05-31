import React from 'react'

const ConfidenceBadge = ({ score }) => {
  if (score == null) return null

  let label = ''
  let color = 'var(--gold)'
  let bg = 'var(--gold-pale)'
  let border = 'rgba(200, 146, 42, 0.2)'

  if (typeof score === 'string') {
    label = score
    if (score.toLowerCase().includes('high')) {
      color = 'var(--teal)'
      bg = 'var(--teal-pale)'
      border = 'rgba(26, 122, 106, 0.2)'
    } else if (score.toLowerCase().includes('low')) {
      color = 'var(--red-deep)'
      bg = 'var(--red-pale)'
      border = 'rgba(139, 32, 32, 0.2)'
    }
  } else {
    // Score is a number (e.g. 0-1 or 0-100)
    const pct = score <= 1 ? score * 100 : score
    label = `${pct.toFixed(0)}%`
    if (pct >= 80) {
      color = 'var(--teal)'
      bg = 'var(--teal-pale)'
      border = 'rgba(26, 122, 106, 0.2)'
    } else if (pct < 50) {
      color = 'var(--red-deep)'
      bg = 'var(--red-pale)'
      border = 'rgba(139, 32, 32, 0.2)'
    }
  }

  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      padding: '2px 8px',
      borderRadius: 12,
      fontSize: 10.5,
      fontWeight: 600,
      color,
      background: bg,
      border: `1px solid ${border}`,
      textTransform: 'uppercase',
      letterSpacing: '0.03em',
      lineHeight: 1,
    }}>
      {label}
    </span>
  )
}

export default ConfidenceBadge
