import React, { useState, useEffect } from 'react'
import Sidebar from './components/Sidebar'
import ChatPage from './pages/ChatPage'
import UploadPage from './pages/UploadPage'
import StatsPage from './pages/StatsPage'

export default function App() {
  const [page, setPage] = useState('chat')          // chat | upload | stats
  const [sessions, setSessions] = useState([])
  const [activeSession, setActiveSession] = useState(null)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [backendOk, setBackendOk] = useState(null)

  // Health-check on mount
  useEffect(() => {
    import('./services/api').then(({ checkHealth }) => {
      checkHealth()
        .then(() => setBackendOk(true))
        .catch(() => setBackendOk(false))
    })
  }, [])

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden', background: 'var(--bg-base)' }}>
      {/* Ambient background */}
      <div style={{
        position: 'fixed', inset: 0, pointerEvents: 'none', zIndex: 0,
        background:
          'radial-gradient(ellipse 80% 50% at 20% 0%, rgba(139,92,246,0.08) 0%, transparent 60%),' +
          'radial-gradient(ellipse 60% 40% at 80% 100%, rgba(59,130,246,0.06) 0%, transparent 60%)',
      }} />

      {/* Connection banner */}
      {backendOk === false && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, zIndex: 200,
          background: 'rgba(239,68,68,0.9)', backdropFilter: 'blur(8px)',
          padding: '8px 20px', textAlign: 'center', fontSize: 12.5, color: 'white',
          letterSpacing: '0.02em',
        }}>
          ⚠ Backend unreachable — make sure FastAPI is running on port 8000
          &nbsp;·&nbsp;
          <code style={{ opacity: .8 }}>uvicorn backend.server:app --port 8000 --reload</code>
        </div>
      )}

      <Sidebar
        open={sidebarOpen}
        onToggle={() => setSidebarOpen(o => !o)}
        page={page}
        onNav={setPage}
        sessions={sessions}
        setSessions={setSessions}
        activeSession={activeSession}
        setActiveSession={setActiveSession}
      />

      <main style={{
        flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column',
        paddingTop: backendOk === false ? 36 : 0,
        position: 'relative', zIndex: 1,
      }}>
        {page === 'chat' && (
          <ChatPage
            activeSession={activeSession}
            setActiveSession={setActiveSession}
            sessions={sessions}
            setSessions={setSessions}
          />
        )}
        {page === 'upload' && <UploadPage onDone={() => setPage('chat')} />}
        {page === 'stats' && <StatsPage />}
      </main>
    </div>
  )
}