#!/bin/bash
# clean-output.sh - Clean output directory for Docker runs

set -e

echo "🧹 Cleaning output directory..."

# Check if output directory exists
if [ -d "output" ]; then
    # Check if directory or its contents are owned by root
    if [ "$(stat -c '%U' output)" = "root" ] || ([ "$(ls -A output 2>/dev/null)" ] && [ "$(sudo find output -user root 2>/dev/null | wc -l)" -gt 0 ]); then
        echo "   Found root-owned directory or files in output/"
        echo "   Fixing with sudo..."
        sudo rm -rf output/*
        sudo chown $(id -u):$(id -g) output
    else
        # No root ownership, just clean the contents
        rm -rf output/*
    fi
else
    # Create directory if it doesn't exist
    mkdir -p output
fi

# Ensure correct ownership and permissions
chmod 755 output

echo "✅ Output directory is clean and ready!"
echo "   Owner: $(stat -c '%U:%G' output)"
echo "   Permissions: $(stat -c '%a' output)"
