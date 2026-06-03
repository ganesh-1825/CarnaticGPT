import React from 'react';
import ragas from "../data/youtube_ragas.json";

function AudioPlayer({ ragaName }) {
  const song = ragas.find(
    x => x.ragam.toLowerCase() === ragaName.toLowerCase()
  );

  if (!song) {
    return (
      <div style={{ color: 'hsl(var(--text-secondary))', padding: '10px' }}>
        Audio unavailable for {ragaName}
      </div>
    );
  }

  // Handle potential YouTube URL variations safely
  const embedUrl = song.youtube.includes("watch?v=")
    ? song.youtube.replace("watch?v=", "embed/")
    : song.youtube; // fallback if already an embed or different format

  return (
    <div className="glass-card animate-fade-in" style={{
      marginTop: '16px',
      padding: '16px 20px',
      background: 'rgba(28, 36, 58, 0.45)',
      borderRadius: 'var(--border-radius-md)',
      border: '1px solid var(--glass-border)',
      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
    }}>
      <h3 style={{ fontSize: '1rem', color: '#fff', marginBottom: '12px' }}>
        {ragaName} Demo - {song.song_name}
      </h3>

      <iframe
        width="100%"
        height="120"
        src={embedUrl}
        frameBorder="0"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowFullScreen
        style={{ borderRadius: '8px' }}
      />
    </div>
  );
}

export default AudioPlayer;
