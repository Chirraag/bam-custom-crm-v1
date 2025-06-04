#!/usr/bin/env python3
"""
Background email sync service
Run this script to continuously sync emails every 10 minutes
"""

import time
import schedule
import logging
from services.email_service import email_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def run_email_sync():
    """Function to run email sync - called by scheduler"""
    try:
        logger.info("Starting scheduled email sync...")
        email_service.sync_emails()
        logger.info("Scheduled email sync completed successfully")
    except Exception as e:
        logger.error(f"Scheduled email sync failed: {e}")

def main():
    """Main function to run the background sync service"""
    logger.info("Email background sync service starting...")
    logger.info("Email sync will run every 10 minutes")
    
    # Schedule email sync every 10 minutes
    schedule.every(10).minutes.do(run_email_sync)
    
    # Run initial sync
    logger.info("Running initial email sync...")
    run_email_sync()
    
    # Keep the service running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    main()