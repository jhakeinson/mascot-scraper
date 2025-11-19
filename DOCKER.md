# Docker Configuration Summary

## What Changed

The application has been configured to read environment variables from `.env` when running in Docker.

## Key Files Modified

### `docker-compose.yml`
- Added `env_file: .env` to automatically load environment variables
- Configured volume for browser profile data persistence
- Enabled `shm_size: 2g` for Chrome stability
- Maps output directory for easy access to scraped data

### `run-docker.sh` (NEW)
- Helper script to simplify Docker execution
- Automatically sets UID/GID for proper file permissions
- Validates `.env` file exists before running

## How It Works

1. **Environment Variables**: Docker Compose reads `.env` and injects all variables into the container
2. **python-dotenv**: The app also uses `load_dotenv()` but Docker environment takes precedence
3. **Volumes**:
   - `./output:/app/output` - Scraped data accessible on host
   - `playwright-data:/tmp/playwright-chrome-profile` - Persistent browser profile

## Quick Start

```bash
# 1. Ensure .env file exists
cp .env.example .env
# Edit .env with your credentials

# 2. Run with Docker
./run-docker.sh

# OR manually
UID=$(id -u) GID=$(id -g) docker compose up --build
```

## Troubleshooting

### Permission Issues
If output files are owned by root:
```bash
# Run with UID/GID set
UID=$(id -u) GID=$(id -g) docker compose up --build
```

### Browser Crashes
If you see Chrome crashing:
- `shm_size: 2g` is already configured
- Check that Docker has enough memory allocated

### Environment Variables Not Loading
Verify with:
```bash
docker compose config | grep -A 10 environment
```

You should see all your `.env` variables listed.
