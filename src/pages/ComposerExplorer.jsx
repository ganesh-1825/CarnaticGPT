import React, { useState } from 'react';
import { Search, User, Award, Quote } from 'lucide-react';

const COMPOSERS_DATABASE = [
  { name: 'Tyagaraja', title: 'The Trinity of Carnatic Music', era: '1767 – 1847', born: 'Thiruvarur, Tamil Nadu', signature: 'Tyagaraja (integrated in kritis)', description: 'One of the greatest composers of Carnatic music. He composed thousands of devotional compositions, most in Telugu and in praise of Lord Rama. Famous for the Pancharatna Kritis (five gems).', works: ['Endaro Mahanubhavulu', 'Jagadananda Karaka', 'Sadinchane'] },
  { name: 'Muthuswami Dikshitar', title: 'The Trinity of Carnatic Music', era: '1775 – 1835', born: 'Thiruvarur, Tamil Nadu', signature: 'Guruguha', description: 'Renowned for his detailed, slow-tempo (Chowka kala) compositions that explore the full aesthetic depth of ragas. He wrote mostly in Sanskrit. Famous for Kamalamba Navavarna and Vatapi Ganapatim.', works: ['Vatapi Ganapatim', 'Balagopala', 'Sri Subramanyaya Namaste'] },
  { name: 'Syama Sastri', title: 'The Trinity of Carnatic Music', era: '1762 – 1827', born: 'Thiruvarur, Tamil Nadu', signature: 'Syamakrishna', description: 'The oldest of the Trinity. Highly revered for his complex rhythmic structures, layam patterns, and composition of Swarajatis (especially the famous Amba Kamakshi Swarajati).', works: ['Amba Kamakshi (Swarajati)', 'Marivere Gati', 'Kanakasaila Viharini'] },
  { name: 'Purandara Dasa', title: 'Father of Carnatic Music', era: '1484 – 1564', born: 'Kshemapura, Karnataka', signature: 'Purandara Vittala', description: 'A Haridasa philosopher and composer. He systematized the entire pedagogy of Carnatic music, introducing introductory swara exercises (Sarali Varisais, Alankarams) in Mayamalavagowla.', works: ['Lambaodara Lakumikara', 'Gajavadana Beduve', 'Bhagyada Lakshmi Baramma'] },
];

export default function ComposerExplorer() {
  const [query, setQuery] = useState('');

  const filteredComposers = COMPOSERS_DATABASE.filter(c => 
    c.name.toLowerCase().includes(query.toLowerCase()) ||
    c.description.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div className="animate-fade-in" style={{ padding: '40px 48px', height: '100%', overflowY: 'auto', display: 'flex', flexDirection: 'column', position: 'relative' }}>
      
      {/* Background Motif */}
      <div style={{ position: 'fixed', bottom: -50, right: -50, fontSize: 300, opacity: 0.015, color: 'var(--peacock)', pointerEvents: 'none', zIndex: 0 }}>
        👤
      </div>

      <div style={{ marginBottom: 40, position: 'relative', zIndex: 1 }}>
        <h1 style={{ fontSize: '2.8rem', fontWeight: 700, fontFamily: 'var(--font-serif)', color: 'var(--peacock)', marginBottom: 12 }}>
          Composer Explorer
        </h1>
        <p className="cultural-text" style={{ color: 'var(--text-secondary)', fontSize: '1.15rem', fontStyle: 'italic', fontFamily: 'var(--font-serif)' }}>
          Discover the history, signatures, and contributions of classical music gurus.
        </p>
      </div>

      {/* Search Box */}
      <div style={{ position: 'relative', maxWidth: 480, marginBottom: 40, zIndex: 1 }}>
        <Search size={18} style={{ position: 'absolute', left: 16, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
        <input 
          type="text" 
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Search composers, signatures..."
          style={{
            width: '100%', padding: '14px 16px 14px 48px', fontSize: 15,
            borderRadius: '12px', border: '1px solid var(--border)',
            background: '#FFFFFF', color: 'var(--text-primary)', outline: 'none',
            boxShadow: 'var(--shadow-sm)', transition: 'all 0.25s'
          }}
          onFocus={e => { e.currentTarget.style.borderColor = 'var(--peacock)'; e.currentTarget.style.boxShadow = '0 0 0 3px rgba(139, 74, 54, 0.08)'; }}
          onBlur={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.boxShadow = 'var(--shadow-sm)'; }}
        />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(420px, 1fr))', gap: 32, position: 'relative', zIndex: 1 }}>
        {filteredComposers.map((comp, i) => (
          <div key={i} className="elevated-card" style={{
            display: 'flex', flexDirection: 'column', gap: 20,
            background: '#FFFFFF', border: '1px solid var(--border)', borderRadius: '20px',
            padding: '32px', transition: 'all var(--transition)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <div style={{
                width: 64, height: 64, borderRadius: '50%',
                background: 'rgba(139, 74, 54, 0.08)', color: 'var(--peacock)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <User size={30} />
              </div>
              <div>
                <h3 style={{ fontSize: 22, fontWeight: 700, fontFamily: 'var(--font-serif)', color: 'var(--peacock)', margin: 0 }}>
                  {comp.name}
                </h3>
                <span style={{ fontSize: 13, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  {comp.title} • {comp.era}
                </span>
              </div>
            </div>

            <p style={{ fontSize: 14.5, color: 'var(--text-secondary)', lineHeight: 1.6, margin: 0 }}>
              {comp.description}
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 12, borderTop: '1px solid var(--border)', paddingTop: 20 }}>
              <div style={{ display: 'flex', gap: 8, fontSize: 13.5, color: 'var(--text-secondary)' }}>
                <Award size={16} color="var(--peacock)" style={{ flexShrink: 0, marginTop: 2 }} />
                <span><strong>Ankita / Mudra (Signature):</strong> <em>{comp.signature}</em></span>
              </div>
              <div style={{ display: 'flex', gap: 8, fontSize: 13.5, color: 'var(--text-secondary)' }}>
                <Quote size={16} color="var(--peacock)" style={{ flexShrink: 0, marginTop: 2 }} />
                <span>
                  <strong>Masterpieces:</strong> {comp.works.join(', ')}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
