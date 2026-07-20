import json
import csv
from abc import ABC, abstractmethod


class BaseStorage(ABC):

    @abstractmethod
    def save(self, report: dict):
        pass


class JsonStorage(BaseStorage):

    def __init__(self, filename="report.json"):
        self.filename = filename

    def save(self, report: dict):
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=4, ensure_ascii=False)


class CsvStorage(BaseStorage):

    def __init__(self, filename="report.csv"):
        self.filename = filename

    def save(self, report: dict):
        with open(self.filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            writer.writerow(["metric", "value"])
            writer.writerow(["generated_at", report["generated_at"]])
            writer.writerow(["coins_count", report["coins_count"]])
            writer.writerow(["market_cap", report["market_cap"]])

