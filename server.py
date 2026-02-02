import asyncio
import os
import sys
import json
import datetime
import sqlite3
import subprocess
import re
import time
import random
from typing import List, Dict, Any, Optional

# ==========================================
# 🛑 المكتبات والاعتمادات الأساسية
# ==========================================
try:
    from telethon import TelegramClient, events, Button, functions, types, errors
    from telethon.sessions import StringSession
    from telethon.tl.functions.messages import (
        StartBotRequest, GetHistoryRequest, ReadHistoryRequest, SendMessageRequest
    )
    from telethon.tl.functions.channels import (
        JoinChannelRequest, LeaveChannelRequest, GetFullChannelRequest
    )
    from telethon.tl.functions.account import UpdateProfileRequest
except ImportError:
    os.system("pip install telethon")
    os.execv(sys.executable, [sys.executable] + sys.argv)

# ==========================================
# 🛑 الإعدادات (API & IDs)
# ==========================================
API_ID = 39719802  
API_HASH = '032a5697fcb9f3beeab8005d6601bde9'  
ADMIN_ID = 8504553407 

IS_SUB_BOT = len(sys.argv) > 2
BOT_TOKEN = sys.argv[1] if IS_SUB_BOT else "8206330079:AAEZ3T1-hgq_VhEG3F8ElGEQb9D14gCk0eY"
OWNER_ID = int(sys.argv[2]) if IS_SUB_BOT else ADMIN_ID

# تهيئة المجلدات
for folder in ['data', 'sessions', 'configs', 'logs']:
    if not os.path.exists(folder): os.makedirs(folder)

# إنشاء ملف الأداة (المستخرج)
EXTRACTOR_SCRIPT = "extractor.py"
with open(EXTRACTOR_SCRIPT, "w", encoding="utf-8") as f:
    f.write("""
import os, asyncio
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

print("🚀 Titan Session Extractor")
API_ID = 39719802
API_HASH = '032a5697fcb9f3beeab8005d6601bde9'

async def main():
    async with TelegramClient(StringSession(), API_ID, API_HASH) as client:
        print("\\n✅ Session Code:\\n")
        print(client.session.save())
        input("\\nDone. Press Enter...")

if __name__ == "__main__":
    asyncio.run(main())
""")

# ==========================================
# 📊 نظام قاعدة البيانات المتقدم (Titan DB)
# ==========================================
class TitanDatabase:
    def __init__(self, user_id):
        self.db_path = f"data/titan_v16_{user_id}.db"
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._init_db()

    def _init_db(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS accounts (
            phone TEXT PRIMARY KEY, session_str TEXT, points INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active', last_action TIMESTAMP)''')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, val TEXT)')
        self.conn.commit()

    def add_acc(self, phone, session):
        self.cursor.execute("INSERT OR REPLACE INTO accounts (phone, session_str) VALUES (?, ?)", (phone, session))
        self.conn.commit()

    def get_all(self):
        self.cursor.execute("SELECT phone, session_str, points FROM accounts WHERE status='active'")
        return self.cursor.fetchall()

    def remove_acc(self, phone):
        self.cursor.execute("DELETE FROM accounts WHERE phone=?", (phone,))
        self.conn.commit()

db = TitanDatabase(OWNER_ID)

# ==========================================
# 🧠 محرك الفحص والعمليات (Titan Engine)
# ==========================================
class TitanEngine:
    @staticmethod
    async def validate(session_str):
        client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
        try:
            await client.connect()
            auth = await client.is_user_authorized()
            return auth, client
        except: return False, None

# ==========================================
# 🖥️ واجهة المستخدم (The UI)
# ==========================================
def main_buttons():
    btns = [
        [Button.inline("➕ إضافة حساب (رقم)", data="add_p"), Button.inline("🔑 إضافة حساب (سيشن)", data="add_s")],
        [Button.inline("🚀 بدء تجمع (رابط)", data="f_link"), Button.inline("🎁 تجميع هدايا", data="f_gift")],
        [Button.inline("🛠 أداة استخراج السيشن", data="send_tool")],
        [Button.inline("💰 فحص وتحويل", data="f_trans"), Button.inline("🔥 تجميع مختلط", data="f_mix")],
        [Button.inline("📊 إحصائياتي", data="stats"), Button.inline("🧹 تنظيف الحسابات", data="cleanup")],
        [Button.inline("⚙️ الإعدادات", data="settings"), Button.inline("📝 السجلات", data="logs")],
        [Button.url("👨‍💻 المطور", "https://t.me/G_6_W")]
    ]
    if not IS_SUB_BOT:
        btns.insert(-1, [Button.inline("👑 تنصيب بوت لزبون (Admin)", data="deploy")])
    return btns

# ==========================================
# ⚡ النواة البرمجية (Core Logic)
# ==========================================
bot = TelegramClient(f"sessions/titan_core_{OWNER_ID}", API_ID, API_HASH)

@bot.on(events.NewMessage(pattern='/start'))
async def start_cmd(event):
    if event.sender_id not in [OWNER_ID, ADMIN_ID]: return
    await event.respond("🔱 **Titan Ultimate V16**\nتم إصلاح كافة الأخطاء البرمجية ونظام التحقق جاهز.", buttons=main_buttons())

# --- [ إرسال الأداة - تم إصلاح خطأ السنتكس ] ---
@bot.on(events.CallbackQuery(data="send_tool"))
async def tool_sender(event):
    await event.answer("جاري تحضير الملف...", alert=False)
    text = (
        "🛠 **أداة استخراج السيشن**\n\n"
        "استخدم هذا الملف لاستخراج كود السيشن من حساباتك بأمان.\n"
        "1. شغل الملف\n2. ادخل الرقم\n3. انسخ الكود الناتج"
    )
    await event.client.send_file(event.chat_id, EXTRACTOR_SCRIPT, caption=text)

# --- [ إضافة سيشن مع تحقق ] ---
@bot.on(events.CallbackQuery(data="add_s"))
async def add_session_logic(event):
    async with bot.conversation(OWNER_ID) as conv:
        await conv.send_message("👤 **أرسل رقم الهاتف:**")
        phone = (await conv.get_response()).text.strip()
        await conv.send_message("🔑 **أرسل كود السيشن:**")
        session = (await conv.get_response()).text.strip()
        
        await conv.send_message("⏳ جاري فحص الحساب...")
        ok, c = await TitanEngine.validate(session)
        if ok:
            db.add_acc(phone, session)
            await conv.send_message(f"✅ تم تفعيل الحساب `{phone}` بنجاح!")
            await c.disconnect()
        else:
            await conv.send_message("❌ السيشن غير صالح.")

# --- [ تجميع الرابط ] ---
@bot.on(events.CallbackQuery(data="f_link"))
async def link_farm(event):
    async with bot.conversation(OWNER_ID) as conv:
        await conv.send_message("🔗 أرسل الرابط:")
        link = (await conv.get_response()).text.strip()
        accs = db.get_all()
        await event.respond(f"🚀 بدء العمل بـ {len(accs)} حساب...")
        
        for p, s, pt in accs:
            ok, c = await TitanEngine.validate(s)
            if ok:
                try:
                    if "start=" in link:
                        u = link.split('/')[-1].split('?')[0]
                        prm = link.split('start=')[-1]
                        await c(StartBotRequest(u, u, prm))
                    else:
                        await c(JoinChannelRequest(link))
                except: pass
                finally: await c.disconnect()
        await event.respond("✅ اكتملت المهمة.")

# --- [ تنظيف الحسابات ] ---
@bot.on(events.CallbackQuery(data="cleanup"))
async def cleaner(event):
    await event.answer("🧹 جاري تصفية المزرعة...", alert=True)
    accs = db.get_all()
    dead = 0
    for p, s, pt in accs:
        ok, c = await TitanEngine.validate(s)
        if not ok:
            db.remove_acc(p)
            dead += 1
        elif c: await c.disconnect()
    await event.respond(f"✅ تم التنظيف. الأرقام المحذوفة: `{dead}`")

# --- [ الإحصائيات ] ---
@bot.on(events.CallbackQuery(data="stats"))
async def stats_view(event):
    accs = db.get_all()
    await event.edit(f"📊 **إحصائيات المزرعة:**\n\n📱 الحسابات: `{len(accs)}`", buttons=[[Button.inline("🔙 رجوع", data="main")]])

@bot.on(events.CallbackQuery(data="main"))
async def back_main(event):
    await event.edit("القائمة الرئيسية:", buttons=main_buttons())

# --- [ تنصيب بوتات الزبائن ] ---
@bot.on(events.CallbackQuery(data="deploy"))
async def deploy_admin(event):
    if event.sender_id != ADMIN_ID: return
    async with bot.conversation(ADMIN_ID) as conv:
        try:
            await conv.send_message("⚙️ التوكن:"); t = (await conv.get_response()).text
            await conv.send_message("👤 الآيدي:"); u = (await conv.get_response()).text
            await conv.send_message("⏳ الأيام:"); d = (await conv.get_response()).text
            subprocess.Popen([sys.executable, __file__, t, u])
            await conv.send_message("🚀 تم التشغيل بنجاح!")
        except Exception as e: await conv.send_message(f"❌ خطأ: {e}")

# ==========================================
# 🏁 التشغيل النهائي
# ==========================================
if __name__ == '__main__':
    print(f"✅ Titan V16 is running for {OWNER_ID}")
    bot.start(bot_token=BOT_TOKEN)
    bot.run_until_disconnected()
