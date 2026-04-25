from ekb_reliability.rules import classify_by_rules


def test_cap_rule():
    res = classify_by_rules("CAP CER 0603 16V 10uF X6S +/-20%")
    assert res.family == "capacitor"


def test_crystal_rule():
    res = classify_by_rules("CRYSTAL 25.0000MHZ 12PF")
    assert res.family == "crystal"


def test_connector_rule():
    res = classify_by_rules("USB 2.0 PORT & DUAL UART PORTS 64-TQFP")
    assert res.family == "integrated_circuit"
