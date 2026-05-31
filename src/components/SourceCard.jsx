/**
 * SourceCard.jsx  —  FIXED
 * Shows: Book Name | Page Number | Confidence | Snippet | YouTube link
 * 
 * Fix: previously showed only "p." because:
 *   - citation.book_name was undefined (field name mismatch)
 *   - excerpt was not rendered unless expanded
 *   - confidence badge was missing when score < threshold
 * 
 * Drop into: frontend/src/components/SourceCard.jsx
 */

import React, { useState } from 'react'
import ConfidenceBadge from './ConfidenceBadge'

const YOUTUBE_BASE = 'https://www.youtube.com/results?search_query='

// Safely get a field from citation, trying multiple possible key names
function field(obj, ...keys) {
  for (const k of keys) {
    const v = obj[k]
    if (v !== undefined && v !== null && v !== '') return v
  }
  return null
}

const TYPE_ICON = {
  music:    '🎵',
  research: '🔬',
  audio:    '🔊',
  theory:   '📖',
}

export default function SourceCard({ citation, index = 0 }) {
  const [expanded, setExpanded] = useState(true)   // open by default so users see content

  if (!citation) return null

  // ── Safely extract all fields (handles snake_case, camelCase, and missing) ──
  const bookName   = field(citation, 'book_name', 'bookName', 'title', 'source_name') || 'Unknown Source'
  const pageNum    = field(citation, 'page_number', 'pageNumber', 'page')
  const confidence = field(citation, 'confidence', 'score', 'confidence_score') || 0
  const confLabel  = field(citation, 'confidence_label', 'confidenceLabel') || null
  const excerpt    = field(citation, 'excerpt', 'snippet', 'text', 'content') || ''
  const sourceFile = field(citation, 'source', 'file_path', 'filepath') || ''
  const chunkType  = field(citation, 'type', 'category', 'chunk_type') || 'theory'
  const song       = field(citation, 'song') || ''
  const composer   = field(citation, 'composer') || ''
  const melakarta  = field(citation, 'melakarta') || ''
  const shruti     = field(citation, 'shruti') || ''

  const ytQuery = encodeURIComponent(`Carnatic music ${bookName} ${chunkType}`)
  const youtubeUrl = field(citation, 'youtube_url', 'youtubeUrl', 'youtube')
  const ytUrl   = youtubeUrl || (YOUTUBE_BASE + ytQuery)
  const icon    = TYPE_ICON[chunkType] || '📖'

  // Shorten file path to filename only
  const fileName = sourceFile
    ? sourceFile.replace(/\\/g, '/').split('/').pop()
    : ''

  return (
    <div
      style={{
        background: 'var(--bg-card2, #161f30)',
        border: '1px solid var(--border, rgba(99,112,175,.18))',
        borderRadius: 10,
        overflow: 'hidden',
        transition: 'border-color .18s',
        animation: `fadeUp .3s ease ${index * 0.06}s both`,
      }}
      onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--border-bright, rgba(139,92,246,.35))'}
      onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border, rgba(99,112,175,.18))'}
    >
      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div style={{ padding: '10px 14px', display: 'flex', alignItems: 'flex-start', gap: 10 }}>

        {/* Type icon */}
        <div style={{
          width: 30, height: 30, borderRadius: 7, flexShrink: 0,
          background: 'linear-gradient(135deg,rgba(139,92,246,.15),rgba(59,130,246,.15))',
          border: '1px solid rgba(139,92,246,.25)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14,
        }}>
          {icon}
        </div>

        {/* Book name + meta row */}
        <div style={{ flex: 1, minWidth: 0 }}>
          {/* Book name — always visible */}
          <p style={{
            fontSize: 13, fontWeight: 600,
            color: 'var(--text-primary, #f1f5f9)',
            overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
            marginBottom: 5,
          }}>
            {chunkType === 'music' && song ? `${song} (${composer})` : bookName}
          </p>

          {/* Meta pills row */}
          <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>

            {/* Page number */}
            {pageNum != null && (
              <span style={{
                fontSize: 11, fontFamily: 'var(--font-mono, monospace)',
                padding: '2px 8px', borderRadius: 5,
                background: 'rgba(59,130,246,.12)',
                border: '0.5px solid rgba(59,130,246,.25)',
                color: 'var(--blue-light, #60a5fa)',
              }}>
                Page {pageNum}
              </span>
            )}

            {/* Confidence badge */}
            {confidence > 0 && (
              <ConfidenceBadge score={confidence} label={confLabel} />
            )}

            {/* Type pill */}
            <span style={{
              fontSize: 10.5, padding: '2px 8px', borderRadius: 5,
              background: 'rgba(139,92,246,.12)',
              border: '0.5px solid rgba(139,92,246,.2)',
              color: 'var(--purple-light, #a78bfa)',
              textTransform: 'capitalize',
            }}>
              {chunkType}
            </span>

          </div>
        </div>

        {/* Expand / collapse button */}
        <button
          onClick={() => setExpanded(e => !e)}
          style={{
            flexShrink: 0, padding: '3px 8px', borderRadius: 5,
            background: 'var(--bg-hover, #1a2540)',
            border: '1px solid var(--border, rgba(99,112,175,.18))',
            color: 'var(--text-muted, #64748b)', fontSize: 11,
            transition: '.15s',
          }}
          title={expanded ? 'Collapse' : 'Expand'}
        >
          {expanded ? '▲' : '▼'}
        </button>
      </div>

      {/* ── Excerpt (always shown when expanded) ───────────────────────────── */}
      {expanded && excerpt && (
        <div style={{
          padding: '10px 14px',
          borderTop: '1px solid var(--border, rgba(99,112,175,.18))',
          background: 'rgba(0,0,0,.18)',
          animation: 'fadeIn .2s ease',
        }}>
          {/* Snippet label */}
          <p style={{
            fontSize: 10, color: 'var(--text-muted, #64748b)',
            textTransform: 'uppercase', letterSpacing: '.06em',
            marginBottom: 6,
          }}>
            Snippet
          </p>
          <p style={{
            fontSize: 12.5,
            color: 'var(--text-secondary, #94a3b8)',
            lineHeight: 1.7,
            fontStyle: 'italic',
            borderLeft: '2px solid var(--purple, #8b5cf6)',
            paddingLeft: 10,
            wordBreak: 'break-word',
          }}>
            "{excerpt}"
          </p>
        </div>
      )}

      {/* ── Footer actions ──────────────────────────────────────────────────── */}
      <div style={{
        padding: '8px 14px',
        borderTop: '1px solid var(--border, rgba(99,112,175,.18))',
        display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap',
      }}>

        {/* Shruti Tag */}
        {shruti && (
          <span style={{
            display: 'inline-flex', alignItems: 'center', gap: 5,
            padding: '4px 11px', borderRadius: 6,
            background: 'rgba(16,185,129,.1)',
            border: '0.5px solid rgba(16,185,129,.25)',
            color: '#34d399', fontSize: 11.5, fontWeight: 500,
          }}>
            Shruti: {shruti}
          </span>
        )}

        {/* YouTube link */}
        {youtubeUrl && (
          <a
            href={youtubeUrl}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 5,
              padding: '4px 11px', borderRadius: 6,
              background: 'rgba(239,68,68,.1)',
              border: '0.5px solid rgba(239,68,68,.25)',
              color: '#f87171', fontSize: 11.5, fontWeight: 500,
              transition: '.15s', textDecoration: 'none',
            }}
            onMouseEnter={e => e.currentTarget.style.background = 'rgba(239,68,68,.2)'}
            onMouseLeave={e => e.currentTarget.style.background = 'rgba(239,68,68,.1)'}
          >
            ▶ Open Recording
          </a>
        )}

        {/* Filename */}
        {fileName && (
          <span style={{
            fontSize: 10.5,
            color: 'var(--text-faint, #374151)',
            overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
            flex: 1,
          }}>
            {fileName}
          </span>
        )}
      </div>
    </div>
  )
}
