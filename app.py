from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from ekb_reliability.exporting import pipeline_result_to_excel_bytes
from ekb_reliability.pipeline import ReliabilityPipeline
from ekb_reliability.reliability.constants import ENVIRONMENT_MULTIPLIER, QUALITY_MULTIPLIER
from ekb_reliability.schemas import PipelineResult

QUALITY_LABELS = {
    "commercial": "Коммерческий",
    "industrial": "Промышленный",
    "military": "Военный",
    "mil_spec": "Военный (MIL-SPEC)",
    "b1": "Военный (B1)",
    "unknown": "Не указано",
}

ENVIRONMENT_LABELS = {
    "ground_benign": "Наземная, благоприятные условия",
    "ground_fixed": "Наземная, стационарная",
    "ground_mobile": "Наземная, подвижная",
    "naval_sheltered": "Морская, защищённая",
    "naval_unsheltered": "Морская, незащищённая",
    "airborne_inhabited_cargo": "Бортовая, обитаемая, транспортная",
    "airborne_inhabited_fighter": "Бортовая, обитаемая, манёвренная",
    "airborne_uninhabited_cargo": "Бортовая, необитаемая, транспортная",
    "airborne_uninhabited_fighter": "Бортовая, необитаемая, манёвренная",
    "space_flight": "Космическая",
    "missile_launch": "Ракетная / пусковая",
    "ground": "Наземная",
    "naval": "Морская",
    "airborne": "Бортовая",
    "space": "Космическая",
    "unknown": "Не указана",
}

FAMILY_LABELS = {
    "resistor": "Резистор",
    "capacitor": "Конденсатор",
    "inductor": "Индуктивность",
    "ferrite": "Ферритовый элемент",
    "diode": "Диод",
    "transistor": "Транзистор",
    "integrated_circuit": "Интегральная схема",
    "connector": "Разъём",
    "relay": "Реле",
    "fuse": "Предохранитель",
    "crystal": "Кварцевый резонатор",
    "sensor_module": "Сенсорный модуль",
    "other": "Прочее",
    "unknown": "Неизвестно",
}

SUBFAMILY_LABELS = {
    "ceramic_capacitor": "Керамический конденсатор",
    "electrolytic_capacitor": "Электролитический конденсатор",
    "film_capacitor": "Плёночный конденсатор",
    "film_or_mica_capacitor": "Плёночный или слюдяной конденсатор",
    "mica_capacitor": "Слюдяной конденсатор",
    "tantalum_capacitor": "Танталовый конденсатор",
    "ferrite_bead": "Ферритовая бусина",
    "signal_diode": "Сигнальный диод",
    "schottky_diode": "Диод Шоттки",
    "zener_diode": "Стабилитрон",
    "tvs_diode": "TVS-диод",
    "bjt": "Биполярный транзистор",
    "mosfet": "MOSFET",
    "microcontroller": "Микроконтроллер",
    "memory_ic": "Микросхема памяти",
    "analog_ic": "Аналоговая ИС",
    "logic_ic": "Логическая ИС",
    "power_ic": "Силовая ИС",
    "op_amp": "Операционный усилитель",
    "generic_ic": "Общая ИС",
    "fixed_resistor": "Постоянный резистор",
    "thermistor": "Термистор",
    "fixed_inductor": "Постоянная индуктивность",
    "common_mode_choke": "Синфазный дроссель",
    "transformer": "Трансформатор",
    "signal_or_rectifier_diode": "Сигнальный / выпрямительный диод",
    "transceiver_ic": "Трансивер",
    "display_module": "Модуль индикации",
    "sensor_module": "Сенсорный модуль",
    "fuse": "Предохранитель",
    "board_connector": "Платный разъём",
    "rf_connector": "ВЧ-разъём",
    "socket": "Сокет",
    "mechanical_relay": "Механическое реле",
    "quartz_crystal": "Кварцевый резонатор",
    "resettable_fuse": "Самовосстанавливающийся предохранитель",
    "unknown": "Неизвестно",
}

METHOD_LABELS = {
    "part_stress": "Детальный расчёт (Part Stress)",
    "parts_count": "Упрощённый расчёт (Parts Count)",
    "none": "Не рассчитывался",
}

BACKEND_LABELS = {
    "reference": "Reference engine",
    "surrogate": "Guarded Random Forest surrogate",
}

DEMO_CASES = {
    "01 — Smoke sample (быстрая проверка, 20 строк)": {
        "path": Path("data/demo_cases/01_smoke_sample.csv"),
        "description": "Небольшой встроенный CSV для быстрого smoke-demo без ручной проверки.",
    },
    "02 — Realistic CAN FD logger (реалистичный CSV, 20 строк)": {
        "path": Path("data/demo_cases/02_realistic_canfd_logger.csv"),
        "description": "Компактный реалистичный BOM со смешанными ИС, пассивными компонентами и датчиками.",
    },
    "03 — Review challenge (есть manual review)": {
        "path": Path("data/demo_cases/03_review_challenge.csv"),
        "description": "Короткий кейс для показа diagnostic-flow: одна строка уходит в manual review.",
    },
    "04 — Supervisor BOM (большой XLSX, multi-sheet)": {
        "path": Path("data/demo_cases/04_supervisor_multisheet_bom.xlsx"),
        "description": "Большой многостраничный BOM для серьёзного показа и realistic evaluation.",
    },
}

STATUS_LABELS = {
    "calculated": "Рассчитано",
    "fallback_parts_count": "Переключено на Parts Count",
    "partial_match": "Частичное совпадение",
    "manual_review_required": "Требуется ручная проверка",
    "unsupported_component": "Компонент не поддерживается",
}

ID_STATUS_LABELS = {
    "calculated": "Распознано",
    "partial_match": "Частично распознано",
    "manual_review_required": "Требуется ручная проверка",
}

COLUMN_LABELS = {
    "source_file": "Файл",
    "source_sheet": "Лист",
    "row_index": "№ строки",
    "raw_description": "Исходное описание",
    "normalized_description": "Нормализованное описание",
    "manufacturer": "Производитель",
    "mpn": "Маркировка / MPN",
    "qty": "Количество",
    "ref_designator": "Позиционные обозначения",
    "family": "Семейство",
    "subfamily": "Подсемейство",
    "identification_confidence": "Уверенность распознавания",
    "identification_status": "Статус распознавания",
    "matched_reference": "Совпадение со справочником",
    "selected_method": "Метод расчёта",
    "status": "Статус",
    "lambda_value": "Интенсивность отказов λ",
    "unit_lambda_value": "Интенсивность отказов λ на 1 шт.",
    "fit": "FIT",
    "mtbf": "MTBF, ч",
    "comment": "Комментарий",
    "assumptions_json": "Допущения (JSON)",
    "extracted_features_json": "Извлечённые признаки (JSON)",
    "model_backend_requested": "Запрошенный контур",
    "model_backend": "Контур расчёта",
    "backend_decision_reason": "Причина выбора контура",
    "surrogate_accepted": "Surrogate принят",
    "reference_ratio_after_calibration": "Отношение surrogate/reference после калибровки",
    "reference_lambda_value": "Reference λ",
    "reference_fit": "Reference FIT",
    "reference_mtbf": "Reference MTBF, ч",
    "surrogate_lambda_value": "Surrogate λ (калибр.)",
    "surrogate_fit": "Surrogate FIT (калибр.)",
    "surrogate_mtbf": "Surrogate MTBF, ч (калибр.)",
    "surrogate_lambda_value_raw": "Surrogate λ (сырой)",
    "surrogate_fit_raw": "Surrogate FIT (сырой)",
    "surrogate_mtbf_raw": "Surrogate MTBF, ч (сырой)",
    "surrogate_calibration_factor": "Коэффициент калибровки surrogate",
}


def label_quality(value: str) -> str:
    return QUALITY_LABELS.get(value, value)


def label_environment(value: str) -> str:
    return ENVIRONMENT_LABELS.get(value, value)


def label_family(value: str) -> str:
    return FAMILY_LABELS.get(value, value)


def label_subfamily(value: str) -> str:
    return SUBFAMILY_LABELS.get(value, value)


def label_method(value: str) -> str:
    return METHOD_LABELS.get(value, value)


def label_backend(value: str) -> str:
    return BACKEND_LABELS.get(value, value)


def label_status(value: str) -> str:
    return STATUS_LABELS.get(value, value)


def label_ident_status(value: str) -> str:
    return ID_STATUS_LABELS.get(value, STATUS_LABELS.get(value, value))


def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns={k: v for k, v in COLUMN_LABELS.items() if k in df.columns})


def prepare_display_df(df: pd.DataFrame) -> pd.DataFrame:
    display_df = df.copy()
    if "family" in display_df.columns:
        display_df["family"] = display_df["family"].map(label_family)
    if "subfamily" in display_df.columns:
        display_df["subfamily"] = display_df["subfamily"].map(label_subfamily)
    if "selected_method" in display_df.columns:
        display_df["selected_method"] = display_df["selected_method"].map(label_method)
    if "status" in display_df.columns:
        display_df["status"] = display_df["status"].map(label_status)
    if "identification_status" in display_df.columns:
        display_df["identification_status"] = display_df["identification_status"].map(label_ident_status)
    return rename_columns(display_df)


st.set_page_config(page_title="Надёжность ЭКБ — MVP", layout="wide")
st.title("Надёжность ЭКБ — MVP")
st.caption("BOM → идентификация → расчёт надёжности → сводка → поиск по маркировке")


@st.cache_resource
def get_pipeline() -> ReliabilityPipeline:
    return ReliabilityPipeline(persistence_enabled=True)


pipe = get_pipeline()

with st.sidebar:
    st.header("Параметры расчёта")
    quality_options = list(QUALITY_MULTIPLIER.keys())
    quality = st.selectbox(
        "Уровень качества",
        options=quality_options,
        index=quality_options.index("commercial"),
        format_func=label_quality,
    )
    environment_options = list(ENVIRONMENT_MULTIPLIER.keys())
    environment = st.selectbox(
        "Среда эксплуатации",
        options=environment_options,
        index=environment_options.index("ground_fixed"),
        format_func=label_environment,
    )
    use_temperature = st.checkbox("Указать рабочую температуру", value=False)
    operating_temp_c = st.number_input(
        "Рабочая температура, °C",
        min_value=-55.0,
        max_value=175.0,
        value=40.0,
        step=5.0,
        disabled=not use_temperature,
    )
    reliability_backend = st.selectbox("Контур оценки надёжности", options=["reference", "surrogate"], format_func=label_backend)
    st.markdown("---")
    st.caption("ML используется для идентификации. Reference — основной инженерный контур. Surrogate — приближённый Random Forest-контур с семейной калибровкой и защитными guardrails; при сильном расхождении строка автоматически остаётся на reference.")
    st.caption(f"Хранилище запусков: {'включено' if pipe.repository is not None else 'недоступно'}")
    with st.expander("Легенда интерфейса", expanded=False):
        st.markdown(
            """
**FIT** — количество отказов на 10^9 часов.

**MTBF** — средняя наработка на отказ в часах.

**Reference** — основной инженерный расчётный контур.

**Surrogate** — ускоряющий приближённый контур; используется только там, где guardrails разрешают замену.

**manual_review_required** — строка не распознана надёжно и требует ручной проверки.

**fallback_parts_count** — детальный расчёт неприменим, поэтому использован упрощённый parts-count режим.

**MIL scope** — в проекте реализован ограниченный validated subset MIL-HDBK-217F, а не полный handbook.
            """
        )

page_upload, page_search, page_history = st.tabs(["BOM-анализ", "Поиск ЭКБ", "История запусков"])

with page_search:
    st.subheader("Поиск ЭКБ по маркировке или описанию")
    col1, col2 = st.columns(2)
    search_description = col1.text_area("Описание / маркировка", placeholder="Например: STM32F103C8T6 ARM MCU 64-LQFP")
    search_mpn = col2.text_input("MPN / part number", placeholder="STM32F103C8T6")
    col3, col4, col5 = st.columns([2, 2, 1])
    search_manufacturer = col3.text_input("Производитель", placeholder="STMicroelectronics")
    search_qty = int(col4.number_input("Количество", min_value=1, value=1, step=1))
    run_search = col5.button("Рассчитать", use_container_width=True)

    if run_search:
        if not search_description.strip() and not search_mpn.strip():
            st.warning("Укажи хотя бы описание или MPN.")
        else:
            result = pipe.evaluate_query(
                description=search_description or search_mpn,
                manufacturer=search_manufacturer or None,
                mpn=search_mpn or None,
                qty=search_qty,
                quality=quality,
                environment=environment,
                operating_temp_c=operating_temp_c if use_temperature else None,
                reliability_backend=reliability_backend,
            )
            st.markdown("### Результат идентификации")
            left, right = st.columns(2)
            left.json(
                {
                    "Семейство": label_family(result["family"]),
                    "Подсемейство": label_subfamily(result["subfamily"]),
                    "Уверенность": round(result["identification_confidence"], 4),
                    "Статус распознавания": label_ident_status(result["identification_status"]),
                    "Совпадение со справочником": result["matched_reference"],
                },
                expanded=True,
            )
            right.json(
                {
                    "Метод расчёта": label_method(result["selected_method"]),
                    "Статус": label_status(result["status"]),
                    "lambda_value": result["lambda_value"],
                    "FIT": result["fit"],
                    "MTBF": result["mtbf"],
                    "Контур": label_backend(result.get("model_backend", "reference")),
                },
                expanded=True,
            )
            with st.expander("Извлечённые признаки", expanded=False):
                st.json(result["extracted_features"], expanded=False)
            with st.expander("Допущения", expanded=False):
                st.json(result["assumptions"], expanded=False)
            if result.get("surrogate_mtbf") is not None:
                st.caption(f"Reference MTBF: {result.get('reference_mtbf')}; Surrogate MTBF: {result.get('surrogate_mtbf')}")
            if result.get("comment"):
                st.info(result["comment"])

    st.markdown("### Совпадения в сохранённой истории")
    history_query = st.text_input("Быстрый поиск по истории", placeholder="Введите MPN или часть описания")
    if history_query:
        matches = pipe.search_parts(history_query, limit=25)
        if matches:
            st.dataframe(prepare_display_df(pd.DataFrame(matches)), use_container_width=True, height=360)
        else:
            st.caption("Совпадения не найдены. История начинает наполняться после запусков BOM-обработки.")

with page_history:
    st.subheader("Последние запуски")
    runs = pipe.list_recent_runs(limit=30)
    if runs:
        runs_df = pd.DataFrame(runs)
        if "environment" in runs_df.columns:
            runs_df["environment"] = runs_df["environment"].map(label_environment)
        if "quality" in runs_df.columns:
            runs_df["quality"] = runs_df["quality"].map(label_quality)
        runs_df = runs_df.rename(
            columns={
                "id": "ID запуска",
                "created_at": "Время запуска",
                "source_file": "Файл",
                "source_kind": "Тип источника",
                "total_rows": "Строк",
                "total_fit": "Total FIT",
                "total_lambda": "Total lambda",
                "system_mtbf_hours": "Системный MTBF, ч",
                "environment": "Среда эксплуатации",
                "quality": "Уровень качества",
            }
        )
        st.dataframe(runs_df, use_container_width=True, height=420)
    else:
        st.info("История пока пуста или БД недоступна.")

with page_upload:
    st.subheader("BOM-анализ")
    source_mode = st.radio("Источник BOM", options=["Загрузить файл", "Встроенный демо-кейс"], horizontal=True)

    source_path: Path | None = None
    source_note = None

    if source_mode == "Загрузить файл":
        uploaded = st.file_uploader("Загрузите BOM-файл (.csv / .xlsx)", type=["csv", "xlsx"])
        if uploaded:
            suffix = Path(uploaded.name).suffix.lower()
            temp_path = Path("data") / f"_uploaded{suffix}"
            temp_path.parent.mkdir(exist_ok=True)
            temp_path.write_bytes(uploaded.getvalue())
            source_path = temp_path
            source_note = f"Загружен файл: {uploaded.name}"
    else:
        demo_name = st.selectbox("Встроенный кейс", options=list(DEMO_CASES.keys()))
        demo_case = DEMO_CASES[demo_name]
        if demo_case["path"].exists():
            source_path = demo_case["path"]
            source_note = demo_case["description"]
        else:
            st.error(f"Демо-файл не найден: {demo_case['path']}")

    if source_note:
        st.caption(source_note)

    with st.expander("Демо-сценарии и быстрый старт", expanded=False):
        st.markdown(
            """
- **01 — Smoke sample**: быстрый показ UI и базового расчёта.
- **02 — Realistic CAN FD logger**: компактный реалистичный BOM для основного демо.
- **03 — Review challenge**: показывает, как система выводит `manual_review_required`.
- **04 — Supervisor BOM**: большой multi-sheet кейс для серьёзного показа.
            """
        )

    if source_path is not None:
        bom_info = pipe.inspect_file(source_path)
        bom_like_sheets = [item["sheet_name"] for item in bom_info["sheet_info"] if item["is_bom_like"] and item["sheet_name"]]
        selected_sheets = None
        suffix = source_path.suffix.lower()

        if suffix == ".xlsx":
            with st.sidebar:
                st.markdown("---")
                st.subheader("Выбор листов")
                selected_sheets = st.multiselect(
                    "Листы для обработки",
                    options=bom_info["sheet_names"],
                    default=bom_like_sheets or bom_info["sheet_names"],
                    help="По умолчанию выбраны листы, похожие на BOM.",
                )
                if not selected_sheets:
                    st.warning("Листы не выбраны. Обработка начнётся после выбора хотя бы одного листа.")
                    selected_sheets = []

        result: PipelineResult = pipe.process_file(
            source_path,
            quality=quality,
            environment=environment,
            operating_temp_c=operating_temp_c if use_temperature else None,
            selected_sheets=selected_sheets if suffix == ".xlsx" else None,
            persist_db=True,
            reliability_backend=reliability_backend,
        )

        df = result.line_results.copy()
        display_df = prepare_display_df(df)

        st.subheader("Сводка запуска")
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("Строк", result.summary["row_count"])
        c2.metric("Общее количество", result.summary["total_qty"])
        c3.metric("Рассчитано", result.summary["calculated_rows"])
        c4.metric("Нужна проверка", result.summary["manual_review_rows"])
        c5.metric("Total FIT", f'{result.summary["total_fit"]:.2f}')
        c6.metric("Системный MTBF, ч", f'{result.summary["system_mtbf_hours"]:.2f}' if result.summary["system_mtbf_hours"] else "∞")
        if result.summary.get("storage_run_id"):
            st.caption(f"Результат сохранён в БД. ID запуска = {result.summary['storage_run_id']}")

        with st.expander("Обнаруженные листы и сопоставление колонок", expanded=False):
            info_rows = []
            for item in bom_info["sheet_info"]:
                info_rows.append(
                    {
                        "Лист": item["sheet_name"] or "<csv>",
                        "Строк": item["row_count"],
                        "Колонок": item["column_count"],
                        "Похоже на BOM": "Да" if item["is_bom_like"] else "Нет",
                        "Сопоставление колонок": json.dumps(item["column_mapping"], ensure_ascii=False),
                    }
                )
            st.dataframe(pd.DataFrame(info_rows), use_container_width=True)

        with st.expander("Параметры запуска", expanded=False):
            st.json(
                {
                    "Среда эксплуатации": label_environment(result.summary["pipeline_options"].get("environment", "unknown")),
                    "Уровень качества": label_quality(result.summary["pipeline_options"].get("quality", "unknown")),
                    "Рабочая температура, °C": result.summary["pipeline_options"].get("operating_temp_c"),
                    "Выбранные листы": result.summary["pipeline_options"].get("selected_sheets"),
                    "Контур": label_backend(result.summary["pipeline_options"].get("reliability_backend", "reference")),
                },
                expanded=False,
            )

        st.subheader("Фильтры")
        f1, f2, f3 = st.columns(3)
        status_options = sorted(df["status"].dropna().unique().tolist())
        family_options = sorted(df["family"].dropna().unique().tolist())
        method_options = sorted(df["selected_method"].dropna().unique().tolist())
        status_filter = f1.multiselect("Статус", options=status_options, default=status_options, format_func=label_status)
        family_filter = f2.multiselect("Семейство", options=family_options, default=family_options, format_func=label_family)
        method_filter = f3.multiselect("Метод расчёта", options=method_options, default=method_options, format_func=label_method)

        filtered_df = df[
            df["status"].isin(status_filter)
            & df["family"].isin(family_filter)
            & df["selected_method"].isin(method_filter)
        ].copy()
        filtered_display_df = prepare_display_df(filtered_df)

        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "BOM / предпросмотр",
            "Идентификация",
            "Надёжность",
            "Сводка и графики",
            "Диагностика",
            "Экспорт",
        ])

        with tab1:
            preview_cols = [
                "source_sheet",
                "row_index",
                "raw_description",
                "manufacturer",
                "mpn",
                "qty",
                "ref_designator",
            ]
            st.dataframe(rename_columns(filtered_display_df[rename_columns(pd.DataFrame(columns=preview_cols)).columns.tolist()]), use_container_width=True, height=500)

        with tab2:
            ident_cols = [
                "source_sheet",
                "raw_description",
                "normalized_description",
                "manufacturer",
                "mpn",
                "family",
                "subfamily",
                "identification_confidence",
                "identification_status",
                "matched_reference",
                "status",
            ]
            st.dataframe(rename_columns(filtered_display_df[rename_columns(pd.DataFrame(columns=ident_cols)).columns.tolist()]), use_container_width=True, height=520)

        with tab3:
            rel_cols = [
                "source_sheet",
                "raw_description",
                "qty",
                "family",
                "subfamily",
                "selected_method",
                "model_backend",
                "status",
                "unit_lambda_value",
                "lambda_value",
                "fit",
                "mtbf",
                "comment",
                "assumptions_json",
            ]
            st.dataframe(rename_columns(filtered_display_df[rename_columns(pd.DataFrame(columns=rel_cols)).columns.tolist()]), use_container_width=True, height=520)

        with tab4:
            left, right = st.columns(2)

            status_counts = filtered_df["status"].value_counts().reset_index()
            status_counts.columns = ["status", "count"]
            status_counts["status"] = status_counts["status"].map(label_status)
            fig1 = px.bar(status_counts, x="status", y="count", title="Распределение строк по статусу")
            left.plotly_chart(fig1, use_container_width=True)

            fam_fit = filtered_df.groupby("family", dropna=False)["fit"].sum().reset_index().sort_values("fit", ascending=False)
            fam_fit["family"] = fam_fit["family"].map(label_family)
            fig2 = px.bar(fam_fit, x="family", y="fit", title="Вклад в FIT по семействам")
            right.plotly_chart(fig2, use_container_width=True)

            method_fit = filtered_df.groupby("selected_method", dropna=False)["fit"].sum().reset_index()
            method_fit["selected_method"] = method_fit["selected_method"].map(label_method)
            fig3 = px.pie(method_fit, names="selected_method", values="fit", title="FIT по методу расчёта")
            st.plotly_chart(fig3, use_container_width=True)

            top = filtered_df.sort_values("fit", ascending=False).head(20)
            top_display = prepare_display_df(top)
            st.write("Топ вкладчиков")
            st.dataframe(
                top_display[["Лист", "Исходное описание", "Семейство", "Подсемейство", "Количество", "FIT", "Контур расчёта", "Статус"]],
                use_container_width=True,
            )

            with st.expander("Справочный уровень MIL для платы (Section 16)", expanded=False):
                st.caption("Показывается отдельно и пока не добавляется автоматически в total system FIT.")
                board_ref = result.summary.get("mil_board_circuit_reference", {})
                if board_ref:
                    st.json({k: v for k, v in board_ref.items() if k != "board_rows"}, expanded=False)
                    rows = board_ref.get("board_rows") or []
                    if rows:
                        st.dataframe(pd.DataFrame(rows), use_container_width=True)

            with st.expander("Сводка по guarded surrogate", expanded=False):
                backend_summary = result.summary.get("backend_selection_summary", {})
                if backend_summary:
                    st.json(backend_summary, expanded=False)

        with tab5:
            diag = filtered_df[filtered_df["status"].isin(["manual_review_required", "unsupported_component", "partial_match"])]
            diag_display = prepare_display_df(diag)
            st.dataframe(
                diag_display[
                    [
                        "Лист",
                        "Исходное описание",
                        "Производитель",
                        "Маркировка / MPN",
                        "Семейство",
                        "Подсемейство",
                        "Уверенность распознавания",
                        "Метод расчёта",
                        "Статус",
                        "Комментарий",
                        "Извлечённые признаки (JSON)",
                    ]
                ],
                use_container_width=True,
                height=520,
            )

        with tab6:
            csv_bytes = filtered_df.to_csv(index=False).encode("utf-8")
            workbook_bytes = pipeline_result_to_excel_bytes(result)
            diagnostics_csv = df[df["status"].isin(["manual_review_required", "unsupported_component", "partial_match"])].to_csv(index=False).encode("utf-8")
            summary_json = json.dumps(result.summary, ensure_ascii=False, indent=2).encode("utf-8")

            st.download_button("Скачать отфильтрованный CSV", csv_bytes, "ekb_results_filtered.csv", "text/csv")
            st.download_button(
                "Скачать Excel-файл",
                workbook_bytes,
                "ekb_results_workbook.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            st.download_button("Скачать CSV с диагностикой", diagnostics_csv, "ekb_diagnostics.csv", "text/csv")
            st.download_button("Скачать summary JSON", summary_json, "ekb_summary.json", "application/json")
    else:
        st.info("Загрузите BOM-файл или выберите встроенный демо-кейс, чтобы начать обработку.")

