#!/bin/bash

# Script to run IntelX checker via Docker
# This script will be called by cron

# Set working directory
cd /home/hungnm/Projects/intelx-checking

# Log directory and files
LOG_DIR="/home/hungnm/Projects/intelx-checking/logs"
DATE_SUFFIX=$(date +%Y-%m-%d)
LOG_FILE="$LOG_DIR/cron_${DATE_SUFFIX}.log"
LATEST_LOG="$LOG_DIR/cron.log"

mkdir -p "$LOG_DIR"

# Log start time
echo "========================================" | tee -a "$LOG_FILE"
echo "Starting IntelX scan at $(date)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# Remove old container if exists
docker-compose down >> "$LOG_FILE" 2>&1

# Run the container
docker-compose up --build 2>&1 | tee -a "$LOG_FILE"

# Log completion
echo "Scan completed at $(date)" | tee -a "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Create/update symlink to latest log
ln -sf "cron_${DATE_SUFFIX}.log" "$LATEST_LOG"

# Clean up logs older than 30 days
find "$LOG_DIR" -name "cron_*.log" -type f -mtime +30 -delete

echo "Log saved to: $LOG_FILE"
