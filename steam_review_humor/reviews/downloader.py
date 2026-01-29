import httpx
import json
import os
import logging
from steam_review_humor.config import HIGH_SCORE_RATIO, API_TIMEOUT

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def download_steam_reviews(
    app_ids: list[int], review_language: str, num_reviews_per_app: int | None
) -> None:
    """
    Downloads Steam reviews and App Info for the specified app IDs and saves them to JSON files.

    :param app_ids: List of Steam App IDs to download reviews for.
    :type app_ids: list[int]
    :param review_language: Language of the reviews to download.
    :type review_language: str
    :param num_reviews_per_app: Number of reviews to download per app. If None, downloads all available reviews.
    :type num_reviews_per_app: int | None
    """
    logger.info("-Starting download of Steam reviews for app IDs: %s", app_ids)
    os.makedirs("data", exist_ok=True)

    for app_id in app_ids:
        # Get App Info for app_id
        app_info = fetch_app_info(app_id)

        with open(f"data/app_{app_id}_info.json", "w", encoding="utf-8") as f:
            json.dump(app_info, f, indent=2, ensure_ascii=False)

        # Fetch Reviews for app_id
        reviews = fetch_reviews_for_app(
            app_id=app_id,
            review_language=review_language,
            num_reviews=num_reviews_per_app,
        )

        logger.info("-Saving reviews to file for app ID: %d", app_id)
        filename = f"data/app_{app_id}_reviews.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(reviews, f, indent=2, ensure_ascii=False)

        logger.info(
            "-Downloaded %d unique reviews for app %d to %s",
            len(reviews["reviews"]),
            app_id,
            filename,
        )


def fetch_reviews_for_app(
    app_id: int, review_language: str, num_reviews: int | None = None
) -> dict:
    """
    Fetches reviews for a given Steam app ID. Uses a hybrid strategy if num_reviews is set. Else, downloads all reviews using 'recent' filter.

    :param app_id: The Steam App ID to fetch reviews for.
    :type app_id: int
    :param review_language: The language of the reviews to fetch.
    :type review_language: str
    :param num_reviews: The number of reviews to fetch. If None, fetches all available reviews.
    :type num_reviews: int | None
    :return: A dictionary containing the fetched reviews.
    :rtype: dict[Any, Any]
    """
    logger.info("--Fetching reviews for app ID: %d", app_id)

    # Keep dictionary for duplication check
    unique_reviews = {}

    # If num_reviews is None, download all available reviews using 'recent' filter
    if num_reviews is None:
        logger.info(
            f"--num_reviews is None. Strategy: Download EVERYTHING using filter='recent'."
        )

        fetch_batch(
            app_id=app_id,
            filter_type="recent",
            language=review_language,
            limit=num_reviews,
            unique_store=unique_reviews,
        )

    # If num_reviews is set, download a subset using all + recent.
    else:
        logger.info(
            f"--num_reviews set to {num_reviews}. Strategy: Hybrid (High Votes + Recent)."
        )

        # Download a percentage using 'all' filter
        limit_all = int(num_reviews * HIGH_SCORE_RATIO)
        fetch_batch(
            app_id=app_id,
            filter_type="all",
            language=review_language,
            limit=limit_all,
            unique_store=unique_reviews,
        )

        # Download remaining using 'recent' filter
        limit_recent = num_reviews - len(unique_reviews)
        if limit_recent > 0:
            fetch_batch(
                app_id=app_id,
                filter_type="recent",
                language=review_language,
                limit=limit_recent,
                unique_store=unique_reviews,
            )

    return {"reviews": list(unique_reviews.values())}


def fetch_batch(
    app_id: int, filter_type: str, language: str, limit: int | None, unique_store: dict
) -> None:
    """
    Helper function to handle pagination and deduplication.
    Updates unique_store in-place.

    :param app_id: The Steam App ID to fetch reviews for.
    :type app_id: int
    :param filter_type: The type of filter to apply when fetching reviews (e.g., "recent", "all").
    :type filter_type: str
    :param language: The language of the reviews to fetch.
    :type language: str
    :param limit: The maximum number of reviews to fetch in this batch.
    :type limit: int | None
    :param unique_store: A dictionary to store unique reviews for deduplication.
    :type unique_store: dict
    """

    url = f"https://store.steampowered.com/appreviews/{app_id}"
    cursor = "*"
    fetched_in_batch = 0

    while fetched_in_batch < limit:
        num_per_page = min(100, limit - fetched_in_batch)

        params = {
            "json": 1,
            "filter": filter_type,
            "language": language,
            "review_type": "all",
            "purchase_type": "all",
            "num_per_page": num_per_page,
            "cursor": cursor,
            "filter_offtopic_activity": 0,
        }

        try:
            response = httpx.get(url, params=params, timeout=API_TIMEOUT)
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError) as e:
            logger.error(f"Error fetching batch ({filter_type}): {e}")
            break

        reviews = data.get("reviews", [])
        new_cursor = data.get("cursor", "")

        if not reviews:
            logger.info(
                f"---No more reviews found for filter '{filter_type}'. Stopping."
            )
            break

        logger.info("---Running deduplication for Batch")
        batch_new_count = 0
        for r in reviews:
            rid = r.get("recommendationid")
            # Only add if we haven't seen this ID before
            if rid and rid not in unique_store:
                unique_store[rid] = r
                batch_new_count += 1

        fetched_in_batch += len(reviews)

        # Cursor safety check (Steam sometimes loops the last cursor)
        if not new_cursor or new_cursor == cursor:
            logger.info(f"---Cursor reached end of stream for filter '{filter_type}'.")
            break

        cursor = new_cursor

        logger.info(
            f"---Batch ({filter_type}): Processed {len(reviews)} items. ({batch_new_count} new unique)."
        )


def fetch_app_info(app_id: int) -> dict:
    """
    Sends a request to the Steam Store API to fetch information about the app.

    :param app_id: The Steam App ID for which to fetch information.
    :type app_id: int
    :return: The app information as a dictionary.
    :rtype: dict[Any, Any]
    """
    logger.info("--Fetching app info for app ID: %d", app_id)
    url = f"https://store.steampowered.com/api/appdetails"
    params = {"appids": app_id, "format": "json"}
    try:
        response = httpx.get(url, params=params, timeout=API_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        app_data = data.get(str(app_id), {})
        if app_data.get("success"):
            return app_data.get("data", {})
    except Exception as e:
        logger.error(f"Failed to fetch app info: {e}")

    return {"error": "Failed to fetch app information"}
