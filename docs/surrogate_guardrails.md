# Guarded surrogate release note

The Random Forest surrogate is no longer used as a blind replacement for the reference engine.

Release changes:
- surrogate is only eligible for calibrated part-stress families;
- parts-count rows stay on the reference contour;
- a family-level post-calibration factor is applied before use;
- if the calibrated surrogate still differs too much from the reference row, the line automatically falls back to the reference result;
- summary JSON now includes `backend_selection_summary` so the accepted/rejected surrogate rows are visible.

Why this was added:
- the shipped surrogate model was noticeably unstable on real BOM data;
- the project now treats surrogate as an acceleration/approximation layer with explicit safety checks, not as an unconditional replacement for the engineering contour.
