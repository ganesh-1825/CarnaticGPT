"""
generate_dataset.py
-------------------
Reads all extracted text files and CarnaticSongsDatabase.csv,
generates 2000-5000 high-quality Carnatic Q/A training pairs,
deduplicates them, and saves to data/training_data/carnatic_qa.json.

Usage:
    python -m training.generate_dataset
    python -m training.generate_dataset --max 5000
"""

import os
import re
import csv
import json
import random
import hashlib
import argparse
import logging
from pathlib import Path
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR        = Path(os.getenv("BASE_DIR", "."))
EXTRACTED_DIR   = BASE_DIR / "data" / "extracted_text"
CSV_PATH        = BASE_DIR / "data" / "music_dataset" / "CarnaticSongsDatabase.csv"
OUTPUT_DIR      = BASE_DIR / "data" / "training_data"
OUTPUT_FILE     = OUTPUT_DIR / "carnatic_qa.json"

TARGET_MIN  = 2000
TARGET_MAX  = 5000

# ---------------------------------------------------------------------------
# Carnatic domain knowledge for template generation
# ---------------------------------------------------------------------------

RAGAS = [
    "Kalyani", "Bhairavi", "Hindolam", "Kharaharapriya", "Mohanam",
    "Shankarabharanam", "Todi", "Hamsadhwani", "Revati", "Madhyamavati",
    "Bilahari", "Natabhairavi", "Charukesi", "Saveri", "Suddhasaveri",
    "Kambhoji", "Begada", "Kedaram", "Anandabhairavi", "Ritigowla",
    "Sriranjani", "Vasanta", "Sahana", "Mukhari", "Nattai",
    "Varali", "Punnagavarali", "Nilambari", "Devagandhari", "Nalinakanti",
    "Jayantasri", "Abhogi", "Amritavarshini", "Simhendramadhyama",
    "Hemavati", "Dharmavati", "Gamanasrama", "Lathangi", "Rasikapriya",
    "Pantuvarali", "Arabhi", "Harikambhoji", "Suddhadhanyasi",
    "Gourimanohari", "Kiravani", "Bowli", "Kokilapriya", "Nayaki",
    "Poorvikalyani", "Kaanada", "Durbari Kaanada", "Sindhu Bhairavi",
]

COMPOSERS = [
    "Tyagaraja", "Muthuswami Dikshitar", "Syama Sastri",
    "Purandaradasa", "Annamacharya", "Bhadrachala Ramadasa",
    "Papanasam Sivan", "G.N. Balasubramanian", "Swati Tirunal",
    "Mysore Vasudevachar", "Oothukkadu Venkata Kavi",
    "Thyagaraja Bhagavathar", "Gopalakrishna Bharati",
    "Arunachala Kavi", "Marimuthu Pillai", "Patnam Subramania Iyer",
]

TALAS = [
    "Adi Tala", "Rupaka Tala", "Misra Chapu", "Khanda Chapu",
    "Tisra Triputa", "Chatusra Nadai", "Khanda Nadai",
    "Misra Nadai", "Sankirna Nadai", "Vilamba Kala", "Madhyama Kala",
]

CONCEPTS = [
    ("Shruti", "the microtonal intervals and pitch relationships in Carnatic music"),
    ("Swara", "the seven musical notes: Sa Ri Ga Ma Pa Da Ni"),
    ("Gamaka", "ornamental techniques applied to notes in Carnatic music"),
    ("Melapakarta", "the 72-raga parent scale classification system"),
    ("Janya Raga", "a derived raga that originates from a parent melapakarta"),
    ("Arohana", "the ascending scale of a raga"),
    ("Avarohana", "the descending scale of a raga"),
    ("Vadi Swara", "the king note or most important note of a raga"),
    ("Samvadi Swara", "the second most important note in a raga"),
    ("Vivadi Swara", "a note that creates dissonance in a raga"),
    ("Alapana", "the free-flowing, improvised exposition of a raga"),
    ("Niraval", "melodic improvisation on a single line of a composition"),
    ("Kalpana Swaras", "improvised solfege passages in a raga"),
    ("Tani Avartanam", "a solo percussion interlude in a Carnatic concert"),
    ("Manodharma Sangeetam", "the improvisational aspect of Carnatic music"),
    ("Pallavi", "the first section and refrain of a Carnatic composition"),
    ("Anupallavi", "the second section that complements the pallavi"),
    ("Charanam", "the verse section containing the main lyrics"),
    ("Sangati", "melodic variations on a phrase within a composition"),
    ("Kriti", "the primary compositional form in Carnatic music"),
    ("Varnam", "a form that encapsulates all technical aspects of a raga"),
    ("Geetam", "simple Carnatic compositions used for early learning"),
    ("Swarajati", "a compositional form combining swara and sahitya"),
    ("Thillana", "a rhythmic and dynamic form often used to conclude concerts"),
    ("Padam", "lyrical compositions often dealing with devotional or romantic themes"),
    ("Javali", "light classical compositions in a romantic style"),
    ("Ragam Tanam Pallavi", "the grand concert form combining raga, tanam, and pallavi"),
    ("Tanam", "a rhythmic pattern performed between alapana and pallavi"),
    ("Nadai", "the rhythmic subdivision within a tala cycle"),
    ("Gati", "rhythmic patterns or speeds within a tala"),
    ("Laghu", "a beat unit in tala consisting of one clap and finger counts"),
    ("Drutam", "a tala unit consisting of one clap and one wave"),
    ("Anudrutam", "the smallest tala unit consisting of a single beat"),
    ("Carnatic Music", "the classical music tradition of South India"),
    ("Raga", "a melodic framework with specific ascending and descending patterns"),
    ("Tala", "the rhythmic cycle forming the time measure in Carnatic music"),
    ("Sahitya", "the lyrics or text of a Carnatic musical composition"),
    ("Mela", "a parent scale in the 72 Melapakarta system"),
    ("Graha Swara", "the note on which a composition begins"),
    ("Nyasa Swara", "the note on which a phrase comes to rest"),
    ("Amsa Swara", "the predominant note of a raga phrase"),
]

DEVOTIONAL_RAGAS = [
    "Bhairavi", "Revati", "Madhyamavati", "Nilambari", "Sindhu Bhairavi",
    "Todi", "Anandabhairavi", "Kedaram", "Begada",
]

AUDIO_TYPES = ["alapana", "arohana", "avarohana", "composition", "sample"]

# ---------------------------------------------------------------------------
# Text cleaning (reused from chunk_text logic but standalone)
# ---------------------------------------------------------------------------

OCR_GARBAGE_RE = re.compile(
    r"(?:[^\x00-\x7F]){5,}"
    r"|[|]{2,}"
    r"|[_]{4,}"
    r"|[.]{5,}"
    r"|\bscanned\s+(?:page|image|document)\b"
    r"|(?:digitized|digitised)\s+by"
    r"|(?:indecipherable|illegible|unclear)\s+(?:text|portion)",
    re.I,
)


def clean_text(text: str) -> str:
    text = re.sub(r"\r\n|\r", "\n", text)
    text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)  # page numbers
    lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        if len(stripped) < 12 and not re.search(r"[a-z]{3,}", stripped, re.I):
            continue
        if OCR_GARBAGE_RE.search(stripped):
            continue
        non_ascii = sum(1 for c in stripped if ord(c) > 127)
        if stripped and non_ascii / len(stripped) > 0.35:
            continue
        lines.append(stripped)
    text = " ".join(lines)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def is_good_sentence(s: str) -> bool:
    s = s.strip()
    if len(s) < 40:
        return False
    if not re.search(r"[a-zA-Z]{4,}", s):
        return False
    alpha = sum(1 for c in s if c.isalpha())
    if len(s) > 0 and alpha / len(s) < 0.45:
        return False
    return True


def split_sentences(text: str) -> list[str]:
    raw = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in raw if is_good_sentence(s)]


# ---------------------------------------------------------------------------
# Content hash for deduplication
# ---------------------------------------------------------------------------

def _hash(text: str) -> str:
    normalised = re.sub(r"\s+", " ", text.strip().lower())
    return hashlib.sha256(normalised.encode()).hexdigest()[:20]


# ---------------------------------------------------------------------------
# Q/A pair builder
# ---------------------------------------------------------------------------

def make_pair(instruction: str, output: str) -> dict:
    return {
        "instruction": instruction.strip(),
        "input": "",
        "output": output.strip(),
    }


# ---------------------------------------------------------------------------
# Generator 1: Definition / Concept questions from extracted text
# ---------------------------------------------------------------------------

DEFINITION_QUESTION_TEMPLATES = [
    "What is {term}?",
    "Define {term} in the context of Carnatic music.",
    "Explain the concept of {term}.",
    "Describe what {term} means in Carnatic classical music.",
    "What does {term} refer to in Carnatic music theory?",
    "Give a detailed explanation of {term}.",
    "How is {term} used in Carnatic music?",
    "What role does {term} play in Carnatic music?",
    "Why is {term} important in Carnatic music?",
    "Can you explain {term} to a student learning Carnatic music?",
]


def generate_concept_pairs() -> list[dict]:
    pairs = []
    for concept, description in CONCEPTS:
        templates = random.sample(DEFINITION_QUESTION_TEMPLATES, min(4, len(DEFINITION_QUESTION_TEMPLATES)))
        for tmpl in templates:
            q = tmpl.format(term=concept)
            a = (
                f"{concept} is {description}. "
                f"In Carnatic classical music, {concept.lower()} plays a fundamental role in defining "
                f"the structure and aesthetic of musical performance and composition. "
                f"Students of Carnatic music study {concept.lower()} as part of their foundational training."
            )
            pairs.append(make_pair(q, a))
    return pairs


# ---------------------------------------------------------------------------
# Generator 2: Raga questions
# ---------------------------------------------------------------------------

RAGA_QUESTION_TEMPLATES = [
    "What is the raga {raga}?",
    "Explain the raga {raga}.",
    "Describe the characteristics of raga {raga}.",
    "What are the arohana and avarohana of raga {raga}?",
    "What is the mood (bhava) of raga {raga}?",
    "Which melapakarta does raga {raga} belong to?",
    "Is raga {raga} a janya or melapakarta raga?",
    "What are the important swaras in raga {raga}?",
    "What time of day is raga {raga} traditionally performed?",
    "List some famous compositions in raga {raga}.",
    "How does raga {raga} differ from other ragas?",
    "What gamaka techniques are associated with raga {raga}?",
]

COMPARE_TEMPLATES = [
    "Compare raga {r1} and raga {r2}.",
    "What is the difference between {r1} and {r2}?",
    "How do {r1} and {r2} differ in their swaras and mood?",
    "Explain the similarities and differences between {r1} and {r2}.",
    "Which is more commonly performed, {r1} or {r2}?",
]

RAGA_ANSWERS = {
    "Kalyani":          "a Sampurna raga (melapakarta 65) with all seven notes in both arohana and avarohana. It uses Prati Madhyama (M2) and all other natural swaras. It has a bright, majestic mood and is often performed in the evening.",
    "Bhairavi":         "a popular janya raga of immense emotional depth. It uses all seven swaras with komal (flat) Ri, Ga, Da, and Ni. It evokes pathos, longing, and devotion, and is often used to conclude concerts.",
    "Hindolam":         "an audava raga (pentatonic) using Sa, Ga2, Ma1, Da2, Ni2 with no Ri or Pa. It evokes a peaceful, introspective mood and is a janya of the 20th melapakarta Natabhairavi.",
    "Kharaharapriya":   "the 22nd melapakarta raga with sampurna arohana and avarohana. It uses Chatusruti Rishabha, Sadharana Gandhara, and Suddha Madhyama. It is considered the foundation of Hindustani Kafi thaat.",
    "Mohanam":          "a pentatonic janya raga using Sa, Ri2, Ga3, Pa, Da2. It has no Ma or Ni. It evokes joy and brightness and is related to the Hindustani raga Bhupali.",
    "Shankarabharanam": "the 29th melapakarta raga equivalent to the Western major scale. All seven swaras are in their natural (suddha) position. It has a grand, auspicious character.",
    "Hamsadhwani":      "an audava janya raga using Sa, Ri2, Ga3, Pa, Ni3. Known for its auspicious, bright character, it is among the most popular ragas for beginners and concert openers.",
    "Revati":           "a janya raga of the 8th melapakarta using Sa, Ri1, Ma1, Pa, Ni1. It has a devotional and serene character and is associated with prayers and early morning performances.",
    "Todi":             "the 8th melapakarta raga with komal Ri, Ga, and Da, and Prati Madhyama. It is a complex, emotive raga evoking deep pathos and is considered one of the most difficult ragas to render.",
    "Abhogi":           "a janya raga using Sa, Ri2, Ga2, Ma1, Da2, omitting Pa and Ni. It has a pleasing and melodious character suitable for light concert pieces.",
    "Nilambari":        "a janya raga associated with lullabies and devotion. It is used in the famous lullaby 'Nilaambari' sung to put Lord Rama to sleep. Its swaras are Sa, Ri2, Ga2, Ma1, Pa, Da2, Ni2.",
    "Bilahari":         "a janya raga of the 29th melapakarta using a vakra (zigzag) avarohana. It has a bright and joyful character and is commonly used in auspicious contexts.",
    "Anandabhairavi":   "a janya raga evoking joy and sometimes pathos. It uses Sa, Ri2, Ga2, Ma1, Pa, Da1, Ni2 with characteristic gamakas. It is one of the favorite ragas for padams and javalis.",
    "Sriranjani":       "a janya raga using Sa, Ri2, Ga2, Ma1, Da2, Ni2, omitting Pa. It has a romantic and pleasing character and is widely used in light classical and film music.",
    "Madhyamavati":     "a janya raga using Sa, Ri2, Ma1, Pa, Ni2, omitting Ga and Da. It has a devotional and serene mood and is often used in mangalam compositions to conclude concerts.",
}


def generate_raga_pairs() -> list[dict]:
    pairs = []

    for raga in RAGAS:
        templates = random.sample(RAGA_QUESTION_TEMPLATES, min(5, len(RAGA_QUESTION_TEMPLATES)))
        base_answer = RAGA_ANSWERS.get(raga, (
            f"an important raga in Carnatic classical music. It has a distinct set of swaras "
            f"(ascending and descending scales) and a characteristic mood (bhava). "
            f"Famous Carnatic composers have composed numerous kritis in this raga, and it is widely "
            f"performed in concerts across South India."
        ))
        for tmpl in templates:
            q = tmpl.format(raga=raga)
            a = f"Raga {raga} is {base_answer}"
            pairs.append(make_pair(q, a))

    # Comparison pairs
    raga_sample = random.sample(RAGAS, min(20, len(RAGAS)))
    for i in range(0, len(raga_sample) - 1, 2):
        r1, r2 = raga_sample[i], raga_sample[i + 1]
        tmpl = random.choice(COMPARE_TEMPLATES)
        q = tmpl.format(r1=r1, r2=r2)
        a = (
            f"Raga {r1} and raga {r2} are both important ragas in Carnatic music but differ significantly. "
            f"{r1} is {RAGA_ANSWERS.get(r1, 'a distinct raga with its own set of swaras and mood')}. "
            f"{r2} is {RAGA_ANSWERS.get(r2, 'another distinct raga with a different set of swaras and emotional character')}. "
            f"The main differences lie in their swara compositions, gamakas, and the emotions they evoke."
        )
        pairs.append(make_pair(q, a))

    return pairs


# ---------------------------------------------------------------------------
# Generator 3: Composer questions
# ---------------------------------------------------------------------------

COMPOSER_TEMPLATES = [
    "Who is {composer}?",
    "Tell me about the composer {composer}.",
    "What are the contributions of {composer} to Carnatic music?",
    "Which compositions is {composer} known for?",
    "What ragas did {composer} frequently compose in?",
    "Describe the musical style of {composer}.",
    "What is the significance of {composer} in Carnatic music history?",
    "How many compositions did {composer} write?",
    "What language did {composer} use in their compositions?",
    "What era did {composer} belong to?",
]

COMPOSER_INFO = {
    "Tyagaraja": (
        "one of the Trinity of Carnatic music (along with Muthuswami Dikshitar and Syama Sastri), "
        "born in 1767 in Tiruvarur. He composed over 700 kritis, mostly in Telugu and Sanskrit, "
        "in praise of Lord Rama. His compositions span hundreds of ragas. Famous works include "
        "'Endaro Mahanubhavulu' in Sriragam, 'Nagumomu' in Abheri, and 'Samaja Vara Gamana' in Hindolam."
    ),
    "Muthuswami Dikshitar": (
        "one of the Trinity of Carnatic music, born in 1775 in Tiruvarur. He composed around 500 kritis, "
        "mostly in Sanskrit, and is known for composing in all 72 melapakarta ragas (the Asampurna Mela series). "
        "His compositions follow the Madhyamakala system. Famous works include 'Vatapi Ganapathim' in Hamsadhwani "
        "and the Navagraha kritis."
    ),
    "Syama Sastri": (
        "the eldest of the Trinity of Carnatic music, born in 1762. He composed around 300 pieces, primarily "
        "in Telugu and Sanskrit, mostly in praise of Goddess Kamakshi. He is known for his mastery of tala "
        "and for introducing Swarajatis as a compositional form. Famous works include 'Devi Brova Samayamide'."
    ),
    "Purandaradasa": (
        "the Father of Carnatic Music, born in 1484. He standardised the curriculum of Carnatic music "
        "education, introducing Sarali Varasai, Janta Varasai, Alankara, Geetam, Swarajati, and Varnam. "
        "He composed over 475,000 compositions in Kannada and Sanskrit in praise of Lord Vishnu."
    ),
    "Annamacharya": (
        "a 15th-century Telugu saint-poet and composer from Andhra Pradesh who composed 32,000 kirtanas "
        "called Sankirtanas in praise of Lord Venkateswara of Tirupati. He is regarded as the Pada Kavita "
        "Pitamaha of Telugu literature."
    ),
    "Swati Tirunal": (
        "the Maharaja of Travancore (1813-1846) who was a prolific composer in multiple languages including "
        "Malayalam, Sanskrit, Telugu, Hindi, and Manipravalam. He composed around 400 kritis and is known for "
        "blending Carnatic and Hindustani styles. Famous works include 'Bhavayami Raghuramam'."
    ),
    "Papanasam Sivan": (
        "a 20th-century Tamil composer known as the 'Thyagaraja of Tamil' who composed over 500 songs in Tamil "
        "and Sanskrit. He was a devoted disciple of Tyagaraja's musical tradition and composed extensively in "
        "Bhakti style. Famous works include 'Raghuvaranthaka' and 'Kanchi Kamatchi'."
    ),
}


def generate_composer_pairs() -> list[dict]:
    pairs = []
    for composer in COMPOSERS:
        info = COMPOSER_INFO.get(composer, (
            f"a significant composer in Carnatic music history who contributed important compositions "
            f"to the repertoire. Their kritis are performed in concerts across South India."
        ))
        templates = random.sample(COMPOSER_TEMPLATES, min(5, len(COMPOSER_TEMPLATES)))
        for tmpl in templates:
            q = tmpl.format(composer=composer)
            a = f"{composer} is {info}"
            pairs.append(make_pair(q, a))
    return pairs


# ---------------------------------------------------------------------------
# Generator 4: Music dataset questions (from CSV)
# ---------------------------------------------------------------------------

CSV_QUESTION_TEMPLATES = [
    "List songs in raga {raga}.",
    "Which songs are composed in {raga}?",
    "Show compositions in {raga}.",
    "What are famous kritis in raga {raga}?",
    "List songs by composer {composer}.",
    "What compositions did {composer} write?",
    "Show kritis by {composer}.",
    "Which songs by {composer} are in the database?",
    "List all songs with tala {tala}.",
    "What kritis use {tala}?",
    "Show Telugu compositions in raga {raga}.",
    "What are some popular Carnatic songs?",
]


def generate_csv_pairs(csv_path: Path) -> list[dict]:
    if not csv_path.exists():
        logger.warning("CSV not found: %s", csv_path)
        return []

    pairs = []
    raga_songs: dict[str, list[str]] = {}
    composer_songs: dict[str, list[str]] = {}
    tala_songs: dict[str, list[str]] = {}

    try:
        with open(csv_path, newline="", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Normalise keys
                norm = {k.strip().lower(): v.strip() for k, v in row.items() if v.strip()}
                song = norm.get("song name") or norm.get("song") or norm.get("title") or norm.get("name") or ""
                raga = norm.get("ragam") or norm.get("raga") or ""
                composer = norm.get("composer") or norm.get("artist") or ""
                tala = norm.get("tala") or norm.get("thala") or ""
                if not song:
                    continue

                song_take = norm.get("song take") or ""
                youtube_link = norm.get("youtube link") or ""

                # Generate unique dynamic QA pairs per individual song composition
                song_clean = song.replace('-', ' ')
                raga_clean = raga.replace('-', ' ') if raga else ""
                composer_clean = composer.replace('-', ' ') if composer else ""
                tala_clean = tala.replace('-', ' ') if tala else ""
                
                if raga_clean and composer_clean:
                    take_str = f" (take {song_take})" if song_take else ""
                    yt_str = f" A classical recording is available to listen on YouTube here: {youtube_link}" if youtube_link else ""
                    
                    pairs.append(make_pair(
                        f"Who composed the song {song_clean}{take_str}?",
                        f"The composition '{song_clean}' in raga {raga_clean} was composed by the legendary Carnatic composer {composer_clean}.{yt_str}"
                    ))
                    pairs.append(make_pair(
                        f"What raga does the song {song_clean}{take_str} belong to?",
                        f"The composition '{song_clean}' is set to the beautiful raga {raga_clean}.{yt_str}"
                    ))
                    pairs.append(make_pair(
                        f"List a famous composition in raga {raga_clean}{take_str}.",
                        f"A highly regarded composition in raga {raga_clean} is '{song_clean}', composed by {composer_clean}.{yt_str}"
                    ))
                    if youtube_link:
                        pairs.append(make_pair(
                            f"Where can I listen to the song {song_clean} in raga {raga_clean}{take_str}?",
                            f"You can listen to '{song_clean}' composed by {composer_clean} in raga {raga_clean} on YouTube here: {youtube_link}"
                        ))
                if tala_clean:
                    pairs.append(make_pair(
                        f"What tala is the composition {song_clean} set to?",
                        f"The composition '{song_clean}' is set to the tala {tala_clean}."
                    ))

                if raga:
                    raga_songs.setdefault(raga, []).append(song)
                if composer:
                    composer_songs.setdefault(composer, []).append(song)
                if tala:
                    tala_songs.setdefault(tala, []).append(song)
    except Exception as e:
        logger.error("CSV read error: %s", e)
        return []

    # Raga-based questions
    for raga, songs in list(raga_songs.items())[:60]:
        sample = songs[:8]
        q = random.choice([
            f"List songs in raga {raga}.",
            f"Which compositions are in raga {raga}?",
            f"Show me kritis in raga {raga}.",
        ])
        a = (
            f"The following songs in raga {raga} are in the database: "
            f"{', '.join(sample)}"
            + (f", and {len(songs) - len(sample)} more." if len(songs) > len(sample) else ".")
        )
        pairs.append(make_pair(q, a))

        # Follow-up about the raga itself
        q2 = f"Is {raga} a popular raga for Carnatic compositions?"
        a2 = f"Yes, raga {raga} has {len(songs)} compositions in the database, making it {'very popular' if len(songs) > 20 else 'a moderately used raga'} among Carnatic composers."
        pairs.append(make_pair(q2, a2))

    # Composer-based questions
    for composer, songs in list(composer_songs.items())[:40]:
        sample = songs[:8]
        q = random.choice([
            f"List songs by {composer}.",
            f"What compositions did {composer} write?",
            f"Show kritis by {composer}.",
        ])
        a = (
            f"{composer} has the following compositions in the database: "
            f"{', '.join(sample)}"
            + (f", and {len(songs) - len(sample)} more." if len(songs) > len(sample) else ".")
        )
        pairs.append(make_pair(q, a))

    # Tala-based questions
    for tala, songs in list(tala_songs.items())[:20]:
        sample = songs[:6]
        q = f"List songs in {tala}."
        a = f"Songs in {tala}: {', '.join(sample)}" + (f", and others." if len(songs) > len(sample) else ".")
        pairs.append(make_pair(q, a))

    # General questions
    all_songs = [s for songs in raga_songs.values() for s in songs]
    if all_songs:
        popular = random.sample(all_songs, min(10, len(all_songs)))
        pairs.append(make_pair(
            "What are some popular Carnatic songs?",
            f"Some popular Carnatic songs include: {', '.join(popular)}. "
            f"These span various ragas and composers from the rich Carnatic tradition."
        ))

    return pairs


# ---------------------------------------------------------------------------
# Generator 5: Extracted text → Q/A pairs
# ---------------------------------------------------------------------------

TEXT_QUESTION_TEMPLATES = [
    "What does the text say about {topic}?",
    "Explain {topic} based on Carnatic music books.",
    "What is mentioned about {topic} in Carnatic literature?",
    "Describe {topic} as explained in Carnatic music texts.",
    "What information is available about {topic}?",
    "According to Carnatic music books, what is {topic}?",
    "How is {topic} described in classical Carnatic music theory?",
]

CARNATIC_TOPICS = [
    "raga", "tala", "swara", "gamaka", "alapana", "composition",
    "Carnatic music", "classical music", "music theory", "notation",
    "performance", "concert", "kriti", "varnam", "pallavi",
]


def _extract_passages(text: str, min_len: int = 120, max_len: int = 600) -> list[str]:
    """Split cleaned text into usable passage chunks."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    passages = []
    current = []
    current_len = 0
    for sent in sentences:
        sent = sent.strip()
        if not sent or not is_good_sentence(sent):
            continue
        if current_len + len(sent) > max_len and current:
            passage = " ".join(current)
            if len(passage) >= min_len:
                passages.append(passage)
            current = [sent]
            current_len = len(sent)
        else:
            current.append(sent)
            current_len += len(sent)
    if current:
        passage = " ".join(current)
        if len(passage) >= min_len:
            passages.append(passage)
    return passages


def _find_topic_in_passage(passage: str) -> Optional[str]:
    """Detect the best topic keyword in a passage for question generation."""
    lower = passage.lower()
    # Check Carnatic-specific terms first
    for concept, _ in CONCEPTS:
        if concept.lower() in lower:
            return concept
    for raga in RAGAS:
        if raga.lower() in lower:
            return f"raga {raga}"
    for composer in COMPOSERS:
        if composer.lower() in lower:
            return composer
    for topic in CARNATIC_TOPICS:
        if topic in lower:
            return topic
    return None


def generate_text_pairs(extracted_dir: Path, max_per_file: int = 80) -> list[dict]:
    if not extracted_dir.exists():
        logger.warning("Extracted text dir not found: %s", extracted_dir)
        return []

    pairs = []
    txt_files = list(extracted_dir.rglob("*.txt"))
    logger.info("Found %d extracted text files.", len(txt_files))

    for txt_file in txt_files:
        try:
            raw = txt_file.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            logger.warning("Cannot read %s: %s", txt_file, e)
            continue

        text = clean_text(raw)
        if len(text) < 200:
            continue

        passages = _extract_passages(text)
        file_pairs = []

        for passage in passages:
            topic = _find_topic_in_passage(passage)
            if not topic:
                continue

            tmpl = random.choice(TEXT_QUESTION_TEMPLATES)
            q = tmpl.format(topic=topic)
            a = passage

            file_pairs.append(make_pair(q, a))
            if len(file_pairs) >= max_per_file:
                break

        pairs.extend(file_pairs)
        logger.info("  %s → %d Q/A pairs", txt_file.name, len(file_pairs))

    return pairs


# ---------------------------------------------------------------------------
# Generator 6: Metadata / system questions
# ---------------------------------------------------------------------------

def generate_metadata_pairs() -> list[dict]:
    pairs = [
        make_pair(
            "What types of Carnatic music information are available?",
            "CarnaticGPT has knowledge about ragas, talas, compositions, composers, music theory concepts, "
            "performance techniques, and audio recordings. It covers topics from basic definitions like Shruti and "
            "Swara to advanced concepts like Manodharma Sangeetam and Ragam Tanam Pallavi."
        ),
        make_pair(
            "What is CarnaticGPT?",
            "CarnaticGPT is an AI assistant specialising in Carnatic classical music. It can answer questions "
            "about ragas, talas, composers, compositions, music theory, and performance practice based on "
            "uploaded books and research papers."
        ),
        make_pair(
            "What ragas are available in the CarnaticGPT database?",
            f"CarnaticGPT has information on many ragas including: {', '.join(random.sample(RAGAS, 20))}, "
            f"and many more from the 72 Melapakarta system and janya ragas."
        ),
        make_pair(
            "Which composers does CarnaticGPT know about?",
            f"CarnaticGPT has information about composers including: {', '.join(COMPOSERS[:10])}, "
            f"and others from the Carnatic music tradition."
        ),
        make_pair(
            "What is the 72 Melapakarta system?",
            "The 72 Melapakarta system is a classification of Carnatic ragas into 72 parent (melapakarta) scales. "
            "Each melapakarta contains all seven swaras in a specific combination of variants. "
            "The system was formalised by Venkatamakhi in his 17th century treatise Chaturdandi Prakasika. "
            "From these 72 parent ragas, thousands of janya (derived) ragas are formed."
        ),
        make_pair(
            "What is the Trinity of Carnatic music?",
            "The Trinity of Carnatic music refers to three great composers who are considered the pillars of "
            "Carnatic classical music: Tyagaraja (1767-1847), Muthuswami Dikshitar (1775-1835), and "
            "Syama Sastri (1762-1827). All three were contemporaries born in Tiruvarur, Tamil Nadu, and "
            "their compositions form the backbone of the modern Carnatic concert repertoire."
        ),
        make_pair(
            "What is raga metadata in Carnatic music?",
            "Raga metadata includes: the raga name, its parent melapakarta number, arohana (ascending scale), "
            "avarohana (descending scale), important swaras (vadi and samvadi), characteristic gamakas, "
            "the appropriate time for performance, the emotional mood (bhava/rasa), and notable compositions."
        ),
        make_pair(
            "What is Shruti metadata?",
            "Shruti in Carnatic music refers to the 22 microtonal intervals within an octave. "
            "Shruti metadata includes the pitch frequency ratios, the position within the scale, "
            "and how each shruti relates to the saptha swaras. The 22 shrutis are: "
            "4 for Ri, 3 for Ga, 2 for Ma, and the remaining distributed among other swaras."
        ),
        make_pair(
            "How many ragas are there in Carnatic music?",
            "Carnatic music has 72 Melapakarta (parent) ragas from which thousands of Janya (derived) "
            "ragas are created. The total number of ragas in active use is estimated to be over 300, "
            "with many more described in ancient treatises. Each raga has a unique combination of swaras, "
            "gamakas, and characteristic phrases."
        ),
        make_pair(
            "What is the difference between Carnatic and Hindustani music?",
            "Carnatic music is the classical music tradition of South India (Tamil Nadu, Karnataka, Andhra Pradesh, "
            "Kerala), while Hindustani music is from North India. Key differences: Carnatic uses a fixed shruti "
            "system and 72 melakartas; Hindustani uses 10 thaats. Carnatic emphasises composition-based "
            "improvisation; Hindustani has more open improvisation. Carnatic uses complex gamakas; "
            "Hindustani uses meend and andolan. Carnatic talas are complex cycles; Hindustani uses "
            "simpler taals like teentaal."
        ),
    ]

    # Per-tala metadata pairs
    for tala in TALAS[:8]:
        pairs.append(make_pair(
            f"What is {tala}?",
            f"{tala} is a rhythmic cycle in Carnatic music. Talas in Carnatic music are measured cycles "
            f"of beats that provide the rhythmic framework for compositions. {tala} has its own specific "
            f"pattern of beats (laghu, drutam, anudrutam) and is used in various compositions across different speeds."
        ))

    return pairs


# ---------------------------------------------------------------------------
# Generator 7: Audio / interactive questions
# ---------------------------------------------------------------------------

def generate_audio_pairs() -> list[dict]:
    pairs = []

    for raga in random.sample(RAGAS, min(30, len(RAGAS))):
        for audio_type in AUDIO_TYPES[:3]:
            q = random.choice([
                f"Play {raga} {audio_type}.",
                f"I want to listen to the {audio_type} of raga {raga}.",
                f"Play the {audio_type} recording for {raga}.",
                f"Can you play {raga} {audio_type} audio?",
            ])
            a = (
                f"Playing the {audio_type} of raga {raga}. "
                f"Raga {raga} is {RAGA_ANSWERS.get(raga, 'an important Carnatic raga')} "
                f"The {audio_type} demonstrates the characteristic notes and phrases of this raga."
            )
            pairs.append(make_pair(q, a))

    # Mood-based audio suggestions
    mood_questions = [
        ("devotional ragas", DEVOTIONAL_RAGAS),
        ("ragas for morning", ["Bhairavi", "Todi", "Saveri", "Bilahari", "Natabhairavi"]),
        ("ragas for evening", ["Kalyani", "Kharaharapriya", "Kambhoji", "Sahana"]),
        ("peaceful ragas", ["Hindolam", "Revati", "Madhyamavati", "Nilambari"]),
        ("joyful ragas", ["Hamsadhwani", "Mohanam", "Bilahari", "Suddhasaveri"]),
        ("melancholic ragas", ["Bhairavi", "Todi", "Anandabhairavi", "Varali"]),
    ]
    for label, ragas in mood_questions:
        q = f"Suggest {label}."
        a = (
            f"Here are some {label} in Carnatic music: {', '.join(ragas[:5])}. "
            f"Each of these ragas has a distinct emotional character suited for {label.replace('ragas for ', '')} "
            f"performances and listening."
        )
        pairs.append(make_pair(q, a))
        pairs.append(make_pair(
            f"Which ragas should I listen to for a {label.split(' ')[0]} mood?",
            a
        ))

    return pairs


# ---------------------------------------------------------------------------
# Generator 8: Advanced theory Q/A
# ---------------------------------------------------------------------------

def generate_advanced_theory_pairs() -> list[dict]:
    pairs = [
        make_pair(
            "What are the different types of gamakas in Carnatic music?",
            "Gamakas (ornaments) in Carnatic music include: Kampita (oscillation), Sphurita (grace note), "
            "Aahata (struck ornament), Pratyaahata (reverse stroke), Tripuchha (three-note ornament), "
            "Andola (swinging), Nokku (jerk), Odukkal (pressing), Ravai (wavy), Khanda (broken), "
            "Tiripa (ascending), Murchhana (scale modulation), Naama (name ornament), Bindu (dot), "
            "Ullasita (highlighting). Each gamaka has specific rules for application to different swaras "
            "in different ragas."
        ),
        make_pair(
            "Explain the concept of Manodharma Sangeetam.",
            "Manodharma Sangeetam refers to the improvisational aspect of Carnatic music. It includes: "
            "Alapana (free raga exploration without tala), Niraval (melodic improvisation on a composition line), "
            "Kalpana Swaras (improvised solfege passages), and Ragam Tanam Pallavi (the grand concert form). "
            "Manodharma requires deep knowledge of raga grammar, tala, and musical aesthetics. It is considered "
            "the highest expression of a musician's creativity within the tradition."
        ),
        make_pair(
            "What is the difference between sampurna and audava ragas?",
            "In Carnatic music, ragas are classified by the number of swaras used: "
            "Sampurna ragas use all 7 swaras in both arohana and avarohana (e.g., Shankarabharanam, Kalyani). "
            "Shadava ragas use 6 swaras (e.g., Mohana which omits Ni). "
            "Audava ragas use 5 swaras (e.g., Mohanam which uses Sa Ri2 Ga3 Pa Da2). "
            "Ragas can also be vakra (zigzag) where the scale is not strictly ascending or descending."
        ),
        make_pair(
            "Explain raga grammar in Carnatic music.",
            "Raga grammar (raga lakshana) defines the rules for each raga: "
            "Arohana-Avarohana (ascending and descending scales), Vadi-Samvadi (important note pair), "
            "Graha Swara (starting note), Nyasa Swara (resting note), characteristic phrases (prayogas), "
            "prohibited note combinations, appropriate gamakas for each swara, time of performance, "
            "and rasa (emotional mood). A musician must internalise these rules to correctly render a raga."
        ),
        make_pair(
            "What is a Varnam and why is it important?",
            "A Varnam is a comprehensive compositional form that encapsulates all the technical aspects of a raga. "
            "It consists of Pallavi, Anupallavi, Muktayi Swara, Charanam, and Chittaswara sections. "
            "Varnams are classified as Tanavarnam (used in concerts) and Padavarnam (used in dance). "
            "They are considered essential practice pieces because they systematically present a raga's grammar, "
            "characteristic phrases, and rhythmic patterns. Advanced students typically begin concerts with a Varnam."
        ),
        make_pair(
            "Explain the Suladi Sapta Tala system.",
            "The Suladi Sapta Tala system consists of 7 basic talas: Dhruva, Matya, Rupaka, Jampa, Triputa, "
            "Ata, and Eka. When combined with 5 jatis (Tisra, Chatusra, Khanda, Misra, Sankirna), they produce "
            "35 talas. Further variations create 175 talas. In practice, the most common talas are Adi Tala "
            "(Chatusra Jati Triputa), Rupaka, Misra Chapu, and Khanda Chapu."
        ),
        make_pair(
            "What are the primary differences between janya and melapakarta ragas?",
            "Melapakarta ragas are parent scales with all 7 swaras used in strict ascending order. "
            "There are exactly 72 melakartas categorised in the Katapayadi system. "
            "Janya ragas are derived from melakartas and can omit swaras (audava, shadava), "
            "use vakra (zigzag) patterns, use different ascending and descending scales (bhashanga), "
            "or borrow swaras from other melakartas (bhashanga ragas). Most ragas performed in concerts are janyas."
        ),
        make_pair(
            "How does Kalpana Swara improvisation work?",
            "Kalpana Swaras (also called Swarakalpana) is improvised solfege improvisation in Carnatic music. "
            "The performer improvises swara passages (using Sa Ri Ga Ma Pa Da Ni syllables) within the raga's "
            "framework, always returning to the designated note in the composition. The passages must: "
            "maintain raga bhava, stay within tala boundaries, use correct gamaka for each swara, "
            "and end on the graha swara of the composition. It is typically performed after niraval."
        ),
    ]
    return pairs


# ---------------------------------------------------------------------------
# Main dataset generation
# ---------------------------------------------------------------------------

def generate_dataset(max_examples: int = TARGET_MAX) -> tuple[list[dict], int]:
    all_pairs: list[dict] = []

    logger.info("Generating concept/definition pairs...")
    all_pairs.extend(generate_concept_pairs())
    logger.info("  -> %d pairs", len(all_pairs))

    logger.info("Generating raga pairs...")
    raga_pairs = generate_raga_pairs()
    all_pairs.extend(raga_pairs)
    logger.info("  -> %d total pairs", len(all_pairs))

    logger.info("Generating composer pairs...")
    all_pairs.extend(generate_composer_pairs())
    logger.info("  -> %d total pairs", len(all_pairs))

    logger.info("Generating metadata pairs...")
    all_pairs.extend(generate_metadata_pairs())
    logger.info("  -> %d total pairs", len(all_pairs))

    logger.info("Generating audio/interactive pairs...")
    all_pairs.extend(generate_audio_pairs())
    logger.info("  -> %d total pairs", len(all_pairs))

    logger.info("Generating advanced theory pairs...")
    all_pairs.extend(generate_advanced_theory_pairs())
    logger.info("  -> %d total pairs", len(all_pairs))

    logger.info("Generating pairs from extracted text files...")
    text_pairs = generate_text_pairs(EXTRACTED_DIR)
    all_pairs.extend(text_pairs)
    logger.info("  -> %d total pairs", len(all_pairs))

    logger.info("Generating pairs from CSV music dataset...")
    csv_pairs = generate_csv_pairs(CSV_PATH)
    all_pairs.extend(csv_pairs)
    logger.info("  -> %d total pairs (including CSV)", len(all_pairs))

    # Deduplication
    seen_q: set[str] = set()
    seen_a: set[str] = set()
    deduped: list[dict] = []
    duplicates_removed = 0
    for pair in all_pairs:
        q_hash = _hash(pair["instruction"])
        a_hash = _hash(pair["output"])
        if q_hash in seen_q or a_hash in seen_a:
            duplicates_removed += 1
            continue
        # Quality gate
        if len(pair["instruction"].strip()) < 10:
            duplicates_removed += 1
            continue
        if len(pair["output"].strip()) < 30:
            duplicates_removed += 1
            continue
        seen_q.add(q_hash)
        seen_a.add(a_hash)
        deduped.append(pair)

    logger.info("After deduplication: %d pairs (%d removed)", len(deduped), duplicates_removed)

    # Shuffle and trim to max
    random.shuffle(deduped)
    final = deduped[:max_examples]

    # Pad to minimum if needed (by repeating with slight variation)
    if len(final) < TARGET_MIN:
        logger.warning(
            "Only %d examples generated (target min: %d). "
            "Add more extracted text files to data/extracted_text/ for better coverage.",
            len(final), TARGET_MIN,
        )

    return final, duplicates_removed


def save_dataset(pairs: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(pairs, f, ensure_ascii=False, indent=2)
    logger.info("Saved %d examples to %s", len(pairs), path)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate CarnaticGPT training dataset")
    parser.add_argument("--max", type=int, default=TARGET_MAX, help="Maximum examples to generate")
    parser.add_argument("--output", type=str, default=str(OUTPUT_FILE), help="Output JSON path")
    args = parser.parse_args()

    total_before = 0
    final_dataset, dupes_removed = generate_dataset(max_examples=args.max)
    output_path = Path(args.output)
    save_dataset(final_dataset, output_path)

    status = "OK: TARGET MET" if len(final_dataset) >= TARGET_MIN else "WARNING: BELOW TARGET - add more extracted text"
    
    print("\n" + "=" * 50)
    print("DATASET GENERATION COMPLETE")
    print("=" * 50)
    print(f"Total Q/A generated (before dedup): ~{len(final_dataset) + dupes_removed}")
    print(f"Duplicates removed:                  {dupes_removed}")
    print(f"Final dataset size:                  {len(final_dataset)}")
    print(f"Output saved to:                     {output_path}")
    print(f"Target range:                        {TARGET_MIN}-{TARGET_MAX}")
    print(f"Status:                              {status}")
    print("=" * 50)
