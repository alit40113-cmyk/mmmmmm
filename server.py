# -*- coding: utf-8 -*-
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👑 THE GRAND IMPERIAL SYSTEM - ULTIMATE TITAN EDITION 👑
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Developed By: 8504553407
- Version: 3.0 (Enterprise)
- Core: Telethon Multi-Instance Management
- Purpose: Full Master Control + Advanced Client Factory
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import sys
import json
import asyncio
import datetime
import random
import logging
import re
import time
import subprocess
from telethon import TelegramClient, events, Button, functions, types
from telethon.sessions import StringSession
from telethon.errors import (
    ApiIdInvalidError,
    PhoneNumberInvalidError,
    SessionPasswordNeededError,
    BotMethodInvalidError,
    AccessTokenInvalidError
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [1] الإعدادات الأساسية والهوية
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

API_ID = 39719802 
API_HASH = '032a5697fcb9f3beeab8005d6601bde9'
BOT_TOKEN = "8206330079:AAEZ3T1-hgq_VhEG3F8ElGEQb9D14gCk0eY" 
MASTER_ID = 8504553407
DB_FILE = "imperial_master_database.json"

# إعداد السجلات بشكل احترافي
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('imperial.log'), logging.StreamHandler()]
)
logger = logging.getLogger("ImperialCore")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [2] محرك قاعدة البيانات المركزية (JSON DB Engine)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class DatabaseManager:
    """كلاس مسؤول عن إدارة البيانات وضمان عدم ضياعها"""
    
    def __init__(self, path):
        self.path = path
        self._ensure_db()

    def _ensure_db(self):
        if not os.path.exists(self.path):
            initial_data = {
                "system_config": {
                    "master_id": MASTER_ID,
                    "target_bot": "@t06bot",
                    "referral_link": "",
                    "global_delay": 40,
                    "max_retry": 3
                },
                "master_accounts": {}, # {phone: session_string}
                "clients_inventory": {}, # {client_id: {token, expiry, limit, accounts: {}}}
                "audit_logs": [],
                "statistics": {"total_collected": 0, "active_bots": 0}
            }
            self.save(initial_data)

    def load(self):
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading database: {e}")
            return {}

    def save(self, data):
        try:
            with open(self.path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving database: {e}")

    def add_log(self, message):
        data = self.load()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data['audit_logs'].append(f"[{timestamp}] {message}")
        if len(data['audit_logs']) > 50:
            data['audit_logs'].pop(0)
        self.save(data)

db = DatabaseManager(DB_FILE)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [3] محرك التجميع الذكي (The Farming Engine)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class FarmingProcessor:
    """محرك معالجة التجميع وتخطي الحمايات"""

    @staticmethod
    async def perform_referral(client, link):
        """محرك تنفيذ الإحالة"""
        try:
            if not link or "start=" not in link:
                return False, "رابط غير صالح"
            
            bot_username = link.split("/")[-1].split("?")[0]
            start_parameter = link.split("start=")[-1]
            
            await client(functions.messages.StartBotRequest(
                bot=bot_username,
                peer=bot_username,
                start_param=start_parameter
            ))
            return True, "تمت الإحالة بنجاح"
        except Exception as e:
            return False, str(e)

    @staticmethod
    async def perform_gift(client, target_bot):
        """محرك سحب الهدية اليومية وتخطي قنوات الاشتراك"""
        try:
            await client.send_message(target_bot, "/start")
            await asyncio.sleep(4)
            
            # محاولة تخطي القنوات والتحقق (Cycle)
            for attempt in range(1, 11):
                messages = await client.get_messages(target_bot, limit=1)
                if not messages or not messages[0].reply_markup:
                    break
                
                button_clicked = False
                for row in messages[0].reply_markup.rows:
                    for btn in row.buttons:
                        # 1. الانضمام للقنوات
                        if isinstance(btn, types.KeyboardButtonUrl):
                            try:
                                channel_username = btn.url.split('/')[-1]
                                await client(functions.channels.JoinChannelRequest(channel=channel_username))
                                button_clicked = True
                            except: pass
                        
                        # 2. النقر على أزرار التحقق
                        elif any(word in btn.text for word in ["تحقق", "تم", "تأكيد", "انضميت", "Verify", "Done"]):
                            await messages[0].click(text=btn.text)
                            await asyncio.sleep(3)
                            button_clicked = True
                        
                        # 3. النقر على زر الهدية
                        elif any(word in btn.text for word in ["هدية", "يومية", "Daily", "Gift", "Claim"]):
                            await messages[0].click(text=btn.text)
                            return True, "تم استلام الهدية بنجاح"
                
                if not button_clicked:
                    break
            return False, "لم يتم العثور على زر الهدية"
        except Exception as e:
            return False, str(e)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [4] نظام إدارة بوتات الزبائن (Sub-Bot Controllers)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def run_client_instance(client_id, bot_token):
    """دالة تشغيل وإدارة نسخة بوت الزبون بشكل مستقل"""
    try:
        # إنشاء جلسة البوت للزبون
        client_bot = TelegramClient(f"sessions/client_{client_id}", API_ID, API_HASH)
        await client_bot.start(bot_token=bot_token)
        
        # --- [ واجهة الزبون ] ---
        @client_bot.on(events.NewMessage(pattern='/start'))
        async def client_start_handler(event):
            if event.sender_id != int(client_id):
                return
            
            current_db = db.load()
            info = current_db['clients_inventory'].get(str(client_id))
            if not info: return
            
            # فحص مدة الاشتراك
            expiry_dt = datetime.datetime.strptime(info['expiry'], '%Y-%m-%d')
            if datetime.datetime.now() > expiry_dt:
                return await event.reply("⚠️ **عذراً، انتهت صلاحية اشتراكك.**\nيرجى التواصل مع الإدارة للتجديد.")

            welcome_text = (
                f"🛡️ **لوحة التحكم الخاصة بك**\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 الهوية: `{client_id}`\n"
                f"📅 تاريخ الانتهاء: `{info['expiry']}`\n"
                f"🔢 الحد المسموح: `{len(info['accounts'])} / {info['limit']}`\n"
                f"🎯 الهدف: `{current_db['system_config']['target_bot']}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━"
            )
            buttons = [
                [Button.inline("➕ إضافة حساب جديد", "c_add"), Button.inline("🗑️ حذف حساب", "c_del")],
                [Button.inline("🚀 بدء تجميع الإحالة", "c_farm_ref"), Button.inline("🎁 بدء تجميع الهدية", "c_farm_gift")],
                [Button.inline("🔄 تجميع شامل (الكل)", "c_farm_all")],
                [Button.inline("📊 عرض حساباتي", "c_list_accs")]
            ]
            await event.reply(welcome_text, buttons=buttons)

        # --- [ أوامر الزبون التفاعلية ] ---
        @client_bot.on(events.CallbackQuery)
        async def client_callback_handler(event):
            cid = str(event.sender_id)
            current_db = db.load()
            action = event.data.decode()

            if action == "c_add":
                if len(current_db['clients_inventory'][cid]['accounts']) >= current_db['clients_inventory'][cid]['limit']:
                    return await event.answer("❌ وصلت للحد الأقصى المسموح لك!", alert=True)
                
                async with client_bot.conversation(event.sender_id) as conv:
                    await conv.send_message("🔑 **يرجى إرسال الـ String Session الخاصة بحسابك:**")
                    ss_input = (await conv.get_response()).text.strip()
                    await conv.send_message("📱 **يرجى إرسال رقم الهاتف لهذا الحساب:**")
                    phone_input = (await conv.get_response()).text.strip()
                    
                    # حفظ وتأكيد
                    current_db['clients_inventory'][cid]['accounts'][phone_input] = ss_input
                    db.save(current_db)
                    await conv.send_message(f"✅ تم ربط الحساب `{phone_input}` بنجاح في نسختك.")

            elif action == "c_del":
                async with client_bot.conversation(event.sender_id) as conv:
                    await conv.send_message("🗑️ **أرسل الرقم الذي تريد حذفه من قائمتك:**")
                    target_del = (await conv.get_response()).text.strip()
                    if target_del in current_db['clients_inventory'][cid]['accounts']:
                        del current_db['clients_inventory'][cid]['accounts'][target_del]
                        db.save(current_db)
                        await conv.send_message(f"✅ تم حذف الحساب `{target_del}`.")
                    else:
                        await conv.send_message("❌ هذا الرقم غير موجود في سجلاتك.")

            elif action == "c_list_accs":
                acc_list = current_db['clients_inventory'][cid]['accounts']
                if not acc_list:
                    return await event.respond("📊 ليس لديك حسابات مربوطة حالياً.")
                msg = "📊 **قائمة حساباتك المربوطة:**\n\n"
                for i, phone in enumerate(acc_list.keys(), 1):
                    msg += f"{i} - 📱 `{phone}`\n"
                await event.respond(msg)

            elif action.startswith("c_farm_"):
                mode = action.split("_")[-1]
                await event.answer("🚀 بدأ المحرك بالعمل على حساباتك...", alert=False)
                
                for phone, session in current_db['clients_inventory'][cid]['accounts'].items():
                    try:
                        temp_client = TelegramClient(StringSession(session), API_ID, API_HASH)
                        await temp_client.connect()
                        if not await temp_client.is_user_authorized():
                            continue
                        
                        if mode in ["ref", "all"]:
                            await FarmingProcessor.perform_referral(temp_client, current_db['system_config']['referral_link'])
                        if mode in ["gift", "all"]:
                            await FarmingProcessor.perform_gift(temp_client, current_db['system_config']['target_bot'])
                        
                        await temp_client.disconnect()
                        await asyncio.sleep(current_db['system_config']['global_delay'])
                    except: continue
                await event.respond("🏁 **اكتملت عملية التجميع لجميع حساباتك.**")

        await client_bot.run_until_disconnected()
    except Exception as e:
        logger.error(f"Failed to start instance for {client_id}: {e}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [5] بوت الماستر الرئيسي (The Master Core)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

master_bot = TelegramClient("ImperialMasterBot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# دالة مساعدة لتوليد واجهة الماستر
def get_master_panel(data):
    text = (
        f"👑 **لوحة تحكم إمبراطورية المصنع**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📱 حسابات الماستر: `{len(data['master_accounts'])}` \n"
        f"💎 إجمالي الزبائن: `{len(data['clients_inventory'])}` \n"
        f"⚙️ الهدف الحالي: `{data['system_config']['target_bot']}`\n"
        f"⏳ التأخير العالمي: `{data['system_config']['global_delay']} ثانية` \n"
        f"━━━━━━━━━━━━━━━━━━━━━"
    )
    buttons = [
        [Button.inline("➕ ربط سيشن للماستر", "m_add_ss"), Button.inline("🗑️ مسح حساب ماستر", "m_del_ss")],
        [Button.inline("📊 عرض حساباتي", "m_view_accs"), Button.inline("🔍 فحص الصلاحية", "m_audit_accs")],
        [Button.inline("🚀 تجميع الماستر", "m_farm_menu"), Button.inline("⚙️ الإعدادات العامة", "m_global_set")],
        [Button.inline("💎 تنصيب لزبون جديد", "m_deploy_client"), Button.inline("🗑️ طرد زبون", "m_terminate_client")],
        [Button.inline("📝 سجل العمليات", "m_view_logs"), Button.inline("📩 أداة الاستخراج", "m_get_tool")],
        [Button.inline("🔄 إعادة تشغيل", "m_reboot_system")]
    ]
    return text, buttons

@master_bot.on(events.NewMessage(pattern='/start'))
async def master_start_handler(event):
    if event.sender_id != MASTER_ID:
        return
    current_data = db.load()
    text, buttons = get_master_panel(current_data)
    await event.reply(text, buttons=buttons)

@master_bot.on(events.CallbackQuery)
async def master_callback_handler(event):
    if event.sender_id != MASTER_ID:
        return
    
    current_data = db.load()
    query = event.data.decode()

    # --- [ 1. إضافة وحذف حسابات الماستر ] ---
    if query == "m_add_ss":
        async with master_bot.conversation(MASTER_ID) as conv:
            await conv.send_message("🔑 **أرسل الـ String Session للماستر:**")
            session_str = (await conv.get_response()).text.strip()
            await conv.send_message("📱 **أرسل رقم الهاتف المرتبط:**")
            phone_num = (await conv.get_response()).text.strip()
            
            try:
                # محاولة فحص السيشن قبل الإضافة
                test_c = TelegramClient(StringSession(session_str), API_ID, API_HASH)
                await test_c.connect()
                if await test_c.is_user_authorized():
                    current_data['master_accounts'][phone_num] = session_str
                    db.save(current_data)
                    db.add_log(f"تم إضافة حساب ماستر جديد: {phone_num}")
                    await conv.send_message(f"✅ تم إضافة الحساب `{phone_num}` بنجاح إلى حسابات الماستر.")
                else:
                    await conv.send_message("❌ السيشن منتهي أو غير صالح!")
                await test_c.disconnect()
            except Exception as e:
                await conv.send_message(f"⚠️ خطأ أثناء الفحص: {e}")

    elif query == "m_del_ss":
        async with master_bot.conversation(MASTER_ID) as conv:
            await conv.send_message("🗑️ **أرسل الرقم المراد حذفه من حسابات الماستر:**")
            p_to_del = (await conv.get_response()).text.strip()
            if p_to_del in current_data['master_accounts']:
                del current_data['master_accounts'][p_to_del]
                db.save(current_data)
                db.add_log(f"تم حذف حساب ماستر: {p_to_del}")
                await conv.send_message(f"✅ تم حذف الرقم `{p_to_del}` نهائياً.")
            else:
                await conv.send_message("❌ الرقم غير موجود في القائمة.")

    # --- [ 2. عرض وفحص حسابات الماستر ] ---
    elif query == "m_view_accs":
        if not current_data['master_accounts']:
            return await event.respond("📊 لا يوجد حسابات ماستر مربوطة حالياً.")
        msg = "📊 **حسابات الماستر المربوطة:**\n\n"
        for i, phone in enumerate(current_data['master_accounts'].keys(), 1):
            msg += f"{i} - 📱 `{phone}`\n"
        await event.respond(msg)

    elif query == "m_audit_accs":
        await event.answer("🔍 جاري فحص جميع الحسابات...", alert=False)
        report = "🔍 **تقرير فحص الصلاحية:**\n\n"
        phones = list(current_data['master_accounts'].keys())
        for ph in phones:
            ss = current_data['master_accounts'][ph]
            try:
                c = TelegramClient(StringSession(ss), API_ID, API_HASH)
                await c.connect()
                if not await c.is_user_authorized():
                    report += f"❌ `{ph}`: منتهي الصلاحية\n"
                    del current_data['master_accounts'][ph]
                else:
                    report += f"✅ `{ph}`: فعال\n"
                await c.disconnect()
            except:
                report += f"❌ `{ph}`: حدث خطأ\n"
                del current_data['master_accounts'][ph]
        db.save(current_data)
        await event.respond(report)

    # --- [ 3. نظام تنصيب الزبائن (الفحص الدقيق) ] ---
    elif query == "m_deploy_client":
        async with master_bot.conversation(MASTER_ID) as conv:
            # 1. فحص الآيدي
            await conv.send_message("👤 **أرسل ID الزبون (أرقام فقط):**")
            client_id = (await conv.get_response()).text.strip()
            if not client_id.isdigit():
                return await conv.send_message("❌ فشل: يجب أن يكون الآيدي أرقاماً فقط.")
            
            # 2. فحص التوكن
            await conv.send_message("🔑 **أرسل توكن البوت الخاص بالزبون:**")
            client_token = (await conv.get_response()).text.strip()
            
            await conv.send_message("🔍 **جاري فحص التوكن وصلاحيته...**")
            try:
                # اختبار التوكن برمجياً قبل الحفظ
                checker = TelegramClient(f"temp_{client_id}", API_ID, API_HASH)
                await checker.start(bot_token=client_token)
                me = await checker.get_me()
                await checker.disconnect()
                await conv.send_message(f"✅ تم التحقق! البوت هو: @{me.username}")
            except Exception:
                return await conv.send_message("❌ فشل: التوكن غير صالح أو لا يمكن الاتصال به.")

            # 3. بقية البيانات
            await conv.send_message("⏳ **عدد أيام الترخيص (مثلاً 30):**")
            days = (await conv.get_response()).text.strip()
            await conv.send_message("🔢 **حد الأرقام المسموح له (مثلاً 10):**")
            limit = (await conv.get_response()).text.strip()

            expiry_date = (datetime.datetime.now() + datetime.timedelta(days=int(days))).strftime('%Y-%m-%d')
            current_data['clients_inventory'][client_id] = {
                "token": client_token,
                "expiry": expiry_date,
                "limit": int(limit),
                "accounts": {}
            }
            db.save(current_data)
            db.add_log(f"تم تنصيب بوت جديد للزبون: {client_id}")
            
            # إطلاق نسخة الزبون فوراً بالخلفية
            asyncio.create_task(run_client_instance(client_id, client_token))
            await conv.send_message(f"🎉 **تم تفعيل المنظومة للزبون بنجاح!**\n📅 الانتهاء: `{expiry_date}`")

    # --- [ 4. الإعدادات والسجلات ] ---
    elif query == "m_global_set":
        async with master_bot.conversation(MASTER_ID) as conv:
            await conv.send_message("🎯 **أرسل يوزر البوت المستهدف الجديد:**")
            current_data['system_config']['target_bot'] = (await conv.get_response()).text.strip()
            await conv.send_message("🔗 **أرسل رابط الإحالة الجديد:**")
            current_data['system_config']['referral_link'] = (await conv.get_response()).text.strip()
            await conv.send_message("⏳ **وقت التأخير بين الحسابات (ثواني):**")
            current_data['system_config']['global_delay'] = int((await conv.get_response()).text.strip())
            db.save(current_data)
            await conv.send_message("✅ تم تحديث الإعدادات العامة للمنظومة.")

    elif query == "m_view_logs":
        logs = current_data['audit_logs']
        if not logs: return await event.respond("📝 السجل فارغ حالياً.")
        await event.respond("📝 **سجل العمليات الأخير:**\n\n" + "\n".join(logs))

    elif query == "m_get_tool":
        tool_script = (
            f"from telethon import TelegramClient\nimport asyncio\n"
            f"API_ID = {API_ID}\nAPI_HASH = '{API_HASH}'\n"
            f"async def get_ss():\n"
            f"  async with TelegramClient(None, API_ID, API_HASH) as c:\n"
            f"    print('\\nYour Session String:\\n', c.session.save())\n"
            f"asyncio.run(get_ss())"
        )
        with open("SessionExtractor.py", "w") as f: f.write(tool_script)
        await event.respond("🛠 **أرسل هذا الملف لزبائنك لاستخراج السيشن:**", file="SessionExtractor.py")

    elif query == "m_reboot_system":
        await event.answer("🔄 جاري إعادة تشغيل كافة النسخ...", alert=True)
        os.execl(sys.executable, sys.executable, *sys.argv)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [6] محرك الإقلاع الذاتي (Auto-Boot)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def boot_system():
    """تشغيل كافة بوتات الزبائن المخزنة عند إقلاع السيرفر"""
    if not os.path.exists("sessions"):
        os.makedirs("sessions")
    
    data = db.load()
    logger.info(f"Booting system with {len(data['clients_inventory'])} client instances...")
    
    for client_id, info in data['clients_inventory'].items():
        # فحص الصلاحية قبل التشغيل
        exp_dt = datetime.datetime.strptime(info['expiry'], '%Y-%m-%d')
        if datetime.datetime.now() < exp_dt:
            asyncio.create_task(run_client_instance(client_id, info['token']))
            logger.info(f"Instance for {client_id} started successfully.")
        else:
            logger.warning(f"Instance for {client_id} skipped (Expired).")

if __name__ == "__main__":
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("👑 Imperial Factory is running...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # تشغيل المنظومة
    master_bot.loop.run_until_complete(boot_system())
    master_bot.run_until_disconnected()
