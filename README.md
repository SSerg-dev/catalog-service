# Мини-сервис каталога

Минимальный каталог товаров на Next.js, FastAPI, aiogram, PostgreSQL и MinIO. Администратор отправляет боту фотографию с названием в подписи, после чего товар появляется в веб-каталоге и Telegram Mini App.

## Архитектура

- `frontend` — Next.js App Router, серверный рендеринг списка товаров.
- `api` — FastAPI, хранит метаданные в PostgreSQL и изображения в MinIO.
- `bot` — aiogram 3 webhook-приложение. Состояние диалога не хранится: название и фото приходят одним сообщением.
- `gateway` — единая локальная точка входа и балансировка между репликами приложений.
- `migrate` и `minio-init` — одноразовая подготовка схемы и bucket.

Приложения stateless. Они не сохраняют сессии или файлы на локальный диск, поэтому `api`, `frontend` и `bot` можно запускать в нескольких репликах. Повторная доставка Telegram update безопасна: `update_id` хранится как уникальный ключ товара, а объект в MinIO получает детерминированное имя.

## Локальный запуск

```bash
cp .env.example .env
docker compose up --build
```

После запуска доступны:

- каталог: <http://localhost:3000>
- API и Swagger: <http://localhost:8000/docs>
- MinIO Console: <http://localhost:9001>
- локальная точка webhook: <http://localhost:8081/telegram/webhook>

Для реального Telegram-бота заполните в `.env`:

- `TELEGRAM_BOT_TOKEN`;
- `TELEGRAM_ADMIN_IDS` — Telegram ID администраторов через запятую;
- `TELEGRAM_WEBHOOK_URL` — публичный HTTPS URL, ведущий на `/telegram/webhook` сервиса `gateway`;
- `WEB_APP_URL` — публичный HTTPS URL frontend;
- безопасные `ADMIN_API_TOKEN` и `TELEGRAM_WEBHOOK_SECRET`.

Локальный порт `8081` можно опубликовать через любой HTTPS-туннель. После старта бот сам регистрирует webhook.

## Масштабирование

```bash
docker compose up --build --scale api=2 --scale frontend=2 --scale bot=2
```

Фиксированные host-порты опубликованы только у `gateway`, поэтому реплики приложений не конфликтуют. В production эту роль выполняет ingress/load balancer, а PostgreSQL и MinIO используют отдельное отказоустойчивое развертывание. Миграции запускаются отдельной задачей до старта новых реплик.

## Проверки

```bash
(cd frontend && npm ci && npm run build)
(cd backend && python -m pytest -q)
(cd bot && python -m pytest -q)
docker compose config --quiet
```

Python-зависимости для локальных тестов перечислены в `requirements-dev.txt`.

## API

- `GET /api/products` — активные товары.
- `GET /api/products/{id}/image` — поток изображения из MinIO.
- `POST /api/products` — создание товара через multipart, защищено `X-Admin-Token`.
- `GET /health` — проверка процесса API.

