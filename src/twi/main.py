from pydantic import ValidationError

from twi.config import Settings
from twi.logging_config import configure_logging, get_logger


def main():
    configure_logging()
    logger = get_logger(__name__)

    try:
        settings = Settings()
    except ValidationError as e:
        print("Configuration Error")
        print(e)
        raise SystemExit(1)

    print("Loaded settings:")
    print(f"DATABASE_URL={settings.database_url}")

    logger.info("Application started.")


if __name__ == "__main__":
    main()