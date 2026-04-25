# Реестр датасетов проекта

## 1. Classification dataset
- Файл: `data/external_inputs/Electronic-components-dataset-main.zip`
- Назначение: обучение текстового классификатора ЭКБ по описаниям компонентов.
- Источник: корпус CSV-экспортов описаний компонентов из Digi-Key.
- Объём: 34 CSV, 16 407 строк.
- Ограничение: покрывает не всю ЭКБ, а curated taxonomy для MVP.

## 2. Regression dataset
- Формируется кодом из `src/ekb_reliability/ml/synthetic.py`.
- Назначение: обучение surrogate-модели Random Forest для оценки MTBF.
- Тип: synthetic reference dataset.
- Источник target: расчёты текущего MIL-grounded reliability engine.

## 3. BOM evaluation files
- `data/sample_bom.csv` — встроенный пример для smoke/demo-сценария.
- `data/external_inputs/real_components_bom_canfd_logger_main.csv` — небольшой реалистичный BOM для демонстрации.
- `data/external_inputs/Свод BOM по 109 (1) (1) (1).xlsx` — большой многостраничный BOM для realistic evaluation.
- `data/demo_cases/01_smoke_sample.csv` — короткий встроенный smoke-case.
- `data/demo_cases/02_realistic_canfd_logger.csv` — компактный realistic-case для показа.
- `data/demo_cases/03_review_challenge.csv` — кейс с гарантированным `manual_review_required`.
- `data/demo_cases/04_supervisor_multisheet_bom.xlsx` — clean alias большого BOM для demo через UI.

## 4. LSTM input data
- Пока используется экспериментальный временной ряд, формируемый модулем `train_lstm.py`.
- Production-grade набор полевых временных рядов отказов в текущий release не включён.