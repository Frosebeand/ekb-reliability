# MIL-HDBK-217F subset implemented in this iteration

This iteration replaces hand-tuned parts-count constants with a manually verified Appendix A subset.

Implemented with exact or directly transcribed `λg` tables and `πQ` factors from the supplied MIL-HDBK-217F Notice 2 pages:

- Section 9.1 resistors: film chip, film insulated, thermistor
- Section 10.1 capacitors: ceramic chip, ceramic general purpose, tantalum chip, aluminum dry, film, mica
- Section 6.1 / 6.3 discrete semiconductors: signal diode, Schottky diode, TVS diode, zener diode, low-frequency BJT
- Section 11.1 / 11.2 inductive devices: transformer, fixed inductor/choke
- Section 13.1 relays: general-purpose mechanical relay
- Section 15.1 / 15.2 connectors: rectangular, RF coaxial, IC socket
- Section 19.1 quartz crystals
- Section 22.1 fuses

Not yet migrated to validated MIL tables in this iteration:

- microcircuits / integrated circuits (Sections 5.1-5.4)
- MOSFET parts-count row selection
- full resistor/capacitor established-reliability subclass mapping
- Section 16 / 17 board- and connection-level contributions in system aggregation
- Telcordia SR-332

Important conservative assumptions used here:

- internal project environments are mapped to MIL symbols (`ground_fixed -> GF`, etc.)
- project quality aliases are reduced to MIL classes conservatively:
  - `military -> mil_spec` or `jan` where the handbook uses JAN classes
  - `industrial -> lower`
  - `commercial -> lower` (or `plastic` for discrete semiconductor packages when applicable)
- unsupported families or unsupported MIL rows still fall back to the legacy MVP parts-count implementation, and this is marked in `assumptions.reference_method`

This keeps the project honest: the validated subset is real, and the non-validated remainder is still explicitly labeled as legacy fallback.
