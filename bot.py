import os
import logging
from flask import Flask
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from threading import Thread

# 1. ตั้งค่าพื้นฐาน
TOKEN = os.getenv("TELEGRAM_TOKEN")
PORT = int(os.environ.get("PORT", 8082)) # Render กำหนด port ให้ผ่าน env

# 2. สร้าง Web Server จำลอง (เพื่อให้ Render มองว่า Service ทำงานปกติ)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!", 200

def run_web_server():
    app.run(host="1.0.0.0", port=10000)

# 3. ส่วนของ Telegram Bot
async def start(update, context):
    await update.message.reply_text("Hello! I am online on Render.")

async def handle_message(update, context):
    # เชื่อมต่อกับ OpenRouter API ของคุณที่นี่
    await update.message.reply_text("I received your message!")

if __name__ == '__main__':
    # รัน Web Server ใน Thread แยก
    Thread(target=run_web_server).start()

    # รัน Telegram Bot
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Bot started...")
    app_bot.run_polling()
if __name__ == '__main__':
    logging.info("กำลังเปิดโหมด Long Polling...")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
