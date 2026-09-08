import os
import sys
from loguru import logger
from pathlib import Path


def setup_logging():
    logger.remove()
    
    if sys.stderr is not None:
        logger.add(
            sys.stderr, 
            level="DEBUG", 
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )

    app_data = Path(os.environ.get("LOCALAPPDATA", Path.home()))
    log_dir = app_data / "SatisfactoryGoogleSharing" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file_path = log_dir / "app_{time:YYYY-MM-DD}.log"

    logger.add(
        sink=str(log_file_path),
        level="DEBUG",
        rotation="10 MB",
        retention="14 days",
        compression="zip",
        encoding="utf-8",
        enqueue=True,
        backtrace=True,
        diagnose=True
    )


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.opt(exception=(exc_type, exc_value, exc_traceback)).critical("App crashed due to an unhandled exception!")
