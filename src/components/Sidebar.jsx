import React, { useState, useEffect, useMemo } from 'react';
import { useAuth } from '../context/AuthContext';
import { listSessions, createSession, deleteSession, renameSession, pinSession } from '../services/api';
import { Search, Pin, Edit2, Trash2, X, Check, LogOut, MessageCircle, BookOpen, UploadCloud, BarChart2, Plus, Moon, Sun, Activity, Music, Users } from 'lucide-react';

const NAV = [
  { id: 'chat', icon: <MessageCircle size={20} strokeWidth={2} />, label: 'Playground' },
  { id: 'library', icon: <BookOpen size={20} strokeWidth={2} />, label: 'Library' },
  { id: 'upload', icon: <UploadCloud size={20} strokeWidth={2} />, label: 'Ingest' },
  { id: 'stats', icon: <BarChart2 size={20} strokeWidth={2} />, label: 'Metrics' },
  { id: 'practice', icon: <Activity size={20} strokeWidth={2} />, label: 'Practice Studio' },
  { id: 'ragas', icon: <Music size={20} strokeWidth={2} />, label: 'Raga Explorer' },
  { id: 'composers', icon: <Users size={20} strokeWidth={2} />, label: 'Composer Explorer' },
];

export default function Sidebar({
  open, onToggle, page, onNav,
  sessions, setSessions,
  activeSession, setActiveSession,
  theme, onThemeToggle,
  autoPlayTTS, onAutoPlayTTSToggle
}) {
  const { user, logout } = useAuth();
  const [search, setSearch] = useState('');
  const [editingId, setEditingId] = useState(null);
  const [editTitle, setEditTitle] = useState('');
  const [deletingId, setDeletingId] = useState(null);

  useEffect(() => {
    fetchSessions();
  }, [user]);

  const fetchSessions = () => {
    if (user) {
      listSessions().then(r => setSessions(r.data || [])).catch(() => {});
    }
  };

  const newSession = async () => {
    try {
      const r = await createSession();
      const sid = r.data.session_id;
      setSessions(s => [{ id: sid, title: 'New Practice Session', is_pinned: false, created_at: r.data.created_at, updated_at: r.data.created_at }, ...s]);
      setActiveSession(sid);
      onNav('chat');
    } catch (e) {
      console.error(e);
    }
  };

  const delSession = async (id) => {
    await deleteSession(id).catch(() => {});
    setSessions(s => s.filter(x => x.id !== id));
    if (activeSession === id) setActiveSession(null);
    setDeletingId(null);
  };

  const handleRename = async (id) => {
    if (!editTitle.trim()) {
      setEditingId(null);
      return;
    }
    await renameSession(id, editTitle).catch(() => {});
    setSessions(s => s.map(x => x.id === id ? { ...x, title: editTitle } : x));
    setEditingId(null);
  };

  const handlePin = async (e, id) => {
    e.stopPropagation();
    await pinSession(id).catch(() => {});
    setSessions(s => s.map(x => x.id === id ? { ...x, is_pinned: !x.is_pinned } : x));
  };

  const filteredSessions = useMemo(() => {
    if (!search.trim()) return sessions;
    const lower = search.toLowerCase();
    return sessions.filter(s => s.title.toLowerCase().includes(lower));
  }, [sessions, search]);

  const pinnedSessions = filteredSessions.filter(s => s.is_pinned);
  const recentSessions = filteredSessions.filter(s => !s.is_pinned);

  const isMobile = window.innerWidth <= 768;
  const W = open ? (isMobile ? 300 : 300) : 72;

  const renderSessionItem = (s) => {
    const isActive = activeSession === s.id;
    const isEditing = editingId === s.id;
    const isDeleting = deletingId === s.id;

    return (
      <div key={s.id}
        onClick={() => { if (!isEditing) { setActiveSession(s.id); onNav('chat'); } }}
        style={{
          padding: '12px 14px', borderRadius: 'var(--radius-sm)', marginBottom: 6,
          cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 12,
          background: isActive ? 'var(--bg-surface-hover)' : 'transparent',
          color: isActive ? 'var(--peacock)' : 'var(--text-secondary)',
          position: 'relative',
          transition: 'all var(--transition-fast)',
        }}
        className="sidebar-session-item"
      >
        <span style={{ display: 'flex', alignItems: 'center', color: isActive ? 'var(--peacock)' : 'var(--text-muted)' }}>
          {s.is_pinned ? <Pin size={16} fill="currentColor" /> : <MessageCircle size={16} />}
        </span>
        
        {isEditing ? (
          <div style={{ flex: 1, display: 'flex', gap: 6 }} onClick={e => e.stopPropagation()}>
            <input 
              autoFocus
              value={editTitle}
              onChange={e => setEditTitle(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') handleRename(s.id); if (e.key === 'Escape') setEditingId(null); }}
              style={{ flex: 1, width: '100%', padding: '4px 8px', fontSize: 14, background: 'var(--bg-surface)', border: '1px solid var(--peacock)', borderRadius: 'var(--radius-sm)', outline: 'none', color: 'var(--text-primary)', fontFamily: 'var(--font-sans)' }}
            />
            <button onClick={() => handleRename(s.id)} style={{ color: 'var(--emerald)' }}><Check size={16} /></button>
            <button onClick={() => setEditingId(null)} style={{ color: '#EF4444' }}><X size={16} /></button>
          </div>
        ) : isDeleting ? (
          <div style={{ flex: 1, display: 'flex', gap: 6, alignItems: 'center', fontSize: 13, color: '#EF4444' }} onClick={e => e.stopPropagation()}>
            <span style={{ fontFamily: 'var(--font-sans)', fontWeight: 700 }}>Delete?</span>
            <button onClick={() => delSession(s.id)} style={{ color: '#EF4444', fontWeight: 'bold' }}>Yes</button>
            <button onClick={() => setDeletingId(null)} style={{ color: 'var(--text-muted)' }}>No</button>
          </div>
        ) : (
          <span style={{ flex: 1, fontSize: 14, fontWeight: isActive ? 700 : 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', textAlign: 'left', fontFamily: 'var(--font-sans)' }}>
            {s.title}
          </span>
        )}

        {!isEditing && !isDeleting && (
          <div className="session-actions" style={{ display: 'flex', gap: 8 }}>
            <button onClick={(e) => handlePin(e, s.id)} title={s.is_pinned ? "Unpin" : "Pin"}><Pin size={14} /></button>
            <button onClick={(e) => { e.stopPropagation(); setEditTitle(s.title); setEditingId(s.id); }} title="Rename"><Edit2 size={14} /></button>
            <button onClick={(e) => { e.stopPropagation(); setDeletingId(s.id); }} title="Delete"><Trash2 size={14} /></button>
          </div>
        )}
      </div>
    );
  };

  return (
    <>
      <style>{`
        .sidebar-session-item:hover { background: var(--bg-surface-hover) !important; color: var(--text-primary) !important; }
        .sidebar-session-item .session-actions { opacity: 0; transition: opacity 0.2s; }
        .sidebar-session-item:hover .session-actions { opacity: 1; }
        .sidebar-session-item .session-actions button { color: var(--text-muted); }
        .sidebar-session-item .session-actions button:hover { color: var(--peacock) !important; transform: scale(1.1); }
      `}</style>
      
      {isMobile && <div className={`mobile-overlay ${open ? 'visible' : ''}`} onClick={onToggle} style={{position: 'fixed', inset: 0, background: 'rgba(0, 0, 0, 0.4)', backdropFilter: 'blur(4px)', zIndex: 9, opacity: open ? 1 : 0, pointerEvents: open ? 'auto' : 'none', transition: 'opacity var(--transition)'}} />}
      
      <aside 
        className={`app-sidebar ${isMobile ? (open ? 'mobile-open' : 'mobile-closed') : ''}`}
        style={{
          width: isMobile ? (open ? 300 : 0) : W,
          backgroundColor: 'var(--bg-sidebar)',
          borderRight: '1px solid var(--border)',
          display: 'flex',
          flexDirection: 'column',
          zIndex: 50,
          transition: 'width var(--transition), transform var(--transition)',
          position: isMobile ? 'absolute' : 'relative',
          height: '100%',
          boxShadow: isMobile ? 'var(--shadow-lg)' : 'none'
        }}
      >
        {/* Brand Header */}
        <div style={{
          padding: open ? '24px' : '24px 14px',
          display:'flex', alignItems:'center', gap:12,
        }}>
          <div style={{
            width:44, height:44, borderRadius:'50%', flexShrink:0,
            background: 'var(--peacock)',
            display:'flex', alignItems:'center', justifyContent:'center',
            boxShadow: 'var(--shadow-sm)'
          }}>
            <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ width: 24, height: 24 }}>
              <circle cx="50" cy="70" r="15" stroke="#FFFFFF" strokeWidth="4" />
              <line x1="50" y1="20" x2="50" y2="55" stroke="#FFFFFF" strokeWidth="5" strokeLinecap="round" />
              <circle cx="43" cy="25" r="4" fill="#FFFFFF" />
              <circle cx="57" cy="30" r="4" fill="#FFFFFF" />
            </svg>
          </div>
          {open && (
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <div style={{ fontWeight:700, fontSize:19, color:'var(--text-primary)', fontFamily:'var(--font-serif)', lineHeight: 1.1 }}>
                CarnaticGPT
              </div>
              <div style={{ fontSize:10, color: 'var(--peacock)', letterSpacing: '0.08em', textTransform: 'uppercase', fontWeight: 600, marginTop: 2, fontFamily: 'var(--font-sans)' }}>
                Digital Gurukul
              </div>
            </div>
          )}
          {open && !isMobile && (
            <button onClick={onToggle} style={{
              marginLeft:'auto', color:'var(--text-muted)', padding:6,
              borderRadius:'var(--radius-full)', background: 'var(--bg-surface-hover)',
            }}
              onMouseEnter={e=>{e.currentTarget.style.color='var(--text-primary)';}}
              onMouseLeave={e=>{e.currentTarget.style.color='var(--text-muted)';}}
            >
              ◀
            </button>
          )}
        </div>

        {/* New Chat FAB (when open) or icon (when closed) */}
        <div style={{ padding: open ? '0 24px 16px' : '0 12px 16px', display: 'flex', justifyContent: 'center' }}>
          <button 
            className="btn-primary" 
            onClick={newSession}
            style={{ width: '100%', padding: open ? '14px 20px' : '14px 0', borderRadius: 'var(--radius-full)' }}
          >
            <Plus size={20} strokeWidth={3} />
            {open && <span style={{ fontSize: 16 }}>New Practice</span>}
          </button>
        </div>

        {/* Main Navigation Tabs */}
        <nav style={{ padding: open ? '0 16px' : '0 8px', borderBottom: '1px solid var(--border)', paddingBottom: 16 }}>
          {NAV.map(n => {
            const isActive = page === n.id;
            return (
              <button key={n.id} onClick={() => onNav(n.id)}
                style={{
                  width:'100%', padding: open ? '12px 16px' : '12px 0',
                  borderRadius: 'var(--radius-sm)',
                  marginBottom: 4,
                  display:'flex', alignItems:'center',
                  gap: open ? 16 : 0, justifyContent: open ? 'flex-start' : 'center',
                  background: isActive ? 'var(--bg-surface-hover)' : 'transparent',
                  color: isActive ? 'var(--peacock)' : 'var(--text-secondary)',
                  fontWeight: 700, fontSize: 15,
                  transition: 'all var(--transition-fast)',
                  fontFamily: 'var(--font-sans)',
                }}
                onMouseEnter={e => { if(!isActive) { e.currentTarget.style.background='var(--bg-surface-hover)'; e.currentTarget.style.color='var(--text-primary)'; } }}
                onMouseLeave={e => { if(!isActive) { e.currentTarget.style.background='transparent'; e.currentTarget.style.color='var(--text-secondary)'; } }}
              >
                <span style={{ display: 'flex', color: isActive ? 'var(--peacock)' : 'inherit' }}>{n.icon}</span>
                {open && <span>{n.label}</span>}
              </button>
            );
          })}
        </nav>

        {/* Session History */}
        {open ? (
          <div style={{ flex:1, display:'flex', flexDirection:'column', overflow:'hidden', margin:'16px 16px 0' }}>
            <div style={{ position: 'relative', marginBottom: 16 }}>
              <Search size={16} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input 
                type="text" 
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="Search past practices..."
                style={{ width: '100%', padding: '10px 14px 10px 40px', fontSize: 14, borderRadius: 'var(--radius-full)', border: '1px solid var(--border)', background: 'var(--bg-surface-hover)', color: 'var(--text-primary)', outline: 'none', transition: 'all var(--transition-fast)' }}
                onFocus={e => { e.currentTarget.style.borderColor = 'var(--peacock)'; e.currentTarget.style.background = 'var(--bg-surface)'; }}
                onBlur={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.background = 'var(--bg-surface-hover)'; }}
              />
            </div>

            <div style={{ flex: 1, overflowY: 'auto', paddingRight: 4 }}>
              {pinnedSessions.length > 0 && (
                <div style={{ marginBottom: 24 }}>
                  <div style={{ fontSize: 12, fontWeight: 800, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6, paddingLeft: 8 }}>
                    <Pin size={14} /> Pinned Texts
                  </div>
                  {pinnedSessions.map(renderSessionItem)}
                </div>
              )}
              
              <div>
                <div style={{ fontSize: 12, fontWeight: 800, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: 8, paddingLeft: 8 }}>
                  Recent Practices
                </div>
                {recentSessions.length === 0 ? (
                  <div style={{ fontSize: 14, color: 'var(--text-muted)', textAlign: 'center', padding: '30px 0', fontFamily: 'var(--font-sans)', fontWeight: 600 }}>
                    {search ? 'No results found.' : 'Ready to begin.'}
                  </div>
                ) : (
                  recentSessions.map(renderSessionItem)
                )}
              </div>
            </div>
          </div>
        ) : (
          <div style={{ flex: 1 }} />
        )}

        {/* Footer: User & Theme */}
        <div style={{ padding: open ? '16px 20px' : '16px 0', borderTop: '1px solid var(--border)', display: 'flex', flexDirection: 'column', gap: 12 }}>
          
          <div style={{ display: 'flex', justifyContent: open ? 'flex-start' : 'center' }}>
            <button onClick={onThemeToggle} className="btn-secondary" style={{ padding: open ? '10px 16px' : '10px', width: open ? '100%' : 'auto', borderRadius: 'var(--radius-full)', justifyContent: open ? 'center' : 'center' }}>
              {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
              {open && <span>{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>}
            </button>
          </div>

          <div style={{ display: 'flex', justifyContent: open ? 'flex-start' : 'center', padding: open ? '0 8px' : '0' }}>
            {open ? (
              <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer', fontSize: 13, fontWeight: 700, color: 'var(--text-secondary)', width: '100%', fontFamily: 'var(--font-sans)', userSelect: 'none' }}>
                <input 
                  type="checkbox" 
                  checked={autoPlayTTS} 
                  onChange={onAutoPlayTTSToggle} 
                  style={{ width: 16, height: 16, cursor: 'pointer', accentColor: 'var(--peacock)' }} 
                />
                <span>Auto-play Voice</span>
              </label>
            ) : (
              <button 
                onClick={onAutoPlayTTSToggle} 
                className="btn-icon" 
                title={autoPlayTTS ? "Disable Voice Auto-play" : "Enable Voice Auto-play"}
                style={{ width: 36, height: 36, border: 'none', background: 'transparent', boxShadow: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center', color: autoPlayTTS ? 'var(--peacock)' : 'var(--text-muted)' }}
              >
                {autoPlayTTS ? '🔊' : '🔇'}
              </button>
            )}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: open ? '8px' : '0', justifyContent: open ? 'flex-start' : 'center' }}>
            <div style={{ width: 40, height: 40, borderRadius: 'var(--radius-full)', background: 'var(--lotus-pink)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 800, fontSize: 18 }}>
              {user ? user.username.charAt(0).toUpperCase() : 'G'}
            </div>
            {open && (
              <div style={{ flex: 1, overflow: 'hidden' }}>
                <div style={{ fontSize: 15, fontWeight: 800, color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {user ? (user.full_name || user.username) : 'Guest'}
                </div>
                <div style={{ fontSize: 13, color: 'var(--text-muted)', fontWeight: 600 }}>
                  {user ? 'Student' : 'Not Logged In'}
                </div>
              </div>
            )}
            {open && (
              <button onClick={logout} title="Log Out" className="btn-icon" style={{ border: 'none', background: 'transparent', boxShadow: 'none' }}>
                <LogOut size={18} />
              </button>
            )}
          </div>
          
        </div>
      </aside>
    </>
  );
}
