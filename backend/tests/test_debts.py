import pytest
from services import debts
from tests.db import MOCK_DB


class TestGetDebtsList:
    def test_empty(self, mock_modules):
        result = debts.get_debts_list()
        assert result["success"] is True
        assert "No hay deudas" in result["message"]

    def test_with_debts(self, mock_modules):
        MOCK_DB["transactions"] = [
            {"player_id": 1, "amount": 10000},
            {"player_id": 2, "amount": 5000},
        ]
        result = debts.get_debts_list()
        assert result["success"] is True
        assert "10,000" in result["message"]
        assert "5,000" in result["message"]
        assert "15,000" in result["message"]

    def test_ignores_zero_balance(self, mock_modules):
        MOCK_DB["transactions"] = [
            {"player_id": 1, "amount": 10000},
            {"player_id": 1, "amount": -10000},
        ]
        result = debts.get_debts_list()
        assert result["success"] is True
        assert "No hay deudas" in result["message"]


class TestCreateDebtByPlayerName:
    def test_with_dni(self, mock_modules, mock_sheet):
        result = debts.create_debt_by_player_name("Juan Perez", 3000)
        assert result["success"] is True

        txs = MOCK_DB.get("transactions", [])
        assert len(txs) == 1
        assert txs[0]["player_id"] == 1
        assert txs[0]["amount"] == 3000

    def test_no_dni_inserts_directly(self, mock_modules):
        MOCK_DB.clear()
        MOCK_DB["players"] = [{"id": 5, "name": "New Player", "dni": None}]
        result = debts.create_debt_by_player_name("New Player", 5000)
        assert result["success"] is True

        txs = MOCK_DB.get("transactions", [])
        assert len(txs) == 1
        assert txs[0]["player_id"] == 5
        assert txs[0]["amount"] == 5000


class TestDeleteDebtByPlayerName:
    def test_with_balance(self, mock_modules):
        MOCK_DB["transactions"] = [
            {"player_id": 1, "amount": 10000},
        ]
        result = debts.delete_debt_by_player_name("Juan Perez")
        assert result["success"] is True

        txs = MOCK_DB.get("transactions", [])
        balances = sum(t["amount"] for t in txs)
        assert balances == 0

    def test_zero_balance(self, mock_modules):
        result = debts.delete_debt_by_player_name("Juan Perez")
        assert result["success"] is True
        assert "no tiene deudas" in result["message"]
