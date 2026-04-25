# Release cleanup notes

Эта поставка была очищена перед демонстрацией и проверкой.

## Что изменено
- добавлен canonical classifier artifact `models/component_classifier.joblib`;
- в runtime добавлен fallback на `models/component_classifier_retrained.joblib`;
- старые промежуточные BOM-выгрузки и устаревшие metric JSON перенесены в `artifacts/archive_legacy/data/`;
- удалены `.pytest_cache` и все `__pycache__`;
- интерфейсная подпись уточнена: reference — основной контур, surrogate — приближённый.

## Что не менялось
- расчётные формулы и веса surrogate-модели не перенастраивались;
- финальные графики в `reports/final_release/` оставлены как текущий authoritative release;
- LSTM по-прежнему остаётся experimental.
