"""Standalone relevance scoring module for ranking Zotero search results.

Pure Python, no external dependencies.
"""

from __future__ import annotations

import re

from zotero_mcp.utils import format_creators

_CURRENT_YEAR = 2026
_RECENCY_BASE_YEAR = 2000


def _tokenize(text: str) -> list[str]:
    """Split text into lowercase word tokens."""
    return re.findall(r"[a-z0-9]+", text.lower())


def score_text_match(query: str, candidate: str) -> float:
    """Score how well *candidate* matches *query*.

    Returns a float in [0, 1]:
      - 1.0  exact match (case-insensitive)
      - 0.7  candidate starts with query
      - 0.5  query is contained in candidate
      - 0.3 * (matching_words / total_query_words)  partial word overlap
      - 0.0  no overlap at all
    """
    if not query or not candidate:
        return 0.0

    q_lower = query.lower()
    c_lower = candidate.lower()

    if q_lower == c_lower:
        return 1.0
    if c_lower.startswith(q_lower):
        return 0.7
    if q_lower in c_lower:
        return 0.5

    q_words = set(_tokenize(query))
    if not q_words:
        return 0.0
    c_words = set(_tokenize(candidate))
    matching = q_words & c_words
    if matching:
        return 0.3 * (len(matching) / len(q_words))

    return 0.0


def score_creators_match(query: str, creators: list[dict]) -> float:
    """Score *query* against a Zotero creators list.

    Each creator dict may contain ``firstName`` / ``lastName`` (and
    ``creatorType``).  The query is matched against each formatted
    "FirstName LastName" string and the best score is returned.
    """
    if not creators:
        return 0.0

    best = 0.0
    for creator in creators:
        parts: list[str] = []
        if "firstName" in creator:
            parts.append(creator["firstName"])
        if "lastName" in creator:
            parts.append(creator["lastName"])
        if not parts and "name" in creator:
            parts.append(creator["name"])
        if not parts:
            continue
        name = " ".join(parts)
        s = score_text_match(query, name)
        if s > best:
            best = s
            if best == 1.0:
                break
    return best


def score_recency(date_str: str | None, max_boost: float = 0.1) -> float:
    """Return a small recency boost in [0, *max_boost*].

    Extracts the first four-digit year from *date_str*.  Years at or before
    2000 receive 0; the current year (2026) receives *max_boost*; values in
    between are linearly interpolated.
    """
    if not date_str:
        return 0.0

    m = re.search(r"\b(\d{4})\b", date_str)
    if not m:
        return 0.0

    year = int(m.group(1))
    if year <= _RECENCY_BASE_YEAR:
        return 0.0
    if year >= _CURRENT_YEAR:
        return max_boost

    span = _CURRENT_YEAR - _RECENCY_BASE_YEAR
    return max_boost * (year - _RECENCY_BASE_YEAR) / span


def rank_results(
    query: str,
    items: list[dict],
    search_fields: list[str],
    weights: dict[str, float] | None = None,
) -> list[tuple[dict, float]]:
    """Score and rank *items* by relevance to *query*.

    Parameters
    ----------
    query:
        The user's search string.
    items:
        Zotero API item dicts (each has a ``"data"`` sub-dict).
    search_fields:
        Which fields inside ``item["data"]`` to consider (e.g.
        ``["title", "creators", "abstractNote"]``).
    weights:
        Optional per-field weight multiplier; defaults to 1.0 for every
        field.

    Returns
    -------
    list[tuple[dict, float]]
        ``(item, normalised_score)`` pairs sorted descending by score.
        Scores are normalised to the 0-1 range.
    """
    if not items:
        return []

    if weights is None:
        weights = {}

    scored: list[tuple[dict, float]] = []

    for item in items:
        data = item.get("data", {})
        total = 0.0

        for field in search_fields:
            w = weights.get(field, 1.0)
            value = data.get(field)
            if value is None:
                continue

            if field == "creators" and isinstance(value, list):
                s = score_creators_match(query, value)
            else:
                s = score_text_match(query, str(value))

            total += s * w

        # Recency boost from the item's date.
        total += score_recency(data.get("date"))

        scored.append((item, total))

    # Normalise scores to 0-1.
    if scored:
        max_score = max(s for _, s in scored)
        if max_score > 0:
            scored = [(item, s / max_score) for item, s in scored]

    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored
