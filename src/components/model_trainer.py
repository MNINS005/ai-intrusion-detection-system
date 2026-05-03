"""
Model Trainer Component
────────────────────────
- Trains RF, XGBoost, DecisionTree with GridSearchCV
- Picks best model by weighted F1 on test set
- Saves best model as model.pkl + training_report.json
"""

import os
import sys
import json
import numpy as np
from dataclasses import dataclass

from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import f1_score

try:
    from xgboost import XGBClassifier
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False

from src.logger import get_logger
from src.exception import IDSException
from src.utils.utils import read_yaml, save_object, create_directories

logger = get_logger(__name__)


# ── Config dataclass ──────────────────────────────────────────────────────────

@dataclass
class ModelTrainerConfig:
    model_dir:    str
    model_path:   str
    random_state: int


# ── Component ─────────────────────────────────────────────────────────────────

class ModelTrainer:
    def __init__(self, config: ModelTrainerConfig):
        self.config = config

    def _get_models(self) -> dict:
        rs = self.config.random_state
        models = {
            "RandomForest": (
                RandomForestClassifier(random_state=rs, n_jobs=-1),
                {
                    "n_estimators":    [100, 200],
                    "max_depth":       [10, 20, None],
                    "min_samples_split": [2, 5],
                },
            ),
            "DecisionTree": (
                DecisionTreeClassifier(random_state=rs),
                {
                    "max_depth":         [10, 20, None],
                    "min_samples_split": [2, 5],
                },
            ),
        }
        if XGB_AVAILABLE:
            models["XGBoost"] = (
                XGBClassifier(
                    random_state=rs, eval_metric="logloss",
                    n_jobs=-1, verbosity=0,
                ),
                {
                    "n_estimators":  [100, 200],
                    "learning_rate": [0.05, 0.1],
                    "max_depth":     [5, 7],
                },
            )
        else:
            logger.warning("XGBoost not installed — skipping.")
        return models

    def initiate_model_trainer(
        self,
        train_arr_path: str,
        test_arr_path:  str,
    ) -> str:
        """
        Returns path to the saved best model.
        """
        logger.info("=" * 60)
        logger.info("  Model Training Started")
        logger.info("=" * 60)

        try:
            create_directories([self.config.model_dir])

            train = np.load(train_arr_path)
            test  = np.load(test_arr_path)
            X_train, y_train = train["X"], train["y"]
            X_test,  y_test  = test["X"],  test["y"]

            logger.info(f"X_train: {X_train.shape} | X_test: {X_test.shape}")

            models  = self._get_models()
            best_model      = None
            best_score      = -1.0
            best_name       = ""
            training_report = {}

            for name, (estimator, param_grid) in models.items():
                logger.info(f"Training {name}...")
                gs = GridSearchCV(
                    estimator,
                    param_grid,
                    cv=3,
                    scoring="f1_weighted",
                    n_jobs=-1,
                    verbose=0,
                )
                gs.fit(X_train, y_train)

                test_f1 = f1_score(
                    y_test,
                    gs.best_estimator_.predict(X_test),
                    average="weighted",
                )

                training_report[name] = {
                    "best_params": gs.best_params_,
                    "cv_f1":       round(float(gs.best_score_), 4),
                    "test_f1":     round(float(test_f1), 4),
                }

                logger.info(
                    f"  {name} → CV F1: {gs.best_score_:.4f} | Test F1: {test_f1:.4f} | "
                    f"params: {gs.best_params_}"
                )

                if test_f1 > best_score:
                    best_score = test_f1
                    best_model = gs.best_estimator_
                    best_name  = name

            logger.info(f"\n>>> Best Model: {best_name} (Test F1 = {best_score:.4f})")

            # Save best model
            save_object(self.config.model_path, best_model)

            # Save training report
            report_path = os.path.join(self.config.model_dir, "training_report.json")
            with open(report_path, "w") as f:
                json.dump(training_report, f, indent=2)
            logger.info(f"Training report saved → {report_path}")

            logger.info("=" * 60)
            logger.info("  Model Training Completed")
            logger.info("=" * 60)

            return self.config.model_path

        except Exception as e:
            raise IDSException(e, sys)


# ── Factory ───────────────────────────────────────────────────────────────────

def get_model_trainer_component(config_path: str = "config/config.yaml") -> ModelTrainer:
    cfg = read_yaml(config_path)["model_trainer"]
    config = ModelTrainerConfig(
        model_dir    = cfg["model_dir"],
        model_path   = cfg["model_path"],
        random_state = cfg["random_state"],
    )
    return ModelTrainer(config)