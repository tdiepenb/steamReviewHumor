import json
import logging
import os
from datetime import datetime

import httpx

from steam_review_humor.config import (
    API_TIMEOUT,
    APP_IDS,
    DATA_DIR,
    DISABLE_EARLY_STOPPING,
    HIGH_SCORE_RATIO,
    NUM_RETRY_BEFORE_EARLY_STOPPING,
    NUM_REVIEWS_PER_APP,
    REVIEW_LANGUAGE,
)

logger = logging.getLogger(__name__)

# Suppress httpx and httpcore logs unless explicitly needed
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


def download_steam_reviews() -> None:
    logger.info("Starting Steam Reviews Download...")
    logger.info("Starting Steam Review Downloader with the following configuration:")
    logger.info("App IDs: %s", APP_IDS)
    logger.info("Review Language: %s", REVIEW_LANGUAGE)
    logger.info("Number of Reviews per App: %s", NUM_REVIEWS_PER_APP)
    logger.info("High Score Ratio: %.2f", HIGH_SCORE_RATIO)
    logger.info("Disable Early Stopping: %s", DISABLE_EARLY_STOPPING)
    logger.info(
        "Number of Retries before Early Stopping: %d", NUM_RETRY_BEFORE_EARLY_STOPPING
    )
    logger.info("API Timeout: %.2f seconds", API_TIMEOUT)
    logger.info("Data Directory: %s/raw", DATA_DIR)

    os.makedirs(f"{DATA_DIR}/raw", exist_ok=True)

    for app_id in APP_IDS:
        # Get App Info for app_id
        app_meta_data = fetch_app_info(app_id)

        # Fetch Reviews for app_id
        reviews_data = fetch_reviews_for_app(
            app_id=app_id,
            review_language=REVIEW_LANGUAGE,
            num_reviews=NUM_REVIEWS_PER_APP,
        )

        data = {
            "downloaded_at": datetime.now().isoformat(),
            "review_count_downloaded": len(reviews_data["reviews"]),
        }
        data["app_info"] = app_meta_data
        data["reviews"] = reviews_data["reviews"]

        game_title = app_meta_data.get("name", f"App_{app_id}")
        filename = f"{DATA_DIR}/raw/app_{app_id}.json"

        logger.info(
            f"-Saving complete dataset for '{game_title}' with ID {app_id} to {filename}"
        )

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(
            f"-Success. Saved {len(reviews_data['reviews'])} reviews + metadata."
        )
        logger.info("Download complete.")


def fetch_reviews_for_app(
    app_id: int, review_language: str, num_reviews: int | None = None
) -> dict:
    """
    Fetches reviews for a given Steam app ID. Uses a hybrid strategy if num_reviews is set. Else, downloads all reviews using 'recent' filter.
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
                disable_early_stopping=DISABLE_EARLY_STOPPING,
            )

    return {"reviews": list(unique_reviews.values())}


def fetch_batch(
    app_id: int,
    filter_type: str,
    language: str,
    limit: int | None,
    unique_store: dict,
    disable_early_stopping: bool = False,
) -> None:
    """
    Helper function to handle pagination and deduplication.
    Updates unique_store in-place.
    """

    url = f"https://store.steampowered.com/appreviews/{app_id}"
    cursor = "*"
    fetched_in_batch = 0
    retry_count = 0

    logger.info(
        f"---Starting batch fetch for filter '{filter_type}' with limit={limit}"
    )

    while limit is None or fetched_in_batch < limit:
        num_per_page = 100 if limit is None else min(100, limit - fetched_in_batch)

        params = {
            "json": 1,
            "filter": filter_type,
            "language": language,
            "review_type": "all",
            "purchase_type": "all",
            "num_per_page": str(num_per_page),
            "cursor": cursor,
            "filter_offtopic_activity": 0,
        }

        # when using "all" filter, set day_range to 365 (max according to Steam API) to get recent high-score reviews older than default 30 days
        if filter_type == "all":
            params["day_range"] = "365"

        try:
            response = httpx.get(url, params=params, timeout=API_TIMEOUT)
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError) as e:
            logger.error(f"Error fetching batch ({filter_type}): {e}")
            break

        reviews = data.get("reviews", [])
        new_cursor = data.get("cursor", "")

        # if not reviews:
        #     logger.info(
        #         f"---No more reviews found for filter '{filter_type}'. Stopping."
        #     )
        #     break

        logger.debug("---Running deduplication for Batch")
        batch_new_count = 0
        for r in reviews:
            rid = r.get("recommendationid")
            # Only add if we haven't seen this ID before
            if rid and rid not in unique_store:
                unique_store[rid] = r
                batch_new_count += 1

        if len(reviews) > 0 and batch_new_count == 0 and not disable_early_stopping:
            logger.info(
                f"---Batch returned {len(reviews)} items, but ALL were duplicates. Retry {retry_count}/{NUM_RETRY_BEFORE_EARLY_STOPPING}."
            )
            retry_count += 1
            if retry_count >= NUM_RETRY_BEFORE_EARLY_STOPPING:
                logger.info(f"---Stopping early.")
                break
        else:
            retry_count = 0  # reset retry count on successful new data

        fetched_in_batch += len(reviews)

        # Cursor safety check (Steam sometimes loops the last cursor)
        if not new_cursor or new_cursor == cursor:
            logger.info(f"---Cursor reached end of stream for filter '{filter_type}'.")
            break

        cursor = new_cursor

        logger.info(
            f"---Batch ({filter_type}): Processed {len(reviews):03d} items. ({batch_new_count:03d} new unique). Total unique so far: {len(unique_store)}"
        )


def fetch_app_info(app_id: int) -> dict:
    """
    Sends a request to the Steam Store API to fetch information about the app.
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
            logger.info(
                f"---Successfully fetched app info for app ID: {app_id} with name: {app_data.get('data', {}).get('name', 'Unknown')}"
            )
            return app_data.get("data", {})
    except Exception as e:
        logger.error(f"Failed to fetch app info: {e}")

    return {"error": "Failed to fetch app information"}
