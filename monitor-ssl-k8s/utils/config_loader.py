import os
import yaml


class YamlConfigLoader:
    def __init__(self, filename):
        self.config = self.load_config(filename)

    def load_config(self, filename):
        with open(filename, "r") as file:
            return yaml.safe_load(file)

    def get_mongodb_uri(self):
        return self.config.get("mongodb_uri", None)

    def get_telegram_config(self):
        return {
            "telegram_bot_token": self.config.get("telegram_bot_token", None),
            "platform": self.config.get("platform", None),
            "telegram_group_id": self.config.get("telegram_group_id", None),
        }


class EnvConfigLoader:
    @staticmethod
    def get_mongodb_uri():
        return os.getenv("MONGODB_URI", "")

    @staticmethod
    def get_telegram_config():
        return {
            "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
            "telegram_group_id": os.getenv("TELEGRAM_GROUP_ID", ""),
        }
