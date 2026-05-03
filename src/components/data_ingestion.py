"""
Data Ingestion Component
────────────────────────
Reads the locally downloaded NSL-KDD .txt files (no headers in the raw file),
assigns the 43 official column names, and saves clean train/test CSVs into
artifacts/raw/.

Expected raw file layout (comma-separated, no header row):
  duration, protocol_type, service, flag, src_bytes, dst_bytes, ..., label, difficulty_level
"""

import os
import sys
import shutil
import pandas as pd
from dataclasses import dataclass

from src.logger import get_logger
from src.exception import IDSException
from src.constants import NSL_KDD_COLUMNS
from src.utils.utils import read_yaml, create_directories

logger = get_logger(__name__)


# ── Config dataclass ──────────────────────────────────────────────────────────

@dataclass
class DataIngestionConfig:
    raw_data_dir:         str
    train_data_path:      str   # source: your local download location
    test_data_path:       str   # source: your local download location
    ingested_train_path:  str   # destination: artifacts/raw/train.csv
    ingested_test_path:   str   # destination: artifacts/raw/test.csv


# ── Component ─────────────────────────────────────────────────────────────────

class DataIngestion:
    def __init__(self, config: DataIngestionConfig):
        self.config = config

    def _read_raw_file(self, file_path: str) -> pd.DataFrame:
        """
        NSL-KDD .txt files have NO header row and 43 comma-separated columns.
        We assign NSL_KDD_COLUMNS (41 features + label + difficulty_level).
        """
        logger.info(f"Reading raw file: {file_path}")

        if not os.path.exists(file_path):
            raise FileNotFoundError(
                f"Raw data file not found at '{file_path}'.\n"
                f"Download KDDTrain+.txt and KDDTest+.txt from:\n"
                f"  https://www.kaggle.com/datasets/hassan06/nslkdd\n"
                f"Then place them in: notebook/data/"
            )

        df = pd.read_csv(
            file_path,
            header=None,           # NO header in the raw file
            names=NSL_KDD_COLUMNS, # assign the 43 official column names
        )

        logger.info(f"Loaded {len(df)} rows, {df.shape[1]} columns from {file_path}")
        logger.info(f"Columns assigned: {list(df.columns)}")
        return df

    def _basic_validation(self, df: pd.DataFrame, tag: str):
        """Sanity checks right after loading."""
        assert df.shape[1] == len(NSL_KDD_COLUMNS), (
            f"[{tag}] Expected {len(NSL_KDD_COLUMNS)} columns, got {df.shape[1]}"
        )
        missing = df.isnull().sum().sum()
        logger.info(f"[{tag}] Shape: {df.shape} | Missing values: {missing}")
        logger.info(f"[{tag}] Label distribution:\n{df['label'].value_counts().to_string()}")

    def initiate_data_ingestion(self) -> tuple[str, str]:
        """
        Main entry point.
        Returns (ingested_train_path, ingested_test_path).
        """
        logger.info("=" * 60)
        logger.info("  Data Ingestion Started")
        logger.info("=" * 60)

        try:
            create_directories([self.config.raw_data_dir])

            # ── Load raw files ────────────────────────────────────────────────
            train_df = self._read_raw_file(self.config.train_data_path)
            test_df  = self._read_raw_file(self.config.test_data_path)

            # ── Validate ──────────────────────────────────────────────────────
            self._basic_validation(train_df, "TRAIN")
            self._basic_validation(test_df,  "TEST")

            # ── Save to artifacts/raw/ ─────────────────────────────────────────
            train_df.to_csv(self.config.ingested_train_path, index=False)
            test_df.to_csv(self.config.ingested_test_path,   index=False)

            logger.info(f"Train CSV saved → {self.config.ingested_train_path}")
            logger.info(f"Test  CSV saved → {self.config.ingested_test_path}")

            logger.info("=" * 60)
            logger.info("  Data Ingestion Completed")
            logger.info("=" * 60)

            return (
                self.config.ingested_train_path,
                self.config.ingested_test_path,
            )

        except Exception as e:
            raise IDSException(e, sys)


# ── Factory: build from config.yaml ──────────────────────────────────────────

def get_data_ingestion_component(config_path: str = "config/config.yaml") -> DataIngestion:
    cfg = read_yaml(config_path)["data_ingestion"]
    config = DataIngestionConfig(
        raw_data_dir        = cfg["raw_data_dir"],
        train_data_path     = cfg["train_data_path"],
        test_data_path      = cfg["test_data_path"],
        ingested_train_path = cfg["ingested_train_path"],
        ingested_test_path  = cfg["ingested_test_path"],
    )
    return DataIngestion(config)