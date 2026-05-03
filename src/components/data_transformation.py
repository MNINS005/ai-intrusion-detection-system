"""
Data Transformation Component
───────────────────────────────
- Builds a ColumnTransformer: OHE for categoricals + scaler for numericals
- fit on train, transform both train & test
- Saves the fitted preprocessor object as preprocessor.pkl
- Saves final arrays as .npz (X + y bundled together)
"""

import os
import sys
import numpy as np
import pandas as pd
from dataclasses import dataclass

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    OneHotEncoder, StandardScaler, MinMaxScaler, RobustScaler
)

from src.logger import get_logger
from src.exception import IDSException
from src.constants import CATEGORICAL_FEATURES, NUMERICAL_FEATURES, TARGET_COLUMN
from src.utils.utils import read_yaml, create_directories, save_object

logger = get_logger(__name__)

SCALER_MAP = {
    "standard": StandardScaler(),
    "minmax":   MinMaxScaler(),
    "robust":   RobustScaler(),
}


# ── Config dataclass ──────────────────────────────────────────────────────────

@dataclass
class DataTransformationConfig:
    transformed_dir:       str
    train_arr_path:        str
    test_arr_path:         str
    preprocessor_obj_path: str
    scaler:                str


# ── Component ─────────────────────────────────────────────────────────────────

class DataTransformation:
    def __init__(self, config: DataTransformationConfig):
        self.config = config

    def _get_preprocessor(self, available_cols: list) -> ColumnTransformer:
        """
        Only uses categorical/numerical features that actually exist in the data.
        Handles edge cases where a feature column might be missing.
        """
        cat_cols = [c for c in CATEGORICAL_FEATURES if c in available_cols]
        num_cols = [c for c in NUMERICAL_FEATURES    if c in available_cols]

        logger.info(f"Categorical features ({len(cat_cols)}): {cat_cols}")
        logger.info(f"Numerical features  ({len(num_cols)}): {num_cols}")

        scaler = SCALER_MAP.get(self.config.scaler, StandardScaler())

        num_pipeline = Pipeline([("scaler", scaler)])
        cat_pipeline = Pipeline([
            ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
        ])

        preprocessor = ColumnTransformer(
            transformers=[
                ("num", num_pipeline, num_cols),
                ("cat", cat_pipeline, cat_cols),
            ],
            remainder="drop",
        )
        return preprocessor

    def initiate_data_transformation(
        self,
        train_path: str,
        test_path:  str,
    ) -> tuple[str, str, str]:
        """
        Returns (train_arr_path, test_arr_path, preprocessor_obj_path).
        """
        logger.info("=" * 60)
        logger.info("  Data Transformation Started")
        logger.info("=" * 60)

        try:
            create_directories([self.config.transformed_dir])

            train_df = pd.read_csv(train_path)
            test_df  = pd.read_csv(test_path)

            X_train = train_df.drop(columns=[TARGET_COLUMN])
            y_train = train_df[TARGET_COLUMN].values

            X_test  = test_df.drop(columns=[TARGET_COLUMN])
            y_test  = test_df[TARGET_COLUMN].values

            logger.info(f"X_train: {X_train.shape} | X_test: {X_test.shape}")

            preprocessor = self._get_preprocessor(list(X_train.columns))

            X_train_arr = preprocessor.fit_transform(X_train)
            X_test_arr  = preprocessor.transform(X_test)

            logger.info(f"After transform → X_train: {X_train_arr.shape} | X_test: {X_test_arr.shape}")

            # Bundle X + y together in .npz
            np.savez_compressed(self.config.train_arr_path, X=X_train_arr, y=y_train)
            np.savez_compressed(self.config.test_arr_path,  X=X_test_arr,  y=y_test)

            # Save fitted preprocessor
            save_object(self.config.preprocessor_obj_path, preprocessor)

            logger.info(f"Train array saved  → {self.config.train_arr_path}")
            logger.info(f"Test  array saved  → {self.config.test_arr_path}")

            logger.info("=" * 60)
            logger.info("  Data Transformation Completed")
            logger.info("=" * 60)

            return (
                self.config.train_arr_path,
                self.config.test_arr_path,
                self.config.preprocessor_obj_path,
            )

        except Exception as e:
            raise IDSException(e, sys)


# ── Factory ───────────────────────────────────────────────────────────────────

def get_data_transformation_component(config_path: str = "config/config.yaml") -> DataTransformation:
    cfg = read_yaml(config_path)["data_transformation"]
    config = DataTransformationConfig(
        transformed_dir       = cfg["transformed_dir"],
        train_arr_path        = cfg["train_arr_path"],
        test_arr_path         = cfg["test_arr_path"],
        preprocessor_obj_path = cfg["preprocessor_obj_path"],
        scaler                = cfg["scaler"],
    )
    return DataTransformation(config)