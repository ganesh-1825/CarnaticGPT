import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import Loader from '../components/Loader';
import { BarChart3, Database, ThumbsUp, Activity, Timer, TrendingUp } from 'lucide-react';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    let isMounted = true;
    api.getStats().then(data => {
      if (isMounted) {
        setStats(data);
        setLoading(false);
      }
    }).catch(e => {
      console.error(e);
      if (isMounted) setLoading(false);
    });
    return () => { isMounted = false; };
  }, []);
  
  if (loading) return <Loader message="Compiling RAG telemetry reports..." />;
  if (!stats) return <div style={{ padding: '40px', textAlign: 'center' }}>Failed to load analytics metrics.</div>;
  
  return (
    <div className="page-viewport animate-fade-in" style={{ paddingBottom: '60px' }}>
      {/* Page Title */}
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{ fontSize: '2rem', fontWeight: 800, marginBottom: '6px' }}>Analytics & Telemetry</h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
          Monitoring real-time search latencies, database indexing capacity, and user feedback ratings.
        </p>
      </div>
      
      {/* Status Deck Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '20px',
        marginBottom: '40px'
      }}>
        {/* Total Queries */}
        <div className="glass-card" style={{ padding: '24px', display: 'flex', alignItems: 'center', gap: '20px' }}>
          <div style={{
            background: 'rgba(182, 85, 255, 0.1)',
            padding: '12px',
            borderRadius: 'var(--border-radius-md)',
            color: 'hsl(var(--accent-glow))'
          }}>
            <Activity size={24} />
          </div>
          <div>
            <span style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
              TOTAL QUERIES
            </span>
            <span style={{ fontSize: '1.75rem', fontWeight: 800 }}>{stats.total_queries}</span>
          </div>
        </div>
        
        {/* Latency */}
        <div className="glass-card" style={{ padding: '24px', display: 'flex', alignItems: 'center', gap: '20px' }}>
          <div style={{
            background: 'rgba(22, 219, 204, 0.1)',
            padding: '12px',
            borderRadius: 'var(--border-radius-md)',
            color: 'hsl(var(--accent-teal))'
          }}>
            <Timer size={24} />
          </div>
          <div>
            <span style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
              AVG LATENCY
            </span>
            <span style={{ fontSize: '1.75rem', fontWeight: 800 }}>{stats.avg_latency_ms} ms</span>
          </div>
        </div>
        
        {/* Total Chunks */}
        <div className="glass-card" style={{ padding: '24px', display: 'flex', alignItems: 'center', gap: '20px' }}>
          <div style={{
            background: 'rgba(255, 179, 0, 0.1)',
            padding: '12px',
            borderRadius: 'var(--border-radius-md)',
            color: 'hsl(var(--accent-gold))'
          }}>
            <Database size={24} />
          </div>
          <div>
            <span style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
              INDEXED CHUNKS
            </span>
            <span style={{ fontSize: '1.75rem', fontWeight: 800 }}>{stats.total_chunks}</span>
          </div>
        </div>
        
        {/* Feedback Ratio */}
        <div className="glass-card" style={{ padding: '24px', display: 'flex', alignItems: 'center', gap: '20px' }}>
          <div style={{
            background: 'rgba(22, 219, 204, 0.1)',
            padding: '12px',
            borderRadius: 'var(--border-radius-md)',
            color: 'hsl(var(--accent-teal))'
          }}>
            <ThumbsUp size={24} />
          </div>
          <div>
            <span style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
              USER UPVOTES
            </span>
            <span style={{ fontSize: '1.75rem', fontWeight: 800 }}>
              {stats.upvotes} <span style={{ fontSize: '0.85rem', color: 'hsl(var(--text-muted))', fontWeight: 400 }}>/{stats.upvotes + stats.downvotes}</span>
            </span>
          </div>
        </div>
      </div>
      
      {/* Visualization graphs */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(440px, 1fr))',
        gap: '24px'
      }}>
        {/* Search volume chart */}
        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '24px' }}>
            <TrendingUp size={18} color="hsl(var(--accent-glow))" />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Query Volume Ingests (Past 5 Days)</h3>
          </div>
          
          {/* Custom interactive CSS graph */}
          <div style={{
            display: 'flex',
            alignItems: 'flex-end',
            justifyContent: 'space-between',
            height: '200px',
            paddingTop: '20px',
            borderBottom: '1px solid var(--glass-border)'
          }}>
            {stats.usage_trend.map((day, idx) => {
              const maxVal = Math.max(...stats.usage_trend.map(d => d.queries));
              const heightPct = (day.queries / maxVal) * 160; // Max 160px
              return (
                <div key={idx} style={{
                  flex: 1,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  <span style={{ fontSize: '0.75rem', color: 'hsl(var(--accent-teal))', fontWeight: 700 }}>
                    {day.queries}
                  </span>
                  <div style={{
                    width: '32px',
                    height: `${heightPct}px`,
                    background: 'linear-gradient(to top, hsl(var(--accent-royal)), hsl(var(--accent-glow)))',
                    borderRadius: '4px 4px 0 0',
                    boxShadow: 'var(--neon-shadow)',
                    transition: 'all 0.4s ease'
                  }} />
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                    {day.date}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
        
        {/* Ragas frequency distribution */}
        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '24px' }}>
            <BarChart3 size={18} color="hsl(var(--accent-teal))" />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Most Queried Carnatic Ragas</h3>
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {Object.entries(stats.raga_distribution).map(([raga, count]) => {
              const maxCount = Math.max(...Object.values(stats.raga_distribution));
              const widthPct = (count / maxCount) * 100;
              return (
                <div key={raga} style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                    <span style={{ fontWeight: 600 }}>Raga {raga}</span>
                    <span style={{ color: 'hsl(var(--accent-teal))', fontWeight: 700 }}>{count} queries</span>
                  </div>
                  <div style={{
                    height: '8px',
                    background: 'rgba(255, 255, 255, 0.05)',
                    borderRadius: '4px',
                    overflow: 'hidden'
                  }}>
                    <div style={{
                      width: `${widthPct}%`,
                      height: '100%',
                      background: 'linear-gradient(to right, hsl(var(--accent-teal)), hsl(var(--accent-glow)))',
                      borderRadius: '4px',
                      boxShadow: '0 0 8px rgba(22, 219, 204, 0.3)'
                    }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
