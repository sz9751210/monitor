import telebot
import schedule
import time

TOKEN = "your-bot-token"
bot = telebot.TeleBot(TOKEN)

TARGET_GROUP_CHAT_ID = "your-chat-id"


def send_message_to_group():
    message = "大家好！"  # 你想發送的消息
    bot.send_message(TARGET_GROUP_CHAT_ID, message)


# 安排任務每天9點執行
schedule.every().day.at("09:00").do(send_message_to_group)
while True:
    schedule.run_pending()
    time.sleep(1)  # 暫停一秒再檢查
