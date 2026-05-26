import re

BANNED_PATTERNS = [
    r'\b(kill\s+yourself|kys)\b',
    r'\b(n[i1]gg[ae3]r)\b',
    r'\b(doxx|doxing)\b',
]

DOXX_PATTERNS = [
    r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',         # phone numbers
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z]{2,}\b',  # emails
    r'\b\d{3}-\d{2}-\d{4}\b',                       # SSN-like
]

SPAM_PATTERNS = [
    r'(https?://\S+\s*){3,}',   # 3+ URLs
]


def contains_banned_content(text: str) -> bool:
    text_lower = text.lower()
    for pattern in BANNED_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    return False


def contains_doxxing(text: str) -> bool:
    for pattern in DOXX_PATTERNS:
        if re.search(pattern, text):
            return True
    return False


def is_spam(text: str) -> bool:
    for pattern in SPAM_PATTERNS:
        if re.search(pattern, text):
            return True
    if len(text) < 3:
        return True
    return False


def sanitize_text(text: str) -> str:
    """Basic XSS protection — strip HTML tags."""
    clean = re.sub(r'<[^>]+>', '', text)
    return clean.strip()


def moderate_content(text: str) -> dict:
    text = sanitize_text(text)
    issues = []
    if contains_banned_content(text):
        issues.append("banned_content")
    if contains_doxxing(text):
        issues.append("doxxing")
    if is_spam(text):
        issues.append("spam")
    return {
        "clean_text": text,
        "issues": issues,
        "allowed": len(issues) == 0
    }
