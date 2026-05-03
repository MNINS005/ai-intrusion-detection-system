"""
Data Preprocessing Component
─────────────────────────────
- Drops unused columns (difficulty_level)
- Encodes labels: binary (0=normal, 1=attack) or multiclass (5 classes)
- Removes duplicates
- Handles missing values
- Logs label distribution (EDA-lite)
"""

import os
import sys
import pandas as pd
from dataclasses import dataclass

from src.logger import get_logger
from src.exception import IDSException
from src.constants import (
    TARGET_COLUMN, DROP_COLUMNS,
    BINARY_LABEL_MAP, MULTICLASS_LABEL_MAP,
)
from src.utils.utils import read_yaml, create_directories

logger = get_logger(__name__)


# ── Config dataclass ──────────────────────────────────────────────────────────

@dataclass
class DataPreprocessingConfig:
    processed_dir:            str
    preprocessed_train_path:  str
    preprocessed_test_path:   str
    target_column:            str
    drop_columns:             list
    binary_classification:    bool


# ── Component ─────────────────────────────────────────────────────────────────

class DataPreprocessing:
    def __init__(self, config: DataPreprocessingConfig):
        self.config = config

    # ── private helpers ───────────────────────────────────────────────────────

    def _drop_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        cols_to_drop = [c for c in self.config.drop_columns if c in df.columns]
        df = df.drop(columns=cols_to_drop)
        logger.info(f"Dropped columns: {cols_to_drop}")
        return df

    def _remove_duplicates(self, df: pd.DataFrame, tag: str) -> pd.DataFrame:
        before = len(df)
        df = df.drop_duplicates()
        removed = before - len(df)
        logger.info(f"[{tag}] Duplicates removed: {removed}")
        return df

    def _handle_missing(self, df: pd.DataFrame, tag: str) -> pd.DataFrame:
        total_missing = df.isnull().sum().sum()
        if total_missing == 0:
            logger.info(f"[{tag}] No missing values found.")
            return df

        logger.warning(f"[{tag}] Found {total_missing} missing values — imputing.")
        for col in df.select_dtypes(include="object").columns:
            df[col].fillna(df[col].mode()[0], inplace=True)
        for col in df.select_dtypes(include="number").columns:
            df[col].fillna(df[col].median(), inplace=True)
        return df

    def _encode_labels(self, df: pd.DataFrame, tag: str) -> pd.DataFrame:
        col = self.config.target_column

        if self.config.binary_classification:
            df[col] = df[col].apply(
                lambda x: 0 if str(x).strip().lower() == "normal" else 1
            )
            dist = df[col].value_counts().to_dict()
            logger.info(
                f"[{tag}] Binary encoding done | normal(0): {dist.get(0,0)} | attack(1): {dist.get(1,0)}"
            )
        else:
            df[col] = df[col].apply(
                lambda x: MULTICLASS_LABEL_MAP.get(str(x).strip().lower(), 1)
            )
            logger.info(
                f"[{tag}] Multiclass encoding done:\n{df[col].value_counts().to_string()}"
            )

        return df

    def _log_eda(self, df: pd.DataFrame, tag: str):
        logger.info(f"[{tag}] Final shape: {df.shape}")
        logger.info(
            f"[{tag}] Label distribution:\n"
            f"{df[self.config.target_column].value_counts().to_string()}"
        )

    # ── main entry point ──────────────────────────────────────────────────────

    def initiate_data_preprocessing(
        self,
        train_path: str,
        test_path:  str,
    ) -> tuple[str, str]:
        """
        Returns (preprocessed_train_path, preprocessed_test_path).
        """
        logger.info("=" * 60)
        logger.info("  Data Preprocessing Started")
        logger.info("=" * 60)

        try:
            create_directories([self.config.processed_dir])

            train_df = pd.read_csv(train_path)
            test_df  = pd.read_csv(test_path)

            for tag, df in [("TRAIN", train_df), ("TEST", test_df)]:
                df = self._drop_columns(df)
                df = self._remove_duplicates(df, tag)
                df = self._handle_missing(df, tag)
                df = self._encode_labels(df, tag)
                self._log_eda(df, tag)
                if tag == "TRAIN":
                    train_df = df
                else:
                    test_df = df

            train_df.to_csv(self.config.preprocessed_train_path, index=False)
            test_df.to_csv(self.config.preprocessed_test_path,   index=False)

            logger.info(f"Preprocessed train saved → {self.config.preprocessed_train_path}")
            logger.info(f"Preprocessed test  saved → {self.config.preprocessed_test_path}")

            logger.info("=" * 60)
            logger.info("  Data Preprocessing Completed")
            logger.info("=" * 60)

            return (
                self.config.preprocessed_train_path,
                self.config.preprocessed_test_path,
            )

        except Exception as e:
            raise IDSException(e, sys)


# ── Factory ───────────────────────────────────────────────────────────────────

def get_data_preprocessing_component(config_path: str = "config/config.yaml") -> DataPreprocessing:
    cfg = read_yaml(config_path)["data_preprocessing"]
    config = DataPreprocessingConfig(
        processed_dir           = cfg["processed_dir"],
        preprocessed_train_path = cfg["preprocessed_train_path"],
        preprocessed_test_path  = cfg["preprocessed_test_path"],
        target_column           = cfg["target_column"],
        drop_columns            = cfg["drop_columns"],
        binary_classification   = cfg["binary_classification"],
    )
    return DataPreprocessing(config)