import os
from pathlib import Path


TEST_DB = Path(__file__).resolve().parents[2] / "data" / "resume_workshop_test.db"
os.environ.setdefault("DATABASE_URL", f"sqlite+pysqlite:///{TEST_DB.as_posix()}")

from app.db import models  # noqa: E402,F401
from app.db.base import Base  # noqa: E402
from app.db.session import engine  # noqa: E402

Base.metadata.create_all(engine)
