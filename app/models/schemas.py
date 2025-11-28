from pydantic import BaseModel
from typing import Optional

class PartSchema(BaseModel):
    supplier_name: str
    part_number: str
    brand: str
    price: float
    currency: str = "RUB"
    delivery_days: int
    count: Optional[int] = None
    link: Optional[str] = None
    brand_img: Optional[str] = None
    image: Optional[str] = None
    count_prefix: str = ""

