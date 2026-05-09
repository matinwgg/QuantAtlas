import pandas as pd
from pathlib import Path

from services.models.train_pipeline import train_and_save_pipeline
from services.feature_store import get_features, pipeline_path
from services.data.data_loader import save_raw_cache


def setup_raw_csv(tmp_path):
    # Use the data loader's save_raw_cache helper to ensure the CSV is placed
    # where the loader expects it (backend/data/raw/us/{symbol}.csv).
    dates = pd.date_range('2023-01-01', periods=30)
    df = pd.DataFrame({
        'open': range(100, 130),
        'high': range(101, 131),
        'low': range(99, 129),
        'close': [100 + i for i in range(30)],
        'volume': [1000 + i*10 for i in range(30)],
    }, index=dates)
    df.index.name = 'date'

    save_raw_cache(df, 'TESTSYM', 'US')

    return True


def test_train_pipeline_creates_artifact(tmp_path):
    setup_raw_csv(tmp_path)

    # train and save
    p = train_and_save_pipeline('TESTSYM', overwrite=True)

    # pipeline file exists
    path = pipeline_path('TESTSYM')
    assert path.exists()

    # get_features should apply pipeline by default; for small test data allow
    # not dropping NA rows
    df = get_features('TESTSYM', refresh=False, limit=5, dropna=False)
    assert not df.empty
