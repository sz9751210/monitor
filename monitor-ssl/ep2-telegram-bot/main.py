import telebot
from datetime import datetime

TOKEN = "your-token"
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=["hello"])
def hello_command(message):
    print(message.from_user)
    bot.send_message(message.chat.id, "Someone has started me!")


@bot.message_handler(commands=["info"])
def handle_info(message):
    # 初始化一個列表來保存消息的屬性資訊
    info = []

    # 添加基本訊息
    info.append(f"訊息ID：{message.message_id}")
    timestamp = datetime.fromtimestamp(message.date)
    formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    info.append(f"發送日期和時間：{formatted_time}")

    # 檢查並添加用戶訊息
    if message.from_user:
        user_info = f"發送者：{message.from_user.first_name}"
        if hasattr(message.from_user, "username"):
            user_info += f" (@{message.from_user.username})"
        info.append(user_info)

    # 檢查並添加聊天訊息
    if message.chat:
        chat_type = "個人聊天" if message.chat.type == "private" else "群聊"
        info.append(f"聊天類型：{chat_type}")
        if hasattr(message.chat, "title"):
            info.append(f"聊天標題：{message.chat.title}")

    # 添加文本內容
    text_content = message.text or "無文本內容"
    info.append(f"訊息內容：{text_content}")

    # 將訊息列表合併成一個字符串
    info_str = "\n".join(info)

    # 發送訊息
    bot.reply_to(message, info_str)


@bot.message_handler(commands=["hello_with_parameters"])
def hello_with_parameters_command(message):
    name = message.text.split()[1] if len(message.text.split()) > 1 else "there"
    bot.send_message(message.chat.id, f"Greetings {name}! I have notified the group.")


bot.infinity_polling()
