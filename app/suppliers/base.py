from abc import ABC, abstractmethod
from typing import List
from app.models.schemas import PartSchema

class BaseSupplier(ABC):
    def __init__(self):
        self.name = "Unknown"

    @abstractmethod
    async def search(self, part_number: str) -> List[PartSchema]:
        pass
