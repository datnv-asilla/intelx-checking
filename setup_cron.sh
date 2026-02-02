#!/bin/bash
# Setup cron job for IntelX daily scan

SCRIPT_DIR="/home/asilla/Asilla/IntelX-checking"
SCRIPT_NAME="intelx_search_new.py"
LOG_FILE="$SCRIPT_DIR/intelx_cron.log"

# Create cron job to run daily at 9:00 AM Vietnam Time
# Server timezone: Asia/Ho_Chi_Minh (UTC+7)
# Cron runs in local time, so 9 AM = 9:00 Vietnam Time
CRON_JOB="0 9 * * * cd $SCRIPT_DIR && /usr/bin/python3 $SCRIPT_NAME >> $LOG_FILE 2>&1"

# Check if cron job already exists
(crontab -l 2>/dev/null | grep -F "$SCRIPT_NAME") && echo "Cron job already exists" && exit 0

# Add cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "✓ Cron job added successfully!"
echo "Script will run daily at 9:00 AM Vietnam Time"
echo "Server timezone: $(timedatectl | grep 'Time zone' | awk '{print $3, $4}')"
echo "Log file: $LOG_FILE"
echo ""
echo "To view cron jobs: crontab -l"
echo "To remove cron job: crontab -e (then delete the line)"
