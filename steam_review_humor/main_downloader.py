import logging

from steam_review_humor.reviews.downloader import download_steam_reviews

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    download_steam_reviews()


if __name__ == "__main__":
    main()
