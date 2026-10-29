"""Article-level cleaning and train/validation split.

Reads the raw Hebrew Wikipedia parquet file, cleans every article,
and writes data/processed/train.txt and data/processed/val.txt.

Usage (from the project root):
    python -m src.data.prepare                  # full dataset
    python -m src.data.prepare --sample 1000    # quick test run
"""

import argparse
import hashlib
import os
import random
import re

import pyarrow.parquet as pq
from tqdm import tqdm

from src.data.normalize import normalize, collapse_whitespace

# ---------- settings ----------

RAW_PATH = os.path.join("data", "raw", "hewiki.parquet")
OUT_DIR = os.path.join("data", "processed")

VAL_FRACTION = 0.05        # 5% of articles go to validation
SEED = 42                  # makes the split reproducible
MIN_ARTICLE_CHARS = 200    # shorter articles are dropped (from the length plot)
MIN_HEBREW_RATIO = 0.5     # lines with fewer Hebrew letters than this are dropped

# Articles are separated by two blank lines. normalize() guarantees at most
# one blank line inside an article, so this separator is never ambiguous.
ARTICLE_SEPARATOR = "\n\n\n"

# Section headers that start the junk at the end of an article.
TRAILING_SECTIONS = ["ראו גם", "הערות שוליים", "קישורים חיצוניים", "לקריאה נוספת"]

# Matches a line that contains ONLY one of the headers (plus optional spaces).
# [ \t]* is used instead of \s* because \s also matches newlines, which would
# make the match start on an earlier empty line.
# ^ and $ with re.MULTILINE mean start and end of a line, not of the whole text.
TRAILING_PATTERN = re.compile(
    r"^[ \t]*(" + "|".join(TRAILING_SECTIONS) + r")[ \t]*$",
    re.MULTILINE,
)


# Used by is_mostly_hebrew to count letters quickly.
HEBREW_LETTER_PATTERN = re.compile(r"[א-ת]")   # א to ת
LATIN_LETTER_PATTERN = re.compile(r"[a-zA-Z]")


# ---------- cleaning steps ----------

def cut_trailing_sections(text: str) -> str:
    """Cut the article at the first line that is exactly a trailing header."""
    match = TRAILING_PATTERN.search(text)
    if match:
        return text[: match.start()]
    return text


def is_mostly_hebrew(line: str) -> bool:
    """True if at least MIN_HEBREW_RATIO of the line's letters are Hebrew.

    Runs after normalize(), so the only letters left are Hebrew and Latin.
    """
    # Fast path: most lines have no English at all, so no counting is needed.
    if not LATIN_LETTER_PATTERN.search(line):
        return HEBREW_LETTER_PATTERN.search(line) is not None
    hebrew = len(HEBREW_LETTER_PATTERN.findall(line))
    latin = len(LATIN_LETTER_PATTERN.findall(line))
    return hebrew / (hebrew + latin) >= MIN_HEBREW_RATIO


def remove_non_hebrew_lines(text: str) -> str:
    """Drop lines that are mostly non-Hebrew; keep blank lines between paragraphs."""
    kept = [line for line in text.split("\n") if line == "" or is_mostly_hebrew(line)]
    return "\n".join(kept)


def clean_article(text: str) -> str:
    """Full cleaning for one article. Returns "" if the article should be dropped."""
    text = cut_trailing_sections(text)
    text = normalize(text)
    text = remove_non_hebrew_lines(text)
    text = collapse_whitespace(text)   # tidy up blank lines left by removed lines
    if len(text) < MIN_ARTICLE_CHARS:
        return ""
    return text


# ---------- main pipeline ----------

def main(sample=None):
    os.makedirs(OUT_DIR, exist_ok=True)
    rng = random.Random(SEED)
    seen_hashes = set()

    stats = {"total": 0, "too_short": 0, "duplicates": 0,
             "train_articles": 0, "val_articles": 0,
             "train_chars": 0, "val_chars": 0}

    parquet_file = pq.ParquetFile(RAW_PATH)
    total_rows = parquet_file.metadata.num_rows if sample is None else sample

    train_path = os.path.join(OUT_DIR, "train.txt")
    val_path = os.path.join(OUT_DIR, "val.txt")

    with open(train_path, "w", encoding="utf-8") as train_f, \
         open(val_path, "w", encoding="utf-8") as val_f, \
         tqdm(total=total_rows, desc="Cleaning articles") as progress:

        # Read the file in batches so the whole dataset never sits in memory.
        for batch in parquet_file.iter_batches(batch_size=1000, columns=["text"]):
            for raw_text in batch.column("text").to_pylist():
                if sample is not None and stats["total"] >= sample:
                    break
                stats["total"] += 1
                progress.update(1)

                text = clean_article(raw_text)
                if not text:
                    stats["too_short"] += 1
                    continue

                # Exact-duplicate check using a short fingerprint of the text.
                fingerprint = hashlib.md5(text.encode("utf-8")).hexdigest()
                if fingerprint in seen_hashes:
                    stats["duplicates"] += 1
                    continue
                seen_hashes.add(fingerprint)

                # Split by article, never by line, so no article leaks into both sets.
                if rng.random() < VAL_FRACTION:
                    val_f.write(text + ARTICLE_SEPARATOR)
                    stats["val_articles"] += 1
                    stats["val_chars"] += len(text)
                else:
                    train_f.write(text + ARTICLE_SEPARATOR)
                    stats["train_articles"] += 1
                    stats["train_chars"] += len(text)

            if sample is not None and stats["total"] >= sample:
                break

    print("\n--- Summary ---")
    print(f"Articles read:      {stats['total']:,}")
    print(f"Dropped (short):    {stats['too_short']:,}")
    print(f"Dropped (dupes):    {stats['duplicates']:,}")
    print(f"Train: {stats['train_articles']:,} articles, {stats['train_chars']:,} chars")
    print(f"Val:   {stats['val_articles']:,} articles, {stats['val_chars']:,} chars")
    print(f"Saved to {train_path} and {val_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean Hebrew Wikipedia and split it.")
    parser.add_argument("--sample", type=int, default=None,
                        help="process only the first N articles (for quick tests)")
    args = parser.parse_args()
    main(sample=args.sample)