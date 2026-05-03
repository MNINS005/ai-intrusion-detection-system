"""
Model Evaluation Component
───────────────────────────
Pure metrics — no plots, no matplotlib, no seaborn.
Saves:
  artifacts/reports/metrics.json                → all scalar metrics
  artifacts/reports/classification_report.json  → per-class breakdown
  artifacts/reports/confusion_matrix.csv        → raw CM as CSV (readable in Excel/pandas)
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from dataclasses import dataclass

from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
    matthews_corrcoef,
    balanced_accuracy_score,
    cohen_kappa_score,
)

from src.logger import get_logger
from src.exception import IDSException
from src.utils.utils import read_yaml, load_object, create_directories
from src.constants import CLASS_NAMES

logger = get_logger(__name__)


# ── Config dataclass ──────────────────────────────────────────────────────────

@dataclass
class ModelEvaluationConfig:
    reports_dir:     str
    metrics_path:    str
    clf_report_path: str
    cm_path:         str


# ── Component ─────────────────────────────────────────────────────────────────

class ModelEvaluation:
    def __init__(self, config: ModelEvaluationConfig):
        self.config = config

    # ── private helpers ───────────────────────────────────────────────────────

    def _compute_roc_auc(self, model, X_test, y_test, is_binary: bool) -> dict:
        result = {}
        if not hasattr(model, "predict_proba"):
            return result
        try:
            proba = model.predict_proba(X_test)
            if is_binary:
                result["roc_auc"] = round(float(roc_auc_score(y_test, proba[:, 1])), 4)
            else:
                result["roc_auc_ovr_weighted"] = round(float(
                    roc_auc_score(y_test, proba, multi_class="ovr", average="weighted")
                ), 4)
                result["roc_auc_ovr_macro"] = round(float(
                    roc_auc_score(y_test, proba, multi_class="ovr", average="macro")
                ), 4)
        except Exception as ex:
            logger.warning(f"ROC-AUC computation skipped: {ex}")
        return result

    def _compute_per_class_metrics(self, y_true, y_pred, classes: list) -> dict:
        """
        Manual per-class TP/FP/FN/TN + derived metrics.
        Gives False Positive Rate (FPR) which sklearn's report doesn't include —
        critical for IDS evaluation.
        """
        result = {}
        for cls in classes:
            label   = CLASS_NAMES.get(cls, str(cls))
            tp = int(((y_pred == cls) & (y_true == cls)).sum())
            fp = int(((y_pred == cls) & (y_true != cls)).sum())
            fn = int(((y_pred != cls) & (y_true == cls)).sum())
            tn = int(((y_pred != cls) & (y_true != cls)).sum())
            support = int((y_true == cls).sum())

            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec  = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1   = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
            fpr  = fp / (fp + tn) if (fp + tn) > 0 else 0.0   # False Positive Rate

            result[label] = {
                "precision":         round(prec, 4),
                "recall":            round(rec, 4),        # also = Detection Rate
                "f1_score":          round(f1, 4),
                "false_positive_rate": round(fpr, 4),
                "tp": tp, "fp": fp, "fn": fn, "tn": tn,
                "support": support,
            }
        return result

    def _save_confusion_matrix(self, y_true, y_pred, classes: list):
        cm     = confusion_matrix(y_true, y_pred, labels=classes)
        labels = [CLASS_NAMES.get(c, str(c)) for c in classes]
        cm_df  = pd.DataFrame(cm, index=labels, columns=labels)
        cm_df.index.name = "Actual \\ Predicted"
        cm_df.to_csv(self.config.cm_path)
        logger.info(f"Confusion matrix CSV saved → {self.config.cm_path}")
        logger.info(f"\nConfusion Matrix:\n{cm_df.to_string()}")

    def _log_summary(self, metrics: dict):
        sep = "─" * 48
        logger.info(f"\n{sep}")
        logger.info("  EVALUATION SUMMARY")
        logger.info(sep)
        logger.info(f"  Accuracy               : {metrics['accuracy']}")
        logger.info(f"  Balanced Accuracy       : {metrics['balanced_accuracy']}")
        logger.info(f"  F1  (weighted)         : {metrics['f1_weighted']}")
        logger.info(f"  F1  (macro)            : {metrics['f1_macro']}")
        logger.info(f"  F1  (micro)            : {metrics['f1_micro']}")
        logger.info(f"  Precision (weighted)   : {metrics['precision_weighted']}")
        logger.info(f"  Precision (macro)      : {metrics['precision_macro']}")
        logger.info(f"  Recall    (weighted)   : {metrics['recall_weighted']}")
        logger.info(f"  Recall    (macro)      : {metrics['recall_macro']}")
        logger.info(f"  MCC                    : {metrics['matthews_corrcoef']}")
        logger.info(f"  Cohen Kappa            : {metrics['cohen_kappa']}")
        if "roc_auc" in metrics:
            logger.info(f"  ROC-AUC (binary)       : {metrics['roc_auc']}")
        if "roc_auc_ovr_weighted" in metrics:
            logger.info(f"  ROC-AUC OvR (weighted) : {metrics['roc_auc_ovr_weighted']}")
            logger.info(f"  ROC-AUC OvR (macro)    : {metrics['roc_auc_ovr_macro']}")
        logger.info(sep)
        logger.info("  Per-Class FPR (False Positive Rates)")
        logger.info(sep)
        for cls_name, vals in metrics["per_class"].items():
            logger.info(
                f"  {cls_name:<12} | DR={vals['recall']:.4f} | "
                f"FPR={vals['false_positive_rate']:.4f} | "
                f"F1={vals['f1_score']:.4f} | support={vals['support']}"
            )
        logger.info(sep)

    # ── main entry point ──────────────────────────────────────────────────────

    def initiate_model_evaluation(
        self,
        model_path:    str,
        test_arr_path: str,
    ) -> dict:
        """
        Returns full metrics dict.
        Artifacts saved:
          - metrics.json
          - classification_report.json
          - confusion_matrix.csv
        """
        logger.info("=" * 60)
        logger.info("  Model Evaluation Started")
        logger.info("=" * 60)

        try:
            create_directories([self.config.reports_dir])

            model  = load_object(model_path)
            data   = np.load(test_arr_path)
            X_test = data["X"]
            y_test = data["y"]

            y_pred    = model.predict(X_test)
            classes   = sorted(np.unique(y_test).tolist())
            is_binary = len(classes) == 2

            # ── scalar metrics ────────────────────────────────────────────────
            metrics = {
                "accuracy":            round(float(accuracy_score(y_test, y_pred)), 4),
                "balanced_accuracy":   round(float(balanced_accuracy_score(y_test, y_pred)), 4),
                "f1_weighted":         round(float(f1_score(y_test, y_pred, average="weighted")), 4),
                "f1_macro":            round(float(f1_score(y_test, y_pred, average="macro")), 4),
                "f1_micro":            round(float(f1_score(y_test, y_pred, average="micro")), 4),
                "precision_weighted":  round(float(precision_score(y_test, y_pred, average="weighted", zero_division=0)), 4),
                "precision_macro":     round(float(precision_score(y_test, y_pred, average="macro",    zero_division=0)), 4),
                "recall_weighted":     round(float(recall_score(y_test, y_pred, average="weighted", zero_division=0)), 4),
                "recall_macro":        round(float(recall_score(y_test, y_pred, average="macro",    zero_division=0)), 4),
                "matthews_corrcoef":   round(float(matthews_corrcoef(y_test, y_pred)), 4),
                "cohen_kappa":         round(float(cohen_kappa_score(y_test, y_pred)), 4),
                "total_samples":       int(len(y_test)),
                "num_classes":         len(classes),
                "is_binary":           is_binary,
            }

            # ── ROC-AUC ───────────────────────────────────────────────────────
            metrics.update(self._compute_roc_auc(model, X_test, y_test, is_binary))

            # ── per-class breakdown with FPR ──────────────────────────────────
            metrics["per_class"] = self._compute_per_class_metrics(y_test, y_pred, classes)

            # ── confusion matrix CSV ──────────────────────────────────────────
            self._save_confusion_matrix(y_test, y_pred, classes)

            # ── save metrics.json ─────────────────────────────────────────────
            with open(self.config.metrics_path, "w") as f:
                json.dump(metrics, f, indent=2)
            logger.info(f"Metrics JSON saved → {self.config.metrics_path}")

            # ── classification report JSON ────────────────────────────────────
            clf_report = classification_report(
                y_test, y_pred,
                target_names=[CLASS_NAMES.get(c, str(c)) for c in classes],
                output_dict=True,
                zero_division=0,
            )
            with open(self.config.clf_report_path, "w") as f:
                json.dump(clf_report, f, indent=2)
            logger.info(f"Classification report JSON saved → {self.config.clf_report_path}")

            # ── log full text report ──────────────────────────────────────────
            clf_str = classification_report(
                y_test, y_pred,
                target_names=[CLASS_NAMES.get(c, str(c)) for c in classes],
                zero_division=0,
            )
            logger.info(f"\nClassification Report:\n{clf_str}")

            self._log_summary(metrics)

            logger.info("=" * 60)
            logger.info("  Model Evaluation Completed")
            logger.info("=" * 60)

            return metrics

        except Exception as e:
            raise IDSException(e, sys)


# ── Factory ───────────────────────────────────────────────────────────────────

def get_model_evaluation_component(config_path: str = "config/config.yaml") -> ModelEvaluation:
    cfg = read_yaml(config_path)["model_evaluation"]
    config = ModelEvaluationConfig(
        reports_dir     = cfg["reports_dir"],
        metrics_path    = cfg["metrics_path"],
        clf_report_path = os.path.join(cfg["reports_dir"], "classification_report.json"),
        cm_path         = os.path.join(cfg["reports_dir"], "confusion_matrix.csv"),
    )
    return ModelEvaluation(config)