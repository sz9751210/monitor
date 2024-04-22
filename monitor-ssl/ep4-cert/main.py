import time
import telebot
import yaml
import schedule
import threading
from mongo import (
    init_mongo_client,
    get_collection,
    load_domain_envs_from_mongodb,
    update_domain_in_mongodb,
    add_domain_to_mongodb,
    delete_domain_in_mongodb,
    bulk_add_domains_to_mongodb,
    get_domain_from_mongodb,
)
from cert import get_ssl_cert_info, parse_ssl_cert_info
from scheduler_jobs import setup_scheduler

mongodb_uri = "mongodb://rootuser:rootpass@localhost:27017/mydatabase?authSource=admin"
telegram_bot_token = "your-token"
bot = telebot.TeleBot(telegram_bot_token)
platform = "your-platform"
telegram_group_id = "your-chat-id"


def convert_to_yaml(python_obj):
    return yaml.dump(python_obj, allow_unicode=True)


@bot.message_handler(commands=["add"])
def handle_add_command(message):
    try:
        _, env, domain = message.text.split(maxsplit=2)
    except ValueError:
        bot.reply_to(
            message, "使用方式不正確。請按照以下格式輸入：\n/add <env> <domain>"
        )
        return
    if get_ssl_cert_info(domain, check_only=True):
        add_successful = add_domain_to_mongodb(collection, env, domain)

        if add_successful:
            bot.reply_to(message, f"domain 新增成功\n環境為{env}\ndomain為{domain}")
        else:
            bot.reply_to(message, "domain 新增失敗，請檢查輸入的資料。")
    else:
        bot.reply_to(message, "證書檢查失敗,請檢查輸入的 domain 是否正確。")


@bot.message_handler(commands=["cert_info"])
def send_cert_info(message):
    try:
        _, get_domain = message.text.split(maxsplit=1)
    except ValueError:
        bot.send_message(
            message.chat.id, "請提供一個 domain 。例如：/cert_info example.com"
        )
        return
    cert = get_ssl_cert_info(get_domain, check_only=False)
    if cert is None or cert is False:
        error_message = f"domain 錯誤: 無法獲取 {get_domain} 的 SSL 證書資訊。"
        bot.send_message(message.chat.id, error_message)
    else:
        cert_info = parse_ssl_cert_info(get_domain, cert)
        bot.send_message(message.chat.id, cert_info)


@bot.message_handler(commands=["get_all"])
def handle_get_all_command(message):
    domain_data = load_domain_envs_from_mongodb(collection)
    print(message.from_user)
    print(domain_data)
    domains = convert_to_yaml(domain_data)
    bot.send_message(message.chat.id, f"{domains}", parse_mode="Markdown")


@bot.message_handler(commands=["get"])
def handle_get_command(message):
    try:
        _, get_env, get_domain = message.text.split(maxsplit=2)
    except ValueError:
        bot.reply_to(
            message,
            "使用方式不正確。請按照以下格式輸入：\n/get <env> <domain>",
        )
        return

    get_result = get_domain_from_mongodb(collection, get_env, get_domain)
    print("get result", get_result)
    if get_result:
        domain_info_yaml = convert_to_yaml(get_result)
        bot.reply_to(message, f"{domain_info_yaml}", parse_mode="Markdown")
    else:
        bot.reply_to(
            message, f"在 {get_env} 環境中未找到 domain  {get_domain} 的訊息。"
        )


@bot.message_handler(commands=["edit"])
def handle_edit_command(message):
    try:
        _, update_env, origin_domain, new_domain = message.text.split(maxsplit=3)
    except ValueError:
        bot.reply_to(
            message,
            "使用方式不正確。請按照以下格式輸入：\n/edit <env> <old_domain> <new_domain>",
        )
        return

    update_result = update_domain_in_mongodb(
        collection, update_env, origin_domain, new_domain
    )
    if update_result:
        bot.reply_to(message, "domain 更新成功。")
    else:
        bot.reply_to(message, "domain 更新失敗，請檢查輸入的資料。")


@bot.message_handler(commands=["del"])
def handle_delete_command(message):
    try:
        _, env, domain = message.text.split(maxsplit=2)
    except ValueError:
        bot.reply_to(
            message, "使用方式不正確。請按照以下格式輸入：\n/del <env> <domain>"
        )
        return

    delete_successful = delete_domain_in_mongodb(collection, env, domain)

    if delete_successful:
        bot.reply_to(message, "domain 刪除成功。")
    else:
        bot.reply_to(message, "domain 刪除失敗，請檢查輸入的資料。")


@bot.message_handler(commands=["bulk_add"])
def handle_bulk_add_command(message):
    parts = message.text.split()
    if len(parts) < 3:
        bot.reply_to(
            message,
            "使用方式不正確。請按照以下格式輸入：\n/bulk_add <env> <domain1> <domain2> ...",
        )
        return

    env = parts[1]
    domains = parts[2:]

    success = bulk_add_domains_to_mongodb(collection, env, domains)

    if success:
        bot.reply_to(message, "domain 批量新增成功。")
    else:
        bot.reply_to(message, "domain 批量新增失敗，請檢查輸入的資料。")


def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    client = init_mongo_client(mongodb_uri)
    collection_name = "domains"
    collection = get_collection(client, collection_name)
    setup_scheduler(
        bot,
        collection,
        telegram_group_id,
        platform,
        telegram_bot_token,
        telegram_group_id,
    )
    t = threading.Thread(target=run_schedule)
    t.start()
    bot.infinity_polling()
