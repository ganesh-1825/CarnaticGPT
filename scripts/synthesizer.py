"""
synthesizer.py  —  FINAL FIX
=============================
Problem:  synthesis_method always "rule_based" because:
          - FT_MODEL_PATH env var is empty
          - model never loaded at startup
          - falls through to rule_based every single call

Fix:
  1. Auto-detects fine-tuned model from common paths at import time
  2. Loads model ONCE at module level (not per-request)
  3. Uses fine-tuned model as primary generator
  4. Smart fallback only if model truly unavailable
  5. Rule-based fallback actually generates clean answers (not raw text)

Drop into:  scripts/synthesizer.py
        OR  backend/services/synthesizer.py
"""

import os
import re
import logging
from pathlib import Path

log = logging.getLogger("synthesizer")

# ═══════════════════════════════════════════════════════════════════════════════
# AUTO-DETECT FINE-TUNED MODEL PATH
# ═══════════════════════════════════════════════════════════════════════════════

def _find_model_path() -> str:
    """
    Look for fine-tuned model in common locations.
    Returns empty string if not found.
    """
    # 1. Explicit env var (highest priority)
    env = os.getenv("FT_MODEL_PATH", "").strip()
    if env and Path(env).exists():
        return env

    # 2. Common project paths (relative to project root)
    _root = Path(__file__).resolve().parent
    while _root.name in ("services", "backend", "scripts"):
        _root = _root.parent

    candidates = [
        _root / "models" / "fine_tuned_model",
        _root / "models" / "carnatic_model",
        _root / "models" / "output",
        _root / "fine_tuned_model",
        _root / "output" / "fine_tuned_model",
        Path("models/fine_tuned_model"),
        Path("models/carnatic_model"),
        Path("fine_tuned_model"),
    ]

    for p in candidates:
        # A valid HuggingFace model dir contains config.json
        if p.exists() and (p / "config.json").exists():
            log.info("Auto-detected fine-tuned model at: %s", p)
            return str(p)

    return ""

_FT_MODEL_PATH = _find_model_path()
_OLLAMA_URL    = os.getenv("OLLAMA_URL",   "http://localhost:11434/api/generate")
_OLLAMA_MODEL  = os.getenv("OLLAMA_MODEL", "phi3:mini")
_HF_MODEL      = os.getenv("HF_MODEL",    "microsoft/phi-3-mini-4k-instruct")
_LLM_MODE      = os.getenv("LLM_MODE",    "auto").lower()  # auto|ft|ollama|hf|rule

# ═══════════════════════════════════════════════════════════════════════════════
# LOAD FINE-TUNED MODEL ONCE AT STARTUP
# ═══════════════════════════════════════════════════════════════════════════════

_ft_model     = None
_ft_tokenizer = None
_ft_loaded    = False   # True = attempted (may still be None if failed)


def _load_ft_model():
    """Load fine-tuned model into module-level globals. Called once."""
    global _ft_model, _ft_tokenizer, _ft_loaded
    if _ft_loaded:
        return
    _ft_loaded = True

    if not _FT_MODEL_PATH:
        log.warning(
            "Fine-tuned model not found. "
            "Set FT_MODEL_PATH env var to your model directory. "
            "Checked: models/fine_tuned_model, models/carnatic_model, fine_tuned_model"
        )
        return

    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM

        log.info("Loading fine-tuned model from: %s", _FT_MODEL_PATH)
        _ft_tokenizer = AutoTokenizer.from_pretrained(
            _FT_MODEL_PATH, trust_remote_code=True
        )
        if _ft_tokenizer.pad_token is None:
            _ft_tokenizer.pad_token = _ft_tokenizer.eos_token

        # Try GPU first, fall back to CPU
        device = "cuda" if torch.cuda.is_available() else "cpu"
        dtype  = torch.float16 if device == "cuda" else torch.float32

        _ft_model = AutoModelForCausalLM.from_pretrained(
            _FT_MODEL_PATH,
            torch_dtype=dtype,
            device_map="auto" if device == "cuda" else None,
            trust_remote_code=True,
            low_cpu_mem_usage=True,
        )
        if device == "cpu":
            _ft_model = _ft_model.to("cpu")

        _ft_model.eval()
        log.info("Fine-tuned model loaded successfully on %s", device.upper())

    except Exception as e:
        log.error("Failed to load fine-tuned model: %s", e)
        log.error("Will use fallback synthesizer instead.")
        _ft_model     = None
        _ft_tokenizer = None


# Load immediately when module is imported
if _LLM_MODE not in ("rule", "ollama", "hf"):
    _load_ft_model()


# ═══════════════════════════════════════════════════════════════════════════════
# PROMPT TEMPLATE (matches training format)
# ═══════════════════════════════════════════════════════════════════════════════

def _build_prompt(query: str, chunks: list[dict]) -> str:
    parts = []
    for i, c in enumerate(chunks[:5], 1):
        m    = c.get("metadata") or {}
        book = m.get("book_name") or m.get("source", "Carnatic Music Book")
        page = m.get("page_number", "?")
        text = (c.get("text") or c.get("content") or "").strip()
        parts.append(f"[Source {i} | {book} | Page {page}]\n{text}")

    context = "\n\n---\n\n".join(parts)

    # Alpaca-style instruction format (matches fine-tuning format)
    return (
        "### Instruction:\n"
        "You are CarnaticGPT, an expert Carnatic classical music assistant. "
        "Answer ONLY from the provided context. "
        "Do not invent ragas, composers, or facts not in the context. "
        "Write a clear, concise answer in 3-6 sentences. "
        "Cite the source number inline.\n\n"
        f"### Context:\n{context}\n\n"
        f"### Question:\n{query}\n\n"
        "### Answer:\n"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def synthesize(
    query: str,
    chunks: list[dict],
    use_llm: bool = True,
) -> tuple[str, str]:
    """
    Generate a natural-language answer from retrieved chunks.

    Returns (answer_string, method_string)
    method: "ft" | "ollama" | "hf" | "rule_based"
    """
    if not chunks:
        return (
            "I could not find relevant information in the uploaded books. "
            "Please upload Carnatic music books and try again.",
            "no_results",
        )

    # Normalise chunk dicts
    norm = []
    for c in chunks:
        text = (c.get("content") or c.get("text") or "").strip()
        if len(text) >= 40:
            norm.append({
                "text":     text,
                "metadata": c.get("metadata") or {},
                "score":    c.get("score", 0),
            })

    if not norm:
        return (
            "The retrieved passages were too short to produce an answer. "
            "Re-index your PDFs with OCR enabled.",
            "empty_chunks",
        )

    if not use_llm or _LLM_MODE == "rule":
        return _rule_based_summary(query, norm)

    # ── 1. Fine-tuned model (primary) ─────────────────────────────────────────
    if _LLM_MODE in ("auto", "ft") and _ft_model is not None:
        try:
            answer = _run_ft_model(query, norm)
            if _is_real_answer(answer):
                log.info("synthesis_method=ft  len=%d", len(answer))
                return answer, "ft"
            log.warning("FT model output failed quality check — falling back.")
        except Exception as e:
            log.warning("FT model inference error (%s) — falling back.", e)

    # ── 2. Ollama ─────────────────────────────────────────────────────────────
    if _LLM_MODE in ("auto", "ollama"):
        try:
            answer = _call_ollama(_build_prompt(query, norm))
            if _is_real_answer(answer):
                log.info("synthesis_method=ollama  len=%d", len(answer))
                return answer, "ollama"
        except Exception as e:
            log.debug("Ollama unavailable: %s", e)

    # ── 3. HuggingFace pipeline ───────────────────────────────────────────────
    if _LLM_MODE in ("auto", "hf"):
        try:
            answer = _call_hf(_build_prompt(query, norm))
            if _is_real_answer(answer):
                log.info("synthesis_method=hf  len=%d", len(answer))
                return answer, "hf"
        except Exception as e:
            log.debug("HF pipeline unavailable: %s", e)

    # ── 4. Smart rule-based (always works) ───────────────────────────────────
    log.info("synthesis_method=rule_based")
    return _rule_based_summary(query, norm)


# ═══════════════════════════════════════════════════════════════════════════════
# FINE-TUNED MODEL INFERENCE
# ═══════════════════════════════════════════════════════════════════════════════

def _run_ft_model(query: str, chunks: list[dict]) -> str:
    import torch
    prompt  = _build_prompt(query, chunks)
    inputs  = _ft_tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=2048,
        padding=False,
    ).to(_ft_model.device)

    with torch.no_grad():
        output_ids = _ft_model.generate(
            **inputs,
            max_new_tokens=350,
            temperature=0.1,
            do_sample=False,
            repetition_penalty=1.15,
            pad_token_id=_ft_tokenizer.eos_token_id,
            eos_token_id=_ft_tokenizer.eos_token_id,
        )

    # Decode only the newly generated tokens
    new_ids = output_ids[0][inputs["input_ids"].shape[1]:]
    answer  = _ft_tokenizer.decode(new_ids, skip_special_tokens=True).strip()

    # Strip any prompt bleed-through
    for marker in ("### Answer:", "Answer:", "ANSWER:"):
        if marker in answer:
            answer = answer.split(marker)[-1].strip()

    return answer


# ═══════════════════════════════════════════════════════════════════════════════
# OLLAMA + HF BACKENDS
# ═══════════════════════════════════════════════════════════════════════════════

_hf_pipeline_obj = None

def _call_ollama(prompt: str) -> str:
    import requests
    r = requests.post(
        _OLLAMA_URL,
        json={"model": _OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=90,
    )
    r.raise_for_status()
    return r.json().get("response", "").strip()


def _call_hf(prompt: str) -> str:
    global _hf_pipeline_obj
    if _hf_pipeline_obj is None:
        from transformers import pipeline
        model_id = _FT_MODEL_PATH or _HF_MODEL
        log.info("Loading HF pipeline: %s", model_id)
        _hf_pipeline_obj = pipeline(
            "text-generation", model=model_id,
            max_new_tokens=350, temperature=0.1,
            do_sample=False, return_full_text=False,
        )
    out = _hf_pipeline_obj(prompt)
    return out[0]["generated_text"].strip()


# ═══════════════════════════════════════════════════════════════════════════════
# QUALITY GATE
# ═══════════════════════════════════════════════════════════════════════════════

_BAD_PATTERNS = [
    r"retrieved context:",
    r"^context:\s*\[",
    r"\[llm unavailable",
    r"showing retrieved context only",
    r"^a history of indian music\b",
    r"^Retrieved Context",
]
_BAD_RE = re.compile("|".join(_BAD_PATTERNS), re.I | re.MULTILINE)

def _is_real_answer(text: str) -> bool:
    if not text or len(text.strip()) < 40:
        return False
    if _BAD_RE.search(text.strip()):
        return False
    # Must contain some alphabetical words
    if len(re.findall(r"[a-zA-Z]{3,}", text)) < 5:
        return False
    return True


# ═══════════════════════════════════════════════════════════════════════════════
# SMART RULE-BASED FALLBACK
# Produces a real answer from top chunks — never returns raw OCR
# ═══════════════════════════════════════════════════════════════════════════════

_TERM_WEIGHTS = {
    "shruti":5,"swara":5,"raga":4,"ragam":4,"tala":4,"thala":4,
    "gamaka":4,"alapana":4,"melapakarta":4,"arohana":4,"avarohana":4,
    "carnatic":3,"classical":2,"music":2,"composer":3,"tyagaraja":3,
    "dikshitar":3,"composition":2,"kriti":3,"varnam":3,"pallavi":3,
    "pitch":3,"note":3,"interval":3,"scale":3,"melody":3,"rhythm":3,
    "octave":3,"tone":3,"frequency":2,"beat":2,"tradition":2,
}

_JUNK_RE = re.compile(
    r"^\s*\d+\s*$"           # page numbers
    r"|^.{0,4}$"             # too short
    r"|(?:[^\x00-\x7F]){5,}" # long non-ASCII
    r"|\b(?:fig(?:ure)?|plate|image)\s*\d+\b",
    re.I,
)


def _sentences(text: str) -> list[str]:
    raw = re.split(r"(?<=[.!?])\s+", text.replace("\n", " "))
    out = []
    for s in raw:
        s = s.strip()
        if len(s) < 35 or _JUNK_RE.search(s):
            continue
        alpha = sum(1 for c in s if c.isalpha())
        if alpha / max(len(s), 1) < 0.45:
            continue
        out.append(s)
    return out


def _score(sent: str, qwords: set) -> float:
    lower = sent.lower()
    words = set(re.findall(r"[a-z]+", lower))
    s  = len(words & qwords) * 5.0
    for term, w in _TERM_WEIGHTS.items():
        if term in lower:
            s += w
    if re.search(r"\b(is|are|refers to|means|defined as|known as|denotes)\b", lower):
        s += 4.0
    wc = len(words)
    if wc < 6:   s -= 5.0
    if wc > 80:  s -= 2.0
    return s


def _rule_based_summary(query: str, chunks: list[dict]) -> tuple[str, str]:
    qwords = set(re.findall(r"[a-z]+", query.lower()))

    scored: list[tuple[float, str, dict]] = []
    for chunk in chunks:
        for sent in _sentences(chunk["text"]):
            scored.append((_score(sent, qwords), sent, chunk["metadata"]))

    if not scored:
        best = chunks[0]["text"][:300].strip()
        return f"{best}", "rule_based"

    scored.sort(key=lambda x: x[0], reverse=True)

    seen:  set[str]   = set()
    top:   list[tuple] = []
    for sc, sent, meta in scored:
        norm = re.sub(r"\s+", " ", sent.lower())
        if norm not in seen and sc > 0:
            seen.add(norm)
            top.append((sc, sent, meta))
        if len(top) >= 5:
            break

    if not top:
        return chunks[0]["text"][:300].strip(), "rule_based"

    # Build subject from query
    subject = _subject(query)

    # Intro: best-scoring sentence; wrap with subject if it doesn't mention it
    best_sent = top[0][1].strip()
    intro = best_sent if subject.lower() in best_sent.lower() else f"{subject}: {best_sent}"
    if not intro.endswith("."):
        intro += "."

    # Body: next 2-3 sentences
    body_parts = []
    for _, sent, _ in top[1:4]:
        clean = sent.strip().rstrip(".")
        if clean.lower() not in intro.lower():
            body_parts.append(clean)
    body = ". ".join(body_parts)
    if body:
        body += "."

    # Citations
    cites:    list[str] = []
    cite_seen: set[str] = set()
    for _, _, meta in top[:3]:
        book = meta.get("book_name") or "Book"
        page = meta.get("page_number", "?")
        key  = f"{book}_{page}"
        if key not in cite_seen:
            cite_seen.add(key)
            cites.append(f"{book} (p.{page})")

    cite_str = ("\n\nSources: " + "; ".join(cites)) if cites else ""
    answer   = f"{intro} {body}{cite_str}".strip()
    return answer, "rule_based"


def _subject(query: str) -> str:
    q = query.strip().rstrip("?")
    for pat in [
        r"what\s+is\s+(?:a\s+|an\s+|the\s+)?(.+)",
        r"(?:explain|describe|define|tell me about)\s+(.+)",
        r"who\s+is\s+(.+)",
        r"what\s+are\s+(.+)",
    ]:
        m = re.match(pat, q, re.I)
        if m:
            return m.group(1).strip().title()
    return q.title()
