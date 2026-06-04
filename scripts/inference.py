"""
inference.py
CarnaticGPT – LLM inference engine with safe multi-backend fallback chain.

Priority order:
  1. Fine-tuned local model  (models/fine_tuned_model)
  2. GGUF via llama-cpp-python (models/*.gguf)
  3. HuggingFace Phi-3-mini   (auto-downloaded)
  4. HuggingFace TinyLlama    (smallest fallback)

Each backend is tried in order; the first one that loads without error is used.
The selected backend is logged once at startup.
"""

import os
import re
import gc
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("inference")
logging.basicConfig(level=logging.INFO)

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
FINETUNED_PATH  = Path("models/fine_tuned_model")
GGUF_DIR        = Path("models")
HF_MODEL_PRIMARY  = "microsoft/Phi-3-mini-4k-instruct"
HF_MODEL_FALLBACK = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

MAX_CONTEXT_CHARS = 3000   # truncate context fed to LLM
MAX_NEW_TOKENS    = 300
TEMPERATURE       = 0.3

# ─────────────────────────────────────────────
# SYSTEM PROMPT
# ─────────────────────────────────────────────
SYSTEM_PROMPT = (
    "You are CarnaticGPT, a knowledgeable expert in Carnatic classical music. "
    "Answer questions accurately and clearly using ONLY the provided context. "
    "If the context does not contain enough information, say: "
    "'I could not find reliable Carnatic knowledge for this query.' "
    "Do not hallucinate. Do not repeat the question. Be concise and informative."
)


def _build_prompt(question: str, context: str) -> str:
    context = context[:MAX_CONTEXT_CHARS]
    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}\n\n"
        f"Answer:"
    )


def _extract_answer(full_text: str, prompt: str) -> str:
    """Strip the prompt from the generated text and clean up."""
    if "Answer:" in full_text:
        answer = full_text.split("Answer:")[-1]
    else:
        answer = full_text[len(prompt):]
    answer = answer.strip()
    # Remove any trailing system-like artifacts
    for stop in ["Question:", "Context:", "<|", "[INST]", "###"]:
        if stop in answer:
            answer = answer.split(stop)[0].strip()
    return answer if answer else "I could not find reliable Carnatic knowledge for this query."


# ─────────────────────────────────────────────
# BACKEND CLASSES
# ─────────────────────────────────────────────
class _FineTunedBackend:
    name = "fine_tuned_local"

    def __init__(self):
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM
        from peft import PeftModel
        import json
        
        # Determine base model from adapter config
        base_model_id = "hf-internal-testing/tiny-random-gpt2"
        adapter_config = FINETUNED_PATH / "adapter_config.json"
        if adapter_config.exists():
            try:
                with open(adapter_config, "r") as f:
                    cfg = json.load(f)
                    base_model_id = cfg.get("base_model_name_or_path", base_model_id)
            except Exception:
                pass
                
        logger.info(f"Loading base model '{base_model_id}' …")
        self.tokenizer = AutoTokenizer.from_pretrained(str(FINETUNED_PATH))
        
        base = AutoModelForCausalLM.from_pretrained(
            base_model_id,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto",
            low_cpu_mem_usage=True,
        )
        logger.info(f"Attaching LoRA adapter from {FINETUNED_PATH} …")
        self.model = PeftModel.from_pretrained(base, str(FINETUNED_PATH))
        self.model.eval()
        self._torch = torch
        logger.info("Fine-tuned model loaded ✓")

    def generate(self, question: str, context: str) -> str:
        import torch
        prompt = _build_prompt(question, context)
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=1024,
        ).to(self.model.device)
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=MAX_NEW_TOKENS,
                temperature=TEMPERATURE,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )
        full_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return _extract_answer(full_text, prompt)


class _GGUFBackend:
    name = "gguf_llama_cpp"

    def __init__(self, model_path: Path):
        from llama_cpp import Llama
        logger.info(f"Loading GGUF model: {model_path} …")
        self.llm = Llama(
            model_path=str(model_path),
            n_ctx=2048,
            n_threads=os.cpu_count() or 4,
            verbose=False,
        )
        self.model_path = model_path
        logger.info("GGUF model loaded ✓")

    def generate(self, question: str, context: str) -> str:
        prompt = _build_prompt(question, context)
        result = self.llm(
            prompt,
            max_tokens=MAX_NEW_TOKENS,
            temperature=TEMPERATURE,
            stop=["Question:", "Context:", "\n\n\n"],
            echo=False,
        )
        answer = result["choices"][0]["text"].strip()
        return answer if answer else "I could not find reliable Carnatic knowledge for this query."


class _HFBackend:
    name = "huggingface_pipeline"

    def __init__(self, model_id: str):
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
        logger.info(f"Loading HuggingFace model: {model_id} …")
        local_only = os.getenv("HF_LOCAL_ONLY", "true").lower() == "true"
        self.tokenizer = AutoTokenizer.from_pretrained(model_id, local_files_only=local_only)
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=dtype,
            device_map="auto",
            low_cpu_mem_usage=True,
            local_files_only=local_only,
        )
        model.eval()
        self.pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=self.tokenizer,
            max_new_tokens=MAX_NEW_TOKENS,
            temperature=TEMPERATURE,
            do_sample=True,
            return_full_text=False,   # return only generated part
        )
        logger.info(f"HuggingFace model loaded ✓ ({model_id})")

    def generate(self, question: str, context: str) -> str:
        prompt = _build_prompt(question, context)
        result = self.pipe(prompt)
        answer = result[0]["generated_text"].strip()
        for stop in ["Question:", "Context:", "<|", "[INST]", "###"]:
            if stop in answer:
                answer = answer.split(stop)[0].strip()
        return answer if answer else "I could not find reliable Carnatic knowledge for this query."


class _GeminiBackend:
    name = "gemini"

    def __init__(self, key: str):
        self.key = key
        logger.info("Gemini backend initialized ✓")

    def generate(self, question: str, context: str) -> str:
        import requests
        prompt = _build_prompt(question, context)
        model = "gemini-2.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.key}"
        data = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }
        try:
            res = requests.post(url, json=data, timeout=12)
            if res.status_code == 200:
                answer = res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
                return answer if answer else "I could not find reliable Carnatic knowledge for this query."
            else:
                logger.error(f"Gemini API error: {res.status_code} - {res.text}")
        except Exception as e:
            logger.error(f"Gemini API request failed: {e}")
        return "I could not find reliable Carnatic knowledge for this query."


# ─────────────────────────────────────────────
# LOADER  – tries backends in order
# ─────────────────────────────────────────────
_backend = None


def _load_backend():
    global _backend

    # 0. Check Gemini API key first if configured
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        try:
            from pathlib import Path
            _root = Path(__file__).resolve().parent
            while _root.name in ("services", "backend", "scripts"):
                _root = _root.parent
            env_path = _root / ".env"
            if env_path.exists():
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            parts = line.split("=", 1)
                            if len(parts) == 2:
                                if parts[0].strip() == "GEMINI_API_KEY" and parts[1].strip():
                                    gemini_key = parts[1].strip()
                                    break
        except Exception:
            pass

    if gemini_key:
        try:
            _backend = _GeminiBackend(gemini_key)
            return
        except Exception as e:
            logger.warning(f"Gemini backend initialization failed: {e}")

    # 1. Fine-tuned local model
    if FINETUNED_PATH.exists() and any(FINETUNED_PATH.iterdir()):
        try:
            _backend = _FineTunedBackend()
            return
        except Exception as e:
            logger.warning(f"Fine-tuned backend failed: {e}")
            gc.collect()

    # 2. GGUF files
    if GGUF_DIR.exists():
        gguf_files = sorted(GGUF_DIR.glob("*.gguf"))
        for gguf_path in gguf_files:
            try:
                _backend = _GGUFBackend(gguf_path)
                return
            except Exception as e:
                logger.warning(f"GGUF backend failed ({gguf_path.name}): {e}")
                gc.collect()

    # 3. HuggingFace Phi-3-mini
    try:
        _backend = _HFBackend(HF_MODEL_PRIMARY)
        return
    except Exception as e:
        logger.warning(f"Phi-3-mini backend failed: {e}")
        gc.collect()

    # 4. TinyLlama (smallest possible fallback)
    try:
        _backend = _HFBackend(HF_MODEL_FALLBACK)
        return
    except Exception as e:
        logger.error(f"All LLM backends failed. Last error: {e}")
        _backend = None


# ─────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────
def get_backend_name() -> str:
    if _backend is None:
        _load_backend()
    return _backend.name if _backend else "none"


def generate_answer(question: str, context: str) -> str:
    """
    Main entry point called by app.py.
    Returns a string answer. Never raises — falls back to context display.
    """
    global _backend
    if _backend is None:
        _load_backend()

    if _backend is None:
        # Return a sentinel string with "unavailable" so synthesizer.py falls back to extractive
        return "LLM unavailable — no compatible model found."

    try:
        return _backend.generate(question, context)
    except Exception as e:
        logger.error(f"Generation error ({_backend.name}): {e}")
        # Try reloading once
        _backend = None
        _load_backend()
        if _backend:
            try:
                return _backend.generate(question, context)
            except Exception as e2:
                logger.error(f"Retry also failed: {e2}")
        return "LLM unavailable (generation failed)."


# ─────────────────────────────────────────────
# CLI TEST
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Backend: {get_backend_name()}")
    ctx = (
        "Shruti in Carnatic music refers to the tonal pitch system. "
        "There are 22 shrutis in an octave according to classical theory. "
        "Shruti is the smallest interval of pitch that can be perceived by the human ear. "
        "It forms the foundation upon which all ragas and swaras are built."
    )
    answer = generate_answer("What is Shruti in Carnatic music?", ctx)
    print(f"\nAnswer:\n{answer}")