from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import funcoes  # só importa o funcoes

def create_app() -> FastAPI:
    app = FastAPI(
        title="Backend IA",
        description="API para integração com agente Mistral",
        version="1.0.0",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Inclui router do módulo funcoes
    app.include_router(funcoes.router, prefix="/funcoes", tags=["Funcoes"])

    @app.get("/")
    async def root():
        return {"message": "Backend IA funcionando"}

    return app

app = create_app()
