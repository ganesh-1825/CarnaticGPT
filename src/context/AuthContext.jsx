import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('carnatic_token') || null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      localStorage.setItem('carnatic_token', token);
      fetchUser(token);
    } else {
      localStorage.removeItem('carnatic_token');
      setUser(null);
      setLoading(false);
    }
  }, [token]);

  const fetchUser = async (authToken) => {
    try {
      setLoading(true);
      const res = await fetch('/api/auth/me', {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      if (!res.ok) {
        // Token is expired or invalid — auto-refresh with a guest token
        console.warn('Stored token is invalid. Auto-logging in as guest...');
        localStorage.removeItem('carnatic_token');
        const guestRes = await fetch('/api/auth/guest', { method: 'POST' });
        if (guestRes.ok) {
          const guestData = await guestRes.json();
          setToken(guestData.access_token);
          setUser({ username: guestData.username, id: guestData.user_id, full_name: 'Guest' });
        } else {
          setToken(null);
          setUser(null);
        }
        return;
      }
      const data = await res.json();
      setUser(data);
    } catch (err) {
      console.error('Auth fetch error:', err);
      setToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);

    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData
    });
    
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || "Login failed");
    }
    const data = await res.json();
    setToken(data.access_token);
    return data;
  };

  const loginAsGuest = async () => {
    const res = await fetch('/api/auth/guest', { method: 'POST' });
    if (!res.ok) throw new Error("Guest login failed");
    const data = await res.json();
    setToken(data.access_token);
    return data;
  };

  const register = async (userData) => {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData)
    });
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || "Registration failed");
    }
    return await res.json();
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('carnatic_active_session');
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, loginAsGuest, register, logout, setToken }}>
      {children}
    </AuthContext.Provider>
  );
};
