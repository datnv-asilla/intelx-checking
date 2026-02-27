#!/bin/bash

# Script to setup cronjob for IntelX checker
# Run weekly on Mondays at 9:00 AM Vietnam Time (UTC+7)
# Server timezone: UTC, so 9:00 AM Vietnam = 2:00 AM UTC

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

# Add new cron job - Weekly on Mondays at 2:00 AM UTC (9:00 AM Vietnam Time)
echo "0 2 * * 1 cd $SCRIPT_DIR && $PYTHON_PATH $PYTHON_SCRIPT >> $LOG_DIR/cron_\$(date +\\%Y-\\%m-\\%d).log 2>&1" >> /tmp/crontab_new.txt

# Install new crontab
crontab /tmp/crontab_new.txt

# Clean up
rm /tmp/crontab_new.txt

echo "✅ Cron job setup complete!"
echo ""
echo "Scheduled to run: Weekly on Mondays at 2:00 AM UTC (9:00 AM Vietnam Time)"
echo "Script location: $PYTHON_SCRIPT"
echo "Python path: $PYTHON_PATH"
echo "Logs directory: $LOG_DIR/cron_YYYY-MM-DD.log"
echo ""
echo "Current crontab:"
crontab -l | grep "intelx"
echo ""
echo "To view logs: tail -f $LOG_DIR/cron_\$(date +%Y-%m-%d).log"
echo "To test manually: cd $SCRIPT_DIR && python3 intelx_search_new.py"
