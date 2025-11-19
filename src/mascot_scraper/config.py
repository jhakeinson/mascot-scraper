import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ------------------------------------------------------------------- #
# Configuration from environment variables
# ------------------------------------------------------------------- #
START_URL = os.getenv("START_URL", "https://app.withmascot.com/login")
MAX_PAGES = int(os.getenv("MAX_PAGES", "10"))
CONCURRENCY = int(os.getenv("CONCURRENCY", "1"))  # simultaneous browser tabs
RATE_LIMIT = float(os.getenv("RATE_LIMIT", "1.0"))  # seconds between requests (same domain)

# Login Credentials
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

# Browser Configuration
USER_DATA_DIR = os.getenv("USER_DATA_DIR", "/tmp/playwright-chrome-profile")
HEADLESS = os.getenv("HEADLESS", "True").lower() in ("true", "1", "yes")

# Output Configuration
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
