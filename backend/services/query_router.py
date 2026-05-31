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
    "avarohana","composer","composition","compositions","tyagaraja","dikshitar","purandaradasa","annamacharya",
    "bhairavi","kalyani","hindolam","mohanam","shankarabharanam","todi","manji","kambhoji",
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
    "prayoga","sanchara","fundamental","important","significance","kattai",
    "recording","recordings","elaborate","suitable","rakti","compare","difference",
]

THEORY_TRIGGERS   = ["what is","define","explain","describe","how does","difference",
                      "compare","types of","kinds of","characteristics","features",
                      "origin","history","significance","importance","role","purpose",
                      "examples of","tell me","elaborate","meaning of"]
MUSIC_TRIGGERS    = ["song","songs","list","compositions by","composed by","composer",
                     "vocalist","performer","singer","album","recording","play",
                     "listen","audio","who composed","who sang","krithi","kriti",
                     "keerthana","popular","famous","show me","find","search",
                     "shruti", "melakarta"]
AUDIO_TRIGGERS    = ["play","listen","audio","sound","hear","alapana",
                     "sample","clip","suggest","recording","recordings"]

RAGA_NAMES = [
    "kalyani","bhairavi","hindolam","kharaharapriya","mohanam","shankarabharanam",
    "sankarabharanam","todi","hamsadhwani","revati","madhyamavati","bilahari",
    "natabhairavi","charukesi","saveri","suddhasaveri","kambhoji","begada",
    "kedaram","anandabhairavi","ritigowla","sriranjani","vasanta","sahana",
    "mukhari","nattai","varali","punnagavarali","nilambari","devagandhari",
    "nalinakanti","jayantasri","abhogi","amritavarshini","simhendramadhyama",
    "hemavati","dharmavati","gamanasrama","lathangi","rasikapriya","pantuvarali",
    "arabhi","harikambhoji","suddhadhanyasi","gourimanohari","kiravani","bowli",
    "poorvikalyani","kaanada","sindhu bhairavi","nayaki","kokilapriya",
    "manji","desh","durga","sivaranjani","bhupalam","amruthavarshini",
    "hamsanadam","keeravani","charukesi","bageshri","yaman","bhairav",
]

@dataclass
class RouterResult:
    mode:           str                      # theory|music|hybrid|rejected
    intent:         str   = "GENERAL"        # RAGA_INFO, COMPARISON, COMPOSER, COMPOSITION, RECORDING, GAMAKA, AROHANA_AVAROHANA, WHY_QUESTION, PRAYOGA, ALAPANA, RAGA_IMPORTANCE, STARTING_NOTE
    shruti_filter:  str | None = None
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
    # Check for multiple questions
    questions = re.split(r'\?+', q)
    questions = [x.strip() for x in questions if x.strip()]
    if len(questions) > 1:
        return RouterResult(mode="multiple_questions")

    if not _is_in_domain(q):
        return RouterResult(mode="rejected")

    raga      = _extract_raga(q)
    audio     = any(t in lower for t in AUDIO_TRIGGERS)
    t_score   = sum(1 for t in THEORY_TRIGGERS if t in lower)
    m_score   = sum(1 for t in MUSIC_TRIGGERS  if t in lower)

    # ── Intent Classifier ────────────────────────────────────────────────────
    intent = "GENERAL"
    shruti_filter = None

    # Check for Shruti filter
    shruti_match = re.search(r"(\d+)\s*(?:kattai|shruthi|shruti)", lower)
    if shruti_match:
        shruti_filter = f"{shruti_match.group(1)} Kattai"

    if "compare" in lower or "difference" in lower:
        intent = "COMPARISON"
    elif "why" in lower.split() and any(w in lower for w in ["fundamental", "important", "significance", "considered"]):
        intent = "RAGA_IMPORTANCE"
    elif "why" in lower.split():
        intent = "WHY_QUESTION"
    elif any(w in lower for w in ["prayoga", "characteristic phrase", "sanchara", "phraseology"]):
        intent = "PRAYOGA"
    elif ("elaborate" in lower and "alapana" in lower) or ("suitable" in lower and "alapana" in lower) or ("which raga" in lower and "alapana" in lower):
        intent = "ALAPANA"
    elif any(w in lower for w in ["fundamental", "importance", "significant", "considered", "why is"]):
        intent = "RAGA_IMPORTANCE"
    elif any(w in lower for w in ["starting note", "graha swara", "begin on", "start on", "graha"]):
        intent = "STARTING_NOTE"
    elif "group" in lower and "shruti" in lower:
        intent = "GROUP_BY_SHRUTI"
    elif audio or "recommend" in lower or "suggest" in lower:
        intent = "RECORDING"
    elif any(g in lower for g in ["gamaka", "kampita", "jaru", "janta", "nokku", "spurita", "pratyahata", "ornamentation"]):
        intent = "GAMAKA"
    elif "arohana" in lower or "avarohana" in lower:
        intent = "AROHANA_AVAROHANA"
    elif any(w in lower for w in ["tyagaraja", "dikshitar", "sastri", "syama", "purandaradasa", "swathi", "thirunal", "annamacharya", "composer"]):
        if any(w in lower for w in ["influence", "impact", "legacy", "contribute"]):
            intent = "COMPOSER_INFLUENCE"
        elif any(w in lower for w in ["raga", "ragas"]):
            intent = "COMPOSER_RAGAS"
        elif any(w in lower for w in ["composition", "song", "kriti", "krithi", "work"]):
            intent = "COMPOSER_WORKS"
        else:
            intent = "COMPOSER"
    elif any(w in lower for w in ["composition", "song", "kriti", "krithi", "varnam", "start on"]):
        intent = "COMPOSITION"
    elif raga:
        intent = "RAGA_INFO"

    if audio and raga:
        mode = "hybrid"
    elif intent in ["COMPOSITION", "RECORDING", "GROUP_BY_SHRUTI"]:
        mode = "music"
    elif t_score > 0 and m_score == 0:
        mode = "theory"
    elif m_score > 0 and t_score == 0:
        mode = "music"
    elif t_score > 0 and m_score > 0:
        mode = "hybrid"
    else:
        mode = "theory"

    theory_filters = ["theory", "research"] if mode in ("theory", "hybrid") else []
    if audio:
        theory_filters = ["theory"] if mode in ("theory", "hybrid") else []

    return RouterResult(
        mode=mode,
        intent=intent,
        shruti_filter=shruti_filter,
        wants_audio=audio,
        raga_name=raga,
        theory_filters=theory_filters,
        music_filters=["music"]              if mode in ("music","hybrid") else [],
        top_k_theory=3 if mode == "hybrid" else 5 if mode == "theory" else 0,
        top_k_music=7 if mode == "hybrid" else 5 if mode == "music" else 0,
    )

def describe_route(r: RouterResult) -> str:
    parts = [f"mode={r.mode}"]
    if r.raga_name:   parts.append(f"raga={r.raga_name}")
    if r.wants_audio: parts.append("audio=True")
    return " | ".join(parts)