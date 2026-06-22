import re
import math

SECTOR_KEYWORDS = {
    "Defence": [
        "defence", "defense", "military", "drdo", "weapons", "drone warfare",
        "idex", "nato", "people's liberation army", "armed forces",
        "ministry of defence", "ballistic", "missile", "combat", "warfighter",
        "pentagon", "air force", "navy seal", "defence procurement",
    ],
    "Robotics": [
        "robot", "robotics", "autonomous vehicle", "drone delivery", "uav ",
        "cobots", "industrial robot", "bvlos", "self-driving", "unmanned aerial",
        "humanoid", "legged robot", "robotic",
    ],
    "Climate": [
        "climate", "carbon", "renewable", "agritech", "agriculture",
        "cleantech", "solar", "electric vehicle", "ev battery", "emissions",
        "sustainability", "net zero", "green hydrogen", "fertilizer", "crop",
        "geoengineering", "wind energy", "wind farm", "offshore wind",
        "energy transition", "coal plant", "natural gas", "grid-scale",
        "battery storage", "clean energy", "fossil fuel",
    ],
    "MedTech": [
        "medtech", "healthtech", "telemedicine", "diagnostics", "medical device",
        "health ai", "clinical trial", "therapeutics",
        "drug discovery", "biotech", "genomics", "wearable health",
        "brain-computer interface", "bci", "gene therapy", "medical implant",
    ],
    "AI Infrastructure": [
        "ai infrastructure", "gpu cluster", "data centre", "data center",
        "large language model", "llm", "foundation model", "cloud ai",
        "training compute", "hyperscaler", "ai chip", "tpu", "nvidia",
        "inference chip", "ai accelerator",
    ],
    "Semiconductors": [
        "semiconductor", "chip fab", "vlsi", "tsmc", "fabless",
        "chips act", "wafer", "node process", "arm holdings",
        "integrated circuit", "chip design", "foundry", "system-on-chip",
        "silicon", "finfet", "logic chip",
    ],
    "Quantum Computing": [
        "quantum computing", "qubit", "quantum communication",
        "quantum cryptography", "quantum advantage", "quantum hardware",
        "quantum software", "national quantum",
    ],
    "Cybersecurity": [
        "cybersecurity", "cyber attack", "zero trust", "cert-in", "data breach",
        "ransomware", "cisa", "vulnerability", "penetration testing",
        "threat intelligence", "endpoint security",
    ],
}

MIN_SENTENCE_LEN = 40


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in parts if len(s.strip()) >= MIN_SENTENCE_LEN]


def _extract_excerpt(body: str) -> str:
    sentences = _split_sentences(body)
    # Skip the first sentence (usually the lede/hook); take the next three
    picked = sentences[1:4] if len(sentences) > 3 else sentences[:3]
    return " ".join(picked)


def _classify_sectors(title: str, body: str) -> list[str]:
    text = (title + " " + body[:3000]).lower()
    return [sector for sector, kws in SECTOR_KEYWORDS.items()
            if any(kw in text for kw in kws)]


def enrich_article(title: str, body: str, word_count: int) -> dict:
    excerpt = _extract_excerpt(body) or body[:400]
    sectors = _classify_sectors(title, body)
    read_minutes = max(1, math.ceil(word_count / 200))
    return {
        "excerpt": excerpt,
        "signal": "",
        "sectors": sectors,
        "estimated_read_minutes": read_minutes,
    }
