from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class ProcessingRun(Base):
    __tablename__ = "processing_runs"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    source_file = Column(Text, nullable=True)
    source_kind = Column(String(50), nullable=False, default="bom_upload")
    total_rows = Column(Integer, nullable=False)
    total_fit = Column(Float, nullable=False)
    total_lambda = Column(Float, nullable=False)
    system_mtbf_hours = Column(Float, nullable=True)
    environment = Column(String(100), nullable=False)
    quality = Column(String(100), nullable=False)
    operating_temp_c = Column(Float, nullable=True)
    selected_sheets = Column(JSON, nullable=True)
    summary = Column(JSON, nullable=False, default=dict)

    line_results = relationship(
        "LineResultRecord",
        back_populates="run",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class LineResultRecord(Base):
    __tablename__ = "line_results"

    id = Column(Integer, primary_key=True)
    processing_run_id = Column(Integer, ForeignKey("processing_runs.id"), nullable=False, index=True)
    source_file = Column(String(255), nullable=True)
    source_sheet = Column(Text, nullable=True)
    row_index = Column(Integer, nullable=True)
    raw_description = Column(Text, nullable=False)
    normalized_description = Column(Text, nullable=False)
    manufacturer = Column(String(255), index=True)
    mpn = Column(String(255), index=True)
    qty = Column(Integer, nullable=False)
    ref_designator = Column(Text, nullable=True)
    family = Column(String(100), nullable=False)
    subfamily = Column(String(100), nullable=False)
    extracted_features = Column(JSON, nullable=False, default=dict)
    identification_confidence = Column(Float, nullable=False)
    identification_status = Column(String(50), nullable=False, default="manual_review_required")
    matched_reference = Column(Text, nullable=True)
    selected_method = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)
    lambda_value = Column(Float, nullable=False)
    unit_lambda_value = Column(Float, nullable=True)
    fit = Column(Float, nullable=False)
    mtbf = Column(Float)
    assumptions = Column(JSON, nullable=False, default=dict)
    comment = Column(Text)

    run = relationship("ProcessingRun", back_populates="line_results")
