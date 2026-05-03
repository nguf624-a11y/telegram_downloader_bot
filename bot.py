import logging
import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp
from flask import Flask, request
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# قراءة التوكن من متغيرات البيئة
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN غير موجود!")

ADMIN_ID = 5838191316
user_stats = {}

# تحسينات للـ Instagram و YouTube
YDL_OPTS_BASE = {
    'format': 'best[ext=mp4]/best[ext=webm]/best',
    'quiet': False,
    'no_warnings': False,
    'socket_timeout': 120,
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    },
    'retries': 15,
    'fragment_retries': 15,
    'outtmpl': '/tmp/%(title)s.%(ext)s',
}

YDL_OPTS_INSTAGRAM = {
    **YDL_OPTS_BASE,
    'socket_timeout': 180,
    'retries': 20,
}

YDL_OPTS_YOUTUBE = {
    **YDL_OPTS_BASE,
    'format': 'best[ext=mp4]/best',
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    
    if user_id not in user_stats:
        user_stats[user_id] = {"downloads": 0}
    
    await update.message.reply_text(
        f"🔥 **أهلاً وسهلاً يا {first_name}!** 🔥\n\n"
        "أنا بوت تحميل متطور وموثوق 100%!\n\n"
        "📺 **المنصات المدعومة:**\n"
        "🔴 YouTube\n"
        "📸 Instagram (Posts, Reels, Stories)\n"
        "🎵 TikTok\n"
        "📘 Facebook\n\n"
        "🌟 **الميزات:**\n"
        "✅ تحميل بأعلى جودة\n"
        "✅ سرعة خرافية\n"
        "✅ لهجة عراقية أصلية 🇮🇶\n"
        "✅ دعم Instagram Stories و Reels\n"
        "✅ تشغيل 24/7 مستقر\n\n"
        "📝 **الاستخدام:**\n"
        "أرسل أي رابط من المنصات فوق وأنا أحمله لك!\n\n"
        "/help - شرح البوت\n"
        "/about - معلومات البوت",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📖 **شرح البوت:**\n\n"
        "1️⃣ أرسل أي رابط من:\n"
        "   • YouTube\n"
        "   • Instagram (Posts, Reels, Stories)\n"
        "   • TikTok\n"
        "   • Facebook\n\n"
        "2️⃣ البوت يحمل الملف ويرسله لك\n\n"
        "🔥 **الميزات:**\n"
        "✅ تحميل بأعلى جودة\n"
        "✅ سرعة خرافية\n"
        "✅ لهجة عراقية أصلية 🇮🇶\n"
        "✅ دعم Stories و Reels من Instagram",
        parse_mode="Markdown"
    )

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🔥 **بوت مثل الطلقة 🔥**\n\n"
        "حبيبي، هذا بوت تحميل متطور وموثوق 100%!\n\n"
        "📺 **المنصات المدعومة:**\n"
        "🔴 YouTube\n"
        "📸 Instagram (Posts, Reels, Stories)\n"
        "🎵 TikTok\n"
        "📘 Facebook\n\n"
        "🌟 **الميزات:**\n"
        "✅ تحميل بأعلى جودة\n"
        "✅ سرعة خرافية\n"
        "✅ البوت عراقي منة وبينة 🇮🇶🫠\n"
        "✅ لهجة عراقية أصلية\n"
        "✅ دعم Instagram Stories و Reels\n"
        "✅ تشغيل 24/7 مستقر\n\n"
        "👨‍💻 **المطور:** @Abdalraouf",
        parse_mode="Markdown"
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ هذا الأمر للمسؤول فقط!")
        return
    
    total_users = len(user_stats)
    total_downloads = sum(u["downloads"] for u in user_stats.values())
    
    await update.message.reply_text(
        f"📊 **إحصائيات البوت:**\n\n"
        f"👥 عدد المستخدمين: {total_users}\n"
        f"📥 عدد التحميلات: {total_downloads}\n",
        parse_mode="Markdown"
    )

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    url = update.message.text
    user_id = update.effective_user.id
    
    if user_id not in user_stats:
        user_stats[user_id] = {"downloads": 0}
    
    valid_domains = ["youtube.com", "youtu.be", "instagram.com", "tiktok.com", "facebook.com", "fb.watch"]
    if not any(domain in url for domain in valid_domains):
        await update.message.reply_text("❌ الرابط ما يشتغل معي يا بعد روحي! 😅")
        return
    
    await update.message.reply_text("⏳ جاري التحميل عيوني... ثواني ويكون جاهز!")
    
    try:
        if "instagram.com" in url:
            ydl_opts = YDL_OPTS_INSTAGRAM
        elif "youtube.com" in url or "youtu.be" in url:
            ydl_opts = YDL_OPTS_YOUTUBE
        else:
            ydl_opts = YDL_OPTS_BASE
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                
                if file_size > 2 * 1024 * 1024 * 1024:
                    await update.message.reply_text("❌ الملف كبير جداً! (أكثر من 2GB)")
                    os.remove(file_path)
                    return
                
                with open(file_path, "rb") as f:
                    await update.message.reply_video(
                        video=f,
                        caption="✅ وتدلل! تم التحميل بنجاح! 🎉"
                    )
                user_stats[user_id]["downloads"] += 1
                os.remove(file_path)
            else:
                await update.message.reply_text("❌ فشل التحميل يا طيب!")
    except Exception as e:
        error_msg = str(e)[:100]
        logger.error(f"Download error: {error_msg}")
        await update.message.reply_text(f"❌ خطأ: {error_msg}")

# إعداد Flask
app = Flask(__name__)
telegram_app = None

@app.route("/webhook", methods=["POST"])
async def webhook():
    try:
        data = request.get_json()
        update = Update.de_json(data, telegram_app.bot)
        await telegram_app.process_update(update)
        return "OK", 200
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return "Error", 500

@app.route("/health", methods=["GET"])
def health():
    return "🔥 البوت شغال وتمام التمام! 🔥", 200

@app.route("/", methods=["GET"])
def index():
    return "🚀 بوت التحميل يعمل بنجاح! 🚀", 200

async def main():
    global telegram_app
    
    telegram_app = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة المعالجات
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CommandHandler("help", help_command))
    telegram_app.add_handler(CommandHandler("about", about_command))
    telegram_app.add_handler(CommandHandler("stats", stats_command))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    
    # إعداد Webhook
    webhook_url = os.getenv("RENDER_EXTERNAL_URL", "https://my-downloader-bot-nn7g.onrender.com")
    if webhook_url.endswith("/"):
        webhook_url = webhook_url[:-1]
    webhook_url = f"{webhook_url}/webhook"
    
    try:
        await telegram_app.bot.delete_webhook(drop_pending_updates=True)
        await telegram_app.bot.set_webhook(url=webhook_url)
        logger.info(f"✅ Webhook تم تفعيله: {webhook_url}")
    except Exception as e:
        logger.error(f"❌ خطأ في Webhook: {e}")
    
    # تشغيل Flask
    port = int(os.getenv("PORT", 5000))
    print(f"🚀 البوت بدأ يشتغل على Webhook... بوت مثل الطلقة 🔥")
    app.run(host="0.0.0.0", port=port, debug=False)

if __name__ == "__main__":
    asyncio.run(main())
