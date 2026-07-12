import os
import sys
import logging
import telebot
from google import genai
from google.genai import errors
from dotenv import load_dotenv

# 1. ตั้งค่า Logging ให้แสดงผลบน Render Dashboard อย่างละเอียดและเรียลไทม์
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# กำหนดชื่อโมเดลหลัก (Gemini 2.5 Flash)
MODEL_NAME = 'gemini-2.5-flash'

# ตรวจสอบ Environment Variables ก่อนเริ่มทำงาน
if not TELEGRAM_BOT_TOKEN or not GEMINI_API_KEY:
    logging.error("Environment Variables ไม่ครบถ้วน! กรุณาเช็ก TELEGRAM_BOT_TOKEN และ GEMINI_API_KEY")
    sys.exit("Error: Missing environment variables.")

try:
    bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    logging.info("=== บอทและ Google GenAI Client เริ่มต้นระบบสำเร็จ ===")
except Exception as e:
    logging.error(f"ไม่สามารถเริ่มระบบบอทได้: {e}")
    sys.exit(1)

# Dictionary เก็บประวัติการแชทแยกตาม ID คนคุย
user_chats = {}

def get_or_create_chat(user_id):
    """ฟังก์ชันช่วยดึงเซสชันแชทเดิม หรือสร้างใหม่ถ้ายังไม่มี"""
    if user_id not in user_chats:
        logging.info(f"กำลังสร้างเซสชันแชทใหม่ให้ยูสเซอร์ {user_id} โดยใช้โมเดล {MODEL_NAME}")
        user_chats[user_id] = gemini_client.chats.create(model=MODEL_NAME)
    return user_chats[user_id]

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.from_user.id
    # สร้างเซสชันแชทใหม่ทันทีเมื่อกด /start เพื่อเคลียร์ค่าเก่า
    user_chats[user_id] = gemini_client.chats.create(model=MODEL_NAME)
    
    welcome_text = (
        "🤖 **ยินดีต้อนรับสู่บอท Gemini 2.5 Flash!**\n\n"
        "คุณสามารถพิมพ์คุยโต้ตอบข้อความกับบอทได้ทันที ระบบจะจำบริบทการคุยก่อนหน้าไว้\n"
        "🔄 พิมพ์คำสั่ง /reset เพื่อล้างความจำและเริ่มคุยหัวข้อใหม่ครับ"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['reset'])
def reset_chat(message):
    user_id = message.from_user.id
    user_chats[user_id] = gemini_client.chats.create(model=MODEL_NAME)
    logging.info(f"ยูสเซอร์ {user_id} ทำการรีเซ็ตประวัติการคุย")
    bot.reply_to(message, "🔄 รีเซ็ตประวัติการสนทนาเรียบร้อยแล้ว! เริ่มต้นคุยเรื่องใหม่ได้เลย")

@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text_message(message):
    user_id = message.from_user.id
    user_input = message.text

    # เปิดสถานะ "กำลังพิมพ์..." ใน Telegram
    bot.send_chat_action(chat_id=message.chat.id, action='typing')

    try:
        # เรียกเซสชันแชทของคนนั้นๆ
        chat_session = get_or_create_chat(user_id)
        
        # ส่งข้อความไปหา Gemini API
        logging.info(f"User {user_id} ส่งข้อความ: {user_input[:20]}...")
        response = chat_session.send_message(user_input)
        
        # ตรวจสอบและส่งผลลัพธ์กลับ
        if response.text:
            bot.reply_to(message, response.text)
        else:
            bot.reply_to(message, "🤖 Gemini ไม่ได้ส่งข้อความตอบกลับมา (คำถามอาจขัดต่อเงื่อนไข Safety Settings ของระบบ)")
            
    except errors.APIError as api_err:
        # ดักจับกรณีเกิดความผิดพลาดที่ตัว API ของ Google โดยตรง (เช่น Key ผิด, โดนจำกัดโควตา)
        logging.error(f"Gemini API Error (User {user_id}): {api_err}")
        error_msg = f"❌ **เกิดข้อผิดพลาดจาก Gemini API:**\n`{api_err.message}`\n\n💡 *คำแนะนำ: โปรดตรวจสอบความถูกต้องของ GEMINI_API_KEY หรือเครดิตใช้งาน*"
        bot.reply_to(message, error_msg, parse_mode='Markdown')
        
    except Exception as e:
        # ดักจับความผิดพลาดทั่วไปอื่นๆ
        logging.error(f"Unexpected Error (User {user_id}): {e}")
        bot.reply_to(message, f"❌ **ระบบหลังบ้านขัดข้อง:**\n`{str(e)}`", parse_mode='Markdown')

if __name__ == '__main__':
    logging.info("กำลังเปิดโหมด Long Polling...")
    # ตั้งค่ารัดกุมเพื่อลดการหลุดจากการเชื่อมต่อเครือข่ายที่ไม่เสถียรบน Cloud
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
