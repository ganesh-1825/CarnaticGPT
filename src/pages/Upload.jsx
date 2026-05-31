import React, { useState, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload, FileText, X, AlertCircle } from 'lucide-react'
import { api } from '../services/api'
import ProgressTracker from '../components/ProgressTracker'

const PIPELINE_STEPS = [
  { label: 'Uploading file to server...' },
  { label: 'Extracting text from PDF...' },
  { label: 'Running OCR if needed...' },
  { label: 'Cleaning and normalising text...' },
  { label: 'Creating semantic chunks...' },
  { label: 'Generating embeddings...' },
  { label: 'Indexing in FAISS vector database...' },
  { label: '✓ Document indexed successfully' },
]

const UploadPage = () => {
  const navigate = useNavigate()
  const fileInputRef = useRef(null)

  const [file, setFile] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const [uploadStatus, setUploadStatus] = useState('idle') // idle|uploading|done|error
  const [steps, setSteps] = useState(PIPELINE_STEPS.map(s => ({ ...s, status: 'pending' })))
  const [currentStep, setCurrentStep] = useState(-1)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  const updateStep = (index, status) => {
    setSteps(prev => prev.map((s, i) => i === index ? { ...s, status } : s))
    setCurrentStep(index)
  }

  const markAllDone = () => {
    setSteps(prev => prev.map(s => ({ ...s, status: 'done' })))
  }

  const animateSteps = async (totalMs = 3200) => {
    const stepMs = totalMs / (PIPELINE_STEPS.length - 1)
    for (let i = 0; i < PIPELINE_STEPS.length - 1; i++) {
      updateStep(i, 'active')
      await new Promise(r => setTimeout(r, stepMs))
      updateStep(i, 'done')
    }
  }

  const handleFileSelect = (selected) => {
    if (!selected) return
    const ext = selected.name.split('.').pop().toLowerCase()
    if (!['pdf', 'txt'].includes(ext)) {
      setError('Only PDF and TXT files are accepted.')
      return
    }
    if (selected.size > 100 * 1024 * 1024) {
      setError('File is too large. Maximum size is 100 MB.')
      return
    }
    setError(null)
    setFile(selected)
  }

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setDragOver(false)
    const dropped = e.dataTransfer.files[0]
    if (dropped) handleFileSelect(dropped)
  }, [])

  const handleUpload = async () => {
    if (!file) return
    setUploadStatus('uploading')
    setError(null)
    setSteps(PIPELINE_STEPS.map(s => ({ ...s, status: 'pending' })))

    // Start step animation concurrently with actual upload
    const animationPromise = animateSteps(3500)

    try {
      const res = await api.uploadFile(file)

      await animationPromise

      if (res.success || res.status === 'success') {
        markAllDone()
        updateStep(PIPELINE_STEPS.length - 1, 'done')
        
        // Map backend stats keys dynamically to support all server variations
        const chunks_added = res.chunks_added || (res.stats && res.stats.chunks) || 0
        const pages_processed = res.pages_processed || (res.stats && res.stats.pages) || 1
        
        setResult({
          ...res,
          chunks_added,
          pages_processed
        })
        setUploadStatus('done')

        // Navigate to chat after brief success display
        setTimeout(() => navigate('/chat'), 1800)
      } else {
        throw new Error(res.message || 'Upload failed')
      }
    } catch (err) {
      await animationPromise.catch(() => {})
      const msg = err.response?.data?.detail || err.message || 'Upload failed. Please try again.'
      setError(msg)
      setUploadStatus('error')
      // Mark last active step as error
      setSteps(prev => prev.map(s => s.status === 'active' ? { ...s, status: 'error' } : s))
    }
  }

  const reset = () => {
    setFile(null)
    setUploadStatus('idle')
    setSteps(PIPELINE_STEPS.map(s => ({ ...s, status: 'pending' })))
    setCurrentStep(-1)
    setError(null)
    setResult(null)
  }

  const isProcessing = uploadStatus === 'uploading'

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '40px 20px',
      background: 'radial-gradient(circle at 10% 20%, rgba(88, 30, 168, 0.15) 0%, transparent 40%), radial-gradient(circle at 80% 80%, rgba(22, 190, 180, 0.08) 0%, transparent 40%), #0b0d19',
    }}>
      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: 40 }}>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 10,
          padding: '6px 16px',
          borderRadius: 20,
          background: 'rgba(200, 146, 42, 0.12)',
          border: '1px solid rgba(200, 146, 42, 0.3)',
          marginBottom: 16,
        }}>
          <div style={{ width: 7, height: 7, borderRadius: '50%', background: 'var(--gold)' }} />
          <span style={{ fontSize: 12, color: 'var(--gold)', fontWeight: 500, letterSpacing: '0.05em' }}>
            CARNATIC MUSIC KNOWLEDGE
          </span>
        </div>
        <h1 style={{
          fontFamily: 'var(--font-display)',
          fontSize: 'clamp(28px, 5vw, 42px)',
          fontWeight: 700,
          color: '#ffffff',
          lineHeight: 1.2,
          marginBottom: 10,
        }}>
          CarnaticGPT
        </h1>
        <p style={{ fontSize: 15, color: 'rgba(255, 255, 255, 0.65)', maxWidth: 420 }}>
          Upload a book or research paper to instantly search and query its contents.
        </p>
      </div>

      {/* Card */}
      <div style={{
        width: '100%', maxWidth: 520,
        background: 'rgba(19, 27, 46, 0.85)',
        borderRadius: 20,
        border: '1px solid rgba(147, 51, 234, 0.3)',
        boxShadow: '0 12px 40px rgba(0, 0, 0, 0.5)',
        backdropFilter: 'blur(16px)',
        overflow: 'hidden',
        position: 'relative',
      }}>
        {/* Drop zone */}
        {uploadStatus === 'idle' && (
          <div style={{ padding: 28 }}>
            <div
              onClick={() => fileInputRef.current?.click()}
              onDrop={handleDrop}
              onDragOver={e => { e.preventDefault(); setDragOver(true) }}
              onDragLeave={() => setDragOver(false)}
              style={{
                border: `2px dashed ${dragOver ? 'var(--gold)' : file ? 'rgba(22, 219, 204, 0.6)' : 'rgba(255, 255, 255, 0.15)'}`,
                borderRadius: 14,
                padding: '36px 24px',
                textAlign: 'center',
                cursor: 'pointer',
                background: dragOver ? 'rgba(200, 146, 42, 0.08)' : file ? 'rgba(22, 219, 204, 0.05)' : 'rgba(255, 255, 255, 0.02)',
                transition: 'all 0.2s ease',
              }}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.txt"
                style={{ display: 'none' }}
                onChange={e => handleFileSelect(e.target.files[0])}
              />
              {file ? (
                <>
                  <div style={{
                    width: 48, height: 48, borderRadius: 12,
                    background: 'rgba(22, 219, 204, 0.12)',
                    border: '1px solid rgba(22, 219, 204, 0.3)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    margin: '0 auto 12px',
                  }}>
                    <FileText size={22} color="rgba(22, 219, 204, 1)" />
                  </div>
                  <p style={{ fontSize: 14, fontWeight: 500, color: '#ffffff', marginBottom: 4 }}>
                    {file.name}
                  </p>
                  <p style={{ fontSize: 12, color: 'rgba(255, 255, 255, 0.5)' }}>
                    {(file.size / (1024 * 1024)).toFixed(2)} MB · Click to change
                  </p>
                </>
              ) : (
                <>
                  <div style={{
                    width: 48, height: 48, borderRadius: 12,
                    background: 'rgba(200, 146, 42, 0.12)',
                    border: '1px solid rgba(200, 146, 42, 0.3)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    margin: '0 auto 14px',
                  }}>
                    <Upload size={22} color="var(--gold)" />
                  </div>
                  <p style={{ fontSize: 14, fontWeight: 500, color: '#ffffff', marginBottom: 6 }}>
                    Drop your PDF or TXT here
                  </p>
                  <p style={{ fontSize: 12, color: 'rgba(255, 255, 255, 0.5)' }}>
                    or click to browse · Max 100 MB
                  </p>
                </>
              )}
            </div>

            {error && (
              <div style={{
                marginTop: 14, padding: '10px 14px', borderRadius: 10,
                background: 'rgba(239, 68, 68, 0.12)', border: '1px solid rgba(239, 68, 68, 0.3)',
                display: 'flex', gap: 8, alignItems: 'flex-start',
              }}>
                <AlertCircle size={15} color="#ef4444" style={{ flexShrink: 0, marginTop: 1 }} />
                <p style={{ fontSize: 13, color: '#fca5a5' }}>{error}</p>
              </div>
            )}

            {file && (
              <div style={{ marginTop: 16, display: 'flex', gap: 10 }}>
                <button
                  onClick={reset}
                  style={{
                    flex: 1, padding: '11px 0', borderRadius: 10,
                    background: 'rgba(255, 255, 255, 0.05)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    fontSize: 13.5, color: '#ffffff',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
                    transition: 'all 0.2s ease',
                    cursor: 'pointer',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)'}
                >
                  <X size={14} /> Clear
                </button>
                <button
                  onClick={handleUpload}
                  style={{
                    flex: 3, padding: '11px 0', borderRadius: 10,
                    background: 'linear-gradient(135deg, hsl(var(--accent-royal)) 0%, hsl(var(--accent-glow)) 100%)',
                    color: 'white',
                    fontSize: 13.5, fontWeight: 500,
                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 7,
                    transition: 'all 0.2s ease',
                    border: 'none',
                    boxShadow: 'var(--neon-shadow)',
                    cursor: 'pointer',
                  }}
                  onMouseEnter={e => e.currentTarget.style.transform = 'translateY(-1px)'}
                  onMouseLeave={e => e.currentTarget.style.transform = 'translateY(0)'}
                >
                  <Upload size={14} /> Index Document
                </button>
              </div>
            )}
          </div>
        )}

        {/* Processing */}
        {(isProcessing || uploadStatus === 'done' || uploadStatus === 'error') && (
          <div style={{ padding: 28 }}>
            {isProcessing && (
              <div style={{ textAlign: 'center', marginBottom: 22 }}>
                <p style={{
                  fontFamily: 'var(--font-display)',
                  fontSize: 17, fontWeight: 600, color: '#ffffff',
                  marginBottom: 4,
                }}>
                  Processing "{file?.name}"
                </p>
                <p style={{ fontSize: 12.5, color: 'rgba(255, 255, 255, 0.5)' }}>
                  This may take a minute for large documents.
                </p>
              </div>
            )}

            {uploadStatus === 'done' && result && (
              <div style={{
                textAlign: 'center', marginBottom: 22,
                padding: '14px 18px', borderRadius: 12,
                background: 'rgba(20, 184, 166, 0.12)', border: '1px solid rgba(20, 184, 166, 0.3)',
              }}>
                <p style={{ fontSize: 15, fontWeight: 600, color: 'rgba(22, 219, 204, 1)', marginBottom: 4 }}>
                  ✓ Indexed Successfully
                </p>
                <p style={{ fontSize: 12.5, color: 'rgba(22, 219, 204, 0.8)' }}>
                  {result.chunks_added} chunks · {result.pages_processed} pages
                </p>
                <p style={{ fontSize: 12, color: 'rgba(22, 219, 204, 0.6)', marginTop: 4 }}>
                  Opening chat…
                </p>
              </div>
            )}

            {uploadStatus === 'error' && (
              <div style={{
                marginBottom: 18, padding: '12px 16px', borderRadius: 12,
                background: 'rgba(239, 68, 68, 0.12)', border: '1px solid rgba(239, 68, 68, 0.3)',
                display: 'flex', gap: 10, alignItems: 'flex-start',
              }}>
                <AlertCircle size={16} color="#ef4444" style={{ flexShrink: 0, marginTop: 2 }} />
                <div>
                  <p style={{ fontSize: 13.5, fontWeight: 500, color: '#fca5a5', marginBottom: 2 }}>
                    Indexing Failed
                  </p>
                  <p style={{ fontSize: 12.5, color: '#fca5a5' }}>{error}</p>
                </div>
              </div>
            )}

            <ProgressTracker steps={steps} currentStep={currentStep} />

            {uploadStatus === 'error' && (
              <button
                onClick={reset}
                style={{
                  marginTop: 18, width: '100%', padding: '11px 0',
                  borderRadius: 10, background: 'rgba(255, 255, 255, 0.08)',
                  border: '1px solid rgba(255, 255, 255, 0.15)',
                  color: 'white',
                  fontSize: 13.5, fontWeight: 500,
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                }}
                onMouseEnter={e => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.15)'}
                onMouseLeave={e => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.08)'}
              >
                Try Again
              </button>
            )}
          </div>
        )}
      </div>

      <p style={{ marginTop: 20, fontSize: 12, color: 'rgba(255, 255, 255, 0.3)', textAlign: 'center' }}>
        Supported: PDF · TXT · Multi-page books · Scanned PDFs (OCR)
      </p>
    </div>
  )
}

export default UploadPage
