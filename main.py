from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config.settings import settings
from api.v1.routes import api_version_one

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_version_one)

@app.get("/")
def healthcheck():
    return {"status": "ok"}