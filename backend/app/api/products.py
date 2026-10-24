from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from minio.error import S3Error
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.dependencies import require_admin_token
from app.models import Product
from app.schemas import ProductResponse
from app.storage import storage


router = APIRouter(prefix="/api/products", tags=["products"])
Session = Annotated[AsyncSession, Depends(get_session)]


def serialize(product: Product) -> ProductResponse:
    return ProductResponse(
        id=product.id,
        title=product.title,
        image_url=f"{settings.public_api_url.rstrip('/')}/api/products/{product.id}/image",
        created_at=product.created_at,
    )


@router.get("", response_model=list[ProductResponse])
async def list_products(session: Session) -> list[ProductResponse]:
    result = await session.scalars(
        select(Product)
        .where(Product.is_active.is_(True))
        .order_by(Product.created_at.desc(), Product.id.desc())
    )
    return [serialize(product) for product in result]


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin_token)],
)
async def create_product(
    session: Session,
    title: Annotated[str, Form(min_length=1, max_length=255)],
    source_update_id: Annotated[int, Form(gt=0)],
    image: Annotated[UploadFile, File()],
) -> ProductResponse:
    normalized_title = title.strip()
    if not normalized_title:
        raise HTTPException(status_code=422, detail="Title cannot be blank")

    content_type = image.content_type or "application/octet-stream"
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=422, detail="Only images are accepted")

    existing = await session.scalar(
        select(Product).where(Product.source_update_id == source_update_id)
    )
    if existing is not None:
        return serialize(existing)

    content = await image.read(settings.max_image_size + 1)
    if not content:
        raise HTTPException(status_code=422, detail="Image is empty")
    if len(content) > settings.max_image_size:
        raise HTTPException(status_code=413, detail="Image is too large")

    object_key = f"products/telegram-update-{source_update_id}"
    await storage.upload(object_key, content, content_type)

    product = Product(
        title=normalized_title,
        image_object_key=object_key,
        image_content_type=content_type,
        source_update_id=source_update_id,
    )
    session.add(product)

    try:
        await session.commit()
        await session.refresh(product)
    except IntegrityError:
        await session.rollback()
        duplicate = await session.scalar(
            select(Product).where(Product.source_update_id == source_update_id)
        )
        if duplicate is None:
            raise
        return serialize(duplicate)
    except Exception:
        await session.rollback()
        await storage.delete(object_key)
        raise

    return serialize(product)


@router.get("/{product_id}/image")
async def get_product_image(product_id: int, session: Session) -> StreamingResponse:
    product = await session.get(Product, product_id)
    if product is None or not product.is_active:
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        response = await storage.open(product.image_object_key)
    except S3Error as error:
        if error.code in {"NoSuchKey", "NoSuchObject"}:
            raise HTTPException(status_code=404, detail="Image not found") from error
        raise

    return StreamingResponse(
        storage.chunks(response),
        media_type=product.image_content_type,
        headers={"Cache-Control": "public, max-age=3600"},
    )

