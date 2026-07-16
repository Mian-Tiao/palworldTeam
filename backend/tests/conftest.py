"""測試共用設定:獨立的測試資料庫 + 種子資料 + TestClient。

DATABASE_URL 必須在匯入任何 app 模組前設定(engine 於匯入時建立)。
"""

import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
TEST_DB_PATH = BACKEND_ROOT / "test_palworld.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
sys.path.insert(0, str(BACKEND_ROOT))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture(scope="session")
def client():
    import app.models  # noqa: F401
    from app.core.db import Base, engine
    from scripts.seed_dev import main as seed_main

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    seed_main()

    from app.main import app

    # with 區塊觸發 lifespan(載入記憶體快取)
    with TestClient(app) as test_client:
        yield test_client

    Base.metadata.drop_all(engine)
    engine.dispose()
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
