import React, { useState } from 'react'
import ConfidenceBadge from './ConfidenceBadge'
import { FileText, Music, BookOpen, Volume2, ChevronDown, ChevronUp, PlayCircle } from 'lucide-react'

const YOUTUBE_BASE = 'https://www.youtube.com/results?search_query='

function field(obj, ...keys) {
  for (const k of keys) {
    const v = obj[k]
    if (v !== undefined && v !== null && v !== '') return v
  }
  return null
}

const TYPE_ICON = {
  music:    <Music size={18} />,
  research: <FileText size={18} />,
  audio:    <Volume2 size={18} />,
  theory:   <BookOpen size={18} />,
}

export default function SourceCard({ citation, index = 0 }) {
  const [expanded, setExpanded] = useState(false)

  if (!citation) return null

  const bookName   = field(citation, 'book_name', 'bookName', 'title', 'source_name') || 'Unknown Source'
  const pageNum    = field(citation, 'page_number', 'pageNumber', 'page')
  const confidence = field(citation, 'confidence', 'score', 'confidence_score') || 0
  const confLabel  = field(citation, 'confidence_label', 'confidenceLabel') || null
  const excerpt    = field(citation, 'excerpt', 'snippet', 'text', 'content') || ''
  const chunkType  = field(citation, 'type', 'category', 'chunk_type') || 'theory'
  const song       = field(citation, 'song') || ''
  const composer   = field(citation, 'composer') || ''
  const shruti     = field(citation, 'shruti') || ''

  const ytQuery = encodeURIComponent(`Carnatic music ${bookName} ${chunkType}`)
  const youtubeUrl = field(citation, 'youtube_url', 'youtubeUrl', 'youtube')
  const ytUrl   = youtubeUrl || (YOUTUBE_BASE + ytQuery)
  const icon    = TYPE_ICON[chunkType] || <BookOpen size={18} />

  return (
    <div
      className="elevated-card"
      style={{
        padding: 0,
        overflow: 'hidden',
        animation: `fadeIn .3s ease ${index * 0.05}s both`,
      }}
    >
      <div 
        style={{ padding: '16px', display: 'flex', alignItems: 'flex-start', gap: 16, cursor: 'pointer', background: expanded ? 'var(--bg-surface-hover)' : 'transparent', transition: 'background var(--transition-fast)' }}
        onClick={() => setExpanded(e => !e)}
      >
        <div style={{
          width: 40, height: 40, borderRadius: 'var(--radius-sm)', flexShrink: 0,
          background: 'rgba(2, 132, 199, 0.1)', color: 'var(--peacock)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          {icon}
        </div>

        <div style={{ flex: 1, minWidth: 0 }}>
          <p style={{
            fontSize: 15, fontWeight: 700,
            color: 'var(--text-primary)',
            fontFamily: 'var(--font-sans)',
            overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
            marginBottom: 4,
          }}>
            {chunkType === 'music' && song ? `${song} (${composer})` : bookName}
          </p>

          <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
            {pageNum != null && (
              <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)' }}>
                Page {pageNum}
              </span>
            )}
            
            {pageNum != null && <span style={{ color: 'var(--border-strong)' }}>•</span>}

            <span style={{
              fontSize: 11, padding: '2px 8px', borderRadius: 'var(--radius-full)',
              background: 'rgba(236, 72, 153, 0.1)', color: 'var(--lotus-pink)',
              textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: 800
            }}>
              {chunkType}
            </span>

            {confidence > 0 && <ConfidenceBadge score={confidence} label={confLabel} />}
          </div>
        </div>

        <div style={{ color: 'var(--text-muted)' }}>
          {expanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
        </div>
      </div>

      {expanded && excerpt && (
        <div style={{
          padding: '16px 20px',
          borderTop: '1px solid var(--border)',
          background: 'var(--bg-surface)',
        }}>
          <p style={{
            fontSize: 15,
            color: 'var(--text-secondary)',
            lineHeight: 1.6,
            fontFamily: 'var(--font-serif)',
            borderLeft: '3px solid var(--peacock)',
            paddingLeft: 16,
            wordBreak: 'break-word',
          }}>
            "{excerpt}"
          </p>
        </div>
      )}

      {(shruti || youtubeUrl || chunkType === 'music') && (
        <div style={{
          padding: '12px 16px',
          borderTop: '1px solid var(--border)',
          display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap',
          background: 'var(--bg-surface-hover)'
        }}>
          {shruti && (
            <span style={{
              fontSize: 12, fontWeight: 700, color: 'var(--peacock)',
              background: 'rgba(2, 132, 199, 0.1)', padding: '4px 10px', borderRadius: 'var(--radius-sm)'
            }}>
              Shruti: {shruti}
            </span>
          )}
          
          <a
            href={ytUrl}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 6,
              fontSize: 13, fontWeight: 700, color: '#EF4444',
              padding: '4px 10px', borderRadius: 'var(--radius-sm)',
              background: 'rgba(239, 68, 68, 0.1)', textDecoration: 'none'
            }}
          >
            <PlayCircle size={16} />
            Listen on YouTube
          </a>
        </div>
      )}
    </div>
  )
}
