import telebot
import yaml
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

mongodb_uri = "mongodb://rootuser:rootpass@localhost:27017/mydatabase?authSource=admin"
TOKEN = "your-token"
bot = telebot.TeleBot(TOKEN)


def convert_to_yaml(python_obj):
    return yaml.dump(python_obj, allow_unicode=True)


@bot.message_handler(commands=["get_all"])
def handle_get_all_command(message):
    domain_data = load_domain_envs_from_mongodb(collection)
    print(message.from_user)
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


@bot.message_handler(commands=["add"])
def handle_add_command(message):
    try:
        _, env, domain = message.text.split(maxsplit=2)
    except ValueError:
        bot.reply_to(
            message, "使用方式不正確。請按照以下格式輸入：\n/add <env> <domain>"
        )
        return

    add_successful = add_domain_to_mongodb(collection, env, domain)

    if add_successful:
        bot.reply_to(message, "domain 新增成功。")
    else:
        bot.reply_to(message, "domain 新增失敗，請檢查輸入的資料。")


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


if __name__ == "__main__":
    client = init_mongo_client(mongodb_uri)
    collection_name = "domains"
    collection = get_collection(client, collection_name)

    bot.infinity_polling()
