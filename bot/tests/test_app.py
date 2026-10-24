from app.config import settings
from app.main import create_app


def test_app_exposes_health_and_webhook() -> None:
    app = create_app()
    paths = {route.resource.canonical for route in app.router.routes()}

    assert "/health" in paths
    assert "/telegram/webhook" in paths


def test_app_configures_aiogram_webhook(monkeypatch) -> None:
    monkeypatch.setattr(
        settings,
        "telegram_bot_token",
        "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi",
    )

    app = create_app()
    paths = {route.resource.canonical for route in app.router.routes()}

    assert "/telegram/webhook" in paths


