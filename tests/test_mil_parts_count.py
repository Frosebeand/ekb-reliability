from ekb_reliability.reliability.mil_parts_count import calculate_mil_parts_count, select_mil_parts_count_row


def test_select_resistor_chip_row():
    row = select_mil_parts_count_row(
        family="resistor",
        subfamily="fixed_resistor",
        features={"package": "0402", "resistance_ohm": 1000.0},
    )
    assert row == "resistor_film_chip"


def test_mil_parts_count_resistor_chip_gf_lower():
    result = calculate_mil_parts_count(
        family="resistor",
        subfamily="fixed_resistor",
        features={"package": "0402", "resistance_ohm": 1000.0},
        qty=10,
        quality="commercial",
        environment="ground_fixed",
    )
    assert result is not None
    # λg=0.016, πQ(lower)=10 => unit FIT = 0.16
    assert round(result.unit_lambda_value * 1e9, 6) == 0.16
    assert round(result.fit, 6) == 1.6
    assert result.assumptions["mil_row_key"] == "resistor_film_chip"
    assert result.assumptions["mil_environment_code"] == "GF"


def test_mil_parts_count_quartz_crystal():
    result = calculate_mil_parts_count(
        family="crystal",
        subfamily="quartz_crystal",
        features={"frequency_hz": 12_000_000},
        qty=1,
        quality="commercial",
        environment="ground_fixed",
    )
    assert result is not None
    # λg=0.096, πQ(lower)=2.1 => unit FIT = 0.2016
    assert round(result.unit_lambda_value * 1e9, 6) == 0.2016
    assert result.assumptions["mil_row_key"] == "quartz_crystal"


def test_microcontroller_parts_count_requires_explicit_mil_quality():
    from ekb_reliability.reliability.mil_parts_count import calculate_mil_parts_count
    result = calculate_mil_parts_count(
        family="integrated_circuit",
        subfamily="microcontroller",
        features={"bit_width": 32, "source_text": "32-bit microcontroller 64-LQFP"},
        qty=1,
        quality="commercial",
        environment="ground_fixed",
    )
    assert result is None


def test_microcontroller_parts_count_military_uses_mil_subset():
    from ekb_reliability.reliability.mil_parts_count import calculate_mil_parts_count
    result = calculate_mil_parts_count(
        family="integrated_circuit",
        subfamily="microcontroller",
        features={"bit_width": 32, "source_text": "32-bit microcontroller 64-LQFP"},
        qty=1,
        quality="military",
        environment="ground_fixed",
    )
    assert result is not None
    assert result.assumptions["reference_method"] == "MIL-HDBK-217F Appendix A (validated subset)"
    assert result.assumptions["mil_row_key"] == "microprocessor_mos_32bit"


def test_memory_ic_parts_count_military_uses_eeprom_row():
    from ekb_reliability.reliability.mil_parts_count import calculate_mil_parts_count
    result = calculate_mil_parts_count(
        family="integrated_circuit",
        subfamily="memory_ic",
        features={"memory_size_bits": 256000, "source_text": "256Kbit I2C EEPROM"},
        qty=1,
        quality="military",
        environment="ground_fixed",
    )
    assert result is not None
    assert result.assumptions["mil_row_key"] == "memory_mos_eeprom_256k"
