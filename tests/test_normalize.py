from src.data.normalize import normalize


def test_strips_niqqud():
    assert normalize("שָׁלוֹם") == "שלום"


def test_niqqud_on_first_word():
    # the pattern found in the data: niqqud only on the title word
    assert normalize("מָתֵמָטִיקָה היא תחום") == "מתמטיקה היא תחום"


def test_gershayim_becomes_quote():
    assert normalize("צה״ל") == 'צה"ל'


def test_geresh_becomes_apostrophe():
    assert normalize("ג׳ירפה") == "ג'ירפה"


def test_maqaf_becomes_hyphen():
    assert normalize("בית־ספר") == "בית-ספר"


def test_curly_quotes():
    assert normalize("“שלום”") == '"שלום"'


def test_dashes_unified():
    assert normalize("1939–1945") == "1939-1945"


def test_removes_right_to_left_mark():
    assert normalize("שלום‏ עולם") == "שלום עולם"


def test_removes_foreign_scripts():
    assert normalize("טוקיו 東京") == "טוקיו"


def test_keeps_english_and_digits():
    assert normalize("Python 3.13") == "Python 3.13"


def test_collapses_spaces():
    assert normalize("מול  הספרדית") == "מול הספרדית"


def test_non_breaking_space():
    assert normalize("שלום עולם") == "שלום עולם"


def test_collapses_blank_lines():
    assert normalize("פסקה א\n\n\n\n\nפסקה ב") == "פסקה א\n\nפסקה ב"


def test_strips_spaces_at_line_edges():
    assert normalize("  שורה  \n  שורה  ") == "שורה\nשורה"


def test_empty_string():
    assert normalize("") == ""
