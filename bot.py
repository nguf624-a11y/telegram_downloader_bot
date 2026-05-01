import logging
import requests
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError

# إعداد السجلات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# التوكن
BOT_TOKEN = "8689457230:AAHkSYe_IEo3HvFrQHuyYHerrjnsA2H1ezQ"
ADMIN_ID = 5838191316

# قاموس لتخزين إحصائيات المستخدمين
user_stats = {}

# خدمات التحميل الموثوقة
DOWNLOAD_SERVICES = {
    "instagram": [
        "https://api.saveig.app/api/download",
        "https://instadownloader.co/api/download",
    ],
    "youtube": [
        "https://api.cobalt.tools/api/json",
        "https://youtube-downloader-api.herokuapp.com/download",
    ],
    "tiktok": [
        "https://api.ssstik.io/fetch",
        "https://tiktok-downloader-api.herokuapp.com/download",
    ],
    "facebook": [
        "https://api.saveig.app/api/download",
    ]
}

async def download_from_instagram(url: str) -> dict:
    """تحميل من Instagram باستخدام خدمات موثوقة"""
    for service_url in DOWNLOAD_SERVICES["instagram"]:
        try:
            payload = {"url": url}
            response = requests.post(service_url, json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if "download_url" in data or "url" in data:
                    return {
                        "success": True,
                        "url": data.get("download_url") or data.get("url"),
                        "type": "video"
                    }
        except Exception as e:
            logger.warning(f"Instagram service failed: {e}")
            continue
    return {"success": False, "error": "فشل التحميل من Instagram"}

async def download_from_youtube(url: str) -> dict:
    """تحميل من YouTube باستخدام خدمات موثوقة"""
    for service_url in DOWNLOAD_SERVICES["youtube"]:
        try:
            payload = {"url": url, "quality": "best"}
            response = requests.post(service_url, json=payload, timeout=60)
            if response.status_code == 200:
                data = response.json()
                if "download_url" in data or "url" in data:
                    return {
                        "success": True,
                        "url": data.get("download_url") or data.get("url"),
                        "type": "video"
                    }
        except Exception as e:
            logger.warning(f"YouTube service failed: {e}")
            continue
    return {"success": False, "error": "فشل التحميل من YouTube"}

async def download_from_tiktok(url: str) -> dict:
    """تحميل من TikTok باستخدام خدمات موثوقة"""
    for service_url in DOWNLOAD_SERVICES["tiktok"]:
        try:
            payload = {"url": url}
            response = requests.post(service_url, json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if "download_url" in data or "url" in data:
                    return {
                        "success": True,
                        "url": data.get("download_url") or data.get("url"),
                        "type": "video"
                    }
        except Exception as e:
            logger.warning(f"TikTok service failed: {e}")
            continue
    return {"success": False, "error": "فشل التحميل من TikTok"}

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
    user_id = update.effective_user.id
    
    # تسجيل الإحصائيات
    if user_id not in user_stats:
        user_stats[user_id] = {"downloads": 0}
    
    # التحقق من نوع الرابط
    if "instagram.com" in url:
        await update.message.reply_text("⏳ جاري التحميل من Instagram عيوني... ثواني ويكون جاهز!")
        result = await download_from_instagram(url)
    elif "youtube.com" in url or "youtu.be" in url:
        await update.message.reply_text("⏳ جاري التحميل من YouTube حبيبي... ثواني ويكون جاهز!")
        result = await download_from_youtube(url)
    elif "tiktok.com" in url:
        await update.message.reply_text("⏳ جاري التحميل من TikTok يا طيب... ثواني ويكون جاهز!")
        result = await download_from_tiktok(url)
    else:
        await update.message.reply_text("❌ الرابط ما يشتغل معي يا بعد روحي! 😅\n\nأرسل رابط من: YouTube, Instagram, TikTok, أو Facebook")
        return
    
    if result["success"]:
        try:
            if result["type"] == "video":
                await update.message.reply_video(
                    video=result["url"],
                    caption="✅ وتدلل! تم التحميل بنجاح! 🎉"
                )
            else:
                await update.message.reply_audio(
                    audio=result["url"],
                    caption="✅ وتدلل! تم التحميل بنجاح! 🎉"
                )
            user_stats[user_id]["downloads"] += 1
        except TelegramError as e:
            await update.message.reply_text(f"❌ فشل الإرسال: {str(e)}")
    else:
        await update.message.reply_text(f"❌ {result['error']}\n\nتأكد من الرابط يا طيب! 🔍")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """أمر المساعدة"""
    await update.message.reply_text(
        "📖 **شرح البوت:**\n\n"
        "1️⃣ أرسل أي رابط من YouTube, Instagram, TikTok, أو Facebook\n"
        "2️⃣ اختر الجودة اللي تريدها\n"
        "3️⃣ البوت يحمل الملف ويرسله لك\n\n"
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
