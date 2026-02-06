import csv
import glob
import json
import logging
import os
import re
from datetime import timezone
from typing import List

import numpy as np
import pandas as pd

from steam_review_humor.config import (
    BINARY_LABEL_FUNNY_THRESHOLD,
    DATA_DIR,
    REVIEW_MIN_AGE_THRESHOLD_DAYS,
)

RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "preprocessed")


logger = logging.getLogger(__name__)


def preprocess_steam_data_to_csv() -> None:
    logger.info("Starting preprocessing of Steam review data...")
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    json_files = glob.glob(os.path.join(RAW_DIR, "app_*.json"))

    if not json_files:
        logger.warning(f"No JSON files found in {RAW_DIR}")
        return

    logger.info(f"Found {len(json_files)} raw files to process.")

    all_reviews = []

    for file_path in json_files:
        try:
            reviews_df = process_single_file_to_df(file_path)
            if reviews_df is not None:
                all_reviews.extend(reviews_df)
        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}", exc_info=True)

    if not all_reviews:
        logger.warning("No reviews found to process.")
        return

    logger.info(
        f"Combining reviews from {len(all_reviews)} files into a single DataFrame..."
    )

    df = pd.DataFrame(all_reviews)

    # convert unix timestamps to datetime
    df["review_timestamp_created"] = pd.to_datetime(
        df["review_timestamp_created"], unit="s", utc=True
    )
    df["review_timestamp_updated"] = pd.to_datetime(
        df["review_timestamp_updated"], unit="s", utc=True
    )
    # Calculate review age in days
    df["review_age_days"] = (
        pd.Timestamp.now(tz=timezone.utc) - df["review_timestamp_created"]
    ).dt.days

    # Filter out reviews that are too new and therefore may not have had time to accumulate funny votes
    initial_count = len(df)
    df = df[df["review_age_days"] >= REVIEW_MIN_AGE_THRESHOLD_DAYS]
    filtered_count = len(df)
    logger.info(
        f"Filtered out {initial_count - filtered_count} reviews that were younger than {REVIEW_MIN_AGE_THRESHOLD_DAYS} days old. Remaining reviews: {filtered_count}"
    )

    if df.empty:
        logger.warning(
            "No reviews left after filtering by age. Reducing age threshold may be necessary."
        )
        return

    logger.info("Labeling reviews using multiple strategies based on 'votes_funny'...")

    # Binary Label (Funny if votes_funny > 0)
    df["label_is_funny_binary"] = (
        df["review_votes_funny"] > BINARY_LABEL_FUNNY_THRESHOLD
    ).astype(int)

    # Min-Max Normalization of votes_funny
    min_funny = df["review_votes_funny"].min()
    max_funny = df["review_votes_funny"].max()
    if max_funny > min_funny:
        df["label_funny_minmax"] = (df["review_votes_funny"] - min_funny) / (
            max_funny - min_funny
        )
    else:
        df["label_funny_minmax"] = (
            0.0  # If all reviews have the same number of funny votes, set to 0
        )

    # Log-Scaled Funny Votes
    df["label_funny_log"] = np.log1p(df["review_votes_funny"])

    # Funny Votes Per Day (Velocity)
    df["label_funny_per_day"] = df["review_votes_funny"] / df["review_age_days"]

    # Categorical (Zero-Inflated Bins)
    df["votes_funny_categorical"] = df["review_votes_funny"].apply(categorize_votes)

    logger.info(
        "Added columns label_is_funny_binary, label_funny_minmax, label_funny_log, label_funny_per_day, votes_funny_categorical to DataFrame."
    )

    # Save to file
    output_file = os.path.join(PROCESSED_DIR, "steam_reviews_preprocessed.csv")
    df.to_csv(output_file, index=False, encoding="utf-8")

    logger.info(f"Saved {len(df)} preprocessed reviews to {output_file}")
    logger.info("Preprocessing complete.")


def process_single_file_to_df(file_path: str) -> List | None:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    app_info_raw = data.get("app_info", {})
    reviews_raw = data.get("reviews", [])
    app_id = app_info_raw.get("steam_appid", "unknown")
    app_name = app_info_raw.get("name", f"App {app_id}")

    if not app_info_raw:
        logger.warning(f"Skipping {file_path}: No app info found.")
        return None

    if not reviews_raw:
        logger.warning(f"Skipping {app_name} (ID: {app_id}): No reviews found.")
        return None

    logger.info(
        f"Processing {app_name} (ID: {app_id}) with {len(reviews_raw)} reviews..."
    )

    processed_app_reviews = []

    for r in reviews_raw:
        # flatten the review and author info, and combine with app info for each review
        rev = {
            # review info
            "review_id": r.get("recommendationid"),
            "review_text_cleaned": clean_text(r.get("review")),
            "review_language": r.get("language"),
            "review_timestamp_created": r.get("timestamp_created"),
            "review_timestamp_updated": r.get("timestamp_updated"),
            "review_voted_up": r.get("voted_up"),
            "review_votes_up": r.get("votes_up"),
            "review_votes_funny": r.get("votes_funny"),
            "review_weighted_vote_score": r.get("weighted_vote_score"),
            "review_comment_count": r.get("comment_count"),
            "review_steam_purchase": r.get("steam_purchase"),
            # author info
            "author_steamid": r.get("author", {}).get("steamid"),
            "author_playtime_forever": r.get("author", {}).get("playtime_forever"),
            "author_playtime_at_review": r.get("author", {}).get("playtime_at_review"),
            # app info
            "app_name": app_name,
            "app_required_age": app_info_raw.get("required_age"),
            "app_is_free": app_info_raw.get("is_free"),
            "app_short_description": app_info_raw.get("short_description"),
            "app_developers": app_info_raw.get("developers"),
            "app_publishers": app_info_raw.get("publishers"),
            "app_metacritic_score": app_info_raw.get("metacritic", {}).get("score"),
            "app_categories": [
                c.get("description") for c in app_info_raw.get("categories", [])
            ],
            "app_genres": [
                g.get("description") for g in app_info_raw.get("genres", [])
            ],
            "app_recommendations": app_info_raw.get("recommendations", {}).get("total"),
            "app_release_date": app_info_raw.get("release_date", {}).get("date"),
        }
        processed_app_reviews.append(rev)

    return processed_app_reviews


def clean_text(text: str) -> str:
    """
    Removes Steam BBCode (e.g., [b], [h1], [table]) from text.
    """
    if not isinstance(text, str):
        return ""
    # Remove tags like [b], [/b], [h1], [url=...]
    # Pattern explanation: \[.*?\] matches anything inside brackets
    text = re.sub(r"\[.*?\]", "", text)
    # Replace newlines with \n character
    text = re.sub(r"\n+", "\\n", text)
    # Collapse multiple spaces into single space
    text = re.sub(r" +", " ", text).strip()

    return text


def categorize_votes(votes):
    if votes == 0:
        return 0  # Not Funny
    elif votes == 1:
        return 1  # Slightly Funny
    elif votes <= 5:
        return 2  # Moderately Funny
    elif votes <= 10:
        return 3  # Very Funny
    else:
        return 4  # Hilarious
