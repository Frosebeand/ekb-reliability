from ekb_reliability.normalization import normalize_text, normalize_mpn


def test_normalize_text():
    text = "CAP CER 0603 16V 10µF X6S В±20%"
    out = normalize_text(text)
    assert "uf" in out
    assert "+/-20%" in out


def test_normalize_mpn():
    assert normalize_mpn(" abm8w-12.0000mhz-8-d1x-t3 ") == "ABM8W-12.0000MHZ-8-D1X-T3"
