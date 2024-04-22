import yaml


def load_config():
    with open("config.yaml", "r") as file:
        return yaml.safe_load(file)


def get_mongodb_uri():
    config = load_config()
    return config.get("mongodb_uri", None)


def get_telegram_config():
    config = load_config()
    return {
        "telegram_bot_token": config.get("telegram_bot_token", None),
        "platform": config.get("platform", None),
        "telegram_group_id": config.get("telegram_group_id", None),
    }
