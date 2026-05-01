import os
import asyncio
import logging
import yt_dlp
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from pathlib import Path
from flask import Flask
from threading import Thread

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

# User-Agent وهمي لتجاوز حظر البوتات
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

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

# دالة التحميل باستخدام yt-dlp مع معالجة متقدمة
async def download_content(url, mode="video", quality="best", retry=0):
    max_retries = 3
    
    ydl_opts = {
        'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
        'user_agent': USER_AGENT,
        'http_headers': {
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        },
        'socket_timeout': 60,
        'extractor_args': {
            'youtube': {
                'skip': ['hls', 'dash']
            },
            'instagram': {
                'skip': ['hls', 'dash']
            }
        }
    }

    if mode == "video":
        if quality == "1080p":
            ydl_opts['format'] = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'
        elif quality == "720p":
            ydl_opts['format'] = 'bestvideo[height<=720]+bestaudio/best[height<=720]'
        elif quality == "480p":
            ydl_opts['format'] = 'bestvideo[height<=480]+bestaudio/best[height<=480]'
        else:
            ydl_opts['format'] = 'bestvideo+bestaudio/best'
        ydl_opts['merge_output_format'] = 'mp4'
    elif mode == "audio":
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await asyncio.to_thread(ydl.extract_info, url, download=True)
            file_path = ydl.prepare_filename(info)
            
            if mode == "audio":
                file_path = str(Path(file_path).with_suffix('.mp3'))
            elif mode == "video":
                file_path = str(Path(file_path).with_suffix('.mp4'))
                
            return file_path, info.get('title', 'video')
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Download error (attempt {retry+1}): {error_msg}")
        
        # إعادة المحاولة للأخطاء المؤقتة
        if retry < max_retries and ('Sign in' in error_msg or 'Timeout' in error_msg or '429' in error_msg):
            await asyncio.sleep(2 ** retry)  # Exponential backoff
            return await download_content(url, mode, quality, retry + 1)
        
        return None, error_msg

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
        "• ⚡️ **سرعة خرافية:** البوت شغال 24 ساعة وما يوكف أبداً - مو بوت ظيم.\n\n"
        "👤 **المطور:** @Abdalraouf\n"
        "🚀 **الإصدار:** 2.5 (بواسطة Manus AI)\n\n"
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
    
    logger.info("Bot started with anti-bot-detection measures...")
    application.run_polling()
