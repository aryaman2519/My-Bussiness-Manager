
import os
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.sale import Sale

logger = logging.getLogger(__name__)

def cleanup_old_invoices(db: Session, retention_days: int = 10):
    """
    Deletes invoices older than `retention_days`.
    Removes both the database record and the PDF file from disk.
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        logger.info(f"🧹 Starting cleanup for records older than {cutoff_date}")
        
        # Find old records
        old_sales = db.query(Sale).filter(Sale.created_at < cutoff_date).all()
        
        if not old_sales:
            logger.info("✅ No old records found for cleanup.")
            return

        deleted_count = 0
        for sale in old_sales:
            # Delete PDF file
            if sale.pdf_file_path and os.path.exists(sale.pdf_file_path):
                try:
                    os.remove(sale.pdf_file_path)
                    logger.info(f"🗑️ Deleted file: {sale.pdf_file_path}")
                except Exception as file_error:
                    logger.error(f"❌ Failed to delete file {sale.pdf_file_path}: {file_error}")
            
            # Delete DB record
            db.delete(sale)
            deleted_count += 1
            
        db.commit()
        logger.info(f"✅ Cleanup complete. Deleted {deleted_count} old records.")

    except Exception as e:
        logger.error(f"❌ Cleanup process failed: {e}")
        db.rollback()
