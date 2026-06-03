import React from 'react'
import { CheckCircle2, Circle, Loader2, AlertTriangle } from 'lucide-react'

const ProgressTracker = ({ steps, currentStep }) => {
  if (!steps || steps.length === 0) return null

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 16 }}>
      {steps.map((step, idx) => {
        const { label, status } = step
        const isPending = status === 'pending'
        const isActive = status === 'active'
        const isDone = status === 'done'
        const isError = status === 'error'

        let icon = <Circle size={15} color="var(--border)" />
        let textColor = 'var(--text-muted)'
        let bgColor = 'transparent'
        let borderStyle = '1px solid transparent'

        if (isDone) {
          icon = <CheckCircle2 size={15} color="var(--peacock)" fill="rgba(139, 74, 54, 0.08)" />
          textColor = 'var(--peacock)'
        } else if (isActive) {
          icon = <Loader2 size={15} color="var(--peacock)" className="animate-spin" />
          textColor = 'var(--peacock)'
          bgColor = 'rgba(139, 74, 54, 0.04)'
          borderStyle = '1px solid var(--border)'
        } else if (isError) {
          icon = <AlertTriangle size={15} color="#ef4444" />
          textColor = '#ef4444'
          bgColor = 'rgba(239, 68, 68, 0.08)'
          borderStyle = '1px solid rgba(239, 68, 68, 0.15)'
        }

        return (
          <div
            key={idx}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '10px 16px',
              borderRadius: 4,
              background: bgColor,
              border: borderStyle,
              transition: 'all 0.2s ease',
              fontFamily: 'var(--font-sans)'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              {icon}
            </div>
            <span style={{ fontSize: 13, fontWeight: isActive || isDone ? 600 : 500, color: textColor, textTransform: 'uppercase', letterSpacing: '1px' }}>
              {label}
            </span>
          </div>
        )
      })}
    </div>
  )
}

export default ProgressTracker
