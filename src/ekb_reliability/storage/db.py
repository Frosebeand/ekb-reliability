from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ekb_reliability.storage.models import Base

DEFAULT_DB_URL = os.getenv("EKB_DB_URL", "sqlite:///ekb_reliability.db")


def make_engine(db_url: str = DEFAULT_DB_URL):
    return create_engine(
        db_url,
        future=True,
        use_insertmanyvalues=False,
        pool_pre_ping=True,
    )


_engine = None
_SessionFactory = None


def init_db(db_url: str = DEFAULT_DB_URL):
    global _engine, _SessionFactory
    _engine = make_engine(db_url)
    Base.metadata.create_all(_engine)
    _SessionFactory = sessionmaker(bind=_engine, future=True, expire_on_commit=False)
    return _engine


def get_session_factory(db_url: str = DEFAULT_DB_URL):
    global _engine, _SessionFactory
    if _SessionFactory is None:
        init_db(db_url)
    return _SessionFactory


def make_session(db_url: str = DEFAULT_DB_URL):
    session_factory = get_session_factory(db_url)
    return session_factory()