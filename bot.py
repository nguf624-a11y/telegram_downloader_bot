import logging
import os
import asyncio
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp
import requests
import json
import shutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN غير موجود!")

ADMIN_ID = 1349568101
user_stats = {}

# إعدادات محسّنة للسرعة
YDL_OPTS = {
    'format': 'best[ext=mp4]/best[ext=webm]/best',
    'quiet': False,
    'no_warnings': False,
    'socket_timeout': 300,
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
    },
    'retries': 20,
    'fragment_retries': 20,
    'skip_unavailable_fragments': True,
    'outtmpl': '/tmp/%(title)s.%(ext)s',
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
        "📸 Instagram\n"
        "🎵 TikTok\n"
        "📘 Facebook\n\n"
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
        "   • Instagram\n"
        "   • TikTok\n"
        "   • Facebook\n\n"
        "2️⃣ البوت يحمل الملف ويرسله لك\n\n"
        "🔥 **الميزات:**\n"
        "✅ تحميل بأعلى جودة\n"
        "✅ سرعة خرافية\n"
        "✅ لهجة عراقية أصلية 🇮🇶",
        parse_mode="Markdown"
    )

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🔥 **بوت مثل الطلقة 🔥**\n\n"
        "حبيبي، هذا بوت تحميل متطور وموثوق 100%!\n\n"
        "📺 **المنصات المدعومة:**\n"
        "🔴 YouTube\n"
        "📸 Instagram\n"
        "🎵 TikTok\n"
        "📘 Facebook\n\n"
        "🌟 **الميزات:**\n"
        "✅ تحميل بأعلى جودة\n"
        "✅ سرعة خرافية\n"
        "✅ البوت عراقي منة وبينة 🇮🇶🫠\n"
        "✅ لهجة عراقية أصلية\n"
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

def download_with_cobalt_api(url):
    """تحميل باستخدام Cobalt API - للـ Instagram و Facebook و TikTok"""
    try:
        # استخدام Cobalt API المجانية
        api_url = "https://api.cobalt.tools/api/json"
        
        payload = {
            "url": url,
            "vCodec": "h264",
            "vQuality": "max",
            "aFormat": "best",
            "filenamePattern": "basic"
        }
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("status") == "success" and data.get("url"):
                # تحميل الملف
                video_url = data.get("url")
                video_response = requests.get(video_url, timeout=30, stream=True)
                
                if video_response.status_code == 200:
                    file_path = f"/tmp/cobalt_{url.split('/')[-1][:20]}.mp4"
                    with open(file_path, "wb") as f:
                        for chunk in video_response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    return file_path
        
        logger.error(f"Cobalt API error: {response.text}")
        return None
    except Exception as e:
        logger.error(f"Cobalt API exception: {str(e)}")
        return None

def download_with_yt_dlp(url, ydl_opts):
    """تحميل الملف باستخدام yt-dlp"""
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            return file_path if os.path.exists(file_path) else None
    except Exception as e:
        logger.error(f"yt-dlp error: {str(e)}")
        return None

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
        file_path = None
        
        # للـ Instagram و Facebook و TikTok - استخدم Cobalt API
        if "instagram.com" in url or "facebook.com" in url or "fb.watch" in url or "tiktok.com" in url:
            logger.info("محاولة Cobalt API...")
            file_path = download_with_cobalt_api(url)
        
        # للـ YouTube - استخدم yt-dlp
        if not file_path and ("youtube.com" in url or "youtu.be" in url):
            logger.info("محاولة yt-dlp...")
            file_path = download_with_yt_dlp(url, YDL_OPTS)
        
        # إذا فشل Cobalt، جرب yt-dlp
        if not file_path:
            logger.info("محاولة yt-dlp كبديل...")
            file_path = download_with_yt_dlp(url, YDL_OPTS)
        
        if file_path and os.path.exists(file_path):
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
            await update.message.reply_text("❌ فشل التحميل يا طيب! جرب رابط آخر!")
    except Exception as e:
        error_msg = str(e)[:150]
        logger.error(f"Download error: {error_msg}")
        await update.message.reply_text(f"❌ خطأ: {error_msg}")

async def set_commands(app: Application) -> None:
    """إضافة قائمة الأوامر"""
    commands = [
        BotCommand("start", "🔥 بدء البوت"),
        BotCommand("help", "📖 شرح البوت"),
        BotCommand("about", "ℹ️ معلومات البوت"),
        BotCommand("stats", "📊 إحصائيات البوت"),
    ]
    await app.bot.set_my_commands(commands)
    logger.info("✅ تم إضافة قائمة الأوامر")

def main() -> None:
    # إنشاء التطبيق
    app = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة المعالجات
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    
    # إضافة قائمة الأوامر عند البدء
    app.post_init = set_commands
    
    print("🚀 البوت بدأ يشتغل مع Cobalt API... بوت مثل الطلقة 🔥")
    app.run_polling()

if __name__ == "__main__":
    main()
