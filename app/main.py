from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth

app = FastAPI(
    title="MA – Maruim Acadêmico",
    description="Backend do sistema de gestão do transporte universitário",
    version="0.1.0"
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

@app.get("/")
def raiz():
    return {"status": "ok", "projeto": "MA – Maruim Acadêmico"}

@app.get("/health")
def health_check():
    return {"status": "online"}