import React, { useState } from 'react';
import { ChevronDown, ChevronUp, BookOpen, Bookmark } from 'lucide-react';

// Truncate long text
const shortText = (text) => {
  if (!text) return '';
  return text.length > 250 ? text.substring(0, 250) + '...' : text;
};

export default function CitationCard({ cit }) {
  const [expanded, setExpanded] = useState(false);
  const scorePct = Math.round((cit.score || 0) * 100);

  // Determine confidence styling
  const confStr = cit.confidence || '';
  const isHigh = typeof confStr === 'string' && confStr.toLowerCase().includes('high');
  const isMedium = typeof confStr === 'string' && confStr.toLowerCase().includes('medium');
  const confLabel = isHigh ? 'HIGH' : isMedium ? 'MEDIUM' : 'LOW';
  const confBg = isHigh
    ? 'rgba(34, 197, 94, 0.15)'
    : isMedium
      ? 'rgba(234, 179, 8, 0.15)'
      : 'rgba(239, 68, 68, 0.15)';
  const confColor = isHigh
    ? 'rgb(134, 239, 172)'
    : isMedium
      ? 'rgb(253, 224, 71)'
      : 'rgb(252, 165, 165)';
  const confBorder = isHigh
    ? 'rgba(34, 197, 94, 0.25)'
    : isMedium
      ? 'rgba(234, 179, 8, 0.25)'
      : 'rgba(239, 68, 68, 0.25)';

  return (
    <div style={{
      background: 'rgba(17, 24, 39, 0.9)',
      border: '1px solid rgba(139, 92, 246, 0.15)',
      borderRadius: 14,
      overflow: 'hidden',
      transition: 'all 0.2s ease',
      boxShadow: '0 4px 16px rgba(0, 0, 0, 0.25)',
      marginBottom: 4,
    }}
    onMouseEnter={e => {
      e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.4)';
      e.currentTarget.style.boxShadow = '0 6px 24px rgba(0, 0, 0, 0.35)';
    }}
    onMouseLeave={e => {
      e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.15)';
      e.currentTarget.style.boxShadow = '0 4px 16px rgba(0, 0, 0, 0.25)';
    }}
    >
      {/* Header bar */}
      <div style={{
        padding: '16px 20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        cursor: 'pointer',
      }} onClick={() => setExpanded(!expanded)}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <BookOpen size={14} color="rgba(139, 92, 246, 0.7)" />
          <span style={{
            fontSize: 14,
            fontWeight: 700,
            color: '#fff',
            letterSpacing: '0.01em',
          }}>
            {cit.book_name} — p.{cit.page}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{
            padding: '4px 12px',
            borderRadius: 20,
            fontSize: 10.5,
            fontWeight: 700,
            letterSpacing: '0.05em',
            background: confBg,
            color: confColor,
            border: `1px solid ${confBorder}`,
            whiteSpace: 'nowrap',
          }}>
            {confLabel} CONFIDENCE
          </span>
          <span style={{ color: 'rgba(255, 255, 255, 0.3)' }}>
            {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </span>
        </div>
      </div>

      {/* Expanded excerpt content */}
      {expanded && (
        <div style={{
          padding: '0 20px 18px',
          fontSize: 13,
          lineHeight: 1.8,
          color: 'rgba(209, 213, 219, 0.85)',
        }} className="animate-fade-in">
          <div style={{
            borderTop: '1px solid rgba(255, 255, 255, 0.04)',
            paddingTop: 14,
            marginBottom: 10,
          }}>
            {cit.type === 'music' && (cit.song || cit.raga || cit.composer || cit.youtube) ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '13px' }}>
                {cit.song && <p style={{ margin: 0 }}><strong>Song:</strong> {cit.song}</p>}
                {cit.raga && <p style={{ margin: 0 }}><strong>Raga:</strong> {cit.raga}</p>}
                {cit.composer && <p style={{ margin: 0 }}><strong>Composer:</strong> {cit.composer}</p>}
                {cit.youtube && (
                  <p style={{ margin: 0 }}>
                    <strong>YouTube:</strong>
                    <a href={cit.youtube} target="_blank" rel="noopener noreferrer" 
                       style={{ color: '#f87171', textDecoration: 'underline', marginLeft: '6px', fontWeight: 600 }}
                       className="hover:text-red-300">
                      Open Link ▶
                    </a>
                  </p>
                )}
              </div>
            ) : (
              <blockquote style={{
                borderLeft: '3px solid rgba(139, 92, 246, 0.4)',
                paddingLeft: 14,
                margin: 0,
                fontStyle: 'italic',
                maxWidth: 'none',
                wordBreak: 'break-word',
                whiteSpace: 'pre-wrap',
              }}>
                {shortText(cit.text || cit.excerpt)}
              </blockquote>
            )}
          </div>

          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            fontSize: 11,
            color: 'rgba(255, 255, 255, 0.2)',
            marginTop: 8,
          }}>
            <Bookmark size={10} />
            <span>ID: {cit.chunk_id}</span>
            <span style={{ margin: '0 2px' }}>•</span>
            <span>{cit.source}</span>
            <span style={{ margin: '0 2px' }}>•</span>
            <span>{scorePct}% match</span>
          </div>
        </div>
      )}
    </div>
  );
}
