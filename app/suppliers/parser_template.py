import httpx
from bs4 import BeautifulSoup
from typing import List
from .base import BaseSupplier
from app.models.schemas import PartSchema

class RealShopSupplier(BaseSupplier):
    def __init__(self):
        self.name = "Название Магазина" # <--- 1. Имя поставщика
        # Ссылка поиска (обычно выглядит как site.ru/search?q=НОМЕР)
        self.base_url = "https://example-autoparts.ru/search" 

    async def search(self, part_number: str) -> List[PartSchema]:
        results = []
        
        # Настраиваем "браузер" (User-Agent), чтобы сайт не думал, что мы робот
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        async with httpx.AsyncClient() as client:
            try:
                # Делаем запрос к сайту
                # Обычно параметры передаются как ?q=номер или ?article=номер
                response = await client.get(
                    self.base_url, 
                    params={"q": part_number}, # <--- 2. Параметр поиска на сайте
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    print(f"Ошибка доступа к сайту {self.name}")
                    return []

                # Превращаем HTML в удобный объект
                soup = BeautifulSoup(response.text, "lxml")

                # --- ЗДЕСЬ НАЧИНАЕТСЯ МАГИЯ ПОИСКА ---
                # Нам нужно найти карточки товаров. 
                # Для этого нужно знать CSS-селекторы (классы) сайта.
                
                # Пример: ищем все блоки с классом 'product-item'
                product_cards = soup.select(".product-item") # <--- 3. CSS селектор карточки товара

                for card in product_cards:
                    try:
                        # Внутри карточки ищем бренд, цену и наличие
                        # .text.strip() очищает текст от пробелов
                        
                        brand = card.select_one(".brand-name").text.strip() # <--- 4. Селектор бренда
                        price_text = card.select_one(".price-value").text.strip() # <--- 5. Селектор цены
                        
                        # Чистим цену от "руб", пробелов и превращаем в число
                        price = float(price_text.replace("₽", "").replace(" ", "").replace("\xa0", ""))

                        results.append(PartSchema(
                            supplier_name=self.name,
                            part_number=part_number,
                            brand=brand,
                            price=price,
                            delivery_days=1, # Можно тоже парсить, если есть на сайте
                            link="https://example-autoparts.ru" # Можно вытащить реальную ссылку
                        ))
                    except Exception as e:
                        # Если в одной карточке ошибка, пропускаем её, идем к следующей
                        continue

            except Exception as e:
                print(f"Ошибка при парсинге {self.name}: {e}")
        
        return results