import React, { useState, useRef, useEffect } from 'react'
import { Play, Pause, Volume2, VolumeX, Gauge, Info } from 'lucide-react'

export default function TTSPlayer({ text, audioId, activeAudioId, setActiveAudioId }) {
  const [playing, setPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [volume, setVolume] = useState(1.0)
  const [isMuted, setIsMuted] = useState(false)
  const [playbackRate, setPlaybackRate] = useState(1.0)
  const [error, setError] = useState(null)
  
  const audioRef = useRef(null)
  const progressRef = useRef(null)
  
  const audioUrl = `/api/tts?text=${encodeURIComponent(text)}`

  // Synchronize playback state with global active audio coordinator
  useEffect(() => {
    if (activeAudioId !== audioId && playing) {
      pauseAudio()
    }
  }, [activeAudioId, audioId])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause()
      }
    }
  }, [])

  // Audio Event Listeners
  useEffect(() => {
    const el = audioRef.current
    if (!el) return

    const handlePlay = () => {
      setPlaying(true)
      setActiveAudioId(audioId)
    }
    const handlePause = () => setPlaying(false)
    const handleEnded = () => {
      setPlaying(false)
      setCurrentTime(0)
    }
    const handleTimeUpdate = () => {
      setCurrentTime(el.currentTime)
    }
    const handleLoadedMetadata = () => {
      setDuration(el.duration || 0)
    }
    const handleError = (e) => {
      console.error('TTS playback error', e)
      setError('Unable to load synthesized voice response.')
      setPlaying(false)
    }

    el.addEventListener('play', handlePlay)
    el.addEventListener('pause', handlePause)
    el.addEventListener('ended', handleEnded)
    el.addEventListener('timeupdate', handleTimeUpdate)
    el.addEventListener('loadedmetadata', handleLoadedMetadata)
    el.addEventListener('error', handleError)

    // Apply initial settings
    el.volume = volume
    el.muted = isMuted
    el.playbackRate = playbackRate

    return () => {
      el.removeEventListener('play', handlePlay)
      el.removeEventListener('pause', handlePause)
      el.removeEventListener('ended', handleEnded)
      el.removeEventListener('timeupdate', handleTimeUpdate)
      el.removeEventListener('loadedmetadata', handleLoadedMetadata)
      el.removeEventListener('error', handleError)
    }
  }, [volume, isMuted, playbackRate])

  const playAudio = () => {
    if (!audioRef.current) return
    setError(null)
    audioRef.current.play().catch(e => {
      console.error('Play failed:', e)
      setError('Playback request was blocked or failed.')
    })
  }

  const pauseAudio = () => {
    if (!audioRef.current) return
    audioRef.current.pause()
  }

  const togglePlay = () => {
    if (playing) {
      pauseAudio()
    } else {
      playAudio()
    }
  }

  // Handle timeline seek
  const handleSeek = (e) => {
    const time = parseFloat(e.target.value)
    setCurrentTime(time)
    if (audioRef.current) {
      audioRef.current.currentTime = time
    }
  }

  // Handle volume adjust
  const handleVolumeChange = (e) => {
    const vol = parseFloat(e.target.value)
    setVolume(vol)
    setIsMuted(vol === 0)
    if (audioRef.current) {
      audioRef.current.volume = vol
      audioRef.current.muted = vol === 0
    }
  }

  const toggleMute = () => {
    const nextMute = !isMuted
    setIsMuted(nextMute)
    if (audioRef.current) {
      audioRef.current.muted = nextMute
    }
  }

  // Handle speed change
  const handleSpeedChange = (e) => {
    const speed = parseFloat(e.target.value)
    setPlaybackRate(speed)
    if (audioRef.current) {
      audioRef.current.playbackRate = speed
    }
  }

  const formatTime = (time) => {
    if (!time || isNaN(time)) return '0:00'
    const mins = Math.floor(time / 60)
    const secs = Math.floor(time % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  // Handle Keyboard accessibility (Space to play/pause when focused)
  const handleKeyDown = (e) => {
    if (e.key === ' ' || e.key === 'Spacebar') {
      e.preventDefault()
      togglePlay()
    }
  }

  return (
    <div 
      className="elevated-card animate-fade-in" 
      style={{ 
        padding: '16px 20px', 
        background: 'var(--bg-surface-hover)', 
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--border)',
        marginTop: 16
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        
        {/* Header Indicator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, fontWeight: 700, color: 'var(--peacock)', fontFamily: 'var(--font-sans)' }}>
          <span style={{ position: 'relative', display: 'flex', h: 8, w: 8 }}>
            <span className="typing-dot" style={{ margin: 0, background: 'var(--peacock)', width: 8, height: 8 }} />
          </span>
          Voice Assistant Audio Synthesizer
        </div>

        {/* Custom Audio Controls Row */}
        <div 
          style={{ 
            display: 'flex', 
            alignItems: 'center', 
            flexWrap: 'wrap',
            gap: 16, 
            background: 'var(--bg-surface)', 
            padding: '12px 16px', 
            borderRadius: 'var(--radius-md)', 
            border: '1px solid var(--border)' 
          }}
        >
          {/* Play/Pause Button */}
          <button 
            onClick={togglePlay} 
            onKeyDown={handleKeyDown}
            aria-label={playing ? "Pause voice response" : "Play voice response"}
            className="btn-primary"
            style={{ 
              width: 44, 
              height: 44, 
              borderRadius: '50%', 
              padding: 0, 
              flexShrink: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer'
            }}
          >
            {playing ? <Pause size={20} fill="currentColor" /> : <Play size={20} fill="currentColor" style={{ marginLeft: 3 }} />}
          </button>

          {/* Timeline / Progress Bar */}
          <div style={{ flex: 1, minWidth: 150, display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{ fontSize: 12.5, fontWeight: 700, color: 'var(--text-muted)', minWidth: 32, fontFamily: 'var(--font-sans)' }}>
              {formatTime(currentTime)}
            </span>
            
            <input 
              ref={progressRef}
              type="range"
              min={0}
              max={duration || 100}
              value={currentTime}
              onChange={handleSeek}
              aria-label="Audio timeline progress"
              style={{
                flex: 1,
                cursor: 'pointer',
                accentColor: 'var(--peacock)',
                height: 5,
                borderRadius: 3,
                outline: 'none'
              }}
            />

            <span style={{ fontSize: 12.5, fontWeight: 700, color: 'var(--text-muted)', minWidth: 32, fontFamily: 'var(--font-sans)' }}>
              {formatTime(duration)}
            </span>
          </div>

          {/* Volume Control */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 100 }}>
            <button 
              onClick={toggleMute}
              aria-label={isMuted ? "Unmute voice response" : "Mute voice response"}
              style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', padding: 4, display: 'flex', alignItems: 'center' }}
            >
              {isMuted || volume === 0 ? <VolumeX size={18} /> : <Volume2 size={18} />}
            </button>
            <input 
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={isMuted ? 0 : volume}
              onChange={handleVolumeChange}
              aria-label="Volume slider"
              style={{
                width: 60,
                cursor: 'pointer',
                accentColor: 'var(--peacock)',
                height: 4,
                outline: 'none'
              }}
            />
          </div>

          {/* Playback Speed Controller */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Gauge size={16} style={{ color: 'var(--text-muted)' }} />
            <select
              value={playbackRate}
              onChange={handleSpeedChange}
              aria-label="Playback speed"
              style={{
                background: 'var(--bg-surface-hover)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-sm)',
                padding: '4px 8px',
                fontSize: 12.5,
                fontWeight: 700,
                color: 'var(--text-primary)',
                outline: 'none',
                cursor: 'pointer',
                fontFamily: 'var(--font-sans)'
              }}
            >
              <option value="0.75">0.75x</option>
              <option value="1.0">1.0x</option>
              <option value="1.25">1.25x</option>
              <option value="1.5">1.5x</option>
              <option value="1.75">1.75x</option>
              <option value="2.0">2.0x</option>
            </select>
          </div>

        </div>

        {/* Error Dialog */}
        {error && (
          <div style={{ fontSize: 13, color: '#EF4444', display: 'flex', alignItems: 'center', gap: 6, fontWeight: 600, fontFamily: 'var(--font-sans)' }}>
            <Info size={14} /> {error}
          </div>
        )}

        {/* Hidden Native Audio Element */}
        <audio 
          ref={audioRef}
          src={audioUrl}
          preload="none"
          style={{ display: 'none' }}
        />

      </div>
    </div>
  )
}
