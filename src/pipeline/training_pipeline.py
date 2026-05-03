"""
Training Pipeline
──────────────────
Chains all 5 components:
  Ingestion → Preprocessing → Transformation → Training → Evaluation
"""

import sys
from src.logger import get_logger
from src.exception import IDSException

from src.components.data_ingestion      import get_data_ingestion_component
from src.components.data_preprocessing  import get_data_preprocessing_component
from src.components.data_transformation import get_data_transformation_component
from src.components.model_trainer       import get_model_trainer_component
from src.components.model_evaluation    import get_model_evaluation_component

logger = get_logger(__name__)

CONFIG_PATH = "config/config.yaml"


class TrainingPipeline:
    def run(self):
        logger.info("╔══════════════════════════════════════════╗")
        logger.info("║     IDS Training Pipeline — NSL-KDD     ║")
        logger.info("╚══════════════════════════════════════════╝")

        try:
            # Stage 1 ─ Data Ingestion
            logger.info("\n[STAGE 1/5] Data Ingestion")
            ingestion = get_data_ingestion_component(CONFIG_PATH)
            train_path, test_path = ingestion.initiate_data_ingestion()

            # Stage 2 ─ Data Preprocessing
            logger.info("\n[STAGE 2/5] Data Preprocessing")
            preprocessing = get_data_preprocessing_component(CONFIG_PATH)
            train_path, test_path = preprocessing.initiate_data_preprocessing(train_path, test_path)

            # Stage 3 ─ Data Transformation
            logger.info("\n[STAGE 3/5] Data Transformation")
            transformation = get_data_transformation_component(CONFIG_PATH)
            train_arr, test_arr, preprocessor_path = transformation.initiate_data_transformation(train_path, test_path)

            # Stage 4 ─ Model Training
            logger.info("\n[STAGE 4/5] Model Training")
            trainer = get_model_trainer_component(CONFIG_PATH)
            model_path = trainer.initiate_model_trainer(train_arr, test_arr)

            # Stage 5 ─ Model Evaluation
            logger.info("\n[STAGE 5/5] Model Evaluation")
            evaluator = get_model_evaluation_component(CONFIG_PATH)
            metrics = evaluator.initiate_model_evaluation(model_path, test_arr)

            logger.info("\n╔══════════════════════════════════════════╗")
            logger.info("║         Pipeline Completed ✓             ║")
            logger.info(f"║  F1  (weighted) : {metrics['f1_weighted']:<22}║")
            logger.info(f"║  Accuracy       : {metrics['accuracy']:<22}║")
            logger.info("╚══════════════════════════════════════════╝")

            return metrics

        except Exception as e:
            raise IDSException(e, sys)


if __name__ == "__main__":
    pipeline = TrainingPipeline()
    pipeline.run()