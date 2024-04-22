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
        # 從 message 中解析參數
        _, get_env, get_domain = message.text.split(maxsplit=2)
    except ValueError:
        # 如果參數數量不正確，回復用戶正確的使用方式
        bot.reply_to(
            message,
            "使用方式不正確。請按照以下格式輸入：\n/get <env> <domain>",
        )
        return

    # 調用更新 MongoDB 的函數
    get_result = get_domain_from_mongodb(collection, get_env, get_domain)
    print("get result", get_result)
    # 根據操作結果回復用戶
    if get_result:
        domain_info_yaml = convert_to_yaml(get_result)
        bot.reply_to(message, f"{domain_info_yaml}", parse_mode="Markdown")
    else:
        bot.reply_to(message, f"在 {get_env} 環境中未找到域名 {get_domain} 的訊息。")


@bot.message_handler(commands=["edit"])
def handle_edit_command(message):
    try:
        # 從 message 中解析參數
        _, update_env, origin_domain, new_domain = message.text.split(maxsplit=3)
    except ValueError:
        # 如果參數數量不正確，回復用戶正確的使用方式
        bot.reply_to(
            message,
            "使用方式不正確。請按照以下格式輸入：\n/edit <env> <old_domain> <new_domain>",
        )
        return

    # 調用更新 MongoDB 的函數
    update_result = update_domain_in_mongodb(
        collection, update_env, origin_domain, new_domain
    )
    # 根據操作結果回復用戶
    if update_result:
        bot.reply_to(message, "域名更新成功。")
    else:
        bot.reply_to(message, "域名更新失敗，請檢查輸入的數據。")


@bot.message_handler(commands=["add"])
def handle_add_command(message):
    try:
        # 從 message 中解析參數
        _, env, domain = message.text.split(maxsplit=2)
    except ValueError:
        # 如果參數數量不正確，回復用戶正確的使用方式
        bot.reply_to(
            message, "使用方式不正確。請按照以下格式輸入：\n/add <env> <domain>"
        )
        return

    # 調用添加域名到 MongoDB 的函數
    add_successful = add_domain_to_mongodb(collection, env, domain)

    # 根據操作結果回復用戶
    if add_successful:
        bot.reply_to(message, "域名添加成功。")
    else:
        bot.reply_to(message, "域名添加失敗，請檢查輸入的數據。")


@bot.message_handler(commands=["del"])
def handle_delete_command(message):
    try:
        # 從 message 中解析參數
        _, env, domain = message.text.split(maxsplit=2)
    except ValueError:
        # 如果參數數量不正確，回復用戶正確的使用方式
        bot.reply_to(
            message, "使用方式不正確。請按照以下格式輸入：\n/del <env> <domain>"
        )
        return

    # 調用從 MongoDB 刪除域名的函數
    delete_successful = delete_domain_in_mongodb(collection, env, domain)

    # 根據操作結果回復用戶
    if delete_successful:
        bot.reply_to(message, "域名刪除成功。")
    else:
        bot.reply_to(message, "域名刪除失敗，請檢查輸入的數據。")


@bot.message_handler(commands=["bulk_add"])
def handle_bulk_add_command(message):
    # 將命令解析為 env 和多個 domain
    parts = message.text.split()
    if len(parts) < 3:
        bot.reply_to(
            message,
            "使用方式不正確。請按照以下格式輸入：\n/bulk_add <env> <domain1> <domain2> ...",
        )
        return

    env = parts[1]
    domains = parts[2:]

    # 調用批量添加域名到 MongoDB 的函數
    success = bulk_add_domains_to_mongodb(collection, env, domains)

    # 根據操作結果回復用戶
    if success:
        bot.reply_to(message, "域名批量添加成功。")
    else:
        bot.reply_to(message, "域名批量添加失敗，請檢查輸入的數據。")


if __name__ == "__main__":
    client = init_mongo_client(mongodb_uri)
    collection_name = "domains"
    collection = get_collection(client, collection_name)

    bot.infinity_polling()
