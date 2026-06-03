import React, { useState, useRef, useCallback } from 'react'
import { uploadPDF } from '../services/api'
import ProgressTracker from '../components/ProgressTracker'
import { UploadCloud, FileText, File, AlertCircle, CheckCircle2 } from 'lucide-react'

const STEPS = [
  { label:'Receiving document…' },
  { label:'Extracting text from PDF…' },
  { label:'Running OCR (if scanned)…' },
  { label:'Cleaning and normalising text…' },
  { label:'Creating semantic chunks…' },
  { label:'Generating embeddings…' },
  { label:'Updating FAISS vector database…' },
  { label:'Document indexed!' },
]

const sleep = ms => new Promise(r => setTimeout(r, ms))

export default function UploadPage({ onDone }) {
  const [file,   setFile]   = useState(null)
  const [drag,   setDrag]   = useState(false)
  const [status, setStatus] = useState('idle')   // idle|running|done|error
  const [steps,  setSteps]  = useState(STEPS.map(s=>({...s,status:'pending'})))
  const [error,  setError]  = useState(null)
  const [result, setResult] = useState(null)
  const inputRef = useRef(null)

  const pick = f => {
    if (!f) return
    const ext = f.name.split('.').pop().toLowerCase()
    if (!['pdf','txt'].includes(ext)) { setError('Only PDF and TXT files accepted.'); return }
    if (f.size > 150*1024*1024) { setError('File too large — max 150 MB.'); return }
    setError(null); setFile(f)
  }

  const onDrop = useCallback(e => {
    e.preventDefault(); setDrag(false); pick(e.dataTransfer.files[0])
  }, [])

  const setStep = (i, s) => setSteps(p => p.map((x,j) => j===i ? {...x,status:s} : x))
  const allDone = ()     => setSteps(p => p.map(x => ({...x,status:'done'})))

  const animateSteps = async (totalMs) => {
    const each = totalMs / (STEPS.length - 1)
    for (let i = 0; i < STEPS.length - 1; i++) {
      setStep(i,'active')
      await sleep(each)
      setStep(i,'done')
    }
  }

  const upload = async () => {
    if (!file || status==='running') return
    setStatus('running'); setError(null)
    setSteps(STEPS.map(s=>({...s,status:'pending'})))

    const anim = animateSteps(3800)
    try {
      const r = await uploadPDF(file)
      await anim
      if (r.data.success) {
        allDone(); setStep(STEPS.length-1,'done')
        setResult(r.data); setStatus('done')
        setTimeout(() => onDone?.(), 2000)
      } else { throw new Error(r.data.message || 'Upload failed') }
    } catch(e) {
      await anim.catch(()=>{})
      setError(e.message); setStatus('error')
      setSteps(p => p.map(s => s.status==='active' ? {...s,status:'error'} : s))
    }
  }

  const reset = () => {
    setFile(null); setStatus('idle'); setError(null); setResult(null)
    setSteps(STEPS.map(s=>({...s,status:'pending'})))
  }

  return (
    <div className="animate-fade-in" style={{
      flex:1, overflow:'auto', padding:'40px 32px',
      display:'flex', flexDirection:'column', alignItems: 'center', position: 'relative'
    }}>
      {/* Background Motif */}
      <div style={{ position: 'fixed', bottom: -50, right: -50, fontSize: 300, opacity: 0.015, color: 'var(--peacock)', pointerEvents: 'none', zIndex: 0 }}>
        📤
      </div>

      <div style={{ width: '100%', maxWidth: 680, position: 'relative', zIndex: 1 }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 48 }}>
          <div style={{ width: 80, height: 80, borderRadius: '50%', background: 'rgba(139, 74, 54, 0.08)', color: 'var(--peacock)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 24px' }}>
             <UploadCloud size={36} />
          </div>
          <h2 style={{ fontSize: '2.5rem', fontWeight: 700, marginBottom: 12, fontFamily: 'var(--font-serif)', color: 'var(--peacock)' }}>
            Ingest Knowledge
          </h2>
          <p style={{ fontSize: '1.15rem', color: 'var(--text-secondary)', fontFamily: 'var(--font-serif)', fontStyle: 'italic', maxWidth: 480, margin: '0 auto' }}>
            Upload PDFs or text files to expand the Digital Gurukul's intelligence.
          </p>
        </div>

        {/* Card */}
        <div className="elevated-card" style={{ padding: '40px', background: '#FFFFFF', border: '1px solid var(--border)', borderRadius: '20px' }}>
          {status === 'idle' && (
            <div>
              {/* Drop zone */}
              <div
                onClick={() => inputRef.current?.click()}
                onDrop={onDrop}
                onDragOver={e => { e.preventDefault(); setDrag(true) }}
                onDragLeave={() => setDrag(false)}
                style={{
                  border: `2px dashed ${drag ? 'var(--peacock)' : file ? 'var(--peacock)' : 'var(--border-strong)'}`,
                  borderRadius: '16px', padding: '60px 24px', textAlign: 'center',
                  cursor: 'pointer',
                  background: drag ? 'rgba(139, 74, 54, 0.05)' : file ? 'rgba(139, 74, 54, 0.02)' : 'var(--bg-app)',
                  transition: 'all var(--transition)',
                }}
              >
                <input ref={inputRef} type="file" accept=".pdf,.txt"
                  style={{display:'none'}} onChange={e=>pick(e.target.files[0])}/>
                
                <div style={{
                  width: 72, height: 72, borderRadius: '50%', margin: '0 auto 24px',
                  background: file ? 'rgba(139, 74, 54, 0.08)' : '#FFFFFF',
                  color: file ? 'var(--peacock)' : 'var(--text-muted)',
                  border: file ? 'none' : '1px solid var(--border)',
                  boxShadow: file ? 'none' : 'var(--shadow-sm)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  transition: 'all var(--transition)'
                }}>
                  {file ? <FileText size={30} /> : <File size={30} />}
                </div>
                {file ? (
                  <>
                    <p style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8, fontFamily: 'var(--font-serif)' }}>{file.name}</p>
                    <p style={{ fontSize: 14, color: 'var(--text-muted)', fontWeight: 500 }}>{(file.size/1024/1024).toFixed(2)} MB • Click to replace</p>
                  </>
                ) : (
                  <>
                    <p style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8, fontFamily: 'var(--font-serif)' }}>
                      Drag & Drop your files here
                    </p>
                    <p style={{ fontSize: 14, color: 'var(--text-muted)', fontWeight: 500 }}>Click to browse • Max 150 MB</p>
                  </>
                )}
              </div>

              {/* Error */}
              {error && (
                <div style={{
                  marginTop: 24, padding: '16px 20px', borderRadius: 'var(--radius-md)',
                  background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)',
                  display: 'flex', gap: 12, alignItems: 'center',
                }}>
                  <AlertCircle color="#EF4444" size={20} />
                  <p style={{fontSize: 14, color: '#EF4444', fontFamily: 'var(--font-sans)', fontWeight: 700}}>{error}</p>
                </div>
              )}

              {file && (
                <div style={{ marginTop: 32, display: 'flex', gap: 16 }}>
                  <button onClick={reset} className="btn-secondary" style={{ flex: 1 }}>Clear</button>
                  <button onClick={upload} className="btn-primary" style={{ flex: 2 }}>
                    Index Document
                  </button>
                </div>
              )}
            </div>
          )}

          {(status==='running'||status==='done'||status==='error') && (
            <div>
              {status==='running' && (
                <div style={{ textAlign: 'center', marginBottom: 40 }}>
                  <p style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 8, fontFamily: 'var(--font-sans)' }}>
                    Reading "{file?.name}"
                  </p>
                  <p style={{ fontSize: 15, color: 'var(--text-secondary)' }}>
                    Please wait — this might take a moment for large books.
                  </p>
                </div>
              )}

              {status==='done' && result && (
                <div style={{
                  textAlign: 'center', marginBottom: 40, padding: '32px',
                  borderRadius: 'var(--radius-lg)', background: 'rgba(16, 185, 129, 0.1)',
                  border: '1px solid rgba(16, 185, 129, 0.2)',
                }}>
                  <CheckCircle2 size={48} color="var(--emerald)" style={{ margin: '0 auto 16px' }} />
                  <p style={{ fontSize: 24, fontWeight: 800, color: 'var(--emerald)', marginBottom: 16, fontFamily: 'var(--font-sans)' }}>
                    Successfully Indexed!
                  </p>
                  <div style={{ display: 'inline-flex', gap: 24, background: 'var(--bg-surface)', padding: '12px 24px', borderRadius: 'var(--radius-full)', boxShadow: 'var(--shadow-sm)' }}>
                     <div>
                       <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)' }}>{result.chunks_added}</div>
                       <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700, letterSpacing: '0.5px' }}>Chunks</div>
                     </div>
                     <div style={{ width: 1, background: 'var(--border)' }} />
                     <div>
                       <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)' }}>{result.pages_processed}</div>
                       <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700, letterSpacing: '0.5px' }}>Pages</div>
                     </div>
                  </div>
                </div>
              )}

              {status==='error' && (
                <div style={{
                  marginBottom: 32, padding: '20px', borderRadius: 'var(--radius-md)',
                  background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)',
                  display: 'flex', gap: 16, alignItems: 'flex-start',
                }}>
                  <AlertCircle color="#EF4444" size={24} style={{ flexShrink: 0 }} />
                  <div>
                    <p style={{fontSize: 16, fontWeight: 800, color: '#EF4444', marginBottom: 4}}>Indexing Failed</p>
                    <p style={{fontSize: 14, color: '#EF4444'}}>{error}</p>
                  </div>
                </div>
              )}

              <ProgressTracker steps={steps}/>

              {status==='error' && (
                <button onClick={reset} className="btn-secondary" style={{ marginTop: 32, width: '100%' }}>
                  Try Again
                </button>
              )}
            </div>
          )}
        </div>

        <p style={{ marginTop: 32, fontSize: 14, color: 'var(--text-muted)', textAlign: 'center', fontWeight: 600 }}>
          Supported: PDF • TXT • Multi-page books • Scanned PDFs (auto-OCR)
        </p>
      </div>
    </div>
  )
}
