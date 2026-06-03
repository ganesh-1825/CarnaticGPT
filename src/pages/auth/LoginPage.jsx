import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Eye, EyeOff, AlertCircle, Loader } from 'lucide-react';
import './auth.css';

export default function LoginPage() {
  const navigate = useNavigate();
  const { login, loginAsGuest } = useAuth();
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [loading, setLoading] = useState(false);
  const [guestLoading, setGuestLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      // Use the email state for the username parameter expected by the auth context
      await login(email, password);
      navigate('/');
    } catch (err) {
      setError(err.message || 'Failed to sign in. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleGuest = async () => {
    setGuestLoading(true);
    try {
      await loginAsGuest();
      navigate('/');
    } catch (err) {
      setError('Guest login failed');
    } finally {
      setGuestLoading(false);
    }
  };

  const handleGoogleLogin = () => {
    // Elegant mock notification for mock sign in, or standard navigation
    alert('Google authentication integration is coming soon in CarnaticGPT production release!');
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
        {/* Large circular icon at top */}
        <div className="auth-logo-circle-container">
          <div className="auth-logo-circle">
            <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
              {/* Modern elegant abstract Tambura/Veena icon */}
              {/* Circular body (Kudam) */}
              <circle cx="50" cy="70" r="15" stroke="#8B4A36" strokeWidth="2.5" fill="#F8F7F5" />
              <circle cx="50" cy="70" r="9" stroke="#8B4A36" strokeWidth="1.5" strokeDasharray="3 2" />
              {/* Long neck (Dandi) */}
              <line x1="50" y1="20" x2="50" y2="55" stroke="#8B4A36" strokeWidth="3" strokeLinecap="round" />
              {/* Strings */}
              <line x1="48" y1="20" x2="48" y2="70" stroke="#8B4A36" strokeWidth="0.8" opacity="0.6" />
              <line x1="52" y1="20" x2="52" y2="70" stroke="#8B4A36" strokeWidth="0.8" opacity="0.6" />
              {/* Tuning pegs */}
              <circle cx="43" cy="25" r="2.5" fill="#8B4A36" />
              <circle cx="57" cy="30" r="2.5" fill="#8B4A36" />
              <path d="M48 20h4" stroke="#8B4A36" strokeWidth="2" />
              {/* Gourd resonator near top */}
              <path d="M42 35c0-4 16-4 16 0 0 4-16 4-16 0z" stroke="#8B4A36" strokeWidth="1.5" fill="#F8F7F5" />
            </svg>
          </div>
        </div>

        <div className="auth-header">
          <h1 className="auth-title">CarnaticGPT</h1>
          <p className="auth-subtitle">Experience the wisdom of Carnatic music</p>
        </div>

        {error && (
          <div className="auth-error">
            <AlertCircle size={16} />
            {error}
          </div>
        )}

        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="auth-input-group">
            <label className="auth-label">Email Address</label>
            <input 
              type="email" 
              className="auth-input" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email address"
              required 
            />
          </div>

          <div className="auth-input-group">
            <label className="auth-label">Password</label>
            <div className="auth-password-wrapper">
              <input 
                type={showPassword ? "text" : "password"}
                className="auth-input pwd-input" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
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

          <div className="auth-options">
            <label className="auth-checkbox">
              <input 
                type="checkbox" 
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
              /> 
              <span>Remember Me</span>
            </label>
            <Link to="/forgot-password" className="auth-link">Forgot Password?</Link>
          </div>

          <button type="submit" className="auth-button primary-btn" disabled={loading || guestLoading}>
            {loading ? <Loader className="animate-spin" size={18} /> : 'Sign In'}
          </button>
        </form>

        <div className="auth-separator">or</div>
        
        <div className="auth-secondary-actions">
          <button type="button" className="auth-secondary-btn" onClick={handleGoogleLogin}>
            <svg viewBox="0 0 24 24" width="18" height="18" xmlns="http://www.w3.org/2000/svg" style={{ marginRight: '8px' }}>
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" fill="#EA4335"/>
            </svg>
            Google
          </button>
          
          <button type="button" className="auth-secondary-btn" onClick={handleGuest} disabled={loading || guestLoading}>
            {guestLoading ? <Loader className="animate-spin" size={18} /> : 'Continue as Guest'}
          </button>
        </div>

        <div className="auth-footer">
          New to CarnaticGPT? <Link to="/signup" className="auth-link font-semibold">Create Account</Link>
        </div>
      </div>
    </div>
  );
}

