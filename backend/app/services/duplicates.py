import math
import re
import unicodedata
from collections import Counter


def normalize_text(text: str) -> str:
    value = unicodedata.normalize("NFKC", text).lower()
    value = re.sub(r"https?://\S+|www\.\S+", " ", value)
    value = re.sub(r"[^\w\s]", " ", value, flags=re.UNICODE)
    return re.sub(r"\s+", " ", value).strip()


def _word_ngrams(text: str, size: int = 2) -> Counter[str]:
    words = normalize_text(text).split()
    if len(words) < size:
        return Counter(words)
    return Counter(" ".join(words[i : i + size]) for i in range(len(words) - size + 1))


def cosine_similarity(left: str, right: str) -> float:
    """Lightweight local cosine similarity over normalized word bigrams."""
    a, b = _word_ngrams(left), _word_ngrams(right)
    if not a or not b:
        return 0.0
    dot = sum(count * b.get(term, 0) for term, count in a.items())
    norm_a = math.sqrt(sum(value * value for value in a.values()))
    norm_b = math.sqrt(sum(value * value for value in b.values()))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0

