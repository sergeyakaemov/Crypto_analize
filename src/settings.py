import os
from enum import Enum
from dotenv import load_dotenv


load_dotenv()


class StorageType(Enum):
    JSON = "json"
    SQLITE = "sqlite"


class Settings:

    def __init__(self):
        raw_storage = os.getenv("STORAGE", "json")

        try:
            self.storage = StorageType(raw_storage)
        except ValueError:
            allowed = ", ".join(item.value for item in StorageType)
            raise ValueError(
                f"Неизвестное значение STORAGE={raw_storage!r}. "
                f"Допустимо: {allowed}"
            ) from None

        self.database = os.getenv("DATABASE", "crypto.db")


settings = Settings()