import re
from typing import Any, Dict

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\b(?:\+\d{1,3}[-.\s]?)?(?:\(\d{2,3}\)|\d{2,3})[-.\s]?\d{3}[-.\s]?\d{4}\b")
CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
ADDRESS_HINT_RE = re.compile(r"\b(\d{1,5}\s+\w+\s+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Lane|Ln|Dr|Drive))\b", re.I)

REDACTED = "[REDACTED]"


def redact_text(text: str) -> str:
    if not text:
        return text
    t = EMAIL_RE.sub(REDACTED, text)
    t = PHONE_RE.sub(REDACTED, t)
    t = CARD_RE.sub(REDACTED, t)
    t = ADDRESS_HINT_RE.sub(REDACTED, t)
    return t


def redact_dict(obj: Dict[str, Any]) -> Dict[str, Any]:
    def _redact(o: Any) -> Any:
        if isinstance(o, str):
            return redact_text(o)
        if isinstance(o, list):
            return [_redact(i) for i in o]
        if isinstance(o, dict):
            return {k: _redact(v) for k, v in o.items()}
        return o

    return _redact(obj)  # type: ignore
