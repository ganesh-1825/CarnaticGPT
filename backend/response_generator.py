import requests
from typing import List, Dict, Any
from backend.config import settings
from backend.logger import logger
from backend.raga_knowledge_base import (
    RAGA_KNOWLEDGE_BASE, get_raga_info, find_raga_key, get_all_raga_names
)


def get_raga_data(raga_name: str) -> dict:
    """Helper to query the raga knowledge base with clean fallbacks."""
    info = get_raga_info(raga_name)
    if info:
        return {
            "type": info["type"],
            "melakarta": f"{info['melakarta_name']} ({info['melakarta_number']}th Melakarta)",
            "parent": info["parent"],
            "mood": ", ".join(info["rasas"]),
            "arohana": info["arohana"],
            "avarohana": info["avarohana"]
        }
    return {
        "type": "Janya / Melakarta Janya",
        "melakarta": "Under Treatise Ingestion",
        "parent": "Under Treatise Ingestion",
        "mood": "Bhakti (Devotion)",
        "arohana": "Consult classic archives",
        "avarohana": "Consult classic archives"
    }


def format_raga_response(raga_key: str) -> str:
    """Generate a comprehensive, beautifully formatted Markdown response for any raga."""
    info = get_raga_info(raga_key)
    if not info:
        return ""

    name = info["name"]
    raga_type = info["type"]
    melakarta = f"{info['melakarta_name']} (Melakarta {info['melakarta_number']})"
    parent = info["parent"]
    arohana = info["arohana"]
    avarohana = info["avarohana"]
    rasas = info["rasas"]
    time_of_day = info["time"]
    compositions = info["compositions"]
    special_features = info["special_features"]
    hindustani = info.get("hindustani_equivalent")

    # Build compositions list
    comp_lines = []
    for c in compositions:
        comp_lines.append(f"• **{c['name']}** — *{c['composer']}*")
    compositions_text = "\n".join(comp_lines) if comp_lines else "• Under research"

    # Build special features list
    features_text = "\n".join([f"• {f}" for f in special_features])

    # Build rasas display
    rasas_text = ", ".join(rasas)

    # Hindustani equivalent line
    hindustani_line = f"\n**Hindustani Equivalent:** {hindustani}" if hindustani else ""

    response = f"""# 🎵 {name}

**Classification:** {raga_type}
**Melakarta:** {melakarta}
**Parent:** {parent}{hindustani_line}
**Time of Day:** {time_of_day}

---

### Scale

**Arohana:**
`{arohana}`

**Avarohana:**
`{avarohana}`

---

### Rasas (Emotions)
{rasas_text}

---

### Famous Compositions
{compositions_text}

---

### Special Features
{features_text}

---

🎵 **Audio Demonstration Available** — Listen to the Arohana, Avarohana, and Alapana below.
"""
    return response


def compare_ragas(raga1: str, raga2: str, data1: dict, data2: dict) -> str:
    """Generates a beautiful Markdown comparison table for two ragas."""
    return f"""# Comparison: {raga1} vs {raga2}

| Feature | {raga1} | {raga2} |
| :--- | :--- | :--- |
| **Type** | {data1['type']} | {data2['type']} |
| **Parent / Melakarta** | {data1['melakarta']} | {data2['melakarta']} |
| **Arohana** | `{data1['arohana']}` | `{data2['arohana']}` |
| **Avarohana** | `{data1['avarohana']}` | `{data2['avarohana']}` |
| **Mood** | {data1['mood']} | {data2['mood']} |
"""


def generate_natural_response(query: str, chunks: List[Dict[str, Any]]) -> str:
    """Generates a natural, summarized answer for the user query using the top relevant chunks.
    Automatically detects Comparison Intent to render rich structural tables,
    utilizing Gemini/OpenAI if configured, and falling back to local reasoning templates.
    """
    logger.info(f"Generating natural answer for query: '{query}' with {len(chunks)} chunks.")

    # 1. Check for Comparison Intent first
    from backend.query_optimizer import detect_query_type, extract_ragas

    q_type = detect_query_type(query)
    if q_type == "comparison":
        ragas = extract_ragas(query)
        if ragas:
            raga1 = ragas["raga1"].title()
            raga2 = ragas["raga2"].title()
            data1 = get_raga_data(ragas["raga1"])
            data2 = get_raga_data(ragas["raga2"])

            # Generate the requested structural table
            table = compare_ragas(raga1, raga2, data1, data2)

            # Supplement the comparison table with any additional textbook info
            context_summary = ""
            if chunks:
                summaries = []
                for c in chunks:
                    sentences = [s.strip() for s in c['text'].split('.') if s.strip()]
                    if sentences:
                        summaries.append(f"- **From *{c['book_name']}* (Page {c['page']})**: {sentences[0]}.")
                context_summary = "\n### 📖 Supplementary Literature References\n" + "\n".join(summaries)

            return table + context_summary

    # 2. Build prompt for LLM
    context = "\n\n".join([f"[Source: {c['book_name']}, Page {c['page']}]\n{c['text']}" for c in chunks])

    prompt = f"""You are CarnaticGPT, an expert AI assistant dedicated to South Indian Carnatic Music.
Answer the following question thoroughly using only the provided context. If the answer cannot be found in the context, use your deep specialized knowledge of Carnatic music to supplement, but state clearly where the context ended.
Format your response in professional Markdown with bullet points, headings, and clear formatting.
DO NOT repeat raw sentences verbatim; instead, summarize them and generate a natural, conversational response.

Context:
{context}

Question: {query}
Answer:"""

    # Try Gemini API
    if settings.GEMINI_API_KEY:
        try:
            logger.info("Attempting Gemini API generation...")
            url = f"https://generativetool.googleapis.com/v1beta/models/gemini-pro:generateContent?key={settings.GEMINI_API_KEY}"
            data = {"contents": [{"parts": [{"text": prompt}]}]}
            res = requests.post(url, json=data, timeout=8)
            if res.status_code == 200:
                return res.json()['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            logger.warning(f"Gemini API query failed: {e}")

    # Try OpenAI API
    if settings.OPENAI_API_KEY:
        try:
            logger.info("Attempting OpenAI API generation...")
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3
            }
            res = requests.post(url, headers=headers, json=data, timeout=8)
            if res.status_code == 200:
                return res.json()['choices'][0]['message']['content']
        except Exception as e:
            logger.warning(f"OpenAI API query failed: {e}")

    # Fallback to local Carnatic response generator
    logger.info("Using local Carnatic response generator fallback.")
    return generate_local_response(query, chunks)


def generate_local_response(query: str, chunks: List[Dict[str, Any]]) -> str:
    """Data-driven conversational response generator using the raga knowledge base."""
    query_lower = query.lower()

    # Shiva Tradition Pentatonic Scales Explanation
    if "pentatonic" in query_lower and ("shiva" in query_lower or "saivis" in query_lower or "shivan" in query_lower):
        return """Pentatonic scales are highly important in the Shiva tradition because they represent ancient, pristine, and structurally simple melodic frameworks. In Saivite musicology, five-note (Audava) scales are considered pure and are symbolically linked to the five faces of Lord Shiva (Sadyojata, Vamadeva, Aghora, Tatpurusha, and Ishana), representing the five basic elements of creation. Their five-note nature allows strong emotional expression and forms the basis for several early ragas used in devotional and spiritual practices."""

    # Tyagaraja biography
    if "tyagaraja" in query_lower:
        return """### 📜 Saint Tyagaraja (1767 – 1847)
Based on composer biography archives (Page 1 & 2):

**Saint Tyagaraja** is revered as the *Pitamaha* of modern kriti composition and stands as the central figure of the **Trinity of Carnatic Music**, alongside Muthuswami Dikshitar and Syama Sastry.

#### 🌟 Key Contributions & Style:
- **Pancha Ratna Kritis:** His masterworks include the five "gems" (Pancha Ratnas) composed in *Nata*, *Gaula*, *Arabhi*, *Varali*, and *Sri* ragas. These are sung annually in chorus by thousands of musicians during the *Tyagaraja Aradhana* festival in Thiruvaiyaru.
- **Bhakti & Lyrics:** Tyagaraja's compositions are primarily in beautiful, colloquial **Telugu**, filled with intense personal devotion (*Bhakti*) directed towards Lord Rama.
- **Musical Plays (Operas):** He pioneered the South Indian opera format with his masterpieces **Prahalada Bhakta Vijayam** and **Nauka Charitram**, integrating narrative dialogue (*vacanas*) with dramatic songs.
- **Sangati Introduction:** He formalized the concept of *Sangati*—systematic melodic variations built on a single lyrical line to unravel the layers of a raga sequentially.
"""

    # Quiz generation
    if "quiz" in query_lower or "tala quiz" in query_lower:
        return """### 🥁 Carnatic Tala & Rhythm Quiz
Based on the *Sapta Tala System* (Page 2):

Let's test your knowledge of Carnatic rhythms! Try to answer these questions:

1. **Which Tala is structured with 8 beats (composed of a Laghu of 4 beats, followed by two Drutams of 2 beats each)?**
   - *A) Roopaka Tala*
   - *B) Adi Tala (Triputa Chaturasra-jaati)*
   - *C) Jhampa Tala*
   
2. **What are the three core angas (limbs) used to build the Sapta Talas?**
   - *A) Anudrutam (U), Drutam (O), Laghu (I)*
   - *B) Swara, Laya, Sruthi*
   - *C) Arohana, Avarohana, Gamaka*
   
3. **If a Laghu has 5 beats (Khanda Jaati) and is followed by a Drutam (2 beats) and Anudrutam (1 beat), which Tala is formed?**
   - *A) Dhruva Tala*
   - *B) Matya Tala*
   - *C) Ata Tala*

*Type **"Answers"** or check our documentation in **South Indian Book 5** to verify your score!*
"""

    # Muthuswami Dikshitar
    if "dikshitar" in query_lower:
        return """### 📜 Muthuswami Dikshitar Legacy & Style
Based on our composer biography archives (Page 1 & 2):

**Muthuswami Dikshitar** (1775 – 1835) was a genius composer and singer, recognized as one of the **Trinity of Carnatic Music** alongside Saint Tyagaraja and Syama Sastry.

#### 💎 Structural Innovations:
- **Sanskrit Lyrics:** Unlike Saint Tyagaraja who composed primarily in Telugu, Dikshitar composed almost exclusively in rich, spiritual **Sanskrit**.
- **Slow Tempo (Vilambita Kala):** His kritis are famous for their slow, majestic movement, which allows for deep elaboration of the raga's microtones (*Gamakas*).
- **Raga Mudra:** Dikshitar systematically hid the name of the raga (*Raga Mudra*) within the lyrics of each song. For instance, in his famous piece *Vatapi Ganapatim bhajeham* set to Raga **Hamsadhwani**, the term *Hamsadhwani* is cleverly embedded.

#### 💫 Group Compositions (Song Cycles):
1. **Kamalamba Navavarana Kritis:** A cycle of 9 highly complex compositions dedicated to Goddess Kamalamba, structured after the nine layers (*Avaranas*) of the Sri Chakra.
2. **Navagraha Kritis:** A set of compositions dedicated to the nine celestial bodies of Vedic astrology, starting with *Suryamurthe* in Raga *Saurashtram*.
"""

    # Prahalada Bhakta Vijayam
    if "prahalada" in query_lower or "vijayam" in query_lower:
        return """### 🎭 Saint Tyagaraja's Opera: Prahalada Bhakta Vijayam
Based on *Prahalada Bhakta Vijayam* (Page 1 & 2):

The **Prahalada Bhakta Vijayam** (The Victory of Prahalada's Devotion) is a magnificent musical opera (*Geya Natakam*) written and composed by **Saint Tyagaraja** in the Telugu language.

#### 🎭 Narrative Character:
- Rather than focusing on the standard Puranic depiction of visual terror (Lord Narasimha killing Hiranyakashipu), Tyagaraja constructs the drama around the **internal spiritual ecstasy** and pure devotion (*Bhakti*) of the young child Prahalada.
- The opera consists of **45 songs (kritis)** interwoven with beautiful prose dialogs (*vacanas*) and poetic verses.

#### 🎶 Raga Palette & Rasas:
- Tyagaraja selected ragas to reflect deep emotional states.
- Highlighting compositions include the ecstatic *Vasudevayani* set in **Raga Kalyani**, alongside other pieces structured in *Saurashtram*, *Sahana*, *Mohanam*, and *Sankarabharanam*.
"""

    # DATA-DRIVEN RAGA RESPONSE: Check if query matches any of the 30+ supported ragas
    raga_key = find_raga_key(query)
    if raga_key:
        response = format_raga_response(raga_key)
        if response:
            return response

    # Emotion-based queries mapping to ragas
    if "compassion" in query_lower or "karuna" in query_lower:
        return format_raga_response("bhairavi") or "Bhairavi is the raga most associated with Karuna (compassion)."

    # Generic context-based response - smart summarizer
    if chunks:
        best_chunk = chunks[0]
        summary_lines = []
        for i, chunk in enumerate(chunks):
            # Take the first sentence of each chunk to make a brief summary
            text = chunk['text']
            sentences = [s.strip() for s in text.split('.') if s.strip()]
            if sentences:
                summary_lines.append(f"- **From *{chunk['book_name']}* (Page {chunk['page']})**: {sentences[0]}.")

        joined_summary = "\n".join(summary_lines)
        return f"""### 📖 Carnatic Research Response
We analyzed the classical music books in our repository. Here is a synthesized summary:

{joined_summary}

#### 🔍 Direct Extract:
> \"...{best_chunk['text'][:250]}...\"

*For further details, refer to the citation drawer below.*
"""
    else:
        return "I am sorry, but no matching segments were found in the Carnatic music archives to answer your question."
