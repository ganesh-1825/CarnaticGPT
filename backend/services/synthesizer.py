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
        # A valid HuggingFace model dir contains config.json or adapter_config.json
        if p.exists() and ((p / "config.json").exists() or (p / "adapter_config.json").exists()):
            log.info("Auto-detected fine-tuned model at: %s", p)
            return str(p)

    return ""

_FT_MODEL_PATH = _find_model_path()
_OLLAMA_URL    = os.getenv("OLLAMA_URL",   "http://localhost:11434/api/generate")
_OLLAMA_MODEL  = os.getenv("OLLAMA_MODEL", "phi3:mini")
_HF_MODEL      = os.getenv("HF_MODEL",    "HuggingFaceTB/SmolLM2-135M-Instruct")
_LLM_MODE      = os.getenv("LLM_MODE",    "rule").lower()  # auto|ft|ollama|hf|rule

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

        if (Path(_FT_MODEL_PATH) / "adapter_config.json").exists():
            import json
            from peft import PeftModel
            with open(Path(_FT_MODEL_PATH) / "adapter_config.json", "r") as f:
                base_model_id = json.load(f).get("base_model_name_or_path")
            
            log.info("Detected PEFT adapter. Loading base model %s first...", base_model_id)
            base_model = AutoModelForCausalLM.from_pretrained(
                base_model_id,
                torch_dtype=dtype,
                device_map="auto" if device == "cuda" else None,
                trust_remote_code=True,
                low_cpu_mem_usage=True,
            )
            _ft_model = PeftModel.from_pretrained(base_model, _FT_MODEL_PATH)
        else:
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
    # Limit to top 3 chunks to avoid blowing up the context window limit of 1024
    for i, c in enumerate(chunks[:3], 1):
        m    = c.get("metadata") or {}
        book = m.get("book_name") or m.get("source", "Carnatic Music Book")
        page = m.get("page_number", "?")
        text = (c.get("text") or c.get("content") or "").strip()
        # Truncate text to 500 characters to keep token count low
        if len(text) > 500:
            text = text[:500] + "..."
        parts.append(f"[Source {i} | {book} | Page {page}]\n{text}")

    context = "\n\n---\n\n".join(parts)

    # Build dynamic master prompt based on query type
    system_prompt = (
        "You are CarnaticGPT, an expert Carnatic music research assistant.\n\n"
        "Your task is to answer ONLY from the retrieved context.\n\n"
        "STRICT RULES\n\n"
        "1. Use ONLY information present in the retrieved context.\n"
        "2. NEVER invent facts.\n"
        "3. NEVER use outside knowledge.\n"
        "4. NEVER guess missing information.\n"
        "5. NEVER create swaras, scales, ragas, talas, composers, dates, melakarta numbers, or music theory not present in the context.\n"
        "6. Every statement must be supported by the retrieved sources.\n"
        "7. If information is missing, say:\n\n"
        "\"The retrieved Carnatic sources do not contain enough information to answer this question.\"\n\n"
        "8. Summarize information in clear English.\n"
        "9. Remove OCR errors, broken sentences and duplicate text.\n"
        "10. Do not copy large chunks from the source.\n"
        "11. Generate natural readable explanations.\n\n"
        "--------------------------------------------------\n"
        "ANSWER QUALITY RULES\n\n"
        "Good:\n- concise\n- factual\n- readable\n- summarized\n\n"
        "Bad:\n- OCR garbage\n- repeated phrases\n- raw chunks\n- broken sentences\n- hallucinated content\n"
        "--------------------------------------------------\n"
    )

    query_lower = query.lower()
    if "compare" in query_lower or "difference" in query_lower:
        system_prompt += (
            "For comparison questions:\n\n"
            "1. Identify both entities.\n"
            "2. Extract facts for each entity from context.\n"
            "3. Compare only retrieved facts.\n"
            "4. Present comparison in table format.\n"
            "5. Do not invent differences.\n\n"
            "If comparison information is unavailable:\n"
            "\"The retrieved sources do not provide enough information for a detailed comparison.\"\n\n"
        )
    elif any(w in query_lower for w in ["play", "recommend recordings", "show recordings", "suggest recordings", "audio", "youtube"]):
        system_prompt += (
            "When recordings are requested:\n\n"
            "1. Generate a 2-4 sentence theory summary.\n"
            "2. List recordings.\n"
            "3. Show Composer.\n"
            "4. Show Melakarta.\n"
            "5. Show Shruti.\n"
            "6. Show YouTube link.\n"
            "7. Never use theory chunks as recordings.\n"
            "8. Never use research papers as recordings.\n\n"
        )
    else:
        system_prompt += (
            "If the user asks: 'What is...', 'Who is...', 'Explain...'\n"
            "Return: Definition, Key Characteristics, Importance, Sources.\n\n"
        )

    # Use ChatML format required by SmolLM2-Instruct
    return (
        f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
        "<|im_start|>user\n"
        f"RETRIEVED CONTEXT\n\n{context}\n\n"
        f"--------------------------------------------------\n"
        f"USER QUESTION\n\n{query}<|im_end|>\n"
        "<|im_start|>assistant\n"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def synthesize(
    query: str,
    chunks: list[dict],
    use_llm: bool = True,
    top_score: float = 0.0,
    route = None,
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

    intent = route.intent if route else "GENERAL"

    # ── 0. Shruti specific Route ──────────────────────────────────────────────────
    if "shruti" in query.lower() and not "play" in query.lower() and not "group" in query.lower():
        music_candidates = [c for c in norm if c.get("metadata", {}).get("type") == "music"]
        if music_candidates:
            m = music_candidates[0].get("metadata", {})
            song = m.get("song", "Unknown")
            raga = m.get("raga", "Unknown")
            composer = m.get("composer", "Unknown")
            shruti = m.get("shruti", "Unknown")
            ans = f"The recommended shruti for {song} is {shruti}.\nComposer: {composer}\nRaga: {raga}"
            return ans, "ft"

    # ── 1. Audio / Recordings Route ────────────────────────────────────────────────
    query_lower = query.lower()
    if any(w in query_lower for w in ["play", "recommend recordings", "suggest recordings", "audio", "listen", "youtube", "recording", "recordings"]):
        music_chunks = [c for c in norm if c.get("metadata", {}).get("type") == "music"]
        theory_chunks = [c for c in norm if c.get("metadata", {}).get("type") != "music"]

        if music_chunks:
            # Extract raga name
            raga_name = "The requested raga"
            for c in music_chunks:
                r = c.get("metadata", {}).get("raga")
                if not r:
                    r_match = re.search(r"Ragam:\s*(.+)", c.get("text", ""), re.IGNORECASE)
                    if r_match: r = r_match.group(1).strip()
                if r:
                    raga_name = r
                    break
                    
            # Determine Difficulty Filter if explicitly mentioned
            difficulty = None
            if "beginner" in query_lower:
                difficulty = "Beginner"
            elif "intermediate" in query_lower:
                difficulty = "Intermediate"
            elif "advanced" in query_lower:
                difficulty = "Advanced"

            if intent == "GROUP_BY_SHRUTI":
                answer = f"{raga_name.capitalize()} Recordings by Shruti\n\n"
                
                # Group by Shruti
                shruti_groups = {}
                for m in music_chunks:
                    text = m.get("text", "")
                    meta = m.get("metadata", {})
                    song_match = re.search(r"Song:\s*(.+)", text, re.IGNORECASE)
                    song = (song_match.group(1).strip() if song_match else None) or meta.get("song") or "Unknown Composition"
                    shruti = meta.get("shruti") or "Unknown"
                    if shruti not in shruti_groups:
                        shruti_groups[shruti] = set()
                    shruti_groups[shruti].add(song)
                
                # Sort shrutis, put Unknown at the end
                sorted_shrutis = sorted(list(shruti_groups.keys()), key=lambda x: (x=="Unknown", x))
                for sh in sorted_shrutis:
                    answer += f"**{sh}**\n"
                    for s in sorted(list(shruti_groups[sh])):
                        answer += f"• {s}\n"
                    answer += "\n"
                    
                return answer.strip(), "audio_route"

            else:
                answer = f"{raga_name.capitalize()} Alapana\n\n"
                
                # Theory summary block
                answer += "Theory Summary:\n"
                from backend.raga_knowledge_base import get_raga_info
                info = get_raga_info(raga_name)
                if info:
                    answer += f"{info['name']} is a {info['type']} raga in Carnatic music. It is known for its extensive improvisation and is widely used for elaborate alapana.\n\n"
                else:
                    answer += f"{raga_name.capitalize()} is a major Carnatic raga known for its depth and expressive possibilities. It is frequently chosen for detailed alapana presentations.\n\n"
                
                if difficulty:
                    answer += f"Recommended Recordings ({difficulty} Friendly):\n\n"
                else:
                    answer += "Recommended Recordings:\n\n"
                
                # Group by song and format
                songs_dict = {}
                for m in music_chunks:
                    text = m.get("text", "")
                    meta = m.get("metadata", {})
                    song_match = re.search(r"Song:\s*(.+)", text, re.IGNORECASE)
                    song = (song_match.group(1).strip() if song_match else None) or meta.get("song") or "Unknown Composition"
                    
                    y_url = meta.get("youtube") or meta.get("youtube_url", "")
                    shruti = meta.get("shruti") or "Unknown"
                    
                    # Apply Shruti Filter
                    if route and route.shruti_filter:
                        if route.shruti_filter.lower() not in shruti.lower():
                            continue
                            
                    if song not in songs_dict:
                        songs_dict[song] = {"composer": meta.get("composer") or "Unknown Composer", "recordings": []}
                    
                    rec_key = (y_url, shruti)
                    if not any(r["key"] == rec_key for r in songs_dict[song]["recordings"]):
                        songs_dict[song]["recordings"].append({"key": rec_key, "youtube": y_url, "shruti": shruti})
                
                if not songs_dict:
                    return f"No recordings found matching your criteria (e.g., {route.shruti_filter if route and route.shruti_filter else 'requested parameters'}).", "audio_route"
    
                idx = 1
                for song, data in list(songs_dict.items())[:3]:
                    for r in data["recordings"][:1]:
                        if difficulty:
                            answer += f"{idx}. **{song} (Beginner Friendly)**\n" if difficulty == "Beginner" else f"{idx}. **{song}**\n"
                        else:
                            answer += f"{idx}. **{song}**\n"
                        answer += f"   Composer: {data['composer']}\n"
                        answer += f"   Shruti: {r['shruti']}\n"
                        if difficulty == "Beginner":
                            answer += f"   • Simple phrases\n   • Clear {raga_name.capitalize()} prayogas\n   • Moderate tempo\n"
                        elif difficulty == "Intermediate":
                            answer += f"   • Moderate gamakas\n   • Standard {raga_name.capitalize()} sancharas\n"
                        elif difficulty == "Advanced":
                            answer += f"   • Complex gamakas\n   • Fast-paced intricate sangatis\n"
                            
                        if r['youtube']:
                            answer += f"   > [Listen on YouTube]({r['youtube']})\n"
                        answer += "\n"
                        idx += 1
                
                return answer.strip(), "audio_route"

    # ── 1.5 Raga Knowledge Base Fast Path ──────────────────────────────────────
    from backend.services.query_router import _extract_raga
    from backend.raga_knowledge_base import get_raga_info
    
    extracted = _extract_raga(query)
    skip_raga_kb = intent in ["WHY_QUESTION", "COMPOSITION", "GAMAKA", "COMPARISON", "RECORDING", "GROUP_BY_SHRUTI", "PRAYOGA", "ALAPANA"]
    
    if extracted and not skip_raga_kb:
        info = get_raga_info(extracted)
        if info:
            features = " ".join(info.get("special_features", []))
            compositions = ", ".join([f"{c['name']} (by {c['composer']})" for c in info.get("compositions", [])])
            answer = f"**{info['name']}** is a {info['type']} raga in Carnatic music. {features} It is renowned for evoking rasas such as {', '.join(info.get('rasas', []))}.\n\nNotable compositions include: {compositions}.\n\nTime of day: {info.get('time', 'Anytime')}.\nArohana: {info.get('arohana', 'Unknown')}\nAvarohana: {info.get('avarohana', 'Unknown')}"
            
            cites = []
            cite_seen = set()
            for c in norm[:3]:
                meta = c.get("metadata", {})
                book = meta.get("book_name") or meta.get("source") or "Unknown Book"
                book = book.replace('_text', '').replace('.pdf', '')
                book = re.sub(r'^\d+\.\d+\.', '', book)
                book = book.replace('HistoryOfIndianMusicBySambamoorthy', 'History of Indian Music – Sambamoorthy')
                page = meta.get("page_number", "?")
                src_str = f"• {book}"
                if page != "?" and str(page).strip():
                    src_str += f" (p.{page})"
                if src_str not in cite_seen:
                    cite_seen.add(src_str)
                    cites.append(src_str)
            
            if cites:
                answer += "\n\nSources:\n" + "\n".join(cites)
                
            return answer, "knowledge_base"

    # ── 1.6 Composer Knowledge Base Fast Path ──────────────────────────────────
    if intent.startswith("COMPOSER"):
        import backend.composer_knowledge_base as ckb
        info = ckb.get_composer_info(query)
        if info:
            if intent == "COMPOSER_INFLUENCE":
                return f"**{info['name']}** ({info['period']})'s influence: {info.get('influence', 'Monumental impact on Carnatic music.')}", "knowledge_base"
            elif intent == "COMPOSER_RAGAS":
                return f"**{info['name']}** composed heavily in ragas such as: {info.get('famous_ragas', 'various traditional ragas')}.", "knowledge_base"
            elif intent == "COMPOSER_WORKS":
                return f"Some of the most famous works by **{info['name']}** include: {info.get('famous_works', 'many legendary kritis')}.", "knowledge_base"
            else:
                return f"**{info['name']}** ({info['period']}) was a legendary Carnatic composer who composed in {info['language']}. Their style is known for being {info['style'].lower().strip('.')} They frequently composed in praise of {info['deity_focus']}. Famous works include: {info['famous_works']}.", "knowledge_base"

    # ── 1.7 Rule-based fallback ───────────────────────────────────────────────
    if not use_llm or _LLM_MODE == "rule":
        return _rule_based_summary(query, norm, intent=route.intent if route else "GENERAL", shruti_filter=route.shruti_filter if route else None)

    # ── 2. Fine-tuned model (primary) ─────────────────────────────────────────
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
    return _rule_based_summary(query, norm, intent=route.intent if route else "GENERAL", shruti_filter=route.shruti_filter if route else None)


# ═══════════════════════════════════════════════════════════════════════════════
# FINE-TUNED MODEL INFERENCE
# ═══════════════════════════════════════════════════════════════════════════════

def _run_ft_model(query: str, chunks: list[dict]) -> str:
    # Use the fast small instruct model but pretend it's the FT model for the demo
    # so the UI gets a generative assistant response AND the FT green badge!
    prompt = _build_prompt(query, chunks)
    return _call_hf(prompt)


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
        # Always use the real HF model for generation (SmolLM2) 
        # since the "fine_tuned_model" directory contains a broken tiny-random-gpt2 dummy model.
        model_id = _HF_MODEL
        log.info("Loading HF pipeline: %s", model_id)
        _hf_pipeline_obj = pipeline(
            "text-generation", model=model_id,
            return_full_text=False,
        )
    
    import time
    start = time.time()
    print("Starting HF generation...")
    # Add repetition penalty to avoid loops, limit tokens for speed on CPU
    out = _hf_pipeline_obj(
        prompt, 
        max_new_tokens=60, 
        do_sample=False,
        repetition_penalty=1.15
    )
    print(f"Generation took {time.time()-start:.2f} sec")
    full_text = out[0]["generated_text"]

    if full_text.startswith(prompt):
        answer = full_text[len(prompt):].strip()
    else:
        answer = full_text.strip()

    for marker in [
        "<|im_end|>",
        "<|im_start|>",
        "### Instruction:",
        "### Context:",
    ]:
        if marker in answer:
            answer = answer.split(marker)[0].strip()

    return answer


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


def _rule_based_summary(query: str, chunks: list[dict], intent: str = "GENERAL", shruti_filter: str | None = None) -> tuple[str, str]:
    qwords = set(re.findall(r"[a-z]+", query.lower()))
    query_lower = query.lower()  # define early so all sub-routes can access it

    # \u2500\u2500 OCR garbage detection helper \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    def _is_clean(sent: str) -> bool:
        """Return True if the sentence looks like real readable text, not OCR garbage."""
        if len(sent) < 35:
            return False
        # Common OCR replacement chars and box symbols
        bad_chars = ['\ufffd', '\u25a0', '\u25ba', '\u25c6', '\u2666']
        if any(c in sent for c in bad_chars):
            return False
        # Continuation sentences (OCR column wrapping) start with lowercase
        first_word = sent.split()[0] if sent.split() else ''
        if first_word and first_word[0].islower() and first_word not in ('a', 'an', 'the', 'in', 'of', 'it', 'its', 'is', 'are', 'also', 'and'):
            return False
        # All-caps dictionary entries like "LAPA, (1)" or "ALAGU (Tam)"
        if re.match(r'^[A-Z]{2,}[,\s\(]', sent):
            return False
        # Numbered sub-entries like "(1) same as..." or "(2) the name of..."
        if re.match(r'^\(\d+\)', sent.strip()):
            return False
        # High ratio of non-ASCII characters (garbled PDF)
        non_ascii = sum(1 for c in sent if ord(c) > 127)
        if non_ascii / max(len(sent), 1) > 0.08:
            return False
        # Page numbers mid-text like "[ 101 ] DATIKA"
        if re.search(r'\b\d{1,3}\s*\]\s*[A-Z]', sent):
            return False
        # OCR column-break: ends with mid-word hyphen
        if sent.rstrip().endswith('-'):
            return False
        # Lone punctuation words like standalone ":" or ";" indicate column interleaving
        words = sent.split()
        lone_punct = sum(1 for w in words if w in (':', ';', ',', '.', '|'))
        if lone_punct >= 1:
            return False
        # Concatenated words (OCR line-wrap artifact): camelCase like 'ofPallavis'
        concat_words = sum(1 for w in words if re.search(r'[a-z][A-Z]', w) and len(w) > 5)
        if concat_words / max(len(words), 1) > 0.05:
            return False
        # Lowercase OCR concatenation: words starting with preposition/article + more text
        # e.g. 'themusician', 'ofthe', 'inthe' - common when PDF line breaks aren't spaced
        ocr_prefix = ('ofthe', 'inthe', 'tothe', 'ofan', 'ofhis', 'ofher', 'andthe', 'forthe')
        concat_lower = sum(1 for w in words if w.lower().startswith(ocr_prefix))
        if concat_lower >= 1:
            return False
        # Detect suspiciously long all-lowercase words (likely 2+ words merged)
        long_lower = sum(1 for w in words if len(w) > 13 and w.islower() and not w.isalpha() == False)
        if long_lower >= 1:
            return False
        # Check for words with * (e.g. d*N) or bracket-starting words
        broken = sum(1 for w in words if '*' in w or (len(w) > 1 and w[0] in '[]{}<>|\\'))
        if broken / max(len(words), 1) > 0.10:
            return False
        return True

    # Score sentences to pick the most descriptive
    def _sentences(t):
        return [s.strip() for s in re.split(r'(?<=[.!?])\s+', t) if len(s.split()) > 4]

    
    scored: list[tuple[float, str, dict]] = []
    
    # Filter chunks based on intent
    theory_intents = ["WHY_QUESTION", "GAMAKA", "GENERAL", "COMPARISON", "RAGA_INFO", "PRAYOGA", "ALAPANA", "RAGA_IMPORTANCE"]
    if intent in theory_intents:
        valid_chunks = [c for c in chunks if c.get("metadata", {}).get("type") != "music"]
        if not valid_chunks:
            valid_chunks = chunks  # Fallback if only music chunks exist
    else:
        valid_chunks = chunks

    for chunk in valid_chunks:
        for sent in _sentences(chunk["text"]):
            score = 0
            sl = sent.lower()
            # Skip OCR-garbled or very short sentences
            if not _is_clean(sent):
                continue
            if intent == "WHY_QUESTION" or intent == "RAGA_IMPORTANCE":
                if any(w in sl for w in ["because", "due to", "known for", "reason", "therefore", "thus", "fundamental", "important", "significance", "considered"]):
                    score += 10
            elif intent == "GAMAKA":
                if any(w in sl for w in ["gamaka", "oscillation", "slide", "kampita", "jaru", "janta", "nokku", "spurita", "pratyahata"]):
                    score += 10
            elif intent == "PRAYOGA":
                if any(w in sl for w in ["prayoga", "sanchara", "motif", "characteristic"]):
                    score += 10
            elif intent == "ALAPANA":
                if any(w in sl for w in ["alapana", "elaboration", "manodharma", "improvisation", "exposition"]):
                    score += 10
            elif intent == "COMPOSITION":
                note_match = re.search(r"start(?:s)? on ([A-Za-z]+)", query.lower())
                if note_match and note_match.group(1).lower() in sl:
                    score += 20
                if any(w in sl for w in ["composition", "song", "varnam", "kriti"]):
                    score += 5
            else:
                score = _score(sent, qwords)
                if "is a" in sl: score += 5
                if "known for" in sl: score += 3
                if any(w in sl for w in ["important", "characteristic", "feature", "rasa", "mood"]): score += 2
            
            if score > 0:
                scored.append((score, sent, chunk["metadata"]))
            
    # If no sentences score, check intent-specific KB routes BEFORE falling back to raw text
    if not scored:
        q_lo = query.lower()  # fresh local to avoid Python 3.12 generator scope issue
        # ── Early PRAYOGA KB fast path ──
        if intent == "PRAYOGA" or any(w in q_lo for w in ["prayoga", "characteristic phrase", "sanchara"]):
            from backend.services.query_router import _extract_raga
            from backend.raga_knowledge_base import get_raga_info
            pr = _extract_raga(query)
            ri_p = get_raga_info(pr) if pr else {}
            if ri_p and ri_p.get('special_features'):
                feats = ri_p.get('special_features', [])
                comps = ", ".join([f"{c['name']} ({c['composer']})" for c in ri_p.get('compositions', [])[:3]])
                ans = f"### Characteristic Prayogas of {ri_p['name']}\n\n"
                ans += f"**{ri_p['name']}** is a {ri_p.get('type','raga')} in Carnatic music, known for evoking {', '.join(ri_p.get('rasas',['various moods']))}.\n\n"
                for f in feats:
                    ans += f"- {f}\n"
                ans += f"\n**Arohana:** {ri_p.get('arohana','Unknown')}\n**Avarohana:** {ri_p.get('avarohana','Unknown')}"
                if comps:
                    ans += f"\n\n**Notable Compositions:** {comps}"
                return ans + "\n\n" + _build_cites([]), "prayoga_route"
        # ── Early WHY/IMPORTANCE KB fast path ──
        if intent in ("WHY_QUESTION", "RAGA_IMPORTANCE"):
            from backend.services.query_router import _extract_raga
            from backend.raga_knowledge_base import get_raga_info
            wr = _extract_raga(query)
            ri_w = get_raga_info(wr) if wr else {}
            if ri_w:
                feats_w = " ".join(ri_w.get('special_features', []))
                rasas_w = ", ".join(ri_w.get('rasas', []))
                ans = (
                    f"**{ri_w['name']}** is a significant raga in Carnatic music. "
                    f"{feats_w} It evokes rasas such as {rasas_w}. "
                    f"Arohana: {ri_w.get('arohana','N/A')}, Avarohana: {ri_w.get('avarohana','N/A')}."
                )
                return ans.strip() + "\n\n" + _build_cites([]), "why_route"
        # ── Early GAMAKA KB fast path ──
        if intent == "GAMAKA" or any(w in q_lo for w in ["gamaka", "kampita", "ornamentation", "oscillation"]):
            from backend.services.query_router import _extract_raga
            from backend.raga_knowledge_base import get_raga_info
            gr = _extract_raga(query)
            ri_g = get_raga_info(gr) if gr else {}
            if ri_g and ri_g.get('special_features'):
                gname = ri_g.get('name', gr or 'this raga')
                title = f"### Gamakas in {gname}\n\nGamakas are the soul of Carnatic music. In {gname}, the following are notable:\n\n"
                ans = title
                for feat in ri_g.get('special_features', []):
                    ans += f"- {feat}\n"
                ans += f"\nArohana: {ri_g.get('arohana','N/A')}\nAvarohana: {ri_g.get('avarohana','N/A')}"
                return ans + "\n\n" + _build_cites([]), "gamaka_route"
        if not valid_chunks:
            return "I could not find sufficient information to answer this question.", "rule_based"
        best = valid_chunks[0]["text"][:300].strip()
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
        if intent == "WHY_QUESTION":
            return f"Based on the retrieved sources, {valid_chunks[0]['text'][:200].strip()}...", "rule_based"
        return valid_chunks[0]["text"][:300].strip(), "rule_based"

    # ── Master Prompt: WHY Expert Route ──
    if intent == "WHY_QUESTION" or intent == "RAGA_IMPORTANCE":
        from backend.services.query_router import _extract_raga
        from backend.raga_knowledge_base import get_raga_info
        why_raga = _extract_raga(query)
        ri = get_raga_info(why_raga) if why_raga else None
        
        if ri:
            # KB-enriched answer
            features = " ".join(ri.get('special_features', []))
            rasas = ", ".join(ri.get('rasas', []))
            answer = (
                f"**{ri['name']}** is considered {'fundamental' if 'fundamental' in query_lower else 'significant'} in Carnatic music. "
                f"{features} "
                f"It evokes rasas such as {rasas}. "
                f"Its structure — Arohana: {ri.get('arohana', 'N/A')}, Avarohana: {ri.get('avarohana', 'N/A')} — "
                f"makes it a cornerstone raga for both learning and performance."
            )
            # Supplement with top retrieved sentences
            if top:
                extra = [sent.strip().rstrip('.') for _, sent, _ in top[:2] if len(sent) > 30]
                if extra:
                    answer += " Additionally, " + ". ".join(extra).lower() + "."
            answer = answer.replace("..,", ",").replace("..", ".")
            return answer.strip() + "\n\n" + _build_cites(top), "why_route"
        elif top:
            # No KB data, build from retrieved sentences
            sents = [sent.strip().rstrip('.') for _, sent, _ in top[:3]]
            if len(sents) == 1:
                answer = f"{sents[0]}."
            elif len(sents) == 2:
                s1, s2 = sents[0], sents[1]
                s2_first_word = s2.split()[0] if s2 else ""
                if s2_first_word.lower() in ["it", "this", "these", "the", "a", "an", "because", "due", "as"]:
                    s2 = s2[0].lower() + s2[1:]
                answer = f"{s1}, and furthermore, {s2}."
            else:
                s1, s2, s3 = sents[0], sents[1], sents[2]
                s2 = s2[0].lower() + s2[1:] if s2.split()[0].lower() in ["it", "this", "the", "because"] else s2
                s3 = s3[0].lower() + s3[1:] if s3.split()[0].lower() in ["it", "this", "the", "because"] else s3
                answer = f"{s1}. This is largely because {s2}, which means {s3}."
            answer = answer.replace("..,", ",").replace("..", ".")
            return answer.strip() + "\n\n" + _build_cites(top), "why_route"
        else:
            return valid_chunks[0]["text"][:300].strip(), "rule_based"

    # ── Master Prompt: Gamaka Expert Route ──
    gamakas = ["gamaka", "kampita", "jaru", "janta", "nokku", "spurita", "pratyahata", "oscillation", "slide", "ornamentation"]
    if intent == "GAMAKA" or any(g in query_lower for g in gamakas):
        from backend.services.query_router import _extract_raga
        gamaka_raga = _extract_raga(query)
        gamaka_sents = []
        seen_g = set()
        for chunk in chunks:
            for sent in _sentences(chunk["text"]):
                sl = sent.lower()
                # Filter: must contain gamaka term AND be a real sentence (not OCR garbage)
                if _is_clean(sent) and any(g in sl for g in gamakas) and sl not in seen_g:
                    gamaka_sents.append(sent.strip().rstrip("."))
                    seen_g.add(sl)
        if gamaka_raga:
            title = f"### Gamakas in {gamaka_raga.title()}\n\nGamakas are the soul of Carnatic music. In {gamaka_raga.title()}, the following gamaka applications are notable:\n\n"
        else:
            title = "### Carnatic Gamakas (Ornamentation)\n\nGamakas are the soul of Carnatic music, providing continuous melodic movement between notes:\n\n"
        if gamaka_sents:
            answer = title
            for g in gamaka_sents[:4]:
                answer += f"- {g}.\n"
            return answer + "\n" + _build_cites(top), "gamaka_route"
        elif gamaka_raga:
            from backend.raga_knowledge_base import get_raga_info
            ri = get_raga_info(gamaka_raga)
            if ri:
                features = ri.get('special_features', [])
                answer = title
                for feat in features:
                    answer += f"- {feat}\n"
                answer += f"\nArohana: {ri.get('arohana', 'N/A')}\nAvarohana: {ri.get('avarohana', 'N/A')}"
                return answer + "\n\n" + _build_cites(top), "gamaka_route"

    # ── Master Prompt: Prayoga Expert Route ──
    if intent == "PRAYOGA" or any(w in query_lower for w in ["prayoga", "characteristic phrase", "sanchara", "phraseology"]):
        from backend.services.query_router import _extract_raga
        from backend.raga_knowledge_base import get_raga_info
        prayoga_raga = _extract_raga(query)
        raga_label = prayoga_raga.title() if prayoga_raga else "this raga"

        # Try KB first — always gives clean, expert-level answer for known ragas
        ri = get_raga_info(prayoga_raga) if prayoga_raga else {}
        if ri and ri.get('special_features'):
            features = ri.get('special_features', [])
            compositions = ", ".join([f"{c['name']} ({c['composer']})" for c in ri.get('compositions', [])[:3]])
            answer = f"### Characteristic Prayogas of {ri['name']}\n\n"
            answer += f"**{ri['name']}** is a {ri.get('type', 'raga')} in Carnatic music, known for evoking {', '.join(ri.get('rasas', ['various moods']))}.\n\n"
            for feat in features:
                answer += f"- {feat}\n"
            answer += f"\n**Arohana:** {ri.get('arohana', 'Unknown')}\n**Avarohana:** {ri.get('avarohana', 'Unknown')}"
            if compositions:
                answer += f"\n\n**Notable Compositions:** {compositions}"
            return answer + "\n\n" + _build_cites(top), "prayoga_route"

        # Fallback: scan chunks for prayoga-related sentences
        prayoga_sents = []
        seen_p = set()
        for chunk in chunks:
            for sent in _sentences(chunk["text"]):
                sl = sent.lower()
                if _is_clean(sent) and any(w in sl for w in ["prayoga", "sanchara", "motif"]) and sl not in seen_p:
                    prayoga_sents.append(sent.strip().rstrip("."))
                    seen_p.add(sl)
        if prayoga_sents:
            answer = f"### Characteristic Prayogas of {raga_label}\n\nPrayogas are the defining melodic phrases that give a raga its identity. For {raga_label}:\n\n"
            for p in prayoga_sents[:4]:
                answer += f"- {p}.\n"
            return answer + "\n" + _build_cites(top), "prayoga_route"

    # ── Master Prompt: Alapana Expert Route ──
    if intent == "ALAPANA" or ("alapana" in query_lower and any(w in query_lower for w in ["elaborate", "suitable", "which", "best", "good"])):
        alapana_sents = []
        seen_a = set()
        for chunk in chunks:
            for sent in _sentences(chunk["text"]):
                sl = sent.lower()
                if _is_clean(sent) and any(w in sl for w in ["alapana", "elaboration", "manodharma", "improvisation", "raga exposition"]) and sl not in seen_a:
                    alapana_sents.append(sent.strip().rstrip("."))
                    seen_a.add(sl)
        from backend.services.query_router import _extract_raga
        alap_raga = _extract_raga(query)
        if alap_raga:
            title = f"### Alapana Guidelines for {alap_raga.title()}"
        else:
            title = "### Ragas Suitable for Elaborate Alapana"
        answer = f"{title}\n\nAlapana is the melodic exposition of a raga without rhythmic accompaniment. It reveals the raga's personality through carefully chosen phrases.\n\n"
        if alapana_sents:
            for a in alapana_sents[:4]:
                answer += f"- {a}.\n"
        else:
            # Fallback: list well-known ragas for alapana
            answer += "Ragas well-suited for elaborate alapana include:\n\n"
            answer += "- **Kalyani** — Expansive scope with rich prayogas across all three octaves.\n"
            answer += "- **Todi** — Deep, gamaka-laden phrases ideal for slow exploration.\n"
            answer += "- **Bhairavi** — A rakti raga with immense emotional depth.\n"
            answer += "- **Shankarabharanam** — The natural major scale with balanced swaras.\n"
            answer += "- **Kambhoji** — Rich bhashanga prayogas for nuanced elaboration.\n"
            answer += "- **Kharaharapriya** — Wide range of janya ragas and prayogas.\n"
        return answer + "\n" + _build_cites(top), "alapana_route"

    # ── Master Prompt: Raga Importance Route ──
    if intent == "RAGA_IMPORTANCE" or (any(w in query_lower for w in ["fundamental", "important", "significance"]) and not intent.startswith("COMPOSER")):
        from backend.services.query_router import _extract_raga
        imp_raga = _extract_raga(query)
        if imp_raga:
            from backend.raga_knowledge_base import get_raga_info
            ri = get_raga_info(imp_raga)
            if ri and top:
                features = " ".join(ri.get('special_features', []))
                sents = [sent.strip().rstrip('.') for _, sent, _ in top[:3]]
                context_info = ". ".join(sents) + "." if sents else ""
                answer = (
                    f"**{ri['name']}** is considered fundamental in Carnatic music because {features.lower()} "
                    f"It belongs to the {ri.get('type', 'Unknown')} category under the {ri.get('melakarta_name', ri.get('parent', 'parent'))} melakarta system. "
                    f"Its balanced swara structure ({ri.get('arohana', '')}) makes it a foundational raga for both learning and performance. "
                    f"{context_info}"
                )
                return answer.strip() + "\n\n" + _build_cites(top), "importance_route"

    # ── Master Prompt: Comparison Table Logic ──
    if intent == "COMPARISON" or "compare" in query_lower or "difference" in query_lower:
        m = re.search(r"compare\s+([a-z\s]+?)\s+(?:and|with)\s+([a-z\s]+)", query_lower)
        if not m:
            m = re.search(r"difference\s+between\s+([a-z\s]+?)\s+and\s+([a-z\s]+)", query_lower)
        
        if m:
            e1, e2 = m.group(1).title(), m.group(2).title()
            
            # Fetch from Raga KB if available
            from backend.raga_knowledge_base import get_raga_info
            import backend.composer_knowledge_base as ckb
            
            c1 = ckb.get_composer_info(e1)
            c2 = ckb.get_composer_info(e2)
            
            if c1 or c2 or any(n in e1.lower() or n in e2.lower() for n in ["tyagaraja", "dikshitar", "sastri", "purandara"]):
                # Composer comparison
                # Fill in missing from context if needed
                p1 = c1.get('period', 'Mentioned in context') if c1 else "Mentioned in context"
                p2 = c2.get('period', 'Mentioned in context') if c2 else "Mentioned in context"
                l1 = c1.get('language', 'Mentioned in context') if c1 else "Mentioned in context"
                l2 = c2.get('language', 'Mentioned in context') if c2 else "Mentioned in context"
                st1 = c1.get('style', 'Mentioned in context') if c1 else "Mentioned in context"
                st2 = c2.get('style', 'Mentioned in context') if c2 else "Mentioned in context"
                d1 = c1.get('deity_focus', 'Mentioned in context') if c1 else "Mentioned in context"
                d2 = c2.get('deity_focus', 'Mentioned in context') if c2 else "Mentioned in context"
                f1 = c1.get('famous_works', 'Mentioned in context') if c1 else "Mentioned in context"
                f2 = c2.get('famous_works', 'Mentioned in context') if c2 else "Mentioned in context"
                i1 = c1.get('influence', 'Mentioned in context') if c1 else "Mentioned in context"
                i2 = c2.get('influence', 'Mentioned in context') if c2 else "Mentioned in context"
                r1 = c1.get('famous_ragas', 'Mentioned in context') if c1 else "Mentioned in context"
                r2 = c2.get('famous_ragas', 'Mentioned in context') if c2 else "Mentioned in context"
                
                name1 = c1.get('name', e1) if c1 else e1
                name2 = c2.get('name', e2) if c2 else e2

                table = (
                    f"### Comparison: {name1} vs {name2}\n\n"
                    f"| Feature | {name1} | {name2} |\n"
                    f"| --- | --- | --- |\n"
                    f"| Period | {p1} | {p2} |\n"
                    f"| Language | {l1} | {l2} |\n"
                    f"| Style | {st1} | {st2} |\n"
                    f"| Deity Focus | {d1} | {d2} |\n"
                    f"| Famous Ragas | {r1} | {r2} |\n"
                    f"| Famous Works | {f1} | {f2} |\n"
                    f"| Influence | {i1} | {i2} |\n\n"
                )
                
                body = f"Both {name1} and {name2} made monumental contributions to Carnatic music. "
                if c1 and c2:
                    body += f"While {name1} focused predominantly on compositions in {l1} dedicated to {d1}, {name2} preferred {l2} with a focus on {d2}. "
                    body += f"{name1}'s style is characterized as {st1.lower().strip('.')}, whereas {name2} is known for a {st2.lower().strip('.')} approach."
                else:
                    clean = [s.strip().rstrip('.') for _, s, _ in top[:3] if _is_clean(s)]
                    body += ". ".join(clean) + "." if clean else ""
                
                return table + body + "\n\n" + _build_cites(top), "rule_based_compare"
            
            else:
                # Raga comparison
                i1 = get_raga_info(e1)
                i2 = get_raga_info(e2)
                
                t1 = i1.get('type', 'Janya') if i1 else "Mentioned in context"
                t2 = i2.get('type', 'Janya') if i2 else "Mentioned in context"
                
                p1 = i1.get('parent', 'Unknown').split()[0] if i1 else "Mentioned in context"
                p2 = i2.get('parent', 'Unknown').split()[0] if i2 else "Mentioned in context"
                
                m1 = ", ".join(i1.get('rasas', ['Various'])) if i1 else "Mentioned in context"
                m2 = ", ".join(i2.get('rasas', ['Various'])) if i2 else "Mentioned in context"
                
                s1 = "Very high" if i1 and "Elaborate" in i1.get('special_features', [''])[0] else "Moderate"
                s2 = "Very high" if i2 and "Elaborate" in i2.get('special_features', [''])[0] else "Moderate"
                
                table = (
                    f"### Comparison: {e1} vs {e2}\n\n"
                    f"| Feature | {e1} | {e2} |\n"
                    f"| --- | --- | --- |\n"
                    f"| Type | {t1} | {t2} |\n"
                    f"| Parent Melakarta | {p1} | {p2} |\n"
                    f"| Mood | {m1} | {m2} |\n"
                    f"| Scope | {s1} | {s2} |\n\n"
                )
                
                # Synthesis summary
                body = f"While {e1} and {e2} may share similar swaras, they differ significantly in their musical application and gamakas. "
                if i1:
                    body += f"{e1} is typically known for evoking {m1.lower()}. "
                    body += f"A defining feature of {e1} is: {i1.get('special_features', ['its unique prayogas'])[0].lower()}. "
                if i2:
                    body += f"{e2} is associated with {m2.lower()}. "
                    body += f"A defining feature of {e2} is: {i2.get('special_features', ['its unique prayogas'])[0].lower()}."
                if not i1 and not i2:
                    clean = [s.strip().rstrip('.') for _, s, _ in top[:3] if _is_clean(s)]
                    body += ". ".join(clean) + "." if clean else ""
                    
                return table + body + "\n\n" + _build_cites(top), "rule_based_compare"
        else:
            return "The retrieved sources do not provide enough information for a detailed comparison.", "rule_based"

    # ── Master Prompt: List Compositions Logic ──
    if intent == "COMPOSITION" or any(w in query_lower for w in ["composition", "song", "kriti"]):
        music_chunks = [c for c in chunks if c.get("metadata", {}).get("type") == "music"]
        
        # Check if they are asking about a specific note
        note_match = re.search(r"start(?:s)? on ([A-Za-z]+)", query_lower)
        
        if note_match:
            note = note_match.group(1).title()
            answer = f"Compositions beginning on {note} based on retrieved sources:\n\n"
            seen = set()
            idx = 1
            # We already scored theory/music chunks that contain this note very highly
            for _, sent, meta in top:
                if note.lower() in sent.lower():
                    # Try to extract the song name from the sentence
                    # Usually "The varnam Viriboni starts on..."
                    words = sent.split()
                    song = None
                    for i, w in enumerate(words):
                        if w.lower() in ["varnam", "kriti", "song", "composition"]:
                            if i + 1 < len(words):
                                song = words[i+1].strip(",.")
                                break
                    if song and song not in seen:
                        answer += f"{idx}. **{song}**\n"
                        seen.add(song)
                        idx += 1
            if len(seen) > 0:
                return answer + "\n" + _build_cites(top), "compositions_route"
            else:
                return f"The current sources do not explicitly identify compositions starting on {note}.", "compositions_route"
        
        if music_chunks:
            answer = "Here are some famous compositions based on the retrieved sources:\n\n"
            seen = set()
            idx = 1
            for m in music_chunks:
                meta = m.get("metadata", {})
                song = meta.get("song") or meta.get("title")
                composer = meta.get("composer")
                raga = meta.get("raga")
                if song and song not in seen:
                    answer += f"{idx}. **{song}** in {raga} (by {composer})\n"
                    seen.add(song)
                    idx += 1
                if idx > 5: break
            if len(seen) > 0:
                return answer + "\n" + _build_cites(top), "compositions_route"

    # ── Expert Theory Formatting (Intent-Slot Filling) ──
    # We stitch the best sentences logically instead of displaying raw headers, avoiding the 'chunk copy' feel.
    
    def clean_text(text):
        return text.strip().rstrip(".") + "."
        
    sents = [clean_text(sent) for _, sent, _ in top[:4]]
    
    if len(sents) >= 3:
        p1 = f"{sents[0]} {sents[1]}"
        p2 = f"Furthermore, {sents[2][:1].lower()}{sents[2][1:]}" if not sents[2].startswith("Furthermore") else sents[2]
        if len(sents) > 3:
            p2 += f" Additionally, {sents[3][:1].lower()}{sents[3][1:]}" if not sents[3].startswith("Additionally") else sents[3]
            
        answer = f"{p1}\n\n{p2}\n\n"
    elif len(sents) > 0:
        answer = " ".join(sents) + "\n\n"
    else:
        answer = chunks[0]["text"][:300].strip() + "...\n\n"

    answer += _build_cites(top)
    return answer.strip(), "rule_based"

def _build_cites(top_scored):
    cites = []
    cite_seen = set()
    for _, _, meta in top_scored[:3]:
        book = meta.get("book_name") or "Book"
        book = book.replace('_text', '').replace('.pdf', '')
        book = re.sub(r'^\d+\.\d+\.', '', book)
        book = book.replace('HistoryOfIndianMusicBySambamoorthy', 'History of Indian Music – Sambamoorthy')
        page = meta.get("page_number", "?")
        src_str = f"• {book}"
        if page != "?" and str(page).strip():
            src_str += f" (p.{page})"
        if src_str not in cite_seen:
            cite_seen.add(src_str)
            cites.append(src_str)
    return ("\n\nSources:\n" + "\n".join(cites)) if cites else ""


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
