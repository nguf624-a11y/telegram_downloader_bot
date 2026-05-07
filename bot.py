import logging
import os
import aiohttp
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN غير موجود!")

ADMIN_ID = 1349568101
user_stats = {}

# Cobalt API Endpoint
COBALT_API = "https://api.cobalt.tools/api/json"

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
        "✅ animation للتحميل\n"
        "✅ إحصائيات مفصلة\n"
        "✅ البوت عراقي منة وبينة 🇮🇶🫠\n"
        "✅ لهجة عراقية أصلية\n"
        "✅ تشغيل 24/7 مستقر\n\n"
        "⏰ **ساعات البوت:**\n"
        "🕐 24/7 مستقر\n"
        "⚡ سرعة البرق\n"
        "🔄 تحديثات مستمرة\n\n"
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

async def download_with_cobalt(url):
    """تحميل الملف باستخدام Cobalt API"""
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "url": url,
                "downloadMode": "auto",
                "quality": "max",
                "isAudioOnly": False,
                "filenamePattern": "basic"
            }
            
            async with session.post(COBALT_API, json=payload, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("status") == "success" and data.get("url"):
                        return data.get("url")
                    else:
                        logger.error(f"Cobalt error: {data}")
                        return None
                else:
                    logger.error(f"Cobalt API error: {resp.status}")
                    return None
    except Exception as e:
        logger.error(f"Cobalt download error: {str(e)}")
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
    
    # إرسال رسالة التحميل مع الانيميشن
    loading_msg = await update.message.reply_text(
        "⠙ جاري التحميل...\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "⬇️ [░░░░░░░░░░] 0%\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "📁 الحجم  : 0 MB / ? MB\n"
        "⚡ السرعة : 0 KB/s\n"
        "⏱ المتبقي: جاري الحساب..."
    )
    
    try:
        # تحميل من Cobalt API
        download_url = await download_with_cobalt(url)
        
        if download_url:
            # تحديث رسالة التحميل
            await loading_msg.edit_text(
                "⠙ جاري التحميل...\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "⬇️ [██████████] 100%\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "📁 الحجم  : تم التحميل\n"
                "⚡ السرعة : ✅ اكتمل\n"
                "⏱ المتبقي: 0s"
            )
            
            # إرسال الملف
            await update.message.reply_video(
                video=download_url,
                caption="✅ وتدلل! تم التحميل بنجاح! 🎉"
            )
            user_stats[user_id]["downloads"] += 1
        else:
            await loading_msg.edit_text("❌ فشل التحميل يا طيب! جرب رابط آخر!")
    except Exception as e:
        error_msg = str(e)[:150]
        logger.error(f"Download error: {error_msg}")
        await loading_msg.edit_text(f"❌ خطأ: {error_msg}")

async def set_commands(app: Application) -> None:
    """إضافة قائمة الأوامر"""
    commands = [
        BotCommand("start", "🔥 بدء البوت"),
        BotCommand("help", "📖 شرح البوت"),
        BotCommand("about", "ℹ️ معلومات البوت"),
        BotCommand("stats", "📊 إحصائيات البوت"),
        BotCommand("broadcast", "📢 إرسال رسالة (مسؤول)"),
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
    
    print("🚀 البوت بدأ يشتغل مع Cobalt API... بوت مثل الطلقة 🔥")
    print("📺 المنصات المدعومة: YouTube, TikTok, Snapchat, Twitter/X, Reddit")
    app.run_polling()

if __name__ == "__main__":
    main()
