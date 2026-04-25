# EKB Reliability MVP

Практический MVP дипломного проекта:

**«Разработка программного обеспечения для идентификации электронной компонентной базы и определения её надёжности с применением машинного обучения»**

## Что делает проект

Система реализует инженерный конвейер:

`BOM -> parsing -> normalization -> identification -> feature extraction -> method selection -> reference calculation -> aggregation -> diagnostics/export`

## Реализовано в текущем release

- загрузка BOM из CSV/XLSX;
- встроенные demo-cases прямо в Streamlit UI;
- автоопределение колонок BOM;
- нормализация описаний, MPN и производителя;
- гибридная идентификация компонента:
  - rule-based слой;
  - candidate matching по MPN;
  - ML-классификатор `TF-IDF + SGDClassifier(log_loss)`;
- извлечение параметров из описаний;
- reference reliability engine;
- guarded surrogate mode;
- агрегация по BOM/изделию;
- Streamlit UI с фильтрами, diagnostics и экспортом;
- поиск ЭКБ по маркировке / MPN / описанию;
- сохранение истории запусков;
- Docker + PostgreSQL schema;
- тесты `pytest`.

## Самое важное ограничение

Проект нужно позиционировать честно:

- это **MIL-based reference engine**, а не полный цифровой двойник всего MIL-HDBK-217F;
- для `parts_count` реализован **validated subset** Appendix A;
- `part_stress` в текущем release остаётся инженерным MVP-контуром, а не полным переносом всех handbook formulas;
- Section 16 board-level reference уже показывается отдельно, но пока не добавляется автоматически в total FIT;
- Section 17 connection-level reference не считается автоматически, потому что стандартный BOM не содержит counts соединений.

Подробно это объяснено в:
- `docs/mil_not_full_explained.md`
- `docs/mil_subset_scope.md`
- `docs/mil_traceability.md`
- `docs/mil_system_level_scope.md`

## Встроенные demo-cases

В UI доступны готовые кейсы:
- `01 — Smoke sample` — быстрый показ;
- `02 — Realistic CAN FD logger` — основной компактный realistic BOM;
- `03 — Review challenge` — показывает `manual_review_required`;
- `04 — Supervisor BOM` — большой multi-sheet XLSX.

Подробности:
- `docs/demo_scenarios.md`

## Запуск локально

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

pip install -r requirements.txt
pip install -e .

streamlit run app.py
```

## Архитектурная идея

- **Reference** — основной инженерный расчётный контур.
- **Surrogate** — ускоряющий приближённый контур, который включается только там, где guardrails разрешают замену.
- ML не заменяет инженерную логику: он используется для идентификации и для surrogate-ускорения, но не подменяет reference engine целиком.

## Финальные артефакты

Единственным авторитетным местом для итоговых метрик и графиков считается:

- `reports/final_release/`

Ключевые папки:
- `reports/final_release/classifier/`
- `reports/final_release/surrogate_mtbf/`
- `reports/final_release/lstm/`
- `reports/final_release/summary/`

## Полезные документы

- `docs/current_release_status.md`
- `docs/tz_progress_matrix.md`
- `docs/dataset_registry.md`
- `docs/demo_scenarios.md`
- `docs/mil_not_full_explained.md`
