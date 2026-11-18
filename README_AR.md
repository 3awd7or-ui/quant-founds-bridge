# حزمة الربط الفعلي بين QUANT FOUNDS و TradingView

تحتوي هذه الحزمة على كل ما تحتاجه لتفعيل الربط الحي (Live Webhook) بين حسابك على **TradingView** ولوحة **QUANT FOUNDS**:

- `server.py`: خادم FastAPI جاهز يستقبل تنبيهات TradingView ويحفظها في قاعدة بيانات SQLite ويعرض اللوحة مباشرة.
- `index.html`: لوحة QUANT FOUNDS المحدثة بميزة الاستقبال التلقائي المباشر.
- `quant_founds_connector.pine`: مؤشر Pine Script v6 غير معاد الرسم (No-Repaint) جاهز للنسخ في TradingView.
- `requirements.txt` و `Procfile`: ملفات النشر السريع على Render أو Railway.

## الخطوة 1: تشغيل الخادم والحصول على رابط HTTPS

### الخيار أ (تشغيل محلي فوري خلال دقيقة عبر ngrok):
```bash
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8000
```
ثم في نافذة طرفية ثانية شغّل:
```bash
ngrok http 8000
```
انسخ رابط `https://xxxx.ngrok-free.app` الذي يظهر لك.

### الخيار ب (نشر سحابي دائم على Render أو Railway):
1. ارفع هذا المجلد إلى مستودع GitHub.
2. أنشئ Web Service جديداً على Render أو Railway، واختر أمر التشغيل:
   `uvicorn server:app --host 0.0.0.0 --port $PORT`
3. أضف متغير بيئة اختياري باسم `QF_WEBHOOK_SECRET` (الافتراضي: `QF_SECRET_2026`).

## الخطوة 2: إعداد التنبيه (Alert) في TradingView
1. افتح TradingView → **Pine Editor** → الصق محتوى `quant_founds_connector.pine` واضغط **Add to chart**.
2. اضغط على زر **Alerts (التنبيهات)** → اختر الشرط: `QUANT FOUNDS — TradingView Connector v1.0` → **Any alert() function call**.
3. في تبويب **Notifications**، فعّل **Webhook URL** وضع الرابط:
   `https://YOUR-DOMAIN/webhook/tradingview`
4. اضغط **Create**.

## الخطوة 3: تفعيل الاستقبال في اللوحة
افتح اللوحة (سواء مباشرة من `https://YOUR-DOMAIN` أو من هنا)، اذهب إلى تبويب **ربط TradingView**، أدخل رابط الخادم `https://YOUR-DOMAIN` ورمز الحماية `QF_SECRET_2026`، واضغط **تفعيل الربط**.
