from fastapi import FastAPI
from routers import attendance, players, chat, matches


app = FastAPI()

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


