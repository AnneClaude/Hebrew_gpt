from src.data.prepare import (
    clean_article,
    cut_trailing_sections,
    is_mostly_hebrew,
    remove_non_hebrew_lines,
)

LONG_PARAGRAPH = "זהו משפט ארוך בעברית שמופיע בערך כדי שהוא יעבור את סף האורך המינימלי. " * 5


def test_cuts_at_trailing_header():
    text = "תוכן אמיתי.\n\nקישורים חיצוניים\n\nקטגוריה א\nקטגוריה ב"
    assert cut_trailing_sections(text) == "תוכן אמיתי.\n\n"


def test_cuts_at_first_of_several_headers():
    text = "תוכן.\n\nראו גם\n\nמשהו\n\nהערות שוליים\n\nעוד"
    assert cut_trailing_sections(text) == "תוכן.\n\n"


def test_header_inside_sentence_is_not_cut():
    text = "בסוף הערך יש קישורים חיצוניים רבים."
    assert cut_trailing_sections(text) == text


def test_header_with_trailing_space_is_cut():
    text = "תוכן.\n\nהערות שוליים \n\nעוד"
    assert cut_trailing_sections(text) == "תוכן.\n\n"


def test_mostly_hebrew():
    assert is_mostly_hebrew("שלום עולם")
    assert is_mostly_hebrew("הוא כתב בשפת Python")
    assert not is_mostly_hebrew("The quick brown fox")
    assert not is_mostly_hebrew("1939 - 1945")


def test_remove_non_hebrew_lines_keeps_blank_lines():
    text = "שורה בעברית\n\nEnglish only line\nעוד שורה"
    assert remove_non_hebrew_lines(text) == "שורה בעברית\n\nעוד שורה"


def test_short_article_is_dropped():
    assert clean_article("קצר מדי.") == ""


def test_long_article_is_kept_and_cleaned():
    raw = LONG_PARAGRAPH + "\n\nקישורים חיצוניים\n\nקטגוריה"
    cleaned = clean_article(raw)
    assert cleaned != ""
    assert "קישורים חיצוניים" not in cleaned
    assert "קטגוריה" not in cleaned
