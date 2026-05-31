import React, { useState, useRef, useEffect } from 'react'
import { Play, Pause, Volume2, VolumeX, Music, ChevronDown, ChevronUp, Sparkles } from 'lucide-react'

// Carnatic Swaras frequency mappings for synth fallback
const SWARA_FREQS = {
  "S": 261.63, "R1": 277.18, "R2": 293.66, "G2": 311.13, "G3": 329.63,
  "M1": 349.23, "M2": 369.99, "P": 392.00, "D1": 415.30, "D2": 440.00,
  "N2": 466.16, "N3": 493.88, "S*": 523.25
}

// Basic scale definitions for synth fallback when mp3 files are unavailable
const RAGA_SYNTH_SCALES = {
  alapana: { arohana: true, avarohana: true, noteDuration: 0.7 },
  arohana: { arohana: true, avarohana: false, noteDuration: 0.5 },
  avarohana: { arohana: false, avarohana: true, noteDuration: 0.5 },
}

// Default scales for common ragas (used when synth fallback triggers)
const RAGA_SCALES = {
  Bhairavi: { arohana: ["S","R2","G2","M1","P","D2","N2","S*"], avarohana: ["S*","N2","D1","P","M1","G2","R2","S"] },
  Kalyani: { arohana: ["S","R2","G3","M2","P","D2","N3","S*"], avarohana: ["S*","N3","D2","P","M2","G3","R2","S"] },
  Mohanam: { arohana: ["S","R2","G3","P","D2","S*"], avarohana: ["S*","D2","P","G3","R2","S"] },
  Mayamalavagowla: { arohana: ["S","R1","G3","M1","P","D1","N3","S*"], avarohana: ["S*","N3","D1","P","M1","G3","R1","S"] },
  Hindolam: { arohana: ["S","G2","M1","D1","N2","S*"], avarohana: ["S*","N2","D1","M1","G2","S"] },
  Todi: { arohana: ["S","R1","G2","M1","P","D1","N2","S*"], avarohana: ["S*","N2","D1","P","M1","G2","R1","S"] },
  Sankarabharanam: { arohana: ["S","R2","G3","M1","P","D2","N3","S*"], avarohana: ["S*","N3","D2","P","M1","G3","R2","S"] },
  Hamsadhwani: { arohana: ["S","R2","G3","P","N3","S*"], avarohana: ["S*","N3","P","G3","R2","S"] },
  Kharaharapriya: { arohana: ["S","R2","G2","M1","P","D2","N2","S*"], avarohana: ["S*","N2","D2","P","M1","G2","R2","S"] },
}

// Fallback scale for unknown ragas
const DEFAULT_SCALE = { arohana: ["S","R2","G3","M1","P","D2","N3","S*"], avarohana: ["S*","N3","D2","P","M1","G3","R2","S"] }

const AUDIO_LABELS = {
  alapana: 'Alapana',
  arohana: 'Arohana',
  avarohana: 'Avarohana',
  composition: 'Composition',
  sample: 'Sample',
}

const AudioTrack = ({ label, url, ragaName, isActive, onActivate }) => {
  const audioRef = useRef(null)
  const audioCtxRef = useRef(null)
  const synthTimeoutsRef = useRef([])
  const [playing, setPlaying] = useState(false)
  const [progress, setProgress] = useState(0)
  const [duration, setDuration] = useState(0)
  const [muted, setMuted] = useState(false)
  const [error, setError] = useState(false)
  const [synthMode, setSynthMode] = useState(false)
  const [currentSwara, setCurrentSwara] = useState('')

  // Stop when another track becomes active
  useEffect(() => {
    if (!isActive && playing) {
      stopAll()
    }
  }, [isActive])

  // Cleanup on unmount
  useEffect(() => {
    return () => stopAll()
  }, [])

  const stopAll = () => {
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current.currentTime = 0
    }
    synthTimeoutsRef.current.forEach(t => clearTimeout(t))
    synthTimeoutsRef.current = []
    if (audioCtxRef.current && audioCtxRef.current.state !== 'closed') {
      audioCtxRef.current.close()
    }
    audioCtxRef.current = null
    setPlaying(false)
    setSynthMode(false)
    setCurrentSwara('')
    setProgress(0)
  }

  const playSynthFallback = () => {
    setSynthMode(true)
    setError(false)

    const AudioContextClass = window.AudioContext || window.webkitAudioContext
    if (!AudioContextClass) return

    const audioCtx = new AudioContextClass()
    audioCtxRef.current = audioCtx

    // Get the scale for this raga
    const normalizedName = ragaName?.trim()
    const scale = RAGA_SCALES[normalizedName] || DEFAULT_SCALE

    // Build sequence based on track type
    let sequence = []
    const trackType = label.toLowerCase()
    if (trackType === 'arohana') {
      sequence = scale.arohana
    } else if (trackType === 'avarohana') {
      sequence = scale.avarohana
    } else {
      // alapana/composition: ascending then descending
      sequence = [...scale.arohana, ...scale.avarohana.slice(1)]
    }

    const noteDuration = trackType === 'alapana' ? 0.7 : 0.5
    const startTime = audioCtx.currentTime
    const totalDuration = sequence.length * noteDuration

    sequence.forEach((swara, idx) => {
      const freq = SWARA_FREQS[swara] || 261.63
      const noteStartTime = startTime + idx * noteDuration

      const osc = audioCtx.createOscillator()
      const gainNode = audioCtx.createGain()
      osc.type = "triangle"

      // Add gamaka slide for alapana
      if (trackType === 'alapana' && idx > 0) {
        const prevFreq = SWARA_FREQS[sequence[idx - 1]] || 261.63
        osc.frequency.setValueAtTime(prevFreq, noteStartTime)
        osc.frequency.exponentialRampToValueAtTime(freq, noteStartTime + 0.2)
      } else {
        osc.frequency.setValueAtTime(freq, noteStartTime)
      }

      gainNode.gain.setValueAtTime(0, noteStartTime)
      gainNode.gain.linearRampToValueAtTime(0.15, noteStartTime + 0.05)
      gainNode.gain.linearRampToValueAtTime(0.1, noteStartTime + noteDuration - 0.1)
      gainNode.gain.exponentialRampToValueAtTime(0.001, noteStartTime + noteDuration)

      osc.connect(gainNode)
      gainNode.connect(audioCtx.destination)
      osc.start(noteStartTime)
      osc.stop(noteStartTime + noteDuration)

      // Schedule visual updates
      const t = setTimeout(() => {
        setCurrentSwara(swara)
        setProgress(((idx + 1) / sequence.length) * 100)
      }, idx * noteDuration * 1000)
      synthTimeoutsRef.current.push(t)
    })

    // Auto-stop at end
    const endT = setTimeout(() => {
      stopAll()
    }, totalDuration * 1000 + 200)
    synthTimeoutsRef.current.push(endT)

    setDuration(totalDuration)
  }

  const togglePlay = () => {
    onActivate()
    if (playing) {
      stopAll()
      return
    }

    setPlaying(true)

    const audio = audioRef.current
    if (!audio) {
      playSynthFallback()
      return
    }

    // Try loading the audio file first
    audio.play()
      .then(() => {
        setSynthMode(false)
        setError(false)
      })
      .catch(() => {
        // MP3 file failed (404 or 0-byte) — use WebAudio synth fallback
        console.warn(`Audio file failed for ${label}, using synth fallback`)
        playSynthFallback()
      })
  }

  const handleTimeUpdate = () => {
    const audio = audioRef.current
    if (!audio || !audio.duration) return
    setProgress((audio.currentTime / audio.duration) * 100)
  }

  const handleSeek = (e) => {
    if (synthMode) return // Can't seek synth playback
    const audio = audioRef.current
    if (!audio || !audio.duration) return
    const rect = e.currentTarget.getBoundingClientRect()
    const pct = (e.clientX - rect.left) / rect.width
    audio.currentTime = pct * audio.duration
    setProgress(pct * 100)
  }

  const formatTime = (s) => {
    if (!s || isNaN(s)) return '0:00'
    const m = Math.floor(s / 60)
    const sec = Math.floor(s % 60)
    return `${m}:${sec.toString().padStart(2, '0')}`
  }

  return (
    <div style={{
      padding: '12px 14px',
      borderRadius: 10,
      background: isActive
        ? 'linear-gradient(135deg, rgba(88, 30, 168, 0.25) 0%, rgba(22, 219, 204, 0.15) 100%)'
        : 'rgba(28, 36, 58, 0.6)',
      border: `1px solid ${isActive ? 'rgba(22, 219, 204, 0.3)' : 'rgba(255, 255, 255, 0.06)'}`,
      transition: 'all 0.2s ease',
      backdropFilter: 'blur(8px)',
    }}>
      <audio
        ref={audioRef}
        src={url}
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={e => setDuration(e.target.duration)}
        onEnded={() => stopAll()}
        onError={() => setError(true)}
        muted={muted}
        preload="metadata"
      />

      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        {/* Play button */}
        <button
          onClick={togglePlay}
          style={{
            width: 34, height: 34, borderRadius: '50%', flexShrink: 0,
            background: playing
              ? 'linear-gradient(135deg, hsl(174, 82%, 47%), hsl(263, 70%, 50%))'
              : 'rgba(255, 255, 255, 0.08)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            transition: 'all 0.2s ease',
            cursor: 'pointer',
            border: playing ? 'none' : '1px solid rgba(255, 255, 255, 0.1)',
            boxShadow: playing ? '0 0 12px rgba(22, 219, 204, 0.3)' : 'none',
          }}
        >
          {playing
            ? <Pause size={14} color="white" fill="white" />
            : <Play size={14} color="white" fill="white" style={{ marginLeft: 2 }} />
          }
        </button>

        {/* Label + progress */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5, alignItems: 'center' }}>
            <span style={{ fontSize: 12.5, fontWeight: 600, color: isActive ? 'hsl(174, 82%, 60%)' : 'rgba(255, 255, 255, 0.85)' }}>
              {AUDIO_LABELS[label] || label}
            </span>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              {synthMode && playing && (
                <span style={{
                  fontSize: 10,
                  fontWeight: 700,
                  color: 'hsl(42, 78%, 60%)',
                  background: 'rgba(219, 166, 22, 0.12)',
                  border: '1px solid rgba(219, 166, 22, 0.2)',
                  borderRadius: 4,
                  padding: '1px 5px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 3,
                }}>
                  <Sparkles size={9} /> Synth
                </span>
              )}
              {synthMode && currentSwara && (
                <span style={{
                  fontSize: 11,
                  fontWeight: 800,
                  color: 'hsl(174, 82%, 60%)',
                  fontFamily: 'monospace',
                }}>
                  {currentSwara.replace('*', '')}
                </span>
              )}
              {!synthMode && duration > 0 && (
                <span style={{ fontSize: 11, color: 'rgba(255, 255, 255, 0.4)', fontFamily: 'monospace' }}>
                  {formatTime(audioRef.current?.currentTime)} / {formatTime(duration)}
                </span>
              )}
            </div>
          </div>
          {/* Progress bar */}
          <div
            onClick={handleSeek}
            style={{
              height: 3, background: 'rgba(255, 255, 255, 0.06)',
              borderRadius: 2, cursor: synthMode ? 'default' : 'pointer', position: 'relative',
            }}
          >
            <div style={{
              height: '100%', width: `${progress}%`,
              background: 'linear-gradient(90deg, hsl(174, 82%, 47%), hsl(263, 70%, 50%))',
              borderRadius: 2,
              transition: playing && !synthMode ? 'none' : 'width 0.15s ease',
              boxShadow: progress > 0 ? '0 0 6px rgba(22, 219, 204, 0.4)' : 'none',
            }} />
          </div>
        </div>

        {/* Mute */}
        <button
          onClick={() => setMuted(m => !m)}
          style={{
            color: muted ? 'rgba(255, 255, 255, 0.2)' : 'rgba(255, 255, 255, 0.4)',
            flexShrink: 0,
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            transition: 'color 0.2s',
          }}
        >
          {muted ? <VolumeX size={14} /> : <Volume2 size={14} />}
        </button>
      </div>
    </div>
  )
}


const RagaAudioPlayer = ({ audioData }) => {
  const [expanded, setExpanded] = useState(true)
  const [activeTrack, setActiveTrack] = useState(null)

  if (!audioData || !audioData.found || !audioData.audio) return null

  const tracks = Object.entries(audioData.audio)
  if (tracks.length === 0) return null

  return (
    <div style={{
      marginTop: 12,
      borderRadius: 12,
      border: '1px solid rgba(22, 219, 204, 0.2)',
      background: 'rgba(28, 36, 58, 0.5)',
      backdropFilter: 'blur(12px)',
      overflow: 'hidden',
      boxShadow: '0 4px 20px rgba(0, 0, 0, 0.2)',
    }}>
      {/* Header */}
      <button
        onClick={() => setExpanded(e => !e)}
        style={{
          width: '100%', padding: '12px 14px',
          display: 'flex', alignItems: 'center', gap: 8,
          background: 'none', cursor: 'pointer', border: 'none',
        }}
      >
        <div style={{
          width: 28, height: 28, borderRadius: 7,
          background: 'linear-gradient(135deg, hsl(174, 82%, 47%), hsl(263, 70%, 50%))',
          display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
          boxShadow: '0 0 10px rgba(22, 219, 204, 0.25)',
        }}>
          <Music size={13} color="white" />
        </div>
        <div style={{ flex: 1, textAlign: 'left' }}>
          <p style={{
            fontSize: 13, fontWeight: 700, color: '#fff',
            letterSpacing: '0.02em', margin: 0,
          }}>
            🎵 {audioData.raga} — Audio
          </p>
          <p style={{ fontSize: 11, color: 'rgba(255, 255, 255, 0.4)', margin: 0 }}>
            {tracks.length} recording{tracks.length !== 1 ? 's' : ''} available
          </p>
        </div>
        {expanded
          ? <ChevronUp size={14} color="rgba(255, 255, 255, 0.4)" />
          : <ChevronDown size={14} color="rgba(255, 255, 255, 0.4)" />
        }
      </button>

      {/* Tracks */}
      {expanded && (
        <div style={{ padding: '0 12px 12px', display: 'flex', flexDirection: 'column', gap: 6 }}>
          {tracks.map(([type, url]) => (
            <AudioTrack
              key={type}
              label={type}
              url={url}
              ragaName={audioData.raga}
              isActive={activeTrack === type}
              onActivate={() => setActiveTrack(type)}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default RagaAudioPlayer
