import asyncio
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

import httpx


load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_BACKEND_URL = os.getenv("API_BACKEND_URL", "http://localhost:8000")
MESSAGE_URL = f"{API_BACKEND_URL}/message"
RESET_URL = f"{API_BACKEND_URL}/reset"


bot = Bot(token=TELEGRAM_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)


main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🩺 Начать разговор")],
        [KeyboardButton(text="🔚 Завершить")],
    ],
    resize_keyboard=True,
)


async def reset_user_session(user_id: int) -> str:
    try:
        async with httpx.AsyncClient() as client:
            await client.post(RESET_URL, json={"user_id": user_id, "message": ""})
        return ""
    except Exception as e:
        return f"⚠️ Ошибка сброса: {e}"


@router.message(CommandStart())
async def cmd_start(message: Message):
    err = await reset_user_session(message.from_user.id)
    if err:
        await message.answer(err)
    await message.answer(
        "Привет! Я AI-доктор. Нажми кнопку, чтобы начать.", reply_markup=main_kb
    )


@router.message(F.text == "🩺 Начать разговор")
async def start_dialog(message: Message):
    await message.answer("Опиши свои жалобы одним сообщением.", reply_markup=main_kb)


@router.message(F.text == "🔚 Завершить")
async def end_dialog(message: Message):
    err = await reset_user_session(message.from_user.id)
    if err:
        await message.answer(f"Ошибка при завершении сессии: {err}")
    else:
        await message.answer(
            "Диалог завершён. Нажми '🩺 Начать разговор', чтобы начать новый.",
            reply_markup=main_kb,
        )


@router.message(F.text)
async def handle_text(message: Message):
    user_id = message.from_user.id
    text = message.text

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                MESSAGE_URL,
                json={"user_id": user_id, "message": text},
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                reply_text = data.get("reply", "Ответ не получен.")

                if data.get("reset_required"):
                    await reset_user_session(user_id)
                    reply_text += "\n\n🔁 Диалог завершён. Нажми '🩺 Начать разговор', чтобы начать новый."
            else:
                reply_text = "Ошибка сервера. Попробуй позже."

    except Exception as e:
        reply_text = f"Ошибка при соединении: {str(e)}"

    await message.answer(reply_text, reply_markup=main_kb)


def run_bot():
    asyncio.run(dp.start_polling(bot))


if __name__ == "__main__":
    run_bot()
