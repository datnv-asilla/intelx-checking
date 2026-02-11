#!/bin/bash

# Script to setup cronjob for Docker-based IntelX checker
# Run every Monday at 9:00 AM

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
RUN_SCRIPT="$SCRIPT_DIR/run_docker_cron.sh"

# Make run script executable
chmod +x "$RUN_SCRIPT"

# Backup current crontab
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null

# Remove existing IntelX cron jobs
crontab -l 2>/dev/null | grep -v "intelx-checking" | grep -v "run_docker_cron.sh" > /tmp/crontab_new.txt

# Add new cron job - Every Monday at 9:00 AM
echo "0 9 * * 1 $RUN_SCRIPT" >> /tmp/crontab_new.txt

# Install new crontab
crontab /tmp/crontab_new.txt

# Clean up
rm /tmp/crontab_new.txt

echo "✅ Cron job setup complete!"
echo ""
echo "Scheduled to run: Every Monday at 9:00 AM"
echo "Script location: $RUN_SCRIPT"
echo ""
echo "Current crontab:"
crontab -l | grep -E "intelx-checking|run_docker_cron.sh|^\s*$"
echo ""
echo "To view logs: tail -f $SCRIPT_DIR/logs/cron.log"
echo "To test manually: $RUN_SCRIPT"
