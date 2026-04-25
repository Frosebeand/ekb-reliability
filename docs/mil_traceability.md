# MIL-HDBK-217F traceability for current implementation

This file lists exactly which MIL-HDBK-217F elements are implemented in code, which are implemented with explicit restrictions, and which remain out of scope.

## Core method logic

### Parts Count method
Implemented from Appendix A page A-1:
- equipment failure rate is the sum of `N_i * λ_g * π_Q`
- per-environment partitioning is supported by selecting the row for the chosen environment code
- for microcircuits an additional `π_L` factor is applied when years in production are less than two

Code:
- `src/ekb_reliability/reliability/mil_parts_count.py`
- `src/ekb_reliability/reliability/parts_count.py`

MIL source:
- Appendix A A-1, equation and notes on `λ_g`, `π_Q`, `N_i`, and `π_L`

## Environment codes

Implemented environment symbols:
- `GB`, `GF`, `GM`, `NS`, `NU`, `AIC`, `AIF`, `AUC`, `AUF`, `ARW`, `SF`, `MF`, `ML`, `CL`

Code:
- `src/ekb_reliability/reliability/mil_parts_count_reference.py`

MIL source:
- Appendix A A-1 references Section 3 environmental symbols
- Section 5.10 page 5-15 contains microcircuit `π_E`

## Validated Appendix A subset now implemented

### Resistors
Implemented rows:
- film chip
- film insulated
- thermistor

### Capacitors
Implemented rows:
- ceramic chip
- ceramic general
- tantalum chip
- aluminum dry electrolytic
- metallized plastic film
- mica

### Diodes / transistors
Implemented rows:
- switching diode
- schottky power rectifier
- transient suppressor / varistor
- avalanche / zener
- low-frequency BJT (`f < 200 MHz`)

### Inductive devices
Implemented rows:
- fixed inductor / choke
- transformer

### Relays
Implemented rows:
- general purpose mechanical relay

### Connectors / sockets
Implemented rows:
- rectangular connector
- RF coaxial connector
- IC socket

### Quartz crystals and fuses
Implemented rows:
- quartz crystals
- fuses

## Newly added microcircuit subset

### Implemented rows
Implemented directly from Appendix A A-2/A-3:
- MOS microprocessors up to 8 bits
- MOS microprocessors up to 16 bits
- MOS microprocessors up to 32 bits
- MOS ROM memories (`16k..64k`, `256k..1M`)
- MOS EPROM/EEPROM/UVEPROM (`16k..64k`, `256k..1M`)
- MOS/BiMOS RAM (`up to 16k`, `256k..1M`)
- CMOS SRAM (`up to 16k`, `256k..1M`)

### Explicit restrictions
These rows are only applied when:
- family = `integrated_circuit`
- subfamily is `microcontroller` or `memory_ic`
- quality alias is explicitly MIL-like (`military` / `mil_spec` or `b1`)
- `π_L` is assumed 1.0 unless `years_in_production` is passed explicitly

Why restricted:
- the visible quality table excerpt reliably gives `.25`, `1.0`, and `2.0` for selected microcircuit categories
- the project has not yet transcribed the full lower-grade/plastic/custom-screening mapping
- therefore commercial/industrial ICs are not silently coerced into the validated MIL subset

## What is still not implemented

### Microcircuits not yet mapped
Not yet implemented from A-2/A-3:
- linear microcircuits
- gate/logic arrays
- PROM/PLA mapping beyond memory subfamily
- VHSIC/VLSI references to section 5.3/5.4 in Parts Count

### Board/system additions
Not yet implemented:
- Section 16 Interconnection Assemblies contribution
- Section 17 Connections contribution

### Full Part Stress alignment
Not yet implemented:
- exact section 5 through 23 formulas and modifiers for the project subset
- exact microcircuit `C1/C2/π_T/π_E/π_Q` model path in the Part Stress engine

## Code behavior summary

1. `parts_count` first tries the validated MIL subset.
2. If no validated row is available, it falls back to the legacy MVP constants.
3. For integrated circuits, validated MIL rows are only used for `microcontroller` and `memory_ic`, and only when quality is explicitly MIL-like.
4. Everything else remains explicit fallback rather than invented mapping.
