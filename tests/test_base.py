from SSSS.base import clean_title, normalize_citations, normalize_year


def test_normalize_year_from_text():
    assert normalize_year("Published in 2024") == 2024


def test_normalize_citations_from_text():
    assert normalize_citations("Cited by 37") == 37


def test_clean_title_removes_unsupported_characters():
    assert clean_title("A title — with noise") == "A title with noise"
