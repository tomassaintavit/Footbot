MOCK_DB = {}


def seed_default_players():
    MOCK_DB["players"] = [
        {"id": 1, "name": "Juan Perez", "dni": "123", "nickname": "Juanpi", "telegram_id": None, "is_admin": False},
        {"id": 2, "name": "Pedro Gomez", "dni": "456", "nickname": "Pedrito", "telegram_id": None, "is_admin": False},
        {"id": 3, "name": "Admin User", "dni": "789", "nickname": "Admin", "telegram_id": "999", "is_admin": True},
    ]
