import asyncio
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.types import (
    Message,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

import httpx

# ───── Загрузка переменных окружения ─────
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_BACKEND_URL = os.getenv("API_BACKEND_URL", "http://localhost:8000")
MESSAGE_URL = f"{API_BACKEND_URL}/message"
RESET_URL = f"{API_BACKEND_URL}/reset"

# ───── Инициализация бота ─────
bot = Bot(token=TELEGRAM_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

# ───── Клавиатура ─────
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🩺 Начать разговор")],
        [KeyboardButton(text="🔚 Завершить")],
    ],
    resize_keyboard=True,
)


# ───── Обработчики ─────
@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    try:
        async with httpx.AsyncClient() as client:
            await client.post(RESET_URL, json={"user_id": user_id, "message": ""})
    except Exception as e:
        await message.answer(f"⚠️ Ошибка сброса: {e}")

    await message.answer(
        "Привет! Я AI-доктор. Нажми кнопку, чтобы начать.", reply_markup=main_kb
    )


@router.message(F.text == "🩺 Начать разговор")
async def start_dialog(message: Message):
    await message.answer("Опиши свои жалобы одним сообщением.", reply_markup=main_kb)


@router.message(F.text == "🔚 Завершить")
async def end_dialog(message: Message):
    user_id = message.from_user.id

    try:
        async with httpx.AsyncClient() as client:
            await client.post(RESET_URL, json={"user_id": user_id, "message": ""})

        await message.answer(
            "Диалог завершён. Нажми '🩺 Начать разговор', чтобы начать новый.",
            reply_markup=main_kb,
        )

    except Exception as e:
        await message.answer(f"Ошибка при завершении сессии: {str(e)}")


@router.message(F.text)
async def handle_text(message: Message):
    user_id = message.from_user.id
    text = message.text

    # await message.answer("Обрабатываю...")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                MESSAGE_URL, json={"user_id": user_id, "message": text}, timeout=30
            )

        if response.status_code == 200:
            reply_text = response.json().get("reply", "Ответ не получен.")
        else:
            reply_text = "Ошибка сервера. Попробуй позже."

    except Exception as e:
        reply_text = f"Ошибка при соединении: {str(e)}"

    await message.answer(reply_text, reply_markup=main_kb)


# ───── Запуск ─────
def run_bot():
    asyncio.run(dp.start_polling(bot))


if __name__ == "__main__":
    run_bot()
