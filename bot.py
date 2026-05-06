import logging
import os
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

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
        "🎵 TikTok\n"
        "👻 Snapchat\n"
        "𝕏 Twitter/X\n"
        "🔗 Reddit\n\n"
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
        "   • TikTok\n"
        "   • Snapchat\n"
        "   • Twitter/X\n"
        "   • Reddit\n\n"
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
        "🎵 TikTok\n"
        "👻 Snapchat\n"
        "𝕏 Twitter/X\n"
        "🔗 Reddit\n\n"
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

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ هذا الأمر للمسؤول فقط!")
        return
    
    if not context.args:
        await update.message.reply_text("❌ استخدم: /broadcast <الرسالة>")
        return
    
    message = " ".join(context.args)
    sent_count = 0
    
    await update.message.reply_text("⏳ جاري إرسال الرسالة للجميع...")
    
    for user_id_to_send in user_stats.keys():
        try:
            await context.bot.send_message(
                chat_id=user_id_to_send,
                text=f"📢 **رسالة من المسؤول:**\n\n{message}",
                parse_mode="Markdown"
            )
            sent_count += 1
        except Exception as e:
            logger.error(f"Failed to send to {user_id_to_send}: {str(e)}")
    
    await update.message.reply_text(
        f"✅ تم إرسال الرسالة لـ {sent_count} مستخدم!",
        parse_mode="Markdown"
    )

def download_with_yt_dlp(url):
    """تحميل الملف باستخدام yt-dlp - يدعم كل المنصات"""
    try:
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
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
    
    # المنصات المدعومة
    valid_domains = [
        "youtube.com", "youtu.be",
        "tiktok.com",
        "snapchat.com", "snap.com",
        "twitter.com", "x.com",
        "reddit.com"
    ]
    
    if not any(domain in url for domain in valid_domains):
        await update.message.reply_text("❌ الرابط ما يشتغل معي يا بعد روحي! 😅\n\nالمنصات المدعومة:\n🔴 YouTube\n🎵 TikTok\n👻 Snapchat\n𝕏 Twitter/X\n🔗 Reddit")
        return
    
    await update.message.reply_text("⏳ جاري التحميل عيوني... ثواني ويكون جاهز!")
    
    try:
        file_path = download_with_yt_dlp(url)
        
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
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    
    # إضافة قائمة الأوامر عند البدء
    app.post_init = set_commands
    
    print("🚀 البوت بدأ يشتغل مع yt-dlp... بوت مثل الطلقة 🔥")
    print("📺 المنصات المدعومة: YouTube, TikTok, Snapchat, Twitter/X, Reddit")
    app.run_polling()

if __name__ == "__main__":
    main()
