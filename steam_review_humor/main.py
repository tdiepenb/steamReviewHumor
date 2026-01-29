import logging
import steam_review_humor.config as config
import json
from steam_review_humor.reviews.downloader import download_steam_reviews

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


if __name__ == "__main__":
    main()
