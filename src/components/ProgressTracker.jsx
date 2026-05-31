import React from 'react'
import { CheckCircle2, Circle, Loader2, AlertTriangle } from 'lucide-react'

const ProgressTracker = ({ steps, currentStep }) => {
  if (!steps || steps.length === 0) return null

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 12 }}>
      {steps.map((step, idx) => {
        const { label, status } = step
        const isPending = status === 'pending'
        const isActive = status === 'active'
        const isDone = status === 'done'
        const isError = status === 'error'

        let icon = <Circle size={15} color="rgba(255, 255, 255, 0.2)" />
        let textColor = 'rgba(255, 255, 255, 0.45)'
        let bgColor = 'transparent'
        let borderStyle = '1px solid transparent'

        if (isDone) {
          icon = <CheckCircle2 size={15} color="rgba(22, 219, 204, 1)" fill="rgba(22, 219, 204, 0.15)" />
          textColor = 'rgba(22, 219, 204, 1)'
        } else if (isActive) {
          icon = <Loader2 size={15} color="var(--gold)" className="animate-spin" />
          textColor = 'var(--gold)'
          bgColor = 'rgba(200, 146, 42, 0.08)'
          borderStyle = '1px solid rgba(200, 146, 42, 0.25)'
        } else if (isError) {
          icon = <AlertTriangle size={15} color="#ef4444" />
          textColor = '#fca5a5'
          bgColor = 'rgba(239, 68, 68, 0.08)'
          borderStyle = '1px solid rgba(239, 68, 68, 0.25)'
        }

        return (
          <div
            key={idx}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '10px 14px',
              borderRadius: 10,
              background: bgColor,
              border: borderStyle,
              transition: 'all 0.2s ease',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              {icon}
            </div>
            <span style={{ fontSize: 13, fontWeight: isActive || isDone ? 500 : 400, color: textColor }}>
              {label}
            </span>
          </div>
        )
      })}
    </div>
  )
}

export default ProgressTracker
