import os
import logging
from flask import Flask
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
import asyncio
from threading import Thread

# ตั้งค่า Logging เพื่อดูสถานะระบบ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = os.getenv("TELEGRAM_TOKEN")
PORT = int(os.environ.get("PORT", 8080))

# 1. สร้าง Web Server จำลองสำหรับ Render Health Check
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running perfectly!", 200

def run_web_server():
    app.run(host="0.0.0.0", port=PORT)

# 2. ฟังก์ชันจัดการคำสั่งของ Telegram Bot
async def start(update, context):
    await update.message.reply_text("Hello! 👋 I am online and running on Render.")

async def handle_message(update, context):
    # TODO: ใส่โค้ดเชื่อมต่อ OpenRouter API ตรงนี้
    await update.message.reply_text("I received your message! processing...")

if __name__ == '__main__':
    if not TOKEN:
        print("❌ Error: TELEGRAM_TOKEN environment variable is missing!")
        exit(1)

    # รัน Web Server แยกไปอีก Thread
    Thread(target=run_web_server, daemon=True).start()

    print("🤖 Starting Telegram Bot...")
    
    # รัน Telegram Bot (แก้ไขการตั้งชื่อตัวแปรให้ตรงกัน)
    app_bot = ApplicationBuilder().token(TOKEN).build()
    
    # เพิ่ม Handlers
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("🚀 Bot started successfully.")
    
    # ใช้ run_polling ของ python-telegram-bot (แก้ปัญหาโครงสร้างทับซ้อน)
    app_bot.run_polling(close_loop=False)
