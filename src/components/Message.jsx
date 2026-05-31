import React, { useState } from 'react';
import { ThumbsUp, ThumbsDown, BookOpen } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import AudioPlayer from './AudioPlayer';
import CitationCard from './CitationCard';
import { api } from '../services/api';
import ragasData from '../data/ragas.json';

export default function Message({ msg }) {
  const isUser = msg.sender === 'user';
  const [rated, setRated] = useState(null); // 'up', 'down', null
  
  const handleFeedback = async (val) => {
    if (!msg.id) return;
    try {
      const rating = val === 'up' ? 1 : -1;
      await api.submitFeedback(msg.id, rating);
      setRated(val);
    } catch (e) {
      console.error("Feedback failed: ", e);
    }
  };
  
  const normalize = (str) => str.toLowerCase().replace(/[\s_-]+/g, '');
  const contentNormalized = normalize(msg.content);

  // Find all ragas mentioned in the AI response to support comparison playback
  let detectedRagas = ragasData
    .filter(r => contentNormalized.includes(normalize(r.name)))
    .map(r => r.name);

  // Priority to the backend detected entity if any
  if (msg.detected_raga) {
    const backendNormalized = normalize(msg.detected_raga);
    const backendMatch = ragasData.find(r => normalize(r.name) === backendNormalized);
    
    if (backendMatch && !detectedRagas.includes(backendMatch.name)) {
      detectedRagas.unshift(backendMatch.name);
    }
  }

  return (
    <div style={{
      display: 'flex',
      justifyContent: isUser ? 'flex-end' : 'flex-start',
      width: '100%'
    }} className="animate-fade-in">
      <div className={isUser ? '' : 'glass-card'} style={{
        maxWidth: '80%',
        padding: '20px',
        borderRadius: 'var(--border-radius-lg)',
        background: isUser ? 'linear-gradient(135deg, rgba(88, 30, 168, 0.45) 0%, rgba(139, 92, 246, 0.35) 100%)' : 'rgba(28, 36, 58, 0.35)',
        border: isUser ? '1px solid rgba(139, 92, 246, 0.2)' : '1px solid var(--glass-border)',
        boxShadow: isUser ? 'none' : '0 4px 20px 0 rgba(0, 0, 0, 0.15)'
      }}>
        {/* Overall Confidence Badge */}
        {!isUser && msg.confidence && (
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '0.7rem',
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            background: msg.confidence === "High Confidence" 
              ? 'rgba(22, 219, 204, 0.12)' 
              : msg.confidence === "Medium Confidence" 
                ? 'rgba(219, 166, 22, 0.12)' 
                : 'rgba(219, 68, 85, 0.12)',
            color: msg.confidence === "High Confidence" 
              ? 'hsl(var(--accent-teal))' 
              : msg.confidence === "Medium Confidence" 
                ? 'hsl(var(--accent-gold))' 
                : 'hsl(355, 85%, 65%)',
            border: msg.confidence === "High Confidence"
              ? '1px solid rgba(22, 219, 204, 0.2)'
              : msg.confidence === "Medium Confidence"
                ? '1px solid rgba(219, 166, 22, 0.2)'
                : '1px solid rgba(219, 68, 85, 0.2)',
            padding: '3px 10px',
            borderRadius: '20px',
            marginBottom: '12px',
            boxShadow: msg.confidence === "High Confidence" 
              ? '0 0 10px rgba(22, 219, 204, 0.1)' 
              : msg.confidence === "Medium Confidence"
                ? '0 0 10px rgba(219, 166, 22, 0.1)'
                : 'none'
          }}>
            <span style={{ 
              display: 'inline-block', 
              width: '6px', 
              height: '6px', 
              borderRadius: '50%', 
              backgroundColor: 'currentColor',
              boxShadow: '0 0 6px currentColor'
            }}></span>
            {msg.confidence}
          </div>
        )}

        {/* Message Content */}
        <div style={{
          fontSize: '0.95rem',
          lineHeight: '1.6',
          color: 'hsl(var(--text-primary))'
        }} className="markdown-content">
          <ReactMarkdown>{msg.content}</ReactMarkdown>
        </div>
        
        {/* Dynamic Multiple Audio Players for Detected Ragas */}
        {!isUser && detectedRagas.length > 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '16px' }}>
            {detectedRagas.map(ragaName => (
              <AudioPlayer key={ragaName} ragaName={ragaName} />
            ))}
          </div>
        )}

        
        {/* Source Citations Shelf */}
        {!isUser && msg.citations && msg.citations.length > 0 && (
          <div style={{ marginTop: '20px', paddingTop: '16px', borderTop: '1px solid var(--glass-border)' }}>
            <span style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '0.75rem',
              color: 'hsl(var(--accent-teal))',
              fontWeight: 700,
              letterSpacing: '0.05em',
              marginBottom: '14px'
            }}>
              <BookOpen size={13} /> CITATIONS & SOURCE ARCHIVES
            </span>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {msg.citations.map((cit, idx) => (
                <CitationCard key={cit.chunk_id || idx} cit={cit} />
              ))}
            </div>
          </div>
        )}
        
        {/* Feedback Bar */}
        {!isUser && msg.id && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginTop: '16px',
            paddingTop: '12px',
            borderTop: '1px dashed var(--glass-border)',
            fontSize: '0.75rem',
            color: 'hsl(var(--text-secondary))'
          }}>
            <span>Was this answer grounded in the sources?</span>
            <div style={{ display: 'flex', gap: '12px' }}>
              <button onClick={() => handleFeedback('up')} style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                color: rated === 'up' ? 'hsl(var(--accent-teal))' : 'hsl(var(--text-secondary))',
                display: 'flex',
                alignItems: 'center',
                gap: '4px'
              }}>
                <ThumbsUp size={13} /> Helpful
              </button>
              <button onClick={() => handleFeedback('down')} style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                color: rated === 'down' ? 'red' : 'hsl(var(--text-secondary))',
                display: 'flex',
                alignItems: 'center',
                gap: '4px'
              }}>
                <ThumbsDown size={13} /> Unreliable
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
