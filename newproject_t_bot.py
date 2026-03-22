import asyncio
import logging
import sys
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from fastapi import FastAPI
import uvicorn

# --- 1. RENDER UCHUN WEB SERVER ---
app = FastAPI()


@app.get("/")
async def health_check():
    return {"status": "bot is running"}


# --- 2. KONFIGURATSIYA ---
# BU YERGA O'Z TOKENINGIZNI QO'YING (Tirnoq ichida)
TOKEN = "8549958201:AAH6EN9L5r731bgeAnphC8kVXpjuShvOmnI"
ADMIN_USERNAME = "@Socrates_xm"
# BU YERGA O'Z ID RAQAMINGIZNI QO'YING (Masalan: 12345678)
ADMIN_ID = 5971900296

bot = Bot(token=TOKEN)
dp = Dispatcher()


# Foydalanuvchi holatlari
class OrderState(StatesGroup):
    lang = State()
    main_menu = State()
    waiting_bot_details = State()
    waiting_direct_message = State()


# --- 3. MATNLAR LUG'ATI ---

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


# --- 4. KEYBOARDLAR ---
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


# --- 5. HANDLERLAR ---
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
    await state.set_state(None)
    await message.answer(TEXTS[lang]['choose_service'], reply_markup=get_main_keyboard(lang))


@dp.message(F.text.in_([TEXTS['uz']['btn_bot_order'], TEXTS['ru']

['btn_bot_order']]))
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
    if message.text in [TEXTS['uz']['btn_back'], TEXTS['ru']['btn_back']]:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'uz')
        await state.set_state(None)
        await message.answer(TEXTS[lang]['choose_service'], reply_markup=get_main_keyboard(lang))
        return

    user_data = await state.get_data()
    lang = user_data.get('lang', 'uz')
    current_state = await state.get_state()
    order_type = "Bot buyurtmasi" if current_state == OrderState.waiting_bot_details else "Yangi murojaat"
    admin_msg = f"🔔 {order_type}!\n👤 Kimdan: @{message.from_user.username}\n🆔 ID: {message.from_user.id}\n📝 Xabar: {message.text}"

    try:
        await bot.send_message(ADMIN_ID,

                               admin_msg)
    except Exception as e:
        logging.error(f"Adminga xabar yuborishda xato: {e}")

    await message.answer(TEXTS[lang]['success'], reply_markup=get_main_keyboard(lang))
    await state.set_state(None)


# --- 6. ASOSIY ISHGA TUSHIRISH LOGIKASI ---
async def main():
    # Logging sozlamalari
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    # Render portni muhitdan oladi (PC da 8000 bo'ladi)
    port = int(os.environ.get("PORT", 8000))

    # 1. Botingizni orqa fonda ishga tushiramiz

    # asyncio.create_task bu loop-ni "RuntimeError" bermasligini ta'minlaydi
    logging.info("Bot polling boshlanmoqda...")
    asyncio.create_task(dp.start_polling(bot))

    # 2. Web serverni asosiy oqimda ishga tushiramiz
    # Uvicorn dasturni yopilib qolishidan saqlaydi
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)

    logging.info(f"Server {port}-portda ishlamoqda...")
    await server.serve()


if __name__ == "__main__":
    try:
        # Eng to'g'ri ishga tushirish usuli shu

        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi")
