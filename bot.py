import logging
import subprocess
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError
import yt_dlp

# إعداد السجلات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# التوكن
BOT_TOKEN = "8689457230:AAHkSYe_IEo3HvFrQHuyYHerrjnsA2H1ezQ"
ADMIN_ID = 5838191316

# قاموس لتخزين إحصائيات المستخدمين
user_stats = {}

# إعدادات yt-dlp المتقدمة
YDL_OPTS = {
    'format': 'best[ext=mp4]/best',
    'quiet': False,
    'no_warnings': False,
    'socket_timeout': 120,
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    },
    'extractor_args': {
        'youtube': {
            'player_client': ['web'],
        }
    },
    'retries': 10,
    'fragment_retries': 10,
}

async def download_video(url: str, quality: str = "best") -> dict:
    """تحميل فيديو باستخدام yt-dlp مع معالجة متقدمة"""
    try:
        opts = YDL_OPTS.copy()
        
        # تحديد الجودة
        if quality == "480p":
            opts['format'] = 'best[height<=480]/best'
        elif quality == "720p":
            opts['format'] = 'best[height<=720]/best'
        elif quality == "1080p":
            opts['format'] = 'best[height<=1080]/best'
        
        opts['outtmpl'] = '/tmp/%(title)s.%(ext)s'
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            
            if os.path.exists(file_path):
                return {
                    "success": True,
                    "file_path": file_path,
                    "title": info.get('title', 'Video')
                }
    except Exception as e:
        logger.error(f"Download error: {e}")
    
    return {"success": False, "error": "فشل التحميل"}

async def download_audio(url: str) -> dict:
    """تحميل صوت باستخدام yt-dlp"""
    try:
        opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': False,
            'no_warnings': False,
            'socket_timeout': 120,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            'retries': 10,
            'outtmpl': '/tmp/%(title)s.%(ext)s',
        }
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')
            
            if os.path.exists(file_path):
                return {
                    "success": True,
                    "file_path": file_path,
                    "title": info.get('title', 'Audio')
                }
    except Exception as e:
        logger.error(f"Audio download error: {e}")
    
    return {"success": False, "error": "فشل التحميل"}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """أمر البدء"""
    user_id = update.effective_user.id
    if user_id not in user_stats:
        user_stats[user_id] = {"downloads": 0}
    
    keyboard = [
        [InlineKeyboardButton("📺 فيديو", callback_data="video")],
        [InlineKeyboardButton("🎵 صوت", callback_data="audio")],
        [InlineKeyboardButton("ℹ️ حول البوت", callback_data="about")],
        [InlineKeyboardButton("📖 المساعدة", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔥 هلا بيك حبيبي! 🔥\n\n"
        "أنا بوت تحميل ذكي وسريع جداً! 💨\n"
        "أرسل لي أي رابط من:\n"
        "📺 YouTube | 📸 Instagram | 🎵 TikTok | 📘 Facebook\n\n"
        "وأنا بحمله لك بأعلى جودة! 🚀",
        reply_markup=reply_markup
    )

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالجة الروابط"""
    url = update.message.text
    user_id = update.effective_user.user.id
    
    # تسجيل الإحصائيات
    if user_id not in user_stats:
        user_stats[user_id] = {"downloads": 0}
    
    # التحقق من صحة الرابط
    valid_domains = ["youtube.com", "youtu.be", "instagram.com", "tiktok.com", "facebook.com"]
    if not any(domain in url for domain in valid_domains):
        await update.message.reply_text("❌ الرابط ما يشتغل معي يا بعد روحي! 😅\n\nأرسل رابط من: YouTube, Instagram, TikTok, أو Facebook")
        return
    
    # رسالة الانتظار
    await update.message.reply_text("⏳ جاري التحميل عيوني... ثواني ويكون جاهز!")
    
    # تحميل الفيديو
    result = await download_video(url)
    
    if result["success"]:
        try:
            with open(result["file_path"], "rb") as f:
                await update.message.reply_video(
                    video=f,
                    caption="✅ وتدلل! تم التحميل بنجاح! 🎉"
                )
            user_stats[user_id]["downloads"] += 1
            
            # حذف الملف بعد الإرسال
            try:
                os.remove(result["file_path"])
            except:
                pass
        except Exception as e:
            await update.message.reply_text(f"❌ فشل الإرسال: {str(e)[:100]}")
    else:
        await update.message.reply_text(f"❌ {result['error']}\n\nتأكد من الرابط يا طيب! 🔍")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """أمر المساعدة"""
    await update.message.reply_text(
        "📖 **شرح البوت:**\n\n"
        "1️⃣ أرسل أي رابط من YouTube, Instagram, TikTok, أو Facebook\n"
        "2️⃣ البوت يحمل الملف ويرسله لك\n"
        "3️⃣ استمتع بالفيديو أو الصوت!\n\n"
        "🔥 **الميزات:**\n"
        "✅ تحميل بأعلى جودة\n"
        "✅ دعم الصوت والفيديو\n"
        "✅ سرعة خرافية - مو بوت ظيم\n"
        "✅ لهجة عراقية أصلية 🇮🇶\n\n"
        "📞 **للمساعدة:** أرسل /about",
        parse_mode="Markdown"
    )

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """أمر حول البوت"""
    await update.message.reply_text(
        "🔥 **بوت مثل الطلقة 🔥**\n\n"
        "حبيبي، هذا بوت تحميل متطور وموثوق 100%!\n\n"
        "📺 **المنصات المدعومة:**\n"
        "🔴 YouTube\n"
        "📸 Instagram (ستوريات وريلز)\n"
        "🎵 TikTok\n"
        "📘 Facebook\n\n"
        "🌟 **الميزات:**\n"
        "✅ تحميل بأعلى جودة\n"
        "✅ دمج الصوت والفيديو تلقائياً\n"
        "✅ سرعة خرافية - مو بوت ظيم\n"
        "✅ البوت عراقي منة وبينة 🇮🇶🫠\n"
        "✅ لهجة عراقية أصلية\n\n"
        "⚠️ **تنبيه:** استخدم البوت بمسؤولية واحترم حقوق الملكية\n\n"
        "👨‍💻 **المطور:** @Abdalraouf",
        parse_mode="Markdown"
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """أمر الإحصائيات (للمسؤول فقط)"""
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

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """أمر الإذاعة (للمسؤول فقط)"""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ هذا الأمر للمسؤول فقط!")
        return
    
    if not context.args:
        await update.message.reply_text("❌ أرسل الرسالة بعد الأمر!")
        return
    
    message = " ".join(context.args)
    count = 0
    
    for user_id_to_send in user_stats.keys():
        try:
            await context.bot.send_message(user_id_to_send, f"📢 {message}")
            count += 1
        except:
            pass
    
    await update.message.reply_text(f"✅ تم إرسال الرسالة لـ {count} مستخدم!")

def main() -> None:
    """بدء البوت"""
    app = Application.builder().token(BOT_TOKEN).build()
    
    # أوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    
    # معالجة الروابط
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    
    # بدء البوت
    print("🚀 البوت بدأ يشتغل... بوت مثل الطلقة 🔥")
    app.run_polling()

if __name__ == "__main__":
    main()
