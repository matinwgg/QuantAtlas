import pandas as pd
import pytest

from services.data import data_loader
from services.feature_store import get_features, pipeline_path
from services.models.train_pipeline import train_and_save_pipeline


@pytest.fixture
def isolated_data_dirs(tmp_path, monkeypatch):
    raw_dir = tmp_path / "raw"
    feature_dir = tmp_path / "features"
    pipeline_dir = tmp_path / "pipelines"
    monkeypatch.setattr(data_loader, "RAW_DATA_DIR", raw_dir)
    monkeypatch.setattr("services.feature_store.BASE_FEATURE_DIR", feature_dir)
    monkeypatch.setattr("services.feature_store.PIPELINE_DIR", pipeline_dir)
    return tmp_path


def setup_raw_csv():
    dates = pd.date_range("2023-01-01", periods=30)
    df = pd.DataFrame(
        {
            "open": range(100, 130),
            "high": range(101, 131),
            "low": range(99, 129),
            "close": [100 + i for i in range(30)],
            "volume": [1000 + i * 10 for i in range(30)],
        },
        index=dates,
    )
    df.index.name = "date"
    data_loader.save_raw_cache(df, "TESTSYM", "US")


def test_train_pipeline_creates_artifact(isolated_data_dirs):
    setup_raw_csv()

    train_and_save_pipeline("TESTSYM", overwrite=True)

    assert pipeline_path("TESTSYM").exists()

    df = get_features("TESTSYM", refresh=False, limit=5, dropna=False)
    assert not df.empty
