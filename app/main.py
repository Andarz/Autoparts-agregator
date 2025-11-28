from fastapi import FastAPI
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
