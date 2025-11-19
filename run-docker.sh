#!/bin/bash
# run-docker.sh - Helper script to run the scraper in Docker

set -e

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "📝 Please create one by copying .env.example:"
    echo "   cp .env.example .env"
    echo "   # Then edit .env with your credentials"
    exit 1
fi

# Set UID and GID for docker-compose (UID is readonly, so we use USER_ID)
export USER_ID=$(id -u)
export GROUP_ID=$(id -g)

echo "🐳 Starting Mascot Scraper in Docker..."
echo "   UID: $USER_ID"
echo "   GID: $GROUP_ID"
echo ""

# Run docker compose with USER_ID and GROUP_ID environment variables
docker compose up --build "$@"
