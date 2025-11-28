import asyncio 
from typing import List
# Это как 'using App.Suppliers.Base;' и 'using App.Models;'
from .base import BaseSupplier
from app.models.schemas import PartSchema

# В C#: public class MyShop : BaseSupplier
class MyShop(BaseSupplier): 
    
    # Это конструктор (в C# это public MyShop() { ... })
    def __init__(self):
        self.name = "Мой Тестовый Магазин"
        self.delay = 2 # Имитация задержки сайта (сек)

    # В C#: public async Task<List<PartSchema>> Search(string part_number)
    async def search(self, part_number: str) -> List[PartSchema]:
        
        print(f"[{self.name}] Начал поиск детали: {part_number}")
        
        # await - это как await в C#, ждем выполнения асинхронной задачи
        await asyncio.sleep(self.delay) 
        
        # Создаем список результатов (как var list = new List<PartSchema>();)
        results = []

        # Добавляем "найденный" товар
        # Обрати внимание: именованные аргументы (supplier_name=...) делают код читаемым
        found_part = PartSchema(
            supplier_name=self.name,
            part_number=part_number,
            brand="TestBrand",
            price=5500.00,
            currency="RUB",
            delivery_days=2,
            available=True
        )
        
        results.append(found_part)
        
        print(f"[{self.name}] Поиск завершен!")
        
        return results