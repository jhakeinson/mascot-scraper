# Mascot Scraper

A web scraper for extracting form data from Mascot using Playwright.

## Configuration

The project uses environment variables for configuration. Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

Then edit `.env` with your credentials and preferences:

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `START_URL` | The login URL for Mascot | `https://app.withmascot.com/login` |
| `MAX_PAGES` | Maximum number of pages to scrape | `10` |
| `CONCURRENCY` | Number of simultaneous browser tabs | `1` |
| `RATE_LIMIT` | Seconds between requests (same domain) | `1.0` |
| `USERNAME` | Your Mascot login email | **Required** |
| `PASSWORD` | Your Mascot login password | **Required** |
| `USER_DATA_DIR` | Chrome profile directory | `/tmp/playwright-chrome-profile` |
| `HEADLESS` | Run browser in headless mode | `True` |

**Important:** Never commit your `.env` file to version control. It contains sensitive credentials.

## Installation

### Local Installation

```bash
# Install dependencies using uv
uv sync

# Install Playwright browsers
uv run playwright install chromium
```

### Docker Installation

```bash
# Make sure you have Docker and Docker Compose installed
# No additional installation needed - Docker handles everything
```

## Usage

### Running Locally

```bash
# Run the scraper
uv run python scraper.py
```

### Running with Docker

```bash
# Easy way: Use the helper script
./run-docker.sh

# Or run in detached mode
./run-docker.sh -d

# Manual way: Build and run with Docker Compose
UID=$(id -u) GID=$(id -g) docker compose up --build

# Or if you prefer to run in detached mode
UID=$(id -u) GID=$(id -g) docker compose up --build -d

# View logs (if running in detached mode)
docker compose logs -f scraper
```

**Note:** The `UID` and `GID` environment variables ensure that output files are owned by your user instead of root.

The scraper will:
1. Log in to Mascot using your credentials
2. Navigate to the inventory form
3. Extract all category and field data
4. Save results to `output/mascot_fields.csv` and `output/mascot_fields.parquet`

## Output

Results are saved in the `output/` directory:
- `mascot_fields.csv` - CSV format
- `mascot_fields.parquet` - Parquet format (more efficient for large datasets)

## Development

The project uses:
- **Playwright** for browser automation
- **BeautifulSoup** for HTML parsing
- **Pydantic** for data validation
- **Pandas** for data export
