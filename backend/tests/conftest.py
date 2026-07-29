import pytest
from unittest.mock import MagicMock, patch
from tests.db import MOCK_DB, seed_default_players


class MockQuery:
    def __init__(self, data=None):
        self._data = data or []

    def select(self, *args):
        return self

    def eq(self, key, value):
        return MockQuery([r for r in self._data if r.get(key) == value])

    def or_(self, *args):
        return self

    def not_(self, *args):
        return self

    def is_(self, *args):
        return self

    def neq(self, key, value):
        return MockQuery([r for r in self._data if r.get(key) != value])

    def order(self, *args, **kwargs):
        return self

    def execute(self):
        result = MagicMock()
        result.data = self._data
        result.count = len(self._data)
        return result


class MockTable:
    def __init__(self, name):
        self.name = name

    def select(self, *args):
        return MockQuery(list(MOCK_DB.get(self.name, [])))

    def insert(self, data):
        if isinstance(data, list):
            for item in data:
                MOCK_DB.setdefault(self.name, []).append(dict(item))
        else:
            MOCK_DB.setdefault(self.name, []).append(dict(data))
        return MockQuery([data])

    def delete(self):
        return MockDeleteQuery(self.name)


class MockDeleteQuery:
    def __init__(self, table_name):
        self.table_name = table_name

    def eq(self, key, value):
        MOCK_DB[self.table_name] = [
            r for r in MOCK_DB.get(self.table_name, []) if r.get(key) != value
        ]
        return MagicMock()

    def not_(self, *args):
        MOCK_DB[self.table_name] = []
        return MagicMock()


@pytest.fixture(autouse=True)
def reset_db():
    MOCK_DB.clear()
    seed_default_players()


@pytest.fixture
def mock_modules():
    with patch("services.debts.supabase") as debts_sb, \
         patch("services.sheets_sync.supabase") as sheets_sb:
        debts_sb.table.side_effect = lambda name: MockTable(name)
        sheets_sb.table.side_effect = lambda name: MockTable(name)
        yield debts_sb, sheets_sb


class MockCell:
    def __init__(self, row_idx=0, col_idx=0, value="", sheet_ref=None):
        self._row_idx = row_idx
        self._col_idx = col_idx
        self._sheet_ref = sheet_ref
        self._value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        self._value = v
        if self._sheet_ref and self._row_idx < len(self._sheet_ref.rows):
            row = self._sheet_ref.rows[self._row_idx]
            if self._col_idx < len(row):
                row[self._col_idx] = str(v)


class MockSheet:
    def __init__(self, rows=None):
        self.rows = rows or [
            ["DNI", "Nombre", "Deuda"],
            ["123", "Juan Perez", "10000"],
            ["456", "Pedro Gomez", "5000"],
        ]

    def get_all_values(self):
        return self.rows

    def range(self, cell_range):
        cells = []
        for i in range(1, len(self.rows)):
            cells.append(MockCell(row_idx=i, col_idx=2, value=self.rows[i][2], sheet_ref=self))
        return cells

    def update_cells(self, cells):
        for c in cells:
            if c._sheet_ref and c._row_idx < len(self.rows):
                while len(self.rows[c._row_idx]) <= c._col_idx:
                    self.rows[c._row_idx].append("")
                self.rows[c._row_idx][c._col_idx] = str(c._value)

    def update_cell(self, row, col, value):
        while len(self.rows) <= row:
            self.rows.append([])
        while len(self.rows[row - 1]) <= col - 1:
            self.rows[row - 1].append("")
        self.rows[row - 1][col - 1] = str(value)


@pytest.fixture
def mock_sheet():
    with patch("services.sheets_sync._get_sheet") as mock:
        sheet = MockSheet()
        mock.return_value = sheet
        yield sheet
