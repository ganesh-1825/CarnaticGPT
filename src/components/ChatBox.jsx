import React, { useRef, useEffect } from 'react';
import ChatMessage from './ChatMessage';
import SuggestedQuestions from './SuggestedQuestions';
import ModelInfo from './ModelInfo';

export default function ChatBox({ messages, loading, onSelectQuestion }) {
  const messagesEndRef = useRef(null);
  
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);
  
  return (
    <div style={{
      flex: 1,
      overflowY: 'auto',
      padding: '24px',
      display: 'flex',
      flexDirection: 'column',
      gap: '20px'
    }}>
      {messages.map((msg, index) => {
        const hasAudio = !!msg.detected_raga;
        
        // Translate message properties into the format expected by ChatMessage
        const mappedMessage = {
          role: msg.sender,
          content: msg.content,
          citations: msg.citations?.map(c => ({
            book_name: c.book_name || "South Indian Music",
            page_number: c.page || c.page_number || 1,
            confidence: c.confidence || (c.score >= 0.8 ? "High Confidence" : c.score >= 0.5 ? "Medium Confidence" : "Low Confidence"),
            excerpt: c.text
          })) || [],
          top_confidence: msg.confidence,
          audio: hasAudio ? (() => {
            // Normalize raga name for filesystem paths (spaces → underscores)
            const ragaDir = msg.detected_raga.replace(/\s+/g, '_');
            return {
              found: true,
              raga: msg.detected_raga,
              audio: {
                alapana: `/audio/${ragaDir}/alapana.mp3`,
                arohana: `/audio/${ragaDir}/arohana.mp3`,
                avarohana: `/audio/${ragaDir}/avarohana.mp3`,
              }
            };
          })() : null
        };

        return (
          <ChatMessage key={msg.id || index} message={mappedMessage} />
        );
      })}
      
      {loading && (
        <div style={{ display: 'flex', gap: '16px', padding: '16px', maxWidth: '80%' }}>
          <div className="glow-spinner" style={{ width: '24px', height: '24px' }}></div>
          <span style={{ color: 'hsl(var(--text-secondary))', fontSize: '0.9rem' }}>
            Retrieving documents and reasoning...
          </span>
        </div>
      )}
      
      {messages.length === 0 && !loading && (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          margin: 'auto 0',
          textAlign: 'center',
          color: 'hsl(var(--text-secondary))',
          padding: '40px 20px'
        }} className="animate-fade-in">
          <h2 style={{ 
            fontSize: '2.5rem', 
            marginBottom: '8px', 
            fontWeight: 800,
            background: 'linear-gradient(135deg, #fff 0%, hsl(var(--text-secondary)) 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            letterSpacing: '-0.03em'
          }}>Namaskaram 🎵</h2>
          
          <p style={{ 
            maxWidth: '520px', 
            fontSize: '0.95rem', 
            lineHeight: 1.6, 
            color: 'hsl(var(--text-secondary))', 
            marginBottom: '10px' 
          }}>
            Welcome to **CarnaticGPT**. Explore South Indian classical music through smart RAG retrieval across curated texts and treatises.
          </p>
          
          <SuggestedQuestions onSelectQuestion={onSelectQuestion} />
          
          <ModelInfo />
        </div>
      )}
      <div ref={messagesEndRef} />
    </div>
  );
}
