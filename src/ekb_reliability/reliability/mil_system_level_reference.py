from __future__ import annotations

# Manually verified Appendix A A-10 rows from MIL-HDBK-217F Notice 2.
# Units: generic failure rate λg in failures / 10^6 hours.
# These tables are exposed for traceability and controlled system-level estimation.

MIL_BOARD_CIRCUIT_ROWS = {
    "plated_through_hole": {
        "mil_ref": "Appendix A A-10, Section 16.1, Plated Through Hole Circuit",
        "lambda_g": {
            "GB": 0.022,
            "GF": 0.045,
            "GM": 0.16,
            "NS": 0.11,
            "NU": 0.29,
            "AIC": 0.11,
            "AIF": 0.18,
            "AUC": 0.36,
            "AUF": 0.62,
            "ARW": 0.42,
            "SF": 0.011,
            "MF": 0.22,
            "ML": 0.60,
            "CL": 11.0,
        },
        "notes": [
            "MIL Appendix A A-10 note 7 applies: plated-through-hole circuit board assumptions are 10 solder joints, 3 planes, no hand soldering.",
        ],
    },
    "surface_mount": {
        "mil_ref": "Appendix A A-10, Section 16.2, Boards Surface Mount Technology Circuit",
        "lambda_g": {
            "GB": 0.0025,
            "GF": 0.37,
            "GM": 1.8,
            "NS": 1.8,
            "NU": 42.0,
            "AIC": 6.1,
            "AIF": 6.1,
            "AUC": 35.0,
            "AUF": 35.0,
            "ARW": 6.1,
            "SF": 0.0025,
            "MF": 0.11,
            "ML": 0.11,
            "CL": 0.11,
        },
        "notes": [
            "MIL Appendix A A-10 note 8 applies: SMT circuit board design assumptions are the same as those shown in Section 16.2 example.",
        ],
    },
}

MIL_SINGLE_CONNECTION_ROWS = {
    "hand_solder_two_wrappings": {
        "mil_ref": "Appendix A A-10, Section 17.1, Hand Solder, Two Wrapping",
        "lambda_g": {"GB": 0.0013, "GF": 0.0026, "GM": 0.0091, "NS": 0.0052, "NU": 0.014, "AIC": 0.0052, "AIF": 0.0078, "AUC": 0.0078, "AUF": 0.010, "ARW": 0.021, "SF": 0.00065, "MF": 0.012, "ML": 0.031, "CL": 0.55},
    },
    "hand_solder_with_wrapping": {
        "mil_ref": "Appendix A A-10, Section 17.1, Hand Solder, W/Wrapping",
        "lambda_g": {"GB": 0.00007, "GF": 0.00014, "GM": 0.00049, "NS": 0.00028, "NU": 0.00077, "AIC": 0.00028, "AIF": 0.00042, "AUC": 0.00042, "AUF": 0.00056, "ARW": 0.0011, "SF": 0.000035, "MF": 0.00063, "ML": 0.0017, "CL": 0.029},
    },
    "crimp": {
        "mil_ref": "Appendix A A-10, Section 17.1, Crimp",
        "lambda_g": {"GB": 0.00023, "GF": 0.00052, "GM": 0.0019, "NS": 0.00060, "NU": 0.0017, "AIC": 0.00060, "AIF": 0.00090, "AUC": 0.00090, "AUF": 0.0012, "ARW": 0.00024, "SF": 0.000075, "MF": 0.0023, "ML": 0.0062, "CL": 0.11},
    },
    "weld": {
        "mil_ref": "Appendix A A-10, Section 17.1, Weld",
        "lambda_g": {"GB": 0.00015, "GF": 0.00030, "GM": 0.0011, "NS": 0.00045, "NU": 0.0013, "AIC": 0.00045, "AIF": 0.00067, "AUC": 0.00067, "AUF": 0.00089, "ARW": 0.0017, "SF": 0.000050, "MF": 0.0013, "ML": 0.0033, "CL": 0.063},
    },
    "clip_terminal": {
        "mil_ref": "Appendix A A-10, Section 17.1, Clip Terminal",
        "lambda_g": {"GB": 0.0000081, "GF": 0.000065, "GM": 0.00048, "NS": 0.00027, "NU": 0.00063, "AIC": 0.00048, "AIF": 0.00065, "AUC": 0.00065, "AUF": 0.00089, "ARW": 0.0019, "SF": 0.0000081, "MF": 0.00030, "ML": 0.00086, "CL": 0.0030},
    },
    "reflow_solder": {
        "mil_ref": "Appendix A A-10, Section 17.1, Reflow Solder",
        "lambda_g": {"GB": 0.00012, "GF": 0.00024, "GM": 0.00084, "NS": 0.00048, "NU": 0.0013, "AIC": 0.00048, "AIF": 0.00072, "AUC": 0.00072, "AUF": 0.00096, "ARW": 0.0019, "SF": 0.000036, "MF": 0.00082, "ML": 0.0019, "CL": 0.0029},
    },
    "spring_socket": {
        "mil_ref": "Appendix A A-10, Section 17.1, Spring Socket",
        "lambda_g": {"GB": 0.00007, "GF": 0.00014, "GM": 0.00048, "NS": 0.00028, "NU": 0.00076, "AIC": 0.00028, "AIF": 0.00041, "AUC": 0.00041, "AUF": 0.00055, "ARW": 0.0011, "SF": 0.000035, "MF": 0.00082, "ML": 0.0019, "CL": 0.0029},
    },
    "terminal_block": {
        "mil_ref": "Appendix A A-10, Section 17.1, Terminal Block",
        "lambda_g": {"GB": 0.00069, "GF": 0.0014, "GM": 0.0048, "NS": 0.0028, "NU": 0.0076, "AIC": 0.0028, "AIF": 0.0041, "AUC": 0.0041, "AUF": 0.0055, "ARW": 0.011, "SF": 0.00035, "MF": 0.0062, "ML": 0.017, "CL": 0.29},
    },
}
