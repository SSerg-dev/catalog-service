from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.api.products import serialize
from app.dependencies import require_admin_token
from app.models import Product


def test_serialize_product() -> None:
    product = Product(
        id=7,
        title="Тестовый товар",
        image_object_key="products/7",
        image_content_type="image/jpeg",
        source_update_id=42,
        created_at=datetime(2026, 10, 23, tzinfo=timezone.utc),
    )

    response = serialize(product)

    assert response.id == 7
    assert response.title == "Тестовый товар"
    assert response.image_url.endswith("/api/products/7/image")


def test_admin_token_validation() -> None:
    require_admin_token("change-me")

    with pytest.raises(HTTPException) as error:
        require_admin_token("wrong-token")

    assert error.value.status_code == 401

