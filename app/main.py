
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routers import auth, viagens, penalidades
from app.scheduler import iniciar_agendador, parar_agendador


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Roda quando o servidor inicia
    iniciar_agendador()
    yield
    # Roda quando o servidor encerra
    parar_agendador()

app = FastAPI(
    title="MA – Maruim Acadêmico",
    description="Backend do sistema de gestão do transporte universitário",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra os routers
app.include_router(auth.router)
app.include_router(viagens.router)
app.include_router(penalidades.router)

@app.get("/")
def raiz():
    return {"status": "ok", "projeto": "MA – Maruim Acadêmico"}

@app.get("/health")
def health_check():
    return {"status": "online"}