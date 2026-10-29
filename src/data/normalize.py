"""Character-level normalization for Hebrew text.

Every rule here comes from the findings in notebooks/01_explore.ipynb.
"""

import re
import unicodedata

# ---------- constants ----------

# Niqqud and cantillation marks (U+0591 to U+05C7).
# Note: the maqaf (U+05BE) is inside this range, so it is replaced
# with a regular hyphen before this pattern is applied.
NIQQUD_PATTERN = re.compile(r"[֑-ׇ]")
MAQAF = "־"

# Quote and dash variants, each mapped to one plain form.
PUNCTUATION_MAP = str.maketrans({
    "״": '"',   # ״ Hebrew gershayim
    "׳": "'",   # ׳ Hebrew geresh
    "“": '"',   # “ left double quote
    "”": '"',   # ” right double quote
    "„": '"',   # „ low double quote
    "‘": "'",   # ‘ left single quote
    "’": "'",   # ’ right single quote
    "–": "-",   # – en dash
    "—": "-",   # — em dash
    "‐": "-",   # ‐ hyphen
    "−": "-",   # − minus sign
    "\t": " ",       # tab
})

# Characters the model is allowed to see. Everything else is removed.
HEBREW_LETTERS = {chr(c) for c in range(0x05D0, 0x05EA + 1)}   # א to ת, incl. final forms
LATIN_LETTERS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
DIGITS = set("0123456789")
PUNCTUATION = set(".,:;!?\"'()-/%&+=[]")
WHITESPACE = {" ", "\n"}

ALLOWED_CHARS = HEBREW_LETTERS | LATIN_LETTERS | DIGITS | PUNCTUATION | WHITESPACE


# ---------- steps ----------

def unicode_normalize(text: str) -> str:
    """Turn compatibility forms into regular ones (NFKC).

    For example: non-breaking space -> space, 'ﬁ' -> 'fi', and Hebrew
    presentation forms -> letter + marks (the marks are stripped next).
    """
    return unicodedata.normalize("NFKC", text)


def strip_niqqud(text: str) -> str:
    """Remove niqqud and cantillation marks, keeping the maqaf as '-'."""
    text = text.replace(MAQAF, "-")
    return NIQQUD_PATTERN.sub("", text)


def remove_format_chars(text: str) -> str:
    """Remove invisible format characters (Unicode category Cf),
    such as right-to-left marks and zero-width joiners."""
    return "".join(ch for ch in text if unicodedata.category(ch) != "Cf")


def unify_punctuation(text: str) -> str:
    """Map quote and dash variants to one plain form each."""
    return text.translate(PUNCTUATION_MAP)


def filter_allowed_chars(text: str) -> str:
    """Remove every character that is not in ALLOWED_CHARS."""
    return "".join(ch for ch in text if ch in ALLOWED_CHARS)


def collapse_whitespace(text: str) -> str:
    """Clean up spaces and blank lines left over by the earlier steps."""
    text = re.sub(r" {2,}", " ", text)       # many spaces -> one
    text = re.sub(r" *\n *", "\n", text)     # no spaces at line edges
    text = re.sub(r"\n{3,}", "\n\n", text)   # at most one blank line
    return text.strip()


# ---------- main entry point ----------

def normalize(text: str) -> str:
    """Apply all normalization steps in the correct order.

    The order matters:
    - NFKC first, because it can produce niqqud from presentation forms
    - maqaf is handled inside strip_niqqud, before the range is removed
    - punctuation is unified before filtering, so ״ becomes " instead of
      being deleted
    - whitespace last, because earlier steps leave gaps behind
    """
    text = unicode_normalize(text)
    text = strip_niqqud(text)
    text = remove_format_chars(text)
    text = unify_punctuation(text)
    text = filter_allowed_chars(text)
    text = collapse_whitespace(text)
    return text