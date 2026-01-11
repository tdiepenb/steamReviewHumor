import logging
import config
import json
from reviews.downloader import (
    download_steam_reviews,
    read_app_info_from_file,
    read_reviews_from_file,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():

    logger.info("Starting Steam Review Downloader with the following configuration:")
    logger.info("App IDs: %s", config.APP_IDS)
    logger.info("Review Language: %s", config.REVIEW_LANGUAGE)
    logger.info("Number of Reviews per App: %s", config.NUM_REVIEWS_PER_APP)

    download_steam_reviews(
        app_ids=config.APP_IDS,
        review_language=config.REVIEW_LANGUAGE,
        num_reviews_per_app=config.NUM_REVIEWS_PER_APP,
    )

    # reviews = read_reviews_from_file("data/app_2807960_reviews.json")
    # app_info = read_app_info_from_file("data/app_2807960_info.json")
    # logger.warning("App Info: %s", json.dumps(app_info, indent=4, sort_keys=True))
    # logger.warning("Number of Reviews: %d", len(reviews.get("reviews", [])))


if __name__ == "__main__":
    main()
