import React from 'react';
import { History, Calendar, Trash2, ArrowRight } from 'lucide-react';

export default function HistoryPage({ sessions, deleteSession, setActiveSessionId, navigateToChat }) {
  const handleSelect = (id) => {
    setActiveSessionId(id);
    navigateToChat();
  };
  
  return (
    <div className="page-viewport animate-fade-in" style={{ paddingBottom: '60px' }}>
      {/* Title */}
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{ fontSize: '2rem', fontWeight: 800, marginBottom: '6px' }}>Conversations Archive</h1>
        <p style={{ color: 'hsl(var(--text-secondary))', fontSize: '0.95rem' }}>
          Browse, review, or resume search transcripts from previous learning sessions.
        </p>
      </div>
      
      <div className="glass-card" style={{ padding: '24px', maxWidth: '800px' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <History size={18} color="hsl(var(--accent-gold))" /> Past Transcripts
        </h3>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {sessions.map((s) => (
            <div key={s.id} className="glass-card animate-fade-in" style={{
              padding: '16px 20px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              background: 'rgba(255, 255, 255, 0.01)',
              borderColor: 'rgba(255, 255, 255, 0.04)'
            }}>
              <div>
                <h4 style={{ fontSize: '1rem', fontWeight: 600, color: '#fff', marginBottom: '6px' }}>{s.title}</h4>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', color: 'hsl(var(--text-muted))' }}>
                  <Calendar size={12} />
                  <span>Started: {new Date(s.created_at).toLocaleDateString()}</span>
                </div>
              </div>
              
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <button onClick={() => deleteSession(s.id)} style={{
                  background: 'none', border: 'none', color: 'hsl(var(--text-muted))', cursor: 'pointer', display: 'flex'
                }} className="trash-btn">
                  <Trash2 size={16} />
                </button>
                <button onClick={() => handleSelect(s.id)} className="btn-secondary" style={{
                  padding: '8px 14px', fontSize: '0.8rem', borderRadius: 'var(--border-radius-sm)', gap: '6px'
                }}>
                  Resume Session <ArrowRight size={12} />
                </button>
              </div>
            </div>
          ))}
          
          {sessions.length === 0 && (
            <div style={{ textAlign: 'center', padding: '40px 0', color: 'hsl(var(--text-muted))' }}>
              No history found. Start a conversation in the playground to register telemetry logs.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
