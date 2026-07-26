import asyncio
import os
import sys
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pyrogram import Client, filters, idle
from pyrogram.errors import FloodWait

try:
    import pytz
except ImportError:
    os.system("pip install pytz")
    import pytz

# ==================== إعدادات الحساب والسجلات ====================
API_ID = 15715463
API_HASH = "78132d613ebb7f8aebd0fe492ff20b8e"
LOG_CHAT_ID = -1001555410554  
SESSION_STRING = os.environ.get("SESSION_STRING")

if not SESSION_STRING:
    print("❌ خطأ: لم يتم العثور على متغير SESSION_STRING في الاستضافة!")
    sys.exit(1)

app = Client(
    "Premium_UserBot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING,
    workers=20
)

msg_cache = {}

def get_user_mention(user):
    if not user: return "مستخدم غير معروف"
    name = user.first_name or "مستخدم"
    return f"[{name}](tg://user?id={user.id})"

# ==================== السيرفر الوهمي لحل مشكلة بورت ريندر ====================
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write("🟢 Pure UserBot Server Is Active!".encode("utf-8"))

def run_web_server():
    try:
        # جلب المنفذ تلقائياً من ريندر أو استخدام 8080 كافتراضي
        port = int(os.environ.get("PORT", 8080))
        server = HTTPServer(("0.0.0.0", port), DummyServer)
        print(f"📡 تم تشغيل سيرفر المنفذ الوهمي على بورت: {port}")
        server.serve_forever()
    except Exception:
        pass

# ==================== 1. محرك مراقبة واقتناص الخاص والميديا ====================
@app.on_message(filters.private & ~filters.me & ~filters.bot, group=1)
async def incoming_private_handler(client, message):
    try:
        user_info = get_user_mention(message.from_user)
        msg_cache[message.id] = {
            "text": message.text or message.caption or "", "user": user_info, "media": True if not message.text else False
        }
        is_self_destruct = False
        if message.photo and message.photo.ttl_seconds: is_self_destruct = True
        elif message.video and message.video.ttl_seconds: is_self_destruct = True

        if is_self_destruct:
            file_path = await message.download()
            if file_path:
                await client.send_document(LOG_CHAT_ID, file_path, caption=f"🚨 **اقتناص ميديا مؤقتة من:** {user_info}")
                os.remove(file_path)
                return

        if message.text:
            await client.send_message(LOG_CHAT_ID, f"📥 **رسالة خاص جديدة من:** {user_info}\n\n💬 النص:\n`{message.text}`")
    except Exception: pass

# ==================== 2. محرك كشف الرسائل المحذوفة ====================
@app.on_deleted_messages(group=2)
async def deleted_messages_handler(client, messages):
    try:
        for msg in messages:
            if msg.id in msg_cache:
                cached = msg_cache[msg.id]
                await client.send_message(LOG_CHAT_ID, f"🗑️ **قام {cached['user']} بحذف رسالة من الخاص!**\n\n💬 **النص المحذوف كان:**\n`{cached['text'] or '[ميديا]'}`")
                del msg_cache[msg.id]
    except Exception: pass

# ==================== 3. محرك كشف الرسائل المعدلة ====================
@app.on_edited_message(filters.private & ~filters.me & ~filters.bot, group=3)
async def edited_messages_handler(client, message):
    try:
        user_info = get_user_mention(message.from_user)
        new_text = message.text or message.caption or "[ميديا]"
        if message.id in msg_cache:
            old_text = msg_cache[message.id]["text"] or "[نص فارغ]"
            if old_text == new_text: return
            await client.send_message(LOG_CHAT_ID, f"✏️ **قام {user_info} بتعديل رسالته!**\n\n❌ **السابقة:** `{old_text}`\n\n✅ **الجديدة:** `{new_text}`")
        msg_cache[message.id] = {"text": new_text, "user": user_info, "media": False if message.text else True}
    except Exception: pass

# ==================== 4. محرك الاسم والبايو الوقتي التلقائي ====================
async def auto_time_engine():
    local_tz = pytz.timezone("Asia/Aden")
    last_minute = ""
    while True:
        try:
            now = datetime.now(local_tz)
            current_time = now.strftime("%I:%M %p").replace("AM", "ص").replace("PM", "م")
            if current_time != last_minute:
                await app.update_profile(first_name=f"ツ | {current_time}", bio=f"الساعة الآن: {current_time}")
                last_minute = current_time
        except Exception: pass
        await asyncio.sleep(30)

# ==================== إقلاع وتشغيل المنظومة ====================
async def main():
    print("⚡ جاري تشغيل الترسانة...")
    while True:
        try:
            await app.start()
            break
        except FloodWait as e:
            await asyncio.sleep(e.value + 5)
        except Exception:
            return

    asyncio.create_task(auto_time_engine())
    try:
        await app.send_message(LOG_CHAT_ID, "🟢 **تم تحديث الكود وحل مشكلة البورت بنجاح!**\nالسورس مستقر الآن على ريندر.")
    except Exception: pass
    await idle()

if __name__ == "__main__":
    # تشغيل سيرفر المنفذ في مسار جانبي لإرضاء ريندر
    threading.Thread(target=run_web_server, daemon=True).start()
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
