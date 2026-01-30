import logging
import os
from datetime import datetime

from steam_review_humor.reviews.downloader import download_steam_reviews

# Create log directory if it doesn't exist
log_dir = "log"
os.makedirs(log_dir, exist_ok=True)

# Create timestamped log filename
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = os.path.join(log_dir, f"steam_reviews_downloader_{timestamp}.log")

# Configure logging with both console and file output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler(log_filename, encoding='utf-8')  # File output
    ]
)
logger = logging.getLogger(__name__)


def main():
    download_steam_reviews()


if __name__ == "__main__":
    main()
