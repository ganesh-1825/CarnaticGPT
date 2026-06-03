import React, { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import Sidebar from './components/Sidebar'
import ChatPage from './pages/ChatPage'
import UploadPage from './pages/UploadPage'
import StatsPage from './pages/StatsPage'
import LibraryPage from './pages/LibraryPage'
import LoginPage from './pages/auth/LoginPage'
import SignupPage from './pages/auth/SignupPage'
import ForgotPasswordPage from './pages/auth/ForgotPasswordPage'
import ResetPasswordPage from './pages/auth/ResetPasswordPage'
import PracticeStudio from './pages/PracticeStudio'
import RagaExplorer from './pages/RagaExplorer'
import ComposerExplorer from './pages/ComposerExplorer'

// Main Layout wrapping the authenticated workspace
function MainWorkspace() {
  const [page, setPage] = useState('chat')          
  const [sessions, setSessions] = useState([])
  const [activeSession, setActiveSession] = useState(() => localStorage.getItem('carnatic_active_session') || null)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [backendOk, setBackendOk] = useState(null)
  
  const { theme, setTheme } = useAuth(); // Assume theme is derived from user pref or local storage
  
  // Theme state fallback
  const [localTheme, setLocalTheme] = useState(() => localStorage.getItem('carnatic_theme') || 'light')
  const [autoPlayTTS, setAutoPlayTTS] = useState(() => localStorage.getItem('autoPlayTTS') === 'true')

  const handleAutoPlayTTSToggle = () => {
    setAutoPlayTTS(prev => {
      const next = !prev;
      localStorage.setItem('autoPlayTTS', next ? 'true' : 'false');
      return next;
    });
  }
  
  useEffect(() => {
    import('./services/api').then(({ checkHealth }) => {
      checkHealth()
        .then(() => setBackendOk(true))
        .catch(() => setBackendOk(false))
    })
  }, [])

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', localTheme)
    localStorage.setItem('carnatic_theme', localTheme)
  }, [localTheme])

  useEffect(() => {
    if (activeSession) {
      localStorage.setItem('carnatic_active_session', activeSession)
    } else {
      localStorage.removeItem('carnatic_active_session')
    }
  }, [activeSession])

  return (
    <div className="app-layout">
      {/* Ambient background with Floating Swaras */}
      <div style={{
        position: 'fixed', inset: 0, pointerEvents: 'none', zIndex: 0,
        overflow: 'hidden'
      }}>
        <span className="floating-swara" style={{ top: '10%', left: '10%', animation: 'floatGentle 8s infinite alternate' }}>Sa</span>
        <span className="floating-swara" style={{ top: '30%', right: '15%', animation: 'floatGentle 10s infinite alternate-reverse' }}>Ri</span>
        <span className="floating-swara" style={{ top: '50%', left: '20%', animation: 'floatGentle 9s infinite alternate' }}>Ga</span>
        <span className="floating-swara" style={{ bottom: '20%', right: '25%', animation: 'floatGentle 11s infinite alternate-reverse' }}>Ma</span>
        <span className="floating-swara" style={{ bottom: '10%', left: '30%', animation: 'floatGentle 8.5s infinite alternate' }}>Pa</span>
        <span className="floating-swara" style={{ top: '15%', left: '50%', animation: 'floatGentle 12s infinite alternate-reverse' }}>Da</span>
        <span className="floating-swara" style={{ bottom: '30%', right: '10%', animation: 'floatGentle 9.5s infinite alternate' }}>Ni</span>
      </div>

      {backendOk === false && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, zIndex: 200,
          background: 'var(--red)', backdropFilter: 'blur(8px)',
          padding: '8px 20px', textAlign: 'center', fontSize: 12.5, color: 'white',
        }}>
          ⚠ Backend unreachable — make sure FastAPI is running on port 8000
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
        theme={localTheme}
        onThemeToggle={() => setLocalTheme(t => t === 'light' ? 'dark' : 'light')}
        autoPlayTTS={autoPlayTTS}
        onAutoPlayTTSToggle={handleAutoPlayTTSToggle}
      />

      <main className="app-main" style={{ paddingTop: backendOk === false ? 36 : 0 }}>
        {page === 'chat' && (
          <ChatPage
            activeSession={activeSession}
            setActiveSession={setActiveSession}
            sessions={sessions}
            setSessions={setSessions}
            onMenuClick={() => setSidebarOpen(true)}
            autoPlayTTS={autoPlayTTS}
          />
        )}
        {page === 'library' && <LibraryPage />}
        {page === 'upload' && <UploadPage onDone={() => setPage('chat')} />}
        {page === 'stats' && <StatsPage />}
        {page === 'practice' && <PracticeStudio />}
        {page === 'ragas' && <RagaExplorer />}
        {page === 'composers' && <ComposerExplorer />}
      </main>
    </div>
  )
}

function AppRoutes() {
  return (
    <Routes>
      {/* Auth Routes */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />

      {/* Protected Routes */}
      <Route path="/" element={<ProtectedRoute><MainWorkspace /></ProtectedRoute>} />
      
      {/* Catch-all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}