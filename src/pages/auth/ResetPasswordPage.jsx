import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { Eye, EyeOff, AlertCircle, Loader, CheckCircle } from 'lucide-react';
import './auth.css';

export default function ResetPasswordPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [token, setToken] = useState('');
  
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const t = params.get('token');
    if (t) setToken(t);
    else setError("Invalid or missing reset token.");
  }, [location]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    if (password !== confirmPassword) {
      return setError('Passwords do not match');
    }
    if (password.length < 4) {
      return setError('Password is too short');
    }

    setLoading(true);
    try {
      const res = await fetch('/api/auth/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, new_password: password })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to reset password");
      
      setSuccess(true);
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
          <h1 className="auth-title">Set New Password</h1>
          <p className="auth-subtitle">Secure your CarnaticGPT account</p>
        </div>

        {error && (
          <div className="auth-error">
            <AlertCircle size={16} />
            {error}
          </div>
        )}

        {success ? (
          <div style={{textAlign: 'center'}}>
            <div style={{color: '#8B4A36', display: 'flex', justifyContent: 'center', marginBottom: 16}}>
              <CheckCircle size={48} />
            </div>
            <p style={{color: 'var(--auth-text-main)', marginBottom: 24}}>Password successfully updated!</p>
            <button onClick={() => navigate('/login')} className="auth-button primary-btn" style={{width: '100%'}}>
              Login Now
            </button>
          </div>
        ) : (
          <form className="auth-form" onSubmit={handleSubmit}>
            <div className="auth-input-group">
              <label className="auth-label">New Password</label>
              <div className="auth-password-wrapper">
                <input 
                  type={showPassword ? "text" : "password"}
                  className="auth-input pwd-input" 
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter new password"
                  disabled={!token}
                  required 
                />
                <button 
                  type="button"
                  tabIndex="-1"
                  className="auth-input-icon-btn" 
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <div className="auth-input-group">
              <label className="auth-label">Confirm New Password</label>
              <input 
                type={showPassword ? "text" : "password"}
                className="auth-input" 
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirm new password"
                disabled={!token}
                required 
              />
            </div>

            <button type="submit" className="auth-button primary-btn" disabled={loading || !token}>
              {loading ? <Loader className="animate-spin" size={18} /> : 'Update Password'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
