import React, { useState, useRef, useEffect } from 'react'
import { Play, Pause, Volume2, Info } from 'lucide-react'

export default function RagaAudioPlayer({ audio }) {
  const [playing, setPlaying] = useState(false)
  const [error, setError] = useState(null)
  const [duration, setDuration] = useState(0)
  const [currentTime, setCurrentTime] = useState(0)
  
  const audioRef = useRef(null)

  useEffect(() => {
    const el = audioRef.current
    if (!el) return

    const handlePlay = () => setPlaying(true)
    const handlePause = () => setPlaying(false)
    const handleEnded = () => setPlaying(false)
    const handleError = (e) => {
      console.error('Audio playback error', e)
      setError('Unable to play audio')
      setPlaying(false)
    }
    const handleTimeUpdate = () => setCurrentTime(el.currentTime)
    const handleLoadedMetadata = () => setDuration(el.duration)

    el.addEventListener('play', handlePlay)
    el.addEventListener('pause', handlePause)
    el.addEventListener('ended', handleEnded)
    el.addEventListener('error', handleError)
    el.addEventListener('timeupdate', handleTimeUpdate)
    el.addEventListener('loadedmetadata', handleLoadedMetadata)

    return () => {
      el.removeEventListener('play', handlePlay)
      el.removeEventListener('pause', handlePause)
      el.removeEventListener('ended', handleEnded)
      el.removeEventListener('error', handleError)
      el.removeEventListener('timeupdate', handleTimeUpdate)
      el.removeEventListener('loadedmetadata', handleLoadedMetadata)
    }
  }, [])

  const toggle = () => {
    if (!audioRef.current) return
    if (playing) {
      audioRef.current.pause()
    } else {
      audioRef.current.play().catch(e => {
        console.error('Play failed:', e)
        setError('Playback failed')
      })
    }
  }

  const formatTime = (time) => {
    if (!time || isNaN(time)) return '0:00'
    const mins = Math.floor(time / 60)
    const secs = Math.floor(time % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  if (!audio || !audio.url) return null

  return (
    <div className="elevated-card" style={{ padding: '20px', background: 'var(--bg-surface-hover)' }}>
      
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
           <div style={{ width: 40, height: 40, borderRadius: 'var(--radius-full)', background: 'var(--saffron)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
             <Volume2 size={20} />
           </div>
           <div>
             <h4 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', fontFamily: 'var(--font-sans)', marginBottom: 2 }}>
               {audio.title || 'Synthesized Audio'}
             </h4>
             <p style={{ fontSize: 13, color: 'var(--text-secondary)', fontWeight: 600 }}>
               {audio.composer || 'CarnaticGPT Synthesis'}
             </p>
           </div>
        </div>
        {audio.raga && (
          <span style={{ fontSize: 12, padding: '4px 10px', background: 'rgba(2, 132, 199, 0.1)', color: 'var(--peacock)', borderRadius: 'var(--radius-full)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            {audio.raga}
          </span>
        )}
      </div>

      {/* Visualizer & Controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, background: 'var(--bg-surface)', padding: '16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)' }}>
        <button 
          onClick={toggle} 
          className="btn-primary"
          style={{ width: 48, height: 48, borderRadius: '50%', padding: 0, flexShrink: 0 }}
        >
          {playing ? <Pause size={24} fill="currentColor" /> : <Play size={24} fill="currentColor" style={{ marginLeft: 4 }} />}
        </button>

        {/* Custom CSS Waveform */}
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 8 }}>
          <div className="audio-wave-container" style={{ flex: 1, justifyContent: 'space-between', opacity: playing ? 1 : 0.3, transition: 'opacity var(--transition-fast)' }}>
             {[...Array(24)].map((_, i) => (
               <div key={i} className="audio-wave-bar" style={{ animationDelay: `${i * 0.1}s`, animationPlayState: playing ? 'running' : 'paused' }} />
             ))}
          </div>
          
          <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-muted)', fontFamily: 'var(--font-sans)', minWidth: 40, textAlign: 'right' }}>
             {formatTime(currentTime)}
          </div>
        </div>
      </div>

      {error && (
        <div style={{ marginTop: 12, fontSize: 13, color: '#EF4444', display: 'flex', alignItems: 'center', gap: 6, fontWeight: 600 }}>
          <Info size={14} /> {error}
        </div>
      )}

      {audio.description && (
        <div style={{ marginTop: 16, fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.6, padding: '12px 16px', background: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)', borderLeft: '3px solid var(--saffron)' }}>
          {audio.description}
        </div>
      )}

      <audio
        ref={audioRef}
        src={`http://localhost:8000${audio.url}`}
        style={{ display: 'none' }}
      />
    </div>
  )
}
