from ekb_reliability.reliability.engine import ReliabilityEngine


def test_reliability_resistor():
    engine = ReliabilityEngine()
    res = engine.evaluate(
        family="resistor",
        subfamily="fixed_resistor",
        features={"resistance_ohm": 10000.0, "power_ratio": 0.5},
        qty=10,
        identification_confidence=0.95,
    )
    assert res.lambda_value > 0
    assert res.fit > 0
    assert res.selected_method in {"part_stress", "parts_count"}
