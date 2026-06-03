import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Eye, EyeOff, AlertCircle, Loader } from 'lucide-react';
import './auth.css';

export default function SignupPage() {
  const navigate = useNavigate();
  const { register } = useAuth();
  
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    full_name: '',
    password: '',
    confirm_password: ''
  });
  
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [terms, setTerms] = useState(false);

  const handleChange = (e) => {
    setFormData({...formData, [e.target.name]: e.target.value});
  };

  const getPwdStrength = (pwd) => {
    let score = 0;
    if (pwd.length > 5) score += 1;
    if (pwd.length > 8) score += 1;
    if (/[A-Z]/.test(pwd)) score += 1;
    if (/[0-9]/.test(pwd)) score += 1;
    if (/[^A-Za-z0-9]/.test(pwd)) score += 1;
    return score;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    if (formData.password !== formData.confirm_password) {
      return setError('Passwords do not match');
    }
    if (!terms) {
      return setError('You must accept the terms and conditions');
    }

    setLoading(true);
    try {
      await register({
        username: formData.username,
        email: formData.email,
        full_name: formData.full_name,
        password: formData.password
      });
      // After success, navigate to login
      navigate('/login');
    } catch (err) {
      setError(err.message || 'Failed to create account');
    } finally {
      setLoading(false);
    }
  };

  const strength = getPwdStrength(formData.password);
  const strengthClass = strength < 2 ? 'pwd-weak' : strength < 4 ? 'pwd-medium' : 'pwd-strong';
  const strengthText = strength === 0 ? '' : strength < 2 ? 'Weak' : strength < 4 ? 'Medium' : 'Strong';

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

      <div className="auth-card" style={{ maxWidth: 540 }}>
        <div className="auth-header">
          <h1 className="auth-title">Create Account</h1>
          <p className="auth-subtitle">Join the CarnaticGPT community</p>
        </div>

        {error && (
          <div className="auth-error">
            <AlertCircle size={16} />
            {error}
          </div>
        )}

        <form className="auth-form" onSubmit={handleSubmit}>
          
          <div style={{display:'flex', gap:'16px'}}>
            <div className="auth-input-group" style={{flex: 1}}>
              <label className="auth-label">Full Name</label>
              <input 
                type="text" name="full_name" className="auth-input" 
                value={formData.full_name} onChange={handleChange}
                placeholder="Name" required 
              />
            </div>
            <div className="auth-input-group" style={{flex: 1}}>
              <label className="auth-label">Username</label>
              <input 
                type="text" name="username" className="auth-input" 
                value={formData.username} onChange={handleChange}
                placeholder="Username" required 
              />
            </div>
          </div>

          <div className="auth-input-group">
            <label className="auth-label">Email</label>
            <input 
              type="email" name="email" className="auth-input" 
              value={formData.email} onChange={handleChange}
              placeholder="Enter your email" required 
            />
          </div>

          <div className="auth-input-group">
            <label className="auth-label">Password</label>
            <div className="auth-password-wrapper">
              <input 
                type={showPassword ? "text" : "password"} name="password"
                className="auth-input pwd-input" 
                value={formData.password} onChange={handleChange}
                placeholder="Create a strong password" required 
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
            {formData.password && (
              <>
                <div className="pwd-strength">
                  <div className={`pwd-strength-bar ${strength >= 1 ? strengthClass : ''}`} />
                  <div className={`pwd-strength-bar ${strength >= 2 ? strengthClass : ''}`} />
                  <div className={`pwd-strength-bar ${strength >= 3 ? strengthClass : ''}`} />
                  <div className={`pwd-strength-bar ${strength >= 4 ? strengthClass : ''}`} />
                </div>
                <div className="pwd-text" style={{color: strength < 2 ? '#EA4335' : strength < 4 ? '#f5a623' : '#34A853'}}>
                  {strengthText}
                </div>
              </>
            )}
          </div>

          <div className="auth-input-group">
            <label className="auth-label">Confirm Password</label>
            <input 
              type={showPassword ? "text" : "password"} name="confirm_password"
              className="auth-input" 
              value={formData.confirm_password} onChange={handleChange}
              placeholder="Confirm your password" required 
            />
          </div>

          <div className="auth-options">
            <label className="auth-checkbox">
              <input type="checkbox" checked={terms} onChange={e=>setTerms(e.target.checked)} /> 
              <span>I accept the Terms and Conditions</span>
            </label>
          </div>

          <button type="submit" className="auth-button primary-btn" disabled={loading}>
            {loading ? <Loader className="animate-spin" size={18} /> : 'Create Account'}
          </button>
        </form>

        <div className="auth-footer">
          Already have an account? <Link to="/login" className="auth-link font-semibold">Login here</Link>
        </div>
      </div>
    </div>
  );
}
