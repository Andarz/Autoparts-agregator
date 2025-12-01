import httpx
from typing import Dict, List, Optional

class TecDocService:
    def __init__(self):
        # ВСТАВЬ СВОЙ КЛЮЧ
        self.api_key = "4b8df632b2mshf6bf04a01f5afd9p100a80jsn80bc749ef6d6"
        self.host = "tecdoc-catalog.p.rapidapi.com"
        self.base_url = f"https://{self.host}"
        
        self.headers_form = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": self.host,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        self.headers_json = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": self.host,
            "Content-Type": "application/json"
        }

    async def get_part_info(self, part_number: str) -> Dict:
        results = {"specs": [], "crosses": [], "image": None, "found": False, "brand": ""}
        if not part_number: return results

        async with httpx.AsyncClient(timeout=25.0) as client:
            article_id = None

            # --- ПОПЫТКА 1: Поиск по Артикулу (POST Form) ---
            try:
                url = f"{self.base_url}/articles/article-number-details"
                payload = {
                    "articleNo": part_number,  
                    "langId": "16",            
                    "countryFilterId": "63",
                    "typeId": "1"
                }
                
                print(f"[TECDOC] 1. Ищу артикул '{part_number}'...", flush=True)
                resp = await client.post(url, data=payload, headers=self.headers_form)
                
                if resp.status_code == 200:
                    data = resp.json()
                    items = []
                    if isinstance(data, list): items = data
                    elif isinstance(data, dict): items = data.get("articles") or data.get("data") or []
                    
                    if items:
                        print(f"[TECDOC] Найдено по артикулу! ID: {items[0].get('articleId')}")
                        self._parse_item(items[0], results)
                        return results
            except Exception as e:
                print(f"[TECDOC ERR 1] {e}")

            # --- ПОПЫТКА 2: Поиск по OEM (POST JSON) ---
            if not results["found"]:
                try:
                    clean_oem = part_number.replace("/", "").replace(" ", "").replace("-", "")
                    print(f"[TECDOC] 2. Ищу OEM '{clean_oem}'...", flush=True)
                    
                    url_oem = f"{self.base_url}/articles-oem/article-oem-search-no"
                    payload_oem = {"article_oem_no": clean_oem, "lang_id": 16, "country_filter_id": 63}
                    
                    resp_oem = await client.post(url_oem, json=payload_oem, headers=self.headers_json)
                    
                    if resp_oem.status_code == 200:
                        data = resp_oem.json()
                        items = data if isinstance(data, list) else data.get("articles", [])
                        
                        if items:
                            article_id = items[0].get("articleId")
                            print(f"[TECDOC] Найдено по OEM! ID: {article_id}")
                            await self._load_details(client, article_id, results)
                except Exception as e:
                    print(f"[TECDOC ERR 2] {e}")

        return results

    async def _load_details(self, client, article_id, results):
        url = f"{self.base_url}/articles/article-details"
        try:
            resp = await client.get(url, params={"articleId": article_id, "includeAll": "true", "langId": 16}, headers={"x-rapidapi-key": self.api_key})
            if resp.status_code == 200:
                data = resp.json()
                item = data[0] if isinstance(data, list) and data else data
                if item:
                    self._parse_item(item, results)
        except Exception:
            pass

    def _parse_item(self, item: dict, results: Dict):
        """Парсинг JSON с проверкой всех уровней вложенности"""
        results["found"] = True
        
        # 1. Бренд
        results["brand"] = item.get("supplierName") or item.get("brandName") or item.get("manufacturerName") or ""
        
        # 2. Картинка
        if not results["image"]:
            if item.get("s3image"): results["image"] = item.get("s3image")
            elif item.get("images"): results["image"] = item["images"][0].get("imageURL600")

        # Вспомогательный объект info (если есть)
        info = item.get("articleInfo", {})

        # 3. Характеристики
        # Ищем список СНАРУЖИ (item) и ВНУТРИ (info)
        specs_list = (
            item.get("allSpecifications") or 
            info.get("allSpecifications") or 
            item.get("articleAttributes") or 
            []
        )
        
        for spec in specs_list:
            name = spec.get("criteriaName") or spec.get("description")
            val = spec.get("criteriaValue") or spec.get("value")
            if name and val:
                if not any(s['name'] == name for s in results['specs']):
                    results["specs"].append({"name": name, "value": val})

        # 4. Кроссы (Оригинал)
        oems_list = (
            item.get("oemNo") or 
            info.get("oemNo") or 
            item.get("oemNumbers") or 
            []
        )
        
        for oem in oems_list:
            b = oem.get("oemBrand") or oem.get("manufacturerName", "OEM")
            n = oem.get("oemDisplayNo") or oem.get("articleNumber", "")
            results["crosses"].append({"brand": b, "number": n})

        # 5. Кроссы (Аналоги)
        crosses_list = (
            item.get("comparableNumbers") or 
            info.get("comparableNumbers") or 
            item.get("articleCrosses") or 
            []
        )
        
        for cross in crosses_list:
            b = cross.get("brandName") or cross.get("supplierName") or cross.get("manufacturerName", "")
            n = cross.get("articleNumber", "")
            results["crosses"].append({"brand": b, "number": n})
        
        print(f"[TECDOC] Готово! Спеков: {len(results['specs'])}, Кроссов: {len(results['crosses'])}")