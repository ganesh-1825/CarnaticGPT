import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { AlertCircle, Loader, CheckCircle } from 'lucide-react';
import './auth.css';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setLoading(true);
    try {
      const res = await fetch('/api/auth/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to process request");
      
      // If server returns dev_token, we can log it (for testing environments without email).
      if (data.dev_token) {
        console.log(`[TESTING] Reset link: /reset-password?token=${data.dev_token}`);
      }
      
      setMessage(data.message);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      {/* Decorative background note on left */}
      <div className="auth-bg-deco left-note">
        <svg viewBox="0 0 100 100" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
          <path d="M40 75c-6.6 0-12-5.4-12-12s5.4-12 12-12 12 5.4 12 12v-38l30-8v28c-6.6 0-12 5.4-12 12s5.4 12 12 12 12-5.4 12-12v-44l-42 11.2v50.8c0 6.6-5.4 12-12 12z"/>
        </svg>
      </div>

      {/* Decorative background swara symbol on right */}
      <div className="auth-bg-deco right-swara">
        <svg viewBox="0 0 200 200" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
          <text x="50%" y="60%" dominantBaseline="middle" textAnchor="middle" fontSize="110" fontFamily="Playfair Display, serif" fontWeight="600" fontStyle="italic">सा</text>
        </svg>
      </div>

      <div className="auth-card">
        <div className="auth-header">
          <h1 className="auth-title">Reset Password</h1>
          <p className="auth-subtitle">Enter your email to receive a reset link</p>
        </div>

        {error && (
          <div className="auth-error">
            <AlertCircle size={16} />
            {error}
          </div>
        )}

        {message ? (
          <div style={{textAlign: 'center'}}>
            <div style={{color: '#8B4A36', display: 'flex', justifyContent: 'center', marginBottom: 16}}>
              <CheckCircle size={48} />
            </div>
            <p style={{color: 'var(--auth-text-main)', marginBottom: 24}}>{message}</p>
            <Link to="/login" className="auth-button primary-btn" style={{textDecoration: 'none'}}>Return to Login</Link>
          </div>
        ) : (
          <form className="auth-form" onSubmit={handleSubmit}>
            <div className="auth-input-group">
              <label className="auth-label">Email Address</label>
              <input 
                type="email" 
                className="auth-input" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your registered email"
                required 
              />
            </div>
            
            <button type="submit" className="auth-button primary-btn" disabled={loading}>
              {loading ? <Loader className="animate-spin" size={18} /> : 'Send Reset Link'}
            </button>
            
            <div className="auth-footer" style={{marginTop: 16}}>
              Remember your password? <Link to="/login" className="auth-link">Login here</Link>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
