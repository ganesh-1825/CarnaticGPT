"""
query_router.py  —  domain filter + query routing for CarnaticGPT
"""
import re
from dataclasses import dataclass, field

# ── Carnatic domain keywords (any match = valid) ─────────────────────────────
DOMAIN_KEYWORDS = [
    "raga","ragam","raaga","tala","thala","swara","shruti","shruthi","gamaka","alapana",
    "carnatic","karnatik","hindustani","music","song","kriti","krithi","varnam",
    "pallavi","anupallavi","charanam","melapakarta","melakarta","janya","arohana",
    "avarohana","composer","composed","composers","who composed","who was","composition","compositions","tyagaraja","dikshitar","purandaradasa","annamacharya","samaja","gamana","vara","vathapi","bhajare","manasa",
    "endaro","mahanubhavulu","nagumomu","vatapi","brochevarevarura","broche","pancharatna","keerthana",
    "kattai","pitch","tonic","frequency",
    "1 kattai","2 kattai","3 kattai","4 kattai","5 kattai","6 kattai","7 kattai",
    "bhairavi","kalyani","hindolam","mohanam","mohana","shankarabharanam","todi","thodi","hanumatodi","manji","kambhoji",
    "hamsadhwani","revati","madhyamavati","bilahari","natabhairavi","charukesi",
    "saveri","begada","kedaram","anandabhairavi","ritigowla","sriranjani","vasanta",
    "sahana","mukhari","nattai","varali","punnagavarali","nilambari","devagandhari",
    "nalinakanti","jayantasri","abhogi","amritavarshini","kiravani","arabhi",
    "harikambhoji","bowli","suddhasaveri","sriranjani","kharaharapriya","nattai",
    "abheri",
    "geetam","swarajati","javali","tillana","thillana","padam","keerthana","devaranama",
    "manodharma","sangeetam","niraval","kalpana","tanam","trinity","saint",
    "instrument","veena","mridangam","violin","ghatam","flute","venu","nadaswaram",
    "concert","performance","recital","bhakti","devotional","classical","tradition",
    "sruthi","nada","sruti","sapta","saptha","adi","rupaka","misra","khanda",
    "tisra","chatusra","sankirna","laghu","drutam","anudrutam",
    "audio","play","listen","hear","sample","watch","video","youtube",
    "what is","define","explain","describe","who is","which","how does","compare",
    "prayoga","sanchara","fundamental","important","significance","kattai",
    "recording","recordings","elaborate","suitable","rakti","compare","difference",
    "parichayam", "rtp",
    "naadam", "nadam", "sangeetham", "sangeetam", "sthayi", "purvanga", "uttaranga",
    "dhatu", "matu", "dhatuvu", "matuvu", "akshara kala", "trikala", "tourya trikama",
    "jaati", "jaatis", "pancha jaatis", "avartham", "angas", "shadangas", "talangas", "sapta talas"
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
    "kalyani","bhairavi","hindolam","kharaharapriya","mohanam","mohana","shankarabharanam",
    "sankarabharanam","todi","thodi","hanumatodi","hamsadhwani","revati","madhyamavati","bilahari",
    "natabhairavi","charukesi","saveri","suddhasaveri","kambhoji","begada",
    "kedaram","anandabhairavi","ritigowla","sriranjani","vasanta","sahana",
    "mukhari","nattai","varali","punnagavarali","nilambari","devagandhari",
    "nalinakanti","jayantasri","abhogi","amritavarshini","simhendramadhyama",
    "hemavati","dharmavati","gamanasrama","lathangi","rasikapriya","pantuvarali",
    "arabhi","harikambhoji","suddhadhanyasi","gourimanohari","kiravani","bowli",
    "poorvikalyani","kaanada","sindhu bhairavi","nayaki","kokilapriya",
    "manji","desh","durga","sivaranjani","bhupalam","amruthavarshini",
    "hamsanadam","keeravani","charukesi","bageshri","yaman","bhairav",
    "abheri",
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

def _is_out_of_scope(q: str) -> bool:
    import re
    lower = q.lower()
    # List of terms that are definitely out of scope for Carnatic musicology
    OUT_OF_SCOPE_TERMS = [
        "whatsapp", "apollo", "artificial intelligence", "coding", "programming",
        "bitcoin", "crypto", "software", "computer", "spacecraft", "astronaut",
        "recipe", "cooking", "football", "cricket", "basketball", "soccer",
        "politics", "presidency", "stock market", "shares", "finance", "medical",
        "medicine", "quantum", "relativity", "chemistry", "biology", "maths",
        "algebra", "geometry", "internet", "website", "email", "smartphone",
        "ai", "machine learning", "deep learning", "blockchain", "ethereum",
        "solana", "web3", "nft", "token", "python", "javascript", "react", "html",
        "css", "database", "developer", "bug", "debugging", "compiler", "git",
        "github", "mars", "galaxy", "telescope", "nasa", "spacex", "kitchen",
        "bake", "fry", "chef", "restaurant", "tennis", "sports", "olympics",
        "athlete", "election", "government", "senate", "parliament", "democrat",
        "republican", "investment", "economics", "economy", "doctor", "hospital",
        "disease", "cancer", "vaccine", "anatomy", "physics", "physic",
        "cellphone", "app", "application", "chatgpt", "openai", "claude",
        "gemini", "copilot", "star wars", "star trek", "movie", "cinema",
        "actor", "hollywood", "bollywood", "netflix"
    ]
    # Check if any out-of-scope term is present in the query
    for term in OUT_OF_SCOPE_TERMS:
        if re.search(r"\b" + re.escape(term) + r"\b", lower):
            return True
    return False

CORE_MUSICOLOGY_KEYWORDS = [
    "raga","ragam","raaga","tala","thala","swara","shruti","shruthi","gamaka","alapana",
    "carnatic","karnatik","hindustani","music","song","kriti","krithi","varnam",
    "pallavi","anupallavi","charanam","melapakarta","melakarta","janya","arohana",
    "ragamalika","tukkada","mangalam",
    "avarohana","composer","composed","composers","who composed","who was","composition","compositions",
    "tyagaraja","dikshitar","purandaradasa","annamacharya","samaja","gamana","vara","vathapi","bhajare","manasa",
    "endaro","mahanubhavulu","nagumomu","vatapi","brochevarevarura","broche","pancharatna",
    "bhairavi","kalyani","hindolam","mohanam","mohana","shankarabharanam","sankarabharanam","todi","thodi","hanumatodi","manji","kambhoji",
    "hamsadhwani","revati","madhyamavati","bilahari","natabhairavi","charukesi",
    "saveri","begada","kedaram","anandabhairavi","ritigowla","sriranjani","vasanta",
    "sahana","mukhari","nattai","varali","punnagavarali","nilambari","devagandhari",
    "nalinakanti","jayantasri","abhogi","amritavarshini","kiravani","arabhi",
    "harikambhoji","bowli","suddhasaveri","sriranjani","kharaharapriya","nattai",
    "abheri",
    "geetam","swarajati","javali","tillana","thillana","padam","keerthana","devaranama",
    "manodharma","sangeetam","niraval","kalpana","tanam","trinity","saint",
    "instrument","veena","mridangam","violin","ghatam","flute","venu","nadaswaram",
    "concert","performance","recital","bhakti","devotional","classical","tradition",
    "sruthi","nada","sruti","sapta","saptha","adi","rupaka","misra","khanda",
    "tisra","chatusra","sankirna","laghu","drutam","anudrutam",
    "prayoga","sanchara","fundamental","important","significance","kattai","rakti",
    "laya","layas","vadya","vadyas","percussion", "morsing", "tambura", "tanpura",
    "sangeetha", "sangeetham", "sangeet", "kutcheri", "avartanam", "nadai", "gati",
    "lakshana", "lakshya", "kirtana", "sing", "singer", "singing", "musician",
    "musicians", "swaras", "svaras", "rtp", "tanam", "dasa", "purandhara", "yaman",
    "bilawal", "thaat", "system", "systems", "western",
    "recording", "recordings", "performance", "performances", "concert", "concerts", "youtube", "video", "videos", "watch",
    "semmangudi", "lalgudi", "balamuralikrishna", "subbulakshmi", "sanjay", "krishna", "tmk", "yesudas",
    "sheshagopalan", "seshagopalan", "sudha", "ragunathan", "jayashri", "ranjani", "gayatri", "parichayam",
    "kalpanaswaram", "swarakalpana", "grahabhedam", "graha bhedam", "modal shift", "jeeva", "nyasa", "graha", "syama", "sastri", "shastri",
    "naadam", "nadam", "sangeetham", "sangeetam", "sthayi", "purvanga", "uttaranga",
    "dhatu", "matu", "dhatuvu", "matuvu", "akshara kala", "trikala", "tourya trikama",
    "jaati", "jaatis", "pancha jaatis", "avartham", "angas", "shadangas", "talangas", "sapta talas",
    "suddha", "madhyamam", "prati", "achala", "chala", "vadi", "samvadi", "anuvadi", "vivadi", "varnam", "tanam", "manodharma", "chittaswaram", "sahityam", "muktayi", "swaram",
    "tiruvaiyaru", "tiruvarur", "thanjavur", "aradhana", "born", "lived", "where is", "located", "location",
    "dasha pranas", "dasha prana", "dasha vidha", "amsha", "apanyasa", "alpatva", "bahutva",
    "shadava", "audava", "varja", "vakra", "mandra sthayi", "tara sthayi", "sampurna"
]


def _is_in_domain(q: str) -> bool:
    lower = q.lower()
    # If a valid raga is recognized in the query, it is by definition in-domain!
    if _extract_raga(q):
        return True
        
    import re
    for kw in CORE_MUSICOLOGY_KEYWORDS:
        if re.search(r"\b" + re.escape(kw) + r"s?\b", lower):
            return True
    return False

def normalize_spelling(text: str) -> str:
    return text.lower().replace("th", "t").replace("sh", "s").replace("ee", "i").replace("aa", "a").replace("-", " ").strip()

def _extract_raga(q: str) -> str | None:
    lower = q.lower()
    q_norm = normalize_spelling(q)
    
    aliases = {
        "todi": "Todi",
        "thodi": "Todi",
        "hanumatodi": "Todi",
        "mohana": "Mohanam",
        "sankarabharanam": "Shankarabharanam",
        "kamavardhani": "Pantuvarali",
    }
    
    for alias, standard in aliases.items():
        if re.search(r"\b" + re.escape(alias) + r"s?\b", lower) or re.search(r"\b" + re.escape(normalize_spelling(alias)) + r"s?\b", q_norm):
            return standard

    import backend.services.database_loader as db_loader
    all_ragas = list(set([r.get("name", "").lower() for r in db_loader.RAGAS] + RAGA_NAMES))
    all_ragas = [r for r in all_ragas if r and r not in ("melakarta", "melakartha")]

    # Sort raga names by length descending to prevent prefix/substring matching issues (e.g. Bhairavi vs Anandabhairavi)
    sorted_ragas = sorted(all_ragas, key=len, reverse=True)
    
    # 1. Exact match on normalized strings
    for r in sorted_ragas:
        r_norm = normalize_spelling(r)
        if re.search(r"\b" + re.escape(r_norm) + r"s?\b", q_norm):
            matched_raga = db_loader.find_raga(r)
            if matched_raga:
                return matched_raga["name"]
            return r.title()
            
    return None


def _resolve_coreferences(parts: list[str]) -> list[str]:
    if len(parts) <= 1:
        return parts

    import backend.services.database_loader as db_loader
    
    composer_found = None
    comp_found = None
    raga_found = None
    
    resolved = []
    
    for idx, p in enumerate(parts):
        resolved_p = p
        
        # 1. Resolve pronouns in current part using accumulated context
        if idx > 0:
            # Replace composer pronouns
            if composer_found:
                resolved_p = re.sub(r"\bhis\b", f"{composer_found}'s", resolved_p, flags=re.IGNORECASE)
                resolved_p = re.sub(r"\btheir\b", f"{composer_found}'s", resolved_p, flags=re.IGNORECASE)
                resolved_p = re.sub(r"\bhe\b", composer_found, resolved_p, flags=re.IGNORECASE)
                resolved_p = re.sub(r"\bthey\b", composer_found, resolved_p, flags=re.IGNORECASE)
                resolved_p = re.sub(r"\bhim\b", composer_found, resolved_p, flags=re.IGNORECASE)
                
            # Replace composition/raga pronouns
            if comp_found:
                resolved_p = re.sub(r"\b(it|its|this composition|this song)\b", comp_found, resolved_p, flags=re.IGNORECASE)
            elif raga_found:
                resolved_p = re.sub(r"\b(it|its|this raga)\b", raga_found, resolved_p, flags=re.IGNORECASE)
                
        # 2. Extract new entities from the resolved part to update the context for downstream parts
        p_lower = resolved_p.lower()
        
        # Look for known compositions in resolved_p
        for track in db_loader.TRACKS:
            song = track.get("song_name", "")
            clean_song = song.split(" - ")[0].split("_")[0].strip()
            if len(clean_song) > 3 and clean_song.lower() in p_lower:
                comp_found = clean_song
                break
                
        if not comp_found:
            for raga in db_loader.RAGAS:
                for comp in raga.get("compositions", []):
                    name = comp.get("name", "")
                    if len(name) > 3 and name.lower() in p_lower:
                        comp_found = name
                        break
                if comp_found:
                    break

        # Look for known composers in resolved_p
        composer_names = ["tyagaraja", "dikshitar", "syamaastri", "syama sastri", "purandaradasa", "swathi thirunal", "annamacharya"]
        for c in composer_names:
            if c in p_lower:
                composer_found = c.title()
                break
        if not composer_found:
            if "trinity" in p_lower:
                composer_found = "the Trinity of Carnatic music"

        # Look for raga names in resolved_p
        raga_in_p = _extract_raga(resolved_p)
        if raga_in_p:
            raga_found = raga_in_p
            
        resolved.append(resolved_p)
        
    return resolved


def split_multi_questions(query: str) -> list[str]:
    raw_parts = _split_multi_questions_raw(query)
    return _resolve_coreferences(raw_parts)


def _split_multi_questions_raw(query: str) -> list[str]:
    lower = query.lower().strip()
    
    # Guard: Comparison/difference queries should NEVER be split
    if any(w in lower for w in ["difference between", "compare", "versus", "vs", "differentiate", "contrast"]):
        return [query]

    # Guard: Raga scale list/explain queries should NEVER be split
    if any(w in lower for w in ["raga", "ragas", "ragam", "ragams"]) and any(w in lower for w in ["scale", "scales", "arohana", "avarohana"]):
        return [query]

    # Split by newlines/bullet points if input has multiple lines
    if '\n' in query:
        parts = []
        for line in query.split('\n'):
            line_clean = line.strip().lstrip('*-•').strip()
            if line_clean:
                parts.append(line_clean)
        if len(parts) > 1:
            return parts

    # First, split by question mark
    questions = re.split(r'\?+', query)
    questions = [x.strip() for x in questions if x.strip()]
    if len(questions) > 1:
        return questions

    # ── Multi-raga list detection ─────────────────────────────────────────────
    # Pattern: "Introduce/Explain/Tell me about X, Y and Z" where X,Y,Z are raga names
    import backend.services.database_loader as db_loader
    all_raga_names = set(RAGA_NAMES)
    # Add DB ragas for detection
    try:
        all_raga_names.update(r.get("name", "").lower() for r in db_loader.RAGAS if r.get("name"))
    except Exception:
        pass

    intro_triggers = ["introduce", "parichayam", "tell me about", "explain", "describe", "about"]
    is_multi_intro = any(t in lower for t in intro_triggers)
    
    if is_multi_intro:
        found_ragas = [r for r in all_raga_names if r and re.search(r"\b" + re.escape(r) + r"\b", lower) and len(r) > 3]
        # Sort by length descending to match longer names first (e.g. "anandabhairavi" before "bhairavi")
        found_ragas = sorted(set(found_ragas), key=len, reverse=True)
        # Deduplicate: remove ragas that are substrings of already-found ragas
        unique_ragas = []
        for r in found_ragas:
            if not any(r != other and r in other for other in found_ragas):
                unique_ragas.append(r)
        
        if len(unique_ragas) >= 2:
            # Determine the intro verb used
            action = "Introduce"
            for t in ["parichayam", "introduce"]:
                if t in lower:
                    action = "Introduce"
                    break
            for t in ["explain", "describe", "tell me about"]:
                if t in lower:
                    action = "Explain"
                    break
            # Re-order ragas in the order they appear in the original query
            ordered = sorted(unique_ragas, key=lambda r: lower.find(r))
            return [f"{action} {r.title()} raga" for r in ordered]

    # ── Multi-composer list detection ─────────────────────────────────────────
    composer_names = ["tyagaraja", "dikshitar", "muthuswami", "syama", "sastri", "purandaradasa",
                      "swathi", "thirunal", "annamacharya", "oottukkadu", "papanasam", "subramania"]
    if any(t in lower for t in ["who is", "tell me about", "explain", "describe", "bio"]):
        found_composers = [c for c in composer_names if re.search(r"\b" + re.escape(c) + r"\b", lower)]
        if len(found_composers) >= 2:
            return [f"Who is {c.title()}?" for c in found_composers]

    # ── Paired theory concept detection ──────────────────────────────────────
    THEORY_CONCEPT_TERMS = [
        "niraval", "kalpanaswaram", "alapana", "tanam", "gamaka", "shruti", "tala",
        "melakarta", "janya", "alpatva", "bahutva", "shadava", "audava", "varja", "vakra",
        "graha swara", "nyasa swara", "jeeva swara", "amsha", "apanyasa", "graha bhedam",
        "arohana", "avarohana", "varnam", "kriti", "pallavi", "anupallavi", "charanam",
        "tukkada", "mangalam", "tillana", "ragamalika", "sapta talas", "concert structure",
        "concert format", "concert sequence"
    ]
    if any(t in lower for t in ["explain", "what is", "define", "describe"]):
        if "arohana" in lower and "avarohana" in lower:
            pass
        else:
            found_concepts = [c for c in THEORY_CONCEPT_TERMS if re.search(r"\b" + re.escape(c) + r"\b", lower)]
            if len(found_concepts) >= 2:
                # Only split if they appear to be listed (joined by "and", comma, etc.)
                # Don't split if it's a single comparison: "difference between X and Y"
                action = "Explain" if "explain" in lower else ("Define" if "define" in lower else "What is")
                return [f"{action} {c}?" for c in found_concepts]

    # ── Coordinated sub-questions (original logic) ────────────────────────────
    if len(questions) == 1:
        q = questions[0]
        split_pattern = r'\b(?:and|as well as|but also|,)\s+(?=(?:who|which|what|how|show|play|introduce|recommend|give|write|list|can\s+you|describe|explain|define)\b)'
        parts = re.split(split_pattern, q, flags=re.IGNORECASE)
        parts = [p.strip() for p in parts if p.strip()]
        if len(parts) > 1:
            return parts
            
    return questions


def route_query(query: str) -> RouterResult:
    q = query.strip()
    lower = q.lower()

    # ── Domain gate ──────────────────────────────────────────────────────────
    # Check for multiple questions
    questions = split_multi_questions(q)
    if len(questions) > 1:
        return RouterResult(mode="multiple_questions")

    if _is_out_of_scope(q) or not _is_in_domain(q):
        return RouterResult(mode="rejected")

    raga      = _extract_raga(q)
    audio     = any(t in lower for t in AUDIO_TRIGGERS)
    t_score   = sum(1 for t in THEORY_TRIGGERS if t in lower)
    m_score   = sum(1 for t in MUSIC_TRIGGERS  if t in lower)

    # ── Intent Classifier ────────────────────────────────────────────────────
    intent = "GENERAL"
    shruti_filter = None

    # Dynamically query against the master artists list
    import backend.services.database_loader as db_loader
    
    # Exclude raga names, talas, and key domain terminology from triggering artist matches
    exclude_artist_words = set(RAGA_NAMES) | set(DOMAIN_KEYWORDS) | {
        "raga", "ragam", "tala", "thala", "laya", "swara", "shruti", "shruthi", 
        "kalyani", "bhairavi", "hindolam", "mohanam", "todi", "shankarabharanam", 
        "hamsadhwani", "ritigowla", "anandabhairavi", "bilahari", "kambhoji", 
        "charukesi", "nattai", "devi", "priya", "saraswathi", "lakshmi", "ganesh",
        "first", "second", "third", "live", "best", "great", "music", "vocal", 
        "instrumental", "classic", "saint", "group", "ensemble", "vocalist", "perform",
        "performance", "record", "recording", "artist", "singer", "famous", "popular"
    }
    
    artist_names = [
        a.get("name", "").lower() for a in db_loader.ARTISTS 
        if a.get("name", "").lower() not in exclude_artist_words
    ]
    artist_words = set()
    for name in artist_names:
        for w in name.split():
            w_clean = w.strip().lower()
            if len(w_clean) > 3 and w_clean not in exclude_artist_words:
                artist_words.add(w_clean)
    
    has_yt_keyword = any(w in lower for w in ["youtube", "video", "watch", "recording", "performance", "recordings", "performances"])
    has_artist_or_comp = (
        any(re.search(rf"\b{re.escape(a)}\b", lower) for a in ["tyagaraja", "dikshitar", "syama", "purandaradasa", "semmangudi", "lalgudi", "balamurali", "subbulakshmi", "ms subbulakshmi", "m s subbulakshmi", "tm krishna", "t m krishna", "tmk", "yesudas", "ranjani", "sudha", "sanjay", "seshagopalan", "jayashri", "aruna", "endaro", "vatapi", "broche", "nagumomu", "balagopala", "viriboni", "ninnukori", "kamalambam"])
        or any(re.search(rf"\b{re.escape(a)}\b", lower) for a in artist_names)
        or any(re.search(rf"\b{re.escape(w)}\b", lower) for w in artist_words)
    )

    THEORY_CONCEPTS_LIST = [
        "sruthi", "sruti", "shruthi", "shruti", "naadam", "nadam", "sangeetham", "sangeetam",
        "swara", "saptha swaras", "sapta swaras", "dwadasa swarasthanas", "arohana", "avarohana",
        "moorchana", "sthayi", "purvanga", "uttaranga", "dhatu", "matu", "dhatuvu", "matuvu",
        "akshara kala", "trikala", "tourya trikama", "jaati", "pancha jaatis", "avartham",
        "angas", "shadangas", "talangas", "sapta talas", "melakarta", "melakartha",
        "suddha madhyamam", "prati madhyamam", "achala swara", "chala swara", "vadi", "samvadi",
        "anuvadi", "vivadi", "achala swaras", "chala swaras", "vadi swara", "samvadi swara",
        "anuvadi swara", "vivadi swara", "tanam", "tanam singing", "ragam alapana", "alapana",
        "manodharma", "manodharma sangeetham", "manodharma sangeetam", "varnam", "varnam structure",
        "pada varnam", "tana varnam", "madhyamakala sahityam", "chittaswaram", "muktayi swaram",
        "muktayi", "charanam", "niraval", "graha bhedam", "grahabhedam", "modal shift",
        # Dasha Pranas
        "dasha pranas", "dasha prana", "dasha vidha", "ten characteristics", "ten attributes",
        "ten pranas", "raga lakshana", "raga lakshanas", "dasha vidha lakshana",
        "amsha", "amsha swara", "apanyasa", "alpatva", "bahutva",
        "shadava", "audava", "varja", "vakra", "vakra swara",
        "sampurna", "mandra sthayi", "tara sthayi", "hexatonic", "pentatonic",
        # Newly added theory concept terms
        "ragam tanam pallavi", "rtp", "gamaka", "gamakas", "gamakam", "gamakams",
        "rakti ragas", "rakti raga", "rakti", "concert structure", "concert format",
        "concert sequence", "katcheri paddhati", "katcheri", "cutcherry", "kriti",
        "krithi", "tillana", "thillana", "sapta talas", "suladi sapta talas",
        "sapta tala", "suladi sapta tala", "ragamalika", "mangalam", "tukkada",
        "pallavi", "kalpana swara", "kalpanaswaram", "swarakalpana",
        "concert", "katcheri", "sequence", "format", "structure", "anatomy", "construction"
    ]
    is_exam_theory = any(c in lower for c in THEORY_CONCEPTS_LIST) and any(t in lower for t in ["what is", "what are", "define", "explain", "short note", "write a note", "write a short note", "briefly explain", "differentiate", "compare", "list", "name", "how is", "vs", "difference", "structure", "how to", "how do", "performed", "how", "meaning of", "explain about", "define about", "describe", "describe about", "tell me about", "introduce", "introduce about"])

    # ── Composition Info Interceptor ──────────────────────────────────────────
    is_comp_info = any(w in lower for w in ["who composed", "composed by", "composer of", "which raga is", "raga of", "ragam of", "which tala is", "tala of", "talam of", "which thala is", "thala of", "thalam of", "set in", "set to", "tala used in", "talam used in"])

    # ── List Ragas by Scale Type Interceptor ───────────────────────────────
    is_list_ragas = any(w in lower for w in ["shadava", "audava", "sampurna", "sampoorna", "hexatonic", "pentatonic", "heptatonic"]) and any(w in lower for w in ["list", "example", "explain", "show", "give", "name", "what are", "what is", "define", "describe"])

    # ── List General Ragas and Scales Interceptor ──────────────────────────
    is_list_ragas_and_scales = (
        any(w in lower for w in ["list", "example", "examples", "show", "give", "name", "what are", "what is", "define", "describe", "explain", "introduce", "tell me about"])
        and any(w in lower for w in ["raga", "ragas", "ragam", "ragams"])
        and any(w in lower for w in ["scale", "scales", "arohana", "avarohana", "swara", "swaras", "note", "notes", "structure"])
    )

    if is_list_ragas:
        intent = "LIST_RAGAS_BY_SCALE"
    elif is_list_ragas_and_scales:
        intent = "LIST_RAGAS_AND_SCALES"
    elif is_comp_info:
        intent = "COMPOSITION_INFO"
    elif ("melakarta" in lower or "melakartha" in lower) and raga and any(w in lower for w in ["number", "which", "what is", "#", "no.", "position"]):
        # "Which melakarta number is Bhairavi?" → RAGA_SCALE (lookup specific raga)
        intent = "RAGA_SCALE"
    elif "melakarta" in lower or "melakartha" in lower:
        intent = "THEORY_CONCEPT_QUERY"
    elif any(w in lower for w in ["evolution", "history of", "origin of"]) and any(w in lower for w in ["music", "carnatic"]):
        intent = "THEORY_CONCEPT_QUERY"
    elif any(k in lower for k in ["ragam tanam pallavi", "rtp", "ragam tanam"]):
        if any(w in lower for w in ["recording", "performance", "recommend", "suggest", "youtube", "play", "listen"]):
            intent = "RECORDING_RECOMMENDATION"
        else:
            intent = "RTP_QUERY"
    elif any(k in lower for k in ["pancharatna", "pancha ratna", "five gems"]):
        intent = "PANCHARATNA_QUERY"
    elif is_exam_theory and not raga:
        intent = "THEORY_CONCEPT_QUERY"
    elif any(w in lower for w in ["compare", "difference", "differentiate", "distinguish", "different", "vs", "versus"]):
        raga_matches = [r for r in RAGA_NAMES + ["manji"] if re.search(r"\b" + re.escape(r) + r"\b", lower)]
        composer_matches = [c for c in ["tyagaraja", "dikshitar", "sastri", "syama", "purandaradasa", "swathi", "thirunal", "annamacharya"] if c in lower]
        tala_matches = [t for t in ["adi", "rupaka", "ata", "triputa", "eka", "chapu", "misra", "khanda"] if t in lower]
        instrument_matches = [i for i in ["veena", "violin", "mridangam", "flute", "venu", "ghatam", "kanjira"] if i in lower]
        system_matches = [s for s in ["carnatic", "karnatik", "hindustani", "western", "indian classical"] if s in lower]
        
        if len(system_matches) >= 2 or (system_matches and any(w in lower for w in ["system", "music", "tradition"])):
            intent = "MUSIC_SYSTEM_COMPARISON"
        elif len(raga_matches) >= 2 or (raga_matches and "raga" in lower):
            intent = "RAGA_COMPARISON"
        elif len(composer_matches) >= 2 or (composer_matches and "composer" in lower):
            intent = "COMPOSER_COMPARISON"
        elif tala_matches or "tala" in lower:
            intent = "TALA_COMPARISON"
        elif instrument_matches or "instrument" in lower:
            intent = "INSTRUMENT_COMPARISON"
        else:
            intent = "COMPARISON"
    elif any(k in lower for k in ["arohana", "avarohana", "arohanam", "avarohanam", "scale"]):
        intent = "RAGA_SCALE"
    elif any(re.search(rf"\b{re.escape(t)}\b", lower) for t in ["adi", "rupaka", "ata", "triputa", "eka", "chapu", "misra", "khanda", "dhruva", "matya", "jhampa"]) and any(re.search(rf"\b{re.escape(w)}\b", lower) for w in ["tala", "talam", "thala", "thalam"]):
        intent = "TALA_QUERY"

    # ── WHY Questions ── MUST come BEFORE recording check to avoid misrouting ──────────────────
    elif "why" in lower.split() and any(w in lower for w in ["fundamental", "important", "significance", "considered", "kalyani", "mayamalavagowla", "sankarabharanam", "todi", "thodi", "beginner"]):
        intent = "RAGA_IMPORTANCE"
    elif "why" in lower.split():
        intent = "WHY_QUESTION"

    # ── Audio / Recording Intent ───────────────────────────────────────────
    elif (has_yt_keyword or "singing" in lower or "rendition" in lower or "render" in lower) and (raga or has_artist_or_comp):
        intent = "YOUTUBE_RECORDING"
    elif raga and has_artist_or_comp:
        intent = "YOUTUBE_RECORDING"

    # ── Theory Concepts ────────────────────────────────────────────────────
    elif any(k in lower for k in ["define raga", "define tala", "define shruti", "define shruthi", "lakshana", "define purandaradasa", "define tyagaraja", "define dikshitar", "define syama", "graha bhedam", "grahabhedam", "modal shift", "niraval", "kalpanaswaram", "swarakalpana", "jeeva swara", "nyasa swara", "graha swara", "melakarta", "melakartha"]):
        intent = "THEORY_CONCEPT_QUERY"

    # ── Shruti/Pitch Intent ────────────────────────────────────────────────
    elif (
        re.search(r"\d+(?:\.\d+)?\s*(?:kattai|shruthi|shruti)", lower)
        or any(f"{i} kattai" in lower for i in range(1, 8))
        or ("shruti" in lower and any(w in lower for w in ["what is", "define", "explain", "value", "1", "2", "3", "4", "5", "6", "7"]))
        or ("kattai" in lower and any(w in lower for w in ["full", "table", "list", "all", "complete", "reference", "chart"]))
        or lower.strip() in ("kattai", "kattai system", "shruti system", "shruti kattai")
    ):
        intent = "SHRUTI_QUERY"
    elif any(w in lower for w in ["audio", "play", "sound"]):
        intent = "AUDIO_QUERY"
    elif any(w in lower for w in ["prayoga", "characteristic phrase", "sanchara", "phraseology", "characteristic phrases", "melodic phrase", "melodic idiom"]):
        intent = "PRAYOGA"
    elif (
        "alapana" in lower and any(w in lower for w in [
            "elaborate", "suitable", "which raga", "guide", "how to", "how do", "explain",
            "rendition", "perform", "practice", "begin", "start", "structure", "approach"
        ])
    ):
        intent = "ALAPANA"
    elif any(w in lower for w in ["fundamental", "importance", "significant", "considered", "why is"]):
        intent = "RAGA_IMPORTANCE"
    elif any(w in lower for w in ["starting note", "graha swara", "begin on", "start on", "graha"]):
        intent = "STARTING_NOTE"
    elif "group" in lower and "shruti" in lower:
        intent = "GROUP_BY_SHRUTI"
    elif audio or "recommend" in lower or "suggest" in lower:
        intent = "RECORDING_RECOMMENDATION"
    elif any(g in lower for g in ["gamaka", "kampita", "jaru", "janta", "nokku", "spurita", "pratyahata", "ornamentation"]):
        intent = "GAMAKA"
    elif "arohana" in lower or "avarohana" in lower:
        intent = "AROHANA_AVAROHANA"
    elif any(w in lower for w in ["where", "location", "located", "birthplace", "born in", "place of birth", "native place", "native of", "where is", "where was"]):
        intent = "LOCATION_QUERY"
    elif any(w in lower for w in ["evolution", "history of", "origin of"]) and any(w in lower for w in ["music", "carnatic"]):
        intent = "THEORY_CONCEPT_QUERY"
    elif any(w in lower for w in ["when", "date", "year", "celebrated", "aradhana", "live", "lived", "born", "died", "birth", "death", "timeline", "period", "century"]):
        intent = "TIME_QUERY"
    elif any(w in lower for w in ["tyagaraja", "dikshitar", "sastri", "syama", "purandaradasa", "swathi", "thirunal", "annamacharya", "composer", "composed", "composers", "who composed", "who was"]):
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
    elif any(k in lower for k in [
        "parichayam",
        "raga parichayam",
        "raga introduction",
        "introduction",
        "overview",
        "briefly explain",
        "short note on",
        "about raga",
        "introduce"
    ]) and raga:
        intent = "RAGA_INFO"
    elif raga:
        intent = "RAGA_INFO"

    if audio and raga:
        mode = "hybrid"
    elif intent in ["COMPOSITION", "RECORDING", "GROUP_BY_SHRUTI", "YOUTUBE_RECORDING", "AUDIO_QUERY", "RECORDING_RECOMMENDATION", "COMPOSITION_INFO"]:
        mode = "music"
    elif intent == "THEORY_CONCEPT_QUERY":
        mode = "theory"
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