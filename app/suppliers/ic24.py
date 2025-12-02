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

        # --- МЕСТО ДЛЯ КУКИ ---
        # Вставь сюда всю длинную строку, которую скопировал из браузера
        self.cookie = "osano_consentmanager_uuid=b70b9b9d-0596-4e7a-90c7-e09cc5356d29; osano_consentmanager=mrO2mjvdsVfuWGFNAKo1uM4j5hVS1Sm7finj74pynDsfZEHLgt2kAvnxJCnb70IOzPMBwELGnO-00cdbJCvDaMxfQjxSOPYm_rkes1MwIZwoMEjHSsjY_7tWUG2fk6W_zsIl601V6y6W2Ju8qf6dlDg3VKjtGyBcV7nRtsc1hsW6JOw-usCH0UMGMsDprA8QhvcbEqWv6jy2RtF5ObdBnVYji2VpE7nFmlCiiPFRC1rW6Xuxg8Hur6eGzsMHkeZu5ej3uyDt7b1jqltYghz6Qm6nLZT13rLEzfDU8F2uqEHoswM9cIm2_6ZtKvSi6P7O7V2Eedu2s54=; TIMEZONE_OFFSET=120; is-mobile=0; lang=LV; _gcl_au=1.1.709909158.1764077100; _ga=GA1.1.240628136.1764077101; cat-price-currency=; hidePrice=0; smuuid=19abc83c8f4-b8da59c88cbc-5e5bf7b3-92df5768-377df75a-893901e0653f; _tt_enable_cookie=1; _ttp=01KAY87J9KSNS9F67CQD3QX2R5_.tt.1; PHPSESSID=b0eb5d77c95c1b7b5334e99165efb81a; VehicleType=449118211818; app_kth=V18302; VehicleArea=O; VehicleNameFull=RENAULT%20GRAND%20SCENIC%20III%20%28JZ0%2F1_%29%201.5%20dCi%20%28JZ09%2C%20JZ0D%2C%20JZ10%2C%20JZ14%2C%20JZ1G%2C%20JZ29%2C%20JZ2C%29; VehicleMakeNamed=RENAULT; VehicleModelNamed=GRAND%20SCENIC%20III%20%28JZ0%2F1_%29; VehicleTypeNamed=1.5%20dCi%20%28JZ09%2C%20JZ0D%2C%20JZ10%2C%20JZ14%2C%20JZ1G%2C%20JZ29%2C%20JZ2C%29; smvr=eyJ2aXNpdHMiOjMsInZpZXdzIjo0LCJ0cyI6MTc2NDM1MjM0Njc0NywiaXNOZXdTZXNzaW9uIjpmYWxzZX0=; ttcsid=1764352346683::x-5DwKTLdpOFOjAZEm6B.4.1764352355238.0; ttcsid_CVVOTUJC77U7SM51I7B0=1764352346682::WrtKOlDkKodB5xavD_UH.4.1764352355239.0; cat-price-sort=0; VehicleMake=44912216; VehicleModel=449121141721; VehicleName=renault-grand-scenic-iii-jz0-1-1-5-dci-jz09-jz0d-jz10-jz14-jz1g-jz29-jz2c; umbrella_open=1; Key=1; app_token=v1.EiAnuTSTgBK4p0BSlz2KqJVDZrD-ROd9ANlkIKNCmCJFwg-ZQdlefzMHjNMapjUkCEtfGhiIzywQ_UyVFLkDiHa2d6a0R5-rOYB7SAQ4p3xrq_slJbe8xUbGOtyw1UEoKxYQwkBhbPEaRXKKVzmNvV9k2WvdN2w3wlhbV6q3pXnRH8PrQpBoJXPfuY1V4OMmL2a6WDeoD0XcFicBqWxCvFp-gCS-CIAH2hfjO3HypUdbxj7A2SA26b4L49NEDMDVd0Ibch27F3N2k-PmJEf2c1TsRvd8SiixvgvCne2myMuhJir_J7vTzDrCn6NOPeN1nG79Nf4CvolIVvuQz3n3xu5CZ5HDUtgfz6NdqqLSUKNtgfcgtqfYQ3e6AQvTLLx10_HxWq7E0Hl_qfMNS37DmTT3P0twmWTKQsqIc72Ow8Pj1n3dt3vzgM0O1BiO1s2oJi86TrejVfllys3Waxr2ODRdX9MHE_4vdFgCLghd6qtQvN2C6QVUZyJzfO4tmZlXetriMmx8leULwJtyUxFAZrfwrqYlkHt7aM9uW7u39NZ6CpDeKZujT1l71uMazTXhyQwRwwDOByHCvhTFHSn50C23XzLXvvyZ257lw7KCu8-WFpjR3xoN_RzBujiP6bGc4A-zXTf7WXR-waxi3DTks7-6yGId7eTzCAVKxGFCWcCQD8Mik6aZNOPQi3JUu-ZM5Q12EPeFdZS6rmnNlrD3lJscCRy03BCH_8RrTEQGddRx6TPz_1MnVfm9P6U_T4owYnbCoIfwtX6YPpeFaknT9qchbg5Tq9ahKNVJ22cTh5QmizztQxqSpu2GCutiATl-IzgsXXSRWiUae_Hm0r-G81nNoJejsJPD6NdoKFx_jPpL1HXbAxf11kOWvnGbGQUA1v-uzC8HF9ouOwHlb_FpUePpoSDz-dLVGh8agTz7pc4DND2kIq6H5-jmSPrKEwDyjy3ZUlKVsA_SqXLYq9ctk4OH2Uy6umf8rsR2xwYaFw7N2JCL13Own_R4woU5x6gbBC_v0jQ1ioFZ5jIzjy4Z0ELhZE4ZELDVSPPrYO4WSq2qDOdvNig15UCr6Yx1vrci0c2EJn-dZus-qnV3wvDd9PD93hsqBv_ybUj3Ngl3cS_UQ7PIJvcZ7-OF4sX3wFAF4S-niqOHtLDMsItAHfq3JovSIkQveCcAb5JPEvcvEOZ32T4GUM2f2XWeNHzCOLcQJNyJ_lh05_SwaNz22bf5uj0FryevYR_1qg5q70m7IIPHyfetkeJZsVz-z0Sg8-kxAocEANY25CoOGrUScdxOPinYJU21NZqZL750IdU347QeWGD3SyxqdJcN4XKS0oikOENdcWXcppXkfi4LQvdBmbGvhUcfaDrNJZgYKyBUBdU; cat-price-type=B; cf_clearance=jWdJzt7ouyFEAo5gI.2VCwJz_zOw9E.exPl.IiDAKFs-1764669952-1.2.1.1-9sBSUDsDQ1ruXEltyDdK3i3aBar_Su2VSOwCb0LyDfoV0fS3a8EeeIdqUriKcIWYj6nvyZ2F87fck5Vu.PjXka_u3qMw534Yfmsds3gMz8zVku_1o7PuJ98ZRNd6cmMUFU9i55PoxZ4OJIHKNCESUd_QTw0YX7suyBilurlyVNk3XWqQDa91xpC2VSnW5wO8vNPaE3NGhlX.x4iFtCJn9UwENn7t9G9I2J9LqsK_0BM; firstrun=F; _ga_0W2HXH1T6S=GS2.1.s1764669948$o20$g1$t1764670027$j46$l0$h0; theme_name=ictheme-pl"
        # ----------------------

    async def search(self, part_number: str) -> List[PartSchema]:
        print(f"[{self.name}] НАЧАЛ ПОИСК: {part_number}", flush=True)
        results = []

        encoded_bytes = base64.b64encode(part_number.encode("utf-8"))
        encoded_code = encoded_bytes.decode("utf-8")
        search_page_url = self.search_url.format(code=encoded_code)

        # Добавляем куку в заголовки
        headers = {
            "Referer": "https://www.ic24.lv/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Cookie": self.cookie,  # <--- ВОТ ЗДЕСЬ ОНА ИСПОЛЬЗУЕТСЯ
        }

        try:
            async with AsyncSession(
                impersonate="chrome120", headers=headers, timeout=30
            ) as client:
                # print(f"[{self.name}] Запрос...", flush=True)
                response = await client.get(search_page_url)

                if response.status_code != 200:
                    print(
                        f"[{self.name}] БЛОКИРОВКА. Статус: {response.status_code}",
                        flush=True,
                    )
                    # Если 403 - значит кука протухла или не скопирована
                    return []

                soup = BeautifulSoup(response.text, "html.parser")

                # Проверка на капчу
                if "Just a moment" in soup.text:
                    print(f"[{self.name}] Капча Cloudflare!", flush=True)
                    return []

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

                        # БРЕНД
                        brand_tag = card.select_one(".manufacture") or card.select_one(
                            ".producer-name"
                        )
                        brand = brand_tag.text.strip() if brand_tag else "Unknown"

                        # АРТИКУЛ
                        desc_tag = card.select_one(".description")
                        sku = part_number
                        if desc_tag:
                            full_desc = desc_tag.text.strip()
                            if brand.lower() in full_desc.lower():
                                parts = re.split(
                                    re.escape(brand), full_desc, flags=re.IGNORECASE
                                )
                                combined_text = " ".join(parts)
                                sku = " ".join(combined_text.split())
                            else:
                                sku = full_desc

                        if sku == part_number:
                            sku_tag = card.select_one(
                                ".producer-code"
                            ) or card.select_one(".code")
                            if sku_tag:
                                sku = sku_tag.text.strip()

                        # ФОТО
                        product_image = None
                        current_element_id = None
                        img_tag = (
                            card.select_one(".zoom_img_without")
                            or card.select_one("img[title]")
                            or card.select_one("img[data-param]")
                        )
                        if img_tag:
                            src = img_tag.get("src") or img_tag.get("data-original")
                            if src and "pixel" not in src:
                                if src.startswith("http"):
                                    product_image = src
                                else:
                                    product_image = self.base_host + src
                                if product_image:
                                    product_image = product_image.replace(
                                        "http://", "https://"
                                    )
                            current_element_id = img_tag.get("id")

                        # НАЛИЧИЕ
                        count = 0
                        delivery_days = 1
                        stock_prefix = ""
                        stock_span = card.select_one(
                            '[datatest-id="tap-item-product-stock"]'
                        )
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

                        # ЦЕНА
                        raw_price = price_tag.text.strip()
                        clean_price = (
                            raw_price.replace("€", "")
                            .replace(" ", "")
                            .replace("\xa0", "")
                            .replace(",", ".")
                        )
                        price = float(clean_price)

                        # ССЫЛКА (Прямая)
                        link_tag = card.select_one(".main-link-product-card")
                        if previous_anchor_id:
                            final_link = f"{search_page_url}#{previous_anchor_id}"
                        else:
                            final_link = search_page_url

                        if link_tag and link_tag.get("href"):
                            href = link_tag.get("href")
                            if href.startswith("http"):
                                final_link = href
                            else:
                                final_link = self.base_host + href

                        if current_element_id:
                            previous_anchor_id = current_element_id

                        results.append(
                            PartSchema(
                                supplier_name=self.name,
                                part_number=sku,
                                brand=brand,
                                image=product_image,
                                price=price,
                                currency="EUR",
                                delivery_days=delivery_days,
                                count=count,
                                count_prefix=stock_prefix,
                                link=final_link,
                            )
                        )
                    except Exception:
                        continue

        except Exception as e:
            print(f"[{self.name}] Ошибка: {e}", flush=True)

        return results
