Contribution Report – Verdict Formatting Layer

Contributor

Module: Reporting Layer
Files Contributed:

- "logiclayer/reporting/formatter.py"
- "logiclayer/tests/test_formatter.py"

---

1. Overview

The contribution focuses on implementing the presentation layer of the Logic Layer verification pipeline. This module converts structured verification results produced by the verification system into a human-readable CLI report while remaining completely independent of the verification logic itself.

The formatter follows the principle of separation of concerns. It does not perform claim verification, source retrieval, or decision making. Instead, it accepts validated verdict data, formats it consistently, and presents the results in an organized report for end users.

The accompanying test suite validates formatter behaviour across normal, invalid, and edge-case inputs to ensure output correctness and long-term maintainability.

---

2. Objectives

The formatter module was designed to achieve the following objectives:

- Convert raw verdict dictionaries into structured data objects.
- Validate incoming verdict data before formatting.
- Produce consistent CLI-friendly output.
- Separate formatting logic from verification logic.
- Handle malformed inputs gracefully.
- Generate complete verification reports with summary statistics.
- Maintain compatibility with the orchestrator through a structured verdict interface.
- Provide comprehensive automated test coverage.

---

3. Architecture

The reporting layer follows the architecture below.

Verifier / Orchestrator
            │
            │ Raw Verdict Dictionaries
            ▼
     formatter.py
            │
    Parse & Validate
            │
    Convert to Verdict Object
            │
    Format Individual Verdicts
            │
    Generate Final Report
            ▼
      CLI Output

The formatter acts purely as the presentation layer and has no dependency on verification algorithms.

---

4. formatter.py Contribution

4.1 Verdict Data Model

A dedicated "Verdict" dataclass was implemented to represent every verified claim.

Responsibilities

- Store structured verdict information.
- Provide type safety.
- Simplify formatting logic.
- Improve maintainability.

Fields include:

- claim
- verdict
- evidence
- source_url
- correction
- tier_used

Using a dataclass improves readability compared to repeatedly accessing raw dictionaries throughout the formatter.

---

4.2 Verdict Validation

A private parsing function validates every incoming verdict before formatting.

Validation includes:

- Required field checking.
- Missing data detection.
- Supported verdict type validation.
- Conversion into a strongly typed "Verdict" object.

Instead of silently accepting invalid data, descriptive "ValueError" exceptions are raised, making integration issues easier to identify during development.

---

4.3 Individual Verdict Formatting

Dedicated formatting functions were implemented for each supported verdict type.

Verified

Displays:

- Verified status
- Original claim
- Supporting evidence
- Source URL

---

Wrong

Displays:

- Incorrect AI claim
- Correct information
- Supporting source

If no correction is available, the formatter gracefully falls back to available evidence.

---

Unverified

Displays:

- Original claim
- Explanation that no supporting evidence was found
- Recommendation for independent verification

Following project review discussions, hallucinated claims are represented as Unverified because the system cannot conclusively prove hallucination without evidence.

---

4.4 Single Verdict Formatter

A wrapper function processes a single verdict dictionary.

Responsibilities include:

- Parse validation
- Exception handling
- Logging parsing failures
- Delegating formatting to the correct formatter

Malformed inputs do not terminate execution. Instead, a readable parse error is returned.

---

4.5 Complete Report Generator

The formatter also generates an entire verification report.

Features include:

- Report header
- Verification summary
- Ordered verdict sections
- Parse error section
- Footer

Summary statistics include:

- Verified count
- Wrong count
- Unverified count
- Total processed claims

This provides users with both detailed information and a high-level overview.

---

4.6 Report Ordering

Reports are intentionally organized by priority.

Order:

1. Wrong Claims
2. Unverified Claims
3. Verified Claims

This design ensures users see the most critical issues first instead of scanning through verified information.

---

4.7 Logging Integration

Python's built-in logging framework was integrated.

Events logged include:

- Parse failures
- Invalid verdicts
- Empty reports
- Report generation summary

Logging improves debugging without affecting user-facing output.

---

5. Error Handling

The formatter handles multiple failure scenarios.

Examples include:

- Missing claim field
- Missing verdict field
- Unknown verdict types
- Empty verdict list
- Malformed dictionaries

Instead of crashing, the formatter either logs the issue or returns a readable parse error message.

---

6. Design Principles Followed

The implementation follows several software engineering principles.

Separation of Concerns

Formatting remains independent from verification.

---

Single Responsibility Principle

Each helper function performs one clearly defined task.

---

Defensive Programming

Incoming data is validated before processing.

---

Readability

Small helper functions improve maintainability.

---

Extensibility

Additional verdict types or output formats can be added with minimal changes.

---

7. test_formatter.py Contribution

A dedicated automated test suite was implemented to validate formatter behaviour.

The objective was to ensure that formatting remains stable even as other project modules evolve.

---

Test Coverage

The tests cover:

Valid Inputs

- Verified verdict formatting
- Wrong verdict formatting
- Unverified verdict formatting

---

Validation Tests

- Missing required fields
- Invalid verdict values
- Malformed verdict dictionaries

---

Report Generation

Tests verify:

- Summary generation
- Report ordering
- Empty reports
- Parse error reporting

---

Edge Cases

Coverage includes:

- Empty verdict collections
- Missing optional fields
- Default values
- Invalid data handling

---

Testing Strategy

The formatter was tested in isolation.

External components such as:

- Orchestrator
- Search tools
- Local database
- LLM

were intentionally excluded to keep tests deterministic and focused on presentation logic.

---

8. Integration with Other Modules

The formatter is intended to consume structured verdict data produced by the verification layer.

Expected pipeline:

User Prompt
      │
      ▼
Connector
      │
      ▼
Orchestrator
      │
      ▼
Verification Tools
      │
      ▼
Structured Verdicts
      │
      ▼
formatter.py
      │
      ▼
CLI Report

This modular architecture allows future improvements in the verification engine without requiring changes to the reporting layer, provided the verdict interface remains consistent.

---

9. Challenges Addressed

Several design decisions were made during implementation.

- Established a consistent verdict schema for reporting.
- Ensured malformed inputs do not terminate report generation.
- Introduced a typed data model for improved maintainability.
- Organized report output by severity rather than processing order.
- Added comprehensive logging for debugging.
- Maintained a presentation-only architecture with no verification logic.

---

10. Technologies Used

- Python 3.12
- Dataclasses
- Type Hints
- Logging Module
- Pytest
- Object-Oriented Design
- Defensive Validation
- Structured CLI Formatting

---

11. Outcome

The contribution delivers a complete reporting subsystem capable of transforming structured verification results into readable CLI reports while maintaining clear separation from the verification pipeline.

The accompanying automated tests provide confidence that the formatter behaves correctly across expected inputs, malformed data, and edge cases, reducing the risk of regressions during future development.

Overall, this contribution establishes a maintainable, testable, and extensible presentation layer that integrates cleanly with the project's verification architecture.