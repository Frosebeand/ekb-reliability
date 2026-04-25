# Матрица соответствия ТЗ — release v3

| Требование ТЗ | Статус | Где подтверждается в проекте | Комментарий |
|---|---|---|---|
| Python 3.11 | Закрыто | `pyproject.toml` | Runtime ориентирован на Python 3.11. |
| Pandas / NumPy / Scikit-learn | Закрыто | `requirements.txt`, `src/ekb_reliability/` | Используются в основном контуре и ML-слоях. |
| TensorFlow | Частично | `requirements.txt`, `reports/final_release/lstm/` | LSTM оставлен в experimental-статусе и пока не является основным демонстрационным модулем. |
| PostgreSQL | Частично | `docker-compose.yml`, `src/ekb_reliability/storage/` | Поддержан как целевая БД в docker-сценарии; локально default может оставаться SQLite. |
| Docker | Закрыто | `Dockerfile`, `docker-compose.yml` | Готов docker-сценарий app + db. |
| Веб/GUI интерфейс | Закрыто | `app.py` | Streamlit UI с анализом BOM, поиском ЭКБ и историей запусков. |
| Загрузка BOM CSV/XLSX | Закрыто | `app.py`, `src/ekb_reliability/bom.py` | Поддержаны CSV и XLSX, включая multi-sheet выбор. |
| Идентификация ЭКБ | Закрыто | `classification.py`, `rules.py`, UI | Rule-based + matching + ML classifier. |
| Расчёт FIT / MTBF / λ | Закрыто в основном сценарии | `pipeline.py`, `reliability/` | Основной reference engine работает; coverage MIL ограничен validated subset + fallback. |
| Визуализация результатов | Закрыто | `app.py`, `reports/final_release/` | Summary, графики, diagnostics, экспорт. |
| Датасет не менее 10 000 компонентов | Частично | `docs/dataset_registry.md` | Общий исходный корпус > 10k, но curated classifier subset уже меньше. Формулировать аккуратно. |
| Accuracy классификации ≥ 85% | Закрыто | `reports/final_release/classifier/classifier_metrics.json` | Accuracy выше порога. |
| ROC-кривые | Закрыто | `reports/final_release/classifier/classifier_roc_curves.png` | В финальном пакете есть ROC. |
| Важность признаков | Закрыто | `reports/final_release/classifier/classifier_feature_importance.png` | В финальном пакете есть feature importance. |
| MAE при прогнозировании MTBF ≤ 10% | Частично / спорная формулировка | `reports/final_release/surrogate_mtbf/`, квал-практика | По смыслу исследовательской части основной метрикой используется MAPE; трактовку нужно согласовать с руководителем. |
| Исходный код проекта | Закрыто по поставке архива | архив проекта | Для формального закрытия пункта про GitLab нужна ссылка на репозиторий. |

## Что считать сильной практической частью уже сейчас
- рабочий BOM pipeline;
- реальный Streamlit UI;
- Docker-сборка;
- classifier + ROC + feature importance;
- guarded surrogate;
- realistic demo cases внутри поставки;
- честный MIL-based reference contour с явно описанными ограничениями.

## Что проговаривать аккуратно
- MIL реализован не полностью, а как validated subset + fallback.
- LSTM пока experimental и не является главным демонстрационным треком.
- Пункт про `MAE <= 10%` лучше защищать через согласованную трактовку с руководителем.
