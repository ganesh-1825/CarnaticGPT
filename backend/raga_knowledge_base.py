"""
CarnaticGPT Raga Knowledge Base
Structured musicological data for 30 curated ragas.
Covers major Carnatic Melakarta/Janya ragas and key Hindustani ragas.
"""

RAGA_KNOWLEDGE_BASE = {
    # ─────────────────────────────────────────────
    # 1. Kalyani
    # ─────────────────────────────────────────────
    "kalyani": {
        "name": "Kalyani",
        "type": "Melakarta",
        "melakarta_number": 65,
        "melakarta_name": "Mechakalyani",
        "parent": "Self (Melakarta 65)",
        "hindustani_equivalent": "Yaman",
        "arohana": "S R2 G3 M2 P D2 N3 S",
        "avarohana": "S N3 D2 P M2 G3 R2 S",
        "swaras": ["S", "R2", "G3", "M2", "P", "D2", "N3"],
        "num_swaras": "Sampurna (7 swaras)",
        "vadi": "M2 (Prati Madhyamam)",
        "samvadi": "S (Shadjam)",
        "gamaka_style": "Uses kampita gamaka predominantly on M2 and G3; the oscillation on M2 (prati madhyama) is the defining gamaka character of Kalyani.",
        "characteristic_phrases": ["S G3 M2 P", "N3 S R2 G3 M2", "P D2 N3 S — the ascent is straight and the descent through G3 M2 is very characteristic"],
        "rasas": ["Majestic", "Devotional", "Grandeur", "Bliss"],
        "time": "Evening",
        "compositions": [
            {"name": "Kamalambam Bhajare", "composer": "Muthuswami Dikshitar"},
            {"name": "Etavunara", "composer": "Tyagaraja"},
            {"name": "Nidhi Chala Sukhama", "composer": "Tyagaraja"},
        ],
        "special_features": [
            "One of the most majestic and widely performed ragas in Carnatic music.",
            "Uses Prati Madhyamam (M2) — this is the key distinguishing feature. Uses prati madhyama (sharp fourth) instead of suddha madhyama.",
            "All seven swaras: Sa, Ri, Ga, Ma (prati), Pa, Da, Ni in both ascent and descent.",
            "65th Melakarta in the Katapayadi classification system.",
            "Equivalent to Hindustani Yaman; often used as a concert opener in North Indian music.",
            "Janya ragas: Hamsanadam, Amruthavarshini, Mohanakalyani and many others.",
        ],
    },
    # ─────────────────────────────────────────────
    # 2. Bhairavi
    # ─────────────────────────────────────────────
    "bhairavi": {
        "name": "Bhairavi",
        "type": "Janya (Bhashanga)",
        "melakarta_number": 20,
        "melakarta_name": "Natabhairavi",
        "parent": "Natabhairavi (Melakarta 20)",
        "hindustani_equivalent": "Bhairavi",
        "arohana": "S R2 G2 M1 P D2 N2 S",
        "avarohana": "S N2 D1 P M1 G2 R2 S",
        "swaras": ["S", "R2", "G2", "M1", "P", "D1", "D2", "N2"],
        "num_swaras": "Sampurna (7 swaras) — Bhashanga: uses D2 in ascent, D1 in descent",
        "vadi": "M1 (Suddha Madhyamam)",
        "samvadi": "S (Shadjam)",
        "gamaka_style": "Heavy use of jaru (slides) and kampita on G2 and N2; the oscillation on G2 (sadharana gandhara) is the most characteristic gamaka. D1 in descent creates the distinctive Bhairavi feel.",
        "characteristic_phrases": ["P D2 N2 S — S N2 D1 P", "M1 G2 R2 S", "G2 M1 P D1 P — the descent D1 is the bhashanga swara"],
        "rasas": ["Karuna", "Bhakti", "Pathos", "Compassion"],
        "time": "Morning",
        "compositions": [
            {"name": "Balagopala", "composer": "Muthuswami Dikshitar"},
            {"name": "Viriboni (Ata Tala Varnam)", "composer": "Pacchimiriam Adiyappaiah"},
            {"name": "Upacharamulanu (Kriti)", "composer": "Saint Tyagaraja"},
        ],
        "special_features": [
            "A Bhashanga raga — borrows D2 (Chatusruti Dhaivata) from outside its parent Natabhairavi (Melakarta 20).",
            "Uses Shuddha Dhaivata (D1) in avarohana and Chatusruti Dhaivata (D2) in arohana.",
            "Traditionally the concluding raga of a Carnatic concert; considered sarva-raga-swaroopini (embodiment of all ragas).",
            "The raga is known for its unique sanchara (melodic movements) and prayoga like P-D-N-S and G-M-P-D1-P.",
            "Classified under Natabhairavi (Melakarta 20) for parent but uses D2 — hence Bhashanga.",
        ],
    },
    # ─────────────────────────────────────────────
    # 3. Hindolam
    # ─────────────────────────────────────────────
    "hindolam": {
        "name": "Hindolam",
        "type": "Janya (Audava — 5 swaras)",
        "melakarta_number": 8,
        "melakarta_name": "Hanuma Todi",
        "parent": "Hanuma Todi (Melakarta 8)",
        "hindustani_equivalent": "Malkouns",
        "arohana": "S G2 M1 D1 N2 S",
        "avarohana": "S N2 D1 M1 G2 S",
        "swaras": ["S", "G2", "M1", "D1", "N2"],
        "num_swaras": "Audava (5 swaras) — Ri (R) and Pa (P) are omitted",
        "vadi": "G2 (Sadharana Gandhara)",
        "samvadi": "N2 (Kaisika Nishada)",
        "gamaka_style": "Slow, heavy kampita gamaka on G2 and D1; the absence of Ri and Pa forces all melodic movement through these gamakas, creating a deeply meditative character.",
        "characteristic_phrases": ["S G2 M1 D1 N2 S", "S N2 D1 M1 G2 S", "N2 S G2 — the opening with N2 going up to S and then G2 is highly characteristic"],
        "rasas": ["Karuna", "Bhakti", "Shanta", "Contemplation"],
        "time": "Night",
        "compositions": [
            {"name": "Saamaja Vara Gamana", "composer": "Tyagaraja"},
            {"name": "Neerajaakshi Kaamaakshi", "composer": "Muthuswami Dikshitar"},
        ],
        "special_features": [
            "An Audava (pentatonic) raga — omits Rishabha (R) and Panchama (P).",
            "Creates a deeply meditative and introspective mood. Equivalent to Hindustani Malkouns.",
            "One of the most ancient pentatonic scales known across world music traditions.",
            "The absence of Rishabha and Panchama creates large interval gaps that force the characteristic gamaka-laden movement.",
        ],
    },
    # ─────────────────────────────────────────────
    # 4. Mohanam
    # ─────────────────────────────────────────────
    "mohanam": {
        "name": "Mohanam",
        "type": "Janya (Audava — 5 swaras)",
        "melakarta_number": 28,
        "melakarta_name": "Harikambhoji",
        "parent": "Harikambhoji (Melakarta 28)",
        "hindustani_equivalent": "Bhoop (Bhoopali)",
        "arohana": "S R2 G3 P D2 S",
        "avarohana": "S D2 P G3 R2 S",
        "swaras": ["S", "R2", "G3", "P", "D2"],
        "num_swaras": "Audava (5 swaras) — Ma (M) and Ni (N) are omitted",
        "vadi": "G3 (Antara Gandhara)",
        "samvadi": "D2 (Chatusruti Dhaivata)",
        "gamaka_style": "Uses nokku (stress/press) gamaka on G3; the intervals are large and clean, creating a bright, universally appealing quality. Gamakas are lighter compared to heavier ragas.",
        "characteristic_phrases": ["S R2 G3 P D2 S", "S D2 P G3 R2 S", "G3 P D2 S — the upper tetrachord movement is the signature phrase"],
        "rasas": ["Joy", "Sweetness", "Devotion", "Happiness"],
        "time": "Anytime",
        "compositions": [
            {"name": "Nannu Brova", "composer": "Tyagaraja"},
            {"name": "Mohana Rama", "composer": "Tyagaraja"},
        ],
        "special_features": [
            "An Audava (pentatonic) raga — omits Madhyama (M) and Nishada (N).",
            "Classification: Janya (derived) raga of Harikambhoji (Melakarta 28).",
            "One of the most popular and universally appealing ragas; extensively used in South Indian film music.",
            "Equivalent to Hindustani Bhoop (Bhoopali).",
        ],
    },
    # ─────────────────────────────────────────────
    # 5. Todi (Shubhapantuvarali)
    # ─────────────────────────────────────────────
    "todi": {
        "name": "Todi (Shubhapantuvarali)",
        "type": "Melakarta",
        "melakarta_number": 45,
        "melakarta_name": "Shubhapantuvarali",
        "parent": "Self (Melakarta 45)",
        "hindustani_equivalent": "Todi",
        "arohana": "S R1 G2 M2 P D1 N2 S",
        "avarohana": "S N2 D1 P M2 G2 R1 S",
        "swaras": ["S", "R1", "G2", "M2", "P", "D1", "N2"],
        "num_swaras": "Sampurna (7 swaras)",
        "vadi": "G2 (Sadharana Gandhara)",
        "samvadi": "N2 (Kaisika Nishada)",
        "gamaka_style": "The most gamaka-intensive raga in Carnatic music. Particularly heavy kampita gamaka on R1 (Shuddha Rishabha) and G2. The R1 is rarely touched without a heavy oscillation. The combination of R1 and M2 creates extreme tonal tension.",
        "characteristic_phrases": ["S R1 G2 M2 — heavy gamaka on R1 and G2", "P D1 N2 S", "G2 M2 G2 R1 S — the descending oscillation is a signature"],
        "rasas": ["Sadness", "Devotion", "Pathos", "Depth"],
        "time": "Morning",
        "compositions": [
            {"name": "Emani Pogathura", "composer": "Tyagaraja"},
            {"name": "Koluvaiyunnade", "composer": "Tyagaraja"},
        ],
        "special_features": [
            "A weighty Melakarta raga known for its deep, intense emotion and gamaka-rich rendering.",
            "Uses both Shuddha Rishabha (R1) and Prati Madhyama (M2), creating a distinctive interval pattern.",
            "One of the most important ragas for elaborate Raga Alapana in concerts.",
            "Often described as the raga that requires the most skill in gamaka execution.",
            "Janya ragas: Suddha Todi, Kurinji, Shuddha Dhanyasi and others.",
        ],
    },
    # ─────────────────────────────────────────────
    # 6. Sankarabharanam
    # ─────────────────────────────────────────────
    "sankarabharanam": {
        "name": "Sankarabharanam",
        "type": "Melakarta",
        "melakarta_number": 29,
        "melakarta_name": "Dheerasankarabharanam",
        "parent": "Self (Melakarta 29)",
        "hindustani_equivalent": "Bilawal",
        "arohana": "S R2 G3 M1 P D2 N3 S",
        "avarohana": "S N3 D2 P M1 G3 R2 S",
        "swaras": ["S", "R2", "G3", "M1", "P", "D2", "N3"],
        "rasas": ["Majestic", "Devotion", "Grandeur", "Serenity"],
        "time": "Anytime",
        "compositions": [
            {"name": "Swara Raga Sudha", "composer": "Tyagaraja"},
            {"name": "Akhilandeswari", "composer": "Muthuswami Dikshitar"},
        ],
        "special_features": [
            "suddha madhyama",
            "Corresponds to the Western major scale (Ionian mode).",
            "One of the most fundamental and important Melakartas in Carnatic music.",
            "Parent of numerous popular Janya ragas like Hamsadhwani, Bilahari, Arabhi, and Nattai.",
        ],
    },
    # ─────────────────────────────────────────────
    # 7. Hamsadhwani
    # ─────────────────────────────────────────────
    "hamsadhwani": {
        "name": "Hamsadhwani",
        "type": "Janya",
        "melakarta_number": 29,
        "melakarta_name": "Dheerasankarabharanam",
        "parent": "Sankarabharanam (Melakarta 29)",
        "hindustani_equivalent": None,
        "arohana": "S R2 G3 P N3 S",
        "avarohana": "S N3 P G3 R2 S",
        "swaras": ["S", "R2", "G3", "P", "N3"],
        "rasas": ["Auspicious", "Bright", "Happy", "Celebration"],
        "time": "Evening",
        "compositions": [
            {"name": "Vatapi Ganapatim", "composer": "Muthuswami Dikshitar"},
            {"name": "Raghuvamsa Sudhambudhi", "composer": "Patnam Subramania Iyer"},
        ],
        "special_features": [
            "pentatonic",
            "An Audava (pentatonic) raga omitting Madhyama and Dhaivata.",
            "Considered highly auspicious; often used to begin concerts.",
            "Vatapi Ganapatim is one of the most famous Carnatic compositions worldwide.",
        ],
    },
    # ─────────────────────────────────────────────
    # 8. Kharaharapriya
    # ─────────────────────────────────────────────
    "kharaharapriya": {
        "name": "Kharaharapriya",
        "type": "Melakarta",
        "melakarta_number": 22,
        "melakarta_name": "Kharaharapriya",
        "parent": "Self (Melakarta 22)",
        "hindustani_equivalent": "Kafi",
        "arohana": "S R2 G2 M1 P D2 N2 S",
        "avarohana": "S N2 D2 P M1 G2 R2 S",
        "swaras": ["S", "R2", "G2", "M1", "P", "D2", "N2"],
        "rasas": ["Devotion", "Serenity", "Contemplation", "Grace"],
        "time": "Anytime",
        "compositions": [
            {"name": "Chakkani Raja", "composer": "Tyagaraja"},
            {"name": "Ramanatham Bhajare", "composer": "Traditional"},
        ],
        "special_features": [
            "Sampurna raga with all seven swaras: Sa, Ri, Ga, Ma, Pa, Da, Ni.",
            "22nd Melakarta raga.",
            "A highly versatile Melakarta raga that serves as the parent for many popular Janya ragas.",
            "Uses Chatusruti Rishabha (R2) and Sadharana Gandhara (G2), giving it a warm, lyrical quality.",
            "Parent to many popular janya ragas including Abhogi, Sriranjani, Suddhadhanyasi, Ritigowla, and Sri Raga.",
        ],
    },
    # ─────────────────────────────────────────────
    # 9. Abhogi
    # ─────────────────────────────────────────────
    "abhogi": {
        "name": "Abhogi",
        "type": "Janya",
        "melakarta_number": 22,
        "melakarta_name": "Kharaharapriya",
        "parent": "Kharaharapriya (Melakarta 22)",
        "hindustani_equivalent": None,
        "arohana": "S R2 G2 M1 D2 S",
        "avarohana": "S D2 M1 G2 R2 S",
        "swaras": ["S", "R2", "G2", "M1", "D2"],
        "rasas": ["Devotion", "Tenderness", "Sweetness"],
        "time": "Anytime",
        "compositions": [
            {"name": "Nagumomu", "composer": "Tyagaraja"},
            {"name": "Abhogi Varnam", "composer": "Traditional"},
        ],
        "special_features": [
            "An Audava (pentatonic) raga omitting Panchama and Nishada.",
            "One of the few ragas that omits the natural fifth (Panchama), creating a unique character.",
            "Nagumomu Ganaleni is one of the most beloved and widely performed Tyagaraja kritis.",
        ],
    },
    # ─────────────────────────────────────────────
    # 10. Revathi
    # ─────────────────────────────────────────────
    "revathi": {
        "name": "Revati (Revathi)",
        "type": "Janya",
        "melakarta_number": 22,
        "melakarta_name": "Kharaharapriya",
        "parent": "Kharaharapriya (Melakarta 22)",
        "hindustani_equivalent": None,
        "arohana": "S R2 G2 M1 P N2 S",
        "avarohana": "S N2 P M1 G2 R2 S",
        "swaras": ["S", "R2", "G2", "M1", "P", "N2"],
        "rasas": ["Serene", "Devotional", "Peace", "Contemplation"],
        "time": "Night",
        "compositions": [
            {"name": "Hari Hari Rama", "composer": "Tyagaraja"},
            {"name": "Revathi Thillana", "composer": "Lalgudi Jayaraman"},
        ],
        "special_features": [
            "A Shadava raga that omits Dhaivata, giving it a serene and nocturnal quality.",
            "Particularly evocative when rendered slowly with gamakas.",
            "Popular choice for concluding pieces in concerts due to its calming mood.",
            "A deeply serene and devotional raga, also spelled Revati.",
        ],
    },
    # ─────────────────────────────────────────────
    # 11. Sivaranjani
    # ─────────────────────────────────────────────
    "sivaranjani": {
        "name": "Sivaranjani",
        "type": "Janya",
        "melakarta_number": 22,
        "melakarta_name": "Kharaharapriya",
        "parent": "Kharaharapriya (Melakarta 22)",
        "hindustani_equivalent": None,
        "arohana": "S R2 G2 P D2 S",
        "avarohana": "S D2 P G2 R2 S",
        "swaras": ["S", "R2", "G2", "P", "D2"],
        "rasas": ["Melancholy", "Romantic", "Nostalgia", "Longing"],
        "time": "Night",
        "compositions": [
            {"name": "Sivaranjani Thillana", "composer": "Lalgudi Jayaraman"},
            {"name": "Film compositions in Sivaranjani", "composer": "Various film composers"},
        ],
        "special_features": [
            "An Audava (pentatonic) raga omitting Madhyama and Nishada.",
            "Extremely popular in South Indian film music for its romantic and melancholic quality.",
            "Though a classical raga, it gained fame primarily through cinematic compositions.",
        ],
    },
    # ─────────────────────────────────────────────
    # 12. Madhyamavathi
    # ─────────────────────────────────────────────
    "madhyamavathi": {
        "name": "Madhyamavathi",
        "type": "Janya",
        "melakarta_number": 22,
        "melakarta_name": "Kharaharapriya",
        "parent": "Kharaharapriya (Melakarta 22)",
        "hindustani_equivalent": None,
        "arohana": "S R2 M1 P N2 S",
        "avarohana": "S N2 P M1 R2 S",
        "swaras": ["S", "R2", "M1", "P", "N2"],
        "rasas": ["Devotion", "Bhakti", "Surrender", "Peace"],
        "time": "Night",
        "compositions": [
            {"name": "Raamabhirami", "composer": "Tyagaraja"},
            {"name": "Madhyamavathi Varnam", "composer": "Traditional"},
        ],
        "special_features": [
            "An Audava (pentatonic) raga omitting Gandhara and Dhaivata.",
            "Considered a powerful raga for devotional singing and bhajans.",
            "Often used as the last raga in a concert before the mangalam.",
        ],
    },
    # ─────────────────────────────────────────────
    # 13. Shuddha Saveri
    # ─────────────────────────────────────────────
    "shuddha_saveri": {
        "name": "Shuddha Saveri",
        "type": "Janya",
        "melakarta_number": 29,
        "melakarta_name": "Dheerasankarabharanam",
        "parent": "Sankarabharanam (Melakarta 29)",
        "hindustani_equivalent": "Durga",
        "arohana": "S R2 M1 P D2 S",
        "avarohana": "S D2 P M1 R2 S",
        "swaras": ["S", "R2", "M1", "P", "D2"],
        "rasas": ["Devotion", "Serenity", "Purity"],
        "time": "Morning",
        "compositions": [
            {"name": "Needu Charana", "composer": "Tyagaraja"},
            {"name": "Shuddha Saveri Varnam", "composer": "Traditional"},
        ],
        "special_features": [
            "An Audava (pentatonic) raga omitting Gandhara and Nishada.",
            "Shares the same scale as Hindustani Durga.",
            "Known for its clean, pure melodic movement with strong devotional appeal.",
        ],
    },
    # ─────────────────────────────────────────────
    # 14. Amruthavarshini
    # ─────────────────────────────────────────────
    "amruthavarshini": {
        "name": "Amruthavarshini",
        "type": "Janya",
        "melakarta_number": 65,
        "melakarta_name": "Mechakalyani",
        "parent": "Mechakalyani (Melakarta 65)",
        "hindustani_equivalent": None,
        "arohana": "S G3 M2 P N3 S",
        "avarohana": "S N3 P M2 G3 S",
        "swaras": ["S", "G3", "M2", "P", "N3"],
        "rasas": ["Auspicious", "Joy", "Wonder", "Rain"],
        "time": "Anytime (rain raga)",
        "compositions": [
            {"name": "Anandamritakarshini", "composer": "Muthuswami Dikshitar"},
            {"name": "Amruthavarshini Kriti", "composer": "Traditional"},
        ],
        "special_features": [
            "An Audava (pentatonic) raga believed to have the power to bring rain.",
            "Dikshitar's Anandamritakarshini is legendarily associated with rain invocation.",
            "Uses Prati Madhyama (M2) and Antara Gandhara (G3), creating a bright, uplifting mood.",
        ],
    },
    # ─────────────────────────────────────────────
    # 15. Hamsanadam
    # ─────────────────────────────────────────────
    "hamsanadam": {
        "name": "Hamsanadam",
        "type": "Janya",
        "melakarta_number": 65,
        "melakarta_name": "Mechakalyani",
        "parent": "Mechakalyani (Melakarta 65)",
        "hindustani_equivalent": None,
        "arohana": "S R2 M2 P N3 S",
        "avarohana": "S N3 P M2 R2 S",
        "swaras": ["S", "R2", "M2", "P", "N3"],
        "rasas": ["Majestic", "Devotion", "Brilliance"],
        "time": "Evening",
        "compositions": [
            {"name": "Hamsanadam Thillana", "composer": "Traditional"},
            {"name": "Bantureethi Kolu (some renditions)", "composer": "Tyagaraja"},
        ],
        "special_features": [
            "An Audava (pentatonic) raga omitting Gandhara and Dhaivata.",
            "Uses Prati Madhyama (M2), distinguishing it from similar pentatonic ragas.",
            "Known for its bright, regal quality and is often used for lively compositions.",
        ],
    },
    # ─────────────────────────────────────────────
    # 16. Bilahari
    # ─────────────────────────────────────────────
    "bilahari": {
        "name": "Bilahari",
        "type": "Janya",
        "melakarta_number": 29,
        "melakarta_name": "Dheerasankarabharanam",
        "parent": "Sankarabharanam (Melakarta 29)",
        "hindustani_equivalent": None,
        "arohana": "S R2 G3 P D2 S",
        "avarohana": "S N3 D2 P M1 G3 R2 S",
        "swaras": ["S", "R2", "G3", "M1", "P", "D2", "N3"],
        "rasas": ["Courage", "Valor", "Joy", "Energy"],
        "time": "Morning",
        "compositions": [
            {"name": "Thillana in Bilahari", "composer": "Poochi Srinivasa Iyengar"},
            {"name": "Namo Namo Raghavaya", "composer": "Tyagaraja"},
        ],
        "special_features": [
            "Asymmetric janya raga: ascent uses five swaras (Sa, Ri, Ga, Pa, Da) while descent uses all seven: Sa, Ni, Da, Pa, Ma, Ga, Ri.",
            "An asymmetric (Vakra) raga: pentatonic in arohana but heptatonic in avarohana.",
            "Conveys a bright, heroic, and energetic mood.",
            "Popular raga for Thillanas and lively concert pieces.",
            "Vakra prayoga in descent.",
        ],
    },
    # ─────────────────────────────────────────────
    # 17. Kamboji
    # ─────────────────────────────────────────────
    "kamboji": {
        "name": "Kamboji",
        "type": "Janya",
        "melakarta_number": 28,
        "melakarta_name": "Harikambhoji",
        "parent": "Harikambhoji (Melakarta 28)",
        "hindustani_equivalent": None,
        "arohana": "S R2 G3 M1 P D2 S",
        "avarohana": "S N2 D2 P M1 G3 R2 S",
        "swaras": ["S", "R2", "G3", "M1", "P", "D2", "N2"],
        "rasas": ["Grandeur", "Devotion", "Majesty", "Depth"],
        "time": "Evening",
        "compositions": [
            {"name": "Sri Subramanyaya Namaste", "composer": "Muthuswami Dikshitar"},
            {"name": "Chetulara", "composer": "Tyagaraja"},
        ],
        "special_features": [
            "A Bhashanga raga; Nishada appears only in the avarohana as Kaisiki Nishada (N2).",
            "One of the Ghana ragas of Carnatic music, considered ancient and venerable.",
            "Often referred to as the 'King of Ragas' (Ragaraja) due to its stately character.",
        ],
    },
    # ─────────────────────────────────────────────
    # 18. Charukesi
    # ─────────────────────────────────────────────
    "charukesi": {
        "name": "Charukesi",
        "type": "Melakarta",
        "melakarta_number": 26,
        "melakarta_name": "Charukesi",
        "parent": "Self (Melakarta 26)",
        "hindustani_equivalent": None,
        "arohana": "S R2 G3 M1 P D1 N2 S",
        "avarohana": "S N2 D1 P M1 G3 R2 S",
        "swaras": ["S", "R2", "G3", "M1", "P", "D1", "N2"],
        "rasas": ["Bright", "Romantic", "Melancholy", "Longing"],
        "time": "Anytime",
        "compositions": [
            {"name": "Charukesi film compositions", "composer": "Various film composers"},
            {"name": "Charukesi Kriti", "composer": "Traditional"},
        ],
        "special_features": [
            "Sampurna raga with all seven swaras: Sa, Ri, Ga, Ma, Pa, Da, Ni.",
            "26th Melakarta raga.",
            "Combines the bright upper tetrachord of Sankarabharanam with the minor lower tetrachord.",
            "Very popular in film music due to its versatile emotional range.",
            "Equivalent to the Western Mixolydian b6 mode.",
        ],
    },
    # ─────────────────────────────────────────────
    # 19. Keeravani
    # ─────────────────────────────────────────────
    "keeravani": {
        "name": "Keeravani",
        "type": "Melakarta",
        "melakarta_number": 21,
        "melakarta_name": "Keeravani",
        "parent": "Self (Melakarta 21)",
        "hindustani_equivalent": "Kirwani",
        "arohana": "S R2 G2 M1 P D1 N3 S",
        "avarohana": "S N3 D1 P M1 G2 R2 S",
        "swaras": ["S", "R2", "G2", "M1", "P", "D1", "N3"],
        "rasas": ["Pathos", "Devotion", "Intensity", "Longing"],
        "time": "Night",
        "compositions": [
            {"name": "Keeravani Kriti", "composer": "Traditional"},
            {"name": "Film compositions in Keeravani", "composer": "Various film composers"},
        ],
        "special_features": [
            "Corresponds to the Western harmonic minor scale.",
            "The combination of Shuddha Dhaivata (D1) and Kakali Nishada (N3) creates a distinctive pull.",
            "Gaining increasing popularity in modern Carnatic and film music.",
        ],
    },
    # ─────────────────────────────────────────────
    # 20. Anandabhairavi
    # ─────────────────────────────────────────────
    "anandabhairavi": {
        "name": "Anandabhairavi",
        "type": "Janya",
        "melakarta_number": 20,
        "melakarta_name": "Natabhairavi",
        "parent": "Natabhairavi (Melakarta 20)",
        "hindustani_equivalent": None,
        "arohana": "S G2 R2 G2 M1 P D2 P S",
        "avarohana": "S N2 D2 P M1 G2 R2 S",
        "swaras": ["S", "R2", "G2", "M1", "P", "D2", "N2"],
        "rasas": ["Bhakti", "Peace", "Love", "Devotion"],
        "time": "Morning",
        "compositions": [
            {"name": "Sobillu Saptaswara", "composer": "Tyagaraja"},
            {"name": "Anandabhairavi Varnam", "composer": "Traditional"},
        ],
        "special_features": [
            "A Bhashanga raga with a characteristic vakra (zigzag) arohana: S G2 R2 G2 M1.",
            "The vakra prayoga gives it a uniquely graceful and winding melodic movement.",
            "One of the oldest ragas in Carnatic tradition with deep emotional resonance.",
        ],
    },
    # ─────────────────────────────────────────────
    # 21. Bhupalam
    # ─────────────────────────────────────────────
    "bhupalam": {
        "name": "Bhupalam",
        "type": "Janya",
        "melakarta_number": 15,
        "melakarta_name": "Mayamalavagowla",
        "parent": "Mayamalavagowla (Melakarta 15)",
        "hindustani_equivalent": None,
        "arohana": "S R1 G2 P D1 S",
        "avarohana": "S D1 P G2 R1 S",
        "swaras": ["S", "R1", "G2", "P", "D1"],
        "rasas": ["Devotion", "Serenity", "Dawn", "Peace"],
        "time": "Early morning (Prathah Sandhya)",
        "compositions": [
            {"name": "Vere Marulanu", "composer": "Tyagaraja"},
            {"name": "Bhupalam Kriti", "composer": "Traditional"},
        ],
        "special_features": [
            "An Audava (pentatonic) raga strongly associated with early morning and dawn.",
            "Uses Shuddha Rishabha (R1) and Shuddha Dhaivata (D1), giving it a solemn quality.",
            "Traditionally the first raga sung in a concert or during morning worship.",
        ],
    },
    # ─────────────────────────────────────────────
    # 22. Arabhi
    # ─────────────────────────────────────────────
    "arabhi": {
        "name": "Arabhi",
        "type": "Janya",
        "melakarta_number": 29,
        "melakarta_name": "Dheerasankarabharanam",
        "parent": "Sankarabharanam (Melakarta 29)",
        "hindustani_equivalent": None,
        "arohana": "S R2 M1 P D2 S",
        "avarohana": "S N3 D2 P M1 G3 R2 S",
        "swaras": ["S", "R2", "G3", "M1", "P", "D2", "N3"],
        "rasas": ["Valor", "Courage", "Devotion", "Brightness"],
        "time": "Morning",
        "compositions": [
            {"name": "Saramaina", "composer": "Tyagaraja"},
            {"name": "Arabhi Varnam", "composer": "Traditional"},
        ],
        "special_features": [
            "An asymmetric raga: pentatonic (Audava) in arohana, heptatonic (Sampoorna) in avarohana.",
            "One of the Ghana ragas of Carnatic music, often featured in concert openings.",
            "The absence of G3 and N3 in arohana but their presence in avarohana creates a distinctive color.",
        ],
    },
    # ─────────────────────────────────────────────
    # 23. Nattai
    # ─────────────────────────────────────────────
    "nattai": {
        "name": "Nattai",
        "type": "Janya",
        "melakarta_number": 29,
        "melakarta_name": "Dheerasankarabharanam",
        "parent": "Sankarabharanam (Melakarta 29)",
        "hindustani_equivalent": None,
        "arohana": "S R2 G3 M1 P N3 S",
        "avarohana": "S N3 P M1 G3 R2 S",
        "swaras": ["S", "R2", "G3", "M1", "P", "N3"],
        "rasas": ["Valor", "Energy", "Grandeur", "Auspiciousness"],
        "time": "Morning",
        "compositions": [
            {"name": "Maha Ganapathim", "composer": "Muthuswami Dikshitar"},
            {"name": "Nattai Varnam", "composer": "Traditional"},
        ],
        "special_features": [
            "A Shadava raga omitting Dhaivata, giving it a bold and bright character.",
            "Traditionally the first raga used to begin Carnatic concerts (after invocation).",
            "Maha Ganapathim is one of the most popular concert-opening compositions.",
        ],
    },
    # ─────────────────────────────────────────────
    # 24. Yaman (Hindustani)
    # ─────────────────────────────────────────────
    "yaman": {
        "name": "Yaman",
        "type": "Melakarta",
        "melakarta_number": 65,
        "melakarta_name": "Mechakalyani",
        "parent": "Equivalent to Kalyani (Melakarta 65)",
        "hindustani_equivalent": "Yaman (self)",
        "arohana": "S R G M(tivra) P D N S",
        "avarohana": "S N D P M(tivra) G R S",
        "swaras": ["S", "R", "G", "M(tivra)", "P", "D", "N"],
        "rasas": ["Romance", "Devotion", "Serenity", "Bliss"],
        "time": "Evening / Night",
        "compositions": [
            {"name": "Various traditional bandishes", "composer": "Traditional"},
            {"name": "Ek Din Ban Ke (film)", "composer": "Various"},
        ],
        "special_features": [
            "One of the most important and foundational ragas of Hindustani music.",
            "Uses Tivra Madhyam (sharp fourth), equivalent to Prati Madhyama in Carnatic.",
            "Same scale as Carnatic Kalyani (Melakarta 65); often the first raga taught to students.",
        ],
    },
    # ─────────────────────────────────────────────
    # 25. Mayamalavagowla
    # ─────────────────────────────────────────────
    "mayamalavagowla": {
        "name": "Mayamalavagowla",
        "type": "Melakarta",
        "melakarta_number": 15,
        "melakarta_name": "Mayamalavagowla",
        "parent": "Self (Melakarta 15)",
        "hindustani_equivalent": "Bhairav",
        "arohana": "S R1 G3 M1 P D1 N3 S",
        "avarohana": "S N3 D1 P M1 G3 R1 S",
        "swaras": ["S", "R1", "G3", "M1", "P", "D1", "N3"],
        "rasas": ["Serenity", "Devotion", "Pedagogical Baseline", "Solemnity"],
        "time": "Anytime",
        "compositions": [
            {"name": "Deva Deva Kalayami", "composer": "Traditional"},
            {"name": "Merusamana", "composer": "Swathi Thirunal"},
            {"name": "Sri Gananatha", "composer": "Traditional"},
        ],
        "special_features": [
            "The fundamental and basic baseline raga for all Carnatic beginners due to its symmetrical structure.",
            "Uses Shuddha Rishabha (R1), Antara Gandhara (G3), Shuddha Dhaivata (D1), and Kakali Nishada (N3).",
            "Equivalent to Hindustani Bhairav; the 15th Melakarta in the Katapayadi scheme.",
        ],
    },
    # ─────────────────────────────────────────────
    # 26. Bhairav (Hindustani)
    # ─────────────────────────────────────────────
    "bhairav": {
        "name": "Bhairav",
        "type": "Melakarta",
        "melakarta_number": 15,
        "melakarta_name": "Mayamalavagowla",
        "parent": "Equivalent to Mayamalavagowla (Melakarta 15)",
        "hindustani_equivalent": "Bhairav (self)",
        "arohana": "S r G M P d N S",
        "avarohana": "S N d P M G r S",
        "swaras": ["S", "r (komal Re)", "G (shuddha)", "M", "P", "d (komal Dha)", "N (shuddha)"],
        "rasas": ["Grandeur", "Devotion", "Solemnity", "Majesty"],
        "time": "Morning",
        "compositions": [
            {"name": "Various traditional bandishes", "composer": "Traditional"},
            {"name": "Man Tarpat Hari Darshan Ko", "composer": "Traditional Dhrupad"},
        ],
        "special_features": [
            "One of the six primary ragas in the Hindustani system.",
            "Uses Komal Rishabh and Komal Dhaivat with Shuddha Gandhara and Nishada.",
            "Same scale as Carnatic Mayamalavagowla (Melakarta 15); a morning raga of great depth.",
        ],
    },
    # ─────────────────────────────────────────────
    # 26. Bageshri (Hindustani)
    # ─────────────────────────────────────────────
    "bageshri": {
        "name": "Bageshri",
        "type": "Janya",
        "melakarta_number": 22,
        "melakarta_name": "Kharaharapriya",
        "parent": "Close to Sriranjani in Carnatic (Kharaharapriya family)",
        "hindustani_equivalent": "Bageshri (self)",
        "arohana": "S G2 M1 D2 N2 S",
        "avarohana": "S N2 D2 M1 G2 R2 S",
        "swaras": ["S", "R2", "G2", "M1", "D2", "N2"],
        "rasas": ["Romance", "Longing", "Shringara", "Tenderness"],
        "time": "Night",
        "compositions": [
            {"name": "Various traditional bandishes", "composer": "Traditional"},
            {"name": "Bageshri Thumri", "composer": "Traditional"},
        ],
        "special_features": [
            "A prominent late-night raga in Hindustani music with deep romantic appeal.",
            "Rishabha is omitted in arohana but appears in avarohana, creating asymmetry.",
            "Close to the Carnatic raga Sriranjani; heavily used in thumri and ghazal genres.",
        ],
    },
    # ─────────────────────────────────────────────
    # 27. Darbari Kanada (Hindustani)
    # ─────────────────────────────────────────────
    "darbari_kanada": {
        "name": "Darbari Kanada",
        "type": "Janya",
        "melakarta_number": 22,
        "melakarta_name": "Kharaharapriya",
        "parent": "Close to Kharaharapriya family in Carnatic",
        "hindustani_equivalent": "Darbari Kanada (self)",
        "arohana": "S R2 G2 M1 P D1 N2 S",
        "avarohana": "S N2 D1 P M1 G2 R2 S",
        "swaras": ["S", "R2", "G2", "M1", "P", "D1", "N2"],
        "rasas": ["Majesty", "Grandeur", "Depth", "Gravity"],
        "time": "Night",
        "compositions": [
            {"name": "Traditional Dhrupad bandishes", "composer": "Traditional"},
            {"name": "Various vilambit khayal compositions", "composer": "Traditional"},
        ],
        "special_features": [
            "A very slow, majestic raga associated with the court of Emperor Akbar via Tansen.",
            "Characterized by heavy, slow andolan (oscillation) on Gandhara and Dhaivata.",
            "One of the most profound and difficult ragas in Hindustani music to render correctly.",
        ],
    },
    # ─────────────────────────────────────────────
    # 28. Malkouns (Hindustani)
    # ─────────────────────────────────────────────
    "malkouns": {
        "name": "Malkouns",
        "type": "Janya",
        "melakarta_number": 8,
        "melakarta_name": "Hanuma Todi",
        "parent": "Same as Hindolam in Carnatic (Hanuma Todi family)",
        "hindustani_equivalent": "Malkouns (self)",
        "arohana": "S G2 M1 D1 N2 S",
        "avarohana": "S N2 D1 M1 G2 S",
        "swaras": ["S", "G2", "M1", "D1", "N2"],
        "rasas": ["Devotion", "Peace", "Night", "Contemplation"],
        "time": "Night",
        "compositions": [
            {"name": "Man Tarpat Hari Darshan Ko (some renditions)", "composer": "Traditional"},
            {"name": "Various traditional bandishes", "composer": "Traditional"},
        ],
        "special_features": [
            "An Audava (pentatonic) raga identical in scale to Carnatic Hindolam.",
            "One of the oldest ragas, considered very meditative and devotional.",
            "Omits Rishabha and Panchama, creating a deeply introspective, inward quality.",
        ],
    },
    # ─────────────────────────────────────────────
    # 29. Desh (Hindustani)
    # ─────────────────────────────────────────────
    "desh": {
        "name": "Desh",
        "type": "Janya",
        "melakarta_number": 28,
        "melakarta_name": "Harikambhoji",
        "parent": "Close to Deshya Todi in Carnatic",
        "hindustani_equivalent": "Desh (self)",
        "arohana": "S R2 G3 M1 P N2 S",
        "avarohana": "S N2 D2 P M1 G2 R2 S",
        "swaras": ["S", "R2", "G2", "G3", "M1", "P", "D2", "N2"],
        "rasas": ["Patriotic", "Romance", "Sweetness", "Light"],
        "time": "Night",
        "compositions": [
            {"name": "Sare Jahan Se Accha (popular tune)", "composer": "Traditional"},
            {"name": "Various light classical compositions", "composer": "Traditional"},
        ],
        "special_features": [
            "A light, romantic raga strongly associated with patriotic and seasonal songs in India.",
            "Uses different Gandhara in arohana (Antara G3) and avarohana (Sadharana G2).",
            "Widely used in semi-classical, thumri, and film music contexts.",
        ],
    },
    # ─────────────────────────────────────────────
    # 30. Durga (Hindustani / Carnatic)
    # ─────────────────────────────────────────────
    "durga": {
        "name": "Durga",
        "type": "Janya",
        "melakarta_number": 29,
        "melakarta_name": "Dheerasankarabharanam",
        "parent": "Same as Shuddha Saveri in Carnatic (Sankarabharanam family)",
        "hindustani_equivalent": "Durga (self)",
        "arohana": "S R2 M1 P D2 S",
        "avarohana": "S D2 P M1 R2 S",
        "swaras": ["S", "R2", "M1", "P", "D2"],
        "rasas": ["Devotion", "Valor", "Strength", "Purity"],
        "time": "Night",
        "compositions": [
            {"name": "Various traditional bandishes", "composer": "Traditional"},
            {"name": "Durga Bhajan compositions", "composer": "Traditional"},
        ],
        "special_features": [
            "An Audava (pentatonic) raga identical to Carnatic Shuddha Saveri.",
            "Associated with the Goddess Durga and often used in devotional contexts.",
            "A raga of simplicity and power, conveying strength through its clean pentatonic lines.",
        ],
    },
    # ─────────────────────────────────────────────
    # 31. Natabhairavi
    # ─────────────────────────────────────────────
    "natabhairavi": {
        "name": "Natabhairavi",
        "type": "Melakarta",
        "melakarta_number": 20,
        "melakarta_name": "Natabhairavi",
        "parent": "Self (Melakarta 20)",
        "hindustani_equivalent": None,
        "arohana": "S R2 G2 M1 P D1 N2 S",
        "avarohana": "S N2 D1 P M1 G2 R2 S",
        "swaras": ["S", "R2", "G2", "M1", "P", "D1", "N2"],
        "rasas": ["Pathos", "Devotion", "Compassion"],
        "time": "Any time",
        "compositions": [
            {"name": "Aparadhamulu", "composer": "Tyagaraja"},
        ],
        "special_features": [
            "Sampurna raga with all seven swaras: Sa, Ri, Ga, Ma, Pa, Da, Ni.",
            "20th Melakarta raga.",
            "Parent of the famous Bhairavi raga (Bhashanga janya).",
        ],
    },
    # ─────────────────────────────────────────────
    # 32. Shanmukhapriya
    # ─────────────────────────────────────────────
    "shanmukhapriya": {
        "name": "Shanmukhapriya",
        "type": "Melakarta",
        "melakarta_number": 56,
        "melakarta_name": "Shanmukhapriya",
        "parent": "Self (Melakarta 56)",
        "hindustani_equivalent": None,
        "arohana": "S R2 G2 M2 P D1 N2 S",
        "avarohana": "S N2 D1 P M2 G2 R2 S",
        "swaras": ["S", "R2", "G2", "M2", "P", "D1", "N2"],
        "rasas": ["Valor", "Devotion", "Grandeur"],
        "time": "Any time",
        "compositions": [
            {"name": "Dayarani Dayarani", "composer": "Tyagaraja"},
        ],
        "special_features": [
            "Sampurna raga with all seven swaras: Sa, Ri, Ga, Ma (prati), Pa, Da, Ni.",
            "56th Melakarta raga using Prati Madhyamam.",
        ],
    },
    # ─────────────────────────────────────────────
    # 33. Simhendramadhyama
    # ─────────────────────────────────────────────
    "simhendramadhyama": {
        "name": "Simhendramadhyama",
        "type": "Melakarta",
        "melakarta_number": 57,
        "melakarta_name": "Simhendramadhyama",
        "parent": "Self (Melakarta 57)",
        "hindustani_equivalent": None,
        "arohana": "S R2 G3 M2 P D1 N2 S",
        "avarohana": "S N2 D1 P M2 G3 R2 S",
        "swaras": ["S", "R2", "G3", "M2", "P", "D1", "N2"],
        "rasas": ["Grandeur", "Devotion", "Majesty"],
        "time": "Any time",
        "compositions": [
            {"name": "Raga Sudha Rasa", "composer": "Tyagaraja"},
        ],
        "special_features": [
            "Sampurna raga with all seven swaras: Sa, Ri, Ga, Ma (prati), Pa, Da, Ni.",
            "57th Melakarta raga.",
            "Known for its majestic and grand quality.",
        ],
    },
    # ─────────────────────────────────────────────
    # 34. Sriranjani
    # ─────────────────────────────────────────────
    "sriranjani": {
        "name": "Sriranjani",
        "type": "Janya",
        "melakarta_number": 22,
        "melakarta_name": "Kharaharapriya",
        "parent": "Kharaharapriya (Melakarta 22)",
        "hindustani_equivalent": None,
        "arohana": "S R2 G2 M1 D2 N2 S",
        "avarohana": "S N2 D2 M1 G2 R2 S",
        "swaras": ["S", "R2", "G2", "M1", "D2", "N2"],
        "rasas": ["Devotion", "Tenderness", "Romance"],
        "time": "Night",
        "compositions": [
            {"name": "Koluvaiyunnade", "composer": "Tyagaraja"},
        ],
        "special_features": [
            "Shadava janya raga with six swaras: Sa, Ri, Ga, Ma, Da, Ni (Pa omitted).",
            "Known for its delicate and devotional quality.",
        ],
    },
    # ─────────────────────────────────────────────
    # 35. Sahana
    # ─────────────────────────────────────────────
    "sahana": {
        "name": "Sahana",
        "type": "Janya",
        "melakarta_number": 28,
        "melakarta_name": "Harikambhoji",
        "parent": "Harikambhoji (Melakarta 28)",
        "hindustani_equivalent": None,
        "arohana": "S R2 G3 M1 P M1 D2 N2 S",
        "avarohana": "S N2 D2 P M1 G3 R2 G3 S",
        "swaras": ["S", "R2", "G3", "M1", "P", "D2", "N2"],
        "rasas": ["Devotion", "Peace", "Love"],
        "time": "Night",
        "compositions": [
            {"name": "Sri Subrahmanyaya", "composer": "Dikshitar"},
        ],
        "special_features": [
            "Vakra (zig-zag) janya raga with all seven swaras: Sa, Ri, Ga, Ma, Pa, Da, Ni appearing in irregular progression.",
            "Characteristic vakra prayoga in both ascent and descent.",
        ],
    },
    # ─────────────────────────────────────────────
    # 36. Begada
    # ─────────────────────────────────────────────
    "begada": {
        "name": "Begada",
        "type": "Janya",
        "melakarta_number": 29,
        "melakarta_name": "Dheerasankarabharanam",
        "parent": "Dheerashankarabharanam (Melakarta 29)",
        "hindustani_equivalent": None,
        "arohana": "S G3 R2 G3 M1 P D2 N3 S",
        "avarohana": "S N3 D2 P M1 G3 R2 S",
        "swaras": ["S", "R2", "G3", "M1", "P", "D2", "N3"],
        "rasas": ["Devotion", "Majesty", "Grandeur"],
        "time": "Morning",
        "compositions": [
            {"name": "Evarura", "composer": "Tyagaraja"},
        ],
        "special_features": [
            "Vakra (zig-zag) janya raga with all seven swaras: Sa, Ri, Ga, Ma, Pa, Da, Ni in irregular order.",
            "Vakra prayoga S-G-R-G in ascent is characteristic.",
        ],
    },
    # ─────────────────────────────────────────────
    # 37. Vasanta
    # ─────────────────────────────────────────────
    "vasanta": {
        "name": "Vasanta",
        "type": "Janya",
        "melakarta_number": 17,
        "melakarta_name": "Suryakantam",
        "parent": "Suryakantam (Melakarta 17)",
        "hindustani_equivalent": None,
        "arohana": "S G3 M1 D1 N3 S",
        "avarohana": "S N3 D1 M1 G3 R1 S",
        "swaras": ["S", "R1", "G3", "M1", "D1", "N3"],
        "rasas": ["Joy", "Romance", "Spring"],
        "time": "Spring/Morning",
        "compositions": [
            {"name": "Sri Ramam", "composer": "Dikshitar"},
        ],
        "special_features": [
            "Shadava janya raga with six swaras: Sa, Ri, Ga, Ma, Da, Ni (Pa omitted in both ascent and descent).",
            "Associated with the season of spring (Vasanta Ritu).",
        ],
    },
    # ─────────────────────────────────────────────
    # 38. Ritigowla
    # ─────────────────────────────────────────────
    "ritigowla": {
        "name": "Ritigowla",
        "type": "Janya",
        "melakarta_number": 22,
        "melakarta_name": "Kharaharapriya",
        "parent": "Kharaharapriya (Melakarta 22)",
        "hindustani_equivalent": None,
        "arohana": "S G2 R2 G2 M1 N2 D2 N2 S",
        "avarohana": "S N2 D2 M1 G2 R2 S",
        "swaras": ["S", "R2", "G2", "M1", "P", "D2", "N2"],
        "rasas": ["Devotion", "Pathos", "Yearning"],
        "time": "Night",
        "compositions": [
            {"name": "Sowmya Dasarate", "composer": "Tyagaraja"},
        ],
        "special_features": [
            "Vakra (zig-zag) janya raga with all seven swaras: Sa, Ri, Ga, Ma, Pa, Da, Ni in irregular order.",
            "Pa is used only in avarohana; arohana skips from Ma to Ni.",
        ],
    },
    # ─────────────────────────────────────────────
    # 39. Sri Raga
    # ─────────────────────────────────────────────
    "sri": {
        "name": "Sri Raga",
        "type": "Janya",
        "melakarta_number": 22,
        "melakarta_name": "Kharaharapriya",
        "parent": "Kharaharapriya (Melakarta 22)",
        "hindustani_equivalent": None,
        "arohana": "S R2 M1 P N2 S",
        "avarohana": "S N2 P D2 N2 P M1 R2 G2 R2 S",
        "swaras": ["S", "R2", "G2", "M1", "P", "D2", "N2"],
        "rasas": ["Devotion", "Majesty", "Auspiciousness"],
        "time": "Evening",
        "compositions": [
            {"name": "Endaro Mahanubhavulu", "composer": "Tyagaraja"},
        ],
        "special_features": [
            "Vakra janya raga with all seven swaras: Sa, Ri, Ga, Ma, Pa, Da, Ni — Ga and Da appear only in avarohana.",
            "One of the five Pancharatna Kritis ragas.",
            "Also known simply as 'Sri'.",
        ],
    },
    # ─────────────────────────────────────────────
    # 40. Suddhadhanyasi
    # ─────────────────────────────────────────────
    "suddhadhanyasi": {
        "name": "Suddhadhanyasi",
        "type": "Janya",
        "melakarta_number": 22,
        "melakarta_name": "Kharaharapriya",
        "parent": "Kharaharapriya (Melakarta 22)",
        "hindustani_equivalent": None,
        "arohana": "S G2 M1 P N2 S",
        "avarohana": "S N2 P M1 G2 S",
        "swaras": ["S", "G2", "M1", "P", "N2"],
        "rasas": ["Devotion", "Peace", "Simplicity"],
        "time": "Any time",
        "compositions": [
            {"name": "Brochevarevarura", "composer": "Mysore Vasudevacharya"},
        ],
        "special_features": [
            "Audava (pentatonic) janya raga with five swaras: Sa, Ga, Ma, Pa, Ni (Ri and Da omitted).",
            "Known for its simple, devotional quality.",
        ],
    },
}

# ──────────────────────────────────────────────────────────────
# Raga Aliases (alternate spellings / names -> canonical keys)
# ──────────────────────────────────────────────────────────────
RAGA_ALIASES = {
    # Carnatic alternate spellings
    "shankarabharanam": "sankarabharanam",
    "dheerasankarabharanam": "sankarabharanam",
    "shubhapantuvarali": "todi",
    "subhapantuvarali": "todi",
    "mechakalyani": "kalyani",
    "mecha kalyani": "kalyani",
    "natabhairavi": "natabhairavi",
    "harikambhoji": "kamboji",
    "hamsadwani": "hamsadhwani",
    "hamsa dhwani": "hamsadhwani",
    "karaharapriya": "kharaharapriya",
    "kara hara priya": "kharaharapriya",
    "ananda bhairavi": "anandabhairavi",
    "shuddhasaveri": "shuddha_saveri",
    "suddha saveri": "shuddha_saveri",
    "suddhasaveri": "shuddha_saveri",
    "amritavarshini": "amruthavarshini",
    "amritha varshini": "amruthavarshini",
    "madhyamavati": "madhyamavathi",
    "sivaranjini": "sivaranjani",
    "shiva ranjani": "sivaranjani",
    "revati": "revathi",
    "mayamalavagaula": "mayamalavagowla",
    # New raga aliases
    "nata bhairavi": "natabhairavi",
    "shanmukha priya": "shanmukhapriya",
    "sanmukhapriya": "shanmukhapriya",
    "simhendra madhyama": "simhendramadhyama",
    "simhendramadhyamam": "simhendramadhyama",
    "sri ranjani": "sriranjani",
    "sree ranjani": "sriranjani",
    "sri raga": "sri",
    "sriraga": "sri",
    "sree": "sri",
    "suddha dhanyasi": "suddhadhanyasi",
    "shuddhadhanyasi": "suddhadhanyasi",
    "shuddha dhanyasi": "suddhadhanyasi",
    "rithi gowla": "ritigowla",
    "riti gowla": "ritigowla",
    "vasantham": "vasanta",
    "begade": "begada",

    # Hindustani alternate spellings
    "kirwani": "keeravani",
    "keervani": "keeravani",
    "malkauns": "malkouns",
    "malkosh": "malkouns",
    "bhairavi_hindustani": "bhairavi",
    "yaman_kalyan": "yaman",
    "darbari": "darbari_kanada",
    "kanada": "darbari_kanada",
    "darbari kanada": "darbari_kanada",
    "bageshree": "bageshri",
    "baageshri": "bageshri",
    "bhoop": "mohanam",
    "bhoopali": "mohanam",
    "bhoopalam": "bhupalam",
    "bilawal": "sankarabharanam",
    "kambhoji": "kamboji",
    "kafi": "kharaharapriya",
}

# ──────────────────────────────────────────────────────────────
# Convenience exports
# ──────────────────────────────────────────────────────────────
SUPPORTED_RAGA_NAMES = list(RAGA_KNOWLEDGE_BASE.keys())


# ──────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────

def get_raga_info(raga_name: str) -> dict:
    """
    Look up a raga by name (case-insensitive, handles aliases).

    Args:
        raga_name: The raga name to look up (e.g. 'kalyani', 'Shankarabharanam', 'yaman').

    Returns:
        A dictionary with raga information, or an empty dict if not found.
    """
    if not raga_name:
        return {}

    key = raga_name.strip().lower().replace("-", "").replace("_", " ")

    # Direct lookup (with underscore normalization)
    normalized_key = key.replace(" ", "_")
    if normalized_key in RAGA_KNOWLEDGE_BASE:
        return RAGA_KNOWLEDGE_BASE[normalized_key]

    # Try without underscores
    no_space_key = key.replace(" ", "")
    for raga_key in RAGA_KNOWLEDGE_BASE:
        if raga_key.replace("_", "") == no_space_key:
            return RAGA_KNOWLEDGE_BASE[raga_key]

    # Alias lookup
    alias_key = key.replace(" ", "_")
    if alias_key in RAGA_ALIASES:
        canonical = RAGA_ALIASES[alias_key]
        return RAGA_KNOWLEDGE_BASE.get(canonical, {})

    # Try alias without underscores
    alias_no_space = key.replace(" ", "")
    for alias, canonical in RAGA_ALIASES.items():
        if alias.replace("_", "").replace(" ", "") == alias_no_space:
            return RAGA_KNOWLEDGE_BASE.get(canonical, {})

    # Partial / substring match (fallback)
    for raga_key, raga_data in RAGA_KNOWLEDGE_BASE.items():
        display_name = raga_data["name"].lower()
        if key in raga_key or key in display_name:
            return raga_data

    return {}


def find_raga_key(query: str) -> str:
    """
    Search a query string for any raga name and return the canonical key.
    Useful for extracting the raga from a user's natural language query.

    Args:
        query: A natural language string that may contain a raga name.

    Returns:
        The canonical key (e.g. 'kalyani') if found, or an empty string.
    """
    if not query:
        return ""

    query_lower = query.lower()

    # Check longest names first to avoid partial matches
    all_names = []
    for key, data in RAGA_KNOWLEDGE_BASE.items():
        all_names.append((data["name"].lower(), key))
        all_names.append((key.replace("_", " "), key))
    for alias, canonical in RAGA_ALIASES.items():
        all_names.append((alias.replace("_", " "), canonical))

    # Sort by length descending so longer names match first
    all_names.sort(key=lambda x: len(x[0]), reverse=True)

    for name, key in all_names:
        if name in query_lower:
            return key

    return ""


def get_all_raga_names() -> list:
    """
    Return a list of all supported raga display names.

    Returns:
        A list of raga display names (e.g. ['Kalyani', 'Bhairavi', ...]).
    """
    return [data["name"] for data in RAGA_KNOWLEDGE_BASE.values()]


# ──────────────────────────────────────────────────────────────
# Quick self-test
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Total ragas in knowledge base: {len(RAGA_KNOWLEDGE_BASE)}")
    print(f"Supported raga keys: {SUPPORTED_RAGA_NAMES}")
    print()

    # Test get_raga_info
    for test_name in ["Kalyani", "shankarabharanam", "Todi", "yaman", "malkouns", "Bhoop"]:
        info = get_raga_info(test_name)
        if info:
            print(f"  get_raga_info('{test_name}') -> {info['name']} (Melakarta {info['melakarta_number']})")
        else:
            print(f"  get_raga_info('{test_name}') -> NOT FOUND")

    print()

    # Test find_raga_key
    for test_query in [
        "Play something in Kalyani raga",
        "I want to hear Bhairavi",
        "Sing a song in Darbari Kanada",
        "What is the arohana of Mohanam?",
    ]:
        key = find_raga_key(test_query)
        print(f"  find_raga_key('{test_query}') -> '{key}'")

    print()
    print(f"All raga display names: {get_all_raga_names()}")
