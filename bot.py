import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

TOKEN = "8802204413:AAHVhQD3AeFez5X3mYyzNWlYO0l166buaWM"
BANNER_URL = "https://i.imgur.com/vHExT2V.png" 

bot = Bot(token=TOKEN)
dp = Dispatcher()

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
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN card_requisites TEXT DEFAULT 'Не указаны'")
    except sqlite3.OperationalError:
        pass
        
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            creator_id INTEGER,
            second_user_id INTEGER,
            amount REAL,
            description TEXT,
            status TEXT DEFAULT 'Ожидает оплаты покупателем'
        )
    """)
    conn.commit()
    conn.close()

class OrderCreation(StatesGroup):
    entering_amount = State()
    entering_description = State()
    entering_second_user = State()

class RequisitesUpdate(StatesGroup):
    entering_card = State()

def get_main_caption():
    return (
        "Добро пожаловать 👋\n\n"
        "🟢 **PlayerOk** — специализированный сервис по обеспечению безопасности внебиржевых сделок.\n\n"
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

def get_back_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад", callback_data="to_main_menu")
    return builder.as_markup()

def get_cancel_reply():
    builder = ReplyKeyboardBuilder()
    builder.button(text="❌ Отменить создание ордера")
    return builder.as_markup(resize_keyboard=True)

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", 
                   (message.from_user.id, message.from_user.username))
    conn.commit()
    conn.close()
    try:
        await message.answer_photo(photo=BANNER_URL, caption=get_main_caption(), reply_markup=get_playerok_menu(), parse_mode="Markdown")
    except Exception:
        await message.answer(get_main_caption(), reply_markup=get_playerok_menu(), parse_mode="Markdown")

@dp.callback_query(F.data == "to_main_menu")
async def to_main_menu(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await call.message.edit_caption(caption=get_main_caption(), reply_markup=get_playerok_menu(), parse_mode="Markdown")
    except Exception:
        try:
            await call.message.delete()
        except Exception:
            pass
        try:
            await call.message.answer_photo(photo=BANNER_URL, caption=get_main_caption(), reply_markup=get_playerok_menu(), parse_mode="Markdown")
        except Exception:
            await call.message.answer(get_main_caption(), reply_markup=get_playerok_menu(), parse_mode="Markdown")
    try:
        await call.answer()
    except Exception:
        pass

@dp.callback_query(F.data == "main_wallets")
async def press_wallets(call: types.CallbackQuery):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance, deals_count FROM users WHERE user_id = ?", (call.from_user.id,))
    row = cursor.fetchone()
    conn.close()
    balance, deals = (row[0], row[1]) if row else (0.0, 0)
    
    text = (
        f"💳 **Ваши кошельки и баланс:**\n\n"
        f"🆔 Ваш ID: `{call.from_user.id}`\n"
        f"💰 Доступный баланс: **{balance} ₽**\n"
        f"📊 Успешных сделок: **{deals}**\n\n"
        f"Вывод средств производится в автоматическом режиме на QIWI, ЮMoney и Банковские карты РФ/СНГ."
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="📥 Пополнить баланс", callback_data="wallet_deposit")
    builder.button(text="📤 Вывести средства", callback_data="wallet_withdraw")
    builder.button(text="🔙 Назад", callback_data="to_main_menu")
    builder.adjust(2, 1)
    try:
        await call.message.edit_caption(caption=text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    except Exception:
        try:
            await call.message.answer_photo(photo=BANNER_URL, caption=text, reply_markup=builder.as_markup(), parse_mode="Markdown")
        except Exception:
            await call.message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    try:
        await call.answer()
    except Exception:
        pass

@dp.callback_query(F.data == "wallet_deposit")
async def wallet_deposit(call: types.CallbackQuery):
    try:
        await call.answer("⚠️ Пополнение баланса временно недоступно.", show_alert=True)
    except Exception:
        pass

@dp.callback_query(F.data == "wallet_withdraw")
async def wallet_withdraw(call: types.CallbackQuery):
    text = "🟢 **Добавьте или обновите платёжные данные**"
    builder = InlineKeyboardBuilder()
    builder.button(text="TON-кошелёк", callback_data="withdraw_ton")
    builder.button(text="Карта/СБП", callback_data="withdraw_card")
    builder.button(text="◀️ В меню", callback_data="to_main_menu")
    builder.adjust(2, 1)
    try:
        await call.message.edit_caption(caption=text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    except Exception:
        try:
            await call.message.answer_photo(photo=BANNER_URL, caption=text, reply_markup=builder.as_markup(), parse_mode="Markdown")
        except Exception:
            await call.message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    try:
        await call.answer()
    except Exception:
        pass

@dp.callback_query(F.data == "withdraw_ton")
async def withdraw_ton(call: types.CallbackQuery):
    try:
        await call.answer("⚠️ Подключение TON-кошелька временно недоступно.", show_alert=True)
    except Exception:
        pass

@dp.callback_query(F.data == "withdraw_card")
async def withdraw_card(call: types.CallbackQuery, state: FSMContext):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT card_requisites FROM users WHERE user_id = ?", (call.from_user.id,))
    row = cursor.fetchone()
    conn.close()
    current_req = row[0] if row else "Не указаны"

    text = (
        f"💳 **Реквизиты карты / СБП**\n\n"
        f"🟢 Текущие: `{current_
