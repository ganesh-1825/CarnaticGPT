import React, { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import ConfidenceBadge from './ConfidenceBadge'
import SourceCard      from './SourceCard'
import RagaAudioPlayer from './RagaAudioPlayer'
import TTSPlayer       from './TTSPlayer'
import { Play, Volume2, Bookmark, Check } from 'lucide-react'

// Simple text-to-speech for ragas if needed
const playTTS = (text) => {
  if (!('speechSynthesis' in window)) return
  window.speechSynthesis.cancel()
  const u = new SpeechSynthesisUtterance(text)
  u.lang = 'en-IN'
  u.rate = 0.9
  window.speechSynthesis.speak(u)
}

export default function ChatMessage({ 
  msg, 
  msgIndex, 
  isLatest, 
  autoPlayTTS, 
  activeAudioId, 
  setActiveAudioId 
}) {
  const isUser = msg.role === 'user'
  const isTyping = msg.content === '__TYPING__'
  const [showSources, setShowSources] = useState(false)
  const [bookmarked, setBookmarked] = useState(false)
  const [showTTSPlayer, setShowTTSPlayer] = useState(false)

  const audioId = msg.id ? String(msg.id) : `msg-${msgIndex}`

  // Automatically trigger voice response if autoPlayTTS preference is enabled
  useEffect(() => {
    if (!isUser && !isTyping && isLatest && autoPlayTTS) {
      setShowTTSPlayer(true)
      setActiveAudioId(audioId)
    }
  }, [isLatest, autoPlayTTS, isUser, isTyping, audioId])

  // Reveal effect for AI messages
  const [revealed, setRevealed] = useState(isUser)
  useEffect(() => {
    if (!isUser) {
      const timer = setTimeout(() => setRevealed(true), 100)
      return () => clearTimeout(timer)
    }
  }, [isUser])

  if (isUser) {
    return (
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 32, opacity: revealed ? 1 : 0, transform: revealed ? 'translateY(0)' : 'translateY(10px)', transition: 'all 0.4s ease-out' }}>
        <div style={{
          background: 'var(--peacock)',
          color: '#fff',
          padding: '16px 24px',
          borderRadius: 'var(--radius-lg)',
          borderBottomRightRadius: '4px',
          maxWidth: '80%',
          fontSize: 16,
          fontFamily: 'var(--font-sans)',
          lineHeight: 1.6,
          boxShadow: 'var(--shadow-md)',
          fontWeight: 600
        }}>
          {msg.content}
        </div>
      </div>
    )
  }

  // Assistant typing state
  if (isTyping) {
    return (
      <div style={{ display: 'flex', marginBottom: 40 }}>
        <div style={{
          width: 48, height: 48, borderRadius: 'var(--radius-full)', flexShrink: 0,
          background: 'var(--saffron)', color: '#fff',
          display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 24,
          marginRight: 20, boxShadow: 'var(--shadow-sm)'
        }}>
          🪕
        </div>
        <div className="elevated-card" style={{
          borderTopLeftRadius: '4px',
          padding: '20px 24px', display: 'flex', alignItems: 'center', gap: 6,
        }}>
          <span className="typing-dot" />
          <span className="typing-dot" />
          <span className="typing-dot" />
        </div>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', marginBottom: 40, opacity: revealed ? 1 : 0, transform: revealed ? 'translateY(0)' : 'translateY(10px)', transition: 'all 0.5s cubic-bezier(0.2, 0.8, 0.2, 1)' }}>
      
      {/* Avatar */}
      <div style={{
        width: 48, height: 48, borderRadius: 'var(--radius-full)', flexShrink: 0,
        background: 'var(--saffron)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 24, color: '#fff',
        marginRight: 20, boxShadow: 'var(--shadow-sm)', fontWeight: 800, fontFamily: 'var(--font-sans)'
      }}>
        C
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div className="elevated-card" style={{
          padding: '32px', borderTopLeftRadius: '4px', position: 'relative'
        }}>
          
          {/* Top Metadata Row */}
          {msg.top_confidence > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24, borderBottom: '1px solid var(--border)', paddingBottom: 16 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <span style={{ fontSize: 13, fontWeight: 800, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px', fontFamily: 'var(--font-sans)' }}>
                  Synthesized Answer
                </span>
                <ConfidenceBadge score={msg.top_confidence} label={msg.confidence_label} />
              </div>
              
              <div style={{ display: 'flex', gap: 8 }}>
                <button title="Save Answer" onClick={() => setBookmarked(!bookmarked)} className="btn-icon" style={{ width: 36, height: 36, border: 'none', background: 'transparent', boxShadow: 'none' }}>
                  {bookmarked ? <Check size={18} color="var(--emerald)" /> : <Bookmark size={18} />}
                </button>
              </div>
            </div>
          )}

          {/* Main Content */}
          <div className="markdown-body" style={{
            color: 'var(--text-primary)',
            fontSize: 17,
            lineHeight: 1.8,
            fontFamily: 'var(--font-sans)'
          }}>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {msg.content}
            </ReactMarkdown>
          </div>

          {/* Premium Text-to-Speech Controls */}
          {!isUser && (
            <>
              {!showTTSPlayer ? (
                <div style={{ marginTop: 20 }}>
                  <button
                    onClick={() => {
                      setShowTTSPlayer(true)
                      setActiveAudioId(audioId)
                    }}
                    className="btn-secondary"
                    aria-label="Listen to answer"
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 8,
                      fontSize: 14.5,
                      fontWeight: 700,
                      fontFamily: 'var(--font-sans)',
                      borderRadius: 'var(--radius-full)',
                      padding: '10px 18px',
                      boxShadow: 'var(--shadow-sm)',
                      cursor: 'pointer'
                    }}
                  >
                    <span>🔊</span> Listen to Answer
                  </button>
                </div>
              ) : (
                <TTSPlayer 
                  text={msg.content}
                  audioId={audioId}
                  activeAudioId={activeAudioId}
                  setActiveAudioId={setActiveAudioId}
                />
              )}
            </>
          )}

          {/* Raga Audio Player Integration */}
          {msg.audio && msg.audio.url && (
            <div style={{ marginTop: 32 }}>
              <RagaAudioPlayer audio={msg.audio} />
            </div>
          )}

          {/* Source Citations */}
          {msg.citations?.length > 0 && (
            <div style={{ marginTop: 32, paddingTop: 24, borderTop: '1px solid var(--border)' }}>
              <button 
                onClick={() => setShowSources(s => !s)}
                style={{
                  display: 'inline-flex', alignItems: 'center', gap: 8,
                  fontSize: 14, fontWeight: 700, color: 'var(--peacock)',
                  fontFamily: 'var(--font-sans)',
                  background: 'rgba(2, 132, 199, 0.05)', padding: '10px 16px', borderRadius: 'var(--radius-full)', border: '1px solid transparent'
                }}
                onMouseEnter={e => { e.currentTarget.style.background = 'rgba(2, 132, 199, 0.1)'; e.currentTarget.style.borderColor = 'rgba(2, 132, 199, 0.2)'; }}
                onMouseLeave={e => { e.currentTarget.style.background = 'rgba(2, 132, 199, 0.05)'; e.currentTarget.style.borderColor = 'transparent'; }}
              >
                <span>{showSources ? 'Hide' : 'Show'}</span>
                {msg.citations.length} References
              </button>

              {showSources && (
                <div style={{ marginTop: 20, display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16 }}>
                  {msg.citations.map((cit, idx) => (
                    <SourceCard key={idx} citation={cit} index={idx} />
                  ))}
                </div>
              )}
            </div>
          )}

        </div>
      </div>
    </div>
  )
}
