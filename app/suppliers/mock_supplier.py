import asyncio
import random
from typing import List
from .base import BaseSupplier
from app.models.schemas import PartSchema

class MockSupplier(BaseSupplier):
    def __init__(self, name="Demo Supplier", delay=1):
        self.name = name
        self.delay = delay

    async def search(self, part_number: str) -> List[PartSchema]:
        # Имитация работы сети
        await asyncio.sleep(self.delay)
        
        # Возвращаем случайные данные для теста
        return [
            PartSchema(
                supplier_name=self.name,
                part_number=part_number,
                brand="BOSCH",
                price=random.randint(1000, 5000),
                delivery_days=random.randint(0, 5),
                link="#"
            )
        ]
