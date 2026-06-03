import React, { useState, useEffect } from 'react'
import { Book, Music, FileText, Star } from 'lucide-react'
import { api } from '../services/api'

const LIBRARY_BOOKS = [
  { title: 'South Indian Music (Book I - VI)', author: 'Prof. P. Sambamoorthy', type: 'Theory', pages: 1240 },
  { title: 'Ragas in Carnatic Music', author: 'Dr. S. Bhagyalekshmy', type: 'Musicology', pages: 412 },
  { title: 'The Spiritual Heritage of Tyagaraja', author: 'V. Raghavan', type: 'Biography', pages: 622 },
  { title: 'Carnatic Music Compositions', author: 'T. K. Govinda Rao', type: 'Repertoire', pages: 850 },
  { title: 'Shruti in Indian Music', author: 'B. C. Deva', type: 'Acoustics', pages: 156 },
]

export default function LibraryPage() {
  const [stats, setStats] = useState(null)
  
  useEffect(() => {
    let isMounted = true;
    api.getStats().then(data => {
      if (isMounted) setStats(data);
    }).catch(e => {
      console.error(e);
    });
    return () => { isMounted = false; };
  }, []);

  return (
    <div className="animate-fade-in" style={{ padding: '40px 48px', height: '100%', overflowY: 'auto', display: 'flex', flexDirection: 'column', position: 'relative' }}>
      
      {/* Background Motif */}
      <div style={{ position: 'fixed', bottom: -50, right: -50, fontSize: 300, opacity: 0.015, color: 'var(--peacock)', pointerEvents: 'none', zIndex: 0 }}>
        📖
      </div>

      <div style={{ marginBottom: 48, position: 'relative', zIndex: 1 }}>
        <h1 style={{ fontSize: '2.8rem', fontWeight: 700, fontFamily: 'var(--font-serif)', color: 'var(--peacock)', marginBottom: 12 }}>
          Reference Library
        </h1>
        <p className="cultural-text" style={{ color: 'var(--text-secondary)', fontSize: '1.15rem', fontStyle: 'italic', fontFamily: 'var(--font-serif)' }}>
          The curated collection of classical knowledge powering CarnaticGPT.
        </p>
      </div>

      {/* Stats Dashboard — Digital Gurukul scope */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '24px', marginBottom: '56px', position: 'relative', zIndex: 1 }}>
          <div className="elevated-card" style={{ display: 'flex', alignItems: 'center', gap: 20, border: '1px solid var(--border)', background: '#FFFFFF' }}>
             <div style={{ width: 56, height: 56, borderRadius: '50%', background: 'rgba(139, 74, 54, 0.08)', color: 'var(--peacock)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
               <Book size={26} />
             </div>
             <div>
               <div style={{ fontSize: '1.8rem', color: 'var(--text-primary)', fontFamily: 'var(--font-serif)', fontWeight: 700 }}>5</div>
               <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px', fontWeight: 600 }}>Books Indexed</div>
             </div>
          </div>
          <div className="elevated-card" style={{ display: 'flex', alignItems: 'center', gap: 20, border: '1px solid var(--border)', background: '#FFFFFF' }}>
             <div style={{ width: 56, height: 56, borderRadius: '50%', background: 'rgba(139, 74, 54, 0.08)', color: 'var(--peacock)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
               <Music size={26} />
             </div>
             <div>
               <div style={{ fontSize: '1.8rem', color: 'var(--text-primary)', fontFamily: 'var(--font-serif)', fontWeight: 700 }}>72</div>
               <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px', fontWeight: 600 }}>Melakarta Ragas</div>
             </div>
          </div>
          <div className="elevated-card" style={{ display: 'flex', alignItems: 'center', gap: 20, border: '1px solid var(--border)', background: '#FFFFFF' }}>
             <div style={{ width: 56, height: 56, borderRadius: '50%', background: 'rgba(139, 74, 54, 0.08)', color: 'var(--peacock)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
               <Star size={26} />
             </div>
             <div>
               <div style={{ fontSize: '1.8rem', color: 'var(--text-primary)', fontFamily: 'var(--font-serif)', fontWeight: 700 }}>15,128</div>
               <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px', fontWeight: 600 }}>Knowledge Chunks</div>
             </div>
          </div>
        </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: '32px', paddingBottom: '16px', borderBottom: '1px solid var(--border)' }}>
        <FileText size={24} color="var(--peacock)" />
        <h2 style={{ fontSize: '1.5rem', fontFamily: 'var(--font-serif)', fontWeight: 700, color: 'var(--text-primary)' }}>
           Archived Texts
        </h2>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 24, position: 'relative', zIndex: 1 }}>
        {LIBRARY_BOOKS.map((book, i) => (
          <div key={i} className="elevated-card" style={{
            display: 'flex', flexDirection: 'column', gap: 16,
            background: '#FFFFFF', border: '1px solid var(--border)', borderRadius: '20px',
            transition: 'all var(--transition)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div style={{
                width: 48, height: 48, borderRadius: '12px',
                background: 'var(--bg-app)', color: 'var(--peacock)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <Book size={20} />
              </div>
              <span style={{
                fontSize: 11, padding: '4px 12px', borderRadius: 'var(--radius-full)',
                background: 'rgba(139, 74, 54, 0.08)', color: 'var(--peacock)',
                textTransform: 'uppercase', letterSpacing: '1px', fontWeight: 600
              }}>
                {book.type}
              </span>
            </div>

            <div>
              <h3 style={{ fontSize: 18, fontWeight: 700, fontFamily: 'var(--font-serif)', color: 'var(--text-primary)', marginBottom: 8, lineHeight: 1.4 }}>
                {book.title}
              </h3>
              <p style={{ fontSize: 14, color: 'var(--text-muted)', fontFamily: 'var(--font-sans)' }}>
                {book.author}
              </p>
            </div>

            <div style={{ marginTop: 'auto', paddingTop: 20, borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: 13, color: 'var(--text-muted)', fontWeight: 500 }}>
                {book.pages} pages digitized
              </span>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--emerald)', fontSize: 13, fontWeight: 600 }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--emerald)' }} /> Indexed
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
