"""
spaCy-based claim extractor.

Given a raw text response produced by a target AI agent, this module splits
it into atomic, checkable factual claims and returns them in the contract
shape the orchestrator (step 5) consumes:

    list[{"claim_id": int, "text": str}]

The list is:
    - ordered (same order the claims appear in the source text),
    - deduplicated (case-insensitive, whitespace-normalized),
    - filtered to drop pure questions, pure interjections, and very short
      fragments that carry no checkable factual content.

Per the build plan (##3) the implementation uses a spaCy pipeline (sentence
segmentation + a small noun-chunk / token heuristic) rather than an LLM, so
it is fast, deterministic, and free at inference time.
"""

from __future__ import annotations

import re
from typing import Any

import spacy
from spacy.language import Language

# ---------------------------------------------------------------------------
# spaCy model loading
# ---------------------------------------------------------------------------
# We use the small English model (`en_core_web_sm`) per the build plan.
# Loading the model is the expensive part (~10-20 MB, one-time), so we keep
# a module-level singleton and load lazily on first use. This keeps `import
# claim_extractor` cheap for any caller that never actually extracts claims
# (e.g. unit tests that mock this module out).

_MODEL_NAME = "en_core_web_sm"
_nlp: Language | None = None

# Minimum character length for a sentence to be considered a claim candidate.
# Short fragments like "Yes.", "Okay.", "True." are pruned to avoid passing
# noise into Qwen / the orchestrator.
_MIN_CLAIM_CHARS = 12

# Maximum number of claims we will return from a single response. This is a
# safety bound to keep the Qwen context window reasonable even if a long
# agent response contains many distinct sentences.
_MAX_CLAIMS = 50


def _get_nlp() -> Language:
    """Return the loaded spaCy pipeline, loading it on first call."""
    global _nlp
    if _nlp is None:
        _nlp = spacy.load(_MODEL_NAME)
    return _nlp


# ---------------------------------------------------------------------------
# Heuristics for filtering non-claims
# ---------------------------------------------------------------------------

# Sentence-level heuristics: a sentence is considered "non-claim" if it
# matches any of these patterns.
_QUESTION_RE = re.compile(r"\?\s*$")  # ends in a question mark
_INTERJECTIONS = {
    "yes", "no", "okay", "ok", "thanks", "thank you", "sure", "right",
    "exactly", "correct", "indeed", "alright", "yep", "nope", "maybe",
    "perhaps", "hmm", "well", "so", "actually", "basically",
}


def _normalize(text: str) -> str:
    """Normalize whitespace and strip trailing punctuation noise."""
    return re.sub(r"\s+", " ", text).strip().strip("\"'`“”‘’")


def _is_question(sentence_text: str) -> bool:
    return bool(_QUESTION_RE.search(sentence_text))


def _is_interjection(sentence_text: str) -> bool:
    # Strip terminal punctuation, lowercase, and check against the list.
    cleaned = re.sub(r"[^a-z\s]", "", sentence_text.lower()).strip()
    return cleaned in _INTERJECTIONS


def _has_checkable_content(doc: Any) -> bool:
    """
    Return True if the spaCy `Doc` carries something we consider a checkable
    claim: at least one content token (noun, verb, adjective, or proper noun)
    AND at least one subject-like token (NOUN / PROPN).
    """
    if not any(token.pos_ in {"NOUN", "PROPN"} for token in doc):
        return False
    if not any(token.pos_ in {"NOUN", "PROPN", "VERB", "ADJ"} for token in doc):
        return False
    return True


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_claims(text: str) -> list[dict[str, str]]:
    """
    Split a raw agent response into atomic, checkable claims.

    Args:
        text: The raw text the target AI agent produced.

    Returns:
        A list shaped as `list[{"claim_id": int, "text": str}]`, ordered as
        the claims appear in the source text, deduplicated
        (case-insensitive, whitespace-normalized), and filtered to drop pure
        questions, pure interjections, and very short fragments.

    Notes:
        - If `text` is empty / non-string, returns `[]` (the orchestrator
          treats this as "no claims to check").
        - Output is capped at `_MAX_CLAIMS` entries.
    """
    if not isinstance(text, str) or not text.strip():
        return []

    nlp = _get_nlp()
    doc = nlp(text)

    seen: set[str] = set()
    claims: list[dict[str, str]] = []

    for sent in doc.sents:
        raw = sent.text
        text_stripped = raw.strip()
        if len(text_stripped) < _MIN_CLAIM_CHARS:
            continue
        if _is_question(text_stripped):
            continue
        if _is_interjection(text_stripped):
            continue
        if not _has_checkable_content(sent):
            continue

        normalized = _normalize(text_stripped).lower()
        if normalized in seen:
            continue
        seen.add(normalized)

        claims.append({"claim_id": len(claims), "text": _normalize(text_stripped)})

        if len(claims) >= _MAX_CLAIMS:
            break

    return claims


if __name__ == "__main__":
    # Quick manual smoke test:
    #   python -m logiclayer.verifier.claim_extractor
    sample = (
        "Python was created by Guido van Rossum and first released in 1991. "
        "The Eiffel Tower can be 15 cm taller during hot days. "
        "Did you know that the moon is made of green cheese? "
        "Yes. "
        "World War II ended in 1945."
    )
    for claim in extract_claims(sample):
        print(claim)
