# List of Steam App IDs to download reviews for
APP_IDS: list[int] = [
    2807960,
    # 1903340
]

# Language for the reviews to be downloaded
REVIEW_LANGUAGE: str = "english"

# Number of reviews to download per app (None for all available reviews)
NUM_REVIEWS_PER_APP: int | None = 5053

# Percentage of the total download limit to dedicate to 'all' (high/mid votes).
# The remainder will be used for 'recent' (zeros).
# 0.6 means 60% high/mid votes, 40% recent/zero votes.
HIGH_SCORE_RATIO = 0.6

# Number of days a review must exist to be considered "settled" (not too new).
# Reviews with 0 funny votes younger than this will be discarded.
REVIEW_AGE_THRESHOLD_DAYS = 60

# Timeout for API requests in seconds (Steam API can be slow)
API_TIMEOUT = 10.0
