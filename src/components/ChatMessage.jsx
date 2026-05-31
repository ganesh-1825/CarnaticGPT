import React, { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import ConfidenceBadge from './ConfidenceBadge'
import SourceCard      from './SourceCard'
import RagaAudioPlayer from './RagaAudioPlayer'

const METHOD_BADGE = {
  ft:           { label:'Fine-tuned',  color:'#a78bfa' },
  ollama:       { label:'Ollama LLM',  color:'#34d399' },
  hf:           { label:'HuggingFace', color:'#60a5fa' },
  rule_based:   { label:'Extracted',   color:'#fbbf24' },
  no_results:   { label:'No results',  color:'#f87171' },
  rejected:     { label:'Rejected',    color:'#f87171' },
}

export default function ChatMessage({ message, msg: legacyMsg }) {
  const msg = message || legacyMsg;
  // ── Safe destructure — every field has a fallback ─────────────────────────
  const role             = msg?.role             ?? 'assistant'
  const content          = msg?.content          ?? ''
  const citations        = Array.isArray(msg?.citations) ? msg.citations : []
  const top_confidence   = msg?.top_confidence   ?? 0
  const confidence_label = msg?.confidence_label ?? null
  const audio            = msg?.audio            ?? null
  const synthesis_method = msg?.synthesis_method ?? null

  const isUser   = role === 'user'
  const isTyping = content === '__TYPING__'

  // Auto-expand sources when high confidence
  const [showSources, setShowSources] = useState(
    !isUser && citations.length > 0 && top_confidence >= 60
  )

  // Guard: if content is somehow null/undefined show fallback
  const displayContent = (!isTyping && !content)
    ? '(No answer generated — check backend logs)'
    : content

  return (
    <div style={{
      display: 'flex',
      flexDirection: isUser ? 'row-reverse' : 'row',
      gap: 10,
      alignItems: 'flex-start',
      animation: 'fadeUp .3s ease',
      maxWidth: '100%',
    }}>

      {/* Avatar */}
      <div style={{
        width: 32, height: 32, borderRadius: 9, flexShrink: 0,
        background: isUser
          ? 'linear-gradient(135deg,#3b82f6,#8b5cf6)'
          : 'linear-gradient(135deg,#8b5cf6,#ec4899)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 14, marginTop: 2,
        boxShadow: isUser ? '0 0 12px rgba(59,130,246,.3)' : '0 0 12px rgba(139,92,246,.3)',
      }}>
        {isUser ? '👤' : '🎵'}
      </div>

      {/* Bubble + extras */}
      <div style={{ maxWidth: 'calc(100% - 86px)', minWidth: 0 }}>

        {/* Message bubble */}
        <div
          className="chat-bubble"
          style={{
            padding: '12px 16px',
            borderRadius: isUser ? '16px 4px 16px 16px' : '4px 16px 16px 16px',
            background: isUser
              ? 'linear-gradient(135deg,rgba(59,130,246,.22),rgba(139,92,246,.22))'
              : 'var(--bg-card)',
            border: `1px solid ${isUser ? 'rgba(139,92,246,.35)' : 'var(--border)'}`,
            /* Explicit colour — prevents invisible-text-on-dark-bg bug */
            color: 'var(--text-primary)',
          }}
        >
          {isTyping ? (
            <div style={{ display:'flex', gap:5, alignItems:'center', padding:'4px 0' }}>
              <span className="typing-dot"/>
              <span className="typing-dot"/>
              <span className="typing-dot"/>
            </div>
          ) : (
            <div className="answer-content markdown-body" style={{
              fontSize: 14,
              lineHeight: 1.8,
              wordBreak: 'break-word',
              color: '#f1f5f9',
            }}>
              <ReactMarkdown
                components={{
                  a: ({node, ...props}) => <a {...props} target="_blank" rel="noopener noreferrer" style={{ color: '#60a5fa', textDecoration: 'none', fontWeight: 'bold' }} />
                }}
              >
                {displayContent}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Synthesis method badge — shown only on assistant messages */}
        {!isUser && !isTyping && synthesis_method && METHOD_BADGE[synthesis_method] && (
          <div style={{ marginTop: 5 }}>
            <span style={{
              fontSize: 10, padding: '2px 8px', borderRadius: 20,
              background: `${METHOD_BADGE[synthesis_method].color}18`,
              border: `0.5px solid ${METHOD_BADGE[synthesis_method].color}40`,
              color: METHOD_BADGE[synthesis_method].color,
              fontFamily: 'var(--font-mono)',
            }}>
              ⚙ {METHOD_BADGE[synthesis_method].label}
            </span>
          </div>
        )}

        {/* Audio player */}
        {audio?.found && <RagaAudioPlayer audioData={audio}/>}

        {/* Sources */}
        {!isUser && citations.length > 0 && !isTyping && (
          <div style={{ marginTop: 8 }}>
            <button
              onClick={() => setShowSources(s => !s)}
              style={{
                display: 'inline-flex', alignItems: 'center', gap: 6,
                padding: '5px 11px', borderRadius: 7,
                background: 'var(--bg-card)',
                border: '1px solid var(--border)',
                color: 'var(--text-secondary)',
                fontSize: 11.5,
                transition: 'var(--transition)',
              }}
              onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--border-bright)'}
              onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
            >
              📚 {citations.length} source{citations.length !== 1 ? 's' : ''}
              {top_confidence > 0 && (
                <span style={{ marginLeft: 4 }}>
                  <ConfidenceBadge score={top_confidence} label={confidence_label}/>
                </span>
              )}
              <span style={{ fontSize: 10 }}>{showSources ? '▲' : '▼'}</span>
            </button>

            {showSources && (
              <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 8 }}>
                {citations.map((c, i) => (
                  <SourceCard
                    key={`${c?.book_name ?? i}-${c?.page_number ?? i}-${i}`}
                    citation={c}
                    index={i}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
