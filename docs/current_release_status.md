# Текущее состояние release v3

## Что доведено в этой итерации
- Финальная поставка вычищена от `__pycache__`, `.pyc` и `.pytest_cache`.
- Добавлены встроенные demo-cases для защиты прямо в Streamlit UI.
- Добавлена UI-легенда с пояснением FIT / MTBF / reference / surrogate / manual review.
- Уточнены документы по границам MIL и по матрице соответствия ТЗ.
- Добавлен отдельный документ с простым объяснением, почему MIL в проекте пока не полный.

## Что уже можно уверенно показывать
- BOM-анализ CSV/XLSX;
- realistic summary по модулю;
- поиск ЭКБ по маркировке и описанию;
- history storage;
- classifier отчёты;
- guarded surrogate mode;
- board-level Section 16 reference как отдельный прозрачный блок.

## Что сознательно не трогалось в этой итерации
- LSTM-трек не удалялся и не перерабатывался;
- full MIL handbook coverage не добавлялся;
- Section 16/17 не включались автоматически в total FIT;
- Telcordia / EPFL не интегрировались как production data sources.
