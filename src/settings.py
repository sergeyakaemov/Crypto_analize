import os
from enum import Enum
from dotenv import load_dotenv


load_dotenv()


class StorageType(Enum):
    JSON = "json"
    SQLITE = "sqlite"


class Settings:

    def __init__(self):
        self.storage = StorageType(os.getenv("STORAGE", "json"))
        self.database = os.getenv("DATABASE", "crypto.db")


settings = Settings()