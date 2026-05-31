import React, { useState } from 'react';
import { api } from '../services/api';
import { Music, Eye, EyeOff, AlertCircle } from 'lucide-react';

export default function Login({ onLoginSuccess }) {
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPass, setShowPass] = useState(false);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) return;
    setLoading(true);
    setError(null);
    
    try {
      if (isRegister) {
        await api.register(username, password);
        // Direct auto-login after successful registration
        const authData = await api.login(username, password);
        onLoginSuccess(authData);
      } else {
        const authData = await api.login(username, password);
        onLoginSuccess(authData);
      }
    } catch (err) {
      setError(err.message || "Authentication portal error");
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div style={{
      width: '100vw',
      height: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'radial-gradient(circle at 10% 20%, rgba(88, 30, 168, 0.25) 0%, transparent 40%), radial-gradient(circle at 90% 90%, rgba(22, 190, 180, 0.15) 0%, transparent 40%), hsl(var(--bg-base))'
    }}>
      <div className="glass-card animate-fade-in" style={{
        width: '100%',
        maxWidth: '400px',
        padding: '40px 30px',
        boxShadow: 'var(--neon-shadow)'
      }}>
        {/* Brand Header */}
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div style={{
            background: 'linear-gradient(135deg, hsl(var(--accent-royal)) 0%, hsl(var(--accent-glow)) 100%)',
            width: '48px',
            height: '48px',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 16px',
            boxShadow: 'var(--neon-shadow)'
          }}>
            <Music size={24} color="#fff" />
          </div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800 }}>
            {isRegister ? "Join CarnaticGPT" : "Welcome to CarnaticGPT"}
          </h2>
          <p style={{ color: 'hsl(var(--text-secondary))', fontSize: '0.85rem', marginTop: '6px' }}>
            {isRegister ? "Create credentials to explore RAG archives" : "Log in to research ragas and composers"}
          </p>
        </div>
        
        {/* Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ fontSize: '0.8rem', color: 'hsl(var(--text-secondary))', fontWeight: 500 }}>Username</label>
            <input
              type="text"
              className="form-input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. Purandara108"
              required
            />
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', position: 'relative' }}>
            <label style={{ fontSize: '0.8rem', color: 'hsl(var(--text-secondary))', fontWeight: 500 }}>Password</label>
            <input
              type={showPass ? "text" : "password"}
              className="form-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
            <button 
              type="button" 
              onClick={() => setShowPass(!showPass)}
              style={{
                position: 'absolute',
                right: '12px',
                bottom: '12px',
                background: 'none',
                border: 'none',
                color: 'hsl(var(--text-secondary))',
                cursor: 'pointer'
              }}
            >
              {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
          
          {/* Error Alert */}
          {error && (
            <div style={{
              background: 'rgba(255, 0, 0, 0.05)',
              border: '1px solid rgba(255, 0, 0, 0.1)',
              borderRadius: 'var(--border-radius-md)',
              padding: '12px',
              color: 'red',
              fontSize: '0.8rem',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <AlertCircle size={16} /> {error}
            </div>
          )}
          
          <button type="submit" className="btn-primary" disabled={loading} style={{ justifyContent: 'center', marginTop: '10px' }}>
            {loading ? "Authenticating..." : isRegister ? "Create Account" : "Access Library"}
          </button>
        </form>
        
        {/* Toggle */}
        <div style={{ textAlign: 'center', marginTop: '24px', fontSize: '0.85rem' }}>
          <span style={{ color: 'hsl(var(--text-secondary))' }}>
            {isRegister ? "Already registered?" : "New to CarnaticGPT?"}
          </span>
          <button 
            onClick={() => { setIsRegister(!isRegister); setError(null); }}
            style={{
              background: 'none',
              border: 'none',
              color: 'hsl(var(--accent-teal))',
              fontWeight: 600,
              marginLeft: '6px',
              cursor: 'pointer'
            }}
          >
            {isRegister ? "Log in here" : "Sign up here"}
          </button>
        </div>
      </div>
    </div>
  );
}
