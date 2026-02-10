import logging
import os
from datetime import datetime

from steam_review_humor.reviews.steam_to_csv_converter import steam_data_to_csv

log_dir = "log/steam_to_csv_converter"
os.makedirs(log_dir, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = os.path.join(log_dir, f"steam_reviews_to_csv_{timestamp}.log")

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
    steam_data_to_csv()


if __name__ == "__main__":
    main()
