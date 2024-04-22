import telebot
import schedule
import time

TOKEN = "your-bot-token"
bot = telebot.TeleBot(TOKEN)

TARGET_GROUP_CHAT_ID = "your-chat-id"


def send_message_to_group():
    message = "大家好！"
    bot.send_message(TARGET_GROUP_CHAT_ID, message)


schedule.every().day.at("09:00").do(send_message_to_group)
while True:
    schedule.run_pending()
    time.sleep(1)
