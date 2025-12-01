from curl_cffi.requests import AsyncSession
from bs4 import BeautifulSoup
from typing import List
from .base import BaseSupplier
from app.models.schemas import PartSchema
import base64
import re

class Ic24Supplier(BaseSupplier):
    def __init__(self):
        self.name = "InterCars (IC24)"
        self.search_url = "https://www.ic24.lv/detalas/search={code}" 
        self.base_host = "https://www.ic24.lv"

    async def search(self, part_number: str) -> List[PartSchema]:
        print(f"[{self.name}] НАЧАЛ ПОИСК: {part_number}", flush=True)
        results = []
        
        encoded_bytes = base64.b64encode(part_number.encode("utf-8"))
        encoded_code = encoded_bytes.decode("utf-8")
        search_page_url = self.search_url.format(code=encoded_code)
        
        # Заголовки
        headers = {
            "Referer": "https://www.ic24.lv/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
        }

        try:
            async with AsyncSession(impersonate="chrome110", headers=headers, timeout=30) as client:
                # print(f"[{self.name}] Запрос...", flush=True)
                response = await client.get(search_page_url)
                
                if response.status_code != 200:
                    print(f"[{self.name}] БЛОКИРОВКА. Статус: {response.status_code}", flush=True)
                    return []

                soup = BeautifulSoup(response.text, "html.parser")
                
                cards = soup.select(".row.m-b-0") 
                if not cards:
                    cards = soup.select(".product-list-item")
                
                print(f"[{self.name}] Найдено: {len(cards)}", flush=True)

                previous_anchor_id = None 

                for i, card in enumerate(cards):
                    try:
                        price_tag = card.select_one(".price_gross_2") 
                        if not price_tag:
                            continue 

                        # 1. БРЕНД
                        brand_tag = card.select_one(".manufacture") or card.select_one(".producer-name")
                        brand = brand_tag.text.strip() if brand_tag else "Unknown"

                        # 2. АРТИКУЛ И ОПИСАНИЕ
                        desc_tag = card.select_one(".description")
                        sku = part_number 
                        if desc_tag:
                            full_desc = desc_tag.text.strip()
                            if brand.lower() in full_desc.lower():
                                parts = re.split(re.escape(brand), full_desc, flags=re.IGNORECASE)
                                combined_text = " ".join(parts)
                                sku = " ".join(combined_text.split())
                            else:
                                sku = full_desc
                        
                        if sku == part_number:
                             sku_tag = card.select_one(".producer-code") or card.select_one(".code")
                             if sku_tag:
                                 sku = sku_tag.text.strip()

                        # 3. ФОТО + ЯКОРЬ (на всякий случай)
                        product_image = None
                        current_element_id = None 
                        img_tag = card.select_one(".zoom_img_without") or card.select_one("img[title]") or card.select_one("img[data-param]")
                        
                        if img_tag:
                            src = img_tag.get("src") or img_tag.get("data-original")
                            if src and "pixel" not in src:
                                if src.startswith("http"):
                                    product_image = src
                                else:
                                    product_image = self.base_host + src
                                
                                # Fix HTTPs
                                if product_image:
                                    product_image = product_image.replace("http://", "https://")
                            
                            current_element_id = img_tag.get("id")

                        # 4. НАЛИЧИЕ
                        count = 0
                        delivery_days = 1 
                        stock_prefix = ""
                        stock_span = card.select_one('[datatest-id="tap-item-product-stock"]')
                        if stock_span:
                            try:
                                count = int(stock_span.text.strip())
                                if count > 0:
                                    delivery_days = 0
                                parent = stock_span.parent
                                if parent and ">" in parent.text:
                                    stock_prefix = "> " 
                            except:
                                count = 0

                        # 5. ЦЕНА
                        raw_price = price_tag.text.strip()
                        clean_price = raw_price.replace("€", "").replace(" ", "").replace("\xa0", "").replace(",", ".")
                        price = float(clean_price)

                        # --- 6. ССЫЛКА (DIRECT PRODUCT LINK) ---
                        # Ищем твой тег <a class="main-link-product-card" ...>
                        link_tag = card.select_one(".main-link-product-card")
                        
                        # Fallback (по умолчанию на поиск с якорем)
                        if previous_anchor_id:
                            final_link = f"{search_page_url}#{previous_anchor_id}"
                        else:
                            final_link = search_page_url

                        # Если нашли прямую ссылку - берем её
                        if link_tag and link_tag.get("href"):
                            href = link_tag.get("href")
                            if href.startswith("http"):
                                final_link = href
                            else:
                                final_link = self.base_host + href

                        # Подготовка якоря для следующей итерации (на случай если прямой ссылки не будет)
                        if current_element_id:
                            previous_anchor_id = current_element_id

                        results.append(PartSchema(
                            supplier_name=self.name,
                            part_number=sku,
                            brand=brand,
                            image=product_image,
                            price=price,
                            currency="EUR",
                            delivery_days=delivery_days,
                            count=count,
                            count_prefix=stock_prefix,
                            link=final_link 
                        ))
                    except Exception:
                        continue
        
        except Exception as e:
            print(f"[{self.name}] Ошибка: {e}", flush=True)

        return results