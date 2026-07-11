# gemini-voice-assistantimport os
import asyncio
import speech_recognition as sr
import edge_tts
import pygame
from google import genai
from google.genai import types

# 🔐 ดึง API Key จาก Environment Variable ชื่อ 'GEMINI_API_KEY'
# (ไม่ต้องวางคีย์ลงในนี้แล้ว ระบบจะไปอ่านค่าจากที่ตั้งไว้บน Server/Render เองครับ)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("🚨 ไม่พบระบบ GEMINI_API_KEY ใน Environment Variables กรุณาตั้งค่าก่อนรันสคริปต์ครับ")

# 🤖 System Instruction กำหนดให้เป็นเลขาและโปรแกรมเมอร์คู่ใจระดับมืออาชีพ
SYSTEM_INSTRUCTION = """
คุณคือ "เลขาส่วนตัวและสุดยอดโปรแกรมเมอร์คู่ใจระดับมืออาชีพ" 
- มีความเชี่ยวชาญในการเขียนโค้ด ออกแบบระบบ และแก้ Bug ระดับสูง
- พูดจาฉะฉาน สุภาพ เป็นการเป็นงาน แต่มีความเป็นกันเองแบบพาร์ตเนอร์คู่คิด (ใช้คำลงท้ายว่า "ครับ")
- เมื่อผู้ใช้ให้เขียนสคริปต์หรือโค้ด ให้เขียนโค้ดที่สะอาด (Clean Code) มีประสิทธิภาพ และอธิบายตรรกะได้อย่างคมคาย
- เนื่องจากการตอบกลับจะถูกแปลงเป็นเสียงพูด ให้พยายามอธิบายเนื้อหาหลักให้กระชับ เข้าใจง่ายเมื่อฟัง และหากมีโค้ดที่ยาวเกินไป ให้สรุปใจความสำคัญให้ผู้ฟังทราบก่อน
"""

# เชื่อมต่อกับ Gemini API
client = genai.Client(api_key=GEMINI_API_KEY)

# สร้าง Session สำหรับการคุยโต้ตอบต่อเนื่อง
chat = client.chats.create(
    model="gemini-2.5-flash",
    config=types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=0.7
    )
)

def listen_to_mic():
    """ฟังก์ชันเปิดไมค์รับเสียงภาษาไทย และแปลงเป็นข้อความ (STT)"""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("\n🎙️  กำลังฟัง... (พูดคำถามของคุณได้เลยครับ)")
        r.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=10)
            print("⏳ กำลังแปลงเสียงเป็นข้อความ...")
            text = r.recognize_google(audio, language="th-TH")
            print(f"👤 คุณพูดว่า: {text}")
            return text
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            print("❌ ไม่เข้าใจเสียงที่พูด กรุณาลองใหม่อีกครั้งครับ")
            return None
        except sr.RequestError:
            print("❌ ระบบแปลงเสียงมีปัญหา กรุณาตรวจสอบอินเทอร์เน็ต")
            return None

async def speak_text(text):
    """ฟังก์ชันแปลงข้อความภาษาไทยเป็นเสียงพากย์ที่เป็นธรรมชาติ (TTS) และเล่นเสียงออกลำโพง"""
    output_filename = "response.mp3"
    voice = "th-TH-NiwatNeural" 
    
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_filename)
    
    # เล่นไฟล์เสียง
    pygame.mixer.init()
    pygame.mixer.music.load(output_filename)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        await asyncio.sleep(0.1)
    pygame.mixer.quit()
    
    # ลบไฟล์เสียงชั่วคราว
    if os.path.exists(output_filename):
        os.remove(output_filename)

async def main():
    print("="*50)
    print("🤖 ระบบเลขาและโปรแกรมเมอร์ส่วนตัว (Gemini Voice AI) เริ่มทำงาน...")
    print("="*50)
    
    welcome_text = "สวัสดีครับผม ผมเป็นเลขาส่วนตัวและโปรแกรมเมอร์คู่ใจของคุณ มีอะไรให้ผมรับใช้หรือช่วยเขียนโค้ดส่วนไหน บอกได้เลยครับ"
    print(f"🤖 AI: {welcome_text}")
    await speak_text(welcome_text)
    
    while True:
        user_text = listen_to_mic()
        
        if user_text:
            if any(word in user_text for word in ["จบการทำงาน", "ปิดโปรแกรม", "บาย", "ลาก่อน"]):
                goodbye = "รับทราบครับ ไว้เจอกันใหม่ครับผม ขอให้เป็นวันที่ดีในการเขียนโค้ดนะครับ"
                print(f"🤖 AI: {goodbye}")
                await speak_text(goodbye)
                break
                
            print("🤖 กำลังประมวลผลคำตอบจาก Gemini...")
            try:
                response = chat.send_message(user_text)
                ai_response = response.text
                
                print(f"🤖 AI:\n{ai_response}")
                await speak_text(ai_response)
                
            except Exception as e:
                print(f"❌ เกิดข้อผิดพลาดจาก Gemini API: {e}")
                await speak_text("ขออภัยครับ เกิดข้อผิดพลาดในการประมวลผลข้อมูล")

if __name__ == "__main__":
    asyncio.run(main())
