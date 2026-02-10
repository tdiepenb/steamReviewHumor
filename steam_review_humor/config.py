###############################
# Shared Configurations
###############################

# Root Data directory for storing data files. The files will be stored in subdirectories under this path.
DATA_DIR: str = "data"

# List of Steam App IDs to download reviews for
APP_IDS: list[int] = [
    2807960,  # Battlefield 6
    1903340,  # Clair Obscur: Expedition 33
    397540,  # Borderlands 3
    1808500,  # ARC Raiders
    1245620,  # ELDEN RING
    2592160,  # Dispatch
    1091500,  # Cyberpunk 2077
    377160,  # Fallout 4
    3405340,  # Megabonk
    1942280,  # Brotato
    1174180,  # Red_Dead_Redemption_2
    2694490,  # Path_of_Exile_2
    1086940,  # Baldurs_Gate_3
    548430,  # Deep_Rock_Galactic
    1085660,  # Destiny_2
    1149460,  # ICARUS
    2001120,  # Split_Fiction
    427520,  # Factorio
    916440,  # Anno_1800
    1222700,  # A_Way_Out
    1774580,  # STAR_WARS_Jedi_Survivor
    1455840,  # Dorfromantik
    837470,  # Untitled_Goose_Game
]


###############################
# Download Configurations
###############################


# Language for the reviews to be downloaded. Pass "all" for all languages. Check "https://partner.steamgames.com/doc/store/localization/languages" for supported languages.
REVIEW_LANGUAGE: str = "english"

# Number of reviews to download per app (None for all available reviews)
NUM_REVIEWS_PER_APP: int | None = 50000

# Disable early stopping for the 'recent' filter portion of the download during the Hybrid strategy when no new reviews are found in a batch. If True, the downloader will continue fetching until the portion of recent reviews are downloaded or the API limit is reached. If False, the downloader will stop early after a set number of retries when no new reviews are found. Set this to true for older games as the 'all' filters results may overlap significantly with 'recent' reviews.
DISABLE_EARLY_STOPPING: bool = True

# Number of retries for when no new reviews are found before early stopping
NUM_RETRY_BEFORE_EARLY_STOPPING: int = 10

# Percentage of the total download limit to dedicate to 'all'. The remainder will be used for 'recent'. 0.6 means 60% high/mid votes, 40% recent/zero votes. Will be ignored if NUM_REVIEWS_PER_APP is None.
HIGH_SCORE_RATIO: float = 0.5

# Timeout for API requests in seconds
API_TIMEOUT: float = 10.0


###############################
# Preprocesssing Configurations
###############################

# Number of days a review must exist to be considered "settled" (not too new). Reviews with 0 funny votes younger than this will be discarded.
REVIEW_MIN_AGE_THRESHOLD_DAYS: int = 30

# Minimum number (>=) of funny votes for a review to be labeled as "funny" in the binary labeling strategy
BINARY_LABEL_FUNNY_THRESHOLD: int = 1
