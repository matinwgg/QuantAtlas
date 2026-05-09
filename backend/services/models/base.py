from abc import ABC, abstractmethod
import pandas as pd


class ModelBase(ABC):
    """Abstract base for model inference wrappers.

    Implementations must return a DataFrame containing at least a `position`
    column (0/1) aligned to the input DataFrame's index.
    """

    @abstractmethod
    def infer(self, df: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError()

    def validate_output(self, df: pd.DataFrame):
        if "position" not in df.columns:
            raise ValueError("Model output must contain 'position' column")
