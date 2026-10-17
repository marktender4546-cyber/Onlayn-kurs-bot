"""
Online kurslar uchun Telegram bot (aiogram 3).
Tillar: O'zbekcha / Русский. To'lov yo'q - faqat ko'rish va ariza qoldirish.
Render'da webhook rejimida, kompyuterda polling rejimida ishlaydi.
"""
import asyncio
import html
import json
import logging
import os
import re
import sqlite3
from pathlib import Path

from aiohttp import web
from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton as IB,
    KeyboardButton,
    Message,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("coursebot")

# ----------------------------------------------------------------- SOZLAMALAR
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_IDS", "").replace(" ", "").split(",") if x}
BASE_URL = os.getenv("BASE_URL") or os.getenv("RENDER_EXTERNAL_URL", "")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "change-me-secret-123")
WEBHOOK_PATH = "/webhook"
PORT = int(os.getenv("PORT", "10000"))
DB_PATH = os.getenv("DB_PATH", "bot.db")

DATA = json.loads((Path(__file__).parent / "data.json").read_text(encoding="utf-8"))
COURSES = {c["id"]: c for c in DATA["courses"]}
CATEGORIES = DATA["categories"]

# ------------------------------------------------------------------- MATNLAR
T = {
    "uz": {
        "choose_lang": "🌍 Tilni tanlang",
        "welcome": "👋 Salom, <b>{name}</b>!\n\n🎓 Bizning o'quv markazimizga xush kelibsiz.\nQuyidagi menyudan kerakli bo'limni tanlang 👇",
        "m_courses": "🎓 Kurslar",
        "m_discounts": "🔥 Chegirmalar",
        "m_search": "🔍 Qidiruv",
        "m_fav": "⭐ Saralanganlar",
        "m_apps": "📋 Arizalarim",
        "m_about": "ℹ️ Biz haqimizda",
        "m_contact": "📞 Aloqa",
        "m_faq": "❓ Savol-javob",
        "m_lang": "🌐 Til",
        "choose_cat": "📂 <b>Yo'nalishni tanlang:</b>",
        "all": "📚 Barcha kurslar",
        "courses_in": "🎓 <b>{cat}</b>\nKursni tanlang 👇",
        "no_courses": "😔 Hozircha kurslar topilmadi.",
        "back": "⬅️ Orqaga",
        "register": "📝 Ro'yxatdan o'tish",
        "program": "📖 Dastur",
        "fav_add": "⭐ Saralash",
        "fav_del": "💫 Saralangandan olish",
        "fav_added": "⭐ Saralanganlarga qo'shildi",
        "fav_removed": "Saralanganlardan olib tashlandi",
        "level": "Daraja",
        "duration": "Davomiyligi",
        "lessons": "Darslar",
        "teacher": "O'qituvchi",
        "rating": "Reyting",
        "price": "Narxi",
        "currency": "so'm",
        "lessons_n": "{n} ta dars",
        "ask_name": "👤 Ism-familiyangizni kiriting:",
        "ask_phone": "📱 Telefon raqamingizni yuboring (tugmani bosing yoki +998901234567 ko'rinishida yozing):",
        "send_phone": "📱 Raqamni yuborish",
        "cancel": "❌ Bekor qilish",
        "bad_phone": "⚠️ Raqam noto'g'ri. Qaytadan kiriting (masalan: +998901234567):",
        "done": "✅ <b>Arizangiz qabul qilindi!</b>\n\n🎓 Kurs: <b>{course}</b>\nMenejerimiz tez orada siz bilan bog'lanadi 📞",
        "cancelled": "Bekor qilindi. Asosiy menyu 👇",
        "ask_search": "🔍 Kurs nomini yozing:",
        "search_res": "🔍 <b>Natijalar:</b>",
        "no_results": "😔 Hech narsa topilmadi. Boshqa so'z bilan urinib ko'ring.",
        "no_fav": "⭐ Saralangan kurslar yo'q.",
        "fav_title": "⭐ <b>Saralangan kurslar:</b>",
        "no_apps": "📋 Sizda hali arizalar yo'q.",
        "apps_title": "📋 <b>Arizalaringiz:</b>",
        "no_disc": "🔥 Hozircha chegirmalar yo'q.",
        "disc_title": "🔥 <b>Chegirmadagi kurslar:</b>",
        "faq_title": "❓ <b>Ko'p beriladigan savollar</b>",
        "lang_set": "✅ Til o'zgartirildi.",
        "details": "📖 <b>{title}</b>\n\n{desc}\n\n<b>🗂 Kurs dasturi:</b>\n{program}",
    },
    "ru": {
        "choose_lang": "🌍 Выберите язык",
        "welcome": "👋 Привет, <b>{name}</b>!\n\n🎓 Добро пожаловать в наш учебный центр.\nВыберите нужный раздел в меню ниже 👇",
        "m_courses": "🎓 Курсы",
        "m_discounts": "🔥 Скидки",
        "m_search": "🔍 Поиск",
        "m_fav": "⭐ Избранное",
        "m_apps": "📋 Мои заявки",
        "m_about": "ℹ️ О нас",
        "m_contact": "📞 Контакты",
        "m_faq": "❓ Вопросы и ответы",
        "m_lang": "🌐 Язык",
        "choose_cat": "📂 <b>Выберите направление:</b>",
        "all": "📚 Все курсы",
        "courses_in": "🎓 <b>{cat}</b>\nВыберите курс 👇",
        "no_courses": "😔 Курсы пока не найдены.",
        "back": "⬅️ Назад",
        "register": "📝 Записаться",
        "program": "📖 Программа",
        "fav_add": "⭐ В избранное",
        "fav_del": "💫 Убрать из избранного",
        "fav_added": "⭐ Добавлено в избранное",
        "fav_removed": "Удалено из избранного",
        "level": "Уровень",
        "duration": "Длительность",
        "lessons": "Уроки",
        "teacher": "Преподаватель",
        "rating": "Рейтинг",
        "price": "Цена",
        "currency": "сум",
        "lessons_n": "{n} уроков",
        "ask_name": "👤 Введите ваше имя и фамилию:",
        "ask_phone": "📱 Отправьте номер телефона (нажмите кнопку или введите в формате +998901234567):",
        "send_phone": "📱 Отправить номер",
        "cancel": "❌ Отмена",
        "bad_phone": "⚠️ Неверный номер. Введите ещё раз (например: +998901234567):",
        "done": "✅ <b>Ваша заявка принята!</b>\n\n🎓 Курс: <b>{course}</b>\nНаш менеджер скоро свяжется с вами 📞",
        "cancelled": "Отменено. Главное меню 👇",
        "ask_search": "🔍 Введите название курса:",
        "search_res": "🔍 <b>Результаты:</b>",
        "no_results": "😔 Ничего не найдено. Попробуйте другое слово.",
        "no_fav": "⭐ В избранном пока пусто.",
        "fav_title": "⭐ <b>Избранные курсы:</b>",
        "no_apps": "📋 У вас пока нет заявок.",
        "apps_title": "📋 <b>Ваши заявки:</b>",
        "no_disc": "🔥 Скидок пока нет.",
        "disc_title": "🔥 <b>Курсы со скидкой:</b>",
        "faq_title": "❓ <b>Частые вопросы</b>",
        "lang_set": "✅ Язык изменён.",
        "details": "📖 <b>{title}</b>\n\n{desc}\n\n<b>🗂 Программа курса:</b>\n{program}",
    },
}


def t(lang: str, key: str, **kw) -> str:
    return T[lang][key].format(**kw) if kw else T[lang][key]


def both(key: str) -> set:
    return {T["uz"][key], T["ru"][key]}


def money(n: int) -> str:
    return f"{n:,}".replace(",", " ")


# ------------------------------------------------------------------- BAZA
def q(sql, args=(), one=False, commit=False):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(sql, args)
        if commit:
            conn.commit()
            return cur.lastrowid
        return cur.fetchone() if one else cur.fetchall()
    finally:
        conn.close()


def init_db():
    q("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY, lang TEXT, name TEXT, username TEXT,
        joined TEXT DEFAULT CURRENT_TIMESTAMP)""", commit=True)
    q("""CREATE TABLE IF NOT EXISTS leads(
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, course_id TEXT,
        name TEXT, phone TEXT, created TEXT DEFAULT CURRENT_TIMESTAMP)""", commit=True)
    q("""CREATE TABLE IF NOT EXISTS favs(
        user_id INTEGER, course_id TEXT, PRIMARY KEY(user_id, course_id))""", commit=True)


def upsert_user(u):
    q("INSERT OR IGNORE INTO users(id, name, username) VALUES(?,?,?)",
      (u.id, u.full_name, u.username), commit=True)
    q("UPDATE users SET name=?, username=? WHERE id=?",
      (u.full_name, u.username, u.id), commit=True)


def get_lang(uid: int):
    r = q("SELECT lang FROM users WHERE id=?", (uid,), one=True)
    return r["lang"] if r and r["lang"] else None


def lng(uid: int) -> str:
    return get_lang(uid) or "uz"


def is_fav(uid, cid) -> bool:
    return q("SELECT 1 FROM favs WHERE user_id=? AND course_id=?", (uid, cid), one=True) is not None


# ------------------------------------------------------------- KLAVIATURALAR
def lang_kb():
    b = InlineKeyboardBuilder()
    b.button(text="🇺🇿 O'zbekcha", callback_data="lang:uz")
    b.button(text="🇷🇺 Русский", callback_data="lang:ru")
    b.adjust(2)
    return b.as_markup()


def menu_kb(lang):
    b = ReplyKeyboardBuilder()
    for k in ("m_courses", "m_discounts", "m_search", "m_fav", "m_apps", "m_about", "m_contact", "m_faq", "m_lang"):
        b.button(text=t(lang, k))
    b.adjust(2, 2, 2, 2, 1)
    return b.as_markup(resize_keyboard=True)


def cat_kb(lang):
    b = InlineKeyboardBuilder()
    for c in CATEGORIES:
        b.button(text=f"{c['icon']} {c[lang]}", callback_data=f"cat:{c['id']}")
    b.button(text=t(lang, "all"), callback_data="cat:all")
    b.adjust(2)
    return b.as_markup()


def courses_kb(lang, courses, back=None):
    b = InlineKeyboardBuilder()
    for c in courses:
        b.button(text=f"{c['title'][lang]} • {money(c['price'])}", callback_data=f"course:{c['id']}")
    b.adjust(1)
    if back:
        b.row(IB(text=t(lang, "back"), callback_data=back))
    return b.as_markup()


def course_kb(lang, c, uid):
    b = InlineKeyboardBuilder()
    b.row(IB(text=t(lang, "register"), callback_data=f"reg:{c['id']}"))
    fav_text = t(lang, "fav_del") if is_fav(uid, c["id"]) else t(lang, "fav_add")
    b.row(IB(text=t(lang, "program"), callback_data=f"prog:{c['id']}"),
          IB(text=fav_text, callback_data=f"fav:{c['id']}"))
    b.row(IB(text=t(lang, "back"), callback_data=f"cat:{c['category']}"))
    return b.as_markup()


def cancel_kb(lang):
    b = ReplyKeyboardBuilder()
    b.button(text=t(lang, "cancel"))
    return b.as_markup(resize_keyboard=True)


def phone_kb(lang):
    b = ReplyKeyboardBuilder()
    b.add(KeyboardButton(text=t(lang, "send_phone"), request_contact=True))
    b.add(KeyboardButton(text=t(lang, "cancel")))
    b.adjust(1)
    return b.as_markup(resize_keyboard=True)


# --------------------------------------------------------------- YORDAMCHILAR
def card_text(lang, c) -> str:
    lines = [
        f"🎓 <b>{html.escape(c['title'][lang])}</b>",
        "",
        html.escape(c["short"][lang]),
        "",
        f"📊 {t(lang, 'level')}: <b>{html.escape(c['level'][lang])}</b>",
        f"⏱ {t(lang, 'duration')}: <b>{html.escape(c['duration'][lang])}</b>",
        f"🎬 {t(lang, 'lessons')}: <b>{t(lang, 'lessons_n', n=c['lessons'])}</b>",
        f"👨‍🏫 {t(lang, 'teacher')}: <b>{html.escape(c['teacher'])}</b>",
        f"⭐ {t(lang, 'rating')}: <b>{c['rating']}</b>",
        "",
    ]
    price = f"💰 {t(lang, 'price')}: "
    if c.get("old_price"):
        price += f"<s>{money(c['old_price'])}</s> "
    price += f"<b>{money(c['price'])} {t(lang, 'currency')}</b>"
    lines.append(price)
    return "\n".join(lines)


async def replace(cb: CallbackQuery, text, kb=None, photo=None):
    """Eski xabarni o'chirib, yangisini yuboradi (matn <-> rasm almashishi uchun)."""
    msg = cb.message
    try:
        await msg.delete()
    except Exception:
        pass
    if photo:
        try:
            await cb.bot.send_photo(msg.chat.id, photo, caption=text, reply_markup=kb)
            return
        except Exception as e:
            log.warning("Rasm yuborilmadi: %s", e)
    await cb.bot.send_message(msg.chat.id, text, reply_markup=kb)


async def send_menu(m: Message, lang: str, text: str = None):
    await m.answer(text or t(lang, "welcome", name=html.escape(m.from_user.first_name)),
                   reply_markup=menu_kb(lang))


# ---------------------------------------------------------------------- FSM
class Reg(StatesGroup):
    name = State()
    phone = State()


class Search(StatesGroup):
    query = State()


router = Router()


# ------------------------------------------------------------ START VA TIL
@router.message(CommandStart())
async def cmd_start(m: Message, state: FSMContext):
    await state.clear()
    upsert_user(m.from_user)
    lang = get_lang(m.from_user.id)
    if not lang:
        await m.answer(f"{T['uz']['choose_lang']} / {T['ru']['choose_lang']}", reply_markup=lang_kb())
    else:
        await send_menu(m, lang)


@router.callback_query(F.data.startswith("lang:"))
async def set_lang(cb: CallbackQuery):
    lang = cb.data.split(":")[1]
    upsert_user(cb.from_user)
    q("UPDATE users SET lang=? WHERE id=?", (lang, cb.from_user.id), commit=True)
    try:
        await cb.message.delete()
    except Exception:
        pass
    await cb.bot.send_message(cb.message.chat.id,
                              t(lang, "welcome", name=html.escape(cb.from_user.first_name)),
                              reply_markup=menu_kb(lang))
    await cb.answer(t(lang, "lang_set"))


@router.message(F.text.in_(both("m_lang")))
async def change_lang(m: Message, state: FSMContext):
    await state.clear()
    await m.answer(f"{T['uz']['choose_lang']} / {T['ru']['choose_lang']}", reply_markup=lang_kb())


@router.message(F.text.in_(both("cancel")))
async def cancel(m: Message, state: FSMContext):
    await state.clear()
    lang = lng(m.from_user.id)
    await m.answer(t(lang, "cancelled"), reply_markup=menu_kb(lang))


# -------------------------------------------------------------------- KATALOG
@router.message(F.text.in_(both("m_courses")))
async def catalog(m: Message, state: FSMContext):
    await state.clear()
    lang = lng(m.from_user.id)
    await m.answer(t(lang, "choose_cat"), reply_markup=cat_kb(lang))


@router.callback_query(F.data == "catalog")
async def catalog_cb(cb: CallbackQuery):
    lang = lng(cb.from_user.id)
    await replace(cb, t(lang, "choose_cat"), cat_kb(lang))
    await cb.answer()


@router.callback_query(F.data.startswith("cat:"))
async def category(cb: CallbackQuery):
    lang = lng(cb.from_user.id)
    cid = cb.data.split(":")[1]
    items = list(COURSES.values()) if cid == "all" else [c for c in COURSES.values() if c["category"] == cid]
    if not items:
        await cb.answer(t(lang, "no_courses"), show_alert=True)
        return
    name = t(lang, "all") if cid == "all" else next(c[lang] for c in CATEGORIES if c["id"] == cid)
    await replace(cb, t(lang, "courses_in", cat=name), courses_kb(lang, items, back="catalog"))
    await cb.answer()


@router.callback_query(F.data.startswith("course:"))
async def course(cb: CallbackQuery):
    lang = lng(cb.from_user.id)
    c = COURSES.get(cb.data.split(":")[1])
    if not c:
        await cb.answer()
        return
    await replace(cb, card_text(lang, c), course_kb(lang, c, cb.from_user.id), photo=c.get("image"))
    await cb.answer()


@router.callback_query(F.data.startswith("prog:"))
async def program(cb: CallbackQuery):
    lang = lng(cb.from_user.id)
    c = COURSES.get(cb.data.split(":")[1])
    if not c:
        await cb.answer()
        return
    prog = "\n".join(f"{i}. {html.escape(x)}" for i, x in enumerate(c["program"][lang], 1))
    text = t(lang, "details", title=html.escape(c["title"][lang]),
             desc=html.escape(c["description"][lang]), program=prog)
    b = InlineKeyboardBuilder()
    b.row(IB(text=t(lang, "register"), callback_data=f"reg:{c['id']}"))
    b.row(IB(text=t(lang, "back"), callback_data=f"course:{c['id']}"))
    await replace(cb, text, b.as_markup())
    await cb.answer()


@router.callback_query(F.data.startswith("fav:"))
async def toggle_fav(cb: CallbackQuery):
    lang = lng(cb.from_user.id)
    cid = cb.data.split(":")[1]
    uid = cb.from_user.id
    if is_fav(uid, cid):
        q("DELETE FROM favs WHERE user_id=? AND course_id=?", (uid, cid), commit=True)
        msg = t(lang, "fav_removed")
    else:
        q("INSERT OR IGNORE INTO favs VALUES(?,?)", (uid, cid), commit=True)
        msg = t(lang, "fav_added")
    try:
        await cb.message.edit_reply_markup(reply_markup=course_kb(lang, COURSES[cid], uid))
    except Exception:
        pass
    await cb.answer(msg)


# ------------------------------------------------------- CHEGIRMA / SARALANGAN
@router.message(F.text.in_(both("m_discounts")))
async def discounts(m: Message, state: FSMContext):
    await state.clear()
    lang = lng(m.from_user.id)
    items = [c for c in COURSES.values() if c.get("old_price")]
    if not items:
        await m.answer(t(lang, "no_disc"))
        return
    await m.answer(t(lang, "disc_title"), reply_markup=courses_kb(lang, items))


@router.message(F.text.in_(both("m_fav")))
async def favorites(m: Message, state: FSMContext):
    await state.clear()
    lang = lng(m.from_user.id)
    rows = q("SELECT course_id FROM favs WHERE user_id=?", (m.from_user.id,))
    items = [COURSES[r["course_id"]] for r in rows if r["course_id"] in COURSES]
    if not items:
        await m.answer(t(lang, "no_fav"))
        return
    await m.answer(t(lang, "fav_title"), reply_markup=courses_kb(lang, items))


# --------------------------------------------------------------------- QIDIRUV
@router.message(F.text.in_(both("m_search")))
async def search_start(m: Message, state: FSMContext):
    lang = lng(m.from_user.id)
    await state.set_state(Search.query)
    await m.answer(t(lang, "ask_search"), reply_markup=cancel_kb(lang))


@router.message(Search.query, F.text)
async def search_do(m: Message, state: FSMContext):
    lang = lng(m.from_user.id)
    needle = m.text.strip().lower()
    items = [c for c in COURSES.values()
             if needle in c["title"]["uz"].lower() or needle in c["title"]["ru"].lower()
             or needle in c["short"][lang].lower()]
    await state.clear()
    if not items:
        await m.answer(t(lang, "no_results"), reply_markup=menu_kb(lang))
        return
    await m.answer(t(lang, "search_res"), reply_markup=menu_kb(lang))
    await m.answer("👇", reply_markup=courses_kb(lang, items))


# ------------------------------------------------------------------ RO'YXATDAN
@router.callback_query(F.data.startswith("reg:"))
async def reg_start(cb: CallbackQuery, state: FSMContext):
    lang = lng(cb.from_user.id)
    cid = cb.data.split(":")[1]
    if cid not in COURSES:
        await cb.answer()
        return
    await state.set_state(Reg.name)
    await state.update_data(course_id=cid)
    await cb.message.answer(t(lang, "ask_name"), reply_markup=cancel_kb(lang))
    await cb.answer()


@router.message(Reg.name, F.text)
async def reg_name(m: Message, state: FSMContext):
    lang = lng(m.from_user.id)
    name = m.text.strip()[:80]
    if len(name) < 2:
        await m.answer(t(lang, "ask_name"))
        return
    await state.update_data(name=name)
    await state.set_state(Reg.phone)
    await m.answer(t(lang, "ask_phone"), reply_markup=phone_kb(lang))


async def finish_reg(m: Message, state: FSMContext, phone: str):
    lang = lng(m.from_user.id)
    d = await state.get_data()
    c = COURSES[d["course_id"]]
    q("INSERT INTO leads(user_id, course_id, name, phone) VALUES(?,?,?,?)",
      (m.from_user.id, c["id"], d["name"], phone), commit=True)
    await state.clear()
    await m.answer(t(lang, "done", course=html.escape(c["title"][lang])), reply_markup=menu_kb(lang))
    uname = f"@{m.from_user.username}" if m.from_user.username else "—"
    note = (f"🆕 <b>Yangi ariza!</b>\n\n🎓 {html.escape(c['title']['uz'])}\n"
            f"👤 {html.escape(d['name'])}\n📱 {html.escape(phone)}\n"
            f"🔗 {uname} | <code>{m.from_user.id}</code>")
    for aid in ADMIN_IDS:
        try:
            await m.bot.send_message(aid, note)
        except Exception as e:
            log.warning("Adminga yuborilmadi %s: %s", aid, e)


@router.message(Reg.phone, F.contact)
async def reg_phone_contact(m: Message, state: FSMContext):
    await finish_reg(m, state, m.contact.phone_number)


@router.message(Reg.phone, F.text)
async def reg_phone_text(m: Message, state: FSMContext):
    lang = lng(m.from_user.id)
    phone = re.sub(r"[^\d+]", "", m.text)
    if len(re.sub(r"\D", "", phone)) < 9:
        await m.answer(t(lang, "bad_phone"))
        return
    await finish_reg(m, state, phone)


@router.message(F.text.in_(both("m_apps")))
async def my_apps(m: Message, state: FSMContext):
    await state.clear()
    lang = lng(m.from_user.id)
    rows = q("SELECT * FROM leads WHERE user_id=? ORDER BY id DESC LIMIT 10", (m.from_user.id,))
    if not rows:
        await m.answer(t(lang, "no_apps"))
        return
    lines = [t(lang, "apps_title"), ""]
    for r in rows:
        c = COURSES.get(r["course_id"])
        title = c["title"][lang] if c else r["course_id"]
        lines.append(f"🎓 <b>{html.escape(title)}</b>\n🕒 {r['created'][:16]}\n")
    await m.answer("\n".join(lines))


# ------------------------------------------------------- MA'LUMOT BO'LIMLARI
@router.message(F.text.in_(both("m_about")))
async def about(m: Message, state: FSMContext):
    await state.clear()
    await m.answer(DATA["about"][lng(m.from_user.id)])


@router.message(F.text.in_(both("m_contact")))
async def contact(m: Message, state: FSMContext):
    await state.clear()
    await m.answer(DATA["contacts"][lng(m.from_user.id)], disable_web_page_preview=True)


@router.message(F.text.in_(both("m_faq")))
async def faq(m: Message, state: FSMContext):
    await state.clear()
    lang = lng(m.from_user.id)
    lines = [t(lang, "faq_title"), ""]
    for item in DATA["faq"]:
        lines.append(f"❓ <b>{html.escape(item['q'][lang])}</b>\n💬 {html.escape(item['a'][lang])}\n")
    await m.answer("\n".join(lines))


# ------------------------------------------------------------------------ ADMIN
@router.message(Command("admin"))
async def admin_panel(m: Message):
    if m.from_user.id not in ADMIN_IDS:
        return
    users = q("SELECT COUNT(*) c FROM users", one=True)["c"]
    today = q("SELECT COUNT(*) c FROM users WHERE date(joined)=date('now')", one=True)["c"]
    leads = q("SELECT COUNT(*) c FROM leads", one=True)["c"]
    await m.answer(
        f"🛠 <b>Admin panel</b>\n\n👥 Foydalanuvchilar: <b>{users}</b>\n🆕 Bugun: <b>{today}</b>\n"
        f"📋 Arizalar: <b>{leads}</b>\n\n/leads — oxirgi 10 ariza\n/broadcast matn — hammaga xabar"
    )


@router.message(Command("leads"))
async def admin_leads(m: Message):
    if m.from_user.id not in ADMIN_IDS:
        return
    rows = q("SELECT * FROM leads ORDER BY id DESC LIMIT 10")
    if not rows:
        await m.answer("Arizalar yo'q.")
        return
    out = []
    for r in rows:
        c = COURSES.get(r["course_id"])
        out.append(f"#{r['id']} 🎓 {html.escape(c['title']['uz'] if c else r['course_id'])}\n"
                   f"👤 {html.escape(r['name'])} | 📱 {html.escape(r['phone'])}\n🕒 {r['created'][:16]}")
    await m.answer("\n\n".join(out))


@router.message(Command("broadcast"))
async def admin_broadcast(m: Message):
    if m.from_user.id not in ADMIN_IDS:
        return
    text = (m.text or "").partition(" ")[2].strip()
    if not text:
        await m.answer("Foydalanish: /broadcast Xabar matni")
        return
    ok = fail = 0
    for r in q("SELECT id FROM users"):
        try:
            await m.bot.send_message(r["id"], text)
            ok += 1
        except Exception:
            fail += 1
        await asyncio.sleep(0.05)
    await m.answer(f"✅ Yuborildi: {ok}\n❌ Xato: {fail}")


@router.message()
async def fallback(m: Message):
    lang = get_lang(m.from_user.id)
    if lang:
        await m.answer(t(lang, "welcome", name=html.escape(m.from_user.first_name)), reply_markup=menu_kb(lang))
    else:
        upsert_user(m.from_user)
        await m.answer(f"{T['uz']['choose_lang']} / {T['ru']['choose_lang']}", reply_markup=lang_kb())


# ----------------------------------------------------------------------- ISHGA TUSHIRISH
def build() -> tuple[Bot, Dispatcher]:
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    return bot, dp


def main():
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN topilmadi! Environment o'zgaruvchisini kiriting.")
    init_db()
    bot, dp = build()

    if not BASE_URL:  # lokal rejim (polling)
        log.info("Polling rejimi")
        asyncio.run(_polling(bot, dp))
        return

    async def on_startup(bot: Bot):
        await bot.set_webhook(f"{BASE_URL}{WEBHOOK_PATH}", secret_token=WEBHOOK_SECRET,
                              drop_pending_updates=True)
        log.info("Webhook: %s%s", BASE_URL, WEBHOOK_PATH)

    dp.startup.register(on_startup)
    app = web.Application()
    app.router.add_get("/", lambda r: web.Response(text="Bot ishlayapti ✅"))
    SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=WEBHOOK_SECRET).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    web.run_app(app, host="0.0.0.0", port=PORT)


async def _polling(bot: Bot, dp: Dispatcher):
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    main()
