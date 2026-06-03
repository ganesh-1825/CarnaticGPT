/**
 * CarnaticGPT Client API Service Layer
 */

const API_BASE = ""; // Handled by Vite reverse proxy in local development

function getHeaders() {
  const token = localStorage.getItem("carnatic_token");
  const headers = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

export const api = {
  // --- AUTH ENTITY ---
  async login(username, password) {
    const params = new URLSearchParams();
    params.append("username", username);
    params.append("password", password);
    
    const res = await fetch(`${API_BASE}/api/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: params,
    });
    
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Authentication login failed");
    }
    return res.json();
  },
  
  async register(username, password) {
    const res = await fetch(`${API_BASE}/api/auth/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username, password }),
    });
    
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Registration failed");
    }
    return res.json();
  },
  
  // --- CHAT INTERACTION ENTITY ---
  async sendQuery(conversationId, message) {
    const res = await fetch(`${API_BASE}/api/chat/query`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ conversation_id: conversationId, message }),
    });
    
    if (!res.ok) {
      throw new Error("Failed to resolve RAG chat response");
    }
    return res.json();
  },
  
  async getSessions() {
    const res = await fetch(`${API_BASE}/api/chat/sessions`, {
      method: "GET",
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error("Failed to load conversation history");
    return res.json();
  },
  
  async getHistory(conversationId) {
    const res = await fetch(`${API_BASE}/api/chat/sessions/${conversationId}/history`, {
      method: "GET",
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error("Failed to retrieve chat history details");
    return res.json();
  },
  
  async deleteSession(conversationId) {
    const res = await fetch(`${API_BASE}/api/chat/sessions/${conversationId}`, {
      method: "DELETE",
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error("Failed to delete chat session");
    return res.json();
  },
  
  // --- FEEDBACK SUBMISSION ---
  async submitFeedback(messageId, rating, comment = "") {
    const res = await fetch(`${API_BASE}/api/chat/feedback`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ message_id: messageId, rating, comment }),
    });
    if (!res.ok) throw new Error("Failed to log user feedback");
    return res.json();
  },
  
  // --- UPLOAD PIPELINE ---
  async uploadFile(file) {
    const formData = new FormData();
    formData.append("file", file);
    
    const token = localStorage.getItem("carnatic_token");
    const headers = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    
    const res = await fetch(`${API_BASE}/api/upload`, {
      method: "POST",
      headers,
      body: formData,
    });
    
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Document upload failed");
    }
    return res.json();
  },
  
  // --- TELEMETRY / ANALYTICS STATS ---
  async getStats() {
    const res = await fetch(`${API_BASE}/api/stats`, {
      method: "GET",
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error("Failed to load telemetry stats");
    return res.json();
  }
};

// --- NAMED EXPORTS FOR MODERN COMPONENTS ---
export async function createSession() {
  const res = await fetch(`${API_BASE}/api/chat/sessions`, {
    method: "POST",
    headers: getHeaders(),
  });
  if (!res.ok) throw new Error("Failed to create chat session");
  return { data: await res.json() };
}

export async function sendMessage(message, conversationId, history = []) {
  const serverHistory = history.map(h => ({
    role: h.role,
    content: h.content || h.text || ""
  }));
  
  const res = await fetch(`${API_BASE}/api/chat/query`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify({ 
      question: message, 
      session_id: conversationId, 
      history: serverHistory 
    }),
  });
  if (!res.ok) throw new Error("Failed to resolve RAG chat response");
  return { data: await res.json() };
}

export async function listSessions() {
  const res = await fetch(`${API_BASE}/api/chat/sessions`, {
    method: "GET",
    headers: getHeaders(),
  });
  if (!res.ok) throw new Error("Failed to load sessions");
  return { data: await res.json() };
}

export async function deleteSession(conversationId) {
  const res = await fetch(`${API_BASE}/api/chat/sessions/${conversationId}`, {
    method: "DELETE",
    headers: getHeaders(),
  });
  if (!res.ok) throw new Error("Failed to delete session");
  return { data: await res.json() };
}

export async function renameSession(conversationId, newTitle) {
  const res = await fetch(`${API_BASE}/api/chat/sessions/${conversationId}/rename`, {
    method: "PUT",
    headers: getHeaders(),
    body: JSON.stringify({ title: newTitle }),
  });
  if (!res.ok) throw new Error("Failed to rename session");
  return { data: await res.json() };
}

export async function pinSession(conversationId) {
  const res = await fetch(`${API_BASE}/api/chat/sessions/${conversationId}/pin`, {
    method: "PUT",
    headers: getHeaders(),
  });
  if (!res.ok) throw new Error("Failed to pin session");
  return { data: await res.json() };
}

export async function getSessionHistory(conversationId) {
  const res = await fetch(`${API_BASE}/api/chat/sessions/${conversationId}/history`, {
    method: "GET",
    headers: getHeaders(),
  });
  if (!res.ok) throw new Error("Failed to load session history");
  return { data: await res.json() };
}

export async function uploadPDF(file) {
  const formData = new FormData();
  formData.append("file", file);
  
  const token = localStorage.getItem("carnatic_token");
  const headers = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  
  const res = await fetch(`${API_BASE}/api/upload`, {
    method: "POST",
    headers: headers,
    body: formData,
  });
  
  if (!res.ok) {
    throw new Error("Failed to upload document");
  }
  return { data: await res.json() };
}

export async function checkHealth() {
  const res = await fetch(`${API_BASE}/api/health`, {
    method: "GET",
  });
  if (!res.ok) throw new Error("Health check failed");
  return res.json();
}
