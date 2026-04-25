from __future__ import annotations

# Exact or directly transcribed Appendix A values from MIL-HDBK-217F Notice 2
# for a limited, explicitly scoped subset used by this project.
# Values are generic failure rates λg in failures / 1e6 hours.
# Only rows that were manually verified from the supplied handbook pages are included.

MIL_ENV_CODES = ["GB", "GF", "GM", "NS", "NU", "AIC", "AIF", "AUC", "AUF", "ARW", "SF", "MF", "ML", "CL"]

ENV_ALIAS_TO_CODE = {
    # internal project aliases
    "ground_benign": "GB",
    "ground_fixed": "GF",
    "ground_mobile": "GM",
    "naval_sheltered": "NS",
    "naval_unsheltered": "NU",
    "airborne_inhabited_cargo": "AIC",
    "airborne_inhabited_fighter": "AIF",
    "airborne_uninhabited_cargo": "AUC",
    "airborne_uninhabited_fighter": "AUF",
    "airborne_rotary_wing": "ARW",
    "space": "SF",
    "missile_flight": "MF",
    "missile_launch": "ML",
    "cannon_launch": "CL",
    # direct MIL symbols are also accepted
    "GB": "GB",
    "GF": "GF",
    "GM": "GM",
    "NS": "NS",
    "NU": "NU",
    "AIC": "AIC",
    "AIF": "AIF",
    "AUC": "AUC",
    "AUF": "AUF",
    "ARW": "ARW",
    "SF": "SF",
    "MF": "MF",
    "ML": "ML",
    "CL": "CL",
}

# For project-level quality aliases we intentionally use conservative mappings.
# "industrial" is treated as Lower because MIL Appendix A does not define an industrial class.
GENERIC_QUALITY_ALIAS = {
    "military": "mil_spec",
    "industrial": "lower",
    "commercial": "lower",
    "unknown": "lower",
    "mil_spec": "mil_spec",
    "lower": "lower",
}

SEMICONDUCTOR_QUALITY_ALIAS = {
    "military": "jan",
    "industrial": "lower",
    "commercial": "plastic",
    "unknown": "plastic",
    "jan": "jan",
    "jantx": "jantx",
    "jantxv": "jantxv",
    "lower": "lower",
    "plastic": "plastic",
}

# πQ factors
QUALITY_FACTORS = {
    "resistor": {
        # Appendix A resistor table shows Established Reliability styles (S/R/P/M) and then MIL-SPEC/Lower.
        # For this project subset we only map high-level aliases to MIL-SPEC and Lower, which are directly shown.
        "mil_spec": 3.0,
        "lower": 10.0,
    },
    "capacitor": {
        # Appendix A capacitor table shows MIL-SPEC and Lower columns in addition to ER classes.
        "mil_spec": 3.0,
        "lower": 10.0,
    },
    "semiconductor_non_rf": {"jantxv": 0.70, "jantx": 1.0, "jan": 2.4, "lower": 5.5, "plastic": 8.0},
    "semiconductor_high_freq_diode": {"jantxv": 0.50, "jantx": 1.0, "jan": 5.0, "lower": 25.0, "plastic": 50.0},
    "semiconductor_schottky": {"jantxv": 0.50, "jantx": 1.0, "jan": 1.8, "lower": 2.5},
    "semiconductor_rf_transistor": {"jantxv": 0.50, "jantx": 1.0, "jan": 2.0, "lower": 5.0},
    "connector": {"mil_spec": 1.0, "lower": 2.0},
    "socket": {"mil_spec": 0.3, "lower": 1.0},
    "quartz_crystal": {"mil_spec": 1.0, "lower": 2.1},
    "inductive_device": {"established_reliability": 0.25, "mil_spec": 1.0, "lower": 3.0},
    "relay_mechanical": {"established_reliability": 0.60, "mil_spec": 1.5, "lower": 2.9},
    "relay_solid_state": {"mil_spec": 1.0, "lower": 1.9},
    "fuse": {},  # πQ not shown/applicable in A-11 table
    # Microcircuits, section 5.10 page 5-15: directly visible/verified categories only.
    "microcircuit": {"mil_spec": 1.0, "b1": 2.0},
}

# λg tables (failures / 1e6 hours)
MIL_PARTS_COUNT_ROWS = {
    "resistor_film_chip": {
        "mil_ref": "Appendix A, Section 9.1, Part Type 'Film, Chip' (style RN)",
        "quality_group": "resistor",
        "lambda_g": {"GB": 0.0037, "GF": 0.016, "GM": 0.070, "NS": 0.050, "NU": 0.180, "AIC": 0.080, "AIF": 0.110, "AUC": 0.160, "AUF": 0.220, "ARW": 0.290, "SF": 0.0018, "MF": 0.160, "ML": 0.400, "CL": 7.0},
    },
    "resistor_film_general": {
        "mil_ref": "Appendix A, Section 9.1, Part Type 'Film, Insulated' (style RL)",
        "quality_group": "resistor",
        "lambda_g": {"GB": 0.0037, "GF": 0.016, "GM": 0.070, "NS": 0.050, "NU": 0.180, "AIC": 0.080, "AIF": 0.110, "AUC": 0.160, "AUF": 0.220, "ARW": 0.290, "SF": 0.0018, "MF": 0.160, "ML": 0.400, "CL": 7.0},
    },
    "resistor_thermistor": {
        "mil_ref": "Appendix A, Section 9.1, Part Type 'Thermistor' (style RTH)",
        "quality_group": "resistor",
        "lambda_g": {"GB": 0.0014, "GF": 0.0058, "GM": 0.023, "NS": 0.017, "NU": 0.061, "AIC": 0.026, "AIF": 0.033, "AUC": 0.045, "AUF": 0.062, "ARW": 0.091, "SF": 0.0007, "MF": 0.054, "ML": 0.130, "CL": 2.5},
    },
    "capacitor_ceramic_chip": {
        "mil_ref": "Appendix A, Section 10.1, Part Type 'Ceramic, Chip' (style CDR)",
        "quality_group": "capacitor",
        "lambda_g": {"GB": 0.0035, "GF": 0.053, "GM": 0.130, "NS": 0.037, "NU": 0.098, "AIC": 0.120, "AIF": 0.140, "AUC": 0.410, "AUF": 0.490, "ARW": 0.380, "SF": 0.0017, "MF": 0.130, "ML": 0.480, "CL": 3.0},
    },
    "capacitor_ceramic_general": {
        "mil_ref": "Appendix A, Section 10.1, Part Type 'Ceramic (General Purpose)' (style CK)",
        "quality_group": "capacitor",
        "lambda_g": {"GB": 0.0017, "GF": 0.026, "GM": 0.064, "NS": 0.018, "NU": 0.048, "AIC": 0.057, "AIF": 0.071, "AUC": 0.200, "AUF": 0.240, "ARW": 0.190, "SF": 0.00086, "MF": 0.064, "ML": 0.240, "CL": 1.5},
    },
    "capacitor_tantalum_chip": {
        "mil_ref": "Appendix A, Section 10.1, Part Type 'Tantalum, Chip' (style CLR)",
        "quality_group": "capacitor",
        "lambda_g": {"GB": 0.0022, "GF": 0.026, "GM": 0.057, "NS": 0.018, "NU": 0.042, "AIC": 0.040, "AIF": 0.050, "AUC": 0.110, "AUF": 0.130, "ARW": 0.130, "SF": 0.0011, "MF": 0.057, "ML": 0.170, "CL": 1.5},
    },
    "capacitor_aluminum_dry": {
        "mil_ref": "Appendix A, Section 10.1, Part Type 'Aluminum Dry' (style CE)",
        "quality_group": "capacitor",
        "lambda_g": {"GB": 0.0013, "GF": 0.019, "GM": 0.047, "NS": 0.014, "NU": 0.036, "AIC": 0.042, "AIF": 0.052, "AUC": 0.150, "AUF": 0.180, "ARW": 0.140, "SF": 0.00063, "MF": 0.047, "ML": 0.170, "CL": 1.1},
    },
    "capacitor_film": {
        "mil_ref": "Appendix A, Section 10.1, Part Type 'Metallized Plastic' (style CH)",
        "quality_group": "capacitor",
        "lambda_g": {"GB": 0.00051, "GF": 0.0061, "GM": 0.013, "NS": 0.0043, "NU": 0.010, "AIC": 0.0095, "AIF": 0.012, "AUC": 0.025, "AUF": 0.030, "ARW": 0.032, "SF": 0.00025, "MF": 0.013, "ML": 0.039, "CL": 0.35},
    },
    "capacitor_mica": {
        "mil_ref": "Appendix A, Section 10.1, Part Type 'MICA (Dipped or Molded)' (style CM)",
        "quality_group": "capacitor",
        "lambda_g": {"GB": 0.00057, "GF": 0.0088, "GM": 0.022, "NS": 0.0062, "NU": 0.016, "AIC": 0.019, "AIF": 0.024, "AUC": 0.069, "AUF": 0.082, "ARW": 0.064, "SF": 0.0029, "MF": 0.022, "ML": 0.080, "CL": 0.50},
    },
    "diode_signal": {
        "mil_ref": "Appendix A, Section 6.1, Part Type 'Switching'",
        "quality_group": "semiconductor_non_rf",
        "lambda_g": {"GB": 0.00094, "GF": 0.0075, "GM": 0.013, "NS": 0.011, "NU": 0.027, "AIC": 0.024, "AIF": 0.054, "AUC": 0.054, "AUF": 0.120, "ARW": 0.120, "SF": 0.00047, "MF": 0.020, "ML": 0.060, "CL": 4.0},
    },
    "diode_schottky": {
        "mil_ref": "Appendix A, Section 6.1, Part Type 'Power Rectifier, Schottky Pwr.'",
        "quality_group": "semiconductor_non_rf",
        "lambda_g": {"GB": 0.0028, "GF": 0.022, "GM": 0.038, "NS": 0.034, "NU": 0.082, "AIC": 0.073, "AIF": 0.160, "AUC": 0.160, "AUF": 0.350, "ARW": 0.130, "SF": 0.0014, "MF": 0.060, "ML": 0.180, "CL": 1.2},
    },
    "diode_tvs": {
        "mil_ref": "Appendix A, Section 6.1, Part Type 'Transient Suppressor/Varistor'",
        "quality_group": "semiconductor_non_rf",
        "lambda_g": {"GB": 0.0029, "GF": 0.023, "GM": 0.040, "NS": 0.035, "NU": 0.084, "AIC": 0.075, "AIF": 0.170, "AUC": 0.170, "AUF": 0.360, "ARW": 0.140, "SF": 0.0015, "MF": 0.062, "ML": 0.180, "CL": 1.2},
    },
    "diode_zener": {
        "mil_ref": "Appendix A, Section 6.1, Part Type 'Voltage Ref/Reg., Avalanche and Zener'",
        "quality_group": "semiconductor_non_rf",
        "lambda_g": {"GB": 0.0033, "GF": 0.024, "GM": 0.039, "NS": 0.035, "NU": 0.082, "AIC": 0.066, "AIF": 0.150, "AUC": 0.130, "AUF": 0.270, "ARW": 0.120, "SF": 0.0016, "MF": 0.060, "ML": 0.160, "CL": 1.3},
    },
    "transistor_bjt_low_freq": {
        "mil_ref": "Appendix A, Section 6.3, Part Type 'NPN/PNP (f < 200 MHz)'",
        "quality_group": "semiconductor_non_rf",
        "lambda_g": {"GB": 0.0015, "GF": 0.0017, "GM": 0.0017, "NS": 0.0017, "NU": 0.0037, "AIC": 0.0030, "AIF": 0.0067, "AUC": 0.0080, "AUF": 0.013, "ARW": 0.0056, "SF": 0.000073, "MF": 0.0027, "ML": 0.0074, "CL": 0.056},
    },
    "inductor_fixed": {
        "mil_ref": "Appendix A, Section 11.2, Part Type 'Coil, Fixed Inductor or Choke'",
        "quality_group": "inductive_device",
        "lambda_g": {"GB": 0.00032, "GF": 0.0022, "GM": 0.00047, "NS": 0.00018, "NU": 0.00063, "AIC": 0.0027, "AIF": 0.0036, "AUC": 0.0037, "AUF": 0.00047, "ARW": 0.0011, "SF": 0.00002, "MF": 0.00051, "ML": 0.0015, "CL": 0.022},
    },
    "inductor_transformer": {
        "mil_ref": "Appendix A, Section 11.1, Part Type 'Transformer, Audio'",
        "quality_group": "inductive_device",
        "lambda_g": {"GB": 0.0015, "GF": 0.010, "GM": 0.040, "NS": 0.030, "NU": 0.11, "AIC": 0.14, "AIF": 0.17, "AUC": 0.17, "AUF": 0.22, "ARW": 0.50, "SF": 0.0075, "MF": 0.24, "ML": 0.70, "CL": 10.0},
    },
    "relay_mechanical_general": {
        "mil_ref": "Appendix A, Section 13.1, Part Type 'General Purpose (Bal. Arm.)'",
        "quality_group": "relay_mechanical",
        "lambda_g": {"GB": 0.049, "GF": 0.12, "GM": 0.35, "NS": 0.17, "NU": 0.49, "AIC": 0.60, "AIF": 0.77, "AUC": 1.30, "AUF": 1.40, "ARW": 3.90, "SF": 0.025, "MF": 1.70, "ML": 5.70, "CL": 17.0},
    },
    "connector_rectangular": {
        "mil_ref": "Appendix A, Section 15.1, Part Type 'Rectangular'",
        "quality_group": "connector",
        "lambda_g": {"GB": 0.023, "GF": 0.027, "GM": 0.10, "NS": 0.14, "NU": 0.38, "AIC": 0.10, "AIF": 0.17, "AUC": 0.34, "AUF": 0.52, "ARW": 0.66, "SF": 0.011, "MF": 0.30, "ML": 0.93, "CL": 13.0},
    },
    "connector_rf_coaxial": {
        "mil_ref": "Appendix A, Section 15.1, Part Type 'RF Coaxial'",
        "quality_group": "connector",
        "lambda_g": {"GB": 0.0045, "GF": 0.053, "GM": 0.046, "NS": 0.027, "NU": 0.075, "AIC": 0.020, "AIF": 0.034, "AUC": 0.067, "AUF": 0.10, "ARW": 0.13, "SF": 0.00022, "MF": 0.0058, "ML": 0.018, "CL": 0.28},
    },
    "connector_socket": {
        "mil_ref": "Appendix A, Section 15.2, Part Type 'IC Sockets (DIP, SIP, PGA)'",
        "quality_group": "socket",
        "lambda_g": {"GB": 0.0035, "GF": 0.011, "GM": 0.049, "NS": 0.021, "NU": 0.063, "AIC": 0.028, "AIF": 0.042, "AUC": 0.039, "AUF": 0.046, "ARW": 0.088, "SF": 0.0018, "MF": 0.049, "ML": 0.13, "CL": 2.3},
    },
    "quartz_crystal": {
        "mil_ref": "Appendix A, Section 19.1, Part Type 'Quartz Crystals'",
        "quality_group": "quartz_crystal",
        "lambda_g": {"GB": 0.032, "GF": 0.096, "GM": 0.32, "NS": 0.19, "NU": 0.51, "AIC": 0.38, "AIF": 0.54, "AUC": 0.70, "AUF": 0.90, "ARW": 0.74, "SF": 0.016, "MF": 1.60, "ML": 4.20, "CL": 100.0},
    },
    "fuse": {
        "mil_ref": "Appendix A, Section 22.1, Part Type 'Fuses'",
        "quality_group": "fuse",
        "lambda_g": {"GB": 0.010, "GF": 0.020, "GM": 0.080, "NS": 0.050, "NU": 0.11, "AIC": 0.090, "AIF": 0.12, "AUC": 0.15, "AUF": 0.18, "ARW": 0.16, "SF": 0.0090, "MF": 0.10, "ML": 0.21, "CL": 2.3},
    },
}


# Microcircuit subset from Appendix A A-2/A-3.
MIL_MICROCIRCUIT_ROWS = {
    "microprocessor_mos_8bit": {
        "mil_ref": "Appendix A A-2, Section 5.1, MOS Technology, Microprocessors, MOS, Up to 8 Bits (40-pin DIP)",
        "quality_group": "microcircuit",
        "lambda_g": {"GB": 0.048, "GF": 0.089, "GM": 0.13, "NU": 0.12, "AIC": 0.16, "AUC": 0.16, "AIF": 0.17, "AUF": 0.24, "ARW": 0.28, "SF": 0.044, "MF": 0.15, "ML": 0.28, "CL": 3.4},
    },
    "microprocessor_mos_16bit": {
        "mil_ref": "Appendix A A-2, Section 5.1, MOS Technology, Microprocessors, MOS, Up to 16 Bits (64-pin PGA)",
        "quality_group": "microcircuit",
        "lambda_g": {"GB": 0.093, "GF": 0.34, "GM": 0.24, "NU": 0.21, "AIC": 0.60, "AUC": 0.60, "AIF": 0.62, "AUF": 0.90, "ARW": 0.42, "SF": 0.094, "MF": 0.52, "ML": 1.0, "CL": 6.6},
    },
    "microprocessor_mos_32bit": {
        "mil_ref": "Appendix A A-2, Section 5.1, MOS Technology, Microprocessors, MOS, Up to 32 Bits (128-pin PGA)",
        "quality_group": "microcircuit",
        "lambda_g": {"GB": 0.19, "GF": 0.49, "GM": 0.45, "NU": 0.34, "AIC": 0.60, "AUC": 0.61, "AIF": 0.66, "AUF": 0.90, "ARW": 0.82, "SF": 0.19, "MF": 0.54, "ML": 1.0, "CL": 12.0},
    },
    "memory_mos_rom_16k": {
        "mil_ref": "Appendix A A-3, Section 5.2, MOS Technology, Memories ROM, 16k to 64k",
        "quality_group": "microcircuit",
        "lambda_g": {"GB": 0.0059, "GF": 0.022, "GM": 0.042, "NU": 0.063, "AIC": 0.045, "AUC": 0.068, "AIF": 0.055, "AUF": 0.099, "ARW": 0.088, "SF": 0.0053, "MF": 0.055, "ML": 0.13, "CL": 2.3},
    },
    "memory_mos_rom_256k": {
        "mil_ref": "Appendix A A-3, Section 5.2, MOS Technology, Memories ROM, 256k to 1M",
        "quality_group": "microcircuit",
        "lambda_g": {"GB": 0.011, "GF": 0.036, "GM": 0.066, "NU": 0.098, "AIC": 0.075, "AUC": 0.11, "AIF": 0.090, "AUF": 0.15, "ARW": 0.14, "SF": 0.011, "MF": 0.083, "ML": 0.20, "CL": 3.3},
    },
    "memory_mos_eeprom_16k": {
        "mil_ref": "Appendix A A-3, Section 5.2, MOS Technology, Memories in PROM (EPROM, EEPROM, UVEPROM), 16k to 64k",
        "quality_group": "microcircuit",
        "lambda_g": {"GB": 0.0061, "GF": 0.022, "GM": 0.043, "NU": 0.064, "AIC": 0.046, "AUC": 0.069, "AIF": 0.056, "AUF": 0.093, "ARW": 0.087, "SF": 0.0054, "MF": 0.054, "ML": 0.13, "CL": 2.3},
    },
    "memory_mos_eeprom_256k": {
        "mil_ref": "Appendix A A-3, Section 5.2, MOS Technology, Memories in PROM (EPROM, EEPROM, UVEPROM), 256k to 1M",
        "quality_group": "microcircuit",
        "lambda_g": {"GB": 0.012, "GF": 0.038, "GM": 0.071, "NU": 0.10, "AIC": 0.080, "AUC": 0.12, "AIF": 0.095, "AUF": 0.16, "ARW": 0.14, "SF": 0.012, "MF": 0.080, "ML": 0.20, "CL": 3.3},
    },
    "memory_mos_ram_16k": {
        "mil_ref": "Appendix A A-3, Section 5.2, MOS Technology, Memories RAM (MOS & BiMOS), Up to 16k",
        "quality_group": "microcircuit",
        "lambda_g": {"GB": 0.0050, "GF": 0.019, "GM": 0.034, "NU": 0.050, "AIC": 0.048, "AUC": 0.083, "AIF": 0.054, "AUF": 0.10, "ARW": 0.073, "SF": 0.0044, "MF": 0.044, "ML": 0.098, "CL": 1.4},
    },
    "memory_mos_ram_256k": {
        "mil_ref": "Appendix A A-3, Section 5.2, MOS Technology, Memories RAM (MOS & BiMOS), 256k to 1M",
        "quality_group": "microcircuit",
        "lambda_g": {"GB": 0.043, "GF": 0.092, "GM": 0.14, "NU": 0.16, "AIC": 0.22, "AUC": 0.46, "AIF": 0.23, "AUF": 0.49, "ARW": 0.30, "SF": 0.015, "MF": 0.15, "ML": 0.30, "CL": 2.6},
    },
    "memory_cmos_sram_16k": {
        "mil_ref": "Appendix A A-3, Section 5.2, Bipolar Technology, Memories SRAM CMOS, Up to 16k",
        "quality_group": "microcircuit",
        "lambda_g": {"GB": 0.0066, "GF": 0.026, "GM": 0.052, "NU": 0.078, "AIC": 0.054, "AUC": 0.078, "AIF": 0.067, "AUF": 0.12, "ARW": 0.11, "SF": 0.0054, "MF": 0.067, "ML": 0.16, "CL": 2.5},
    },
    "memory_cmos_sram_256k": {
        "mil_ref": "Appendix A A-3, Section 5.2, Bipolar Technology, Memories SRAM CMOS, 256k to 1M",
        "quality_group": "microcircuit",
        "lambda_g": {"GB": 0.033, "GF": 0.14, "GM": 0.20, "NU": 0.39, "AIC": 0.20, "AUC": 0.35, "AIF": 0.20, "AUF": 0.39, "ARW": 0.24, "SF": 0.033, "MF": 0.14, "ML": 0.30, "CL": 5.8},
    },
}
