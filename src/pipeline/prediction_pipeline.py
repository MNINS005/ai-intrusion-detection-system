"""
Prediction Pipeline
────────────────────
Loads preprocessor.pkl + model.pkl and runs inference on new input.
"""

import os
import sys
import pandas as pd
from dataclasses import dataclass

from src.logger import get_logger
from src.exception import IDSException
from src.utils.utils import read_yaml, load_object
from src.constants import CATEGORICAL_FEATURES, NUMERICAL_FEATURES

logger = get_logger(__name__)
# prediction_pipeline.py
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CONFIG_PATH = os.path.join(BASE, 'config', 'config.yaml')


def resolve_artifact_path(path: str) -> str:
    if os.path.isabs(path):
        return path

    candidates = [
        os.path.normpath(os.path.join(BASE, path)),
        os.path.normpath(os.path.join(BASE, path.lstrip("./\\"))),
    ]

    if path.startswith("../") or path.startswith("..\\"):
        candidates.append(os.path.normpath(os.path.join(BASE, path[3:])))

    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate

    return candidates[0]


@dataclass
class PredictPipelineConfig:
    model_path:   str
    preprocessor_path: str


class PredictPipeline:
    def __init__(self, config_path: str = CONFIG_PATH):
        cfg = read_yaml(config_path)
        self.config = PredictPipelineConfig(
            model_path        = resolve_artifact_path(cfg["model_trainer"]["model_path"]),
            preprocessor_path = resolve_artifact_path(cfg["data_transformation"]["preprocessor_obj_path"]),
        )
        self.model        = load_object(self.config.model_path)
        self.preprocessor = load_object(self.config.preprocessor_path)

    def predict(self, features: pd.DataFrame):
        """
        features: DataFrame with the 41 NSL-KDD feature columns (no label).
        Returns numpy array of predictions.
        """
        try:
            feature_cols = NUMERICAL_FEATURES + CATEGORICAL_FEATURES
            features = features[[c for c in feature_cols if c in features.columns]]
            transformed = self.preprocessor.transform(features)
            predictions = self.model.predict(transformed)
            return predictions
        except Exception as e:
            raise IDSException(e, sys)


class CustomData:
    """Helper to convert a single request into a DataFrame for prediction."""

    def __init__(self, **kwargs):
        # Pass all 41 NSL-KDD features as keyword args
        self.data = kwargs

    def get_data_as_dataframe(self) -> pd.DataFrame:
        try:
            return pd.DataFrame([self.data])
        except Exception as e:
            raise IDSException(e, sys)
        
