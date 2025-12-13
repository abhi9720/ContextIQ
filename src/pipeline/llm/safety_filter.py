
import re
from typing import Literal

class PotentiallyUnsafeContentError(Exception):
    """Custom exception for content that fails the safety filter."""
    pass

# In a real-world application, these patterns would be more comprehensive and
# likely loaded from a configuration file or a dedicated service.
PATTERNS = {
    "EMAIL": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
    "PHONE_NUMBER": r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
    # Using \b for word boundaries to prevent matching substrings within words.
    "GENERIC_PROFANITY": r"\b(bad_word_1|very_bad_word_2)\b",
}

REDACTION_PLACEHOLDER = "[REDACTED]"

def filter_safety(
    text: str, 
    method: Literal['raise', 'redact'] = 'raise'
) -> str:
    """
    Scans and sanitizes text for sensitive information or denylisted content.

    This function uses a predefined set of regular expressions to find and
    handle PII (Personally Identifiable Information) and profane language.

    Args:
        text: The input text to scan.
        method: The action to take when unsafe content is found.
                'raise': Throws a PotentiallyUnsafeContentError (default).
                'redact': Replaces the found content with a placeholder.

    Returns:
        The sanitized text if the method is 'redact', or the original text
        if no unsafe content is found.

    Raises:
        PotentiallyUnsafeContentError: If the method is 'raise' and unsafe
                                     content is detected.
    """
    if method == 'raise':
        for pattern_name, regex in PATTERNS.items():
            if re.search(regex, text, re.IGNORECASE):
                raise PotentiallyUnsafeContentError(
                    f"Input text contains potentially unsafe content matching rule: '{pattern_name}'"
                )
        return text
    elif method == 'redact':
        sanitized_text = text
        for regex in PATTERNS.values():
            sanitized_text = re.sub(regex, REDACTION_PLACEHOLDER, sanitized_text, flags=re.IGNORECASE)
        return sanitized_text
    else:
        raise ValueError("Invalid filter method specified. Choose 'raise' or 'redact'.")
