import httpx
import json
import os
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def download_steam_reviews(
    app_ids: list[int], review_language: str, num_reviews_per_app: int | None
) -> dict | None:
    logger.info("Starting download of Steam reviews for app IDs: %s", app_ids)
    os.makedirs("data", exist_ok=True)
    logger.info("Created data directory if it did not exist.")

    for app_id in app_ids:
        logger.info("Fetching app info for app ID: %d", app_id)
        app_info = fetch_app_info(app_id)

        logger.info("Storing app info for app ID: %d", app_id)
        with open(f"data/app_{app_id}_info.json", "w", encoding="utf-8") as f:
            json.dump(app_info, f, indent=2, ensure_ascii=False)

        logger.info("Fetching reviews for app ID: %d", app_id)
        reviews = fetch_reviews_for_app(
            app_id=app_id,
            review_language=review_language,
            num_reviews=num_reviews_per_app,
        )

        logger.info("Saving reviews to file for app ID: %d", app_id)
        filename = f"data/app_{app_id}_reviews.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(reviews, f, indent=2, ensure_ascii=False)

        logger.info("Downloaded reviews for app %d to %s", app_id, filename)


def fetch_reviews_for_app(
    app_id: int, review_language: str, num_reviews: int | None = None
) -> dict:
    url = "https://store.steampowered.com/appreviews/"
    all_reviews = []
    cursor = "*"
    page_count = 0
    data = {}

    while True:
        if num_reviews and len(all_reviews) >= num_reviews:
            break

        num_per_page = 100
        if num_reviews:
            num_per_page = min(100, num_reviews - len(all_reviews))

        params = {
            "json": 1,
            "filter": "all",
            "language": review_language,
            "day_range": 9223372036854775807,
            "review_type": "all",
            "purchase_type": "all",
            "num_per_page": num_per_page,
            "cursor": cursor,
        }

        response = httpx.get(url + str(app_id), params=params)
        response.raise_for_status()
        data = response.json()
        reviews = data.get("reviews", [])

        if not reviews:
            print(f"No more reviews found after {page_count} pages")
            break

        all_reviews.extend(reviews)
        cursor = data.get("cursor", "")
        page_count += 1

        logger.info(
            "Fetched page %d for app ID: %d, total reviews fetched: %d",
            page_count,
            app_id,
            len(all_reviews),
        )

        if not cursor:
            print(f"Reached end of reviews after {page_count} pages")
            break

    logger.info("Fetched %d reviews for app ID: %d", len(all_reviews), app_id)
    return {"reviews": all_reviews[:num_reviews]}


def fetch_app_info(app_id: int) -> dict:
    url = f"https://store.steampowered.com/api/appdetails"
    params = {"appids": app_id, "format": "json"}

    response = httpx.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    app_data = data.get(str(app_id), {})
    if app_data.get("success"):
        return app_data.get("data", {})
    else:
        return {"error": "Failed to fetch app information"}


def read_reviews_from_file(filepath: str) -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def read_app_info_from_file(filepath: str) -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)
