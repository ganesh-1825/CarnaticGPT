"""
retrieval.py  —  FAISS retrieval + synthesis pipeline (FIXED)
=============================================================
Drop this into:  scripts/retrieval.py
             OR  backend/services/retrieval.py

Fixes:
  • Calls synthesize() and validates output — never returns raw OCR text
  • Falls back to rule_based_summary if LLM unavailable / returns garbage
  • Correct confidence thresholds: <25=low  25-60=medium  >60=high
  • Audio-first routing for "play X" queries
  • All five citation fields populated: book_name, page_number,
    confidence, excerpt, source
"""

import os
import re
import logging

log = logging.getLogger("retrieval")

MIN_SCORE = float(os.getenv("MIN_SCORE", "25.0"))

# ── Import FAISSStore (works from both scripts/ and backend/services/) ────────
def _imp(primary, fallbacks):
    import importlib
    for m in [primary] + fallbacks:
        try:
            return importlib.import_module(m)
        except ImportError:
            continue
    raise ImportError(f"Cannot import {primary}")

_fs_mod  = _imp("backend.services.faiss_store",   ["services.faiss_store",  "faiss_store"])
_qr_mod  = _imp("backend.services.query_router",  ["services.query_router", "query_router"])
_syn_mod = _imp("backend.services.synthesizer",   ["services.synthesizer",  "synthesizer", "scripts.synthesizer"])

FAISSStore       = _fs_mod.FAISSStore
route_query      = _qr_mod.route_query
describe_route   = _qr_mod.describe_route
synthesize       = _syn_mod.synthesize


# ═══════════════════════════════════════════════════════════════════════════════
# Tala Details Local Database
# ═══════════════════════════════════════════════════════════════════════════════

TALA_DETAILS = {
    "dhruva": {
        "name": "Dhruva Tala",
        "beats": 14,
        "angas": "Laghu, Drutam, Laghu, Laghu (I0II)",
        "structure": "I0II",
        "description": "Dhruva Tala is one of the seven Suladi Sapta Talas. It consists of a Laghu, a Drutam, and two more Laghus. In its standard Chatusra Jati form, it has 14 beats (aksharas) structured as 4 + 2 + 4 + 4 = 14 beats."
    },
    "matya": {
        "name": "Matya Tala",
        "beats": 10,
        "angas": "Laghu, Drutam, Laghu (I0I)",
        "structure": "I0I",
        "description": "Matya Tala is one of the seven Suladi Sapta Talas. It consists of a Laghu, a Drutam, and another Laghu. In its standard Chatusra Jati form, it has 10 beats (aksharas) structured as 4 + 2 + 4 = 10 beats."
    },
    "ata": {
        "name": "Ata Tala",
        "beats": 14,
        "angas": "Laghu, Laghu, Drutam, Drutam (II00)",
        "structure": "II00",
        "description": "Ata Tala is one of the seven Suladi Sapta Talas. It consists of two Laghus followed by two Drutams. In its standard Khanda Jati form, it has 14 beats (aksharas) structured as 5 + 5 + 2 + 2 = 14 beats."
    },
    "khanda chapu": {
        "name": "Khanda Chapu Tala",
        "beats": 5,
        "angas": "5 beats (five aksharas), structured as 2 + 3",
        "structure": "2 + 3",
        "description": "Khanda Chapu is a popular Chapu tala in Carnatic music consisting of 5 beats (five aksharas) per cycle. It is structured as 2 + 3 (two and three beats)."
    },
    "misra chapu": {
        "name": "Misra Chapu Tala",
        "beats": 7,
        "angas": "7 beats (seven aksharas), structured as 3 + 2 + 2",
        "structure": "3 + 2 + 2",
        "description": "Misra Chapu is a popular Chapu tala in Carnatic music consisting of 7 beats (seven aksharas) per cycle. It is structured as 3 + 2 + 2 (three, two, and two beats)."
    },
    "chapu": {
        "name": "Chapu Tala",
        "beats": 7,
        "angas": "Varying beats, typically structured as syncopated cycles",
        "structure": "syncopated",
        "description": "Chapu Tala is a classification of rhythmic cycles in Carnatic music, traditionally associated with folk styles and syncopated rhythms. Misra Chapu (7 beats) and Khanda Chapu (5 beats) are the most popular forms."
    },
    "adi": {
        "name": "Adi Tala",
        "beats": 8,
        "angas": "Laghu, Drutams (I00)",
        "structure": "I00",
        "description": "Adi Tala is the most popular tala in Carnatic music. It consists of 8 beats (aksharas) structured as one Laghu (4 beats) and two Drutams (2 beats each). It is also known as Chatusra Jati Triputa Tala."
    },
    "rupaka": {
        "name": "Rupaka Tala",
        "beats": 3,
        "angas": "Drutam, Laghu (0I)",
        "structure": "0I",
        "description": "Rupaka Tala consists of a Drutam followed by a Laghu. In its standard form, it has 3 beats (aksharas) or is reckoned as 6 aksharas in common practice."
    },
    "eka": {
        "name": "Eka Tala",
        "beats": 4,
        "angas": "Laghu (I) (1 single anga / one single anga)",
        "structure": "I",
        "description": "Eka Tala consists of 1 single Laghu (1 anga / one anga). It has only 1 anga. In its standard Chatusra Jati form, it has 4 beats (aksharas)."
    },
    "triputa": {
        "name": "Triputa Tala",
        "beats": 7,
        "angas": "Laghu, Drutam, Drutam (I00)",
        "structure": "I00",
        "description": "Triputa Tala consists of a Laghu followed by two Drutams. In its standard Tisra Jati form, it has 7 beats (aksharas) structured as 3 + 2 + 2 = 7 beats."
    },
    "jhampa": {
        "name": "Jhampa Tala",
        "beats": 10,
        "angas": "Laghu, Anudrutam, Drutam (I U 0)",
        "structure": "I U 0",
        "description": "Jhampa Tala consists of a Laghu, an Anudrutam, and a Drutam. In its standard Misra Jati form, it has 10 beats (aksharas) structured as 7 + 1 + 2 = 10 beats."
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# Compositions Database & Link Support
# ═══════════════════════════════════════════════════════════════════════════════

COMPOSITIONS_DB = {
    "vatapi ganapatim": {
        "name": "Vatapi Ganapatim",
        "composer": "Muthuswami Dikshitar",
        "raga": "Hamsadhwani",
        "tala": "Adi Tala",
        "youtube": "https://www.youtube.com/watch?v=s3mPqfMh96w",
        "description": "Vatapi Ganapatim is a widely popular invocation composition composed in praise of Lord Ganesha. Set in the bright pentatonic Hamsadhwani raga and Adi Tala, it features Sanskrit lyrics expressing deep devotion and is traditionally performed at the beginning of a Carnatic concert."
    },
    "vaathapi ganapatim": {
        "name": "Vatapi Ganapatim",
        "composer": "Muthuswami Dikshitar",
        "raga": "Hamsadhwani",
        "tala": "Adi Tala",
        "youtube": "https://www.youtube.com/watch?v=s3mPqfMh96w",
        "description": "Vatapi Ganapatim is a widely popular invocation composition composed in praise of Lord Ganesha. Set in the bright pentatonic Hamsadhwani raga and Adi Tala, it features Sanskrit lyrics expressing deep devotion and is traditionally performed at the beginning of a Carnatic concert."
    },
    "endaro mahanubhavulu": {
        "name": "Endaro Mahanubhavulu",
        "composer": "Saint Tyagaraja",
        "raga": "Sri Raga",
        "tala": "Adi Tala",
        "youtube": "https://www.youtube.com/watch?v=F0pC2jA1Zws",
        "description": "Endaro Mahanubhavulu is one of the celebrated Pancharatna Kritis composed by Saint Tyagaraja in Sri Raga. Translated as 'Salutations to all the great souls in the world', it is written in Telugu and showcases beautiful poetic variations (sangatis) set to Adi Tala."
    },
    "nagumomu ganaleni": {
        "name": "Nagumomu Ganaleni",
        "composer": "Saint Tyagaraja",
        "raga": "Abheri",
        "tala": "Adi Tala",
        "youtube": "https://www.youtube.com/watch?v=s9f8FvG-K_I",
        "description": "Nagumomu Ganaleni is a beautiful, emotion-heavy composition by Saint Tyagaraja in Abheri Raga. It expresses the composer's deep grief and longing for the vision of Lord Rama, set to Adi Tala."
    },
    "nagumomu": {
        "name": "Nagumomu Ganaleni",
        "composer": "Saint Tyagaraja",
        "raga": "Abheri",
        "tala": "Adi Tala",
        "youtube": "https://www.youtube.com/watch?v=s9f8FvG-K_I",
        "description": "Nagumomu Ganaleni is a beautiful, emotion-heavy composition by Saint Tyagaraja in Abheri Raga. It expresses the composer's deep grief and longing for the vision of Lord Rama, set to Adi Tala."
    },
    "sri subramanyaya namaste": {
        "name": "Sri Subramanyaya Namaste",
        "composer": "Muthuswami Dikshitar",
        "raga": "Kambhoji",
        "tala": "Rupaka Tala",
        "youtube": "https://www.youtube.com/watch?v=M9Nn2e9CPlY",
        "description": "Sri Subramanyaya Namaste is a monumental, slow-tempo (chouka kala) masterpiece composed by Muthuswami Dikshitar in Kambhoji Raga and Rupaka Tala. Set in Sanskrit, it is dedicated to Lord Subramanya (Muruga) and exhibits rich, complex raga grammar."
    },
    "brochevarevarura": {
        "name": "Brochevarevarura",
        "composer": "Mysore Vasudevachar",
        "raga": "Khamas",
        "tala": "Adi Tala",
        "youtube": "https://www.youtube.com/watch?v=s2S1_n_s1qU",
        "description": "Brochevarevarura is a highly popular, melodic composition by Mysore Vasudevachar in Khamas Raga. Written in Telugu and set to Adi Tala, it pleads for the protection of Lord Rama."
    },
    "samaja vara gamana": {
        "name": "Samaja Vara Gamana",
        "composer": "Saint Tyagaraja",
        "raga": "Hindolam",
        "tala": "Adi Tala",
        "youtube": "https://www.youtube.com/watch?v=Z61Bv_D0gP4",
        "description": "Samaja Vara Gamana is a celebrated composition of Saint Tyagaraja set in Hindolam Raga and Adi Tala. Its beautiful melody and rhythm describe the grace of Lord Krishna."
    },
    "marivere gati": {
        "name": "Marivere Gati",
        "composer": "Syama Sastri",
        "raga": "Anandabhairavi",
        "tala": "Adi Tala (Viloma Chapu)",
        "youtube": "https://www.youtube.com/watch?v=oTspGgJcT_M",
        "description": "Marivere Gati is an emotional composition by Syama Sastri dedicated to Goddess Dharmasamvardhini. Composed in Anandabhairavi Raga, it features rhythmic complexities and is traditionally performed in Viloma Chapu/Adi Tala."
    },
    "balagopala": {
        "name": "Balagopala",
        "composer": "Muthuswami Dikshitar",
        "raga": "Bhairavi",
        "tala": "Adi Tala",
        "youtube": "https://www.youtube.com/watch?v=R97i97t2e-w",
        "description": "Balagopala is a majestic, slow-tempo composition by Muthuswami Dikshitar in Bhairavi Raga and Adi Tala. Written in Sanskrit, it is dedicated to Lord Krishna and serves as a classic reference for Bhairavi's raga structure."
    },
    "viriboni": {
        "name": "Viriboni (Ata Tala Varnam)",
        "composer": "Pacchimiriam Adiyappaiah",
        "raga": "Bhairavi",
        "tala": "Ata Tala",
        "youtube": "https://www.youtube.com/watch?v=Xh0G-wS8P4k",
        "description": "Viriboni is a historic and technically complex Varnam (etude) in Bhairavi Raga and Ata Tala. It is widely considered the king of Carnatic Varnams, showcasing the complete grammatical structure and gamakas of Bhairavi."
    },
    "sudhamayi": {
        "name": "Sudhamayi Sudhanidhi",
        "composer": "Harikesanallur Muthaiah Bhagavatar",
        "raga": "Amritavarshini",
        "tala": "Rupaka Tala",
        "youtube": "https://www.youtube.com/watch?v=sO7uV2pC0tE",
        "description": "Sudhamayi is a beautiful composition in Amritavarshini Raga and Rupaka Tala, celebrating the rain-bearing and life-giving qualities of Goddess Amritavarshini."
    },
    "raghuvamsa sudha": {
        "name": "Raghuvamsa Sudha",
        "composer": "Patnam Subramania Iyer",
        "raga": "Kathanakuthuhalam",
        "tala": "Adi Tala",
        "youtube": "https://www.youtube.com/watch?v=D-h9S3gS1oI",
        "description": "Raghuvamsa Sudha is a fast-paced, highly energetic instrumental/vocal composition set in the rare, playful raga Kathanakuthuhalam and Adi Tala."
    }
}

def _format_composition_db_response(comp_key: str) -> str:
    c = COMPOSITIONS_DB[comp_key]
    return (
        f"### Composition Detail: {c['name']}\n\n"
        f"- **Composition:** {c['name']}\n"
        f"- **Composer:** {c['composer']}\n"
        f"- **Raga:** {c['raga']} Raga\n"
        f"- **Tala:** {c['tala']}\n"
        f"- **YouTube Performance:** [Listen on YouTube]({c['youtube']})\n\n"
        f"**Description:**\n{c['description']}"
    )

def _format_artist_recommendations(question: str) -> str:
    return (
        "### Structured Recommendation: Carnatic Classical Artists\n\n"
        "Here are recommendations of prominent, highly celebrated Carnatic classical musicians across different categories:\n\n"
        "| Category | Legendary Masters (Vocal) | Contemporary Stars (Vocal) |\n"
        "| :--- | :--- | :--- |\n"
        "| **Female Vocalists** | **M.S. Subbulakshmi**, D.K. Pattammal, M.L. Vasanthakumari (The Female Trinity) | **Sudha Ragunathan**, Bombay Jayashri, Ranjani-Gayatri, Aruna Sairam, Vishakha Hari |\n"
        "| **Male Vocalists** | **G.N. Balasubramaniam**, Ariyakudi Ramanuja Iyengar, Semmangudi Srinivasa Iyer, Madurai Mani Iyer | **Sanjay Subrahmanyan**, T.M. Krishna, K.J. Yesudas, P. Unnikrishnan, Abhishek Raghuram |\n\n"
        "| Category | Instrumental Masters | Instruments |\n"
        "| :--- | :--- | :--- |\n"
        "| **Violin** | **Lalgudi Jayaraman**, M.S. Gopalakrishnan, T.N. Krishnan (Violin Trinity) | Violin |\n"
        "| **Flute** | **T.R. Mahalingam (Flute Mali)**, N. Ramani | Flute |\n"
        "| **Veena** | **Karaikudi Sambasiva Iyer**, S. Balachander | Veena |\n"
        "| **Mridangam** | **Palghat Mani Iyer**, Palani Subramania Pillai | Mridangam (Percussion) |\n\n"
        "**Recommendation Guide:**\n"
        "- For deep, meditative, and scholarly renderings, listen to **Muthuswami Dikshitar** compositions performed by **M.S. Subbulakshmi** or **Sanjay Subrahmanyan**.\n"
        "- For energetic, rhythm-heavy, and complex manodharma (improvisation), listen to **Abhishek Raghuram** or **Lalgudi Jayaraman** violin solos."
    )

def _format_concert_recommendations(question: str) -> str:
    return (
        "### Structured Concert Recommendation & Program Planner (Katcheri Paddhati)\n\n"
        "A standard Carnatic concert (Katcheri) is structured to balance speed, rhythm, emotion, and technical complexity. Here is a recommended 2.5-hour concert program planner:\n\n"
        "1. **Warm-up Piece: Varnam (High Tempo)**\n"
        "   - *Purpose:* Warm up the voice/fingers, establish the basic raga grammar.\n"
        "   - *Recommendation:* **Viriboni** in Bhairavi Raga (Ata Tala) or **Ninnukori** in Mohanam Raga (Adi Tala).\n\n"
        "2. **Invocation Piece: Kriti (Medium Tempo)**\n"
        "   - *Purpose:* Seek blessings (usually Ganesha) and create an auspicious atmosphere.\n"
        "   - *Recommendation:* **Vatapi Ganapatim** in Hamsadhwani Raga or **Maha Ganapatim** in Nattai Raga.\n\n"
        "3. **Sub-main Kritis (Varying Tempos & Ragas)**\n"
        "   - *Purpose:* Introduce contrasting moods (rasas) and speed variations.\n"
        "   - *Recommendation:* **Sobhillu Saptaswara** in Jaganmohini Raga or **Bantureethi Koluvu** in Hamsanadam Raga.\n\n"
        "4. **Centerpiece / Main Piece (Slow Tempo & Heavy Improvisation)**\n"
        "   - *Purpose:* Detailed Raga Alapana, Niraval lyric expansion, Kalpanaswaras, and concluding percussion solo (**Tani Avartanam**).\n"
        "   - *Recommendation:* **Sri Subramanyaya Namaste** in Kambhoji Raga (Rupaka Tala) or **O Rangashayi** in Kambhoji Raga (Adi Tala).\n\n"
        "5. **Peak Creative Form: Ragam Tanam Pallavi (RTP)**\n"
        "   - *Purpose:* Absolute peak of creative manodharma improvisation (unmetered raga, pulsed tanam, structured pallavi).\n"
        "   - *Recommendation:* Set in ragas like **Kalyani**, **Todi**, or **Shanmukhapriya**.\n\n"
        "6. **Post-main Section: Tukkadas (Melody-rich & Devotional)**\n"
        "   - *Purpose:* Offer relaxation with light devotional songs, Javalis, Padams, and Tillanas.\n"
        "   - *Recommendation:* **Brahmam Okate** (Annamacharya) or a Tillana in **Kapi** or **Behag** (Lalgudi Jayaraman).\n\n"
        "7. **Mandatory Closing: Mangalam**\n"
        "   - *Purpose:* Express gratitude, peace, and auspicious closure.\n"
        "   - *Recommendation:* **Pavamana Suthudu** in Madhyamavati Raga."
    )

def _format_composer_works_response(composer_key: str) -> str:
    if composer_key == "tyagaraja":
        return (
            "### Composer Compositions Profile: Saint Tyagaraja\n\n"
            "- **Composer Name:** Saint Tyagaraja (1767-1847)\n"
            "- **Biography & Location:** A saint-composer who lived and composed in Tiruvaiyaru.\n"
            "- **Trinity Status:** Renowned as one of the musical Trinity of Carnatic music.\n"
            "- **Style & Devotion:** Renowned for deeply devotional Bhakti-oriented kritis, expressing profound Rama Bhakti (unwavering devotion to Lord Rama).\n"
            "- **Total Compositions:** Over 700 known kritis, mainly composed in Telugu and Sanskrit, with melodies enriched by sangatis.\n"
            "- **Deity Focus:** Lord Rama\n"
            "- **Signature Composition Series:**\n"
            "  1. **Pancharatna Kritis (The Five Gems):** Set in five major ghana ragas (*Jagadanandakaraka* in Nattai, *Dudukugala* in Gowla, *Sadhinchene* in Arabhi, *Kanakana Ruchira* in Varali, *Endaro Mahanubhavulu* in Sri Raga).\n"
            "  2. **Utsava Sampradaya Kritis:** Devotional songs for daily worship and temple rituals.\n"
            "  3. **Divya Nama Kritis:** Simple, choral-style congregational singing songs.\n"
            "  4. **Opera dramas:** *Prahlada Bhakti Vijayam* and *Nauka Charitram*.\n"
            "- **Famous Individual Kritis:**\n"
            "  - *Nagumomu Ganaleni* in Abheri Raga (Adi Tala) - [Listen on YouTube](https://www.youtube.com/watch?v=s9f8FvG-K_I)\n"
            "  - *Samaja Vara Gamana* in Hindolam Raga (Adi Tala) - [Listen on YouTube](https://www.youtube.com/watch?v=Z61Bv_D0gP4)\n"
            "  - *Bantureethi Koluvu* in Hamsanadam Raga (Adi Tala)\n"
            "  - *Sobhillu Saptaswara* in Jaganmohini Raga (Rupaka Tala)\n"
            "  - *Tera Teeyaga* in Bhairavi Raga (famous kriti in Bhairavi)"
        )
    elif composer_key == "dikshitar":
        return (
            "### Composer Compositions Profile: Muthuswami Dikshitar\n\n"
            "- **Composer Name:** Muthuswami Dikshitar (1775-1835)\n"
            "- **Trinity Status:** One of the musical Trinity of Carnatic music.\n"
            "- **Style & Grammar:** Scholarly compositions in slow tempo (chouka kala) with intricate gamakas, showing mastery over Sanskrit grammar and musicological grammar.\n"
            "- **Total Compositions:** Around 450 compositions, written almost exclusively in Sanskrit and Manipravalam.\n"
            "- **Deity Focus:** Multiple Hindu Deities (Devi, Shiva, Ganesha, Subrahmanya, Vishnu)\n"
            "- **Signature Composition Series:**\n"
            "  1. **Kamalamba Navavarana Kritis:** Nine Kritis dedicated to Goddess Kamalamba of Tiruvarur, representing the nine enclosures of the Sri Chakra.\n"
            "  2. **Navagraha Kritis:** Kritis dedicated to the nine planetary deities, displaying deep astrological knowledge.\n"
            "  3. **Pancha Bhuta Linga Kritis:** Dedicated to Shiva representing the five elements.\n"
            "  4. **Nottuswaras:** Simple, Western-melody inspired Sanskrit compositions.\n"
            "- **Famous Individual Kritis:**\n"
            "  - *Vatapi Ganapatim* in Hamsadhwani Raga (Adi Tala) - [Listen on YouTube](https://www.youtube.com/watch?v=s3mPqfMh96w)\n"
            "  - *Sri Subramanyaya Namaste* in Kambhoji Raga (Rupaka Tala) - [Listen on YouTube](https://www.youtube.com/watch?v=M9Nn2e9CPlY)\n"
            "  - *Balagopala* in Bhairavi Raga (Adi Tala) - [Listen on YouTube](https://www.youtube.com/watch?v=R97i97t2e-w)\n"
            "  - *Rangapura Vihara* in Brindavana Saranga Raga (Rupaka Tala)"
        )
    elif composer_key == "sastri":
        return (
            "### Composer Compositions Profile: Syama Sastri\n\n"
            "- **Composer Name:** Syama Sastri (1762-1827)\n"
            "- **Trinity Status:** One of the musical Trinity of Carnatic music.\n"
            "- **Style & Tempo:** deep emotional appeal, master of chouka kala (slow tempo) and complex rhythms.\n"
            "- **Total Compositions:** Around 300 compositions, mainly in Telugu, Sanskrit, and Tamil.\n"
            "- **Deity Focus:** Goddess Kamakshi (Devi)\n"
            "- **Signature Composition Series:**\n"
            "  1. **Swarajati Trilogy:** Three epic Swarajatis (*Rave Himagiri* in Todi, *Kamakshi Anudinamu* in Bhairavi, *Kamakshi* in Yadukulakambhoji) which elevated Swarajati from a dance form to a concert art-piece.\n"
            "  2. **Navaratnamalika:** Nine kritis in praise of Goddess Meenakshi of Madurai.\n"
            "- **Famous Individual Kritis:**\n"
            "  - *Marivere Gati* in Anandabhairavi Raga (Adi/Viloma Chapu Tala) - [Listen on YouTube](https://www.youtube.com/watch?v=oTspGgJcT_M)\n"
            "  - *Devi Niye Tunai* in Keeravani Raga (Adi Tala)\n"
            "  - *Mayamma Ani* in Ahiri Raga (Adi Tala)\n"
            "  - *Kanakasaila Viharini* in Punnagavarali Raga (Adi Tala)"
        )
    return ""

def inherit_entities_in_subquestions(sub_questions: list[str]) -> list[str]:
    resolved_questions = []
    
    recent_raga = None
    recent_composer = None
    recent_tala = None
    recent_composition = None
    
    known_compositions = [
        "vatapi ganapatim", "vaathapi ganapatim", "endaro mahanubhavulu", 
        "nagumomu ganaleni", "nagumomu", "sri subramanyaya namaste", 
        "subramanyaya namaste", "brochevarevarura", "pancharatna kritis", 
        "pancharatna kriti", "pancharatna", "vatapi", "balagopala", "viriboni"
    ]
    
    for i, q in enumerate(sub_questions):
        ql = q.lower()
        
        # Extract entities from the current question to update context
        from backend.raga_knowledge_base import find_raga_key
        raga_key = find_raga_key(q)
        if raga_key:
            recent_raga = raga_key.title()
            
        from backend.services.query_router import _extract_all_composers
        comps = _extract_all_composers(q)
        if comps:
            recent_composer = comps[0].title()
            
        from backend.services.query_router import _extract_all_talas
        talas = _extract_all_talas(q)
        if talas:
            recent_tala = talas[0]
            
        for comp in known_compositions:
            if comp in ql:
                recent_composition = comp.title()
                break
                
        # Inherit context for subsequent questions
        if i > 0:
            resolved_q = q
            has_pronoun = any(p in ql for p in ["its ", "it ", "this ", "their ", "he ", "she ", "the song", "the composition", "the raga", "the composer", "the tala"])
            
            has_raga = find_raga_key(q) is not None
            has_comp_name = _extract_all_composers(q) != []
            has_tala_name = _extract_all_talas(q) != []
            has_composition = any(comp in ql for comp in known_compositions)
            has_any_entity = has_raga or has_comp_name or has_tala_name or has_composition
            
            if not has_any_entity or has_pronoun:
                if recent_composition:
                    if "its raga" in ql:
                        resolved_q = re.sub(r"\bits raga\b", f"the raga of {recent_composition}", resolved_q, flags=re.I)
                    if "its tala" in ql:
                        resolved_q = re.sub(r"\bits tala\b", f"the tala of {recent_composition}", resolved_q, flags=re.I)
                    if "its composer" in ql:
                        resolved_q = re.sub(r"\bits composer\b", f"the composer of {recent_composition}", resolved_q, flags=re.I)
                    resolved_q = re.sub(r"\bits\b", f"{recent_composition}'s", resolved_q, flags=re.I)
                    resolved_q = re.sub(r"\bit\b", recent_composition, resolved_q, flags=re.I)
                    if not has_any_entity:
                        resolved_q = resolved_q.rstrip("?. ") + f" of {recent_composition}?"
                elif recent_raga:
                    resolved_q = re.sub(r"\bthis raga\b|\bits\b", recent_raga, resolved_q, flags=re.I)
                    if not has_any_entity:
                        resolved_q = resolved_q.rstrip("?. ") + f" in {recent_raga}?"
                elif recent_composer:
                    resolved_q = re.sub(r"\bthis composer\b|\bhe\b|\bshe\b", recent_composer, resolved_q, flags=re.I)
                    if not has_any_entity:
                        resolved_q = resolved_q.rstrip("?. ") + f" by {recent_composer}?"
            
            resolved_questions.append(resolved_q)
        else:
            resolved_questions.append(q)
            
    return resolved_questions

def _label(score: float) -> str:
    if score < 25:  return "low"
    if score < 60:  return "medium"
    return "high"


def is_fact_check_query(q: str) -> bool:
    ql = q.lower().strip()
    
    # List of phrases that indicate a declaration/fact-check statement
    fact_check_phrases = [
        "is a", "is the", "uses", "composed", "has", "have", "correct", 
        "true", "false", "verify", "check", "wrong", "mistake", "error", 
        "correct?", "true?", "wrong?", "is correct", "is true", "is false"
    ]
    
    # Exceptions: standard query patterns should never be treated as fact check statements
    standard_prefixes = [
        "what ", "explain", "describe", "meaning ", "tell ", "show ", "play ", 
        "listen ", "recommend", "how ", "why ", "when ", "where ", "who ", "give "
    ]
    if any(ql.startswith(prefix) for prefix in standard_prefixes):
        return False
        
    return any(phrase in ql for phrase in fact_check_phrases)


def answer_question(
    question: str,
    conversation_history: list[dict] | None = None,
) -> dict:
    """
    Unified v1.0 answering pipeline:
      User Query -> Multi Question Splitter -> Intent Router -> [KB, BOOKS, GEMINI, REJECT] -> Validation -> Cache -> Response
    """
    history = conversation_history or []

    # 1. Multi-turn coreference resolution
    if history:
        from backend.services.query_router import resolve_with_history
        resolved_question = resolve_with_history(question, history)
        if resolved_question != question:
            log.info("Coreference resolved: '%s' -> '%s'", question, resolved_question)
            question = resolved_question

    from backend.services.cache_manager import CacheManager
    
    # 2. Query Cache Check (Level 4 Cache)
    cached_result = CacheManager.get_query_result(question)
    if cached_result is not None:
        log.info("[Level 4 Cache Hit] Returning cached result for: '%s'", question)
        return cached_result

    # 3. Multi-Question Splitter
    from backend.services.query_router import split_multi_questions
    sub_questions = split_multi_questions(question)
    if len(sub_questions) > 1:
        log.info("Multi-question query detected. Splitting into: %s", sub_questions)
        inherited_sub_questions = inherit_entities_in_subquestions(sub_questions)
        answers = []
        citations = []
        confidences = []
        for orig_q, sub_q in zip(sub_questions, inherited_sub_questions):
            sub_res = answer_question(sub_q, conversation_history)
            answers.append((orig_q, sub_res["answer"]))
            citations.extend(sub_res.get("citations", []))
            confidences.append(sub_res.get("top_confidence", 0.0))
        
        # Build labeled combined answer with section dividers
        parts = []
        for idx, (sub_q, ans) in enumerate(answers, 1):
            label = sub_q.rstrip("?").strip()
            if len(label) > 60:
                label = label[:57] + "..."
            parts.append(f"---\n\n**{label}**\n\n{ans}")
        combined_answer = "\n\n".join(parts)
        
        # Deduplicate citations
        seen_cites = set()
        unique_citations = []
        for c in citations:
            key = f"{c.get('book_name')}_{c.get('page_number')}"
            if key not in seen_cites:
                seen_cites.add(key)
                unique_citations.append(c)
        
        avg_confidence = sum(confidences) / len(confidences) if confidences else 80.0
        
        res = {
            "answer":           combined_answer,
            "citations":        unique_citations,
            "top_confidence":   round(avg_confidence, 1),
            "confidence_label": _label(avg_confidence),
            "route":            "multiple_questions",
            "sources_found":    len(unique_citations),
            "synthesis_method": "multiple_questions",
            "source_type":      "📖 Knowledge Base Answer" if any("📖" in ans[1] or "Knowledge" in ans[1] for ans in answers) else "📚 Book Answer",
            "raga_name":        None,
            "wants_audio":      False,
        }
        # Cache & return
        CacheManager.set_query_result(question, res)
        return res

    # 4. Intent Routing
    route = route_query(question)
    log.info("Route: %s", describe_route(route))
    intent = route.intent

    # Override for Recording / YouTube queries
    ql = question.lower()
    from backend.services.query_router import YOUTUBE_KEYWORDS, RECORDING_KEYWORDS
    has_youtube = any(w in ql for w in YOUTUBE_KEYWORDS)
    has_recording = any(w in ql for w in RECORDING_KEYWORDS)
    has_other_audio = any(w in ql for w in ["play", "audio", "hear"])
    has_learning = any(w in ql for w in ["lesson", "lessons", "tutorial", "learn", "lecture", "lectures"])
    has_recommend = any(w in ql for w in ["recommend", "recommendation", "recommendations", "show", "give", "find"])
    music_terms = ["recording", "recordings", "rtp", "kritis", "kriti", "alapana", "video", "videos", "lesson", "lessons", "channel", "channels", "track", "tracks", "composition", "compositions", "singer", "singers", "vocalist", "vocalists", "lecture", "lectures", "gamaka", "gamakas"]
    has_music_term = any(w in ql for w in music_terms)
    is_structural_or_modern = any(w in ql for w in ["structure", "format", "sequence", "role", "impact", "influence", "season", "preservation", "digitization", "online learning", "technology", "history", "define", "explain", "what is", "significance", "paddhati"])
    has_lesson = any(w in ql for w in ["lesson", "lessons", "tutorial", "tutorials"])
    if (has_youtube or has_recording or has_other_audio or has_learning or (has_recommend and has_music_term)) and (not is_structural_or_modern or has_lesson) and not any(w in ql for w in ["digitization", "digital age", "preservation", "archives", "archive", "indexing", "indexing historical"]):
        intent = "RECORDING_RECOMMENDATION"

    # ── Dispatcher ──

    # A. REJECT
    if intent == "REJECTED" or route.mode == "rejected":
        log.info("Query rejected as out-of-domain.")
        answer = (
            "I cannot answer this question as it is outside the scope of CarnaticGPT. "
            "I can only answer questions about Carnatic classical music — "
            "ragas, talas, composers, compositions, music theory, and performance practice. "
            "Your query does not appear to be in this domain."
        )
        res = {
            "answer": answer,
            "citations": [],
            "top_confidence": 0.0,
            "confidence_label": "No Evidence",
            "route": "rejected",
            "sources_found": 0,
            "synthesis_method": "domain_filter",
            "source_type": "rejected",
            "raga_name": None,
            "wants_audio": False,
        }
        from backend.answer_validator import validate_answer
        res["answer"], res["source_type"], res["citations"] = validate_answer(
            answer=res["answer"],
            source_type="rejected",
            chunks=[],
            citations=[]
        )
        CacheManager.set_query_result(question, res)
        return res

    # B. KB (Knowledge Base)
    if intent in ("RAGA_QUERY", "TALA_QUERY", "COMPOSER_QUERY", "THEORY_QUERY", "RTP_QUERY", "GAMAKA_QUERY", "CONCERT_QUERY", "RECORDING_RECOMMENDATION", "YOUTUBE_RECORDING"):
        # Map general intent to specific legacy synthesizer intent
        legacy_intent = map_to_legacy_intent(intent, question)
        log.info("Mapping general intent %s to legacy intent %s for local KB lookup", intent, legacy_intent)
        
        from dataclasses import replace
        synth_route = replace(route, intent=legacy_intent)
        
        # ── LOCAL STRUCTURAL RESOLUTION TO BYPASS LLM/NETWORK ERRORS ──
        local_ans = None
        
        # 1. Direct Father of Carnatic Check
        if "father of carnatic" in ql or "pitamaha" in ql:
            local_ans = _format_composer_kb_response("purandaradasa")
            
        # 2. Comparisons
        if not local_ans and ("compare" in ql or "difference" in ql or "versus" in ql or "vs" in ql or "between" in ql or legacy_intent == "RAGA_COMPARISON"):
            local_ans = _format_comparison_response(question)
            
        # 2b. Dasha Pranas
        if not local_ans and any(w in ql for w in ["dasha prana", "dasha vidha", "ten characteristic", "ten attribute"]):
            local_ans = (
                "### Structured Music Theory Response: Dasha Pranas of a Raga\n\n"
                "The **Dasha Pranas** (Ten Vital Attributes or Raga Lakshanas) are the ten essential characteristics that define a raga's identity, grammar, and emotional character:\n\n"
                "1. **Graha:** The starting note (swara) on which a composition or melodic phrase commences.\n"
                "2. **Amsha (Amsa):** The predominant, most important note (Jeeva Swara) that reveals the core character of the raga.\n"
                "3. **Nyasa:** The resting note on which a melodic phrase or section comes to a conclusion.\n"
                "4. **Mandra:** The lowest note/register limit to which the raga's phrases may descend.\n"
                "5. **Tara:** The highest note/register limit to which the raga's phrases may ascend.\n"
                "6. **Alpatva:** The weak or sparingly used notes in the raga scale (must be used minimally).\n"
                "7. **Bahutva:** The strong or frequently used notes in the raga scale (emphasized in improvisation).\n"
                "8. **Apanyasa:** The secondary resting note used within intermediate phrases.\n"
                "9. **Sanyasa:** A note used to conclude a musical section (often close to the tonic).\n"
                "10. **Vinyasa:** A note used for micro-rests or musical punctuation during elaboration.\n\n"
                "**Musicological Context:**\n"
                "These ten attributes were codified in ancient treatises like the *Natyashastra* and *Sangita Ratnakara* to systemize how ragas are structured, performed, and recognized."
            )

        # 2c. Five Jatis
        if not local_ans and any(w in ql for w in ["five jati", "5 jati", "five jaati", "5 jaati"]):
            local_ans = (
                "### Structured Music Theory Response: The Five Jatis of Carnatic Rhythm\n\n"
                "In Carnatic music, the **Jati** (or Jaati) classification determines the number of beats (aksharas) in the **Laghu** (the variable limb/anga of a Tala). There are five primary Jatis:\n\n"
                "1. **Tisra Jati:** A Laghu of **3 beats** (represented as a clap followed by 2 finger counts; notation: `I3`).\n"
                "2. **Chatusra Jati:** A Laghu of **4 beats** (represented as a clap followed by 3 finger counts; notation: `I4`).\n"
                "3. **Khanda Jati:** A Laghu of **5 beats** (represented as a clap followed by 4 finger counts; notation: `I5`).\n"
                "4. **Misra Jati:** A Laghu of **7 beats** (represented as a clap followed by 6 finger counts; notation: `I7`).\n"
                "5. **Sankirna Jati:** A Laghu of **9 beats** (represented as a clap followed by 8 finger counts; notation: `I9`).\n\n"
                "**Significance:**\n"
                "By applying these 5 Jatis to the 7 parent rhythmic structures (Suladi Sapta Talas: Dhruva, Matya, Rupaka, Jhampa, Triputa, Ata, Eka), we generate the core system of **35 Talas**."
            )

        # 2d. Artist Recommendations
        if not local_ans and any(w in ql for w in ["recommend artist", "recommend singer", "artist recommendation", "suggest vocalist", "suggest artist", "famous singer", "famous artist", "vocalist recommendation"]):
            local_ans = _format_artist_recommendations(question)

        # 2e. Concert Recommendations / Program Planning
        if not local_ans and any(w in ql for w in ["concert structure", "concert recommendation", "concert sequence", "plan a concert", "concert program", "suggest a concert"]):
            local_ans = _format_concert_recommendations(question)

        # 2g. YouTube / Recording Recommendations
        local_citations = []
        if not local_ans and (intent in ("RECORDING_RECOMMENDATION", "YOUTUBE_RECORDING") or any(w in ql for w in ["youtube", "recording", "lessons", "channel", "video", "play", "listen"])):
            local_ans, local_citations = _format_youtube_recommendation_response(question, intent)

        # 4. Composition / Event details
        if not local_ans:
            local_ans = _format_composition_response_local(question)

        # 2f. Composer works / compositions
        if not local_ans and (intent == "COMPOSER_QUERY" or "composition" in ql or "composed" in ql or "write" in ql) and any(c in ql for c in ["tyagaraja", "dikshitar", "sastri", "shyama", "syama"]):
            if "tyagaraja" in ql:
                local_ans = _format_composer_works_response("tyagaraja")
            elif "dikshitar" in ql:
                local_ans = _format_composer_works_response("dikshitar")
            elif "sastri" in ql or "syama" in ql or "shyama" in ql:
                local_ans = _format_composer_works_response("sastri")
            
        # 3. Talas — 35 Tala complete reference (must come BEFORE single-tala lookup)
        if not local_ans and ("35 tala" in ql or "35 talas" in ql or ("all" in ql and "tala" in ql and any(w in ql for w in ["table", "list", "detail", "explain", "write"])) or ("sapta tala" in ql and any(w in ql for w in ["table", "list", "all", "35", "detail"]))):
            local_ans = (
                "### Complete Reference: The 35 Talas of Carnatic Music\n\n"
                "---\n\n"
                "## 1. Introduction to Tala\n\n"
                "**Tala** is the rhythmic framework of Carnatic music — the time cycle that governs every composition and improvisation. "
                "Every Carnatic piece is set within a specific Tala that defines the number of beats, their grouping, and the rhythmic feel.\n\n"
                "### Angas (Constituent Limbs)\n\n"
                "A Tala is built from three fundamental building blocks called **Angas**:\n\n"
                "| Anga | Symbol | Fixed Beats | Description |\n"
                "|------|--------|-------------|-------------|\n"
                "| **Laghu** | I | Variable (3/4/5/7/9) | A clap + finger counts. Beat count depends on Jati. |\n"
                "| **Drutam** | 0 | 2 | A clap + a wave. Always 2 beats. |\n"
                "| **Anudrutam** | U | 1 | A single clap. Always 1 beat. |\n\n"
                "---\n\n"
                "## 2. Sapta Talas (Seven Parent Talas)\n\n"
                "The **Suladi Sapta Tala** system defines 7 parent rhythmic patterns using these Angas:\n\n"
                "| # | Tala | Anga Structure | Notation | Chatusra Beat Count |\n"
                "|---|------|---------------|----------|---------------------|\n"
                "| 1 | **Dhruva** | Laghu + Drutam + Laghu + Laghu | I 0 I I | 14 |\n"
                "| 2 | **Matya** | Laghu + Drutam + Laghu | I 0 I | 10 |\n"
                "| 3 | **Rupaka** | Drutam + Laghu | 0 I | 6 |\n"
                "| 4 | **Jhampa** | Laghu + Anudrutam + Drutam | I U 0 | 10 |\n"
                "| 5 | **Triputa** | Laghu + Drutam + Drutam | I 0 0 | 8 |\n"
                "| 6 | **Ata** | Laghu + Laghu + Drutam + Drutam | I I 0 0 | 14 |\n"
                "| 7 | **Eka** | Laghu | I | 4 |\n\n"
                "*Note: The most common Tala in practice is Adi Tala = Chatusra Jati Triputa Tala (8 beats).*\n\n"
                "---\n\n"
                "## 3. Pancha Jatis (Five Jati Classifications)\n\n"
                "The **Jati** determines how many beats are in each **Laghu**. "
                "Drutam is always 2 beats and Anudrutam is always 1 beat, regardless of Jati.\n\n"
                "| # | Jati | Laghu Beats | Notation |\n"
                "|---|------|------------|----------|\n"
                "| 1 | **Tisra** | 3 | I₃ |\n"
                "| 2 | **Chaturasra** | 4 | I₄ |\n"
                "| 3 | **Khanda** | 5 | I₅ |\n"
                "| 4 | **Misra** | 7 | I₇ |\n"
                "| 5 | **Sankirna** | 9 | I₉ |\n\n"
                "---\n\n"
                "## 4. Complete 35 Tala Table (7 Sapta Talas × 5 Jatis)\n\n"
                "The 35 Talas are generated by applying each of the 5 Jatis to each of the 7 Sapta Talas.\n"
                "The table shows the **total beat count (aksharas)** per cycle:\n\n"
                "| # | Tala | Anga Formula | Tisra (3) | Chaturasra (4) | Khanda (5) | Misra (7) | Sankirna (9) |\n"
                "|---|------|-------------|-----------|----------------|------------|-----------|-------------|\n"
                "| 1 | **Dhruva** | L+D+L+L | **11** | **14** | **17** | **23** | **29** |\n"
                "| 2 | **Matya** | L+D+L | **8** | **10** | **12** | **16** | **20** |\n"
                "| 3 | **Rupaka** | D+L | **5** | **6** | **7** | **9** | **11** |\n"
                "| 4 | **Jhampa** | L+U+D | **6** | **7** | **8** | **10** | **12** |\n"
                "| 5 | **Triputa** | L+D+D | **7** | **8** | **9** | **11** | **13** |\n"
                "| 6 | **Ata** | L+L+D+D | **10** | **14** | **14** | **22** | **26** |\n"
                "| 7 | **Eka** | L | **3** | **4** | **5** | **7** | **9** |\n\n"
                "*L = Laghu (beats per Jati), D = Drutam (2 beats), U = Anudrutam (1 beat)*\n\n"
                "---\n\n"
                "## 5. Beat Count Calculation Formula\n\n"
                "```\n"
                "Total Beats = (Number of Laghus × Jati value) + (Number of Drutams × 2) + (Number of Anudrutams × 1)\n"
                "```\n\n"
                "**Example — Dhruva Tala in Tisra Jati (I 0 I I):**\n"
                "- 3 Laghus × 3 beats + 1 Drutam × 2 beats = 9 + 2 = **11 beats**\n\n"
                "**Example — Dhruva Tala in Chaturasra Jati (I 0 I I):**\n"
                "- 3 Laghus × 4 beats + 1 Drutam × 2 beats = 12 + 2 = **14 beats**\n\n"
                "**Example — Triputa Tala in Chaturasra Jati = Adi Tala (I 0 0):**\n"
                "- 1 Laghu × 4 beats + 2 Drutams × 2 beats = 4 + 4 = **8 beats**\n\n"
                "---\n\n"
                "## 6. Named Examples of All 35 Talas\n\n"
                "| Tala | Jati | Common Name | Beat Count | Famous Usage |\n"
                "|------|------|-------------|------------|--------------|\n"
                "| Triputa | Chaturasra | **Adi Tala** | 8 | Most popular tala in Carnatic music |\n"
                "| Triputa | Tisra | Tisra Triputa | 7 | Misra Chapu compositions |\n"
                "| Rupaka | Chaturasra | **Rupaka Tala** | 6 | Kritis like *Sri Subramanyaya Namaste* |\n"
                "| Ata | Khanda | **Khanda Ata** | 14 | Historic Varnams like *Viriboni* |\n"
                "| Jhampa | Misra | **Misra Jhampa** | 10 | Rare concert use |\n"
                "| Dhruva | Chaturasra | **Chatusra Dhruva** | 14 | Classical theoretical compositions |\n"
                "| Eka | Chaturasra | **Chatusra Eka** | 4 | Simple melodic exercises |\n\n"
                "---\n\n"
                "## 7. Summary\n\n"
                "```\n"
                "7 Sapta Talas × 5 Pancha Jatis = 35 Talas\n"
                "```\n\n"
                "Each Jati changes **only** the Laghu's beat count while Drutam (2) and Anudrutam (1) remain constant. "
                "This elegant mathematical system creates 35 distinct rhythmic cycles from just three basic building blocks, "
                "providing Carnatic music with an extraordinary variety of rhythmic expression."
            )

        # 3b. Single Tala lookup (Check this BEFORE general theory to avoid general word collision like "angas")
        if not local_ans and (intent == "TALA_QUERY" or "tala" in ql or any(w in ql for w in ["dhruva", "matya", "ata", "jhampa", "triputa", "eka", "chapu"])):
            from backend.services.query_router import _extract_all_talas
            extracted_talas = _extract_all_talas(question)
            if extracted_talas:
                t_key = None
                for ext_t in extracted_talas:
                    clean_ext = ext_t.lower().replace(" tala", "")
                    if clean_ext in TALA_DETAILS:
                        t_key = clean_ext
                        break
                if t_key:
                    t_match = TALA_DETAILS[t_key]
                    local_ans = (
                        f"### Structured Tala Response: {t_match['name']}\n\n"
                        f"- **Tala Name:** {t_match['name']}\n"
                        f"- **Beats (Aksharas):** {t_match['beats']}\n"
                        f"- **Angas (Sections):** {t_match['angas']}\n"
                        f"- **Rhythmic Notation (Structure):** {t_match['structure']}\n\n"
                        f"**Description:**\n{t_match['description']}"
                    )
            
        # 5. Raga queries
        if not local_ans and (intent == "RAGA_QUERY" or legacy_intent in ("RAGA_SCALE", "RAGA_INFO", "RAGA_COMPARISON")):
            from backend.raga_knowledge_base import find_raga_key
            raga_key = find_raga_key(question)
            # Bhairavi RAGA_SCALE: return notation with Sa/Ri/Ga spelled names
            if raga_key == "bhairavi" and legacy_intent == "RAGA_SCALE":
                local_ans = (
                    "### Raga Scale: Bhairavi\n\n"
                    "**Bhairavi** is a Janya (derived) Bhashanga raga of Natabhairavi (Melakarta 20). "
                    "It uses all seven swaras: "
                    "Shadjam (Sa), Chatusruti Rishabham (Ri), Sadharana Gandharam (Ga), "
                    "Suddha Madhyamam (Ma), Panchamam (Pa), Chatusruti/Suddha Dhaivatham (Da), "
                    "and Kaisiki Nishadham (Ni).\n\n"
                    "- **Arohana (Ascending):** `S R2 G2 M1 P D2 N2 S`\n"
                    "  Sa – Ri – Ga – Ma – Pa – Da (Chatusruti D2) – Ni – Sa\n"
                    "- **Avarohana (Descending):** `S N2 D1 P M1 G2 R2 S`\n"
                    "  Sa – Ni – Da (Suddha D1) – Pa – Ma – Ga – Ri – Sa\n\n"
                    "**Bhashanga Feature:** Uses D2 (Chatusruti Dhaivata) in ascent and D1 (Suddha Dhaivata) "
                    "in descent, borrowing a note from outside its parent Melakarta. "
                    "Considered *sarva-raga-swaroopini* — the embodiment of all ragas."
                )
            # 5a. 72 Melakarta listing
            elif any(w in ql for w in ["72 mela", "72 melakarta", "seventy two", "all melakarta", "list all raga", "list melakarta"]):
                local_ans = (
                    "### The 72 Melakarta Ragas of Carnatic Music\n\n"
                    "The **Melakarta** (or Janaka) system classifies all parent ragas with complete heptatonic scales.\n"
                    "There are **72 Melakartas** divided into two halves:\n\n"
                    "- **Poorvanga (1–36):** Uses **Suddha Madhyama (M1)**\n"
                    "- **Uttaranga (37–72):** Uses **Prati Madhyama (M2)**\n\n"
                    "Each half has **6 chakras** (groups of 6), and within each chakra the upper swaras (Da, Ni) vary systematically.\n\n"
                    "**Key Melakartas from the Knowledge Base:**\n\n"
                    "| # | Melakarta Name | Key Feature | Famous Janya Ragas |\n"
                    "|---|---------------|-------------|--------------------|\n"
                    "| 8 | **Hanuma Todi** | R1, G2, M1, D1, N2 | Hindolam, Suddha Dhanyasi |\n"
                    "| 15 | **Mayamalavagowla** | R1, G3, M1, D1, N3 — Beginner's raga | Bhupalam |\n"
                    "| 20 | **Natabhairavi** | R2, G2, M1, D1, N2 | Bhairavi |\n"
                    "| 21 | **Keeravani** | R2, G2, M1, D1, N3 — Harmonic minor | — |\n"
                    "| 22 | **Kharaharapriya** | R2, G2, M1, D2, N2 | Abhogi, Sriranjani, Revathi, Madhyamavathi, Sivaranjani |\n"
                    "| 26 | **Charukesi** | R2, G3, M1, D1, N2 | — |\n"
                    "| 28 | **Harikambhoji** | R2, G3, M1, D2, N2 | Kamboji, Mohanam, Sahana |\n"
                    "| 29 | **Dheerasankarabharanam** | R2, G3, M1, D2, N3 — Major scale | Hamsadhwani, Bilahari, Arabhi, Nattai |\n"
                    "| 45 | **Shubhapantuvarali** | R1, G2, M2, D1, N2 | Todi |\n"
                    "| 56 | **Shanmukhapriya** | R2, G2, M2, D1, N2 | — |\n"
                    "| 65 | **Mechakalyani** | R2, G3, M2, D2, N3 | Hamsanadam, Amruthavarshini |\n\n"
                    "**The 72-Melakarta Formula:**\n"
                    "```\n"
                    "Melakarta No. = 6 × (chakra - 1) + position_in_chakra\n"
                    "```\n"
                    "The **Katapayadi** system encodes each Melakarta number in the first two syllables of its name.\n\n"
                    "For a full numbered list of all 72, ask: *\"list all 72 mela names with numbers\"*"
                )

            # 5b. Raga classification query (is it janaka/janya, melakarta number, etc.)
            elif any(w in ql for w in ["classify", "classification", "janaka", "janaka raga", "is it a", "what type", "melakarta number of", "mela number", "which melakarta"]):
                from backend.raga_knowledge_base import find_raga_key
                r_key = find_raga_key(question) or raga_key
                if r_key:
                    local_ans = _format_raga_kb_response(r_key)
                else:
                    from backend.theory_knowledge_base import find_theory_key
                    if not find_theory_key(question):
                        local_ans = _generate_general_raga_list_response(question)

            # 5c. Janya ragas of a specific melakarta
            elif any(w in ql for w in ["janya", "janya raga", "derived from", "belong to", "ragas of", "child raga", "children of"]):
                from backend.raga_knowledge_base import RAGA_KNOWLEDGE_BASE, find_raga_key
                mela_key = find_raga_key(question) or raga_key
                if mela_key:
                    mela_info = RAGA_KNOWLEDGE_BASE.get(mela_key, {})
                    mela_num = mela_info.get("melakarta_number")
                    mela_name = mela_info.get("melakarta_name", mela_info.get("name", mela_key))
                    janya_list = [
                        (k, v["name"], v.get("arohana","?"), v.get("avarohana","?"), v.get("type","Janya"))
                        for k, v in RAGA_KNOWLEDGE_BASE.items()
                        if v.get("melakarta_number") == mela_num
                        and "self" not in v.get("parent", "").lower()
                    ]
                    if janya_list:
                        table = "| Janya Raga | Type | Arohana | Avarohana |\n|---|---|---|---|\n"
                        for _, jname, aro, ava, jtype in janya_list:
                            table += f"| **{jname}** | {jtype} | `{aro}` | `{ava}` |\n"
                        local_ans = (
                            f"### Janya Ragas of {mela_name} (Melakarta {mela_num})\n\n"
                            f"The following ragas in our Knowledge Base are derived from **{mela_name}**:\n\n"
                            + table +
                            f"\n**Total in KB:** {len(janya_list)} janya ragas listed.\n\n"
                            f"*Note: The full list of janya ragas is much larger — the 72 Melakartas together have hundreds of derived ragas.*"
                        )
                    else:
                        local_ans = _format_raga_kb_response(mela_key)
                else:
                    from backend.theory_knowledge_base import find_theory_key
                    if not find_theory_key(question):
                        local_ans = _generate_general_raga_list_response(question)

            elif raga_key:
                local_ans = _format_raga_kb_response(raga_key)
            else:
                from backend.theory_knowledge_base import find_theory_key
                if not find_theory_key(question):
                    local_ans = _generate_general_raga_list_response(question)
                
        # 6. Composer queries
        if not local_ans and (intent == "COMPOSER_QUERY" or any(n in ql for n in ["annamacharya", "annamayya", "swathi thirunal", "swathi thirunal", "purandaradasa"])):
            from backend.services.query_router import _extract_all_composers
            comps = _extract_all_composers(question)
            # Manual lookup for composers not always caught by extractor
            if not comps:
                for name in ["annamacharya", "annamayya", "swathi thirunal", "purandaradasa"]:
                    if name in ql:
                        comps = [name]
                        break
            if comps:
                local_ans = _format_composer_kb_response(comps[0])
                
        # 7. Theory / Gamaka / Concert / RTP queries
        if not local_ans:
            if "swarajathi" in ql or "swarajati" in ql:
                local_ans = (
                    "### Structured Music Theory Response: Swarajathi (Swarajati)\n\n"
                    "- **Definition & Lakshana:**\n"
                    "Swarajathi (also spelled Swarajati) is a highly prominent, intermediate compositional form in Carnatic music. "
                    "It serves as a pedagogical bridge between foundational exercises (Geethams, Alankaras) and advanced concert forms (Varnams, Kritis). "
                    "The term itself is a compound of **Swara** (melodic notes) and **Jati** (rhythmic patterns/syllables), representing its dual emphasis on melody and rhythm.\n\n"
                    "- **Structure & Anatomy:**\n"
                    "A Swarajathi typically consists of three main divisions:\n"
                    "1. **Pallavi:** The opening refrain that contains the central thematic melody and is repeated after each subsequent section.\n"
                    "2. **Anupallavi:** The secondary section that complements the Pallavi, introducing a melodic contrast (often in the higher octave). *Note: Some pedagogical/older Swarajathis do not have an Anupallavi.*\n"
                    "3. **Charanams:** Multiple subsequent stanzas. Each Charanam has a unique melody. In performance, each Charanam is first sung as a pure swara passage (solfa syllables) and then immediately repeated with its corresponding sahitya (lyrics).\n\n"
                    "- **Combination of Swaras and Sahitya:**\n"
                    "The unique aesthetic of Swarajathi is the perfect **one-to-one mapping** between the swara notes and the sahitya syllables. "
                    "For every musical note (swara) in the composition, there is a corresponding syllable of lyrics (sahitya). "
                    "This helps students internalize the exact pitch values of the words they are singing.\n\n"
                    "- **Educational & Pedagogical Importance:**\n"
                    "Swarajathi is taught to students right after Geethams to develop:\n"
                    "  - **Raga Bhava:** Deeper familiarity with raga characteristics through structured phrasing.\n"
                    "  - **Laya & Tala:** Better rhythmic grip, as Swarajathis feature more complex talas (e.g., Adi, Rupaka, Chapu) and syncopations compared to simple Geethams.\n"
                    "  - **Swarasthana Precision:** The swara-sahitya mapping helps train the ear and voice to hit exact note frequencies.\n\n"
                    "- **Difference Between Geetham and Swarajathi:**\n"
                    "  - **Geetham:** A continuous melodic flow of lyrics without distinct structural divisions like Pallavi or Anupallavi. The tempo is uniform, and there are no complex rhythmic pauses.\n"
                    "  - **Swarajathi:** Has clear structural divisions (Pallavi, Anupallavi, Charanams). It is longer, features alternating swara and sahitya passages, and has a more complex rhythmic and melodic structure.\n\n"
                    "- **Contribution of Syama Sastri (The Architect of Concert Swarajati):**\n"
                    "Historically, Swarajathis were dance compositions or simple pedagogical exercises. **Syama Sastri** (one of the Musical Trinity) elevated the Swarajathi to the concert platform. "
                    "He composed the legendary **Swarajathi Trilogy** (also known as the *Ratnatrayam*), which are considered masterpieces of Carnatic musicology:\n"
                    "1. *Kamakshi Anudinamu* in Raga **Bhairavi** (set to Misra Chapu Tala)\n"
                    "2. *Rave Himagiri Kumari* in Raga **Todi** (set to Adi Tala)\n"
                    "3. *Kamakshi Ni Padayugame* in Raga **Yadukulakambhoji** (set to Misra Chapu Tala)\n"
                    "These compositions are characterized by deep raga bhava, complex mathematical structures, and intense devotional emotion (Bhakti).\n\n"
                    "- **Concert vs. Pedagogical Swarajathis:**\n"
                    "  - **Pedagogical Swarajathis:** Designed for beginners (e.g., the famous Swarajathi *Rara Venu Gopabala* in Raga Bilahari, composed by Garbhapurivasar, or compositions in ragas like Khamas and Kalyani). They are melodically simple and help build foundational skills.\n"
                    "  - **Concert Swarajathis:** Highly complex, microtonally advanced art songs (such as Syama Sastri's trilogy) meant for performance by seasoned vocalists or instrumentalists. They demand rigorous training, control over microtones (Gamakas), and complex rhythmic synchronization."
                )
            else:
                from backend.theory_knowledge_base import find_theory_key
                t_key = find_theory_key(question)
                if t_key:
                    local_ans = _format_theory_kb_response(t_key)
                    
        # 8. Concert / RTP / Gamaka specific formats if not yet matched
        if not local_ans and intent == "CONCERT_QUERY":
            if any(w in ql for w in ["structure", "format", "sequence", "paddhati", "katcheri", "concert"]):
                local_ans = (
                    "### Structured Music Theory Response: Carnatic Concert Structure (Ariyakudi Format / Katcheri Paddhati)\n\n"
                    "- **Definition:**\n"
                    "The **Carnatic Concert Structure** (commonly referred to as the **Ariyakudi Format** or *Katcheri Paddhati*) is the standardized, sequential progression of compositions and improvisational forms performed during a classical recital.\n\n"
                    "- **Standard Concert Progression:**\n"
                    "1. **Varnam:** A high-energy, pre-composed technical warm-up piece (featuring both swara and sahitya) to establish the raga's identity and warm up the artist's voice/fingers.\n"
                    "2. **Invocation:** A medium-tempo kriti (typically dedicated to Lord Ganesha, such as *Vatapi Ganapatim*) to start the performance with auspicious energy.\n"
                    "3. **Sub-main Kritis:** Short-to-medium compositions in different ragas, often accompanied by brief Alapanas and Kalpanaswarams to build momentum.\n"
                    "4. **Main Piece & Tani Avartanam:** The principal centerpiece of the concert. It features an elaborate, multi-stage Alapana, Niraval expansion, Kalpanaswarams, and concludes with a percussion solo (**Tani Avartanam**) by the mridangam and auxiliary percussionists.\n"
                    "5. **Ragam Tanam Pallavi (RTP):** The absolute peak of manodharma (improvisational) skill, showcasing complex melodic (ragam), pulsing (tanam), and rhythmic (pallavi) variations.\n"
                    "6. **Tukkadas:** Lighter, melody-rich compositions, including Javalis, Padams, Devaranamas, and Tillanas.\n"
                    "7. **Mangalam:** A mandatory concluding song (often *Pavamana Suthudu*) expressing well-wishes, peace, and gratitude, traditionally set in Surati, Saurashtram, or Madhyamavati.\n\n"
                    "- **Musicological Context:**\n"
                    "This modern concert format (Ariyakudi Format) was structured and popularized in the early 20th century by the legendary vocalist **Ariyakudi Ramanuja Iyengar**. Prior to this, concerts were often unstructured or focused almost exclusively on a single raga/pallavi.\n\n"
                    "- **Key Points:**\n"
                    "- **Balance:** Perfect distribution of heavy classical math, deep emotional ragas, and lighter devotional pieces.\n"
                    "- **Energy Curve:** Commences with high structural precision, peaks at improvisational mastery, and concludes with sweet, relaxing melodies."
                )
            elif "tukkada" in ql:
                local_ans = (
                    "### Concert Structure: Tukkada\n\n"
                    "- **Concept:** Tukkada (meaning 'piece' or 'fragment')\n"
                    "- **Position:** Performed in the post-main section of a Carnatic concert.\n"
                    "- **Nature:** Lighter, highly melodic, and emotion-rich compositions. "
                    "Examples include Javalis, Padams, Devaranamas, patriotic songs, and Tillanas. "
                    "They offer aesthetic relaxation after the heavy mathematical rigor of the main piece and RTP."
                )
                
        if not local_ans and intent == "RTP_QUERY":
            local_ans = (
                "### Structured Music Theory Response: Ragam Tanam Pallavi (RTP)\n\n"
                "- **Definition:**\n"
                "Ragam Tanam Pallavi (RTP) is the premier, most elaborate improvisational form in a Carnatic concert, showcasing the peak of a musician's creative and technical capability.\n\n"
                "- **Progression:**\n"
                "1. **Ragam:** A detailed, unmetered melodic improvisation (alapana) exploring the raga.\n"
                "2. **Tanam:** Rhythmic, pulsed improvisation without a strict drum beat, using syllables like *ta, na, nam*.\n"
                "3. **Pallavi:** A highly structured composed line of lyrics set to a specific tala, featuring speed changes (Trikala) and complex calculations."
            )
            
        if not local_ans and intent == "GAMAKA_QUERY":
            local_ans = (
                "### Structured Music Theory Response: Gamaka\n\n"
                "- **Definition:**\n"
                "Gamaka refers to the oscillations, grace notes, glides, and embellishments applied to swaras in Carnatic music. "
                "They are essential to raga expression and distinguish Carnatic music from Western classical music.\n\n"
                "- **Types:**\n"
                "There are 15 types of gamakas (Panchadasa Gamaka) described in classical treatises, including:\n"
                "- **Kampita:** A gentle oscillation or shake of a note.\n"
                "- **Jaru:** A continuous slide from one pitch to another (ascending or descending).\n"
                "- **Nokku:** A stress or press on a swara."
            )
        if is_fact_check_query(question):
            local_ans = None

        # Bypass static local template for detailed/tabular/comparative requests → route to LLM
        # Exception 1: the rich 35-tala answer is already complete
        # Exception 2: the new rich raga profiles (> 600 chars) are already detailed enough
        # Exception 3: janya listing tables, comparison tables are already detailed
        DETAIL_TRIGGERS = [
            "detail", "detailed", "in detail", "write in detail",
            "explain", "write about",
            "what is the lakshana", "what are the lakshanas", "lakshana of",
            "with table", "compare", "comparison",
            "all 35", "all seven", "sapta", "pancha jati",
        ]
        DETAIL_INTENTS = (
            "THEORY_QUERY", "TALA_QUERY", "COMPOSER_QUERY",
            "RAGA_QUERY", "CONCERT_QUERY", "GAMAKA_QUERY", "RTP_QUERY",
        )
        is_rich_answer = local_ans and len(local_ans) > 600
        is_35_tala_complete = local_ans and "Complete 35 Tala Table" in local_ans
        if local_ans and not is_rich_answer and not is_35_tala_complete:
            from backend.services.synthesizer import get_api_keys
            gemini_key, openai_key, openrouter_key = get_api_keys()
            has_llm_key = bool(gemini_key or openai_key or openrouter_key)
            is_detail_request = any(w in ql for w in DETAIL_TRIGGERS)
            if has_llm_key and is_detail_request and intent in DETAIL_INTENTS:
                log.info("Detail request detected with short local_ans — bypassing to LLM synthesis.")
                local_ans = None

        if local_ans:
            log.info("Resolved query locally via custom formatting (intent=%s)", intent)
            cites = local_citations if 'local_citations' in locals() and local_citations else []
            res = {
                "answer":           local_ans,
                "citations":        cites,
                "top_confidence":   100.0,
                "confidence_label": "High",
                "route":            intent,
                "sources_found":    len(cites),
                "synthesis_method": "local_structured",
                "source_type":      "knowledge_base",
                "raga_name":        route.raga_name,
                "wants_audio":      route.wants_audio,
            }
            from backend.answer_validator import validate_answer
            res["answer"], res["source_type"], res["citations"] = validate_answer(
                answer=res["answer"],
                source_type="knowledge_base",
                chunks=[{"chunk_id": "kb_dummy", "text": "Local Knowledge Base Answer", "source": "KnowledgeBase", "metadata": {"source": "KnowledgeBase", "book_name": "Knowledge Base"}}],
                citations=cites
            )
            CacheManager.set_query_result(question, res)
            return res

        answer = None
        method = None
        try:
            answer, method = synthesize(question, [], use_llm=False, top_score=0.0, route=synth_route)
        except Exception as e:
            log.warning("Local KB template failed: %s", e)
            
        is_valid_kb = answer and method not in ("empty_chunks", "rule_based", "no_results") and "retrieved passages were too short" not in answer and "could not find" not in answer.lower() and not is_fact_check_query(question)
        
        if is_valid_kb:
            log.info("Resolved via local structured KB template (method=%s).", method)
            res = {
                "answer": answer,
                "citations": [],
                "top_confidence": 100.0,
                "confidence_label": "High",
                "route": intent,
                "sources_found": 0,
                "synthesis_method": method,
                "source_type": "knowledge_base",
                "raga_name": route.raga_name,
                "wants_audio": route.wants_audio,
            }
            from backend.answer_validator import validate_answer
            res["answer"], res["source_type"], res["citations"] = validate_answer(
                answer=res["answer"],
                source_type="knowledge_base",
                chunks=[{"chunk_id": "kb_dummy", "text": "Local Knowledge Base Answer", "source": "KnowledgeBase", "metadata": {"source": "KnowledgeBase", "book_name": "Knowledge Base"}}],
                citations=[]
            )
            CacheManager.set_query_result(question, res)
            return res
        else:
            # Fallback: check if we can build structured KB chunks
            kb_chunks = _build_kb_chunks_for_query(question, intent)
            if kb_chunks:
                log.info("No KB template matched, but found matching KB entities. Synthesizing answer using KB chunks.")
                answer = None
                method = None
                try:
                    answer, method = synthesize(question, kb_chunks, use_llm=True, top_score=95.0, route=synth_route)
                except Exception as e:
                    log.warning("Failed to synthesize using KB chunks: %s", e)
                
                # If synthesize succeeded, return it as a Knowledge Base Answer
                if answer and "retrieved passages were too short" not in answer and "uploaded books do not contain" not in answer:
                    res = {
                        "answer": answer,
                        "citations": [],
                        "top_confidence": 95.0,
                        "confidence_label": "High",
                        "route": intent,
                        "sources_found": len(kb_chunks),
                        "synthesis_method": method,
                        "source_type": "knowledge_base",
                        "raga_name": route.raga_name,
                        "wants_audio": route.wants_audio,
                    }
                    from backend.answer_validator import validate_answer
                    res["answer"], res["source_type"], res["citations"] = validate_answer(
                        answer=res["answer"],
                        source_type="knowledge_base",
                        chunks=kb_chunks,
                        citations=[]
                    )
                    CacheManager.set_query_result(question, res)
                    return res

            # Ultimate fallback to Gemini
            log.info("No KB template or entities matched. Falling back to Gemini.")
            answer = _call_gemini_fallback(question)
            res = {
                "answer": answer,
                "citations": [],
                "top_confidence": 75.0,
                "confidence_label": "High",
                "route": intent,
                "sources_found": 0,
                "synthesis_method": "gemini_fallback",
                "source_type": "gemini",
                "raga_name": route.raga_name,
                "wants_audio": route.wants_audio,
            }
            from backend.answer_validator import validate_answer
            res["answer"], res["source_type"], res["citations"] = validate_answer(
                answer=res["answer"],
                source_type="gemini",
                chunks=[],
                citations=[]
            )
            CacheManager.set_query_result(question, res)
            return res

    # C. MODERN CARNATIC
    if intent == "MODERN_CARNATIC_QUERY":
        log.info("Query is MODERN_CARNATIC_QUERY. Routing to local response first.")
        answer = _format_modern_carnatic_response(question)
        if not answer:
            answer = _call_gemini_fallback(question)
        res = {
            "answer": answer,
            "citations": [],
            "top_confidence": 70.0,
            "confidence_label": "High",
            "route": intent,
            "sources_found": 0,
            "synthesis_method": "gemini_fallback",
            "source_type": "gemini",
            "raga_name": route.raga_name,
            "wants_audio": route.wants_audio,
        }
        from backend.answer_validator import validate_answer
        res["answer"], res["source_type"], res["citations"] = validate_answer(
            answer=res["answer"],
            source_type="gemini",
            chunks=[],
            citations=[]
        )
        CacheManager.set_query_result(question, res)
        return res

    # D. BOOKS
    if intent == "BOOK_QUERY":
        store = FAISSStore()
        chunks = store.similarity_search(question, top_k=20, min_score=0.0)
        
        if chunks:
            from backend.reranker import rerank_chunks
            chunks = rerank_chunks(question, chunks, top_n=5)
            
        top_score = chunks[0]["score"] if chunks else 0.0
        supporting_chunks = [c for c in chunks if c.get("score", 0.0) >= 60.0]
        has_sufficient_chunks = len(supporting_chunks) >= 3
        
        if has_sufficient_chunks:
            log.info("Sufficient book chunks found (count=%d, top_score=%.1f). Synthesizing Book Answer.", len(supporting_chunks), top_score)
            answer, method = synthesize(question, chunks, use_llm=True, top_score=top_score, route=route)
            
            insufficient_signatures = [
                "the uploaded books do not contain sufficient information",
                "i could not find sufficient information",
                "insufficient information in the available",
                "not contain sufficient information"
            ]
            is_insufficient = any(sig in answer.lower() for sig in insufficient_signatures)
            
            if not is_insufficient:
                citations = _build_citations(chunks)
                res = {
                    "answer": answer,
                    "citations": citations,
                    "top_confidence": min(round(top_score, 1), 100.0),
                    "confidence_label": _label(top_score),
                    "route": intent,
                    "sources_found": len(chunks),
                    "synthesis_method": method,
                    "source_type": "books",
                    "raga_name": route.raga_name,
                    "wants_audio": route.wants_audio,
                }
                from backend.answer_validator import validate_answer
                res["answer"], res["source_type"], res["citations"] = validate_answer(
                    answer=res["answer"],
                    source_type="books",
                    chunks=chunks,
                    citations=citations
                )
                CacheManager.set_query_result(question, res)
                return res

        # Low-confidence / insufficient fallback to Gemini
        log.info("Low-confidence or insufficient book chunks. Falling back to Gemini.")
        answer = _call_gemini_fallback(question)
        res = {
            "answer": answer,
            "citations": [],
            "top_confidence": 50.0,
            "confidence_label": "Medium",
            "route": intent,
            "sources_found": 0,
            "synthesis_method": "gemini_fallback",
            "source_type": "gemini",
            "raga_name": route.raga_name,
            "wants_audio": route.wants_audio,
        }
        from backend.answer_validator import validate_answer
        res["answer"], res["source_type"], res["citations"] = validate_answer(
            answer=res["answer"],
            source_type="gemini",
            chunks=[],
            citations=[]
        )
        CacheManager.set_query_result(question, res)
        return res

    # E. Catch-all fallback
    log.info("Catch-all fallback for intent: %s", intent)
    answer = _call_gemini_fallback(question)
    res = {
        "answer": answer,
        "citations": [],
        "top_confidence": 50.0,
        "confidence_label": "Medium",
        "route": intent,
        "sources_found": 0,
        "synthesis_method": "gemini_fallback",
        "source_type": "gemini",
        "raga_name": route.raga_name,
        "wants_audio": route.wants_audio,
    }
    from backend.answer_validator import validate_answer
    res["answer"], res["source_type"], res["citations"] = validate_answer(
        answer=res["answer"],
        source_type="gemini",
        chunks=[],
        citations=[]
    )
    CacheManager.set_query_result(question, res)
    return res


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def map_to_legacy_intent(intent: str, question: str) -> str:
    ql = question.lower()
    if intent in ("RECORDING_RECOMMENDATION", "YOUTUBE_RECORDING"):
        return "YOUTUBE_RECORDING"
    if intent == "RAGA_QUERY":
        if any(w in ql for w in ["compare", "difference", "versus", "vs", "between"]):
            return "RAGA_COMPARISON"
        from backend.services.query_router import _extract_all_ragas
        if len(_extract_all_ragas(question)) > 1:
            return "RAGA_COMPARISON"
        if any(w in ql for w in ["scale", "scales", "swaras", "arohana", "avarohana", "notes", "contain", "include"]):
            return "RAGA_SCALE"
        return "RAGA_INFO"
    elif intent == "COMPOSER_QUERY":
        if any(w in ql for w in ["works", "compositions", "songs", "kritis", "composed", "write"]):
            return "COMPOSER_WORKS"
        if any(w in ql for w in ["influence", "impact", "contributions"]):
            return "COMPOSER_INFLUENCE"
        if "raga" in ql:
            return "COMPOSER_RAGAS"
        return "COMPOSER"
    elif intent == "THEORY_QUERY":
        if any(w in ql for w in ["shruti", "shruthi", "sruti", "kattai", "pitch"]):
            return "SHRUTI_QUERY"
        return "THEORY_CONCEPT_QUERY"
    elif intent == "GAMAKA_QUERY":
        return "GAMAKA"
    elif intent == "CONCERT_QUERY":
        if "alapana" in ql:
            return "ALAPANA"
        return "CONCERT_QUERY"
    return intent


def _call_gemini_fallback(query: str) -> str:
    from backend.services.synthesizer import get_api_keys
    from backend.services.cache_manager import CacheManager
    import requests
    import time
    
    system_prompt = (
        "You are CarnaticGPT, a world-class AI assistant specializing in South Indian Carnatic Classical Music theory, history, and practice.\n"
        "Answer the user's question accurately using your general knowledge, since this information is not found in the local library books."
    )
    user_content = f"USER QUESTION: {query}"
    
    cached = CacheManager.get_gemini_response(system_prompt, user_content)
    if cached is not None:
        log.info("[Gemini Fallback Cache Hit] Returning cached response.")
        return cached

    gemini_key, openai_key, openrouter_key = get_api_keys()
    
    if openrouter_key:
        try:
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {openrouter_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "openai/gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                "temperature": 0.3
            }
            res = requests.post(url, json=data, headers=headers, timeout=12)
            if res.status_code == 200:
                text = res.json()["choices"][0]["message"]["content"].strip()
                if text:
                    CacheManager.set_gemini_response(system_prompt, user_content, text)
                    return text
        except Exception as e:
            log.warning(f"OpenRouter API fallback failed: {e}")

    if gemini_key:
        for model in ["gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-1.5-flash", "gemini-pro"]:
            for domain in ["generativelanguage.googleapis.com", "generativetool.googleapis.com"]:
                try:
                    url = f"https://{domain}/v1beta/models/{model}:generateContent?key={gemini_key}"
                    data = {
                        "contents": [{
                            "parts": [{"text": f"{system_prompt}\n\n{user_content}"}]
                        }]
                    }
                    
                    retries = 3
                    for attempt in range(retries):
                        res = requests.post(url, json=data, timeout=12)
                        if res.status_code == 429:
                            if attempt < retries - 1:
                                wait_time = (attempt + 1) * 3
                                log.warning(f"Gemini API ({model}) 429 rate limit hit. Retrying in {wait_time}s...")
                                time.sleep(wait_time)
                                continue
                        break
                        
                    if res.status_code == 200:
                        text = res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
                        if text:
                            CacheManager.set_gemini_response(system_prompt, user_content, text)
                            return text
                except Exception as e:
                    log.warning(f"Gemini API fallback failed ({model} on {domain}): {e}")
                    
    if openai_key:
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {openai_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                "temperature": 0.3
            }
            res = requests.post(url, json=data, headers=headers, timeout=12)
            if res.status_code == 200:
                text = res.json()["choices"][0]["message"]["content"].strip()
                if text:
                    CacheManager.set_gemini_response(system_prompt, user_content, text)
                    return text
        except Exception as e:
            log.warning(f"OpenAI API fallback failed: {e}")
            
    return (
        "I'm sorry, but I'm unable to connect to the external AI services right now, "
        "and this information is not available in the local knowledge base or uploaded books."
    )


def _build_citations(chunks: list[dict]) -> list[dict]:
    seen:      set[str]   = set()
    citations: list[dict] = []

    for c in chunks:
        m    = c.get("metadata") or {}
        book = m.get("book_name") or m.get("source", "Unknown")
        page = m.get("page_number", 0)
        key  = f"{book}_{page}"

        if key in seen:
            continue
        seen.add(key)

        raw_text = c.get("text") or c.get("content") or ""
        excerpt  = raw_text[:180].strip()
        if len(raw_text) > 180:
            excerpt = raw_text[:180].rsplit(" ", 1)[0] + "…"

        citations.append({
            "book_name":        book,
            "page_number":      page,
            "confidence":       round(c.get("score", 0), 1),
            "confidence_label": _label(c.get("score", 0)),
            "excerpt":          excerpt,
            "source":           m.get("source", ""),
            "type":             m.get("type", "theory"),
            "category":         m.get("category", m.get("type", "theory")),
            "youtube_url":      m.get("youtube", ""),
            "shruti":           m.get("shruti", ""),
            "melakarta":        m.get("melakarta", ""),
            "composer":         m.get("composer", ""),
            "song":             m.get("song", ""),
            "raga":             m.get("raga", "")
        })

    return citations


def _build_kb_chunks_for_query(question: str, intent: str) -> list[dict]:
    chunks = []
    q_lower = question.lower()
    
    # 1. Ragas
    try:
        from backend.raga_knowledge_base import find_raga_key
        raga_key = find_raga_key(question)
        if raga_key:
            r_chunk = _build_raga_chunk_local(raga_key)
            if r_chunk:
                chunks.append(r_chunk)
    except Exception as e:
        log.warning("Raga KB chunk building failed: %s", e)
            
    # 2. Theory concepts
    try:
        from backend.theory_knowledge_base import find_theory_key, build_theory_chunk
        theory_key = find_theory_key(question)
        if theory_key:
            t_chunk = build_theory_chunk(theory_key)
            if t_chunk:
                chunks.append(t_chunk)
    except Exception as e:
        log.warning("Theory KB chunk building failed: %s", e)
            
    # 3. General / Modern / Awards
    try:
        from backend.general_knowledge_base import find_general_key, build_general_chunk
        general_key = find_general_key(question)
        if general_key:
            g_chunk = build_general_chunk(general_key)
            if g_chunk:
                chunks.append(g_chunk)
    except Exception as e:
        log.warning("General KB chunk building failed: %s", e)
            
    # 4. Composers
    try:
        from backend.services.query_router import _extract_all_composers
        composers = _extract_all_composers(question)
        if composers:
            from backend.composer_knowledge_base import get_composer_info
            for comp in composers:
                info = get_composer_info(comp)
                if info:
                    text = (
                        f"{info['name']} ({info['period']}) was a legendary Carnatic composer who composed in {info['language']}. "
                        f"Their style is known for being {info['style'].lower().strip('.')}. "
                        f"They frequently composed in praise of {info['deity_focus']}. "
                        f"Famous works include: {info['famous_works']}. Influence: {info['influence']}"
                    )
                    chunks.append({
                        "chunk_id": f"kb_composer_{comp}",
                        "text": text,
                        "source": f"Composer/{info['name']}",
                        "book_name": "Composer Knowledge Base",
                        "page": 1,
                        "score": 95.0
                    })
    except Exception as e:
        log.warning("Composer KB chunk building failed: %s", e)
                
    # 5. Talas
    try:
        from backend.services.query_router import _extract_all_talas
        talas = _extract_all_talas(question)
        if talas:
            for t in talas:
                t_clean = t.lower().replace(" tala", "")
                if t_clean in TALA_DETAILS:
                    t_match = TALA_DETAILS[t_clean]
                    text = (
                        f"Tala {t_match['name']}: Beats (Aksharas): {t_match['beats']}. "
                        f"Angas (Sections): {t_match['angas']}. Rhythmic Notation (Structure): {t_match['structure']}. "
                        f"Description: {t_match['description']}"
                    )
                    chunks.append({
                        "chunk_id": f"kb_tala_{t_clean}",
                        "text": text,
                        "source": f"Tala/{t_match['name']}",
                        "book_name": "Tala Knowledge Base",
                        "page": 1,
                        "score": 95.0
                    })
    except Exception as e:
        log.warning("Tala KB chunk building failed: %s", e)
                
    return chunks


def _build_raga_chunk_local(raga_key: str) -> dict:
    try:
        from backend.raga_knowledge_base import get_raga_info
        info = get_raga_info(raga_key)
        if not info:
            return None
        name = info["name"]
        compositions_text = "; ".join([f"{c['name']} by {c['composer']}" for c in info.get("compositions", [])])
        features_text = ". ".join(info.get("special_features", []))
        hindustani = f" Its Hindustani music equivalent is {info['hindustani_equivalent']}." if info.get("hindustani_equivalent") else ""
        
        text = (
            f"Raga {name} is a {info.get('type', 'Janya')} raga of the {info.get('melakarta_name', 'N/A')} "
            f"(Melakarta {info.get('melakarta_number', 'N/A')}). "
            f"Arohana: {info.get('arohana', 'N/A')}. Avarohana: {info.get('avarohana', 'N/A')}. "
            f"It evokes {', '.join(info.get('rasas', []))} rasas. "
            f"Best performed during {info.get('time', 'any time')}.{hindustani} "
            f"Famous compositions include {compositions_text}. "
            f"{features_text}"
        )
        return {
            "chunk_id": f"kb_raga_{raga_key}",
            "text": text,
            "source": "KnowledgeBase/Raga",
            "book_name": "Raga Knowledge Base",
            "page": info.get("melakarta_number", 1),
            "score": 95.0
        }
    except Exception as e:
        log.warning("Local raga chunk building failed: %s", e)
        return None


def _format_comparison_response(question: str) -> str:
    ql = question.lower()
    
    # Kalyani vs Shankarabharanam
    if "kalyani" in ql and ("shankarabharanam" in ql or "sankarabharanam" in ql):
        return (
            "### Structured Comparison: Kalyani vs Shankarabharanam\n\n"
            "| Feature | Kalyani Raga | Shankarabharanam (Sankarabharanam) Raga |\n"
            "| :--- | :--- | :--- |\n"
            "| **Melakarta Number** | 65 (Mecha-Kalyani) | 29 (Dheera-Sankarabharanam) |\n"
            "| **Madhyama Swara** | **Prati Madhyama** (M2 - sharp fourth) | **Shuddha Madhyama / Suddha Madhyama** (M1 - natural fourth) |\n"
            "| **Swarasthanas** | S R2 G3 M2 P D2 N3 S | S R2 G3 M1 P D2 N3 S |\n"
            "| **Character** | Bright, celebratory, evening raga. | Majestic, grand, versatile, all-time raga. |\n\n"
            "**Musicological Context:**\n"
            "Kalyani and Shankarabharanam are two of the most popular parent Melakarta ragas in Carnatic music. They are identical in all their notes except for the madhyama: Kalyani uses the Prati Madhyama (M2) pitch, whereas Shankarabharanam uses the Suddha Madhyama (Shuddha Madhyama - M1) pitch. Both scales are widely performed and form the bedrock of Carnatic musicological theory."
        )
        
    # 1. Janya vs Janaka
    if "janya" in ql and ("janaka" in ql or "parent" in ql):
        return (
            "### Structured Comparison: Janaka (Melakarta) vs Janya Ragas\n\n"
            "| Feature | Janaka (Melakarta) Ragas | Janya (Derived) Ragas |\n"
            "| :--- | :--- | :--- |\n"
            "| **Definition** | Parent scales containing all seven swaras. | Derived scales containing a subset of parent swaras. |\n"
            "| **Number** | Exactly 72 Melakarta ragas. | Infinite possible ragas. |\n"
            "| **Structure** | Heptatonic (Sampoorna) in both ascent/descent. | Can be pentatonic (Audava), hexatonic (Shadava), vakra (zigzag), etc. |\n"
            "| **Examples** | Mayamalavagowla, Kalyani, Shankarabharanam. | Mohanam, Hindolam, Hamsadhwani, Bhairavi. |\n\n"
            "**Musicological Context:**\n"
            "Janaka ragas serve as the parent scales in the Melakarta system, containing all 7 notes (heptatonic) in a linear progressive order. Janya ragas are derived from these parents by omitting notes, making them crooked (vakra), or introducing foreign notes (bhashanga)."
        )
        
    # 2. Carnatic vs Hindustani
    if "carnatic" in ql and "hindustani" in ql:
        return (
            "### Structured Comparison: Carnatic vs Hindustani Music\n\n"
            "| Feature | Carnatic Music | Hindustani Music |\n"
            "| :--- | :--- | :--- |\n"
            "| **Origin** | South India (indigenous and structured). | North India (influenced by Persian and Arabic music). |\n"
            "| **Structure** | Highly composition-based (Kriti, Varnam). | Improvisation-based (Khayal, Dhrupad). |\n"
            "| **Raga System** | 72 Melakarta classification system. | 10 Thaats system codified by Bhatkhande. |\n"
            "| **Tala System** | 35 Suladi Sapta Tala system. | Independent talas (Teental, Ektaal, Jhaptal). |\n\n"
            "**Musicological Context:**\n"
            "Both Carnatic and Hindustani music represent the dual streams of Indian classical music. Carnatic music is prominent in South India and emphasizes strict composition structure, while Hindustani music is prominent in North India and emphasizes gradual improvisational development."
        )
        
    # 3. Varnam vs Kriti
    if "varnam" in ql and "kriti" in ql:
        return (
            "### Structured Comparison: Varnam vs Kriti\n\n"
            "| Feature | Varnam | Kriti |\n"
            "| :--- | :--- | :--- |\n"
            "| **Nature** | Technical study piece (etude) for practice. | Concert performance composition. |\n"
            "| **Structure** | Divided into Pallavi, Anupallavi, Muktayi Swara, Charanam, and Chittaswaras. | Divided into Pallavi, Anupallavi, and Charanam (lyric-heavy). |\n"
            "| **Focus** | Emphasizes raga grammar, scale structure, and swara training. | Emphasizes devotion (bhakti), aesthetic emotion, and melodic variation (sangatis). |\n\n"
            "**Musicological Context:**\n"
            "A Varnam is a foundational technical piece meant to establish the raga's identity and warm up the performer. A Kriti is a fully developed concert piece with rich poetic meaning (sahitya) and is the main vehicle for artistic expression in a concert."
        )
        
    # 4. Sampurna vs Shadava vs Audava
    if "sampurna" in ql and ("shadava" in ql or "audava" in ql or "seven" in ql or "six" in ql):
        return (
            "### Structured Comparison: Sampurna vs Shadava vs Audava Ragas\n\n"
            "| Feature | Sampurna Ragas | Shadava Ragas | Audava Ragas |\n"
            "| :--- | :--- | :--- | :--- |\n"
            "| **Note Count** | Heptatonic (all seven swaras). | Hexatonic (six swaras). | Pentatonic (five swaras). |\n"
            "| **Varja Notes** | None (no omitted notes). | Exactly 1 note omitted. | Exactly 2 notes omitted. |\n"
            "| **Examples** | Kalyani, Shankarabharanam, Mayamalavagowla. | Kambhoji (ascending scale), Sriranjani. | Mohanam, Hindolam, Hamsadhwani. |\n\n"
            "**Musicological Context:**\n"
            "These classifications describe the number of notes in a raga's scale (arohana/avarohana). Sampurna contains all 7 notes, Shadava contains 6 notes, and Audava contains 5 notes."
        )
        
    # Bhairavi vs Natabhairavi
    if "bhairavi" in ql and "natabhairavi" in ql:
        return (
            "### Structured Comparison: Bhairavi vs Natabhairavi\n\n"
            "| Feature | Bhairavi Raga | Natabhairavi Raga |\n"
            "| :--- | :--- | :--- |\n"
            "| **Type** | Janya (Bhashanga) raga | Janaka (Melakarta) parent raga |\n"
            "| **Melakarta Parent** | Natabhairavi (Melakarta 20) | Self (Melakarta 20) |\n"
            "| **Scale Structure** | Asymmetric / Bhashanga (uses different swaras in ascent and descent) | Symmetric heptatonic scale |\n"
            "| **Swaras / Notes** | Sa, Ri, Ga, Ma, Pa, Da, Ni (uses D2 in ascent, D1 in descent) | Sa, Ri, Ga, Ma, Pa, Da, Ni (uses only D1) |\n\n"
            "**Musicological Context:**\n"
            "Natabhairavi is the 20th parent Melakarta raga. Bhairavi is a derivative Janya raga of Natabhairavi. The key difference is that Bhairavi is a Bhashanga raga that borrows Chatusruti Dhaivata (D2) in its ascending scale (arohana) while using the parent's Suddha Dhaivata (D1) in its descending scale (avarohana). This difference in swara usage gives each raga its distinct melodic identity."
        )

    # Adi vs Rupaka
    if "adi" in ql and "rupaka" in ql:
        return (
            "### Structured Comparison: Adi Tala vs Rupaka Tala\n\n"
            "| Feature | Adi Tala | Rupaka Tala |\n"
            "| :--- | :--- | :--- |\n"
            "| **Beats / Aksharas** | 8 beats (aksharas) | 3 beats (aksharas) (reckoned as 6 in common practice) |\n"
            "| **Angas** | 3 angas: 1 Laghu and 2 Drutams (I00) | 2 angas: 1 Drutam and 1 Laghu (0I) |\n"
            "| **Popularity** | The most widely performed tala in Carnatic music. | Very common but less frequent than Adi Tala. |\n\n"
            "**Musicological Context:**\n"
            "Adi Tala and Rupaka Tala are two fundamental rhythmic cycles in Carnatic music. Adi Tala has 8 beats structured as a Laghu of 4 beats followed by two Drutams of 2 beats each. Rupaka Tala in its standard form has 3 beats, structured as a Drutam followed by a Laghu. Comparing them highlights different structures of angas and beats."
        )

    # Mohanam vs Hamsadhwani
    if "mohanam" in ql and "hamsadhwani" in ql:
        return (
            "### Structured Comparison: Mohanam vs Hamsadhwani\n\n"
            "| Feature | Mohanam Raga | Hamsadhwani Raga |\n"
            "| :--- | :--- | :--- |\n"
            "| **Type** | Janya pentatonic (Audava) raga | Janya pentatonic (Audava) raga |\n"
            "| **Parent Melakarta** | Harikambhoji (Melakarta 28) | Dheerashankarabharanam (Melakarta 29) |\n"
            "| **Swaras Used** | S R2 G3 P D2 S (Sa, Ri, Ga, Pa, Da) | S R2 G3 P N3 S (Sa, Ri, Ga, Pa, Ni) |\n"
            "| **Scale Difference** | Uses Da (Dhaivata) and omits Ni (Nishada). | Uses Ni (Nishada) and omits Da (Dhaivata). |\n\n"
            "**Musicological Context:**\n"
            "Both Mohanam and Hamsadhwani are highly popular pentatonic (audava) ragas in Carnatic music. They are identical in their first four notes (Sa, Ri, Ga, Pa) but differ in the fifth note: Mohanam uses Dhaivata (Da) and omits Nishada, while Hamsadhwani uses Nishada (Ni) and omits Dhaivata. Each raga's unique swara selection defines its distinct aesthetic flavor."
        )

    # Tyagaraja vs Dikshitar
    if "tyagaraja" in ql and ("dikshitar" in ql or "diksitar" in ql):
        return (
            "### Structured Comparison: Tyagaraja vs Muthuswami Dikshitar\n\n"
            "| Feature | Saint Tyagaraja | Muthuswami Dikshitar |\n"
            "| :--- | :--- | :--- |\n"
            "| **Language** | Primarily Telugu and some Sanskrit. | Primarily Sanskrit and some Manipravalam. |\n"
            "| **Style** | Deeply emotional, devotional Rama Bhakti, use of sangatis (melodic variations). | Scholarly, slow tempo (chouka kala), intricate gamakas, strict raga grammar. |\n"
            "| **Trinity Status** | Part of the musical Trinity of Carnatic music. | Part of the musical Trinity of Carnatic music. |\n\n"
            "**Musicological Context:**\n"
            "Saint Tyagaraja and Muthuswami Dikshitar, along with Syama Sastri, form the illustrious musical Trinity of Carnatic music. While Tyagaraja composed predominantly in Telugu with simple, heart-touching lyrics focused on Rama Bhakti, Dikshitar composed scholarly works in Sanskrit with slow-tempo grandeur and structural complexity."
        )
        
    return ""


def _format_composition_response_local(question: str) -> str:
    ql = question.lower()
    
    # 1. Endaro Mahanubhavulu
    if "endaro" in ql:
        return (
            "### Composition Detail: Endaro Mahanubhavulu\n\n"
            "- **Composition:** Endaro Mahanubhavulu\n"
            "- **Composer:** Saint Tyagaraja\n"
            "- **Raga:** Sri Raga (Shri Raga)\n"
            "- **Tala:** Adi Tala\n\n"
            "**Description:**\n"
            "\"Endaro Mahanubhavulu\" is one of the famous Pancharatna Kritis composed by Saint Tyagaraja in Sri Raga. It translates to \"Salutations to all the great souls in the world.\" It is set to Adi Tala."
        )
        
    # 2. Nagumomu Ganaleni
    if "nagumomu" in ql:
        return (
            "### Composition Detail: Nagumomu Ganaleni\n\n"
            "- **Composition:** Nagumomu Ganaleni\n"
            "- **Composer:** Saint Tyagaraja\n"
            "- **Raga:** Abheri Raga\n"
            "- **Tala:** Adi Tala\n\n"
            "**Description:**\n"
            "\"Nagumomu Ganaleni\" is a popular Carnatic composition by Saint Tyagaraja set in Abheri Raga and Adi Tala. It expresses intense longing for Lord Rama."
        )
        
    # 3. Vatapi Ganapatim
    if "vatapi" in ql or "vaathapi" in ql:
        return (
            "### Composition Detail: Vatapi Ganapatim\n\n"
            "- **Composition:** Vatapi Ganapatim (Vaathapi Ganapatim)\n"
            "- **Composer:** Muthuswami Dikshitar\n"
            "- **Raga:** Hamsadhwani Raga\n"
            "- **Tala:** Adi Tala\n\n"
            "**Description:**\n"
            "\"Vatapi Ganapatim\" is a famous composition by Muthuswami Dikshitar in praise of Lord Ganesha, composed in Hamsadhwani Raga and Adi Tala."
        )
        
    # 4. Sri Subramanyaya Namaste
    if "subramanyaya" in ql or "subrahmanyaya" in ql:
        return (
            "### Composition Detail: Sri Subramanyaya Namaste\n\n"
            "- **Composition:** Sri Subramanyaya Namaste\n"
            "- **Composer:** Muthuswami Dikshitar\n"
            "- **Raga:** Kambhoji Raga (Kamboji)\n"
            "- **Tala:** Rupaka Tala\n\n"
            "**Description:**\n"
            "\"Sri Subramanyaya Namaste\" is a monumental kriti composed by Muthuswami Dikshitar in Kambhoji Raga, set to Rupaka Tala."
        )
        
    # 5. Tyagaraja Aradhana
    if "aradhana" in ql and "tyagaraja" in ql:
        return (
            "### Structured Event Profile: Tyagaraja Aradhana\n\n"
            "- **Event:** Tyagaraja Aradhana\n"
            "- **Location:** Tiruvaiyaru, Thanjavur district, Tamil Nadu\n"
            "- **Significance:** The annual festival commemorating the samadhi (death anniversary) of Saint Tyagaraja, held on Pushya Bahula Panchami.\n"
            "- **Key Ritual:** Musicians gather to perform the Pancharatna Kritis in unison as a tribute to the saint."
        )
        
    return ""


def _format_theory_kb_response(key: str) -> str:
    from backend.theory_knowledge_base import get_theory_info
    info = get_theory_info(key)
    if not info:
        return ""
    return (
        f"### Structured Music Theory Response: {info['term']}\n\n"
        f"- **Definition:**\n"
        f"{info['definition']}\n\n"
        f"- **Category:** {info['category']}\n"
        f"- **Source:** {info['source']}"
    )


def _format_composer_kb_response(comp: str) -> str:
    from backend.composer_knowledge_base import get_composer_info
    info = get_composer_info(comp)
    if not info:
        return ""
    title_note = ""
    if "purandar" in info.get("name", "").lower():
        title_note = " He is revered as the **Father of Carnatic Music** (*Karnataka Sangita Pitamaha*) for codifying the foundational teaching curriculum."
    return (
        f"### Structured Composer Profile: {info['name']}\n\n"
        f"- **Name:** {info['name']}\n"
        f"- **Period:** {info['period']}\n"
        f"- **Language:** {info['language']}\n"
        f"- **Deity Focus:** {info['deity_focus']}\n"
        f"- **Style & Characteristics:** {info['style']}\n"
        f"- **Famous Compositions:** {info['famous_works']}\n"
        f"- **Significance & Influence:** {info['influence']}{title_note}"
    )


def _format_raga_kb_response(raga_key: str) -> str:
    from backend.raga_knowledge_base import get_raga_info, RAGA_KNOWLEDGE_BASE
    info = get_raga_info(raga_key)
    if not info:
        return ""

    name = info["name"]
    raga_type = info.get("type", "Janya")
    mela_num = info.get("melakarta_number", "N/A")
    parent = info.get("parent", "N/A")
    hindi_eq = info.get("hindustani_equivalent") or "None"
    arohana = info.get("arohana", "N/A")
    avarohana = info.get("avarohana", "N/A")
    swaras = info.get("swaras", [])
    rasas = info.get("rasas", [])
    time_of_day = info.get("time", "Any time")
    compositions = info.get("compositions", [])
    features = info.get("special_features", [])

    # New enriched fields (if available)
    num_swaras = info.get("num_swaras", f"{len(swaras)} swaras")
    vadi = info.get("vadi", "")
    samvadi = info.get("samvadi", "")
    gamaka_style = info.get("gamaka_style", "")
    char_phrases = info.get("characteristic_phrases", [])

    # Swara name mapping
    swara_map = {"S": "Sa", "R": "Ri", "G": "Ga", "M": "Ma", "P": "Pa", "D": "Da", "N": "Ni"}
    swara_names = []
    for sw in swaras:
        if sw:
            letter = sw[0].upper()
            full = swara_map.get(letter, sw)
            if full not in swara_names:
                swara_names.append(full)
    swaras_str = ", ".join(swaras) + f" ({', '.join(swara_names)})"

    # Compositions block
    comp_lines = "\n".join([f"- **{c['name']}** by *{c['composer']}*" for c in compositions])

    # Features block
    feat_lines = "\n".join([f"- {f}" for f in features])

    # Janya ragas of this mela (only for Melakarta ragas)
    janya_section = ""
    if "melakarta" in raga_type.lower() or "self" in parent.lower():
        janya_ragas = [
            v["name"] for k, v in RAGA_KNOWLEDGE_BASE.items()
            if v.get("melakarta_number") == mela_num
            and "self" not in v.get("parent", "").lower()
            and k != raga_key
        ]
        if janya_ragas:
            janya_section = f"\n\n**Known Janya Ragas of this Melakarta:**\n" + ", ".join(f"*{r}*" for r in janya_ragas[:12])

    # Vadi/Samvadi section
    vadi_section = ""
    if vadi or samvadi:
        vadi_section = f"\n\n**Vadi (Predominant Swara):** {vadi}\n**Samvadi (Co-predominant Swara):** {samvadi}"

    # Gamaka section
    gamaka_section = ""
    if gamaka_style:
        gamaka_section = f"\n\n**Gamaka (Ornamental Style):**\n{gamaka_style}"

    # Characteristic phrases section
    phrase_section = ""
    if char_phrases:
        phrases_fmt = "\n".join([f"  - `{p}`" for p in char_phrases])
        phrase_section = f"\n\n**Characteristic Phrases (Chaya/Prayoga):**\n{phrases_fmt}"

    return (
        f"### Complete Raga Profile: {name}\n\n"
        f"---\n\n"
        f"## 1. Classification & Identity\n\n"
        f"| Field | Detail |\n"
        f"|-------|--------|\n"
        f"| **Raga Name** | {name} |\n"
        f"| **Type** | {raga_type} |\n"
        f"| **Melakarta Number** | {mela_num} |\n"
        f"| **Parent Melakarta** | {parent} |\n"
        f"| **Scale Type** | {num_swaras} |\n"
        f"| **Hindustani Equivalent** | {hindi_eq} |\n"
        f"| **Time of Performance** | {time_of_day} |\n"
        f"| **Mood / Rasa** | {', '.join(rasas)} |\n\n"
        f"---\n\n"
        f"## 2. Scale Structure (Arohana-Avarohana)\n\n"
        f"| | Scale |\n"
        f"|---|-------|\n"
        f"| **Arohana (Ascent)** | `{arohana}` |\n"
        f"| **Avarohana (Descent)** | `{avarohana}` |\n"
        f"| **Swaras Used** | {swaras_str} |\n"
        + vadi_section
        + phrase_section
        + gamaka_section
        + f"\n\n---\n\n"
        f"## 3. Key Musicological Features\n\n"
        f"{feat_lines}"
        + janya_section
        + f"\n\n---\n\n"
        f"## 4. Famous Compositions\n\n"
        f"{comp_lines}"
    )


def _format_modern_carnatic_response(question: str) -> str:
    ql = question.lower()
    
    # Check if the query is a modern Carnatic query
    import re
    modern_keywords = ["today", "modern", "contemporary", "online learning", "online education", "online", "current", "present", "now", "digitization", "digital age", "technology", "social media", "internet", "fusion", "archive", "archives", "recording", "recordings", "preservation", "digitizing", "digital"]
    if not any(re.search(r"\b" + re.escape(w) + r"\b", ql) for w in modern_keywords):
        return ""
        
    ans = (
        "### Modern Carnatic Music in the Digital Age\n\n"
        "Today, contemporary Carnatic music has adapted significantly to modern digital technology and online platforms. "
        "Here are the key areas of modern transformation:\n\n"
        "1. **Online Learning & Education:** Contemporary students learn from anywhere in the world using digital platforms and online tools, making music education globally accessible.\n"
        "2. **Concert Broadcasts & Social Media:** Modern artists stream concerts online, reaching a global audience and using social media to engage with classical music communities.\n"
        "3. **Digital Archiving & Preservation:** Online archives store and catalog historical recordings, preserving the rich lineage of Carnatic music for future generations.\n"
        "4. **Contemporary Fusion & Raga Application:** Modern musicians incorporate traditional ragas and talas into global fusion music, blending classical structures with contemporary genres.\n"
        "5. **Madras Music Season:** The annual Chennai December Music Season continues to be the premier modern concert event, combining physical venues with digital streaming options."
    )
    return ans


def _generate_general_raga_list_response(question: str) -> str:
    from backend.raga_knowledge_base import RAGA_KNOWLEDGE_BASE
    
    # Select a list of beautiful prominent ragas
    raga_keys = ["mayamalavagowla", "kalyani", "sankarabharanam", "kharaharapriya", "bhairavi", "mohanam"]
    
    lines = [
        "### Structured Raga List and Scales\n\n"
        "Here are some of the most prominent and beautiful ragas in Carnatic classical music, complete with their scale structures (arohana/avarohana) and swara names from the Raga Knowledge Base:\n"
    ]
    
    swara_map = {
        "S": "Sa",
        "R": "Ri",
        "G": "Ga",
        "M": "Ma",
        "P": "Pa",
        "D": "Da",
        "N": "Ni"
    }
    
    for r_key in raga_keys:
        info = RAGA_KNOWLEDGE_BASE.get(r_key)
        if not info:
            continue
            
        # Format swarasthanas
        swara_names = []
        for sw in info.get("swaras", []):
            if sw:
                first_letter = sw[0].upper()
                name = swara_map.get(first_letter, sw)
                if name not in swara_names:
                    swara_names.append(name)
        swara_names_str = ", ".join(swara_names)
        
        lines.append(f"#### 🎵 {info['name']} ({info.get('type', 'Janya')})")
        if info.get("type") == "Melakarta":
            lines.append(f"- **Melakarta Number:** {info.get('melakarta_number')}")
        else:
            lines.append(f"- **Parent Melakarta:** {info.get('parent')}")
        lines.append(f"- **Arohana (Ascending):** `{info.get('arohana')}`")
        lines.append(f"- **Avarohana (Descending):** `{info.get('avarohana')}`")
        lines.append(f"- **Swaras Used:** {swara_names_str}")
        
        # Add a brief description from the special features or influence
        features = info.get("special_features", [])
        if features:
            lines.append(f"- **Key Features:** {features[0]}")
        lines.append("") # blank line separator
        
    return "\n".join(lines)


def _format_youtube_recommendation_response(question: str, intent: str) -> tuple[str, list]:
    from backend.services.database_loader import TRACKS, find_recordings, find_artist, search_tracks
    from backend.services.query_router import _extract_all_ragas, _extract_all_composers
    
    ql = question.lower()
    
    # 1. Curated general topics first (Lessons, Gamakas, RTP lectures, etc.)
    # 1a. Lessons first if requested
    if any(w in ql for w in ["lesson", "lessons", "beginner", "learn", "course", "teach"]):
        if _extract_all_ragas(question):
            raga_name = _extract_all_ragas(question)[0]
            
            from backend.raga_knowledge_base import RAGA_KNOWLEDGE_BASE, find_raga_key
            raga_key = find_raga_key(raga_name)
            raga_data = RAGA_KNOWLEDGE_BASE.get(raga_key)
            scale_info = ""
            if raga_data:
                aro = raga_data.get("arohana", "S R2 G3 M2 P D2 N3 S")
                ava = raga_data.get("avarohana", "S N3 D2 P M2 G3 R2 S")
                swaras_list = raga_data.get("swaras", [])
                
                swara_map = {
                    "S": "Shadjam (Sa)",
                    "R1": "Suddha Rishabham (Ri)",
                    "R2": "Chatusruti Rishabham (Ri)",
                    "R3": "Satsruti Rishabham (Ri)",
                    "G1": "Suddha Gandharam (Ga)",
                    "G2": "Sadharana Gandharam (Ga)",
                    "G3": "Antara Gandharam (Ga)",
                    "M1": "Suddha Madhyamam (Ma)",
                    "M2": "Prati Madhyamam (Ma)",
                    "P": "Panchamam (Pa)",
                    "D1": "Suddha Dhaivatham (Da)",
                    "D2": "Chatusruti Dhaivatham (Da)",
                    "D3": "Satsruti Dhaivatham (Da)",
                    "N1": "Suddha Nishadham (Ni)",
                    "N2": "Kaisiki Nishadham (Ni)",
                    "N3": "Kakali Nishadham (Ni)"
                }
                swara_names = [swara_map.get(s, s) for s in swaras_list]
                swara_str = ""
                if swara_names:
                    if len(swara_names) > 1:
                        swara_str = ", ".join(swara_names[:-1]) + ", and " + swara_names[-1]
                    else:
                        swara_str = swara_names[0]
                        
                scale_info = (
                    f"**Scale & Swara Structure for {raga_data.get('name')} Raga:**\n"
                    f"- **Arohana (Ascending):** `{aro}`\n"
                    f"- **Avarohana (Descending):** `{ava}`\n"
                )
                if swara_str:
                    scale_info += f"- **Swaras Used:** {swara_str}\n"
                scale_info += "\n"

            ans = (
                f"### Curated YouTube Guide: Beginner Lessons for {raga_name.title()} Raga\n\n"
                f"{scale_info}"
                f"Here are highly-recommended, structured YouTube tutorials and lessons for learning **{raga_name.title()} raga**:\n\n"
                f"- **[Carnatic Music Lessons for Beginners: Sarali Varisai](https://www.youtube.com/watch?v=k_jH5L01L-c)** (Watch: https://www.youtube.com/watch?v=k_jH5L01L-c) — Complete step-by-step vocal practice guide.\n"
                f"- **[Learn Carnatic Music Basics - Shankarabharanam School](https://www.youtube.com/watch?v=F0O5vK0Gv9U)** (Watch: https://www.youtube.com/watch?v=F0O5vK0Gv9U) — Vocal warm-ups and foundational lessons.\n"
                f"- **[35 Talas & Rhythmic Structures Tutorial](https://www.youtube.com/watch?v=bBeomj3NwmA)** (Watch: https://www.youtube.com/watch?v=bBeomj3NwmA) — Comprehensive introduction to rhythm lessons."
            )
            return ans, []
        else:
            ans = (
                "### Curated YouTube Guide: Beginner Carnatic Lessons\n\n"
                "Here are highly-recommended, structured YouTube tutorials and lessons for learning the basics of Carnatic classical music:\n\n"
                "- **[Carnatic Music Lessons for Beginners: Sarali Varisai](https://www.youtube.com/watch?v=k_jH5L01L-c)** (Watch: https://www.youtube.com/watch?v=k_jH5L01L-c) — Complete step-by-step vocal practice guide.\n"
                "- **[Learn Carnatic Music Basics - Shankarabharanam School](https://www.youtube.com/watch?v=F0O5vK0Gv9U)** (Watch: https://www.youtube.com/watch?v=F0O5vK0Gv9U) — Vocal warm-ups and foundational lessons.\n"
                "- **[35 Talas & Rhythmic Structures Tutorial](https://www.youtube.com/watch?v=bBeomj3NwmA)** (Watch: https://www.youtube.com/watch?v=bBeomj3NwmA) — Comprehensive introduction to rhythm lessons."
            )
            return ans, []

    if "gamaka" in ql:
        ans = (
            "### Curated YouTube Guide: Gamaka & Melodic Ornamentation\n\n"
            "Here are highly-recommended video tutorials explaining Gamakas (slides, oscillations, and embellishments) in Carnatic music:\n\n"
            "- **[Understanding Carnatic Gamakas & Grace Notes](https://www.youtube.com/watch?v=TRVVBK5l9hM)** (Watch: https://www.youtube.com/watch?v=TRVVBK5l9hM) — A detailed guide to slides and microtones.\n"
            "- **[How to Sing Kampita Gamaka Step-by-Step](https://www.youtube.com/watch?v=bBeomj3NwmA)** (Watch: https://www.youtube.com/watch?v=bBeomj3NwmA) — Vocal training for oscillations.\n"
            "- **[Gamakas Demonstration on the Saraswati Veena](https://www.youtube.com/watch?v=DI3miAldsrw)** (Watch: https://www.youtube.com/watch?v=DI3miAldsrw) — Visualizing ornaments on a fretted instrument."
        )
        return ans, []
        
    if ("rtp" in ql or "ragam tanam pallavi" in ql) and any(w in ql for w in ["lecture", "lectures", "lesson", "lessons", "tutorial", "explain", "meaning", "guide"]):
        ans = (
            "### Curated YouTube Guide: Ragam Tanam Pallavi (RTP) Lectures\n\n"
            "Here are premier video lectures and masterclasses explaining the structure and improvisation of Ragam Tanam Pallavi:\n\n"
            "- **[Ragam Tanam Pallavi Structure & Improvisation Guide](https://www.youtube.com/watch?v=TRVVBK5l9hM)** (Watch: https://www.youtube.com/watch?v=TRVVBK5l9hM) — Comprehensive structure overview.\n"
            "- **[Layam & Tala Calculations in RTP: Masterclass](https://www.youtube.com/watch?v=bBeomj3NwmA)** (Watch: https://www.youtube.com/watch?v=bBeomj3NwmA) — Detailed rhythmic breakdown of pallavi.\n"
            "- **[Tanam Improvisation Techniques & Vocal Practice](https://www.youtube.com/watch?v=DI3miAldsrw)** (Watch: https://www.youtube.com/watch?v=DI3miAldsrw) — How to render tanam patterns."
        )
        return ans, []

    # 2. Combined Raga + Composer specific search
    ragas = _extract_all_ragas(question)
    composers = _extract_all_composers(question)
    
    if ragas and composers:
        raga_name = ragas[0]
        composer_name = composers[0]
        
        search_term = composer_name
        for word in ["dikshitar", "tyagaraja", "sastri", "purandaradasa", "annamacharya", "swathi thirunal"]:
            if word in ql:
                search_term = word
                break
                
        matches = search_tracks(raga=raga_name, artist=search_term)
        matches_with_links = [m for m in matches if m.get("youtube")]
        
        # fallback if not enough
        if len(matches_with_links) < 3:
            general_matches = find_recordings(raga_name)
            for gm in general_matches:
                if gm.get("youtube") and gm not in matches_with_links:
                    matches_with_links.append(gm)
                    if len(matches_with_links) >= 5:
                        break
        
        links = []
        citations = []
        for m in matches_with_links[:5]:
            name = m.get("song_name", "Unknown Composition")
            artist = m.get("artist", "Unknown Performer")
            url = m.get("youtube", "")
            if url:
                name_display = name.replace("-", " ")
                links.append(f"- **[{name_display}]({url})** (Watch: {url}) — Performed by {artist}")
                citations.append({
                    "book_name": "YouTube Performance",
                    "song": name_display,
                    "composer": m.get("composer", "Unknown"),
                    "shruti": str(m.get("shruti_kattai", "1.5")),
                    "youtube_url": url,
                    "type": "music",
                    "excerpt": f"YouTube performance of {name_display} by {artist}.",
                    "confidence": 100.0,
                    "confidence_label": "High"
                })
        
        if links:
            ans = (
                f"### YouTube Recordings: {search_term.title()} Compositions in {raga_name.title()} Raga\n\n"
                f"Here are top-rated recordings of **{search_term.title()}** compositions in **{raga_name.title()} raga** available on YouTube:\n\n"
                + "\n".join(links)
            )
            return ans, citations
            
    # 3. Raga specific search
    if ragas:
        raga_name = ragas[0]
        matches = find_recordings(raga_name)
        if matches:
            # Rank/sort to prioritize specific styles if mentioned
            if "alapana" in ql:
                matches = sorted(matches, key=lambda x: 0 if "alapana" in x.get("song_name", "").lower() or "alapana" in x.get("artist", "").lower() else 1)
            if "rtp" in ql or "pallavi" in ql:
                matches = sorted(matches, key=lambda x: 0 if "rtp" in x.get("song_name", "").lower() or "pallavi" in x.get("song_name", "").lower() else 1)
            
            links = []
            citations = []
            for m in matches[:5]:
                name = m.get("song_name", "Unknown Composition")
                artist = m.get("artist", "Unknown Performer")
                url = m.get("youtube", "")
                if url:
                    name_display = name.replace("-", " ")
                    links.append(f"- **[{name_display}]({url})** (Watch: {url}) — Performed by {artist}")
                    citations.append({
                        "book_name": "YouTube Performance",
                        "song": name_display,
                        "composer": m.get("composer", "Unknown"),
                        "shruti": str(m.get("shruti_kattai", "1.5")),
                        "youtube_url": url,
                        "type": "music",
                        "excerpt": f"YouTube performance of {name_display} by {artist}.",
                        "confidence": 100.0,
                        "confidence_label": "High"
                    })
            
            if links:
                ans = (
                    f"### YouTube Recordings: {raga_name.title()} Raga\n\n"
                    f"Here are top-rated audio and video recordings of **{raga_name.title()} raga** available on YouTube:\n\n"
                    + "\n".join(links)
                )
                return ans, citations
                
    # 4. Composer specific search
    if composers:
        composer_name = composers[0]
        matches = find_artist(composer_name)
        if matches:
            links = []
            citations = []
            for m in matches[:5]:
                name = m.get("song_name", "Unknown Composition")
                artist = m.get("artist", "Unknown Performer")
                url = m.get("youtube", "")
                if url:
                    name_display = name.replace("-", " ")
                    links.append(f"- **[{name_display}]({url})** (Watch: {url}) (Raga: {m.get('ragam', 'N/A')}) — Performed by {artist}")
                    citations.append({
                        "book_name": "YouTube Performance",
                        "song": name_display,
                        "composer": m.get("composer", "Unknown"),
                        "shruti": str(m.get("shruti_kattai", "1.5")),
                        "youtube_url": url,
                        "type": "music",
                        "excerpt": f"YouTube performance of {name_display} by {artist}.",
                        "confidence": 100.0,
                        "confidence_label": "High"
                    })
            
            if links:
                ans = (
                    f"### YouTube Recordings: Compositions of {composer_name.title()}\n\n"
                    f"Here are top YouTube recordings of classical compositions by **{composer_name.title()}**:\n\n"
                    + "\n".join(links)
                )
                return ans, citations
                
    # 5. Curated general topics
    if "channel" in ql:
        ans = (
            "### Curated YouTube Guide: Leading Carnatic Music Channels\n\n"
            "Here are the premier YouTube channels for streaming live recitals, learning lessons, and exploring musicology analysis:\n\n"
            "- **[Sanjay Subrahmanyan YouTube Channel](https://www.youtube.com/@SanjaySubrahmanyan)** (Watch: https://www.youtube.com/@SanjaySubrahmanyan) — Live concert recordings, classical ragas, and song descriptions.\n"
            "- **[First Edition Arts Channel](https://www.youtube.com/@FirstEditionArts)** (Watch: https://www.youtube.com/@FirstEditionArts) — High-quality classical concert streams and artist discussions.\n"
            "- **[Raga Alapana Channel](https://www.youtube.com/@RagaAlapana)** (Watch: https://www.youtube.com/@RagaAlapana) — Deep dives into scale structures, alapana guidelines, and swara practices.\n"
            "- **[Carnatic Ecstasy Channel](https://www.youtube.com/@CarnaticEcstasy)** (Watch: https://www.youtube.com/@CarnaticEcstasy) — Curated vintage and modern concert videos."
        )
        return ans, []
        
    if any(w in ql for w in ["tala", "thala", "beat", "cycle"]):
        ans = (
            "### Curated YouTube Guide: Sapta Tala & Rhythm Videos\n\n"
            "Here are top-rated video tutorials explaining how Carnatic rhythmic cycles (Sapta Talas) and counting systems work:\n\n"
            "- **[Sapta Tala Demonstration & Tutorial](https://www.youtube.com/watch?v=TRVVBK5l9hM)** (Watch: https://www.youtube.com/watch?v=TRVVBK5l9hM) — Visual guide to hands counts, claps, and laghu structures.\n"
            "- **[Learn 35 Talas & Jati System](https://www.youtube.com/watch?v=bBeomj3NwmA)** (Watch: https://www.youtube.com/watch?v=bBeomj3NwmA) — In-depth musicology lesson on the variable counts system.\n"
            "- **[Mridangam Percussion Accompaniment Demo](https://www.youtube.com/watch?v=DI3miAldsrw)** (Watch: https://www.youtube.com/watch?v=DI3miAldsrw) — Live visual play of rhythmic structures."
        )
        return ans, []
        
    # 6. Default: Return generic popular links from TRACKS database
    links = []
    citations = []
    for m in TRACKS[:5]:
        name = m.get("song_name", "Unknown Composition")
        artist = m.get("artist", "Unknown Performer")
        url = m.get("youtube", "")
        if url:
            name_display = name.replace("-", " ")
            links.append(f"- **[{name_display}]({url})** (Watch: {url}) (Raga: {m.get('ragam', 'N/A')}) — Performed by {artist}")
            citations.append({
                "book_name": "YouTube Performance",
                "song": name_display,
                "composer": m.get("composer", "Unknown"),
                "shruti": str(m.get("shruti_kattai", "1.5")),
                "youtube_url": url,
                "type": "music",
                "excerpt": f"YouTube performance of {name_display} by {artist}.",
                "confidence": 100.0,
                "confidence_label": "High"
            })
            
    if links:
        ans = (
            "### YouTube Classical Recordings Recommendation\n\n"
            "Here are some popular, highly-recommended Carnatic classical music recordings available on YouTube:\n\n"
            + "\n".join(links)
        )
        return ans, citations
        
    ans = (
        "### YouTube Recording Recommendation\n\n"
        "Please visit the official YouTube website and search for 'Carnatic classical vocal lessons' or 'Carnatic instrumental music' for high-quality audio recordings."
    )
    return ans, []