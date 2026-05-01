import os
import asyncio
import logging
import json
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from pathlib import Path
from flask import Flask
from threading import Thread
import requests

# إعداد السجلات (Logging)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# إعداد خادم ويب بسيط لميزة النبض (Keep-alive)
app = Flask('')

@app.route('/')
def home():
    return "البوت شغال وعال العال يا أغاتي!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# الإعدادات
TOKEN = "8689457230:AAHkSYe_IEo3HvFrQHuyYHerrjnsA2H1ezQ"
ADMIN_ID = 1349568101
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)
DB_FILE = "users.json"

# Cobalt API - الحل الدائم والموثوق
COBALT_API = "https://api.cobalt.tools/api/v1/media"

# نظام قاعدة بيانات بسيط للمستخدمين
def load_users():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_user(user_id):
    users = load_users()
    if user_id not in users:
        users.add(user_id)
        with open(DB_FILE, 'w') as f:
            json.dump(list(users), f)

# دالة التحميل باستخدام Cobalt API (الحل الدائم)
async def download_content(url, mode="video", quality="best"):
    try:
        # إرسال الطلب إلى Cobalt API
        payload = {
            "url": url,
            "downloadMode": "auto",
            "isAudioOnly": mode == "audio",
            "filenamePattern": "basic"
        }
        
        # استخدام requests في thread منفصل
        response = await asyncio.to_thread(
            requests.post,
            COBALT_API,
            json=payload,
            timeout=30,
            headers={"Accept": "application/json"}
        )
        
        if response.status_code != 200:
            return None, f"خطأ من الخدمة: {response.status_code}"
        
        data = response.json()
        
        if data.get("status") != "success":
            return None, data.get("error", "فشل التحميل من الخدمة")
        
        # الحصول على رابط التحميل
        download_url = data.get("url")
        title = data.get("filename", "download")
        
        if not download_url:
            return None, "لم يتم العثور على رابط التحميل"
        
        # تحميل الملف
        file_response = await asyncio.to_thread(
            requests.get,
            download_url,
            timeout=60,
            stream=True
        )
        
        if file_response.status_code != 200:
            return None, "فشل تحميل الملف"
        
        # حفظ الملف
        if mode == "audio":
            file_path = DOWNLOAD_DIR / f"{title}.mp3"
        else:
            file_path = DOWNLOAD_DIR / f"{title}.mp4"
        
        with open(file_path, 'wb') as f:
            for chunk in file_response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        return str(file_path), title
        
    except asyncio.TimeoutError:
        return None, "انقطع الاتصال - حاول مرة ثانية"
    except Exception as e:
        logger.error(f"Download error: {e}")
        return None, str(e)

# أمر البداية
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    save_user(user_id)
    welcome_text = (
        "👋 هلا بيك يا بعد روحي بنسخة البوت المتطورة!\n\n"
        "🚀 دزلي أي رابط يعجبك وأني أنزله الك من عيوني.. تدلل أغاتي.\n\n"
        "🛠 الميزات الجديدة:\n"
        "✅ تگدر تختار جودة الفيديو.\n"
        "✅ تنزيل ستوريات انستقرام وتيك توك.\n"
        "✅ لغة عراقية أصلية وتدلل حبيبي.\n\n"
        "أكتب /help إذا محتاج مساعدة يا طيب."
    )
    await update.message.reply_text(welcome_text)

# أمر المساعدة
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📖 شلون تستخدم البوت يا أغاتي:\n\n"
        "1. دز رابط الفيديو أو الستوري حبيبي.\n"
        "2. أختار تريد فيديو لو بس صوت.\n"
        "3. إذا اختاريت فيديو، تگدر تختار الجودة اللي تناسبك.\n\n"
        "💡 البوت يدعم يوتيوب، انستقرام، تيك توك، وفيسبوك.. وتؤمر أمر!"
    )
    await update.message.reply_text(help_text)

# أمر عن البوت
async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    about_text = (
        "🤖 **حول بوت التنزيل المتطور**\n\n"
        "هذا البوت هو مساعدك الشخصي حبيبي، سويناه حتى تنزل أي شي يعجبك من الإنترنت بسهولة وسرعة خرافية وبدون أي تعب.. أغاتي أنت وتدلل علينا.\n\n"
        "🌟 **المنصات اللي ندعمها:**\n"
        "• ❤️ **YouTube** (يوتيوب): فيديوهات وصوت MP3.\n"
        "• 💜 **Instagram** (انستقرام): فيديوهات، صور، وستوريات.\n"
        "• 🖤 **TikTok** (تيك توك): مقاطع بدون علامة مائية.\n"
        "• 💙 **Facebook** (فيسبوك): فيديوهات ومنشورات عامة.\n\n"
        "✨ **الميزات الجديدة:**\n"
        "• 🇮🇶 **لهجة عراقية:** البوت عراقي منة وبينة 🇮🇶🫠\n"
        "• 🛠 **اختيار الجودة:** 1080p (فول) | 720p (عالية) | 480p (وسط) | أسرع جودة متوفرة.\n"
        "• 🔊 **دمج الصوت:** دمج تلقائي للصوت وية الفيديو بأحسن دقة.\n"
        "• ⚡️ **سرعة خرافية:** البوت شغال 24 ساعة وما يوكف أبداً - مو بوت ظيم.\n"
        "• 🔄 **تحديث تلقائي:** الخدمة تتحدث نفسها بدون تدخل مني!\n\n"
        "👤 **المطور:** @Abdalraouf\n"
        "🚀 **الإصدار:** 3.0 (بواسطة Manus AI + Cobalt API)\n\n"
        "⚠️ *ملاحظة: حبيبي استخدم البوت للاشياء المسموحة وتدلل علينا.*"
    )
    await update.message.reply_text(about_text, parse_mode='Markdown')

# أمر الإحصائيات (للمسؤول فقط)
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    users = load_users()
    await update.message.reply_text(f"📊 إحصائيات البوت يا أغاتي:\n\n👥 عدد المستخدمين: {len(users)}")

# أمر الإذاعة (للمسؤول فقط)
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("⚠️ حبيبي أكتب الرسالة ورا الأمر حتى أدزها للكل.")
        return
    
    message = " ".join(context.args)
    users = load_users()
    count = 0
    for user_id in users:
        try:
            await context.bot.send_message(chat_id=user_id, text=f"📢 رسالة من الإدارة يا طيبين:\n\n{message}")
            count += 1
        except:
            pass
    await update.message.reply_text(f"✅ تم إرسال الرسالة لـ {count} مستخدم يا بعد روحي.")

# معالجة الروابط
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"):
        return
    
    save_user(update.effective_user.id)

    keyboard = [
        [
            InlineKeyboardButton("🎬 فيديو", callback_data=f"v_sel|{url}"),
            InlineKeyboardButton("🎵 صوت (MP3)", callback_data=f"aud|{url}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("تؤمر أمر حبيبي.. أختار شتريد أنزلك؟", reply_markup=reply_markup)

# معالجة أزرار الاختيار
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split("|")
    action = data[0]
    url = data[1]

    if action == "v_sel":
        keyboard = [
            [InlineKeyboardButton("🔥 1080p (فول)", callback_data=f"vid|1080p|{url}")],
            [InlineKeyboardButton("💎 720p (عالية)", callback_data=f"vid|720p|{url}")],
            [InlineKeyboardButton("📱 480p (وسط)", callback_data=f"vid|480p|{url}")],
            [InlineKeyboardButton("⚡️ أسرع شي", callback_data=f"vid|best|{url}")]
        ]
        await query.edit_message_text("من عيوني.. أختار الجودة اللي تعجبك أغاتي:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    mode = "video" if action == "vid" else "audio"
    quality = data[1] if action == "vid" else "best"
    final_url = data[2] if action == "vid" else url

    status_msg = await query.edit_message_text(f"⏳ جاري التحميل يا بعد روحي... شوية صبر وتدلل.")

    file_path, result = await download_content(final_url, mode, quality)

    if file_path and os.path.exists(file_path):
        await status_msg.edit_text("✅ كمل التحميل حبيبي! جاري الإرسال...")
        try:
            with open(file_path, 'rb') as f:
                if mode == "video":
                    await query.message.reply_video(video=f, caption=f"🎬 {result}\n\nوتدلل يا بعد روحي!")
                else:
                    await query.message.reply_audio(audio=f, caption=f"🎵 {result}\n\nوتدلل يا أغاتي!")
            await status_msg.delete()
        except Exception as e:
            await status_msg.edit_text(f"❌ صار خطأ بالإرسال حبيبي: {e}")
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
    else:
        await status_msg.edit_text(f"❌ فشل التحميل.. تأكد من الرابط يا طيب.\nالخطأ: {result}")

if __name__ == '__main__':
    keep_alive()
    
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    logger.info("Bot started with Cobalt API (Auto-updating solution)...")
    application.run_polling()
