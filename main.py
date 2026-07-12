import os
import telebot
from google import genai
from dotenv import load_dotenv

# โหลดค่าจากไฟล์ .env (กรณีใช้งานเครื่องคอมพิวเตอร์ส่วนตัว)
load_dotenv()

# ดึงค่า Token และ Key จาก Environment Variables เพื่อความปลอดภัย
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ตรวจสอบความถูกต้องของค่า Configuration
if not TELEGRAM_BOT_TOKEN or not GEMINI_API_KEY:
    raise ValueError("กรุณาตั้งค่า TELEGRAM_BOT_TOKEN และ GEMINI_API_KEY ในระบบก่อนเริ่มทำงาน")

# เริ่มต้นอินสแตนซ์ของ Telegram Bot และ Google GenAI Client
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# Dictionary สำหรับเก็บเซสชันการแชทแยกตาม ID ของผู้ใช้แต่ละคน เพื่อให้บอทจำบริบทที่คุยกันก่อนหน้าได้
user_chats = {}

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.from_user.id
    
    # สร้างหรือรีเซ็ตเซสชันการแชทด้วย Gemini 2.5 Flash ให้ผู้ใช้คนนี้ใหม่
    user_chats[user_id] = gemini_client.chats.create(model='gemini-2.5-flash')
    
    welcome_text = (
        "สวัสดีครับ! ยินดีต้อนรับสู่บอท Gemini 2.5 Flash เวอร์ชันสนทนามาตรฐาน 🤖💬\n\n"
        "คุณสามารถส่งข้อความมาพูดคุย ปรึกษา หรือถามคำถามได้ทันที ระบบจะจดจำเรื่องราวที่คุยกันก่อนหน้า\n"
        "หากต้องการเริ่มหัวข้อใหม่ และล้างความจำเก่า ให้พิมพ์คำสั่ง /reset ครับ"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['reset'])
def reset_chat(message):
    user_id = message.from_user.id
    
    # สร้างแชทเซสชันใหม่ทับอันเดิมเพื่อล้างประวัติการคุย
    user_chats[user_id] = gemini_client.chats.create(model='gemini-2.5-flash')
    bot.reply_to(message, "🔄 รีเซ็ตประวัติการสนทนาเรียบร้อยแล้ว! เริ่มต้นคุยเรื่องใหม่ได้เลยครับ")

@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text_message(message):
    user_id = message.from_user.id
    user_input = message.text

    # ถ้าผู้ใช้เปิดแชทขึ้นมาแต่ยังไม่มีเซสชันในระบบ ให้สร้างขึ้นมาใหม่ก่อน
    if user_id not in user_chats:
        user_chats[user_id] = gemini_client.chats.create(model='gemini-2.5-flash')

    # แสดงสถานะบนแอป Telegram ว่าบอทกำลังพิมพ์ตอบกลับ (Typing...) เพื่อเพิ่ม UX ที่ดี
    bot.send_chat_action(chat_id=message.chat.id, action='typing')

    try:
        # ส่งคำพูดของผู้ใช้เข้าไปในแชทเซสชันของ Gemini
        response = user_chats[user_id].send_message(user_input)
        
        # ส่งคำตอบรับกลับไปหาผู้ใช้ใน Telegram (รองรับข้อความได้ยาวสูงสุด 4096 ตัวอักษร)
        bot.reply_to(message, response.text)
        
    except Exception as e:
        print(f"Error occurring: {e}")
        bot.reply_to(message, "❌ ขออภัยด้วยครับ เกิดข้อผิดพลาดในการประมวลผลคำตอบ กรุณาลองใหม่อีกครั้ง")

if __name__ == '__main__':
    print("🤖 บอทแชท Gemini 2.5 Flash เริ่มต้นทำงานเรียบร้อยแล้ว (โหมด Long Polling)...")
    # ใช้ infinity_polling เพื่อควบคุมระบบไม่ให้หยุดทำงานหากเจอปัญหาเน็ตหลุดชั่วคราว
    bot.infinity_polling()
