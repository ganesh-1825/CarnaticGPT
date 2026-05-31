"""
CarnaticGPT Theory Knowledge Base
Structured definitions for fundamental Carnatic music concepts.
Injected during retrieval when a theory query matches a known concept.
"""

THEORY_KNOWLEDGE_BASE = {
    "shruti": {
        "term": "Shruti",
        "definition": "Shruti is the smallest perceptible pitch interval in Indian classical music. It serves as the fundamental tonal reference and microtonal unit from which all swaras (musical notes) are derived. In Carnatic music theory, there are 22 Shrutis within one octave (Saptak). These 22 microtonal intervals divide the octave and form the basis for constructing the 12 swarasthanas (semitonal positions). Shruti also refers to the drone pitch or tonic reference (Adhara Shadja) to which all performers tune their instruments. The concept originates from ancient texts like the Natya Shastra by Bharata Muni.",
        "category": "Fundamental Concept",
        "source": "Carnatic Music Theory"
    },
    "ragam": {
        "term": "Ragam (Raga)",
        "definition": "Ragam is the melodic framework in Indian classical music that defines a specific arrangement of swaras (musical notes) and characteristic phrases (prayogas) used to create musical expression. A Ragam prescribes the ascending scale (Arohana), descending scale (Avarohana), characteristic phrases (Sanchara), dominant note (Vadi), and emotional mood (Rasa). In the Carnatic Melakarta system, there are 72 parent Melakartas (Sampoorna ragas using all 7 notes) and hundreds of derivative Janya ragas. Each Ragam has a unique melodic personality defined by its note combinations, gamakas, and prayogas.",
        "category": "Fundamental Concept",
        "source": "Carnatic Music Theory"
    },
    "gamaka": {
        "term": "Gamaka",
        "definition": "Gamaka refers to the ornamental oscillations, embellishments, and grace notes applied to swaras in Carnatic music. Gamakas are essential to raga expression and distinguish Carnatic music from Western music. There are 15 types of Gamakas described in classical texts including: Kampita (oscillation between adjacent notes), Sphurita (a quick touch of a higher note), Pratyahata (rebounding effect), Ahata (sliding approach), Andolita (gentle swing), and Nokku (stress gamaka). Without gamakas, a raga loses its identity and emotional depth. They are the life-breath (Prana) of Carnatic music.",
        "category": "Ornamentation",
        "source": "Carnatic Music Theory"
    },
    "swara": {
        "term": "Swara",
        "definition": "Swara refers to a musical note or pitch in Indian classical music. The seven fundamental swaras are: Shadjam (Sa), Rishabham (Ri), Gandharam (Ga), Madhyamam (Ma), Panchamam (Pa), Dhaivatam (Da), and Nishadam (Ni). Together they form the Sapta Swaras. Sa and Pa are fixed (Achala swaras), while Ri, Ga, Ma, Da, and Ni each have multiple variants (Vikruti swaras), giving 16 swarasthanas in total. In the Melakarta system, specific combinations of these variants define the 72 parent ragas.",
        "category": "Fundamental Concept",
        "source": "Carnatic Music Theory"
    },
    "talam": {
        "term": "Talam (Tala)",
        "definition": "Talam is the rhythmic framework in Carnatic music that governs the time cycle of a musical composition. The Sapta Tala system defines seven primary talas: Dhruva, Matya, Rupaka, Jhampa, Triputa, Ata, and Eka. Each tala is built from combinations of three basic rhythmic units (angas): Laghu (variable beats), Drutam (2 beats), and Anudrutam (1 beat). The most common tala is Adi Tala (Chatusra Jati Triputa Tala) with 8 beats. With 5 jati variations (Tisra, Chatusra, Khanda, Misra, Sankirna), there are 35 possible talas in the system.",
        "category": "Rhythm",
        "source": "Carnatic Music Theory"
    },
    "jeeva swara": {
        "term": "Jeeva Swara",
        "definition": "Jeeva Swara (also called Jiva Swara or Life Note) is the most important and characteristic note of a raga that gives it its distinctive identity and life. It is the swara that, when emphasized or elaborated, immediately evokes the mood and character of the raga. For example, the Jeeva Swara of Kalyani is the Prati Madhyamam (M2), which gives Kalyani its bright, majestic quality. Every raga has one or more Jeeva Swaras. Related concepts include Vadi (sonant/dominant note) and Samvadi (consonant note).",
        "category": "Raga Theory",
        "source": "Carnatic Music Theory"
    },
    "melakarta": {
        "term": "Melakarta",
        "definition": "Melakarta is the systematic classification of parent ragas in Carnatic music. The Melakarta scheme organizes 72 fundamental Sampoorna (heptatonic) ragas that use all seven swaras in both ascending and descending scales. These 72 ragas are divided into two groups of 36: Suddha Madhyama (M1) ragas and Prati Madhyama (M2) ragas. Each Melakarta raga serves as a parent for numerous derivative Janya ragas. The numbering follows the Katapayadi system, where the first two syllables of the raga name encode its number.",
        "category": "Classification System",
        "source": "Carnatic Music Theory"
    },
    "kriti": {
        "term": "Kriti",
        "definition": "Kriti is the most important and elaborate compositional form in Carnatic music. A Kriti has three main sections: Pallavi (the opening theme), Anupallavi (the second section, often in a higher octave), and Charanam (the concluding section). Kritis are composed in specific ragas and talas and contain sahitya (lyrics) with deep devotional or philosophical content. The Trinity of Carnatic Music — Tyagaraja, Muthuswami Dikshitar, and Syama Sastri — elevated the Kriti form to its highest artistic expression.",
        "category": "Compositional Form",
        "source": "Carnatic Music Theory"
    },
    "alapana": {
        "term": "Alapana",
        "definition": "Alapana (also Ragam or Raga Alapana) is the elaborate, improvised exposition of a raga performed without rhythmic accompaniment (tala). It is the opening segment of a Carnatic music performance where the musician systematically unfolds the raga's melodic structure, exploring its characteristic phrases, mood, and nuances across different octaves. Alapana begins slowly in the lower octave (Mandra Sthayi), gradually ascends through the middle (Madhya) and upper (Tara) octaves, and returns. It demonstrates the performer's mastery of the raga's grammar and aesthetics.",
        "category": "Performance Form",
        "source": "Carnatic Music Theory"
    },
    "carnatic music": {
        "term": "Carnatic Music",
        "definition": "Carnatic Music (also Karnatik or Karnataka Sangeetam) is one of the two major traditions of Indian classical music, originating from South India. It is a melody-based system built on the dual pillars of Raga (melodic framework) and Tala (rhythmic framework). The tradition was shaped by the Musical Trinity: Saint Tyagaraja, Muthuswami Dikshitar, and Syama Sastri in the 18th-19th centuries. Key features include the 72 Melakarta raga classification system, extensive use of Gamakas (ornamentations), and structured compositional forms like Varnam, Kriti, and Tillana.",
        "category": "Overview",
        "source": "Carnatic Music Theory"
    },
    "computational musicology": {
        "term": "Computational Musicology",
        "definition": "Computational Musicology is an interdisciplinary field that applies computational methods, algorithms, and data analysis techniques to study, analyze, and understand music. In the context of Carnatic music, it involves using techniques like signal processing for raga recognition, machine learning for swara detection, NLP for lyric analysis, and statistical methods for melodic pattern discovery. Research areas include automatic raga identification from audio recordings, gamaka analysis through pitch contour extraction, tala cycle detection, and computational comparison of performances across artists and traditions.",
        "category": "Research Field",
        "source": "Computational Musicology Research"
    }
}

THEORY_TERMS = list(THEORY_KNOWLEDGE_BASE.keys())


def find_theory_key(query: str) -> str:
    """Find a matching theory concept from a query string."""
    q = query.lower()
    # Check for multi-word matches first (longer matches take priority)
    sorted_terms = sorted(THEORY_TERMS, key=len, reverse=True)
    for term in sorted_terms:
        if term in q:
            return term
    return None


def get_theory_info(key: str) -> dict:
    """Get theory definition by key."""
    return THEORY_KNOWLEDGE_BASE.get(key, None)


def build_theory_chunk(key: str) -> dict:
    """Build a high-quality retrieval chunk from the theory knowledge base."""
    info = get_theory_info(key)
    if not info:
        return None
    
    text = (
        f"{info['term']}: {info['definition']}"
    )
    
    return {
        "chunk_id": f"kb_theory_{key}",
        "text": text,
        "source": f"Theory/{info['source']}",
        "book_name": info["source"],
        "page": 1,
        "score": 0.94
    }
