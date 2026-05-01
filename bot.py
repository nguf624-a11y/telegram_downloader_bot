import os
import asyncio
import logging
import yt_dlp
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
    return "Bot is alive!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# الإعدادات
TOKEN = "8689457230:AAHkSYe_IEo3HvFrQHuyYHerrjnsA2H1ezQ"
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

# دالة التحميل باستخدام yt-dlp
async def download_content(url, mode="video"):
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
    }

    if mode == "video":
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
        logger.error(f"Download error: {e}")
        return None, str(e)

# أمر البداية
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 أهلاً بك في بوت التنزيل المتطور!\n\n"
        "🚀 أرسل لي رابطاً من (يوتيوب، انستقرام، تيك توك، فيسبوك) وسأقوم بتحميله لك بأعلى جودة.\n\n"
        "✅ تم إصلاح مشاكل الصوت والاستقرار.\n"
        "👥 البوت متاح للجميع الآن!"
    )
    await update.message.reply_text(welcome_text)

# معالجة الروابط
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"):
        return

    keyboard = [
        [
            InlineKeyboardButton("🎬 فيديو (أعلى جودة)", callback_data=f"vid|{url}"),
            InlineKeyboardButton("🎵 صوت (MP3)", callback_data=f"aud|{url}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("اختر الصيغة المطلوبة:", reply_markup=reply_markup)

# معالجة أزرار الاختيار
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split("|")
    mode_code = data[0]
    url = data[1]
    mode = "video" if mode_code == "vid" else "audio"

    status_msg = await query.edit_message_text(f"⏳ جاري التحميل... يرجى الانتظار.")

    file_path, result = await download_content(url, mode)

    if file_path and os.path.exists(file_path):
        await status_msg.edit_text("✅ اكتمل التحميل! جاري الإرسال...")
        try:
            with open(file_path, 'rb') as f:
                if mode == "video":
                    await query.message.reply_video(video=f, caption=f"🎬 {result}")
                else:
                    await query.message.reply_audio(audio=f, caption=f"🎵 {result}")
            await status_msg.delete()
        except Exception as e:
            await status_msg.edit_text(f"❌ خطأ أثناء الإرسال: {e}")
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
    else:
        await status_msg.edit_text(f"❌ فشل التحميل. تأكد من الرابط.\nالخطأ: {result}")

if __name__ == '__main__':
    # تشغيل ميزة النبض
    keep_alive()
    
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    logger.info("Bot started with Keep-alive...")
    application.run_polling()
