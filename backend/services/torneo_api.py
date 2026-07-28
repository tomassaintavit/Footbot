import os
import logging
import httpx

logger = logging.getLogger(__name__)

API_BASE = os.getenv("GOLDEN_API_BASE", "https://torneo-golden-backend-production.up.railway.app")
TORNEO_ID = os.getenv("GOLDEN_TORNEO_ID", "6a650df4f46de517ab5b0caa")
EQUIPO_ID = os.getenv("GOLDEN_EQUIPO_ID", "690d4eec95279dd224e528f6")

TIMEOUT = 30.0


def _get(url: str) -> dict:
    with httpx.Client(timeout=TIMEOUT) as client:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.json()


def get_jugadores() -> list[dict]:
    url = f"{API_BASE}/jugadores-equipos/obtener-jugadores-torneo/{EQUIPO_ID}/{TORNEO_ID}"
    data = _get(url)
    return data.get("jugadores", [])


def get_partidos() -> list[dict]:
    url = f"{API_BASE}/partidos/{TORNEO_ID}"
    data = _get(url)
    return data.get("fechas", [])


def get_posiciones() -> list[dict]:
    url = f"{API_BASE}/posiciones/{TORNEO_ID}"
    return _get(url)


def get_torneos_vigentes() -> list[dict]:
    url = f"{API_BASE}/torneos/vigentes"
    data = _get(url)
    return data.get("torneos", [])
