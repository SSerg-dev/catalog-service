from io import BytesIO

import httpx
from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    Update,
    WebAppInfo,
)

from app.config import settings


router = Router()
api_client = httpx.AsyncClient(timeout=30)


def is_admin(message: Message) -> bool:
    return message.from_user is not None and message.from_user.id in settings.admin_ids


def menu(message: Message) -> ReplyKeyboardMarkup:
    rows = [
        [
            KeyboardButton(
                text="Открыть каталог",
                web_app=WebAppInfo(url=settings.web_app_url),
            )
        ]
    ]
    if is_admin(message):
        rows.append([KeyboardButton(text="Создать товар")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


async def show_catalog(message: Message) -> None:
    await message.answer("У меня есть товар", reply_markup=menu(message))


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    await show_catalog(message)


@router.message(F.text == "Создать товар")
async def request_product(message: Message) -> None:
    if not is_admin(message):
        await show_catalog(message)
        return

    await message.answer(
        "Отправьте фотографию товара и укажите его название в подписи к фото."
    )


@router.message(F.photo)
async def create_product(message: Message, event_update: Update) -> None:
    if not is_admin(message):
        await show_catalog(message)
        return

    title = (message.caption or "").strip()
    if not title:
        await message.answer("Добавьте название товара в подпись к фотографии.")
        return

    photo = message.photo[-1]
    image = BytesIO()
    await message.bot.download(photo.file_id, destination=image)

    response = await api_client.post(
        f"{settings.api_base_url.rstrip('/')}/api/products",
        headers={"X-Admin-Token": settings.admin_api_token},
        data={"title": title, "source_update_id": str(event_update.update_id)},
        files={"image": ("product.jpg", image.getvalue(), "image/jpeg")},
    )

    if response.status_code >= 500:
        response.raise_for_status()
    if response.status_code not in {200, 201}:
        await message.answer("Не удалось сохранить товар. Попробуйте ещё раз.")
        return

    await message.answer("Товар добавлен.", reply_markup=menu(message))


@router.message()
async def handle_other_message(message: Message) -> None:
    await show_catalog(message)

