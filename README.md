# 🎓 Kurs sotuvchi Telegram bot — Render'ga joylash qo'llanmasi

## 📁 Fayllar
| Fayl | Vazifasi |
|---|---|
| `bot.py` | Bot kodi |
| `data.json` | Kurslar, kategoriyalar, "Biz haqimizda", aloqa, savol-javoblar (uz + ru) |
| `requirements.txt` | Kutubxonalar |
| `render.yaml` | Render sozlamasi (ixtiyoriy) |

## ✨ Bot imkoniyatlari
- 🌐 O'zbek / Rus tili (istalgan vaqt almashtiriladi)
- 🎓 Kategoriyalar bo'yicha kurslar katalogi, rasm, narx, reyting, o'qituvchi, davomiyligi
- 📖 Har bir kurs dasturi (modullar ro'yxati)
- 🔥 Chegirmadagi kurslar (eski narx chizilgan holda)
- 🔍 Kurs qidirish
- ⭐ Saralanganlar
- 📝 Ariza qoldirish (ism + telefon) → adminga darhol xabar boradi
- 📋 Foydalanuvchining arizalari tarixi
- ℹ️ Biz haqimizda, 📞 Aloqa, ❓ Savol-javob
- 🛠 Admin: `/admin` (statistika), `/leads` (oxirgi arizalar), `/broadcast matn` (hammaga xabar)

## ✏️ Kurslarni o'zgartirish
`data.json` faylini oching va kurslarni tahrirlang:
- `image` — rasm havolasi (to'g'ridan-to'g'ri `.jpg/.png` URL). Hozirgi `picsum.photos` havolalari faqat namuna.
- `price` / `old_price` — narx (`old_price` bo'lsa kurs "Chegirmalar" bo'limiga tushadi; kerak bo'lmasa o'chirib tashlang).
- Yangi kurs qo'shish uchun mavjud kursni nusxalab, `id` ni noyob qiling.
- Fayl o'zgargach GitHub'ga push qiling — Render o'zi qayta ishga tushiradi.

## 💻 Kompyuterda sinash (ixtiyoriy)
```bash
pip install -r requirements.txt
export BOT_TOKEN="123456:ABC..."      # Windows: set BOT_TOKEN=...
export ADMIN_IDS="123456789"
python bot.py
```
`BASE_URL` bo'lmasa bot avtomatik polling rejimida ishlaydi.

## 🚀 Render'ga joylash (qadam-baqadam)

### 1-qadam. Kodni GitHub'ga yuklang
1. https://github.com da yangi **private** repository oching (masalan `course-bot`).
2. `course-bot` papkasidagi barcha fayllarni (`bot.py`, `data.json`, `requirements.txt`, `render.yaml`, `.gitignore`) yuklang.
   > ⚠️ Bot tokenini kodga yoki GitHub'ga **yozmang**. U faqat Render'da environment o'zgaruvchisi sifatida kiritiladi.

### 2-qadam. Ma'lumotlarni tayyorlang
- **BOT_TOKEN** — @BotFather dan olingan token.
- **ADMIN_IDS** — sizning Telegram ID raqamingiz (@userinfobot ga `/start` yozsangiz ko'rsatadi). Bir nechta admin bo'lsa vergul bilan: `111,222`.

### 3-qadam. Render'da Web Service yarating
1. https://render.com ga GitHub orqali kiring.
2. **New +** → **Web Service** → repositoryingizni tanlang.
3. Sozlamalar:
   - **Language/Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
   - **Instance Type:** `Free`
4. **Environment Variables** bo'limida qo'shing:

| Key | Value |
|---|---|
| `BOT_TOKEN` | BotFather tokeni |
| `ADMIN_IDS` | Sizning Telegram ID |
| `WEBHOOK_SECRET` | istalgan uzun tasodifiy matn (masalan `k8Jd92hSdf72jsA`) |
| `PYTHON_VERSION` | `3.12.3` |

5. **Create Web Service** ni bosing.

> Render `RENDER_EXTERNAL_URL` ni o'zi beradi, bot webhook'ni avtomatik shu manzilga o'rnatadi — qo'shimcha hech narsa qilish shart emas.

### 4-qadam. Tekshirish
- Render **Logs** bo'limida `Webhook: https://...onrender.com/webhook` yozuvi chiqishi kerak.
- Brauzerda servis manzilini oching — `Bot ishlayapti ✅` ko'rinadi.
- Telegram'da botingizga `/start` yuboring.

## ⚠️ Muhim eslatmalar (Free tarif)
1. **Uxlab qolish:** 15 daqiqa so'rov bo'lmasa Render servisni uxlatadi; keyingi xabarda bot 30–60 soniyada uyg'onadi. Bunga yo'l qo'ymaslik uchun https://uptimerobot.com da servis manziliga har 5 daqiqada ping yuboradigan monitor qo'ying yoki pullik tarifga o'ting (Starter).
2. **Ma'lumotlar bazasi:** Free tarifda fayl tizimi vaqtinchalik — qayta deploy/restart bo'lganda `bot.db` (foydalanuvchilar, arizalar, saralanganlar) o'chib ketadi. Arizalar adminga Telegram orqali darhol yuboriladi, shuning uchun yo'qolmaydi. Doimiy saqlash kerak bo'lsa: pullik tarifda **Disk** ulang (Mount path `/data`, env: `DB_PATH=/data/bot.db`) yoki tashqi baza (masalan Postgres) ishlating.
3. **Xavfsizlik:** token faqat Render environment'da turishi kerak. Agar token oshkor bo'lsa, @BotFather → `/revoke` orqali yangilang.

## 🔧 Muammolar
| Muammo | Yechim |
|---|---|
| Bot javob bermayapti | Render Logs'ni tekshiring; `BOT_TOKEN` to'g'riligini ko'ring |
| Rasm chiqmayapti | `data.json` dagi `image` havolasi to'g'ridan-to'g'ri rasmga olib borishi kerak |
| Adminga ariza kelmayapti | `ADMIN_IDS` to'g'ri va admin botga avval `/start` bosgan bo'lishi kerak |
| Deploy xato beryapti | `PYTHON_VERSION=3.12.3` qo'yilganini tekshiring |
