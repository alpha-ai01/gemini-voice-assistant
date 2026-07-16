import requests

# เพิ่มตัวแปรนี้ที่ด้านบนของไฟล์ (ตั้งค่าใน Render Environment Variables ด้วยนะครับ)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

async def handle_message(update, context):
    user_text = update.message.text
    
    # 1. ส่งสถานะให้ผู้ใช้รู้ว่ากำลังคิด
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    # 2. ส่งคำถามไปยัง OpenRouter
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "google/gemini-2.0-flash-exp", # หรือรุ่นที่คุณต้องการ
            "messages": [{"role": "user", "content": user_text}]
        }
    )
    
    # 3. ดึงคำตอบออกมา
    data = response.json()
    reply = data['choices'][0]['message']['content']
    
    # 4. ส่งคำตอบกลับไปที่ Telegram
    await update.message.reply_text(reply)
