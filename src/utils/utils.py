import os
import sys
import yaml
import pickle
import numpy as np
from src.logger import get_logger
from src.exception import IDSException

logger = get_logger(__name__)


def read_yaml(file_path: str) -> dict:
    try:
        with open(file_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise IDSException(e, sys)


def save_object(file_path: str, obj):
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            pickle.dump(obj, f)
        logger.info(f"Object saved → {file_path}")
    except Exception as e:
        raise IDSException(e, sys)


def load_object(file_path: str):
    try:
        with open(file_path, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        raise IDSException(e, sys)


def save_numpy_array(file_path: str, array: np.ndarray):
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        np.save(file_path, array)
        logger.info(f"Array saved → {file_path}")
    except Exception as e:
        raise IDSException(e, sys)


def load_numpy_array(file_path: str) -> np.ndarray:
    try:
        return np.load(file_path, allow_pickle=True)
    except Exception as e:
        raise IDSException(e, sys)


def create_directories(paths: list):
    for path in paths:
        os.makedirs(path, exist_ok=True)
        logger.info(f"Directory created/verified: {path}")