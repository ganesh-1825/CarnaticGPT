"""
query_router.py  —  domain filter + query routing for CarnaticGPT
"""
import re
from dataclasses import dataclass, field

# ── Carnatic domain keywords (any match = valid) ─────────────────────────────
DOMAIN_KEYWORDS = [
    "raga","ragam","tala","thala","swara","shruti","shruthi","gamaka","alapana",
    "carnatic","karnatik","hindustani","music","song","kriti","krithi","varnam",
    "pallavi","anupallavi","charanam","melapakarta","melakarta","janya","arohana",
    "avarohana","composer","tyagaraja","dikshitar","purandaradasa","annamacharya",
    "bhairavi","kalyani","hindolam","mohanam","shankarabharanam","todi","kambhoji",
    "hamsadhwani","revati","madhyamavati","bilahari","natabhairavi","charukesi",
    "saveri","begada","kedaram","anandabhairavi","ritigowla","sriranjani","vasanta",
    "sahana","mukhari","nattai","varali","punnagavarali","nilambari","devagandhari",
    "nalinakanti","jayantasri","abhogi","amritavarshini","kiravani","arabhi",
    "harikambhoji","bowli","suddhasaveri","sriranjani","kharaharapriya","nattai",
    "geetam","swarajati","javali","thillana","padam","keerthana","devaranama",
    "manodharma","sangeetam","niraval","kalpana","tanam","trinity","saint",
    "instrument","veena","mridangam","violin","ghatam","flute","venu","nadaswaram",
    "concert","performance","recital","bhakti","devotional","classical","tradition",
    "sruthi","nada","sruti","sapta","saptha","adi","rupaka","misra","khanda",
    "tisra","chatusra","sankirna","laghu","drutam","anudrutam",
    "audio","play","listen","hear","sample",
    "what is","define","explain","describe","who is","which","how does","compare",
]

THEORY_TRIGGERS   = ["what is","define","explain","describe","how does","difference",
                      "compare","types of","kinds of","characteristics","features",
                      "origin","history","significance","importance","role","purpose",
                      "examples of","tell me","elaborate","meaning of"]
MUSIC_TRIGGERS    = ["song","songs","list","compositions by","composed by","composer",
                     "vocalist","performer","singer","album","recording","play",
                     "listen","audio","who composed","who sang","krithi","kriti",
                     "keerthana","popular","famous","show me","find","search"]
AUDIO_TRIGGERS    = ["play","listen","audio","sound","hear","alapana","arohana",
                     "avarohana","sample","clip"]

RAGA_NAMES = [
    "kalyani","bhairavi","hindolam","kharaharapriya","mohanam","shankarabharanam",
    "todi","hamsadhwani","revati","madhyamavati","bilahari","natabhairavi",
    "charukesi","saveri","suddhasaveri","kambhoji","begada","kedaram",
    "anandabhairavi","ritigowla","sriranjani","vasanta","sahana","mukhari",
    "nattai","varali","punnagavarali","nilambari","devagandhari","nalinakanti",
    "jayantasri","abhogi","amritavarshini","simhendramadhyama","hemavati",
    "dharmavati","gamanasrama","lathangi","rasikapriya","pantuvarali","arabhi",
    "harikambhoji","suddhadhanyasi","gourimanohari","kiravani","bowli",
    "poorvikalyani","kaanada","sindhu bhairavi","nayaki","kokilapriya",
]

@dataclass
class RouterResult:
    mode:           str                      # theory|music|hybrid|rejected
    wants_audio:    bool  = False
    raga_name:      str | None = None
    theory_filters: list  = field(default_factory=list)
    music_filters:  list  = field(default_factory=list)
    top_k_theory:   int   = 5
    top_k_music:    int   = 5

def _is_in_domain(q: str) -> bool:
    lower = q.lower()
    return any(kw in lower for kw in DOMAIN_KEYWORDS)

def _extract_raga(q: str) -> str | None:
    lower = q.lower()
    for r in RAGA_NAMES:
        if re.search(r"\b" + re.escape(r) + r"s?\b", lower):
            return r.title()
    return None

def route_query(query: str) -> RouterResult:
    q = query.strip()
    lower = q.lower()

    # ── Domain gate ──────────────────────────────────────────────────────────
    if not _is_in_domain(q):
        return RouterResult(mode="rejected")

    raga      = _extract_raga(q)
    audio     = any(t in lower for t in AUDIO_TRIGGERS)
    t_score   = sum(1 for t in THEORY_TRIGGERS if t in lower)
    m_score   = sum(1 for t in MUSIC_TRIGGERS  if t in lower)

    if audio and raga:
        mode = "hybrid"
    elif re.search(r"\b(list|show|find|search|songs?|compositions?|who\s+composed|vocalist)\b", lower):
        mode = "music"
    elif t_score > 0 and m_score == 0:
        mode = "theory"
    elif m_score > 0 and t_score == 0:
        mode = "music"
    elif t_score > 0 and m_score > 0:
        mode = "hybrid"
    else:
        mode = "theory"

    return RouterResult(
        mode=mode,
        wants_audio=audio,
        raga_name=raga,
        theory_filters=["theory","research"] if mode in ("theory","hybrid") else [],
        music_filters=["music"]              if mode in ("music","hybrid") else [],
        top_k_theory=5 if mode in ("theory","hybrid") else 0,
        top_k_music=5  if mode in ("music","hybrid")  else 0,
    )

def describe_route(r: RouterResult) -> str:
    parts = [f"mode={r.mode}"]
    if r.raga_name:   parts.append(f"raga={r.raga_name}")
    if r.wants_audio: parts.append("audio=True")
    return " | ".join(parts)