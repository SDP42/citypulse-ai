from datetime import datetime, timezone

import pytest

from citypulse.core.settings import Settings
from citypulse.db.connection import connect, migrate
from citypulse.db.seed import WARDS, seed_all

NOW = datetime(2026, 10, 14, tzinfo=timezone.utc)


@pytest.fixture
def settings():
    return Settings(data_mode="synthetic", max_upload_mb=25)


@pytest.fixture
def db(tmp_path):
    con = connect(tmp_path / "t.sqlite")
    migrate(con)
    seed_all(con)
    yield con
    con.close()


requires_wards = pytest.mark.skipif(not WARDS.exists(), reason="data/processed/mumbai_wards.geojson not built (scripts/build_wards.py)")
