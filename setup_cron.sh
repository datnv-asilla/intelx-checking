#!/bin/bash

# Script to setup cronjob for IntelX checker
# Run daily at 9:00 AM

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_SCRIPT="$SCRIPT_DIR/intelx_search_new.py"
LOG_DIR="$SCRIPT_DIR/logs"

# Create logs directory
mkdir -p "$LOG_DIR"

# Find Python3 path
PYTHON_PATH=$(which python3)

# Backup current crontab
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null

# Remove existing IntelX cron jobs
crontab -l 2>/dev/null | grep -v "intelx_search_new.py" | grep -v "intelx-checking" > /tmp/crontab_new.txt

# Add new cron job - Daily at 9:00 AM with date-based logging
echo "0 9 * * * cd $SCRIPT_DIR && $PYTHON_PATH $PYTHON_SCRIPT >> $LOG_DIR/cron_\$(date +\\%Y-\\%m-\\%d).log 2>&1" >> /tmp/crontab_new.txt

# Install new crontab
crontab /tmp/crontab_new.txt

# Clean up
rm /tmp/crontab_new.txt

echo "✅ Cron job setup complete!"
echo ""
echo "Scheduled to run: Daily at 9:00 AM"
echo "Script location: $PYTHON_SCRIPT"
echo "Python path: $PYTHON_PATH"
echo "Logs directory: $LOG_DIR/cron_YYYY-MM-DD.log"
echo ""
echo "Current crontab:"
crontab -l | grep "intelx"
echo ""
echo "To view logs: tail -f $LOG_DIR/cron_\$(date +%Y-%m-%d).log"
echo "To test manually: cd $SCRIPT_DIR && python3 intelx_search_new.py"
