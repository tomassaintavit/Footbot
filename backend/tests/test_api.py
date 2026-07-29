import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


class MockQuery:
    def __init__(self, data=None):
        self._data = data or []

    def select(self, *args):
        return self

    def order(self, *args, **kwargs):
        return self

    def limit(self, *args):
        return self

    def lt(self, *args):
        return self

    def gte(self, *args):
        return self

    def execute(self):
        result = MagicMock()
        result.data = self._data
        return result


@pytest.fixture
def mock_sb():
    return MagicMock()


@pytest.fixture
def client(mock_sb):
    patchers = [
        patch("routers.public.supabase", mock_sb),
        patch("routers.admin.supabase", mock_sb),
        patch("services.players.supabase", mock_sb),
        patch("services.matches.supabase", mock_sb),
        patch("services.positions.supabase", mock_sb),
    ]
    for p in patchers:
        p.start()

    from routers import admin as admin_router
    from main import app

    admin_override = lambda: {"id": 1, "name": "Admin User", "is_admin": True}
    app.dependency_overrides[admin_router._verify_admin] = admin_override

    yield TestClient(app)

    app.dependency_overrides.clear()
    for p in patchers:
        p.stop()


class TestPublicEndpoints:
    def test_top_scorers(self, client, mock_sb):
        mock_sb.table.return_value = MockQuery([
            {"name": "Juan", "goals": 10},
            {"name": "Pedro", "goals": 7},
            {"name": "Luis", "goals": 5},
        ])
        resp = client.get("/api/public/players/top-scorers")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        assert data[0]["name"] == "Juan"

    def test_top_scorers_empty(self, client, mock_sb):
        mock_sb.table.return_value = MockQuery([])
        resp = client.get("/api/public/players/top-scorers")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_top_yellow(self, client, mock_sb):
        mock_sb.table.return_value = MockQuery([
            {"name": "Pedro", "yellow_cards": 4},
        ])
        resp = client.get("/api/public/players/top-yellow")
        assert resp.status_code == 200
        assert resp.json()[0]["yellow_cards"] == 4

    def test_top_red(self, client, mock_sb):
        mock_sb.table.return_value = MockQuery([
            {"name": "Luis", "red_cards": 2},
        ])
        resp = client.get("/api/public/players/top-red")
        assert resp.status_code == 200
        assert resp.json()[0]["red_cards"] == 2

    def test_last_match_found(self, client, mock_sb):
        mock_sb.table.return_value = MockQuery([
            {"id": 1, "opponent": "Rival FC", "match_date": "2026-01-01T00:00:00"},
        ])
        resp = client.get("/api/public/matches/last")
        assert resp.status_code == 200
        assert resp.json()["opponent"] == "Rival FC"

    def test_last_match_not_found(self, client, mock_sb):
        mock_sb.table.return_value = MockQuery([])
        resp = client.get("/api/public/matches/last")
        assert resp.status_code == 200
        assert resp.json() is None

    def test_upcoming_matches(self, client, mock_sb):
        mock_sb.table.return_value = MockQuery([
            {"id": 2, "opponent": "Next FC"},
        ])
        resp = client.get("/api/public/matches/upcoming")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_positions(self, client, mock_sb):
        mock_sb.table.return_value = MockQuery([
            {"position": 1, "team": "Buen Palo", "points": 30},
        ])
        resp = client.get("/api/public/positions")
        assert resp.status_code == 200
        assert resp.json()[0]["team"] == "Buen Palo"


class TestAdminEndpoints:
    def test_me(self, client):
        resp = client.get("/api/admin/me", headers={"Authorization": "Bearer test"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "Admin User"

    def test_debts(self, client, mock_sb):
        mock_sb.table.return_value = MockQuery([])
        resp = client.get("/api/admin/debts", headers={"Authorization": "Bearer test"})
        assert resp.status_code == 200
        assert resp.json() == []

    def test_debts_summary(self, client, mock_sb):
        mock_sb.table.return_value = MockQuery([])
        resp = client.get("/api/admin/debts/summary", headers={"Authorization": "Bearer test"})
        assert resp.status_code == 200
        data = resp.json()
        assert "total_debt" in data
        assert "total_paid" in data
        assert "total_charged" in data
        assert "by_player" in data
