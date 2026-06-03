import React from 'react'

export default function ConfidenceBadge({ score, label }) {
  if (typeof score !== 'number') return null
  
  // Normalize score to [0, 1] range if it was passed in [0, 100] range
  const normalizedScore = score > 1.0 ? score / 100 : score
  
  let color = 'var(--text-muted)'
  let bg = 'var(--bg-surface-hover)'
  let displayLabel = label || 'Neutral'

  if (normalizedScore >= 0.8) {
    color = 'var(--emerald)'
    bg = 'rgba(16, 185, 129, 0.1)'
    displayLabel = label || 'High Confidence'
  } else if (normalizedScore >= 0.5) {
    color = 'var(--saffron)'
    bg = 'rgba(245, 158, 11, 0.1)'
    displayLabel = label || 'Medium Confidence'
  } else {
    color = 'var(--lotus-pink)'
    bg = 'rgba(236, 72, 153, 0.1)'
    displayLabel = label || 'Low Confidence'
  }

  const scorePct = Math.round(normalizedScore * 100)

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        fontSize: '11px',
        fontWeight: 800,
        fontFamily: 'var(--font-sans)',
        padding: '4px 10px',
        borderRadius: 'var(--radius-full)',
        background: bg,
        color: color,
        textTransform: 'uppercase',
        letterSpacing: '0.5px'
      }}
      title={`Confidence Score: ${scorePct}%`}
    >
      <span style={{ 
        width: 6, height: 6, borderRadius: '50%', background: color,
        boxShadow: `0 0 4px ${color}`
      }} />
      {displayLabel} ({scorePct}%)
    </span>
  )
}
