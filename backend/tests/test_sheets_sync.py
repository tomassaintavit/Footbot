import pytest
from services import sheets_sync
from tests.db import MOCK_DB


class TestAddMonthlyFee:
    def test_adds_to_all_players(self, mock_modules, mock_sheet):
        result = sheets_sync.add_monthly_fee(5000)
        assert result["success"] is True
        assert result["updated"] == 2

        txs = MOCK_DB.get("transactions", [])
        assert len(txs) == 2
        assert all(t["amount"] == 5000 for t in txs)
        assert all(t["description"] == "Cuota mensual" for t in txs)

        sheet = mock_sheet
        assert "15000" in sheet.rows[1][2]
        assert "10000" in sheet.rows[2][2]

    def test_empty_sheet_returns_error(self, mock_modules, mock_sheet):
        mock_sheet.rows = []
        result = sheets_sync.add_monthly_fee(5000)
        assert result["success"] is False
        assert "Sheet vacío" in result["error"]


class TestReduceDebt:
    def test_reduces_debt(self, mock_modules, mock_sheet):
        result = sheets_sync.reduce_debt("123", 3000)
        assert result["success"] is True
        assert result["previous_debt"] == 10000
        assert result["new_debt"] == 7000

        txs = MOCK_DB.get("transactions", [])
        assert len(txs) == 1
        assert txs[0]["amount"] == -3000
        assert txs[0]["description"] == "Pago"

    def test_cannot_go_below_zero(self, mock_modules, mock_sheet):
        result = sheets_sync.reduce_debt("123", 999999)
        assert result["success"] is True
        assert result["new_debt"] == 0

    def test_dni_not_found(self, mock_modules, mock_sheet):
        result = sheets_sync.reduce_debt("999", 1000)
        assert result["success"] is False
        assert "no encontrado" in result["error"]


class TestSetPlayerDebt:
    def test_sets_exact_amount(self, mock_modules, mock_sheet):
        result = sheets_sync.set_player_debt("123", 8000)
        assert result["success"] is True
        assert result["new_debt"] == 8000

        txs = MOCK_DB.get("transactions", [])
        assert len(txs) == 1
        assert txs[0]["amount"] == -2000

    def test_sets_to_zero(self, mock_modules, mock_sheet):
        result = sheets_sync.set_player_debt("123", 0)
        assert result["success"] is True
        assert result["new_debt"] == 0

        txs = MOCK_DB.get("transactions", [])
        assert len(txs) == 1
        assert txs[0]["amount"] == -10000


class TestAddToPlayerDebt:
    def test_adds_to_existing(self, mock_modules, mock_sheet):
        result = sheets_sync.add_to_player_debt("123", 2000)
        assert result["success"] is True
        assert result["previous_debt"] == 10000
        assert result["new_debt"] == 12000

        txs = MOCK_DB.get("transactions", [])
        assert len(txs) == 1
        assert txs[0]["amount"] == 2000


class TestSyncDebts:
    def test_no_diff(self, mock_modules, mock_sheet):
        MOCK_DB["transactions"] = [
            {"player_id": 1, "amount": 10000},
            {"player_id": 2, "amount": 5000},
        ]
        result = sheets_sync.sync_debts()
        assert result["success"] is True
        assert result["updated"] == 0

    def test_with_diff_creates_adjustment(self, mock_modules, mock_sheet):
        MOCK_DB["transactions"] = [
            {"player_id": 1, "amount": 5000},
        ]
        result = sheets_sync.sync_debts()
        assert result["success"] is True
        assert result["updated"] >= 1

        txs = MOCK_DB.get("transactions", [])
        total = sum(t["amount"] for t in txs)
        assert total == 15000
