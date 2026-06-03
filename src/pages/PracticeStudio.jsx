import React, { useState, useEffect, useRef } from 'react';
import { Play, Square, Music, Compass, Volume2, Activity } from 'lucide-react';

export default function PracticeStudio() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [pitch, setPitch] = useState(130.81); // C3
  const [pitchName, setPitchName] = useState('Sa (C / 1-Kattai)');
  const [tempo, setTempo] = useState(80);
  const [activeExercise, setActiveExercise] = useState(0);
  const audioContextRef = useRef(null);
  const oscillatorsRef = useRef([]);

  const EXERCISES = [
    { title: 'Sarali Varisai 1', scale: 'Sa Ri Ga Ma | Pa Da Ni Sa | Sa Ni Da Pa | Ma Ga Ri Sa', description: 'Simple ascending and descending sequence in Mayamalavagowla.' },
    { title: 'Sarali Varisai 2', scale: 'Sa Ri Sa Ri | Sa Ri Ga Ma | Pa Da Pa Da | Pa Da Ni Sa', description: 'Focus on repetition of the initial swara intervals.' },
    { title: 'Janta Varisai 1', scale: 'SS RR GG MM | PP DD NN SS | SS NN DD PP | MM GG RR SS', description: 'Double swaras (Janta) emphasizing microtonal accentuation.' },
    { title: 'Dhattu Varisai 1', scale: 'Sa Ga Ri Sa | Ri Ma Ga Ri | Ga Pa Ma Ga | Ma Da Pa Ma', description: 'Interlocking zigzag intervals to master finger/vocal agility.' },
  ];

  const PITCH_OPTIONS = [
    { name: '1 Kattai (C / C3)', freq: 130.81 },
    { name: '2 Kattai (D / D3)', freq: 146.83 },
    { name: '3 Kattai (E / E3)', freq: 164.81 },
    { name: '4 Kattai (F / F3)', freq: 174.61 },
    { name: '5 Kattai (G / G3)', freq: 196.00 },
  ];

  const startDrone = () => {
    try {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      const ctx = new AudioContext();
      audioContextRef.current = ctx;

      // Create primary node (Sa)
      const osc1 = ctx.createOscillator();
      const gain1 = ctx.createGain();
      osc1.frequency.setValueAtTime(pitch, ctx.currentTime);
      osc1.type = 'triangle';
      gain1.gain.setValueAtTime(0.12, ctx.currentTime);
      osc1.connect(gain1);
      gain1.connect(ctx.destination);

      // Create perfect fifth node (Pa)
      const osc2 = ctx.createOscillator();
      const gain2 = ctx.createGain();
      osc2.frequency.setValueAtTime(pitch * 1.5, ctx.currentTime); // Perfect fifth (Pa)
      osc2.type = 'sine';
      gain2.gain.setValueAtTime(0.08, ctx.currentTime);
      osc2.connect(gain2);
      gain2.connect(ctx.destination);

      // Create octave node (Higher Sa)
      const osc3 = ctx.createOscillator();
      const gain3 = ctx.createGain();
      osc3.frequency.setValueAtTime(pitch * 2, ctx.currentTime); // Octave
      osc3.type = 'sine';
      gain3.gain.setValueAtTime(0.04, ctx.currentTime);
      osc3.connect(gain3);
      gain3.connect(ctx.destination);

      osc1.start();
      osc2.start();
      osc3.start();

      oscillatorsRef.current = [
        { osc: osc1, gain: gain1 },
        { osc: osc2, gain: gain2 },
        { osc: osc3, gain: gain3 }
      ];
      setIsPlaying(true);
    } catch (e) {
      console.error("Web Audio API failed", e);
    }
  };

  const stopDrone = () => {
    oscillatorsRef.current.forEach(({ osc }) => {
      try {
        osc.stop();
      } catch (e) {}
    });
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => {});
    }
    oscillatorsRef.current = [];
    setIsPlaying(false);
  };

  useEffect(() => {
    if (isPlaying) {
      stopDrone();
      startDrone();
    }
  }, [pitch]);

  useEffect(() => {
    return () => {
      if (isPlaying) {
        stopDrone();
      }
    };
  }, [isPlaying]);

  return (
    <div className="animate-fade-in" style={{ padding: '40px 48px', height: '100%', overflowY: 'auto', display: 'flex', flexDirection: 'column', position: 'relative' }}>
      
      {/* Background Motif */}
      <div style={{ position: 'fixed', bottom: -50, right: -50, fontSize: 300, opacity: 0.015, color: 'var(--peacock)', pointerEvents: 'none', zIndex: 0 }}>
        🪕
      </div>

      <div style={{ marginBottom: 48, position: 'relative', zIndex: 1 }}>
        <h1 style={{ fontSize: '2.8rem', fontWeight: 700, fontFamily: 'var(--font-serif)', color: 'var(--peacock)', marginBottom: 12 }}>
          Practice Studio
        </h1>
        <p className="cultural-text" style={{ color: 'var(--text-secondary)', fontSize: '1.15rem', fontStyle: 'italic', fontFamily: 'var(--font-serif)' }}>
          Hone your swaras with an integrated tanpura drone and classical exercise guides.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '32px', position: 'relative', zIndex: 1 }}>
        
        {/* Tanpura Drone Box */}
        <div className="elevated-card" style={{ background: '#FFFFFF', border: '1px solid var(--border)', borderRadius: '20px', padding: '32px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '28px' }}>
            <Volume2 size={24} color="var(--peacock)" />
            <h3 style={{ fontSize: '1.4rem', fontWeight: 700, fontFamily: 'var(--font-serif)', color: 'var(--text-primary)' }}>Interactive Tanpura Drone</h3>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '24px', padding: '16px 0' }}>
            <div style={{
              width: 120, height: 120, borderRadius: '50%',
              background: isPlaying ? 'rgba(139, 74, 54, 0.08)' : 'var(--bg-app)',
              border: isPlaying ? '2px solid var(--peacock)' : '1px solid var(--border)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              cursor: 'pointer', transition: 'all 0.3s ease',
              boxShadow: isPlaying ? '0 0 24px rgba(139, 74, 54, 0.15)' : 'none'
            }}
              onClick={isPlaying ? stopDrone : startDrone}
            >
              {isPlaying ? (
                <Square size={36} color="var(--peacock)" fill="var(--peacock)" />
              ) : (
                <Play size={36} style={{ marginLeft: 6 }} color="var(--peacock)" fill="var(--peacock)" />
              )}
            </div>

            <div style={{ textAlign: 'center' }}>
              <p style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>
                {isPlaying ? 'Drone Active' : 'Drone Inactive'}
              </p>
              <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                {isPlaying ? 'Synthesizing Sa - Pa - Sa' : 'Click the dial to trigger drone'}
              </p>
            </div>

            {/* Pitch Tuning Selector */}
            <div style={{ width: '100%', marginTop: '12px' }}>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--text-muted)', marginBottom: '8px' }}>
                Pitch Tuner (Kattai)
              </label>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {PITCH_OPTIONS.map((opt) => (
                  <button
                    key={opt.freq}
                    onClick={() => { setPitch(opt.freq); setPitchName(opt.name); }}
                    style={{
                      width: '100%', padding: '12px 16px', borderRadius: '12px',
                      border: '1px solid var(--border)',
                      background: pitch === opt.freq ? 'rgba(139, 74, 54, 0.08)' : '#FFFFFF',
                      color: pitch === opt.freq ? 'var(--peacock)' : 'var(--text-primary)',
                      fontSize: '14px', fontWeight: pitch === opt.freq ? 600 : 500,
                      textAlign: 'left', cursor: 'pointer', transition: 'all 0.2s'
                    }}
                  >
                    {opt.name} {pitch === opt.freq && '✓'}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Swara Vocal Gym */}
        <div className="elevated-card" style={{ background: '#FFFFFF', border: '1px solid var(--border)', borderRadius: '20px', padding: '32px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '28px' }}>
            <Activity size={24} color="var(--peacock)" />
            <h3 style={{ fontSize: '1.4rem', fontWeight: 700, fontFamily: 'var(--font-serif)', color: 'var(--text-primary)' }}>Vocal Exercises</h3>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {EXERCISES.map((ex, i) => (
              <div
                key={i}
                onClick={() => setActiveExercise(i)}
                style={{
                  padding: '16px', borderRadius: '16px',
                  border: i === activeExercise ? '1.5px solid var(--peacock)' : '1px solid var(--border)',
                  background: i === activeExercise ? 'rgba(139, 74, 54, 0.02)' : '#FFFFFF',
                  cursor: 'pointer', transition: 'all 0.2s'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <span style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)' }}>{ex.title}</span>
                  {i === activeExercise && <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--peacock)' }} />}
                </div>
                <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 12 }}>{ex.description}</p>
                <div style={{
                  background: 'var(--bg-app)', padding: '10px 14px', borderRadius: '8px',
                  fontFamily: 'var(--font-serif)', fontStyle: 'italic', fontSize: 13.5, color: 'var(--peacock)',
                  letterSpacing: '0.5px'
                }}>
                  {ex.scale}
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}
