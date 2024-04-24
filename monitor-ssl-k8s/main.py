import telebot
import schedule
import time
import threading
from utils.bot_commands_handler import setup_handlers
from classes.repos import DomainRepo, init_mongo_client, get_collection
from classes.services import DomainService
from utils.config_loader import EnvConfigLoader
from utils.scheduler_jobs import setup_scheduler


def setup_bot_handlers(bot, service):
    setup_handlers(bot, service)


def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)


def run_in_background(job):
    thread = threading.Thread(target=job)
    thread.daemon = True
    thread.start()


if __name__ == "__main__":
    mongodb_uri = EnvConfigLoader.get_mongodb_uri()
    telegram_config = EnvConfigLoader.get_telegram_config()
    telegram_bot_token = telegram_config["telegram_bot_token"]
    telegram_group_id = telegram_config["telegram_group_id"]

    bot = telebot.TeleBot(telegram_bot_token)

    client = init_mongo_client(mongodb_uri)
    collection_name = "cert"
    collection = get_collection(client, collection_name)

    domain_repo = DomainRepo(collection)
    domain_service = DomainService(domain_repo)

    setup_bot_handlers(bot, domain_service)
    setup_scheduler(
        bot,
        domain_service,
        telegram_group_id,
    )
    run_in_background(run_schedule)
    bot.infinity_polling()
