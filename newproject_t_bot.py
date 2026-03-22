from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# Render uchun oddiy portni band qilib turuvchi server
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_health_check():
    server = HTTPServer(('0.0.0.0', 10000), HealthCheckHandler)
    server.serve_forever()

# Botni ishga tushirishdan oldin bu funksiyani alohida oqimda (thread) yuritamiz
threading.Thread(target=run_health_check, daemon=True).start()

# --- BU YERDAN KEYIN SIZNING ASOSIY BOT KODINGIZ BOSHLANADI ---
# Masalan: executor.start_polling(dp) yoki dp.run_polling(bot)

import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext  # To'g'ri import shu yerda

# --- KONFIGURATSIYA ---
TOKEN = "8549958201:AAGNdr6gNFLkvvEZ0dofCieB6BMv_m_i6qE"
ADMIN_USERNAME = "@Socrates_xm"
# DIQQAT: O'z ID raqamingizni @userinfobot orqali bilib, bu yerga yozing:
ADMIN_ID = 123456789  # O'z ID-ingizni kiriting

bot = Bot(token=TOKEN)
dp = Dispatcher()


# Foydalanuvchi holatlari
class OrderState(StatesGroup):
    lang = State()
    main_menu = State()
    waiting_bot_details = State()
    waiting_direct_message = State()


# --- MATNLAR LUG'ATI ---
TEXTS = {
    'uz': {
        'welcome': "Salom! Men xsmdev botiman.",
        'choose_service': "O'zingizga kerakli xizmatni tanlang:",
        'btn_bot_order': "🤖 Telegram bot yasash",
        'btn_contact_admin': "👨‍💻 Admin bilan bog'lanish",
        'btn_direct_msg': "✍️ Murojaat qoldirish",
        'btn_back': "⬅️ Ortga",
        'ask_details': "Qanday bot xohlaysiz? Bot nimalar qila olishi kerak? Batafsil yozing:",
        'ask_msg': "Murojaatingizni yozib qoldiring:",
        'success': "Ma'lumot qabul qilindi. Tez orada admin siz bilan bog'lanadi!",
        'admin_info': f"Admin bilan bog'lanish uchun: {ADMIN_USERNAME}"
    },
    'ru': {
        'welcome': "Привет! Я бот xsmdev.",
        'choose_service': "Выберите интересующую вас услугу:",
        'btn_bot_order': "🤖 Заказать телеграм бот",
        'btn_contact_admin': "👨‍💻 Связаться с админом",
        'btn_direct_msg': "✍️ Оставить обращение",
        'btn_back': "⬅️ Назад",
        'ask_details': "Какой бот вы хотите? Опишите функционал и ваши ожидания:",
        'ask_msg': "Введите ваше обращение:",
        'success': "Информация получена. Скоро админ свяжется с вами!",
        'admin_info': f"Для связи с админом: {ADMIN_USERNAME}"
    }
}


# --- KEYBOARDLAR ---
def get_lang_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="🇺🇿 O'zbekcha")
    builder.button(text="🇷🇺 Русский")
    return builder.as_markup(resize_keyboard=True)


def get_main_keyboard(lang):
    builder = ReplyKeyboardBuilder()
    builder.button(text=TEXTS[lang]['btn_bot_order'])
    builder.button(text=TEXTS[lang]['btn_contact_admin'])
    builder.button(text=TEXTS[lang]['btn_direct_msg'])
    builder.adjust(1, 2)
    return builder.as_markup(resize_keyboard=True)


def get_back_keyboard(lang):
    builder = ReplyKeyboardBuilder()
    builder.button(text=TEXTS[lang]['btn_back'])
    return builder.as_markup(resize_keyboard=True)


# --- HANDLERLAR ---

@dp.message(CommandStart())
async def command_start_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(f"Salom! Men xsmdev botiman. \n\nIltimos, tilni tanlang / Пожалуйста, выберите язык:",
                         reply_markup=get_lang_keyboard())


@dp.message(F.text.in_(["🇺🇿 O'zbekcha", "🇷🇺 Русский"]))
async def set_language(message: types.Message, state: FSMContext):
    lang = 'uz' if "O'zbekcha" in message.text else 'ru'
    await state.update_data(lang=lang)
    await message.answer(TEXTS[lang]['welcome'])
    await message.answer(TEXTS[lang]['choose_service'], reply_markup=get_main_keyboard(lang))


@dp.message(F.text.in_([TEXTS['uz']['btn_back'], TEXTS['ru']['btn_back']]))
async def back_to_menu(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get('lang', 'uz')
    await state.set_state(None)  # Holatni tozalash
    await message.answer(TEXTS[lang]['choose_service'], reply_markup=get_main_keyboard(lang))


@dp.message(F.text.in_([TEXTS['uz']['btn_bot_order'], TEXTS['ru']['btn_bot_order']]))
async def bot_order_process(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get('lang', 'uz')
    await state.set_state(OrderState.waiting_bot_details)
    await message.answer(TEXTS[lang]['ask_details'], reply_markup=get_back_keyboard(lang))


@dp.message(F.text.in_([TEXTS['uz']['btn_contact_admin'], TEXTS['ru']['btn_contact_admin']]))
async def contact_admin(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get('lang', 'uz')
    await message.answer(TEXTS[lang]['admin_info'])


@dp.message(F.text.in_([TEXTS['uz']['btn_direct_msg'], TEXTS['ru']['btn_direct_msg']]))
async def direct_msg_process(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get('lang', 'uz')
    await state.set_state(OrderState.waiting_direct_message)
    await message.answer(TEXTS[lang]['ask_msg'], reply_markup=get_back_keyboard(lang))


@dp.message(OrderState.waiting_bot_details)
@dp.message(OrderState.waiting_direct_message)
async def handle_input(message: types.Message, state: FSMContext):
    # Agar foydalanuvchi "Ortga" tugmasini bossa
    if message.text in [TEXTS['uz']['btn_back'], TEXTS['ru']['btn_back']]:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'uz')
        await state.set_state(None)
        await message.answer(TEXTS[lang]['choose_service'], reply_markup=get_main_keyboard(lang))
        return

    user_data = await state.get_data()
    lang = user_data.get('lang', 'uz')
    current_state = await state.get_state()

    # Adminga xabar yuborish qismi
    order_type = "Bot buyurtmasi" if current_state == OrderState.waiting_bot_details else "Yangi murojaat"
    admin_msg = f"🔔 {order_type}!\n👤 Kimdan: @{message.from_user.username}\n🆔 ID: {message.from_user.id}\n📝 Xabar: {message.text}"

    try:
        await bot.send_message(ADMIN_ID, admin_msg)
    except Exception as e:
        logging.error(f"Adminga xabar yuborishda xato: {e}")

    await message.answer(TEXTS[lang]['success'], reply_markup=get_main_keyboard(lang))
    await state.set_state(None)


async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())


