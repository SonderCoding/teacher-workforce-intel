import logging

_configured = False


def configure_logging():
    global _configured
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(module)s | %(message)s",
    )
    _configured = True


def get_logger(name: str):
    global _configured
    if not _configured:
        configure_logging()
    return logging.getLogger(name)