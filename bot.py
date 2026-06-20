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

class OrderStates(StatesGroup):
    choosing_method = State()
    choosing_currency = State()
    entering_data = State()
    waiting_for_wallet = State() # Новое состояние

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            card_requisites TEXT DEFAULT 'Не указаны',
            wallet_address TEXT DEFAULT 'Не указан'
        )
    """)
    conn.commit()
    conn.close()

def get_main_caption():
    return "Добро пожаловать 👋\n\n🟢 **PlayerOk** — безопасные сделки.\n\n🛡 Выберите раздел:"

def get_playerok_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔹 Создать ордер", callback_data="main_create")
    builder.button(text="📘 Кошельки", callback_data="main_wallets")
    builder.adjust(1)
    return builder.as_markup()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer_photo(photo=BANNER_URL, caption=get_main_caption(), reply_markup=get_playerok_menu(), parse_mode="Markdown")

@dp.callback_query(F.data == "main_create")
async def create_order(call: types.CallbackQuery, state: FSMContext):
    text = "🔒 **Создание ордера**\n\n> *Выберите способ оплаты*"
    builder = InlineKeyboardBuilder()
    builder.button(text="🔹 TON", callback_data="method_ton")
    builder.button(text="🔹 USDT (TON)", callback_data="method_usdt")
    builder.button(text="💳 Карта/СБП", callback_data="method_card")
    builder.button(text="🆕 Звёзды", callback_data="method_stars")
    builder.button(text="◀️ В меню", callback_data="to_main_menu")
    builder.adjust(2, 2, 1)
    await call.message.edit_caption(caption=text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await state.set_state(OrderStates.choosing_method)

@dp.callback_query(F.data.in_(["method_ton", "method_usdt"]))
async def request_wallet(call: types.CallbackQuery, state: FSMContext):
    text = "📥 **Введите ваш TON-кошелек**\n\nПожалуйста, отправьте адрес вашего кошелька в ответ на это сообщение."
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data="main_create")
    await call.message.edit_caption(caption=text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await state.set_state(OrderStates.waiting_for_wallet)

@dp.message(OrderStates.waiting_for_wallet)
async def save_wallet(message: types.Message, state: FSMContext):
    wallet = message.text
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET wallet_address = ? WHERE user_id = ?", (wallet, message.from_user.id))
    conn.commit()
    conn.close()
    await message.answer("✅ **Кошелек успешно привязан!**")
    await state.clear()
    # Возвращаем в главное меню
    await message.answer_photo(photo=BANNER_URL, caption=get_main_caption(), reply_markup=get_playerok_menu(), parse_mode="Markdown")

async def main():
    init_db()
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
