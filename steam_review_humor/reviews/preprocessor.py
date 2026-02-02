import glob
import json
import logging
import os
import re
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from steam_review_humor.config import (
    APP_INFO_KEYS_TO_KEEP,
    DATA_DIR,
    REVIEW_MIN_AGE_THRESHOLD_DAYS,
)

logger = logging.getLogger(__name__)


def preprocess_steam_data() -> None:
    raw_dir = os.path.join(DATA_DIR, "raw")
    processed_dir = os.path.join(DATA_DIR, "preprocessed")
    os.makedirs(processed_dir, exist_ok=True)

    json_files = glob.glob(os.path.join(raw_dir, "app_*.json"))

    if not json_files:
        logger.warning(f"No JSON files found in {raw_dir}")
        return

    logger.info(f"Found {len(json_files)} raw files to process.")

    for file_path in json_files:
        try:
            process_single_file(file_path, processed_dir)
        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}", exc_info=True)


def process_single_file(file_path: str, output_dir: str) -> None:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    app_info_raw = data.get("app_info", {})
    reviews_raw = data.get("reviews", [])
    app_id = app_info_raw.get("steam_appid", "unknown")
    game_name = app_info_raw.get("name", f"App {app_id}")

    if not reviews_raw:
        logger.warning(f"Skipping {game_name} (ID: {app_id}): No reviews found.")
        return

    logger.info(f"Processing {game_name} (ID: {app_id})...")

    # --- 1. Process App Info ---
    clean_app_info = extract_app_info(app_info_raw)

    # --- 2. Process Reviews (Pandas) ---
    df = pd.DataFrame(reviews_raw)

    # A. Timestamp Formatting (Unix -> UTC Datetime)
    # Steam gives unix timestamps (seconds). We convert to UTC.
    time_cols = ["timestamp_created", "timestamp_updated", "last_played"]
    for col in time_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], unit="s", utc=True)

    # B. Calculate Age & Filter
    now_utc = pd.Timestamp.now(tz=timezone.utc)
    df["days_old"] = (now_utc - df["timestamp_created"]).dt.days

    # Clip days_old to 1 to avoid division by zero later
    df["days_old"] = df["days_old"].clip(lower=1)

    # Filter: Discard young reviews
    initial_count = len(df)
    df = df[df["days_old"] >= REVIEW_MIN_AGE_THRESHOLD_DAYS].copy()
    dropped_count = initial_count - len(df)

    if dropped_count > 0:
        logger.info(
            f"   - Dropped {dropped_count} reviews younger than {REVIEW_MIN_AGE_THRESHOLD_DAYS} days."
        )
    if df.empty:
        logger.warning(
            f"   - All reviews filtered out for {game_name}. Skipping CSV save."
        )
        return

    # C. Feature Engineering: Funny Metrics
    # Funny Votes Per Day (Velocity)
    df["funny_votes_per_day"] = df["votes_funny"] / df["days_old"]

    # Normalized Funny Score (0 to 1 Log Scale)
    # We use log1p (log(x+1)) to handle the "power law" distribution of votes
    df["log_funny"] = np.log1p(df["votes_funny"])
    max_log_val = df["log_funny"].max()

    if max_log_val > 0:
        df["funny_score_norm"] = df["log_funny"] / max_log_val
    else:
        df["funny_score_norm"] = 0.0

    # D. Text Cleaning (Remove BBCode)
    if "review" in df.columns:
        df["review_clean"] = df["review"].apply(clean_bbcode)

    # --- 3. Merge App Info ---
    # Broadcast the app info columns to every row in the dataframe
    for key, value in clean_app_info.items():
        df[f"game_{key}"] = str(value)  # Convert complex types to string for CSV safety

    # --- 4. Save to CSV ---
    output_filename = f"app_{app_id}_preprocessed.csv"
    output_path = os.path.join(output_dir, output_filename)

    # Select and Reorder columns for clarity
    cols_to_save = [
        "recommendationid",
        "game_name",
        "funny_score_norm",
        "votes_funny",
        "funny_votes_per_day",
        "days_old",
        "voted_up",
        "review_clean",
        "review",  # Keep both clean and raw just in case
        "timestamp_created",
    ]
    # Add dynamic game info cols
    cols_to_save.extend(
        [c for c in df.columns if c.startswith("game_") and c != "game_name"]
    )

    # Only save columns that actually exist (intersection)
    final_cols = [c for c in cols_to_save if c in df.columns]

    df[final_cols].to_csv(output_path, index=False, encoding="utf-8")
    logger.info(f"   - Saved {len(df)} rows to {output_filename}")


def extract_app_info(app_info: dict) -> dict:
    """
    Extracts relevant metadata from the nested app_info dictionary
    based on the configuration whitelist.
    """
    cleaned = {}

    # simple extraction
    for key in APP_INFO_KEYS_TO_KEEP:
        if key in app_info:
            val = app_info[key]

            # Special handling for common Steam API nested structures
            if key == "genres" and isinstance(val, list):
                # Extract just the names: [{'id': '1', 'description': 'Action'}, ...] -> "Action, RPG"
                val = ", ".join([g.get("description", "") for g in val])

            elif key == "categories" and isinstance(val, list):
                val = ", ".join([c.get("description", "") for c in val])

            elif key == "metacritic" and isinstance(val, dict):
                val = val.get("score", "")

            cleaned[key] = val

    return cleaned


def clean_bbcode(text: str) -> str:
    """
    Removes Steam BBCode (e.g., [b], [h1], [table]) from text.
    """
    if not isinstance(text, str):
        return ""

    # Remove tags like [b], [/b], [h1], [url=...]
    # Pattern explanation: \[.*?\] matches anything inside brackets
    text = re.sub(r"\[.*?\]", "", text)

    # Collapse multiple spaces/newlines into single space
    text = re.sub(r"\s+", " ", text).strip()

    return text
