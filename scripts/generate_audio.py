import os
import math
import wave
import struct

# Carnatic Swaras Frequency mappings relative to C4 (261.63 Hz)
SWARA_FREQS = {
    "S": 261.63,
    "R1": 277.18,  # Suddha Rishabham (C#4)
    "R2": 293.66,  # Chatusruti Rishabham (D4)
    "G2": 311.13,  # Sadharana Gandharam (D#4)
    "G3": 329.63,  # Antara Gandharam (E4)
    "M1": 349.23,  # Suddha Madhyamam (F4)
    "M2": 369.99,  # Prati Madhyamam (F#4)
    "P": 392.00,   # Panchamam (G4)
    "D1": 415.30,  # Suddha Dhaivatham (G#4)
    "D2": 440.00,  # Chatusruti Dhaivatham (A4)
    "N2": 466.16,  # Kaisiki Nishadham (A#4)
    "N3": 493.88,  # Kakali Nishadham (B4)
    "S*": 523.25   # High Shadjam (C5)
}

RAGA_SCALES = {
    "Bhairavi": {
        "arohana": ["S", "R2", "G2", "M1", "P", "D2", "N2", "S*"],
        "avarohana": ["S*", "N2", "D1", "P", "M1", "G2", "R2", "S"],
        "alapana": ["S", "G2", "M1", "P", "N2", "D2", "N2", "P", "M1", "G2", "R2", "S"],
        "sample": ["S", "R2", "G2", "M1", "P", "P", "M1", "P", "N2", "D2", "S*", "N2", "S*"]
    },
    "Kalyani": {
        "arohana": ["S", "R2", "G3", "M2", "P", "D2", "N3", "S*"],
        "avarohana": ["S*", "N3", "D2", "P", "M2", "G3", "R2", "S"],
        "alapana": ["S", "G3", "M2", "P", "N3", "D2", "N3", "S*", "N3", "D2", "P", "M2", "G3", "R2", "S"],
        "sample": ["G3", "G3", "M2", "P", "D2", "N3", "S*", "S*", "N3", "D2", "P", "M2", "G3", "R2"]
    },
    "Mohanam": {
        "arohana": ["S", "R2", "G3", "P", "D2", "S*"],
        "avarohana": ["S*", "D2", "P", "G3", "R2", "S"],
        "alapana": ["S", "R2", "G3", "P", "D2", "P", "G3", "P", "D2", "S*", "D2", "P", "G3", "R2", "S"],
        "sample": ["G3", "G3", "R2", "S", "R2", "G3", "G3", "P", "G3", "P", "D2", "D2", "S*"]
    },
    "Hindolam": {
        "arohana": ["S", "G2", "M1", "D1", "N2", "S*"],
        "avarohana": ["S*", "N2", "D1", "M1", "G2", "S"],
        "alapana": ["S", "G2", "M1", "D1", "N2", "S*", "N2", "D1", "M1", "G2", "S"],
        "sample": ["S", "G2", "M1", "M1", "D1", "N2", "S*", "S*", "N2", "D1", "M1", "G2", "S"]
    }
}

def generate_swara_wav(filepath, swaras, duration_per_note=0.5, sample_rate=22050):
    """Generates a WAV file containing synthesized notes for the given list of swara syllables."""
    # Ensure parent dir exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with wave.open(filepath, 'wb') as w:
        w.setnchannels(1)  # Mono
        w.setsampwidth(2)  # 16-bit PCM
        w.setframerate(sample_rate)
        
        for idx, swara in enumerate(swaras):
            freq = SWARA_FREQS.get(swara, 261.63)
            num_samples = int(duration_per_note * sample_rate)
            
            for i in range(num_samples):
                t = i / sample_rate
                
                # Apply envelope (Attack, Decay, Sustain, Release)
                # Linear attack in first 10% of note, decay/sustain, release in last 15%
                envelope = 1.0
                attack_len = int(num_samples * 0.1)
                release_len = int(num_samples * 0.15)
                
                if i < attack_len:
                    envelope = i / attack_len
                elif i > num_samples - release_len:
                    envelope = (num_samples - i) / release_len
                
                # Alapana style pitch slides (gamakas)
                current_freq = freq
                if len(swaras) > 1 and idx > 0 and idx % 3 == 0 and i < num_samples * 0.4:
                    # slide from previous note to current note
                    prev_freq = SWARA_FREQS.get(swaras[idx - 1], 261.63)
                    slide_pct = i / (num_samples * 0.4)
                    current_freq = prev_freq + (freq - prev_freq) * slide_pct
                
                # Synthesize warm triangle-like wave with slight second harmonic for realism
                val = 0.7 * math.sin(2 * math.pi * current_freq * t) + 0.3 * math.sin(4 * math.pi * current_freq * t)
                val *= envelope * 16384  # Scale to 16-bit range (max 32767)
                
                packed = struct.pack('<h', int(val))
                w.writeframesraw(packed)

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Target directories
    assets_audio_dir = os.path.join(base_dir, "assets", "audio")
    frontend_audio_dir = os.path.join(base_dir, "frontend", "public", "audio")
    
    print(f"Generating educational raga audio files...")
    
    for raga, types in RAGA_SCALES.items():
        print(f"Synthesizing swaras for Raga {raga}...")
        for type_name, swaras in types.items():
            # Standard duration parameters
            dur = 0.5
            if type_name == "alapana":
                dur = 0.75  # slower and more expressive
            elif type_name == "sample":
                dur = 0.45  # faster composition pace
                
            # Create filenames (WAV disguised as MP3, fully sniffable and playable by HTML5 Audio)
            filename = f"{type_name}.mp3"
            
            # Destination 1: assets/audio/Raga/filename
            path1 = os.path.join(assets_audio_dir, raga, filename)
            generate_swara_wav(path1, swaras, duration_per_note=dur)
            
            # Destination 2: frontend/public/audio/Raga/filename
            path2 = os.path.join(frontend_audio_dir, raga, filename)
            generate_swara_wav(path2, swaras, duration_per_note=dur)
            
    print("Audio assets successfully generated and synced in both locations!")

if __name__ == "__main__":
    main()
