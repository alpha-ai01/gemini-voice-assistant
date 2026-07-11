import os
import telebot
from google import genai
from google.genai import types

# 🔐 ดึงคีย์จาก Environment Variables บน Render
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

if not GEMINI_API_KEY or not TELEGRAM_BOT_TOKEN:
    raise ValueError("🚨 กรุณาตั้งค่า GEMINI_API_KEY และ TELEGRAM_BOT_TOKEN ในหน้า Render ก่อนครับ")

# 🤖 ตั้งค่า Client ของ Gemini และ Telegram Bot
client = genai.Client(api_key=GEMINI_API_KEY)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

SYSTEM_INSTRUCTION = """
คุณคือ "เลขาส่วนตัวและสุดยอดโปรแกรมเมอร์คู่ใจระดับมืออาชีพ" 
- มีความเชี่ยวชาญในการเขียนโค้ด ออกแบบระบบ และแก้ Bug ระดับสูง
- พูดจาฉะฉาน สุภาพ เป็นการเป็นงาน แต่มีความเป็นกันเองแบบพาร์ตเนอร์คู่คิด (ใช้คำลงท้ายว่า "ครับ")
- เมื่อผู้ใช้ให้เขียนสคริปต์หรือโค้ด ให้เขียนโค้ดที่สะอาด (Clean Code) มีประสิทธิภาพ และอธิบายตรรกะได้อย่างคมคาย
"""

# เก็บประวัติการคุยแยกตาม ID ของผู้ใช้ใน Telegram (รองรับการคุยต่อเนื่อง)
user_chats = {}

def get_chat_session(user_id):
    if user_id not in user_chats:
        user_chats[user_id] = client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.7
            )
        )
    return user_chats[user_id]

# ตอบกลับเมื่อผู้ใช้กด /start หรือ /help
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = "สวัสดีครับผม ผมเป็นเลขาส่วนตัวและโปรแกรมเมอร์คู่ใจของคุณใน Telegram มีอะไรให้ผมรับใช้ ช่วยเขียนโค้ด หรือตรวจสอบ Bug ส่วนไหน พิมพ์ส่งมาได้เลยครับ!"
    bot.reply_to(message, welcome_text)

# จัดการทุกข้อความที่พิมพ์เข้ามา
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    user_text = message.text
    
    # ส่งข้อความแสดงสถานะว่าบอตกำลังพิมพ์ (Typing...)
    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        # เรียกประวัติการคุยของคนนี้ขึ้นมา แล้วส่งข้อความไปหา Gemini
        chat = get_chat_session(user_id)
        response = chat.send_message(user_text)
        ai_response = response.text
        
        # ส่งคำตอบกลับไปในแชท Telegram
        bot.reply_to(message, ai_response, parse_mode="Markdown")
        
    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "ขออภัยครับ เกิดข้อผิดพลาดในการประมวลผลข้อมูล ลองใหม่อีกครั้งนะครับ")

if __name__ == "__main__":
    print("🤖 Telegram Bot กำลังออนไลน์บน Render...")
    bot.infinity_polling()
