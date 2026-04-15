import logging
import sys
from datetime import datetime

# Configure standard logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("job_finder")

def log(message, level="info"):
    """
    Structured log function for the application.
    """
    if level.lower() == "info":
        logger.info(message)
    elif level.lower() == "error":
        logger.error(message)
    elif level.lower() == "warning":
        logger.warning(message)
    elif level.lower() == "debug":
        logger.debug(message)
    else:
        print(f"[{datetime.now().isoformat()}] [LOG] {message}")
