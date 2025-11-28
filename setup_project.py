import os

# Структура проекта и содержимое файлов
project_structure = {
    "requirements.txt": """fastapi
uvicorn
jinja2
python-multipart
httpx
pydantic
pydantic-settings
aiofiles
""",
    ".gitignore": """__pycache__/
*.pyc
.env
.venv/
env/
""",
    ".env": """SECRET_KEY=supersecretkey
""",
    "app/__init__.py": "",
    "app/main.py": """from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers import web

app = FastAPI(title="Auto Parts Aggregator")

# Подключение статики (CSS, JS)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Подключение маршрутов
app.include_router(web.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
""",
    "app/core/__init__.py": "",
    "app/core/config.py": """from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Auto Parts Aggregator"
    
    class Config:
        env_file = ".env"

settings = Settings()
""",
    "app/models/__init__.py": "",
    "app/models/schemas.py": """from pydantic import BaseModel
from typing import Optional

class PartSchema(BaseModel):
    supplier_name: str
    part_number: str
    brand: str
    price: float
    currency: str = "RUB"
    delivery_days: int
    count: Optional[int] = None
    link: Optional[str] = None
""",
    "app/suppliers/__init__.py": "",
    "app/suppliers/base.py": """from abc import ABC, abstractmethod
from typing import List
from app.models.schemas import PartSchema

class BaseSupplier(ABC):
    def __init__(self):
        self.name = "Unknown"

    @abstractmethod
    async def search(self, part_number: str) -> List[PartSchema]:
        pass
""",
    "app/suppliers/mock_supplier.py": """import asyncio
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
""",
    "app/routers/__init__.py": "",
    "app/routers/web.py": """import asyncio
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
""",
    "app/templates/base.html": """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Агрегатор{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; }
        .main-container { max-width: 800px; margin: 40px auto; padding: 20px; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    </style>
</head>
<body>
    <div class="container">
        {% block content %}{% endblock %}
    </div>
</body>
</html>
""",
    "app/templates/index.html": """{% extends "base.html" %}

{% block content %}
<div class="main-container text-center">
    <h2 class="mb-4">🚙 Поиск запчастей</h2>
    <form action="/search" method="post">
        <div class="input-group input-group-lg mb-3">
            <input type="text" name="part_code" class="form-control" placeholder="Введите номер детали..." required>
            <button class="btn btn-primary" type="submit">Найти</button>
        </div>
        <small class="text-muted">Поиск выполняется по всем подключенным поставщикам одновременно.</small>
    </form>
</div>
{% endblock %}
""",
    "app/templates/results.html": """{% extends "base.html" %}

{% block content %}
<div class="mt-4">
    <a href="/" class="btn btn-outline-secondary mb-3">← Назад</a>
    <h4>Результаты для: {{ search_code }}</h4>
    
    {% if parts %}
    <div class="table-responsive bg-white p-3 rounded shadow-sm">
        <table class="table table-hover align-middle">
            <thead class="table-light">
                <tr>
                    <th>Поставщик</th>
                    <th>Бренд / Артикул</th>
                    <th>Цена</th>
                    <th>Срок</th>
                    <th></th>
                </tr>
            </thead>
            <tbody>
                {% for part in parts %}
                <tr>
                    <td><span class="badge bg-secondary">{{ part.supplier_name }}</span></td>
                    <td>
                        <strong>{{ part.brand }}</strong><br>
                        <small class="text-muted">{{ part.part_number }}</small>
                    </td>
                    <td class="fs-5 fw-bold text-success">{{ part.price }} ₽</td>
                    <td>
                        {% if part.delivery_days == 0 %}
                            <span class="text-success fw-bold">В наличии</span>
                        {% else %}
                            {{ part.delivery_days }} дн.
                        {% endif %}
                    </td>
                    <td>
                        <button class="btn btn-sm btn-primary">Заказать</button>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% else %}
        <div class="alert alert-warning">Ничего не найдено.</div>
    {% endif %}
</div>
{% endblock %}
""",
    "app/static/css/style.css": "/* Дополнительные стили */",
    "app/static/js/main.js": "// Скрипты",
    "tests/__init__.py": "",
    "tests/test_suppliers.py": "# Тесты для поставщиков"
}

def create_structure():
    for path, content in project_structure.items():
        # Создаем папки, если их нет
        dir_name = os.path.dirname(path)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name)
        
        # Записываем файлы
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Created: {path}")

if __name__ == "__main__":
    create_structure()
    print("\\n✅ Проект успешно создан!")
    print("👉 Теперь выполни следующие команды:")
    print("1. python -m venv venv (Создать виртуальное окружение)")
    print("2. venv\\Scripts\\activate (Windows) или source venv/bin/activate (Linux/Mac)")
    print("3. pip install -r requirements.txt")
    print("4. uvicorn app.main:app --reload")