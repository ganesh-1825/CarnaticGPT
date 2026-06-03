import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function ProtectedRoute({ children }) {
  const { user, token, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: 'var(--bg-app)', flexDirection: 'column', gap: 16 }}>
        <div style={{ animation: 'spin 1s linear infinite', border: '3px solid rgba(2, 132, 199, 0.2)', borderTopColor: 'var(--peacock)', borderRadius: '50%', width: 48, height: 48 }} />
        <p style={{ color: 'var(--text-secondary)', fontSize: 15, fontFamily: 'var(--font-sans)', fontWeight: 600 }}>Loading your Gurukul...</p>
      </div>
    );
  }

  // If no token at all (and not loading), redirect to login
  if (!token && !user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}
