"""
CarnaticGPT Composer Knowledge Base
Structured musicological data for prominent Carnatic composers.
"""

COMPOSER_KNOWLEDGE_BASE = {
    "tyagaraja": {
        "name": "Tyagaraja",
        "period": "1767-1847",
        "language": "Telugu, Sanskrit",
        "style": "Bhakti-oriented, expressive, simple yet profound melodies (sangatis).",
        "deity_focus": "Lord Rama",
        "famous_works": "Pancharatna Kritis, Utsava Sampradaya Kritis, Prahlada Bhakti Vijayam",
        "influence": "Popularised the Kriti format with sangatis (melodic variations). Deeply influenced modern concert structure.",
        "famous_ragas": "Kharaharapriya, Harikambhoji, Todi, Kalyani"
    },
    "dikshitar": {
        "name": "Muthuswami Dikshitar",
        "period": "1775-1835",
        "language": "Sanskrit, Manipravalam",
        "style": "Scholarly, slow tempo (chauka kala), intricate gamakas, structural grandeur, inclusion of raga mudras.",
        "deity_focus": "Multiple Deities (Kamalamba, Navagrahas, Shiva, Devi)",
        "famous_works": "Navagraha Kritis, Kamalamba Navavarana Kritis, Nottuswaras",
        "influence": "Brought Hindustani ragas to Carnatic music. Master of scholarly, slow-paced compositions.",
        "famous_ragas": "Bhairavi, Anandabhairavi, Sri, Yamunakalyani"
    },
    "sastri": {
        "name": "Syama Sastri",
        "period": "1762-1827",
        "language": "Telugu, Sanskrit, Tamil",
        "style": "Rhythmic complexity (tala mastery), deeply emotional, use of rare ragas and viloma chapu tala.",
        "deity_focus": "Goddess Kamakshi, Devi",
        "famous_works": "Swarajatis (Bhairavi, Todi, Yadukulakambhoji), Navaratnamalika",
        "influence": "Known for his unmatched mastery over complex talas like Misra Chapu. Architect of the modern Swarajati.",
        "famous_ragas": "Anandabhairavi, Bhairavi, Yadukulakambhoji, Todi"
    },
    "purandaradasa": {
        "name": "Purandaradasa",
        "period": "1484-1564",
        "language": "Kannada, Sanskrit",
        "style": "Foundational Carnatic teaching exercises (Sarali, Jantai), devotional padas, accessible philosophy.",
        "deity_focus": "Lord Krishna (Purandara Vittala)",
        "famous_works": "Pillari Gitas, Devarnamas, Navaratna Malike",
        "influence": "Known as the Pitamaha (Grandfather) of Carnatic music. Structured the basic lessons (Sarali, Jantai) in Mayamalavagowla.",
        "famous_ragas": "Mayamalavagowla, Malahari, Mohanam"
    },
    "swathi_thirunal": {
        "name": "Swathi Thirunal",
        "period": "1813-1846",
        "language": "Sanskrit, Malayalam, Hindi, Telugu, Kannada",
        "style": "Royal patronage, mastery of diverse musical forms (Kriti, Padam, Varnam, Tillana, Dhrupad).",
        "deity_focus": "Lord Padmanabha",
        "famous_works": "Navaratri Kritis, Navavidha Bhakti Kritis, Utsava Prabandhas",
        "influence": "Royal patron who composed in diverse languages and forms, including Hindustani Dhrupad and Khayal.",
        "famous_ragas": "Bhairavi, Kalyani, Shankarabharanam"
    },
    "annamayya": {
        "name": "Annamacharya",
        "period": "1408-1503",
        "language": "Telugu, Sanskrit",
        "style": "Pioneer of the Sankirtana format (Pallavi + Charanas), profound devotion, social themes.",
        "deity_focus": "Lord Venkateshwara",
        "famous_works": "Sringara Sankirtanas, Adhyatma Sankirtanas (e.g., Brahmam Okate)",
        "influence": "First known composer of the Sankirtana format. Immense cultural impact on Telugu literature and devotion.",
        "famous_ragas": "Bouli, Mukhari, Ahiri"
    }
}

def get_composer_info(name: str) -> dict | None:
    name_clean = name.lower().strip()
    
    # Check aliases
    if "syama" in name_clean or "shyama" in name_clean:
        return COMPOSER_KNOWLEDGE_BASE["sastri"]
    if "thyagaraja" in name_clean:
        return COMPOSER_KNOWLEDGE_BASE["tyagaraja"]
    if "muthuswami" in name_clean:
        return COMPOSER_KNOWLEDGE_BASE["dikshitar"]
    if "swathi" in name_clean or "thirunal" in name_clean:
        return COMPOSER_KNOWLEDGE_BASE["swathi_thirunal"]
        
    for k, v in COMPOSER_KNOWLEDGE_BASE.items():
        if k in name_clean or name_clean in k or v["name"].lower() in name_clean:
            return v
    return None
