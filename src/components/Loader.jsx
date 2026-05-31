import React from 'react';

export default function LoadingOverlay({ message }) {
  return (
    <div className="fixed inset-0 bg-neutral-950/80 backdrop-blur-sm z-50 flex flex-col items-center justify-center space-y-4">
      <div className="w-12 h-12 border-4 border-amber-500 border-t-transparent rounded-full animate-spin"></div>
      <div className="bg-neutral-900 border border-neutral-800 px-6 py-3 rounded-lg shadow-2xl text-center min-w-[260px]">
        <p className="text-sm font-medium tracking-wide text-amber-400 animate-pulse">
          {message || "Processing Pipeline Elements..."}
        </p>
        <p className="text-[10px] text-neutral-500 mt-1">Please wait, modifying index mappings</p>
      </div>
    </div>
  );
}