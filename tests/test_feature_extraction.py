from ekb_reliability.features import extract_features


def test_extract_cap_features():
    feat = extract_features("CAP CER 0603 16V 10uF X6S +/-20%")
    assert abs(feat["capacitance_f"] - 10e-6) < 1e-12
    assert feat["rated_voltage_v"] == 16.0
    assert feat["tolerance_pct"] == 20.0


def test_extract_resistor_features():
    feat = extract_features("RESISTOR 10kohm 0.125W +/-1% 0603")
    assert feat["resistance_ohm"] == 10000.0
    assert feat["power_w"] == 0.125
