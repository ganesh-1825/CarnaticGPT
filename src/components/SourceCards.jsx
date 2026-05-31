/**
 * SourceCards.jsx  —  CarnaticGPT source + citation display
 *
 * Props:
 *   sources    []   — array from response.sources
 *                     each: { text, metadata:{ book_name, page_number, type,
 *                                              source, score, ... }, score }
 *   citations  []   — array from response.citations
 *                     each: { book_name, page_number, source, confidence,
 *                             confidence_label, snippet, song, raga,
 *                             composer, youtube }
 *
 * Usage:
 *   import SourceCards from './SourceCards';
 *   <SourceCards sources={response.sources} citations={response.citations} />
 */

import { useState } from "react";

// ── Confidence ────────────────────────────────────────────────────────────────
function tier(score) {
  const s = score <= 1 ? score * 100 : score;          // normalise 0-1 → 0-100
  if (s >= 60) return { label: "High",   dot: "#22c55e", bg: "rgba(34,197,94,.12)",  border: "rgba(34,197,94,.3)"  };
  if (s >= 25) return { label: "Medium", dot: "#f59e0b", bg: "rgba(245,158,11,.12)", border: "rgba(245,158,11,.3)" };
  return              { label: "Low",    dot: "#ef4444", bg: "rgba(239,68,68,.12)",  border: "rgba(239,68,68,.3)"  };
}

function ConfBadge({ score }) {
  if (score == null) return null;
  const s  = score <= 1 ? score * 100 : score;
  const t  = tier(s);
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 5,
      padding: "2px 9px", borderRadius: 20, fontSize: 11, fontWeight: 600,
      color: t.dot, background: t.bg, border: `1px solid ${t.border}`,
      flexShrink: 0,
    }}>
      <span style={{ width: 6, height: 6, borderRadius: "50%", background: t.dot }} />
      {t.label} · {Math.round(s)}%
    </span>
  );
}

// ── Chevron ───────────────────────────────────────────────────────────────────
function Chevron({ open }) {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
      <polyline points={open ? "18 15 12 9 6 15" : "6 9 12 15 18 9"} />
    </svg>
  );
}

// ── Type chip colours ─────────────────────────────────────────────────────────
const TYPE_CLR = {
  theory:         { fg: "#818cf8", bg: "rgba(129,140,248,.1)", bd: "rgba(129,140,248,.3)" },
  research:       { fg: "#fb923c", bg: "rgba(251,146,60,.1)",  bd: "rgba(251,146,60,.3)"  },
  music:          { fg: "#34d399", bg: "rgba(52,211,153,.1)",  bd: "rgba(52,211,153,.3)"  },
  audio_metadata: { fg: "#fbbf24", bg: "rgba(251,191,36,.1)",  bd: "rgba(251,191,36,.3)"  },
};
const typeClr = (t) => TYPE_CLR[t] || { fg: "#94a3b8", bg: "rgba(148,163,184,.1)", bd: "rgba(148,163,184,.3)" };

// ── Helpers ───────────────────────────────────────────────────────────────────
function bookName(meta = {}, fallback = "") {
  if (meta.book_name && meta.book_name !== "unknown" && meta.book_name !== "undefined")
    return meta.book_name;
  const src = meta.source || fallback;
  return src.replace(/\\/g, "/").split("/").pop().replace(/\.pdf$/i, "") || "Unknown Source";
}

function cleanSnippet(text = "") {
  return text
    .split("\n")
    .filter(ln => {
      const t   = ln.trim();
      const alp = (t.match(/[a-zA-Z]/g) || []).length;
      return t.length > 15 && alp / Math.max(t.length, 1) >= 0.38;
    })
    .join(" ")
    .replace(/\s{2,}/g, " ")
    .slice(0, 280);
}

// ══════════════════════════════════════════════════════════════════════════════
// SOURCE CARD  (from response.sources — faiss_store format)
// ══════════════════════════════════════════════════════════════════════════════
function SourceCard({ item, idx }) {
  const [open, setOpen] = useState(false);

  // faiss_store returns: { text, metadata:{...}, score }
  const meta   = item.metadata || {};
  const score  = item.score ?? meta.score;
  const name   = bookName(meta);
  const page   = meta.page_number ?? meta.page;
  const type   = meta.type || meta.category || "theory";
  const tc     = typeClr(type);
  const snip   = cleanSnippet(item.text || meta.content || "");

  return (
    <div style={{
      borderRadius: 10,
      border: "1px solid rgba(255,255,255,.07)",
      borderLeft: `3px solid ${tc.fg}`,
      background: "rgba(255,255,255,.02)",
      overflow: "hidden",
    }}>
      {/* ── Header ── */}
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          width: "100%", padding: "10px 14px",
          display: "flex", alignItems: "center",
          justifyContent: "space-between", gap: 10,
          background: "transparent", border: "none",
          cursor: "pointer", color: "#e2e8f0", textAlign: "left",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8, minWidth: 0, flex: 1 }}>
          {/* type chip */}
          <span style={{
            flexShrink: 0, fontSize: 10, fontWeight: 700,
            letterSpacing: "0.06em", textTransform: "uppercase",
            padding: "2px 8px", borderRadius: 10,
            color: tc.fg, background: tc.bg, border: `1px solid ${tc.bd}`,
          }}>
            {type}
          </span>
          {/* book + page */}
          <div style={{ minWidth: 0 }}>
            <div style={{
              fontSize: 12, fontWeight: 600, color: "#cbd5e1",
              overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
            }}>
              {name}
            </div>
            {page != null && page > 0 && (
              <div style={{ fontSize: 10, color: "#64748b", marginTop: 1 }}>
                Page {page}
              </div>
            )}
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
          <ConfBadge score={score} />
          <span style={{ color: "#475569" }}><Chevron open={open} /></span>
        </div>
      </button>

      {/* ── Expanded body ── */}
      {open && (
        <div style={{ padding: "0 14px 14px", borderTop: "1px solid rgba(255,255,255,.05)" }}>
          {meta.source && (
            <div style={{
              fontSize: 10, color: "#475569", marginTop: 10, marginBottom: 6,
              fontFamily: "monospace", wordBreak: "break-all",
            }}>
              {meta.source}
            </div>
          )}
          {snip
            ? <p style={{ margin: "8px 0 0", fontSize: 12, color: "#94a3b8", lineHeight: 1.75 }}>{snip}</p>
            : <p style={{ margin: "8px 0 0", fontSize: 12, color: "#475569", fontStyle: "italic" }}>No readable text.</p>
          }
          <div style={{ display: "flex", flexWrap: "wrap", gap: "4px 14px", marginTop: 10 }}>
            {meta.char_count   && <span style={{ fontSize: 10, color: "#475569" }}>{meta.char_count} chars</span>}
            {meta.chunk_index != null && <span style={{ fontSize: 10, color: "#475569" }}>Chunk #{meta.chunk_index}</span>}
          </div>
        </div>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// CITATION ROW  (from response.citations — cleaned format)
// ══════════════════════════════════════════════════════════════════════════════
function CitationRow({ c, num }) {
  const name   = c.book_name || bookName({}, c.source || "");
  const snip   = cleanSnippet(c.snippet || "");
  const hasYT  = !!c.youtube;

  return (
    <div style={{
      display: "flex", gap: 10, alignItems: "flex-start",
      padding: "9px 0",
      borderBottom: "1px solid rgba(255,255,255,.04)",
    }}>
      <span style={{
        flexShrink: 0, width: 20, height: 20, borderRadius: "50%",
        background: "rgba(99,102,241,.15)",
        border: "1px solid rgba(99,102,241,.3)",
        color: "#818cf8", fontSize: 10, fontWeight: 700,
        display: "flex", alignItems: "center", justifyContent: "center",
      }}>
        {num}
      </span>

      <div style={{ minWidth: 0, flex: 1 }}>
        {/* book + page + confidence */}
        <div style={{
          display: "flex", alignItems: "baseline",
          flexWrap: "wrap", gap: "0 10px",
        }}>
          <span style={{ fontSize: 12, fontWeight: 600, color: "#cbd5e1" }}>{name}</span>
          {c.page_number > 0 && (
            <span style={{ fontSize: 11, color: "#64748b" }}>p. {c.page_number}</span>
          )}
          {c.confidence != null && (
            <ConfBadge score={c.confidence} />
          )}
        </div>

        {/* music metadata row */}
        {(c.song || c.raga || c.composer) && (
          <div style={{ display: "flex", flexWrap: "wrap", gap: "3px 12px", marginTop: 4, fontSize: 11 }}>
            {c.song     && <span style={{ color: "#94a3b8" }}>🎵 <b style={{ color: "#e2e8f0" }}>{c.song}</b></span>}
            {c.raga     && <span style={{ color: "#94a3b8" }}>Raga: <b style={{ color: "#818cf8" }}>{c.raga}</b></span>}
            {c.composer && <span style={{ color: "#94a3b8" }}>By: <b style={{ color: "#e2e8f0" }}>{c.composer}</b></span>}
          </div>
        )}

        {/* snippet */}
        {snip && (
          <p style={{ margin: "5px 0 0", fontSize: 11, color: "#64748b", lineHeight: 1.65 }}>
            {snip}
          </p>
        )}

        {/* YouTube link */}
        {hasYT && (
          <a
            href={c.youtube}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: "inline-flex", alignItems: "center", gap: 5,
              marginTop: 6, padding: "4px 11px", borderRadius: 20,
              background: "rgba(239,68,68,.1)", border: "1px solid rgba(239,68,68,.25)",
              color: "#f87171", fontSize: 11, fontWeight: 600,
              textDecoration: "none",
            }}
          >
            ▶ Watch on YouTube
          </a>
        )}
      </div>
    </div>
  );
}


// ══════════════════════════════════════════════════════════════════════════════
// MAIN EXPORT
// ══════════════════════════════════════════════════════════════════════════════
export default function SourceCards({ sources = [], citations = [] }) {
  const [tab, setTab] = useState(citations.length > 0 ? "citations" : "sources");

  const hasSources   = sources.length > 0;
  const hasCitations = citations.length > 0;
  if (!hasSources && !hasCitations) return null;

  const tabBtn = (id, label, count) => (
    <button
      key={id}
      onClick={() => setTab(id)}
      style={{
        padding: "5px 14px", borderRadius: 20,
        fontSize: 11, fontWeight: 700, letterSpacing: "0.04em",
        border: "1px solid",
        borderColor: tab === id ? "rgba(99,102,241,.4)" : "rgba(255,255,255,.08)",
        background:  tab === id ? "rgba(99,102,241,.12)" : "transparent",
        color:       tab === id ? "#818cf8" : "#64748b",
        cursor: "pointer",
      }}
    >
      {label} {count}
    </button>
  );

  return (
    <div style={{ marginTop: 12 }}>
      {/* Tabs */}
      <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
        {hasCitations && tabBtn("citations", "🔖 Citations", citations.length)}
        {hasSources   && tabBtn("sources",   "📄 Sources",   sources.length)}
      </div>

      {/* Citations tab */}
      {tab === "citations" && hasCitations && (
        <div style={{
          padding: "4px 12px",
          background: "rgba(255,255,255,.02)",
          border: "1px solid rgba(255,255,255,.07)",
          borderRadius: 10,
        }}>
          {citations.map((c, i) => <CitationRow key={i} c={c} num={i + 1} />)}
        </div>
      )}

      {/* Sources tab */}
      {tab === "sources" && hasSources && (
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {sources.map((s, i) => <SourceCard key={s.metadata?.id || i} item={s} idx={i} />)}
        </div>
      )}
    </div>
  );
}
