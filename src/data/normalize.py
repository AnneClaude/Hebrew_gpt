"""Character-level normalization for Hebrew text.

Every rule here comes from the findings in notebooks/01_explore.ipynb.
"""

import re
import sys
import unicodedata

# ---------- constants ----------

# Niqqud and cantillation marks (U+0591 to U+05C7).
# Note: the maqaf (U+05BE) is inside this range, so it is replaced
# with a regular hyphen before this pattern is applied.
NIQQUD_PATTERN = re.compile("[\u0591-\u05C7]")
MAQAF = "\u05BE"

# Quote and dash variants, each mapped to one plain form.
PUNCTUATION_MAP = {
    "\u05F4": '"',   # Hebrew gershayim
    "\u05F3": "'",   # Hebrew geresh
    "\u201C": '"',   # left double quote
    "\u201D": '"',   # right double quote
    "\u201E": '"',   # low double quote
    "\u2018": "'",   # left single quote
    "\u2019": "'",   # right single quote
    "\u2013": "-",   # en dash
    "\u2014": "-",   # em dash
    "\u2010": "-",   # hyphen
    "\u2212": "-",   # minus sign
    "\t": " ",       # tab
}

# Characters the model is allowed to see. Everything else is removed.
HEBREW_LETTERS = {chr(c) for c in range(0x05D0, 0x05EA + 1)}   # alef to tav, incl. final forms
LATIN_LETTERS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
DIGITS = set("0123456789")
PUNCTUATION = set(".,:;!?\"'()-/%&+=[]")
WHITESPACE = {" ", "\n"}

ALLOWED_CHARS = HEBREW_LETTERS | LATIN_LETTERS | DIGITS | PUNCTUATION | WHITESPACE


# ---------- precompiled regexes (for speed) ----------
# This code runs over ~1 billion characters. A Python loop that checks every
# character one by one is slow; a regex does the same work in C, much faster.

def _format_char_class() -> str:
    """Build a regex character class of every format character (category Cf).

    Consecutive code points are written as ranges (e.g. U+200B to U+200F),
    which keeps the regex small and fast.
    """
    codes = [c for c in range(sys.maxunicode + 1) if unicodedata.category(chr(c)) == "Cf"]
    parts = []
    start = prev = codes[0]
    for c in codes[1:] + [None]:
        if c is not None and c == prev + 1:
            prev = c
            continue
        if start == prev:
            parts.append(re.escape(chr(start)))
        else:
            parts.append(re.escape(chr(start)) + "-" + re.escape(chr(prev)))
        if c is not None:
            start = prev = c
    return "[" + "".join(parts) + "]"


# Invisible format characters: right-to-left marks, zero-width joiners, etc.
FORMAT_CHARS_PATTERN = re.compile(_format_char_class())

# Any of the quote/dash variants from PUNCTUATION_MAP.
PUNCTUATION_PATTERN = re.compile("[" + "".join(PUNCTUATION_MAP) + "]")

# Any character that is NOT allowed ([^...] means "not one of these").
DISALLOWED_PATTERN = re.compile(
    "[^" + "".join(re.escape(ch) for ch in sorted(ALLOWED_CHARS)) + "]"
)


# ---------- steps ----------

def unicode_normalize(text: str) -> str:
    """Turn compatibility forms into regular ones (NFKC).

    For example: non-breaking space -> space, the 'fi' ligature -> 'fi',
    and Hebrew presentation forms -> letter + marks (the marks are stripped next).
    """
    return unicodedata.normalize("NFKC", text)


def strip_niqqud(text: str) -> str:
    """Remove niqqud and cantillation marks, keeping the maqaf as '-'."""
    text = text.replace(MAQAF, "-")
    return NIQQUD_PATTERN.sub("", text)


def remove_format_chars(text: str) -> str:
    """Remove invisible format characters (Unicode category Cf)."""
    return FORMAT_CHARS_PATTERN.sub("", text)


def unify_punctuation(text: str) -> str:
    """Map quote and dash variants to one plain form each."""
    return PUNCTUATION_PATTERN.sub(lambda m: PUNCTUATION_MAP[m.group()], text)


def filter_allowed_chars(text: str) -> str:
    """Remove every character that is not in ALLOWED_CHARS."""
    return DISALLOWED_PATTERN.sub("", text)


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
    - punctuation is unified before filtering, so gershayim becomes " instead
      of being deleted
    - whitespace last, because earlier steps leave gaps behind
    """
    text = unicode_normalize(text)
    text = strip_niqqud(text)
    text = remove_format_chars(text)
    text = unify_punctuation(text)
    text = filter_allowed_chars(text)
    text = collapse_whitespace(text)
    return text