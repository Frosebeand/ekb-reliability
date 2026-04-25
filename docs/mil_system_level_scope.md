# MIL system-level additions: current scope

This project now includes a **traceable Section 16 reference layer** from MIL-HDBK-217F Appendix A A-10.

## What is included

### Section 16 board-circuit rows
- **16.1 Plated Through Hole Circuit**
- **16.2 Boards Surface Mount Technology Circuit**

These rows are stored in:
- `src/ekb_reliability/reliability/mil_system_level_reference.py`

And exposed through:
- `src/ekb_reliability/reliability/mil_system_level.py`

## How they are used

The current project does **not** merge Section 16 board-circuit rates into total system FIT automatically.

Instead, the pipeline summary now reports:
- per-sheet inferred board technology;
- selected MIL Section 16 row;
- generic failure rate `lambda_g` in failures / 10^6 hours;
- total board-circuit reference for the processed BOM.

This is intentionally reported **separately** because Appendix A A-10 includes explicit design assumptions, and the project does not yet ask the user to confirm those assumptions.

## Board technology inference

For each `source_sheet`, the pipeline infers:
- `surface_mount` if SMD/chip package hints dominate;
- `plated_through_hole` if DIP/TO-92/TO-220/axial/radial/through-hole hints dominate;
- `unknown` if neither side is strong enough.

When the technology cannot be inferred, the board-level reference is not applied for that sheet.

## Why Section 17 is not auto-applied yet

Appendix A A-10 also contains **Section 17 single-connection** rows:
- hand solder, two wrapping;
- hand solder, with wrapping;
- crimp;
- weld;
- clip terminal;
- reflow solder;
- spring socket;
- terminal block.

The project now stores these rows as a validated reference table, but does **not** auto-estimate counts from BOM lines.

Section 17 requires explicit connection counts, which are not directly present in a standard BOM.

A manual helper exists:
- `calculate_single_connection_reference(connection_type, count, environment)`

## Not yet included in totals

Still **not merged** into total system failure rate:
- Section 16 board-circuit references;
- Section 17 single-connection references.

This keeps the current totals honest and prevents silent assumptions.
