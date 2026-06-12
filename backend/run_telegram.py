#!/usr/bin/env python
"""
Entry point standalone para desarrollo local.
Carga .env e inicia el bot de Telegram.
"""
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

from services.telegram_bot import main

if __name__ == "__main__":
    main()
