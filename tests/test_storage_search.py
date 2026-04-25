from __future__ import annotations

import pytest
pytest.importorskip("sqlalchemy")

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ekb_reliability.pipeline import ReliabilityPipeline
from ekb_reliability.search import evaluate_part_query
from ekb_reliability.storage.models import Base
from ekb_reliability.storage.repository import StorageRepository


def make_repo():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return StorageRepository(sessionmaker(bind=engine, future=True, expire_on_commit=False))


def test_repository_saves_and_lists_runs(tmp_path: Path):
    pipe = ReliabilityPipeline(persistence_enabled=False)
    result = pipe.process_file(Path("data/sample_bom.csv"), persist_db=False)

    repo = make_repo()
    run_id = repo.save_pipeline_result(
        source_file="sample_bom.csv",
        source_kind="bom_upload",
        result=result,
        pipeline_options=result.summary["pipeline_options"],
    )

    assert run_id >= 1
    runs = repo.list_recent_runs(limit=5)
    assert len(runs) == 1
    assert runs[0]["source_file"] == "sample_bom.csv"


def test_repository_search_parts_by_mpn(tmp_path: Path):
    pipe = ReliabilityPipeline(persistence_enabled=False)
    result = pipe.process_file(Path("data/sample_bom.csv"), persist_db=False)
    repo = make_repo()
    repo.save_pipeline_result(
        source_file="sample_bom.csv",
        source_kind="bom_upload",
        result=result,
        pipeline_options=result.summary["pipeline_options"],
    )
    rows = repo.search_parts("CL10X106MO8NRN")
    assert rows
    assert rows[0]["mpn"] == "CL10X106MO8NRN"


def test_evaluate_query_uses_db_history_exact_mpn():
    pipe = ReliabilityPipeline(persistence_enabled=False)
    result = pipe.process_file(Path("data/sample_bom.csv"), persist_db=False)
    repo = make_repo()
    repo.save_pipeline_result(
        source_file="sample_bom.csv",
        source_kind="bom_upload",
        result=result,
        pipeline_options=result.summary["pipeline_options"],
    )
    query_result = evaluate_part_query(
        description="",
        manufacturer=None,
        mpn="CL10X106MO8NRN",
        qty=1,
        classifier=pipe.classifier,
        surrogate=pipe.surrogate,
        repository=repo,
        quality="commercial",
        environment="ground_fixed",
        operating_temp_c=None,
    )
    assert query_result["family"] == "capacitor"
    assert query_result["matched_reference"] in {"db_history", "bom_bootstrap", None}
