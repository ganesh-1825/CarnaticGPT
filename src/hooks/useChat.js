import { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';

export function useChat() {
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Fetch active sessions list
  const loadSessions = useCallback(async () => {
    try {
      const data = await api.getSessions();
      setSessions(data);
      if (data.length > 0 && !activeSessionId) {
        // Default to loading the first session
        setActiveSessionId(data[0].id);
      }
    } catch (err) {
      console.error(err);
    }
  }, [activeSessionId]);
  
  // Load message logs for active session
  useEffect(() => {
    if (!activeSessionId) return;
    
    let isMounted = true;
    const fetchHistory = async () => {
      setLoading(true);
      setError(null);
      try {
        const history = await api.getHistory(activeSessionId);
        if (isMounted) {
          setMessages(history);
        }
      } catch (err) {
        if (isMounted) {
          setError("Failed to load message history");
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };
    
    fetchHistory();
    return () => { isMounted = false; };
  }, [activeSessionId]);
  
  // Helper to format session titles
  const createSessionTitle = (query) => {
    return query.length > 30 ? query.substring(0, 30) + "..." : query;
  };

  const generateId = () => {
    return (window.crypto && window.crypto.randomUUID) 
      ? window.crypto.randomUUID() 
      : Date.now().toString(36) + Math.random().toString(36).substring(2);
  };

  // Send chat message
  const sendMessage = async (text) => {
    if (!text.trim()) return;
    
    let sessionId = activeSessionId;
    if (!sessionId) {
      // Create new dynamic session id
      sessionId = generateId();
      setActiveSessionId(sessionId);
    }
    
    // Auto-update the active session title locally in the sidebar immediately (only on first question)
    setSessions(prev => {
      const exists = prev.find(s => s.id === sessionId);
      if (exists) {
        if (exists.title === "New Chat") {
          const sessionTitle = createSessionTitle(text);
          return prev.map(s => s.id === sessionId ? { ...s, title: sessionTitle } : s);
        }
        return prev;
      } else {
        const sessionTitle = createSessionTitle(text);
        return [{ id: sessionId, title: sessionTitle, created_at: new Date().toISOString() }, ...prev];
      }
    });
    
    // Add user message locally for immediate UI update
    const userMsg = {
      id: Date.now(),
      sender: "user",
      content: text,
      created_at: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);
    
    try {
      const ragResponse = await api.sendQuery(sessionId, text);
      
      // Add assistant response
      const assistantMsg = {
        id: Date.now() + 1,
        sender: "assistant",
        content: ragResponse.response,
        citations: ragResponse.citations,
        confidence: ragResponse.confidence,
        detected_raga: ragResponse.detected_raga,
        created_at: new Date().toISOString()
      };
      
      // Update with assistant response
      setMessages(prev => [...prev, assistantMsg]);
      await loadSessions(); // Sync and verify with backend DB
    } catch (err) {
      setError("Failed to generate response. Please verify server connection.");
    } finally {
      setLoading(false);
    }
  };
  
  // Delete dynamic session
  const deleteSession = async (id) => {
    try {
      await api.deleteSession(id);
      setSessions(prev => prev.filter(s => s.id !== id));
      if (activeSessionId === id) {
        setMessages([]);
        setActiveSessionId(null);
      }
    } catch (err) {
      console.error(err);
    }
  };
  
  // Start new session thread
  const startNewSession = () => {
    // Avoid creating multiple empty "New Chat" sessions
    const hasEmptyChat = sessions.find(s => s.title === "New Chat");
    if (hasEmptyChat) {
      setActiveSessionId(hasEmptyChat.id);
      setMessages([]);
      return;
    }

    const newSessionId = generateId();
    setActiveSessionId(newSessionId);
    setMessages([]);
    setSessions(prev => [{
      id: newSessionId,
      title: "New Chat",
      created_at: new Date().toISOString()
    }, ...prev]);
  };
  
  return {
    sessions,
    activeSessionId,
    setActiveSessionId,
    messages,
    loading,
    error,
    sendMessage,
    deleteSession,
    startNewSession,
    loadSessions
  };
}
