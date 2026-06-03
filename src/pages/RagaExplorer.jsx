import React, { useState } from 'react';
import { Search, Music, Play, HelpCircle } from 'lucide-react';

const RAGAS_DATABASE = [
  { name: 'Kalyani', melakarta: '65th Melakarta (Mechakalyani)', arohana: 'S R2 G3 M2 P D2 N3 S', avarohana: 'S N3 D2 P M2 G3 R2 S', notes: [130.81, 146.83, 164.81, 185.00, 196.00, 220.00, 246.94, 261.63], mood: 'Auspiciousness, peace, grandeur. Usually sung in the evening.' },
  { name: 'Mayamalavagowla', melakarta: '15th Melakarta', arohana: 'S R1 G3 M1 P D1 N3 S', avarohana: 'S N3 D1 P M1 G3 R1 S', notes: [130.81, 138.59, 164.81, 174.61, 196.00, 207.65, 246.94, 261.63], mood: 'Devotional, meditative, peaceful. The starter scale for beginners.' },
  { name: 'Bhairavi', melakarta: '20th Melakarta (Janya - Natabhairavi)', arohana: 'S R2 G2 M1 P D2 N2 S', avarohana: 'S N2 D1 P M1 G2 R2 S', notes: [130.81, 146.83, 155.56, 174.61, 196.00, 220.00, 233.08, 261.63], mood: 'Majestic, emotional depth, versatile. Represents devotion and pathos.' },
  { name: 'Mohanam', melakarta: 'Janya of Harikambhoji (Pentatonic)', arohana: 'S R2 G3 P D2 S', avarohana: 'S D2 P G3 R2 S', notes: [130.81, 146.83, 164.81, 196.00, 220.00, 261.63], mood: 'Joy, beauty, calmness. Universal five-tone scale sung at any time.' },
  { name: 'Hamsadhwani', melakarta: 'Janya of Dheerashankarabharanam', arohana: 'S R2 G3 P N3 S', avarohana: 'S N3 P G3 R2 S', notes: [130.81, 146.83, 164.81, 196.00, 246.94, 261.63], mood: 'Happiness, energy, devotion. Typically sung at the start of concerts.' },
  { name: 'Sankarabharanam', melakarta: '29th Melakarta (Dheerashankarabharanam)', arohana: 'S R2 G3 M1 P D2 N3 S', avarohana: 'S N3 D2 P M1 G3 R2 S', notes: [130.81, 146.83, 164.81, 174.61, 196.00, 220.00, 246.94, 261.63], mood: 'Grandeur, heroism, cosmic order. Equivalent to the Western major scale.' },
];

export default function RagaExplorer() {
  const [query, setQuery] = useState('');
  const [playingRaga, setPlayingRaga] = useState(null);

  const filteredRagas = RAGAS_DATABASE.filter(r => 
    r.name.toLowerCase().includes(query.toLowerCase()) ||
    r.melakarta.toLowerCase().includes(query.toLowerCase())
  );

  const playScale = (raga) => {
    if (playingRaga) return; // Prevent double play
    setPlayingRaga(raga.name);

    try {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      const ctx = new AudioContext();
      
      let time = ctx.currentTime;
      raga.notes.forEach((freq, index) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(freq, time);
        
        gain.gain.setValueAtTime(0.12, time);
        // Exponential decay
        gain.gain.exponentialRampToValueAtTime(0.001, time + 0.35);
        
        osc.connect(gain);
        gain.connect(ctx.destination);
        
        osc.start(time);
        osc.stop(time + 0.4);
        
        time += 0.4;
      });

      // Clear active play state
      setTimeout(() => {
        setPlayingRaga(null);
        ctx.close();
      }, raga.notes.length * 400);

    } catch (e) {
      console.error(e);
      setPlayingRaga(null);
    }
  };

  return (
    <div className="animate-fade-in" style={{ padding: '40px 48px', height: '100%', overflowY: 'auto', display: 'flex', flexDirection: 'column', position: 'relative' }}>
      
      {/* Background Motif */}
      <div style={{ position: 'fixed', bottom: -50, right: -50, fontSize: 300, opacity: 0.015, color: 'var(--peacock)', pointerEvents: 'none', zIndex: 0 }}>
        🎵
      </div>

      <div style={{ marginBottom: 40, position: 'relative', zIndex: 1 }}>
        <h1 style={{ fontSize: '2.8rem', fontWeight: 700, fontFamily: 'var(--font-serif)', color: 'var(--peacock)', marginBottom: 12 }}>
          Raga Explorer
        </h1>
        <p className="cultural-text" style={{ color: 'var(--text-secondary)', fontSize: '1.15rem', fontStyle: 'italic', fontFamily: 'var(--font-serif)' }}>
          Browse Melakartas and Janyas, explore scales, and play notes with interactive audio synthesis.
        </p>
      </div>

      {/* Search Box */}
      <div style={{ position: 'relative', maxWidth: 480, marginBottom: 40, zIndex: 1 }}>
        <Search size={18} style={{ position: 'absolute', left: 16, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
        <input 
          type="text" 
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Search ragas, classifications..."
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

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: 24, position: 'relative', zIndex: 1 }}>
        {filteredRagas.map((raga, i) => (
          <div key={i} className="elevated-card" style={{
            display: 'flex', flexDirection: 'column', gap: 16,
            background: '#FFFFFF', border: '1px solid var(--border)', borderRadius: '20px',
            padding: '24px', transition: 'all var(--transition)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{
                fontSize: 11, padding: '4px 12px', borderRadius: 'var(--radius-full)',
                background: 'rgba(139, 74, 54, 0.08)', color: 'var(--peacock)',
                textTransform: 'uppercase', letterSpacing: '1px', fontWeight: 600
              }}>
                {raga.melakarta}
              </span>
              <button 
                onClick={() => playScale(raga)}
                disabled={playingRaga !== null}
                style={{
                  width: 36, height: 36, borderRadius: '50%',
                  background: playingRaga === raga.name ? 'var(--peacock)' : 'rgba(139, 74, 54, 0.08)',
                  color: playingRaga === raga.name ? '#FFFFFF' : 'var(--peacock)',
                  display: 'flex', alignItems: 'center', justifySelf: 'center', justifyContent: 'center',
                  cursor: playingRaga === raga.name ? 'default' : 'pointer'
                }}
              >
                <Play size={16} fill="currentColor" style={{ marginLeft: 2 }} />
              </button>
            </div>

            <div>
              <h3 style={{ fontSize: 20, fontWeight: 700, fontFamily: 'var(--font-serif)', color: 'var(--peacock)', marginBottom: 12 }}>
                {raga.name}
              </h3>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 16 }}>
                <div>
                  <span style={{ fontSize: 11, textTransform: 'uppercase', color: 'var(--text-muted)', display: 'block', fontWeight: 600 }}>Arohana (Ascending)</span>
                  <span style={{ fontSize: 14, fontWeight: 600, fontFamily: 'var(--font-serif)', color: 'var(--text-primary)' }}>{raga.arohana}</span>
                </div>
                <div>
                  <span style={{ fontSize: 11, textTransform: 'uppercase', color: 'var(--text-muted)', display: 'block', fontWeight: 600 }}>Avarohana (Descending)</span>
                  <span style={{ fontSize: 14, fontWeight: 600, fontFamily: 'var(--font-serif)', color: 'var(--text-primary)' }}>{raga.avarohana}</span>
                </div>
              </div>

              <p style={{ fontSize: 13.5, color: 'var(--text-secondary)', borderTop: '1px solid var(--border)', paddingTop: 16 }}>
                <strong>Aesthetic:</strong> {raga.mood}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
