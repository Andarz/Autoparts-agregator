import asyncio
from fastapi import APIRouter, Request, Form, Response 
from fastapi.templating import Jinja2Templates
from curl_cffi.requests import AsyncSession

from app.suppliers.mock_supplier import MockSupplier
from app.suppliers.ic24 import Ic24Supplier
from app.suppliers.my_shop import MyShop

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

ACTIVE_SUPPLIERS = [
    # MockSupplier(name="Exist (Demo)", delay=0.5),
    # MockSupplier(name="Autodoc (Demo)", delay=1.0),
    MyShop(),
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

    return templates.TemplateResponse("results.html", {
        "request": request, 
        "parts": flat_results,
        "search_code": clean_code
    })

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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        async with AsyncSession(impersonate="chrome120", headers=headers, verify=False) as client:
            resp = await client.get(url)
            
            if resp.status_code == 200:
                content_type = resp.headers.get("content-type", "image/jpeg")
                return Response(content=resp.content, media_type=content_type)
            else:
                # Теперь мы увидим реальную ошибку в терминале, если она останется
                print(f"[Proxy Error] URL: {url} | Status: {resp.status_code}", flush=True)
                return Response(status_code=resp.status_code)
                
    except Exception as e:
        print(f"[Proxy Exception] {e}", flush=True)
        return Response(status_code=500)