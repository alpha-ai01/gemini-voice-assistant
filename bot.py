import os
import logging
import requests
from flask import Flask
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from threading import Thread
from dotenv import load_dotenv

# 1. โหลด .env ถ้ามี (สำหรับการรันในเครื่อง)
load_dotenv()

# 2. ดึงค่า (จะอ่านจากไฟล์ .env หรือจาก Render Environment Variables ก็ได้)
TOKEN = os.getenv("TELEGRAM_TOKEN")
API_KEY = os.getenv("OPENROUTER_API_KEY")
PORT = int(os.environ.get("PORT", 8080))

# ตั้งค่า Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Web Server จำลอง
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!", 200

def run_web_server():
    app.run(host="0.0.0.0", port=PORT)

# ฟังก์ชันจัดการข้อความ
async def start(update, context):
    await update.message.reply_text("Hello! I am ready to assist you.")

async def handle_message(update, context):
    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "google/gemini-2.0-flash-exp",
                "messages": [{"role": "user", "content": user_text}]
            }
        )
        data = response.json()
        if "choices" in data:
            reply = data['choices'][0]['message']['content']
        else:
            reply = "Sorry, I couldn't get a response from the AI."
        await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text("Error occurred.")
        print(f"Error: {e}")

if __name__ == '__main__':
    # รัน Web Server
    Thread(target=run_web_server, daemon=True).start()

    # รัน Bot
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Bot started successfully.")
    app_bot.run_polling()
