import difflib
import re
from collections import Counter


_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "into", "is", "it",
    "of", "on", "or", "that", "the", "to", "with", "we", "this", "these", "those", "their", "our",
    "paper", "method", "results", "using", "used", "use", "based", "can", "also", "show", "shows",
}


def _normalize_text(text: str) -> str:
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", text or "")
    text = re.sub(r"`[^`]*`", " ", text)
    text = re.sub(r"[#>*_\-]", " ", text)
    return text.lower()


def _extract_keywords(text: str, max_terms: int = 40) -> list[str]:
    normalized = _normalize_text(text)
    terms = re.findall(r"[a-z][a-z0-9]{2,}", normalized)
    filtered = [term for term in terms if term not in _STOPWORDS]
    freq = Counter(filtered)
    return [term for term, _ in freq.most_common(max_terms)]


def _jaccard_similarity(lhs: set[str], rhs: set[str]) -> float:
    if not lhs or not rhs:
        return 0.0
    union = lhs | rhs
    if not union:
        return 0.0
    return len(lhs & rhs) / len(union)


def _relation_type(source_markdown: str, overlap_score: float) -> str:
    cues = ("compare", "compared", "baseline", "outperform", "extends", "extension", "prior work")
    has_compare_cue = any(cue in (source_markdown or "").lower() for cue in cues)
    if has_compare_cue and overlap_score >= 0.2:
        return "extends_or_compares"
    return "related_topic"


def find_related_papers(
    source_title: str,
    source_markdown: str,
    candidates: list[dict],
    max_results: int = 5,
    min_score: float = 0.22,
) -> list[dict]:
    """Rank existing papers by topical relatedness to the provided source paper."""
    source_keywords = set(_extract_keywords(f"{source_title}\n{source_markdown}"))
    ranked = []

    for candidate in candidates:
        candidate_id = candidate.get("id")
        candidate_title = candidate.get("title") or ""
        candidate_markdown = candidate.get("markdown") or ""

        # Fallback if markdown is unavailable
        candidate_text = candidate_markdown if candidate_markdown else candidate_title
        candidate_keywords = set(_extract_keywords(f"{candidate_title}\n{candidate_text}"))

        title_similarity = difflib.SequenceMatcher(None, source_title.lower(), candidate_title.lower()).ratio()
        keyword_similarity = _jaccard_similarity(source_keywords, candidate_keywords)
        score = (0.45 * title_similarity) + (0.55 * keyword_similarity)

        if score < min_score:
            continue

        shared_terms = sorted(source_keywords & candidate_keywords)
        evidence = ", ".join(shared_terms[:5])
        relation_type = _relation_type(source_markdown, keyword_similarity)

        ranked.append({
            "id": candidate_id,
            "title": candidate_title,
            "score": round(score, 4),
            "relation_type": relation_type,
            "evidence": evidence,
        })

    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked[:max_results]
