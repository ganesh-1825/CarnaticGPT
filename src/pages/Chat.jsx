import React, { useState } from 'react';
import ChatBox from '../components/ChatBox';
import { Send, Sparkles, MessageSquarePlus } from 'lucide-react';

export default function Chat({ messages, loading, sendMessage, startNewSession }) {
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (!input.trim() || loading) return;
    sendMessage(input);
    setInput("");
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      overflow: 'hidden'
    }} className="animate-fade-in">
      {/* Top action header */}
      <div style={{
        padding: '16px 30px',
        borderBottom: '1px solid var(--glass-border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        backdropFilter: 'blur(8px)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Sparkles size={16} color="hsl(var(--accent-teal))" />
          <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>CarnaticGPT Playground</h3>
        </div>
        <button className="btn-secondary" onClick={startNewSession} style={{
          padding: '8px 14px', fontSize: '0.8rem', borderRadius: 'var(--border-radius-sm)', gap: '6px'
        }}>
          <MessageSquarePlus size={14} /> New Conversation
        </button>
      </div>

      {/* Messages list */}
      <ChatBox messages={messages} loading={loading} onSelectQuestion={sendMessage} />

      {/* Search Prompt Input Dock */}
      <div style={{
        padding: '24px 30px',
        borderTop: '1px solid var(--glass-border)',
        background: 'rgba(22, 28, 45, 0.25)',
        backdropFilter: 'blur(16px)'
      }}>
        <div style={{
          position: 'relative',
          display: 'flex',
          alignItems: 'center',
          maxWidth: '960px',
          margin: '0 auto'
        }}>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about Ragas, Composers, and Compositions (e.g. Mayamalavagowla scale, Muthuswami Dikshitar style)..."
            rows={1}
            style={{
              width: '100%',
              background: 'rgba(255, 255, 255, 0.03)',
              border: '1px solid var(--glass-border)',
              borderRadius: 'var(--border-radius-lg)',
              padding: '16px 60px 16px 20px',
              color: '#fff',
              outline: 'none',
              resize: 'none',
              fontSize: '0.95rem',
              lineHeight: '1.5',
              maxHeight: '120px'
            }}
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            style={{
              position: 'absolute',
              right: '12px',
              background: 'linear-gradient(135deg, hsl(var(--accent-royal)) 0%, hsl(var(--accent-glow)) 100%)',
              border: 'none',
              width: '40px',
              height: '40px',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              color: '#fff',
              opacity: (loading || !input.trim()) ? 0.5 : 1,
              transition: 'all 0.2s ease',
              boxShadow: 'var(--neon-shadow)'
            }}
          >
            <Send size={16} />
          </button>
        </div>
        <span style={{
          display: 'block',
          textAlign: 'center',
          fontSize: '0.75rem',
          color: 'hsl(var(--text-muted))',
          marginTop: '10px'
        }}>
          CarnaticGPT can compose reasoning mistakes. Cross-check core raga scales with original books.
        </span>
      </div>
    </div>
  );
}
