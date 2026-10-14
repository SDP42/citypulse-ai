from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from citypulse.api.routes import health, imports, observations, sources
from citypulse.core.errors import install_handlers
from citypulse.db.connection import connect, migrate
from citypulse.db.seed import seed_all


@asynccontextmanager
async def lifespan(app: FastAPI):
    con = connect()
    try:
        migrate(con)
        seed_all(con)
    finally:
        con.close()
    yield


app = FastAPI(title="CityPulse AI", version="0.0.1", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
install_handlers(app)
app.include_router(health.router)
app.include_router(sources.router)
app.include_router(imports.router)
app.include_router(observations.router)
