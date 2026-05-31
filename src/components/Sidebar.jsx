import React, { useEffect } from 'react'
import { listSessions, createSession, deleteSession } from '../services/api'

const NAV = [
  { id:'chat',   icon:'💬', label:'Chat Playground' },
  { id:'upload', icon:'📤', label:'Ingest Documents' },
  { id:'stats',  icon:'📊', label:'Analytics Metrics' },
]

export default function Sidebar({ open, onToggle, page, onNav,
                                   sessions, setSessions,
                                   activeSession, setActiveSession }) {

  useEffect(() => {
    listSessions()
      .then(r => setSessions(r.data.sessions || []))
      .catch(() => {})
  }, [])

  const newSession = async () => {
    try {
      const r = await createSession()
      const sid = r.data.session_id
      setSessions(s => [{ id:sid, title:'New conversation', message_count:0, created_at:r.data.created_at }, ...s])
      setActiveSession(sid)
      onNav('chat')
    } catch(e) { console.error(e) }
  }

  const delSession = async (e, id) => {
    e.stopPropagation()
    await deleteSession(id).catch(()=>{})
    setSessions(s => s.filter(x => x.id !== id))
    if (activeSession === id) setActiveSession(null)
  }

  const W = open ? 260 : 64

  return (
    <aside style={{
      width: W, flexShrink:0,
      background:'var(--bg-surface)',
      borderRight:'1px solid var(--border)',
      display:'flex', flexDirection:'column',
      transition:'width .2s ease',
      overflow:'hidden',
      position:'relative', zIndex:10,
    }}>
      {/* Logo */}
      <div style={{
        padding: open ? '20px 18px 16px' : '20px 14px 16px',
        borderBottom:'1px solid var(--border)',
        display:'flex', alignItems:'center', gap:10,
      }}>
        <div style={{
          width:36, height:36, borderRadius:10, flexShrink:0,
          background:'linear-gradient(135deg,#8b5cf6,#3b82f6)',
          display:'flex', alignItems:'center', justifyContent:'center',
          fontSize:18, boxShadow:'0 0 16px rgba(139,92,246,.4)',
        }}>🎵</div>
        {open && (
          <div>
            <div style={{ fontWeight:700, fontSize:15, letterSpacing:'.01em' }}
                 className="grad-text">CarnaticGPT</div>
            <div style={{ fontSize:10.5, color:'var(--text-muted)', marginTop:1 }}>
              RAG Engine v2.0
            </div>
          </div>
        )}
        <button onClick={onToggle} style={{
          marginLeft:'auto', color:'var(--text-muted)', padding:4,
          borderRadius:6, transition:'var(--transition)',
        }}
          onMouseEnter={e=>e.currentTarget.style.color='var(--text-primary)'}
          onMouseLeave={e=>e.currentTarget.style.color='var(--text-muted)'}
        >
          {open ? '◀' : '▶'}
        </button>
      </div>

      {/* Nav */}
      <nav style={{ padding:'10px 10px 0' }}>
        {NAV.map(n => (
          <button key={n.id} onClick={() => onNav(n.id)}
            style={{
              width:'100%', padding: open ? '9px 12px' : '9px 0',
              borderRadius: 8, marginBottom:2,
              display:'flex', alignItems:'center',
              gap: open ? 10 : 0, justifyContent: open ? 'flex-start' : 'center',
              background: page===n.id ? 'var(--purple-pale)' : 'transparent',
              color: page===n.id ? 'var(--purple-light)' : 'var(--text-secondary)',
              fontWeight: page===n.id ? 500 : 400, fontSize:13.5,
              borderLeft: page===n.id ? '2px solid var(--purple)' : '2px solid transparent',
              transition:'var(--transition)',
            }}
            onMouseEnter={e => { if(page!==n.id) e.currentTarget.style.background='var(--bg-hover)' }}
            onMouseLeave={e => { if(page!==n.id) e.currentTarget.style.background='transparent' }}
          >
            <span style={{ fontSize:15 }}>{n.icon}</span>
            {open && <span>{n.label}</span>}
          </button>
        ))}
      </nav>

      {/* Sessions */}
      {open && (
        <div style={{ flex:1, display:'flex', flexDirection:'column', overflow:'hidden', margin:'14px 10px 0' }}>
          <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:8 }}>
            <span style={{ fontSize:10.5, color:'var(--text-muted)', textTransform:'uppercase', letterSpacing:'.08em' }}>
              Chat Sessions
            </span>
            <button onClick={newSession} style={{
              width:22, height:22, borderRadius:'50%',
              background:'var(--purple-pale)', color:'var(--purple-light)',
              display:'flex', alignItems:'center', justifyContent:'center',
              fontSize:16, lineHeight:1, transition:'var(--transition)',
            }}
              onMouseEnter={e=>e.currentTarget.style.background='var(--purple)'}
              onMouseLeave={e=>e.currentTarget.style.background='var(--purple-pale)'}
              title="New chat"
            >+</button>
          </div>

          <div style={{ flex:1, overflowY:'auto' }}>
            {sessions.length === 0 && (
              <p style={{ fontSize:12, color:'var(--text-faint)', textAlign:'center', marginTop:16 }}>
                No recent sessions
              </p>
            )}
            {sessions.map(s => (
              <div key={s.id}
                onClick={() => { setActiveSession(s.id); onNav('chat') }}
                style={{
                  padding:'8px 10px', borderRadius:8, marginBottom:3,
                  cursor:'pointer', display:'flex', alignItems:'center', gap:6,
                  background: activeSession===s.id ? 'var(--purple-pale)' : 'transparent',
                  border: activeSession===s.id ? '1px solid var(--border-bright)' : '1px solid transparent',
                  transition:'var(--transition)',
                  color: activeSession===s.id ? 'var(--text-primary)' : 'var(--text-secondary)',
                }}
                onMouseEnter={e => { 
                  if(activeSession!==s.id) e.currentTarget.style.background='var(--bg-hover)';
                  const btn = e.currentTarget.querySelector('.delete-btn');
                  if (btn) btn.style.opacity = 1;
                }}
                onMouseLeave={e => { 
                  if(activeSession!==s.id) e.currentTarget.style.background='transparent';
                  const btn = e.currentTarget.querySelector('.delete-btn');
                  if (btn) btn.style.opacity = 0;
                }}
              >
                <span style={{ fontSize:12 }}>💬</span>
                <span style={{ flex:1, fontSize:12.5, overflow:'hidden',
                               textOverflow:'ellipsis', whiteSpace:'nowrap' }}>
                  {s.title || 'New conversation'}
                </span>
                <button 
                  className="delete-btn"
                  onClick={e => delSession(e,s.id)}
                  style={{ color:'var(--text-faint)', fontSize:13, opacity:0,
                           transition:'var(--transition)', padding:'0 2px' }}
                  onMouseEnter={e => { e.stopPropagation(); e.currentTarget.style.color='var(--red)' }}
                  onMouseLeave={e => e.currentTarget.style.color='var(--text-faint)'}
                >×</button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Footer status */}
      <div style={{
        padding: open ? '12px 16px' : '12px 0',
        borderTop:'1px solid var(--border)',
        display:'flex', alignItems:'center', gap:8,
        justifyContent: open ? 'flex-start' : 'center',
      }}>
        <span style={{
          width:7, height:7, borderRadius:'50%',
          background:'var(--green)',
          boxShadow:'0 0 6px var(--green)',
          flexShrink:0,
        }}/>
        {open && <span style={{ fontSize:11.5, color:'var(--text-muted)' }}>System Online</span>}
      </div>
    </aside>
  )
}
