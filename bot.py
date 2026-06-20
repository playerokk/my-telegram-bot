import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

TOKEN = "8802204413:AAEuXzZXSnUYqdv6I-hExGd100yQeIm0lCk"

dp = Dispatcher()

def get_main_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="🤝 Создать сделку")
    builder.button(text="👤 Мой профиль")
    builder.button(text="❓ Поддержка")
    builder.adjust(1, 2)
    return builder.as_markup(resize_keyboard=True)

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        f"👋 Добро пожаловать в Демо-Гарант бот, {message.from_user.first_name}!\nЗдесь вы можете безопасно проводить сделки.",
        reply_markup=get_main_menu()
    )

@dp.message(lambda message: message.text == "👤 Мой профиль")
async def user_profile(message: types.Message):
    await message.answer(
        f"📋 **Ваш профиль:**\n\n"
        f"🆔 ID: `{message.from_user.id}`\n"
        f"👤 Имя: {message.from_user.first_name}\n"
        f"💰 Баланс: 0.00 ₽\n"
        f"⭐️ Рейтинг: 5.0 (0 отзывов)",
        parse_mode="Markdown"
    )

@dp.message(lambda message: message.text == "🤝 Создать сделку")
async def create_deal(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="🛒 Я покупатель", callback_data="deal_buyer")
    builder.button(text="📦 Я продавец", callback_data="deal_seller")
    await message.answer("Выберите вашу роль в будущей сделке:", reply_markup=builder.as_markup())

@dp.callback_query(lambda call: call.data.startswith("deal_"))
async def process_deal_role(call: types.CallbackQuery):
    role = "Покупатель" if call.data == "deal_buyer" else "Продавец"
    await call.answer()
    await call.message.edit_text(f"Вы выбрали роль: **{role}**.\n\n⏳ Демо-режим хостинга.", parse_mode="Markdown")

@dp.message(lambda message: message.text == "❓ Поддержка")
async def support(message: types.Message):
    await message.answer("⚠️ Если у вас возникли вопросы, обратитесь в нашу официальную поддержку.")

async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
