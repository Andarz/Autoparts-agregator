import asyncio
from fastapi import APIRouter, Request, Form, Response
from fastapi.templating import Jinja2Templates
from curl_cffi.requests import AsyncSession

from app.suppliers.mock_supplier import MockSupplier
from app.suppliers.ic24 import Ic24Supplier
from app.services.tecdoc import TecDocService

tecdoc_service = TecDocService()
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

ACTIVE_SUPPLIERS = [
    # MockSupplier(name="Exist (Demo)", delay=0.5),
    # MockSupplier(name="Autodoc (Demo)", delay=1.0),
    # MyShop(),
    Ic24Supplier(),
]


@router.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/search")
async def search(request: Request, part_code: str = Form(...)):
    clean_code = part_code.strip().upper()

    tasks = [s.search(clean_code) for s in ACTIVE_SUPPLIERS]
    results_list = await asyncio.gather(*tasks)

    flat_results = []
    for res in results_list:
        flat_results.extend(res)

    flat_results.sort(key=lambda x: x.price)

    return templates.TemplateResponse(
        "results.html",
        {"request": request, "parts": flat_results, "search_code": clean_code},
    )


# --- ИСПРАВЛЕННЫЙ ПРОКСИ (FIXED URL) ---
@router.get("/proxy-image")
async def proxy_image(url: str):
    if not url:
        return Response(status_code=404)

    # !!! ГЛАВНОЕ ИСПРАВЛЕНИЕ !!!
    # FastAPI превратил %23 в #. Из-за этого запрос обрезается.
    # Превращаем обратно # в %23, чтобы сервер получил полный путь.
    url = url.replace("#", "%23")

    headers = {
        "Referer": "https://www.ic24.lv/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    try:
        async with AsyncSession(
            impersonate="chrome120", headers=headers, verify=False
        ) as client:
            resp = await client.get(url)

            if resp.status_code == 200:
                content_type = resp.headers.get("content-type", "image/jpeg")
                return Response(content=resp.content, media_type=content_type)
            else:
                # Теперь мы увидим реальную ошибку в терминале, если она останется
                print(
                    f"[Proxy Error] URL: {url} | Status: {resp.status_code}", flush=True
                )
                return Response(status_code=resp.status_code)

    except Exception as e:
        print(f"[Proxy Exception] {e}", flush=True)
        return Response(status_code=500)

    # --- НОВАЯ ФУНКЦИЯ: ПОИСК В GOOGLE ---


# --- ИСПРАВЛЕННЫЙ ПОИСК (через DuckDuckGo) ---
@router.get("/google-search-api")
async def google_search_api(query: str):
    """
    Ищет в интернете (DuckDuckGo HTML) с фильтром по Латвии.
    Это работает намного стабильнее, чем прямой парсинг Google.
    """
    if not query:
        return {"results": []}

    # kl=lv-lv -> Регион Латвия
    # q=query -> Запрос
    ddg_url = f"https://html.duckduckgo.com/html/"

    results = []

    # Формируем данные формы (так работает DuckDuckGo HTML)
    data = {
        "q": query,
        "kl": "lv-lv",  # Регион: Латвия
    }

    try:
        # Используем curl_cffi
        async with AsyncSession(impersonate="chrome120") as client:
            # Делаем POST запрос (так надежнее для DDG)
            resp = await client.post(ddg_url, data=data)

            if resp.status_code == 200:
                from bs4 import BeautifulSoup

                soup = BeautifulSoup(resp.text, "html.parser")

                # Селекторы DuckDuckGo Lite
                # Результаты лежат в div с классом "result"
                search_blocks = soup.select(".result")

                for block in search_blocks:
                    try:
                        # Ищем заголовок и ссылку
                        link_tag = block.select_one(".result__a")
                        snippet_tag = block.select_one(".result__snippet")

                        if link_tag:
                            title = link_tag.text.strip()
                            link = link_tag.get("href")
                            desc = snippet_tag.text.strip() if snippet_tag else "..."

                            # Убираем рекламные блоки и ссылки на сам DDG
                            if link.startswith("http") and "duckduckgo.com" not in link:
                                results.append(
                                    {"title": title, "link": link, "desc": desc}
                                )
                    except:
                        continue
            else:
                print(f"Ошибка DDG: {resp.status_code}")

    except Exception as e:
        print(f"Ошибка поиска: {e}")

    # Ограничиваем выдачу топ-15, чтобы не грузить лишнее
    return {"results": results[:15]}


@router.get("/api/tecdoc-info")
async def api_tecdoc_info(part: str):
    """
    Фронтенд запрашивает информацию о детали через наш сервер.
    """
    if not part:
        return {"found": False}

    data = await tecdoc_service.get_part_info(part)
    return data
