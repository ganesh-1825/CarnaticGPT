import React from 'react';

export default function AudioPlayerComponent({ audioPaths, title }) {
  // Expected paths format: { alapana: "url", arohana: "url", avarohana: "url" }
  return (
    <div className="bg-neutral-950 p-3 rounded border border-neutral-800 space-y-3">
      <div className="text-xs font-semibold text-neutral-300 flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></span>
        Audio Reference Architecture Track Elements
      </div>

      <div className="grid grid-cols-1 gap-2">
        {Object.entries(audioPaths).map(([trackName, trackUrl]) => (
          <div key={trackName} className="flex flex-col sm:flex-row sm:items-center justify-between bg-neutral-900 p-2 rounded border border-neutral-800 gap-2">
            <span className="text-[11px] font-mono uppercase text-amber-400 tracking-wider">
              ▶ {trackName}
            </span>
            <audio
              controls
              src={trackUrl}
              className="h-6 max-w-full sm:max-w-[240px] opacity-80 hover:opacity-100 transition"
            >
              Your browser does not support the audio playback control layer.
            </audio>
          </div>
        ))}
      </div>
    </div>
  );
}