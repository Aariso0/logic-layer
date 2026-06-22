"""
Verdict Formatting Layer.

This module converts raw verification results produced by the
verification orchestrator into structured, human-readable CLI output.

Responsibilities:
    - Validate incoming verdict dictionaries.
    - Convert dictionaries into strongly typed Verdict objects.
    - Detect hallucinated claims.
    - Format individual verdicts.
    - Generate complete verification reports.

The formatter is presentation-only and contains no verification logic.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Mapping, Optional

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class Verdict:
    """Structured representation of a single claim verdict.

    Attributes:
        claim:
            The atomic factual claim that was checked.

        verdict:
            One of:
                - verified
                - wrong
                - unverified

        evidence:
            Evidence supporting or contradicting the claim.

        source_url:
            URL of the source providing evidence.

        correction:
            Correct statement for wrong claims.

        tier_used:
            Verification tier that produced the result.
            "none" indicates no tier found evidence.

    Example:
        >>> Verdict(
        ...     claim="Paris is the capital of France",
        ...     verdict="verified",
        ...     evidence="Government reference",
        ...     source_url="https://example.com",
        ...     tier_used="tier1",
        ... )
    """

    claim: str
    verdict: str
    evidence: Optional[str] = None
    source_url: Optional[str] = None
    correction: Optional[str] = None
    tier_used: str = "none"


def _parse_verdict(raw: Mapping[str, Any]) -> Verdict:
    """Convert a raw verdict dictionary into a Verdict object.

    Args:
        raw:
            Raw verdict dictionary containing at minimum:
                - claim
                - verdict

    Returns:
        Parsed Verdict instance.

    Raises:
        ValueError:
            If required fields are missing or the verdict
            type is invalid.
    """
    required_fields = ("claim", "verdict")

    for field_name in required_fields:
        if not raw.get(field_name):
            raise ValueError(
                f"Verdict missing required field: "
                f"'{field_name}'. Got: {raw}"
            )

    valid_verdicts = {"verified", "wrong", "unverified"}

    if raw["verdict"] not in valid_verdicts:
        raise ValueError(
            f"Unknown verdict type: '{raw['verdict']}'. "
            f"Expected one of {sorted(valid_verdicts)}"
        )

    return Verdict(
        claim=str(raw["claim"]),
        verdict=str(raw["verdict"]),
        evidence=raw.get("evidence"),
        source_url=raw.get("source_url"),
        correction=raw.get("correction"),
        tier_used=str(raw.get("tier_used", "none")),
    )


def _is_hallucinated(verdict: Verdict) -> bool:
    """Determine whether a wrong claim is a hallucination.

    Notes:
        Wrong claim:
            Evidence exists and contradicts the claim.

        Hallucinated claim:
            No evidence footprint exists and no verification
            tier was able to support the claim.

    Args:
        verdict:
            Parsed Verdict object.

    Returns:
        True if the verdict is considered hallucinated.
    """
    return (
        verdict.verdict == "wrong"
        and verdict.tier_used == "none"
    )


def _format_verified(verdict: Verdict) -> str:
    """Format a verified verdict for CLI output."""
    source = verdict.source_url or "local knowledge base"
    evidence = verdict.evidence or "matched local fact"

    return "\n".join(
        [
            "  ✓  VERIFIED",
            f"     Claim    : {verdict.claim}",
            f"     Evidence : {evidence}",
            f"     Source   : {source}",
        ]
    )


def _format_wrong(verdict: Verdict) -> str:
    """Format an incorrect verdict for CLI output."""
    correct = (
        verdict.correction
        or verdict.evidence
        or "see source"
    )

    source = verdict.source_url or "local knowledge base"

    if _is_hallucinated(verdict):
        label = "  ⚡  HALLUCINATED"
        note = (
            "     Note     : AI invented this claim. "
            "No supporting evidence was found."
        )
    else:
        label = "  ✗  WRONG"
        note = None

    lines = [
        label,
        f"     AI said  : {verdict.claim}",
        f"     Truth    : {correct}",
        f"     Source   : {source}",
    ]

    if note:
        lines.append(note)

    return "\n".join(lines)


def _format_unverified(verdict: Verdict) -> str:
    """Format an unverified verdict for CLI output."""
    return "\n".join(
        [
            "  ⚠  UNVERIFIED",
            f"     Claim    : {verdict.claim}",
            (
                "     Status   : No evidence found in local "
                "database or trusted sources."
            ),
            (
                "     Action   : Treat this claim with caution "
                "and verify independently."
            ),
        ]
    )


def format_verdict(raw: Mapping[str, Any]) -> str:
    """Format a single verdict dictionary.

    Args:
        raw:
            Raw verdict dictionary.

    Returns:
        Human-readable verdict block.
    """
    try:
        verdict = _parse_verdict(raw)
    except ValueError as error:
        logger.error("Failed to parse verdict: %s", error)
        return f"  ?  PARSE ERROR: {error}"

    match verdict.verdict:
        case "verified":
            return _format_verified(verdict)

        case "wrong":
            return _format_wrong(verdict)

        case "unverified":
            return _format_unverified(verdict)

        case _:
            return (
                "  ?  UNKNOWN VERDICT TYPE "
                f"({verdict.verdict})"
            )


def format_report(
    verdicts: list[Mapping[str, Any]],
) -> str:
    """Generate a complete verification report.

    The report is ordered by urgency:

        1. Wrong / hallucinated claims
        2. Unverified claims
        3. Verified claims

    Args:
        verdicts:
            Collection of raw verdict dictionaries.

    Returns:
        Fully formatted CLI report.

    Example:
        >>> verdicts = [
        ...     {
        ...         "claim": "Earth has two moons",
        ...         "verdict": "wrong",
        ...         "correction": "Earth has one moon",
        ...     }
        ... ]
        >>> print(format_report(verdicts))
    """
    wide = "━" * 56
    sep = "─" * 56

    if not verdicts:
        logger.warning(
            "format_report called with empty verdict list"
        )

        return (
            f"\n"
            f"{wide}\n"
            f"  LOGIC LAYER — VERIFICATION REPORT\n"
            f"{wide}\n"
            f"  No claims were identified in the response.\n"
            f"{wide}"
        )

    # Parse all verdicts once to avoid repeated validation.
    parsed_verdicts: list[Verdict] = []
    parse_errors: list[str] = []

    for raw in verdicts:
        try:
            parsed_verdicts.append(_parse_verdict(raw))
        except ValueError as error:
            logger.error(
                "Skipping malformed verdict: %s",
                error,
            )
            parse_errors.append(str(error))

    verified = [
        v for v in parsed_verdicts
        if v.verdict == "verified"
    ]

    wrong = [
        v for v in parsed_verdicts
        if v.verdict == "wrong"
    ]

    unverified = [
        v for v in parsed_verdicts
        if v.verdict == "unverified"
    ]

    hallucinated = [
        v for v in wrong
        if _is_hallucinated(v)
    ]

    total = len(parsed_verdicts)

    summary = "  " + "  |  ".join(
        [
            f"{len(verified)} verified",
            f"{len(wrong)} wrong",
            f"{len(hallucinated)} hallucinated",
            f"{len(unverified)} unverified",
            f"{total} total",
        ]
    )

    sections: list[str] = []

    # Highest-priority findings appear first.
    if wrong:
        sections.extend(
            [
                "WRONG / HALLUCINATED CLAIMS",
                sep,
            ]
        )

        for verdict in wrong:
            sections.append(
                _format_wrong(verdict)
            )
            sections.append("")

    if unverified:
        sections.extend(
            [
                "UNVERIFIED CLAIMS",
                sep,
            ]
        )

        for verdict in unverified:
            sections.append(
                _format_unverified(verdict)
            )
            sections.append("")

    if verified:
        sections.extend(
            [
                "VERIFIED CLAIMS",
                sep,
            ]
        )

        for verdict in verified:
            sections.append(
                _format_verified(verdict)
            )
            sections.append("")

    # Show parsing failures separately so users know
    # some verdicts could not be processed.
    if parse_errors:
        sections.extend(
            [
                "PARSE ERRORS",
                sep,
            ]
        )

        for error in parse_errors:
            sections.append(
                f"  ?  {error}"
            )
            sections.append("")

    output_lines = [
        "",
        wide,
        "  LOGIC LAYER — VERIFICATION REPORT",
        wide,
        summary,
        wide,
        "",
        *sections,
        wide,
    ]

    logger.info(
        (
            "Report formatted: "
            "%d total, %d wrong, "
            "%d unverified, %d verified"
        ),
        total,
        len(wrong),
        len(unverified),
        len(verified),
    )

    return "\n".join(output_lines)

