import React from 'react';
import { HelpCircle, RefreshCw, GitCompare, User, HelpCircle as QuizIcon } from 'lucide-react';

export default function SuggestedQuestions({ onSelectQuestion }) {
  const suggestions = [
    {
      text: "Explain Bhairavi",
      icon: <HelpCircle size={16} color="hsl(var(--accent-teal))" />,
      tag: "Raga"
    },
    {
      text: "Compare Kalyani vs Mohanam",
      icon: <GitCompare size={16} color="hsl(var(--accent-glow))" />,
      tag: "Comparison"
    },
    {
      text: "Who is Tyagaraja?",
      icon: <User size={16} color="hsl(var(--accent-gold))" />,
      tag: "Composer"
    },
    {
      text: "Generate Tala Quiz",
      icon: <QuizIcon size={16} color="hsl(var(--accent-teal))" />,
      tag: "Interactive"
    }
  ];

  return (
    <div style={{
      width: '100%',
      maxWidth: '800px',
      margin: '24px auto 0 auto',
    }}>
      <h4 style={{
        fontSize: '0.85rem',
        fontWeight: 700,
        textTransform: 'uppercase',
        letterSpacing: '0.08em',
        color: 'hsl(var(--accent-teal))',
        marginBottom: '14px',
        textAlign: 'left'
      }}>
        💡 Suggested Musical Explanations
      </h4>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: '12px',
        width: '100%'
      }}>
        {suggestions.map((item, idx) => (
          <button
            key={idx}
            onClick={() => onSelectQuestion(item.text)}
            className="glass-card"
            style={{
              padding: '16px',
              borderRadius: 'var(--border-radius-md)',
              border: '1px solid var(--glass-border)',
              background: 'rgba(255, 255, 255, 0.02)',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'flex-start',
              gap: '10px',
              textAlign: 'left',
              transition: 'all 0.2s ease',
              width: '100%'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = 'hsl(var(--accent-teal))';
              e.currentTarget.style.boxShadow = '0 0 15px rgba(22, 219, 204, 0.15)';
              e.currentTarget.style.transform = 'translateY(-2px)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'var(--glass-border)';
              e.currentTarget.style.boxShadow = 'none';
              e.currentTarget.style.transform = 'translateY(0)';
            }}
          >
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              width: '100%'
            }}>
              {item.icon}
              <span style={{
                fontSize: '0.65rem',
                fontWeight: 700,
                textTransform: 'uppercase',
                color: 'hsl(var(--text-muted))',
                background: 'rgba(255, 255, 255, 0.05)',
                padding: '2px 6px',
                borderRadius: '4px'
              }}>{item.tag}</span>
            </div>
            <span style={{
              fontSize: '0.9rem',
              fontWeight: 600,
              color: 'hsl(var(--text-primary))',
              lineHeight: 1.4
            }}>
              {item.text}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
