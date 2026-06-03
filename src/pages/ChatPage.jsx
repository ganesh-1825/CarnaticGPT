import React, { useState, useRef, useEffect, useCallback } from 'react'
import { sendMessage, createSession } from '../services/api'
import ChatMessage from '../components/ChatMessage'
import { Send, Menu } from 'lucide-react'

const QUICK_ACTIONS = [
  { text: 'Explore Ragas', query: 'List some beautiful Carnatic ragas and explain their scales', icon: '🎵', color: 'var(--peacock)' },
  { text: 'Learn Talas', query: 'Explain how Adi Tala and other common talas work', icon: '🎼', color: 'var(--peacock)' },
  { text: 'Great Composers', query: 'Who are the Trinity of Carnatic music and what are their contributions?', icon: '👤', color: 'var(--peacock)' },
  { text: 'RTP & Manodharma', query: 'What is Ragam Tanam Pallavi and how is it structured?', icon: '🎤', color: 'var(--peacock)' },
]

export default function ChatPage({ activeSession, setActiveSession, setSessions, onMenuClick, autoPlayTTS }) {
  const [messages, setMessages] = useState([])
  const [input,    setInput]    = useState('')
  const [loading,  setLoading]  = useState(false)
  const [activeAudioId, setActiveAudioId] = useState(null)
  const bottomRef = useRef(null)
  const textRef   = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior:'smooth' })
  }, [messages])

  useEffect(() => {
    if (activeSession) {
      import('../services/api').then(({ getSessionHistory }) => {
        getSessionHistory(activeSession)
          .then(r => {
            setMessages(r.data.history || [])
          })
          .catch(e => console.error("Failed to load conversation history:", e))
      })
    } else {
      setMessages([])
    }
  }, [activeSession])

  const ensureSession = useCallback(async () => {
    if (activeSession) return activeSession
    const r   = await createSession()
    const sid = r.data.session_id
    setActiveSession(sid)
    setSessions(s => [{ id:sid, title:'New Practice', message_count:0 }, ...s])
    return sid
  }, [activeSession, setActiveSession, setSessions])

  const send = async (question) => {
    const q = (question || input).trim()
    if (!q || loading) return
    setInput('')
    setActiveAudioId(null) // Stop active audio playbacks on new question

    const sid = await ensureSession()

    setMessages(m => [...m,
      { role:'user',      content: q },
      { role:'assistant', content:'__TYPING__' },
    ])
    setLoading(true)

    try {
      const r = await sendMessage(q, sid, messages.filter(m=>m.content!=='__TYPING__'))
      const d = r.data
      setMessages(m => [
        ...m.slice(0, -1),
        {
          role:'assistant',
          content:           d.answer,
          citations:         d.citations || [],
          top_confidence:    d.top_confidence,
          confidence_label:  d.confidence_label,
          audio:             d.audio,
        }
      ])
      setSessions(s => s.map(x =>
        x.id === sid ? { ...x, title: q.slice(0,48) } : x
      ))
    } catch(e) {
      setMessages(m => [
        ...m.slice(0,-1),
        { role:'assistant', content:`I'm sorry, I hit a wrong note: ${e.message}` }
      ])
    } finally {
      setLoading(false)
      textRef.current?.focus()
    }
  }

  const onKey = e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
  }

  const empty = messages.length === 0

  return (
    <div style={{ display:'flex', flexDirection:'column', height:'100%', overflow:'hidden', position: 'relative' }}>
      
      {/* Top bar (Mobile only) */}
      <div className="d-md-none" style={{
        padding: '16px 20px',
        display: 'flex', alignItems: 'center', gap: 16,
        background: 'var(--bg-app)',
        borderBottom: '1px solid var(--border)',
        zIndex: 10
      }}>
        <button className="btn-icon" onClick={onMenuClick} style={{ border: 'none', background: 'transparent', boxShadow: 'none' }}>
          <Menu size={24} />
        </button>
        <div style={{ flex: 1 }} />
      </div>

      {/* Messages Feed */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', paddingTop: empty ? 0 : 20, paddingBottom: 140, overflowY: 'auto' }}>
        {empty && (
          <div className="animate-fade-in" style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '0 24px', position: 'relative' }}>
            
            {/* Subtle premium background watermark of a Veena outline */}
            <div style={{
              position: 'absolute',
              inset: 0,
              zIndex: -1,
              opacity: 0.02,
              background: 'url("data:image/svg+xml,%3Csvg viewBox=\'0 0 100 100\' fill=\'none\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Ccircle cx=\'50\' cy=\'70\' r=\'15\' stroke=\'%238B4A36\' stroke-width=\'2.5\' fill=\'%23F8F7F5\'/%3E%3Ccircle cx=\'50\' cy=\'70\' r=\'9\' stroke=\'%238B4A36\' stroke-width=\'1.5\' stroke-dasharray=\'3 2\'/%3E%3Cline x1=\'50\' y1=\'20\' x2=\'50\' y2=\'55\' stroke=\'%238B4A36\' stroke-width=\'3\' stroke-linecap=\'round\'/%3E%3C/svg%3E") no-repeat center center',
              backgroundSize: '40%',
              pointerEvents: 'none',
            }} />

            <div style={{ textAlign: 'center', maxWidth: 680, width: '100%', padding: '40px 0' }}>
              
              <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 64, height: 64, borderRadius: '50%', background: 'rgba(139, 74, 54, 0.06)', marginBottom: 24 }}>
                <span style={{ fontSize: 32 }}>🪕</span>
              </div>
              
              <h1 style={{ fontSize: '2.5rem', marginBottom: 6, fontFamily: 'var(--font-serif)', color: 'var(--peacock)' }}>
                CarnaticGPT
              </h1>
              <p style={{ fontSize: '1.1rem', color: 'var(--text-muted)', fontFamily: 'var(--font-serif)', fontStyle: 'italic', marginBottom: 16 }}>
                Digital Gurukul
              </p>
              
              <p style={{ fontSize: '1rem', color: 'var(--text-secondary)', marginBottom: 40, letterSpacing: '0.01em' }}>
                Explore Ragas, Talas, Composers and Classical Wisdom
              </p>

              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
                gap: 16,
                textAlign: 'left'
              }}>
                {QUICK_ACTIONS.map((s, idx) => (
                  <button key={idx} onClick={() => send(s.query)} className="elevated-card" style={{
                    padding: '24px', display: 'flex', alignItems: 'center', gap: 16, 
                    cursor: 'pointer', borderRadius: '20px', border: '1px solid var(--border)',
                    background: '#FFFFFF', transition: 'all 0.25s ease'
                  }}>
                    <div style={{ fontSize: 24, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      {s.icon}
                    </div>
                    <span style={{ fontSize: 15, color: 'var(--text-primary)', fontWeight: 600, fontFamily: 'var(--font-sans)' }}>{s.text}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {!empty && (
          <div style={{ maxWidth: 880, margin: '0 auto', width: '100%', padding: '0 24px' }}>
            {messages.map((m, i) => (
              <ChatMessage 
                key={i} 
                msg={m} 
                msgIndex={i}
                isLatest={i === messages.length - 1}
                autoPlayTTS={autoPlayTTS}
                activeAudioId={activeAudioId}
                setActiveAudioId={setActiveAudioId}
              />
            ))}
            <div ref={bottomRef} style={{height: 20}} />
          </div>
        )}
      </div>

      {/* Floating Input Area (ShrutiFlow Glass/White Style) */}
      <div style={{
        position: 'absolute', bottom: 32, left: '50%', transform: 'translateX(-50%)',
        width: '100%', maxWidth: 880, padding: '0 24px', zIndex: 20
      }}>
        <div style={{
          padding: '8px 12px',
          display: 'flex',
          alignItems: 'flex-end',
          borderRadius: '24px', // Rounded 24px
          background: 'rgba(255, 255, 255, 0.9)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          border: '1px solid var(--border)',
          boxShadow: 'var(--shadow-lg)'
        }}>
          <textarea
            ref={textRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={onKey}
            placeholder="Ask anything about Carnatic Music..."
            rows={1}
            style={{
              flex: 1, border: 'none', outline: 'none',
              padding: '12px 16px', fontSize: 15, fontWeight: 400,
              resize: 'none', maxHeight: 120, minHeight: 48,
              lineHeight: 1.6,
              color: 'var(--text-primary)',
              background: 'transparent'
            }}
          />
          <button
            onClick={() => send()}
            disabled={!input.trim() || loading}
            className={input.trim() && !loading ? "btn-primary" : "btn-icon"}
            style={{
              width: 48, height: 48, borderRadius: 'var(--radius-full)', margin: 4,
              padding: 0, border: 'none',
              cursor: input.trim() && !loading ? 'pointer' : 'not-allowed',
            }}
          >
            {loading ? (
               <div className="typing-dot" style={{ background: '#fff', margin: 'auto' }} />
            ) : (
              <Send size={18} strokeWidth={2.5} />
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
