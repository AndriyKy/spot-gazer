import logging

from colorlog import ColoredFormatter

from .settings import CONSOLE_LOG_LEVEL, FILE_LOG_LEVEL

# Create a logger with the root logger's name
logger = logging.getLogger()

# Set the logging level for the logger to the lowest level you want to log to the console
logger.setLevel(CONSOLE_LOG_LEVEL)
logging.getLogger("asyncio").setLevel(logging.WARNING)
logging.getLogger("https").setLevel(logging.ERROR)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)

datetime_format = "%d.%m.%Y %H:%M:%S"

# Create a formatter for the log messages (customize as needed)
file_formatter = logging.Formatter("[%(levelname)-8s] (%(asctime)s) (%(name)s) %(message)s", datefmt=datetime_format)
console_formatter = ColoredFormatter(
    "[%(log_color)s%(levelname)-8s%(reset)s] (%(cyan)s%(asctime)s%(reset)s) (%(name)s) %(message)s",
    datefmt=datetime_format,
    log_colors={
        "DEBUG": "bg_white",
        "INFO": "bg_green",
        "WARNING": "bg_yellow",
        "ERROR": "bg_red",
        "CRITICAL": "bg_bold_red",
    },
    reset=True,
    style="%",
)

# Create a StreamHandler to log messages to the console
console_handler = logging.StreamHandler()
console_handler.setLevel(CONSOLE_LOG_LEVEL)  # Set the level to the lowest level you want to print to the console
console_handler.setFormatter(console_formatter)

# Create a FileHandler to log messages to a file
file_handler = logging.FileHandler("spot-gazer.log")
file_handler.setLevel(FILE_LOG_LEVEL)  # Set the level to the lowest level you want to log to the file
file_handler.setFormatter(file_formatter)

# Add the handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)
