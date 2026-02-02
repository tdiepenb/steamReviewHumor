import logging
import os
from datetime import datetime

# Import the new function
from steam_review_humor.reviews.preprocessor import preprocess_steam_data

# Create log directory if it doesn't exist
log_dir = "log/preprocessing"
os.makedirs(log_dir, exist_ok=True)

# Create timestamped log filename
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = os.path.join(log_dir, f"steam_reviews_preprocessing_{timestamp}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_filename, encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def main():
    logger.info("Starting Data Preprocessing...")
    preprocess_steam_data()
    logger.info("Preprocessing complete.")


if __name__ == "__main__":
    main()
