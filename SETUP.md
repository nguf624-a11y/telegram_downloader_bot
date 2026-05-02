# 🚀 دليل التشغيل الكامل للبوت

## **الحل الأفضل والدائم: Uptime Robot + Render**

### **المرحلة 1: إعداد Render (مجاني)**

#### الخطوات:
1. اذهب إلى: https://render.com
2. سجل بـ GitHub
3. اضغط "New +" → "Web Service"
4. اختر المستودع: `telegram_downloader_bot`
5. الإعدادات:
   - **Name**: telegram-bot
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
   - **Environment Variables**: 
     - `TELEGRAM_BOT_TOKEN`: `8689457230:AAHkSYe_IEo3HvFrQHuyYHerrjnsA2H1ezQ`

6. اضغط "Create Web Service"

---

### **المرحلة 2: إعداد Uptime Robot (مجاني)**

#### الخطوات:
1. اذهب إلى: https://uptimerobot.com
2. سجل حساب مجاني
3. اضغط "Add Monitor"
4. الإعدادات:
   - **Monitor Type**: HTTP(s)
   - **URL**: رابط البوت من Render (مثل: `https://telegram-bot-xxxxx.onrender.com`)
   - **Monitoring Interval**: 5 دقائق
   - **Alert Contacts**: بريدك الإلكتروني

5. اضغط "Create Monitor"

---

### **النتيجة:**

✅ البوت يعمل 24/7 على Render
✅ Uptime Robot يراقبه كل 5 دقائق
✅ إذا توقف البوت → Uptime Robot يعيد تشغيله تلقائياً
✅ مجاني 100% بدون اشتراكات

---

## **متغيرات البيئة المطلوبة:**

```
TELEGRAM_BOT_TOKEN=8689457230:AAHkSYe_IEo3HvFrQHuyYHerrjnsA2H1ezQ
```

---

## **المميزات:**

- ✅ تشغيل 24/7 مستقر
- ✅ مجاني 100%
- ✅ آمن (بدون توكن مباشر في الكود)
- ✅ دعم YouTube + Instagram + TikTok + Facebook
- ✅ سرعة خرافية

---

## **الدعم:**

أي مشكلة، تواصل معي! 💪
