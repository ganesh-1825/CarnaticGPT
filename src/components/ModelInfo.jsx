import React from 'react';
import { Cpu, BookOpen, Layers, Zap } from 'lucide-react';

export default function ModelInfo() {
  const stats = [
    {
      label: "Model",
      value: "Phi-3 Mini",
      icon: <Cpu size={16} color="hsl(var(--accent-glow))" />
    },
    {
      label: "Indexed Books",
      value: "24",
      icon: <BookOpen size={16} color="hsl(var(--accent-gold))" />
    },
    {
      label: "Chunks",
      value: "12,420",
      icon: <Layers size={16} color="hsl(var(--accent-teal))" />
    },
    {
      label: "RAG Mode",
      value: "Enabled",
      icon: <Zap size={16} color="hsl(var(--accent-teal))" />,
      badge: true
    }
  ];

  return (
    <div className="glass-card" style={{
      width: '100%',
      maxWidth: '800px',
      margin: '30px auto 0 auto',
      padding: '20px 24px',
      border: '1px solid var(--glass-border)',
      background: 'rgba(28, 36, 58, 0.25)',
      borderRadius: 'var(--border-radius-lg)',
      boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.2)',
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
        paddingBottom: '12px',
        marginBottom: '16px'
      }}>
        <Cpu size={18} color="hsl(var(--accent-teal))" />
        <h4 style={{
          fontSize: '0.9rem',
          fontWeight: 700,
          textTransform: 'uppercase',
          letterSpacing: '0.06em',
          color: 'hsl(var(--text-primary))',
          margin: 0
        }}>
          RAG Pipeline Engine Status
        </h4>
      </div>
      
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
        gap: '16px'
      }}>
        {stats.map((item, idx) => (
          <div key={idx} style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            background: 'rgba(255, 255, 255, 0.01)',
            padding: '10px 14px',
            borderRadius: 'var(--border-radius-md)',
            border: '1px solid rgba(255, 255, 255, 0.03)'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: 'rgba(255, 255, 255, 0.03)',
              width: '32px',
              height: '32px',
              borderRadius: '8px'
            }}>
              {item.icon}
            </div>
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'flex-start'
            }}>
              <span style={{
                fontSize: '0.7rem',
                color: 'hsl(var(--text-secondary))',
                fontWeight: 500
              }}>
                {item.label}
              </span>
              {item.badge ? (
                <span style={{
                  fontSize: '0.85rem',
                  fontWeight: 700,
                  color: '#fff',
                  background: 'rgba(22, 219, 204, 0.2)',
                  border: '1px solid rgba(22, 219, 204, 0.3)',
                  padding: '1px 6px',
                  borderRadius: '6px',
                  marginTop: '2px',
                  boxShadow: '0 0 8px rgba(22, 219, 204, 0.1)'
                }}>
                  {item.value}
                </span>
              ) : (
                <span style={{
                  fontSize: '0.95rem',
                  fontWeight: 700,
                  color: 'hsl(var(--text-primary))',
                  marginTop: '2px'
                }}>
                  {item.value}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
