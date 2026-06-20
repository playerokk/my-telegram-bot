import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

TOKEN = "8802204413:AAHR3Pv8p9fitrRbqDInANi5NJ4l3hraSiw"
BANNER_URL = "https://i.imgur.com/vHExT2V.png"

bot = Bot(token=TOKEN)
dp = Dispatcher()

class RequisitesUpdate(StatesGroup):
    entering_card = State()

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance REAL DEFAULT 0.0,
            deals_count INTEGER DEFAULT 0,
            card_requisites TEXT DEFAULT 'Не указаны'
        )
    """)
    conn.commit()
    conn.close()

def get_main_caption():
    return (
        "Добро пожаловать 👋\n\n"
        "🟢 **PlayerOk** — специализированный сервис по обеспечение безопасности внебиржевых сделок.\n\n"
        "🥇 **Автоматизированный алгоритм исполнения.**\n"
        "🚀 **Скорость и автоматизация.**\n"
        "💳 **Удобный и быстрый вывод средств.**\n\n"
        "• Комиссия сервиса: **1%**\n"
        "• Режим работы: **24/7**\n"
        "• Поддержка: @PlayerokEscrow\n\n"
        "🛡 Выберите нужный раздел ниже:"
    )

def get_playerok_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔹 Создать ордер", callback_data="main_create")
    builder.button(text="📘 Кошельки", callback_data="main_wallets")
    builder.button(text="🔔 Безопасность", callback_data="main_security")
    builder.button(text="💙 Рефералы", callback_data="main_ref")
    builder.button(text="🔹 Канал", url="https://t.me/Playerok")
    builder.button(text="💬 Поддержка", callback_data="main_support")
    builder.button(text="🔹 Язык", callback_data="main_lang")
    builder.adjust(1, 2, 2, 2)
    return builder.as_markup()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", 
                   (message.from_user.id, message.from_user.username))
    conn.commit()
    conn.close()
    await message.answer_photo(photo=BANNER_URL, caption=get_main_caption(), reply_markup=get_playerok_menu(), parse_mode="Markdown")

@dp.callback_query(F.data == "to_main_menu")
async def to_main_menu(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_caption(caption=get_main_caption(), reply_markup=get_playerok_menu(), parse_mode="Markdown")

@dp.callback_query(F.data == "main_wallets")
async def press_wallets(call: types.CallbackQuery, state: FSMContext):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT card_requisites FROM users WHERE user_id = ?", (call.from_user.id,))
    row = cursor.fetchone()
    conn.close()
    current_req = row[0] if row else "Не указаны"

    text = (
        f"💳 **Реквизиты карты / СБП**\n\n"
        f"> Текущие: {current_req}\n\n"
        f"📝 **Отправьте реквизиты:**\n"
        f"• *Для рублей РФ — укажите СБП и банк*\n"
        f"• *Для других валют — номер карты*\n\n"
        f"> **Примеры:**\n"
        f"> СБП ТБанк — +7 912 345-67-89\n"
        f"> Карта — 5536 9141 2847 3956"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ В меню", callback_data="to_main_menu")
    
    await call.message.edit_caption(caption=text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await state.set_state(RequisitesUpdate.entering_card)

@dp.message(RequisitesUpdate.entering_card)
async def process_entering_card(message: types.Message, state: FSMContext):
    new_req = message.text
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET card_requisites = ? WHERE user_id = ?", (new_req, message.from_user.id))
    conn.commit()
    conn.close()
    await state.clear()
    await message.answer("✅ **Реквизиты обновлены**")
    await message.answer_photo(photo=BANNER_URL, caption=get_main_caption(), reply_markup=get_playerok_menu(), parse_mode="Markdown")

async def main():
    logging.basicConfig(level=logging.INFO)
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
