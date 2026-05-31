import React, { useState, useRef, useCallback } from 'react'
import { uploadPDF } from '../services/api'
import ProgressTracker from '../components/ProgressTracker'

const STEPS = [
  { label:'Uploading file to server…' },
  { label:'Extracting text from PDF…' },
  { label:'Running OCR (if scanned)…' },
  { label:'Cleaning and normalising text…' },
  { label:'Creating semantic chunks…' },
  { label:'Generating embeddings…' },
  { label:'Updating FAISS vector database…' },
  { label:'✓ Document indexed — ready for questions' },
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
    <div style={{
      flex:1, overflow:'auto', padding:'28px 32px',
      display:'flex', flexDirection:'column',
    }}>
      <div style={{ maxWidth:560 }}>
        {/* Header */}
        <h2 style={{ fontSize:20, fontWeight:700, marginBottom:4 }} className="grad-text">
          Ingest Documents
        </h2>
        <p style={{ fontSize:13, color:'var(--text-muted)', marginBottom:24 }}>
          Upload PDF books or research papers. They are automatically indexed into FAISS and
          immediately available for question answering.
        </p>

        {/* Card */}
        <div className="glass" style={{ borderRadius:16, overflow:'hidden' }}>
          {status === 'idle' && (
            <div style={{ padding:28 }}>
              {/* Drop zone */}
              <div
                onClick={() => inputRef.current?.click()}
                onDrop={onDrop}
                onDragOver={e => { e.preventDefault(); setDrag(true) }}
                onDragLeave={() => setDrag(false)}
                style={{
                  border:`2px dashed ${drag ? 'var(--purple)' : file ? 'var(--green)' : 'var(--border)'}`,
                  borderRadius:12, padding:'36px 24px', textAlign:'center',
                  cursor:'pointer',
                  background: drag ? 'var(--purple-pale)' : file ? 'var(--green-pale)' : 'transparent',
                  transition:'all .2s ease',
                }}
              >
                <input ref={inputRef} type="file" accept=".pdf,.txt"
                  style={{display:'none'}} onChange={e=>pick(e.target.files[0])}/>
                <div style={{
                  width:52,height:52,borderRadius:14,margin:'0 auto 14px',
                  background: file ? 'var(--green-pale)' : 'var(--purple-pale)',
                  border:`1px solid ${file ? 'rgba(16,185,129,.3)' : 'rgba(139,92,246,.3)'}`,
                  display:'flex',alignItems:'center',justifyContent:'center',fontSize:22,
                }}>
                  {file ? '📄' : '📤'}
                </div>
                {file ? (
                  <>
                    <p style={{ fontSize:14,fontWeight:600,color:'var(--text-primary)',marginBottom:4 }}>{file.name}</p>
                    <p style={{ fontSize:12,color:'var(--text-muted)' }}>{(file.size/1024/1024).toFixed(2)} MB · Click to change</p>
                  </>
                ) : (
                  <>
                    <p style={{ fontSize:14,fontWeight:500,color:'var(--text-secondary)',marginBottom:6 }}>
                      Drop PDF or TXT here
                    </p>
                    <p style={{ fontSize:12,color:'var(--text-muted)' }}>or click to browse · Max 150 MB</p>
                  </>
                )}
              </div>

              {/* Error */}
              {error && (
                <div style={{
                  marginTop:14,padding:'10px 14px',borderRadius:9,
                  background:'var(--red-pale)',border:'1px solid rgba(239,68,68,.25)',
                  display:'flex',gap:8,alignItems:'flex-start',
                }}>
                  <span style={{color:'var(--red)',fontSize:14,flexShrink:0}}>⚠</span>
                  <p style={{fontSize:12.5,color:'#f87171'}}>{error}</p>
                </div>
              )}

              {file && (
                <div style={{ marginTop:18, display:'flex', gap:10 }}>
                  <button onClick={reset} style={{
                    flex:1, padding:'10px', borderRadius:9,
                    background:'var(--bg-hover)', border:'1px solid var(--border)',
                    color:'var(--text-muted)', fontSize:13,
                  }}>Clear</button>
                  <button onClick={upload} style={{
                    flex:3, padding:'10px', borderRadius:9,
                    background:'linear-gradient(135deg,var(--purple),var(--blue))',
                    color:'white', fontSize:13, fontWeight:600,
                    boxShadow:'0 4px 16px rgba(139,92,246,.3)',
                    transition:'var(--transition)',
                  }}
                    onMouseEnter={e=>e.currentTarget.style.opacity='.9'}
                    onMouseLeave={e=>e.currentTarget.style.opacity='1'}
                  >
                    🚀 Index Document
                  </button>
                </div>
              )}
            </div>
          )}

          {(status==='running'||status==='done'||status==='error') && (
            <div style={{ padding:28 }}>
              {status==='running' && (
                <div style={{ textAlign:'center', marginBottom:22 }}>
                  <p style={{ fontSize:15,fontWeight:600,color:'var(--text-primary)',marginBottom:4 }}>
                    Processing <span className="grad-text">"{file?.name}"</span>
                  </p>
                  <p style={{ fontSize:12,color:'var(--text-muted)' }}>
                    Please wait — large PDFs may take a minute.
                  </p>
                </div>
              )}

              {status==='done' && result && (
                <div style={{
                  textAlign:'center', marginBottom:22, padding:'14px 18px',
                  borderRadius:10, background:'var(--green-pale)',
                  border:'1px solid rgba(16,185,129,.25)',
                }}>
                  <p style={{ fontSize:16,fontWeight:700,color:'var(--green)',marginBottom:4 }}>
                    ✓ Indexed Successfully
                  </p>
                  <p style={{ fontSize:12.5,color:'var(--green)' }}>
                    {result.chunks_added} chunks · {result.pages_processed} pages · Total: {result.total_indexed} vectors
                  </p>
                  <p style={{ fontSize:12,color:'var(--green)',marginTop:6,opacity:.7 }}>
                    Redirecting to chat…
                  </p>
                </div>
              )}

              {status==='error' && (
                <div style={{
                  marginBottom:18,padding:'12px 16px',borderRadius:10,
                  background:'var(--red-pale)',border:'1px solid rgba(239,68,68,.25)',
                  display:'flex',gap:10,alignItems:'flex-start',
                }}>
                  <span style={{color:'var(--red)',fontSize:18,flexShrink:0}}>✕</span>
                  <div>
                    <p style={{fontSize:13.5,fontWeight:600,color:'#f87171',marginBottom:3}}>Indexing Failed</p>
                    <p style={{fontSize:12.5,color:'#f87171'}}>{error}</p>
                  </div>
                </div>
              )}

              <ProgressTracker steps={steps}/>

              {status==='error' && (
                <button onClick={reset} style={{
                  marginTop:18,width:'100%',padding:'11px',borderRadius:9,
                  background:'linear-gradient(135deg,var(--purple),var(--blue))',
                  color:'white',fontSize:13.5,fontWeight:600,
                }}>Try Again</button>
              )}
            </div>
          )}
        </div>

        <p style={{ marginTop:14,fontSize:11.5,color:'var(--text-faint)',textAlign:'center' }}>
          Supported: PDF · TXT · Multi-page books · Scanned PDFs (auto-OCR)
        </p>
      </div>
    </div>
  )
}
