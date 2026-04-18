import logging
import sys
import colorlog

def setup_logging():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # 检查是否已经存在处理器
    if not logger.hasHandlers():
        # Create a console handler
        console_handler = colorlog.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # Create a formatter and add it to the handler
        formatter = colorlog.ColoredFormatter(
            '%(asctime)s - %(name)s - %(log_color)s%(levelname)s%(reset)s - %(message)s',
            log_colors={
                'DEBUG':    'cyan',
                'INFO':     'green',
                'WARNING':  'yellow',
                'ERROR':    'red',
                'CRITICAL': 'bold_red',
            }
        )
        console_handler.setFormatter(formatter)

        # Add the handler to the logger
        logger.addHandler(console_handler)

    return logger

if __name__ == "__main__":
    logger = setup_logging()
    # logger.info("Hello, World!")
    # logger.warning("This is a warning message.")
    # logger.error("This is an error message.")
    # logger.critical("This is a critical message.")
    # logger.debug("This is a debug message.")
