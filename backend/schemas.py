from pydantic import BaseModel
from typing import Optional, List

class ChatRequest(BaseModel):
    prompt: str
    model: str = "llama3"
    auth_id: str


class AttendanceRequest(BaseModel):
    text: str
    model: str = "llama3"
    # TODO (Fase 8): Añadir el campo auth_id para recibir el ID del usuario logueado
    auth_id: str
    

class Player(BaseModel):
    name: str
    nickname: Optional[str] = None
    dni: Optional[str] = None
    email: Optional[str] = None

class PlayerSync(BaseModel):
    name: str
    nickname: Optional[str] = None
    dni: Optional[str] = None
    email: Optional[str] = None
    goals: int = 0
    yellow_cards: int = 0
    red_cards: int = 0
    is_suspended: bool = False
    suspension_reason: Optional[str] = None
    is_admin: bool = False
    auth_id: str

class MatchSync(BaseModel):
    match_date: str  # Formato ISO o similar
    opponent: str
    field: Optional[str] = None
    category: Optional[str] = "Silver"