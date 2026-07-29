import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import attendance, players, matches, public, admin

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from services.telegram_bot import start_bot, stop_bot
    await start_bot()
    yield
    await stop_bot()


app = FastAPI(lifespan=lifespan)

# Permitimos peticiones desde cualquier origen (necesario para producción en Vercel/Render)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # En producción, permitimos cualquier origen para evitar errores de CORS
    allow_credentials=True,
    allow_methods=["*"],   # GET, POST, PUT, DELETE, OPTIONS, etc.
    allow_headers=["*"],   # Content-Type, Authorization, etc.
)


app.include_router(attendance.router)
app.include_router(players.router)
app.include_router(matches.router)
app.include_router(public.router)
app.include_router(admin.router)

@app.get("/")
def root():
    return {"message": "Footbot API is running"}

# # Dependency to get the current user
# async def get_current_user():
#     user = supabase.auth.get_user()
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid authentication credentials",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     return user


