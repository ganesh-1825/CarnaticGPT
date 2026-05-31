import React, { useState, useEffect, useRef } from 'react';
import { Play, Square, Music, Volume2, Sparkles, AlertCircle } from 'lucide-react';

// Carnatic Swaras Frequency mappings relative to C4 (261.63 Hz)
const SWARA_FREQS = {
  "S": 261.63,
  "R1": 277.18,  // Suddha Rishabham (C#4)
  "R2": 293.66,  // Chatusruti Rishabham (D4)
  "G2": 311.13,  // Sadharana Gandharam (D#4)
  "G3": 329.63,  // Antara Gandharam (E4)
  "M1": 349.23,  // Suddha Madhyamam (F4)
  "M2": 369.99,  // Prati Madhyamam (F#4)
  "P": 392.00,   // Panchamam (G4)
  "D1": 415.30,  // Suddha Dhaivatham (G#4)
  "D2": 440.00,  // Chatusruti Dhaivatham (A4)
  "N2": 466.16,  // Kaisiki Nishadham (A#4)
  "N3": 493.88,  // Kakali Nishadham (B4)
  "S*": 523.25   // High Shadjam (C5)
};

const RAGA_SCALES = {
  "Bhairavi": {
    arohana: ["S", "R2", "G2", "M1", "P", "D2", "N2", "S*"],
    avarohana: ["S*", "N2", "D1", "P", "M1", "G2", "R2", "S"],
    alapana: ["S", "G2", "M1", "P", "N2", "D2", "N2", "P", "M1", "G2", "R2", "S"],
    composition: ["S", "R2", "G2", "M1", "P", "P", "M1", "P", "N2", "D2", "S*", "N2", "S*"]
  },
  "Kalyani": {
    arohana: ["S", "R2", "G3", "M2", "P", "D2", "N3", "S*"],
    avarohana: ["S*", "N3", "D2", "P", "M2", "G3", "R2", "S"],
    alapana: ["S", "G3", "M2", "P", "N3", "D2", "N3", "S*", "N3", "D2", "P", "M2", "G3", "R2", "S"],
    composition: ["G3", "G3", "M2", "P", "D2", "N3", "S*", "S*", "N3", "D2", "P", "M2", "G3", "R2"]
  },
  "Mohanam": {
    arohana: ["S", "R2", "G3", "P", "D2", "S*"],
    avarohana: ["S*", "D2", "P", "G3", "R2", "S"],
    alapana: ["S", "R2", "G3", "P", "D2", "P", "G3", "P", "D2", "S*", "D2", "P", "G3", "R2", "S"],
    composition: ["G3", "G3", "R2", "S", "R2", "G3", "G3", "P", "G3", "P", "D2", "D2", "S*"]
  },
  "Mayamalavagowla": {
    arohana: ["S", "R1", "G3", "M1", "P", "D1", "N3", "S*"],
    avarohana: ["S*", "N3", "D1", "P", "M1", "G3", "R1", "S"],
    alapana: ["S", "R1", "G3", "M1", "P", "M1", "P", "D1", "N3", "S*", "N3", "D1", "P", "M1", "G3", "R1", "S"],
    composition: ["S", "R1", "G3", "M1", "P", "P", "D1", "D1", "N3", "N3", "S*", "S*"]
  },
  "Hindolam": {
    arohana: ["S", "G2", "M1", "D1", "N2", "S*"],
    avarohana: ["S*", "N2", "D1", "M1", "G2", "S"],
    alapana: ["S", "G2", "M1", "D1", "N2", "S*", "N2", "D1", "M1", "G2", "S"],
    composition: ["S", "G2", "M1", "M1", "D1", "N2", "S*", "S*", "N2", "D1", "M1", "G2", "S"]
  },
  "Todi": {
    arohana: ["S", "R1", "G2", "M1", "P", "D1", "N2", "S*"],
    avarohana: ["S*", "N2", "D1", "P", "M1", "G2", "R1", "S"],
    alapana: ["S", "R1", "G2", "M1", "P", "D1", "N2", "S*", "N2", "D1", "P", "M1", "G2", "R1", "S"],
    composition: ["S", "R1", "G2", "M1", "D1", "N2", "S*", "N2", "D1", "P", "M1", "G2", "R1", "S"]
  },
  "Sankarabharanam": {
    arohana: ["S", "R2", "G3", "M1", "P", "D2", "N3", "S*"],
    avarohana: ["S*", "N3", "D2", "P", "M1", "G3", "R2", "S"],
    alapana: ["S", "R2", "G3", "M1", "P", "D2", "N3", "S*", "N3", "D2", "P", "M1", "G3", "R2", "S"],
    composition: ["S", "R2", "G3", "P", "M1", "G3", "R2", "S", "R2", "G3", "M1", "P", "D2", "N3", "S*"]
  },
  "Hamsadhwani": {
    arohana: ["S", "R2", "G3", "P", "N3", "S*"],
    avarohana: ["S*", "N3", "P", "G3", "R2", "S"],
    alapana: ["S", "R2", "G3", "P", "N3", "S*", "N3", "P", "G3", "R2", "G3", "P", "S"],
    composition: ["S", "R2", "G3", "P", "N3", "S*", "N3", "P", "G3", "R2", "S", "R2", "G3"]
  },
  "Kharaharapriya": {
    arohana: ["S", "R2", "G2", "M1", "P", "D2", "N2", "S*"],
    avarohana: ["S*", "N2", "D2", "P", "M1", "G2", "R2", "S"],
    alapana: ["S", "R2", "G2", "M1", "P", "D2", "N2", "S*", "N2", "D2", "P", "M1", "G2", "R2", "S"],
    composition: ["G2", "M1", "P", "D2", "N2", "S*", "N2", "D2", "P", "M1", "G2", "R2", "S"]
  },
  "Abhogi": {
    arohana: ["S", "R2", "G2", "M1", "D2", "S*"],
    avarohana: ["S*", "D2", "M1", "G2", "R2", "S"],
    alapana: ["S", "R2", "G2", "M1", "D2", "M1", "G2", "R2", "G2", "M1", "D2", "S*"],
    composition: ["S", "R2", "G2", "M1", "D2", "S*", "D2", "M1", "G2", "R2", "S", "R2", "G2"]
  },
  "Revathi": {
    arohana: ["S", "R1", "G2", "M1", "D1", "N2", "S*"],
    avarohana: ["S*", "N2", "D1", "M1", "G2", "R1", "S"],
    alapana: ["S", "R1", "G2", "M1", "D1", "N2", "S*", "N2", "D1", "M1", "G2", "R1", "S"],
    composition: ["S", "R1", "G2", "M1", "D1", "N2", "D1", "M1", "G2", "R1", "S", "G2", "M1"]
  },
  "Sivaranjani": {
    arohana: ["S", "R2", "G2", "P", "D2", "S*"],
    avarohana: ["S*", "D2", "P", "G2", "R2", "S"],
    alapana: ["S", "R2", "G2", "P", "D2", "S*", "D2", "P", "G2", "R2", "S", "R2", "G2"],
    composition: ["S", "R2", "G2", "P", "D2", "P", "G2", "R2", "S", "R2", "G2", "P", "D2"]
  },
  "Madhyamavathi": {
    arohana: ["S", "R2", "M1", "P", "N2", "S*"],
    avarohana: ["S*", "N2", "P", "M1", "R2", "S"],
    alapana: ["S", "R2", "M1", "P", "N2", "S*", "N2", "P", "M1", "R2", "S", "R2", "M1"],
    composition: ["S", "R2", "M1", "P", "N2", "P", "M1", "R2", "S", "R2", "M1", "P", "N2"]
  },
  "Shuddha_Saveri": {
    arohana: ["S", "R2", "M1", "P", "D2", "S*"],
    avarohana: ["S*", "D2", "P", "M1", "R2", "S"],
    alapana: ["S", "R2", "M1", "P", "D2", "S*", "D2", "P", "M1", "R2", "S", "R2", "M1"],
    composition: ["S", "R2", "M1", "P", "D2", "P", "M1", "R2", "S", "R2", "M1", "P", "D2"]
  },
  "Amruthavarshini": {
    arohana: ["S", "G3", "M2", "P", "N3", "S*"],
    avarohana: ["S*", "N3", "P", "M2", "G3", "S"],
    alapana: ["S", "G3", "M2", "P", "N3", "S*", "N3", "P", "M2", "G3", "S", "G3", "M2"],
    composition: ["S", "G3", "M2", "P", "N3", "P", "M2", "G3", "S", "G3", "M2", "P", "N3"]
  },
  "Hamsanadam": {
    arohana: ["S", "R2", "M2", "P", "N3", "S*"],
    avarohana: ["S*", "N3", "P", "M2", "R2", "S"],
    alapana: ["S", "R2", "M2", "P", "N3", "S*", "N3", "P", "M2", "R2", "S", "R2", "M2"],
    composition: ["S", "R2", "M2", "P", "N3", "P", "M2", "R2", "S", "R2", "M2", "P", "N3"]
  },
  "Bilahari": {
    arohana: ["S", "R2", "G3", "P", "D2", "S*"],
    avarohana: ["S*", "N3", "D2", "P", "M1", "G3", "R2", "S"],
    alapana: ["S", "R2", "G3", "P", "D2", "S*", "N3", "D2", "P", "M1", "G3", "R2", "S"],
    composition: ["S", "R2", "G3", "P", "D2", "P", "G3", "R2", "S", "R2", "G3", "P", "D2"]
  },
  "Kamboji": {
    arohana: ["S", "R2", "G3", "M1", "P", "D2", "S*"],
    avarohana: ["S*", "N2", "D2", "P", "M1", "G3", "R2", "S"],
    alapana: ["S", "R2", "G3", "M1", "P", "D2", "S*", "N2", "D2", "P", "M1", "G3", "R2", "S"],
    composition: ["G3", "M1", "P", "D2", "S*", "N2", "D2", "P", "M1", "G3", "R2", "S", "R2"]
  },
  "Charukesi": {
    arohana: ["S", "R2", "G3", "M1", "P", "D1", "N2", "S*"],
    avarohana: ["S*", "N2", "D1", "P", "M1", "G3", "R2", "S"],
    alapana: ["S", "R2", "G3", "M1", "P", "D1", "N2", "S*", "N2", "D1", "P", "M1", "G3", "R2", "S"],
    composition: ["S", "R2", "G3", "M1", "P", "D1", "N2", "D1", "P", "M1", "G3", "R2", "S"]
  },
  "Keeravani": {
    arohana: ["S", "R2", "G2", "M1", "P", "D1", "N3", "S*"],
    avarohana: ["S*", "N3", "D1", "P", "M1", "G2", "R2", "S"],
    alapana: ["S", "R2", "G2", "M1", "P", "D1", "N3", "S*", "N3", "D1", "P", "M1", "G2", "R2", "S"],
    composition: ["S", "R2", "G2", "M1", "D1", "N3", "S*", "N3", "D1", "P", "M1", "G2", "R2", "S"]
  },
  "Anandabhairavi": {
    arohana: ["S", "R2", "G2", "M1", "P", "D2", "S*"],
    avarohana: ["S*", "N2", "D2", "P", "M1", "G2", "R2", "S"],
    alapana: ["S", "R2", "G2", "M1", "P", "D2", "S*", "N2", "D2", "P", "M1", "G2", "R2", "S"],
    composition: ["G2", "M1", "P", "D2", "S*", "N2", "D2", "P", "M1", "G2", "R2", "S", "R2"]
  },
  "Bhupalam": {
    arohana: ["S", "R1", "G2", "P", "D1", "S*"],
    avarohana: ["S*", "D1", "P", "G2", "R1", "S"],
    alapana: ["S", "R1", "G2", "P", "D1", "S*", "D1", "P", "G2", "R1", "S", "R1", "G2"],
    composition: ["S", "R1", "G2", "P", "D1", "P", "G2", "R1", "S", "R1", "G2", "P", "D1"]
  },
  "Arabhi": {
    arohana: ["S", "R2", "M1", "P", "D2", "S*"],
    avarohana: ["S*", "N3", "D2", "P", "M1", "G3", "R2", "S"],
    alapana: ["S", "R2", "M1", "P", "D2", "S*", "N3", "D2", "P", "M1", "G3", "R2", "S"],
    composition: ["S", "R2", "M1", "P", "D2", "P", "M1", "R2", "S", "R2", "M1", "P", "D2"]
  },
  "Nattai": {
    arohana: ["S", "R2", "G3", "M1", "P", "N3", "S*"],
    avarohana: ["S*", "N3", "P", "M1", "G3", "R2", "S"],
    alapana: ["S", "R2", "G3", "M1", "P", "N3", "S*", "N3", "P", "M1", "G3", "R2", "S"],
    composition: ["G3", "M1", "P", "N3", "S*", "N3", "P", "M1", "G3", "R2", "S", "R2", "G3"]
  },
  "Yaman": {
    arohana: ["S", "R2", "G3", "M2", "P", "D2", "N3", "S*"],
    avarohana: ["S*", "N3", "D2", "P", "M2", "G3", "R2", "S"],
    alapana: ["S", "R2", "G3", "M2", "P", "D2", "N3", "S*", "N3", "D2", "P", "M2", "G3", "R2", "S"],
    composition: ["S", "R2", "G3", "M2", "D2", "N3", "S*", "N3", "D2", "P", "M2", "G3", "R2", "S"]
  },
  "Bhairav": {
    arohana: ["S", "R1", "G3", "M1", "P", "D1", "N3", "S*"],
    avarohana: ["S*", "N3", "D1", "P", "M1", "G3", "R1", "S"],
    alapana: ["S", "R1", "G3", "M1", "P", "D1", "N3", "S*", "N3", "D1", "P", "M1", "G3", "R1", "S"],
    composition: ["S", "R1", "G3", "M1", "D1", "N3", "S*", "N3", "D1", "P", "M1", "G3", "R1", "S"]
  },
  "Bageshri": {
    arohana: ["S", "G2", "M1", "D2", "N2", "S*"],
    avarohana: ["S*", "N2", "D2", "M1", "G2", "R2", "S"],
    alapana: ["S", "G2", "M1", "D2", "N2", "S*", "N2", "D2", "M1", "G2", "R2", "S", "G2"],
    composition: ["S", "G2", "M1", "D2", "N2", "D2", "M1", "G2", "R2", "S", "G2", "M1", "D2"]
  },
  "Darbari_Kanada": {
    arohana: ["S", "R2", "G2", "M1", "P", "D1", "N2", "S*"],
    avarohana: ["S*", "N2", "D1", "P", "M1", "G2", "R2", "S"],
    alapana: ["S", "R2", "G2", "M1", "P", "D1", "N2", "S*", "N2", "D1", "P", "M1", "G2", "R2", "S"],
    composition: ["G2", "M1", "P", "D1", "N2", "S*", "N2", "D1", "P", "M1", "G2", "R2", "S"]
  },
  "Malkouns": {
    arohana: ["S", "G2", "M1", "D1", "N2", "S*"],
    avarohana: ["S*", "N2", "D1", "M1", "G2", "S"],
    alapana: ["S", "G2", "M1", "D1", "N2", "S*", "N2", "D1", "M1", "G2", "S", "G2", "M1"],
    composition: ["S", "G2", "M1", "D1", "N2", "D1", "M1", "G2", "S", "G2", "M1", "D1", "N2"]
  },
  "Desh": {
    arohana: ["S", "R2", "G3", "M1", "P", "N2", "S*"],
    avarohana: ["S*", "N2", "D2", "P", "M1", "G2", "R2", "S"],
    alapana: ["S", "R2", "G3", "M1", "P", "N2", "S*", "N2", "D2", "P", "M1", "G2", "R2", "S"],
    composition: ["S", "R2", "G3", "M1", "P", "N2", "P", "M1", "G2", "R2", "S", "R2", "G3"]
  },
  "Durga": {
    arohana: ["S", "R2", "M1", "P", "D2", "S*"],
    avarohana: ["S*", "D2", "P", "M1", "R2", "S"],
    alapana: ["S", "R2", "M1", "P", "D2", "S*", "D2", "P", "M1", "R2", "S", "R2", "M1"],
    composition: ["S", "R2", "M1", "P", "D2", "P", "M1", "R2", "S", "R2", "M1", "P", "D2"]
  }
};

// Flexible raga name matching for multi-word names, underscores, hyphens, case variations
const SUPPORTED_RAGAS = Object.keys(RAGA_SCALES);
const normalizeRagaName = (name) => {
  const n = name.trim().toLowerCase().replace(/[\s_-]+/g, '');
  return SUPPORTED_RAGAS.find(r => r.toLowerCase().replace(/[\s_-]+/g, '') === n) || null;
};

export default function RagaAudioPanel({ raga }) {
  const [playingType, setPlayingType] = useState(null); // 'arohana', 'avarohana', 'alapana', 'sample', null
  const [currentSwara, setCurrentSwara] = useState("");
  const [activeScaleIdx, setActiveScaleIdx] = useState(-1);
  const [isSynthMode, setIsSynthMode] = useState(false);
  
  const audioRef = useRef(null);
  const audioCtxRef = useRef(null);
  const synthTimeoutsRef = useRef([]);

  // Resolve target raga name using flexible matching
  const cleanRaga = normalizeRagaName(raga) || 'Mayamalavagowla';
  const ragaData = RAGA_SCALES[cleanRaga] || RAGA_SCALES["Mayamalavagowla"];

  useEffect(() => {
    return () => stopAllPlayback();
  }, []);

  useEffect(() => {
    stopAllPlayback();
  }, [raga]);

  const stopAllPlayback = () => {
    // 1. Stop HTML5 audio player
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.src = "";
    }
    
    // 2. Stop Web Audio synthesizer
    synthTimeoutsRef.current.forEach(t => clearTimeout(t));
    synthTimeoutsRef.current = [];
    
    if (audioCtxRef.current && audioCtxRef.current.state !== 'closed') {
      audioCtxRef.current.close();
    }
    audioCtxRef.current = null;
    
    setPlayingType(null);
    setCurrentSwara("");
    setActiveScaleIdx(-1);
    setIsSynthMode(false);
  };

  const playFile = (type) => {
    stopAllPlayback();
    setPlayingType(type);
    
    // Define target static file path
    const filePaths = {
      arohana: `/audio/${cleanRaga}/arohana.mp3`,
      avarohana: `/audio/${cleanRaga}/avarohana.mp3`,
      alapana: `/audio/${cleanRaga}/alapana.mp3`,
      sample: `/audio/${cleanRaga}/sample_song.mp3`
    };
    
    const targetSrc = filePaths[type];
    
    if (audioRef.current) {
      audioRef.current.src = targetSrc;
      audioRef.current.load(); // Force loading of new file buffers immediately
      
      audioRef.current.play().catch(err => {
        // If file fails to play (like 404 missing in local server),
        // trigger the in-browser Web Audio Synthesizer fallback automatically!
        console.warn(`Static clip ${targetSrc} failed to load. Defaulting to WebSynthesizer fallback.`);
        playSynthesizerFallback(type);
      });
    }
  };

  const playSynthesizerFallback = (type) => {
    setIsSynthMode(true);
    
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) return;
    
    const audioCtx = new AudioContextClass();
    audioCtxRef.current = audioCtx;
    
    const startTime = audioCtx.currentTime;
    let sequence = [];
    let noteDuration = 0.6;
    
    if (type === "arohana") {
      sequence = ragaData.arohana;
    } else if (type === "avarohana") {
      sequence = ragaData.avarohana;
    } else if (type === "alapana") {
      sequence = ragaData.alapana;
      noteDuration = 0.8; // slower, expressive tempo for alapana
    } else if (type === "sample") {
      sequence = ragaData.composition;
      noteDuration = 0.5; // faster tempo for composition plucks
    }
    
    sequence.forEach((swara, idx) => {
      const freq = SWARA_FREQS[swara] || 261.63;
      const noteStartTime = startTime + idx * noteDuration;
      
      const osc = audioCtx.createOscillator();
      const gainNode = audioCtx.createGain();
      
      // Use warm triangle wave for flute/reed sound
      osc.type = "triangle";
      
      // Alapana mode: add expressive sliding/gamaka sweeps
      if (type === "alapana" && idx > 0) {
        const prevFreq = SWARA_FREQS[sequence[idx - 1]] || 261.63;
        osc.frequency.setValueAtTime(prevFreq, noteStartTime);
        osc.frequency.exponentialRampToValueAtTime(freq, noteStartTime + 0.25); // Gamaka portamento slide
      } else {
        osc.frequency.setValueAtTime(freq, noteStartTime);
      }
      
      // Envelope setup to avoid clicking
      gainNode.gain.setValueAtTime(0, noteStartTime);
      gainNode.gain.linearRampToValueAtTime(0.18, noteStartTime + 0.05); // Attack
      gainNode.gain.linearRampToValueAtTime(0.12, noteStartTime + noteDuration - 0.1); // Sustain
      gainNode.gain.exponentialRampToValueAtTime(0.001, noteStartTime + noteDuration); // Release
      
      osc.connect(gainNode);
      gainNode.connect(audioCtx.destination);
      
      osc.start(noteStartTime);
      osc.stop(noteStartTime + noteDuration);
      
      // Schedule visual UI transitions
      const t = setTimeout(() => {
        setActiveScaleIdx(idx);
        setCurrentSwara(swara);
      }, idx * noteDuration * 1000);
      
      synthTimeoutsRef.current.push(t);
    });
    
    // Auto-stop at sequence end
    const endT = setTimeout(() => {
      stopAllPlayback();
    }, sequence.length * noteDuration * 1000);
    
    synthTimeoutsRef.current.push(endT);
  };

  const handleAudioEnded = () => {
    stopAllPlayback();
  };

  const buttons = [
    { type: "arohana", label: "Play Arohana", desc: "Ascending Scale" },
    { type: "avarohana", label: "Play Avarohana", desc: "Descending Scale" },
    { type: "alapana", label: "Play Alapana", desc: "Microtonal Improv" },
    { type: "sample", label: "Play Sample Song", desc: "Seeded kriti phrase" }
  ];

  return (
    <div className="glass-card animate-fade-in" style={{
      marginTop: '20px',
      padding: '20px 24px',
      background: 'rgba(28, 36, 58, 0.45)',
      borderRadius: 'var(--border-radius-lg)',
      border: playingType ? '1px solid rgba(22, 219, 204, 0.3)' : '1px solid var(--glass-border)',
      boxShadow: playingType ? '0 0 20px rgba(22, 219, 204, 0.12)' : '0 6px 20px rgba(0, 0, 0, 0.15)',
      transition: 'all 0.3s ease'
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
        paddingBottom: '12px',
        marginBottom: '16px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Music size={16} color="hsl(var(--accent-teal))" />
          <h4 style={{ fontSize: '0.9rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#fff', margin: 0 }}>
            🎵 {cleanRaga} Audio Demonstration
          </h4>
        </div>
        
        {playingType && (
          <button 
            onClick={stopAllPlayback} 
            style={{
              background: 'rgba(255, 0, 0, 0.15)',
              border: '1px solid rgba(255, 0, 0, 0.3)',
              color: 'red',
              fontSize: '0.75rem',
              fontWeight: 700,
              padding: '3px 10px',
              borderRadius: 'var(--border-radius-sm)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}
          >
            <Square size={10} fill="red" /> Stop Clip
          </button>
        )}
      </div>

      {/* Buttons Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
        gap: '12px'
      }}>
        {buttons.map((btn) => {
          const isActive = playingType === btn.type;
          return (
            <button
              key={btn.type}
              onClick={() => playFile(btn.type)}
              className="glass-card"
              style={{
                background: isActive 
                  ? 'linear-gradient(135deg, rgba(88, 30, 168, 0.35) 0%, rgba(22, 219, 204, 0.25) 100%)'
                  : 'rgba(255, 255, 255, 0.02)',
                border: isActive ? '1px solid hsl(var(--accent-teal))' : '1px solid var(--glass-border)',
                borderRadius: 'var(--border-radius-md)',
                padding: '12px 10px',
                cursor: 'pointer',
                textAlign: 'center',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '4px',
                transition: 'all 0.2s ease'
              }}
              onMouseEnter={(e) => {
                if (!isActive) e.currentTarget.style.borderColor = 'hsl(var(--accent-teal))';
              }}
              onMouseLeave={(e) => {
                if (!isActive) e.currentTarget.style.borderColor = 'var(--glass-border)';
              }}
            >
              <span style={{ fontSize: '0.85rem', fontWeight: 700, color: isActive ? 'hsl(var(--accent-teal))' : '#fff' }}>
                {btn.label}
              </span>
              <span style={{ fontSize: '0.65rem', color: 'hsl(var(--text-secondary))' }}>
                {btn.desc}
              </span>
            </button>
          );
        })}
      </div>

      {/* Status Bar */}
      {playingType && (
        <div style={{
          marginTop: '16px',
          background: 'rgba(255, 255, 255, 0.01)',
          border: '1px solid rgba(255, 255, 255, 0.03)',
          borderRadius: '8px',
          padding: '10px 14px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontSize: '0.8rem'
        }} className="animate-fade-in">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ 
              display: 'inline-block', 
              width: '6px', 
              height: '6px', 
              borderRadius: '50%', 
              background: 'hsl(var(--accent-teal))',
              animation: 'spin 1.5s linear infinite'
            }}></span>
            <span style={{ color: 'hsl(var(--text-secondary))', fontWeight: 600 }}>
              Playing: <span style={{ color: '#fff', textTransform: 'capitalize' }}>{playingType}</span>
            </span>
            {isSynthMode && (
              <span style={{
                background: 'rgba(219, 166, 22, 0.1)',
                color: 'hsl(var(--accent-gold))',
                fontSize: '0.65rem',
                fontWeight: 700,
                padding: '2px 6px',
                borderRadius: '4px',
                border: '1px solid rgba(219, 166, 22, 0.15)',
                display: 'flex',
                alignItems: 'center',
                gap: '2px'
              }}>
                <Sparkles size={10} /> Synth Fallback
              </span>
            )}
          </div>
          
          {isSynthMode && currentSwara && (
            <span style={{ fontWeight: 800, color: 'hsl(var(--accent-teal))' }}>
              Swara Syllable: "{currentSwara.replace("*", "")}"
            </span>
          )}
          
          {!isSynthMode && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', opacity: 0.7 }}>
              <Volume2 size={14} />
              <span>MP3 Stream</span>
            </div>
          )}
        </div>
      )}

      {/* Hidden HTML5 Audio Element */}
      <audio 
        ref={audioRef} 
        onEnded={handleAudioEnded}
      />
    </div>
  );
}
