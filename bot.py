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
    await message.answer_photo(photo=BANNER_URL, caption=get_main_caption(), reply_markup=get_playerok_menu(), parse_mode="Markdown")

@dp.callback_query(F.data == "to_main_menu")
async def to_main_menu(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_caption(caption=get_main_caption(), reply_markup=get_playerok_menu(), parse_mode="Markdown")

@dp.callback_query(F.data == "main_create")
async def create_order(call: types.CallbackQuery, state: FSMContext):
    text = "🟢 **Создание ордера**\n\n> *Выберите способ оплаты со стороны покупателя*"
    builder = InlineKeyboardBuilder()
    builder.button(text="🔹 TON", callback_data="method_ton")
    builder.button(text="🔹 USDT (TON)", callback_data="method_usdt")
    builder.button(text="💳 Карта/СБП", callback_data="method_card")
    builder.button(text="🆕 Звёзды", callback_data="method_stars")
    builder.button(text="◀️ В меню", callback_data="to_main_menu")
    builder.adjust(2, 2, 1)
    await call.message.edit_caption(caption=text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await state.set_state(OrderStates.choosing_method)

@dp.callback_query(F.data == "method_ton")
async def method_ton(call: types.CallbackQuery):
    text = "⚠️ **TON-кошелёк не привязан**\n\n*Добавьте его в разделе «Кошельки»*"
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data="main_create")
    await call.message.edit_caption(caption=text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "method_card")
@dp.callback_query(F.data == "method_usdt")
async def choose_currency(call: types.CallbackQuery, state: FSMContext):
    text = "💳 **Валюта ордера**\n\n> *Выберите валюту*"
    builder = InlineKeyboardBuilder()
    currencies = ["RUB", "USD", "EUR", "UAH", "KZT", "BYN", "UZS"]
    for cur in currencies:
        builder.button(text=cur, callback_data=f"cur_{cur}")
    builder.button(text="◀️ Назад", callback_data="main_create")
    builder.adjust(2, 2, 2, 1, 1)
    await call.message.edit_caption(caption=text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await state.set_state(OrderStates.choosing_currency)

@dp.callback_query(F.data == "method_stars")
async def method_stars(call: types.CallbackQuery, state: FSMContext):
    text = "⭐ **Получатель звёзд**\n\n*Укажите @username получателя*\n\n> *Минимум: 100 звёзд*"
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data="main_create")
    await call.message.edit_caption(caption=text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await state.set_state(OrderStates.entering_data)

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
