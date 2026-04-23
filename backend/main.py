from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import attendance, players, chat, matches

app = FastAPI()

# Permitimos peticiones desde el frontend de React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # La URL donde corre Vite
    allow_credentials=True,
    allow_methods=["*"],   # GET, POST, PUT, DELETE, OPTIONS, etc.
    allow_headers=["*"],   # Content-Type, Authorization, etc.
)

app.include_router(attendance.router)
app.include_router(players.router)
app.include_router(chat.router)
app.include_router(matches.router)

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


