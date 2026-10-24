from datetime import datetime

from pydantic import BaseModel


class ProductResponse(BaseModel):
    id: int
    title: str
    image_url: str
    created_at: datetime

