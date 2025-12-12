from datetime import datetime
import logging
import time

from config import Config
from drive_manager import DriveManager
from email_composer import EmailService
from google_auth import GoogleAuth
from sheet_manager import SheetManager


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)
def main():
    logger.info("Starting Batch Mailer...")

    try:
        Config.validate() # Ensure env vars are loaded

        gmail_svc, sheets_svc, drive_svc = GoogleAuth.get_services()
        sheet_manager = SheetManager(sheets_svc, Config.SPREADSHEET_ID)
        drive_manager = DriveManager(drive_svc)
        email_service = EmailService(gmail_svc)

        headers, rows = sheet_manager.load_data(Config.TAB_NAME)

        try:
            col_map = {
                'email': headers.index('email'),
                'name': headers.index('name'),
                'cert': headers.index('certif'),
                'sent': headers.index('sent?'),
                'timestamp': headers.index('timestamp')
            }
        except ValueError as e:
            logger.error(f"Column missing in spreadsheet: {e}")
            return

        logger.info(f"Found {len(rows)} rows.")

        for i, row in enumerate(rows):
            try:
                def get_val(idx): return row[idx].strip() if len(row) > idx else ""

                email = get_val(col_map['email'])
                if not email: continue

                if get_val(col_map['sent']).lower() == "yes":
                    continue

                name = get_val(col_map['name'])
                cert_link = get_val(col_map['cert'])

                logger.info(f"Processing: {email}")

                cert_data, cert_name = drive_manager.download_file(cert_link)
                email_service.send_email(email, name, cert_data, cert_name)

                sheet_manager.update_cell(Config.TAB_NAME, i, col_map['sent'], "Yes")
                sheet_manager.update_cell(Config.TAB_NAME, i, col_map['timestamp'], datetime.now().strftime("%Y-%m-%d %H:%M"))

                logger.info(f"Success: {email}")
                time.sleep(1)

            except Exception as e:
                logger.error(f"Row {i+2} failed: {e}")

    except Exception as e:
        logger.critical(f"Fatal Error: {e}")

    logger.info("Job Complete.")

if __name__ == "__main__":
    main()