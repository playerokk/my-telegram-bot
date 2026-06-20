import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# ЗАМЕНИ ЭТОТ ТОКЕН НА РАБОЧИЙ В @BotFather
TOKEN = "СЮДА_ВСТАВЬ_НОВЫЙ_ТОКЕН_ИЗ_BOTFATHER"
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
            await message.answer(get_main_caption(), reply_markup=get_playerok_menu(), parse_mode="Markdown")
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
        f"🟢 Текущие: `{current_req}`\n\n"
        f"📝 **Отправьте реквизиты:**\n"
        f"• Для рублей РФ — укажите СБП и банк\n"
        f"• Для других валют — номер карты\n\n"
        f"🟢 **Примеры:**\n"
        f"СБП ТБанк — +7 912 345-67-89\n"
        f"Карта — 5536 9141 2847 3956"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад", callback_data="wallet_withdraw")
    
    try:
        await call.message.edit_caption(caption=text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    except Exception:
        try:
            await call.message.answer_photo(photo=BANNER_URL, caption=text, reply_markup=builder.as_markup(), parse_mode="Markdown")
        except Exception:
            await call.message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    
    await state.set_state(RequisitesUpdate.entering_card)
    try:
        await call.answer()
    except Exception:
        pass

@dp.message(RequisitesUpdate.entering_card)
async def process_entering_card(message: types.Message, state: FSMContext):
    new_req = message.text
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET card_requisites = ? WHERE user_id = ?", (message.from_user.id, new_req))
    conn.commit()
    conn.close()
    await state.clear()
    
    await message.answer("🟢 **Реквизиты обновлены**")
    
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance, deals_count FROM users WHERE user_id = ?", (message.from_user.id,))
    row = cursor.fetchone()
    conn.close()
    balance, deals = (row[0], row[1]) if row else (0.0, 0)
    
    text = (
        f"💳 **Ваши кошельки и баланс:**\n\n"
        f"🆔 Ваш ID: `{message.from_user.id}`\n"
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
        await message.answer_photo(photo=BANNER_URL, caption=text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    except Exception:
        await message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "main_security")
async def press_security(call: types.CallbackQuery):
    text = (
        "🔔 **Безопасность сделок на PlayerOk:**\n\n"
        "1. При создании ордера средства покупателя замораживаются на специальном гарант-счете.\n"
        "2. Продавец получает уведомление и передает товар/услугу.\n"
        "3. Деньги переводятся продавцу только после того, как покупатель лично подтвердит успешное выполнение сделки.\n\n"
        "🔒 Все ваши данные зашифрованы протоколом защиты данных Escrow."
    )
    try:
        await call.message.edit_caption(caption=text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
    except Exception:
        try:
            await call.message.answer_photo(photo=BANNER_URL, caption=text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
        except Exception:
            await call.message.answer(text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
    try:
        await call.answer()
    except Exception:
        pass

@dp.callback_query(F.data == "main_ref")
async def press_ref(call: types.CallbackQuery):
    ref_link = f"https://t.me/{(await bot.get_me()).username}?start={call.from_user.id}"
    text = (
        "💙 **Реферальная программа PlayerOk**\n\n"
        "Приглашайте друзей и получайте **0.5%** от суммы каждой их успешной сделки на свой баланс!\n\n"
        "🔗 **Ваша пригласительная ссылка:**\n"
        f"`{ref_link}`\n\n"
        "Количество ваших рефералов: **0**\n"
        "Заработано с рефералов: **0.00 ₽**"
    )
    try:
        await call.message.edit_caption(caption=text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
    except Exception:
        try:
            await call.message.answer_photo(photo=BANNER_URL, caption=text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
        except Exception:
            await call.message.answer(text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
    try:
        await call.answer()
    except Exception:
        pass

@dp.callback_query(F.data == "main_support")
async def press_support(call: types.CallbackQuery):
    text = (
        "💬 **Служба поддержки PlayerOk**\n\n"
        "Наши специалисты работают круглосуточно и без выходных.\n"
        "Если у вас возник спор внутри сделки или техническая проблема, пишите нашему официальному менеджеру:\n\n"
        "👉 **Контакты поддержки:** @PlayerokEscrow"
    )
    try:
        await call.message.edit_caption(caption=text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
    except Exception:
        try:
            await call.message.answer_photo(photo=BANNER_URL, caption=text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
        except Exception:
            await call.message.answer(text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
    try:
        await call.answer()
    except Exception:
        pass

@dp.callback_query(F.data == "main_lang")
async def press_lang(call: types.CallbackQuery):
    text = "🔹 **Выбор языка / Language**\n\nТекущий язык бота: 🇷🇺 Русский"
    builder = InlineKeyboardBuilder()
    builder.button(text="🇷🇺 Русский", callback_data="lang_set")
    builder.button(text="🇺🇸 English", callback_data="lang_set")
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

@dp.callback_query(F.data == "lang_set")
async def lang_set(call: types.CallbackQuery):
    try:
        await call.answer("✅ Язык успешно изменен!", show_alert=False)
    except Exception:
        pass

@dp.message(F.text == "❌ Отменить создание ордера")
async def cancel_order_creation(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Создание ордера отменено.", reply_markup=types.ReplyKeyboardRemove())
    try:
        await message.answer_photo(photo=BANNER_URL, caption=get_main_caption(), reply_markup=get_playerok_menu(), parse_mode="Markdown")
    except Exception:
        await message.answer(get_main_caption(), reply_markup=get_playerok_menu(), parse_mode="Markdown")

@dp.callback_query(F.data == "main_create")
async def create_order_start(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(OrderCreation.entering_amount)
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer("💰 **[Шаг 1/3]** Введите сумму будущего ордера в рублях (только цифры):", reply_markup=get_cancel_reply(), parse_mode="Markdown")
    try:
        await call.answer()
    except Exception:
        pass

@dp.message(OrderCreation.entering_amount)
async def process_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount <= 0:
            await message.answer("❌ Сумма должна быть больше нуля. Введите число заново:")
            return
        await state.update_data(order_amount=amount)
        await state.set_state(OrderCreation.entering_description)
        await message.answer("📝 **[Шаг 2/3]** Введите описание товара или услуги:", parse_mode="Markdown")
    except ValueError:
        await message.answer("❌ Введите корректную сумму числом (например: 500):")

@dp.message(OrderCreation.entering_description)
async def process_description(message: types.Message, state: FSMContext):
    await state.update_data(order_desc=message.text)
    await state.set_state(OrderCreation.entering_second_user)
    await message.answer("🆔 **[Шаг 3/3]** Введите Telegram ID второго участника сделки (только цифры):", parse_mode="Markdown")

@dp.message(OrderCreation.entering_second_user)
async def process_second_user(message: types.Message, state: FSMContext):
    try:
        second_id = int(message.text)
        user_data = await state.get_data()
        
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO orders (creator_id, second_user_id, amount, description) VALUES (?, ?, ?, ?)", 
                       (message.from_user.id, second_id, user_data['order_amount'], user_data['order_desc']))
        order_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        await state.clear()
        await message.answer("✅ Ордер успешно сформирован в системе!", reply_markup=types.ReplyKeyboardRemove())
        
        order_text = (
            f"📦 **Карточка Ордера №{order_id}**\n\n"
            f"💰 Сумма сделки: **{user_data['order_amount']} ₽**\n"
            f"📝 Описание: {user_data['order_desc']}\n"
            f"👥 Инициатор: `{message.from_user.id}`\n"
            f"🤝 Второй участник: `{second_id}`\n\n"
            f"⏳ **Статус:** Ожидает оплаты покупателем через Гарант-счет."
        )
        builder = InlineKeyboardBuilder()
        builder.button(text="💳 Перейти к оплате", callback_data=f"pay_order_{order_id}")
        builder.button(text="🔙 Главное меню", callback_data="to_main_menu")
        builder.adjust(1)
        
        try:
            await message.answer_photo(photo=BANNER_URL, caption=order_text, reply_markup=builder.as_markup(), parse_mode="Markdown")
        except Exception:
            await message.answer(order_text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    except ValueError:
        await message.answer("❌ Telegram ID должен состоять только из цифр. Попробуйте еще раз:")

@dp.callback_query(F.data.startswith("pay_order_"))
async def pay_order_action(call: types.CallbackQuery):
    try:
        await call.answer("❌ Ошибка: Недостаточно средств на балансе. Пополните кошелек в меню.", show_alert=True)
    except Exception:
        pass

async def main():
    logging.basicConfig(level=logging.INFO)
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
