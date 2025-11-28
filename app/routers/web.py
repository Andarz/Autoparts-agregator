import asyncio
from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from app.suppliers.mock_supplier import MockSupplier

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Список подключенных поставщиков
# Сюда будем добавлять реальных парсеров позже
ACTIVE_SUPPLIERS = [
    MockSupplier(name="Exist (Demo)", delay=0.5),
    MockSupplier(name="Autodoc (Demo)", delay=1.0),
    MockSupplier(name="Local Shop", delay=0.2),
]

@router.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/search")
async def search(request: Request, part_code: str = Form(...)):
    clean_code = part_code.strip().upper()
    
    # Запускаем поиск параллельно по всем поставщикам
    tasks = [s.search(clean_code) for s in ACTIVE_SUPPLIERS]
    results_list = await asyncio.gather(*tasks)
    
    # Собираем все результаты в один список
    flat_results = []
    for res in results_list:
        flat_results.extend(res)
        
    # Сортировка по цене
    flat_results.sort(key=lambda x: x.price)

    return templates.TemplateResponse("results.html", {
        "request": request, 
        "parts": flat_results,
        "search_code": clean_code
    })
