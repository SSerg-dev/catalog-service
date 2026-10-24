import asyncio
import logging

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramRetryAfter
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from app.config import settings
from app.handlers import api_client, router


logging.basicConfig(level=logging.INFO)


async def health(_: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


async def unavailable(_: web.Request) -> web.Response:
    return web.json_response(
        {"detail": "TELEGRAM_BOT_TOKEN is not configured"}, status=503
    )


async def on_startup(bot: Bot, dispatcher: Dispatcher) -> None:
    if settings.telegram_webhook_url:
        webhook = await bot.get_webhook_info()
        if webhook.url == settings.telegram_webhook_url:
            return

        try:
            await bot.set_webhook(
                settings.telegram_webhook_url,
                secret_token=settings.telegram_webhook_secret,
                allowed_updates=dispatcher.resolve_used_update_types(),
            )
        except TelegramRetryAfter as error:
            await asyncio.sleep(error.retry_after)
            webhook = await bot.get_webhook_info()
            if webhook.url != settings.telegram_webhook_url:
                raise


async def on_shutdown(bot: Bot) -> None:
    await api_client.aclose()
    await bot.session.close()


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/health", health)

    if not settings.telegram_bot_token:
        app.router.add_post("/telegram/webhook", unavailable)
        return app

    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    dispatcher.startup.register(on_startup)
    dispatcher.shutdown.register(on_shutdown)

    SimpleRequestHandler(
        dispatcher=dispatcher,
        bot=bot,
        secret_token=settings.telegram_webhook_secret,
    ).register(app, path="/telegram/webhook")
    setup_application(app, dispatcher, bot=bot)
    return app


if __name__ == "__main__":
    web.run_app(create_app(), host="0.0.0.0", port=8080)

