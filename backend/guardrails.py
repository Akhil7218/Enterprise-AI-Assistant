"""
guardrails.py
=============
Implements two guardrail layers as described in the Review-2 methodology:

  Stage 2 – Input Guardrails
      Screen the incoming query for PII, bias markers, and prompt-injection patterns
      before any retrieval or LLM call takes place.

  Stage 5 – Output Screening
      Scan the generated response for potential data-leakage signals and for
      the model's own "I don't know" refusal so the frontend can display it cleanly.
"""

import re

# ── PII patterns ───────────────────────────────────────────────────────────────
# Detect common PII that should not be sent into the RAG pipeline.
_PII_PATTERNS = [
    (re.compile(r"\b\d{10,12}\b"),                         "phone number"),
    (re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"), "email address"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),                 "SSN"),
    (re.compile(r"\b(?:\d[ -]?){13,16}\b"),                 "credit card number"),
    (re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"),             "PAN number"),   # Indian PAN
    (re.compile(r"\b\d{12}\b"),                             "Aadhaar number"),
]

# ── Prompt-injection patterns ──────────────────────────────────────────────────
_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(previous|all|prior|above)\s+instructions?", re.IGNORECASE),
    re.compile(r"reveal\s+(the\s+)?(system\s+prompt|prompt|instructions?|context)", re.IGNORECASE),
    re.compile(r"act\s+as\s+(an?\s+)?(admin|administrator|root|superuser)", re.IGNORECASE),
    re.compile(r"bypass\s+(the\s+)?(security|access|restriction|filter|guard)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+", re.IGNORECASE),
    re.compile(r"disregard\s+(your\s+)?(previous|prior|all)\s+", re.IGNORECASE),
    re.compile(r"pretend\s+(you\s+are|to\s+be)\s+", re.IGNORECASE),
    re.compile(r"forget\s+(everything|all|your\s+instructions?)", re.IGNORECASE),
    re.compile(r"override\s+(your\s+)?(instructions?|rules?|guidelines?)", re.IGNORECASE),
    re.compile(r"show\s+me\s+(confidential|restricted|private|payroll|salary)", re.IGNORECASE),
    re.compile(r"(jailbreak|jail\s+break)", re.IGNORECASE),
    re.compile(r"</?(system|user|assistant|prompt)>", re.IGNORECASE),   # tag injection
]

# ── Bias / hate markers (basic) ────────────────────────────────────────────────
_BIAS_PATTERNS = [
    re.compile(r"\b(racist|sexist|misogyn|homophob|discriminat)\w*\b", re.IGNORECASE),
]

# ── Output leakage signals ─────────────────────────────────────────────────────
_LEAKAGE_PATTERNS = [
    re.compile(r"system\s+prompt", re.IGNORECASE),
    re.compile(r"confidential\s+instructions?", re.IGNORECASE),
    re.compile(r"salary\s+of\s+\w+\s+is\s+\$?\d+", re.IGNORECASE),
    re.compile(r"password\s*[:=]\s*\S+", re.IGNORECASE),
]


# ── Public API ─────────────────────────────────────────────────────────────────

def check_input(query: str) -> dict:
    """
    Run input guardrail checks on the user query.

    Returns
    -------
    {
        "blocked": bool,
        "reason":  str | None   # human-readable reason if blocked, else None
    }
    """
    # 1. PII detection
    for pattern, label in _PII_PATTERNS:
        if pattern.search(query):
            return {
                "blocked": True,
                "reason": (
                    f"Your query appears to contain a {label}. "
                    "Please remove personal information before submitting."
                ),
            }

    # 2. Prompt-injection detection
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(query):
            return {
                "blocked": True,
                "reason": (
                    "Your query contains patterns associated with prompt-injection attacks "
                    "and cannot be processed."
                ),
            }

    # 3. Bias / hate-speech markers
    for pattern in _BIAS_PATTERNS:
        if pattern.search(query):
            return {
                "blocked": True,
                "reason": (
                    "Your query contains language that violates the acceptable-use policy "
                    "and cannot be processed."
                ),
            }

    return {"blocked": False, "reason": None}


def check_output(response: str) -> dict:
    """
    Run output guardrail checks on the LLM-generated response.

    Returns
    -------
    {
        "blocked": bool,
        "reason":  str | None
    }
    """
    # 1. Leakage signals
    for pattern in _LEAKAGE_PATTERNS:
        if pattern.search(response):
            return {
                "blocked": True,
                "reason": (
                    "The generated response was blocked by the output safety filter "
                    "due to a potential data-leakage signal."
                ),
            }

    return {"blocked": False, "reason": None}
