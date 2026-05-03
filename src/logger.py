import logging
import os
from datetime import datetime

LOGS_DIR = "logs"
os.makedirs(LOGS_DIR, exist_ok=True)

LOG_FILE_PATH = os.path.join(
    LOGS_DIR,
    f"{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"
)

logging.basicConfig(
    filename=LOG_FILE_PATH,
    format="[ %(asctime)s ] %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# also stream to console
console_handler = logging.StreamHandler()
console_handler.setFormatter(
    logging.Formatter("[ %(asctime)s ] %(name)s - %(levelname)s - %(message)s")
)
logging.getLogger().addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)