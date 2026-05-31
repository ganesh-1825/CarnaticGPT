import React, { useState, useRef, useEffect, useCallback } from 'react'
import { sendMessage, createSession } from '../services/api'
import ChatMessage from '../components/ChatMessage'

const STARTERS = [
  'What is Shruti in Carnatic music?',
  'Explain the raga Hindolam',
  'What are Jeeva Swaras?',
  'Explain Gamaka techniques',
  'Who is Tyagaraja?',
  'Compare Kalyani and Mohanam ragas',
  'What is the 72 Melapakarta system?',
  'Play Bhairavi alapana',
]

const FRAMEWORK_INFO = [
  'Similarity Floor Threshold: >0.70',
  'Target Extraction Count (Top K): 5',
  'Realtime Cross-Encoder Reranking: Active',
  'Domain Validation: Carnatic-only filter',
]

export default function ChatPage({ activeSession, setActiveSession, setSessions }) {
  const [messages, setMessages] = useState([])
  const [input,    setInput]    = useState('')
  const [loading,  setLoading]  = useState(false)
  const bottomRef = useRef(null)
  const textRef   = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior:'smooth' })
  }, [messages])

  const ensureSession = useCallback(async () => {
    if (activeSession) return activeSession
    const r   = await createSession()
    const sid = r.data.session_id
    setActiveSession(sid)
    setSessions(s => [{ id:sid, title:'New conversation', message_count:0 }, ...s])
    return sid
  }, [activeSession, setActiveSession, setSessions])

  const send = async (question) => {
    const q = (question || input).trim()
    if (!q || loading) return
    setInput('')

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
      // Update session title
      setSessions(s => s.map(x =>
        x.id === sid ? { ...x, title: q.slice(0,48) } : x
      ))
    } catch(e) {
      setMessages(m => [
        ...m.slice(0,-1),
        { role:'assistant', content:`Error: ${e.message}` }
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
    <div style={{ display:'flex', flexDirection:'column', height:'100%', overflow:'hidden' }}>
      {/* Top bar */}
      <div style={{
        padding:'14px 24px', borderBottom:'1px solid var(--border)',
        background:'var(--bg-surface)',
        display:'flex', alignItems:'center', justifyContent:'space-between',
        flexShrink:0,
      }}>
        <div>
          <h1 style={{ fontSize:18, fontWeight:700, letterSpacing:'-.01em' }}
              className="grad-text">CarnaticGPT Chat</h1>
          <p style={{ fontSize:12, color:'var(--text-muted)', marginTop:2 }}>
            Ask questions about Carnatic ragas, composers, and theory from uploaded books.
          </p>
        </div>
        <button onClick={() => setMessages([])}
          style={{
            padding:'6px 14px', borderRadius:8,
            background:'var(--bg-card)', border:'1px solid var(--border)',
            color:'var(--text-secondary)', fontSize:12.5,
            transition:'var(--transition)',
          }}
          onMouseEnter={e=>e.currentTarget.style.borderColor='var(--border-bright)'}
          onMouseLeave={e=>e.currentTarget.style.borderColor='var(--border)'}
        >
          + New Chat
        </button>
      </div>

      {/* Framework banner */}
      {empty && (
        <div style={{
          margin:'16px 24px 0',
          padding:'12px 16px', borderRadius:10,
          background:'var(--bg-card)',
          border:'1px solid var(--border)',
          flexShrink:0,
        }}>
          <p style={{ fontSize:11.5, fontWeight:600, color:'var(--purple-light)', marginBottom:8 }}>
            Active Framework Metrics
          </p>
          <p style={{ fontSize:11.5, color:'var(--text-muted)', marginBottom:6 }}>
            Strict domain monitoring validates queries against Carnatic structural metadata before FAISS retrieval.
          </p>
          <div style={{ display:'flex', flexWrap:'wrap', gap:6 }}>
            {FRAMEWORK_INFO.map((f,i) => (
              <span key={i} style={{
                fontSize:11, padding:'3px 9px', borderRadius:20,
                background:'var(--purple-pale)',
                border:'0.5px solid rgba(139,92,246,.2)',
                color:'var(--purple-light)',
              }}>• {f}</span>
            ))}
          </div>
        </div>
      )}

      {/* Messages */}
      <div style={{
        flex:1, overflowY:'auto', padding:'20px 24px',
        display:'flex', flexDirection:'column', gap:20,
      }}>
        {empty && (
          <div style={{ marginTop:20 }}>
            <p style={{ fontSize:12, color:'var(--text-muted)', marginBottom:12 }}>
              Try a question:
            </p>
            <div style={{ display:'flex', flexWrap:'wrap', gap:8 }}>
              {STARTERS.map((s,i) => (
                <button key={i} onClick={() => send(s)}
                  style={{
                    padding:'7px 14px', borderRadius:20,
                    background:'var(--bg-card)',
                    border:'1px solid var(--border)',
                    color:'var(--text-secondary)', fontSize:12.5,
                    transition:'var(--transition)',
                  }}
                  onMouseEnter={e=>{e.currentTarget.style.borderColor='var(--border-bright)';e.currentTarget.style.color='var(--text-primary)'}}
                  onMouseLeave={e=>{e.currentTarget.style.borderColor='var(--border)';e.currentTarget.style.color='var(--text-secondary)'}}
                >{STARTERS[i]}</button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => <ChatMessage key={i} message={m}/>)}
        <div ref={bottomRef}/>
      </div>

      {/* Input */}
      <div style={{
        padding:'16px 24px', borderTop:'1px solid var(--border)',
        background:'var(--bg-surface)', flexShrink:0,
      }}>
        <div style={{
          display:'flex', gap:10, alignItems:'flex-end',
          background:'var(--bg-card)',
          border:`1px solid ${loading ? 'var(--border-bright)' : 'var(--border)'}`,
          borderRadius:14, padding:'12px 14px',
          transition:'var(--transition)',
        }}>
          <textarea
            ref={textRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={onKey}
            placeholder="Ask about Carnatic ragas, talas, composers… (Enter to send)"
            rows={1}
            style={{
              flex:1, background:'transparent', border:'none', outline:'none',
              color:'var(--text-primary)', fontSize:13.5, lineHeight:1.6,
              resize:'none', maxHeight:120, overflowY:'auto',
            }}
            onInput={e => {
              e.target.style.height = 'auto'
              e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
            }}
          />
          <button onClick={() => send()} disabled={!input.trim() || loading}
            style={{
              width:36, height:36, borderRadius:9, flexShrink:0,
              background: input.trim() && !loading
                ? 'linear-gradient(135deg,var(--purple),var(--blue))'
                : 'var(--bg-hover)',
              border:'none',
              color:'white', fontSize:15,
              display:'flex', alignItems:'center', justifyContent:'center',
              transition:'var(--transition)',
              opacity: (!input.trim() || loading) ? .5 : 1,
              cursor: (!input.trim() || loading) ? 'not-allowed' : 'pointer',
            }}>
            {loading ? <span style={{ animation:'spin 1s linear infinite', display:'inline-block' }}>⟳</span> : '➤'}
          </button>
        </div>
        <p style={{ fontSize:10.5, color:'var(--text-faint)', textAlign:'center', marginTop:7 }}>
          Shift+Enter for newline · Only answers from uploaded Carnatic books
        </p>
      </div>
    </div>
  )
}
