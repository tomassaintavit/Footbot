import pytest
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from telegram import Update
from telegram.ext import ContextTypes


@pytest.fixture
def mock_update():
    update = AsyncMock(spec=Update)
    user = MagicMock()
    user.id = 7959667351
    user.first_name = "Admin"
    update.effective_user = user
    update.message = AsyncMock()
    update.message.reply_text = AsyncMock()
    update.message.text = "/test"
    return update


@pytest.fixture
def mock_context():
    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = []
    context.user_data = {}
    context.bot = AsyncMock()
    return context


class TestBasicCommands:
    @pytest.mark.asyncio
    async def test_start(self, mock_update, mock_context):
        from services.telegram_bot import start
        await start(mock_update, mock_context)
        mock_update.message.reply_text.assert_awaited_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "Buen Palo" in text
        assert "Footbot" in text

    @pytest.mark.asyncio
    async def test_help(self, mock_update, mock_context):
        from services.telegram_bot import help_command
        await help_command(mock_update, mock_context)
        mock_update.message.reply_text.assert_awaited_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "/jugadores" in text
        assert "/pagar_lote" in text


class TestAdminCommands:
    @pytest.mark.asyncio
    async def test_unknown_message(self, mock_update, mock_context):
        from services.telegram_bot import unknown_message
        await unknown_message(mock_update, mock_context)
        mock_update.message.reply_text.assert_awaited_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "/start" in text

    @pytest.mark.asyncio
    async def test_deudas_as_admin(self, mock_update, mock_context):
        with patch("services.telegram_bot.find_player_by_telegram_id") as find_p, \
             patch("services.telegram_bot.debts") as mock_debts:

            find_p.return_value = {"id": 1, "name": "Admin", "is_admin": True}
            mock_debts.get_debts_list.return_value = {
                "success": True,
                "message": "💸 <b>Deudas Pendientes</b>..."
            }

            from services.telegram_bot import deudas_command
            await deudas_command(mock_update, mock_context)
            mock_update.message.reply_text.assert_awaited_once()
            assert "Deudas Pendientes" in mock_update.message.reply_text.call_args[0][0]

    @pytest.mark.asyncio
    async def test_deudas_rejected(self, mock_update, mock_context):
        with patch("services.telegram_bot.find_player_by_telegram_id") as find_p:
            find_p.return_value = {"id": 2, "name": "NotAdmin", "is_admin": False}

            from services.telegram_bot import deudas_command
            await deudas_command(mock_update, mock_context)
            mock_update.message.reply_text.assert_awaited_once()
            text = mock_update.message.reply_text.call_args[0][0]
            assert "Solo administradores" in text

    @pytest.mark.asyncio
    async def test_jugadores(self, mock_update, mock_context):
        with patch("services.telegram_bot.find_player_by_telegram_id") as find_p, \
             patch("services.telegram_bot.players") as mock_players:

            find_p.return_value = {"id": 1, "name": "Admin", "is_admin": True}
            mock_players.get_players_list.return_value = {
                "message": "Lista de jugadores..."
            }

            from services.telegram_bot import jugadores_command
            await jugadores_command(mock_update, mock_context)
            mock_update.message.reply_text.assert_awaited_once()
            assert "Lista de jugadores" in mock_update.message.reply_text.call_args[0][0]

    @pytest.mark.asyncio
    async def test_partidos(self, mock_update, mock_context):
        with patch("services.telegram_bot.find_player_by_telegram_id") as find_p, \
             patch("services.telegram_bot.matches") as mock_matches:

            find_p.return_value = {"id": 1, "name": "Admin", "is_admin": True}
            mock_matches.get_next_matches.return_value = {"message": "Próximos partidos..."}

            from services.telegram_bot import partidos_command
            await partidos_command(mock_update, mock_context)
            mock_update.message.reply_text.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_sincronizar(self, mock_update, mock_context):
        with patch("services.telegram_bot.find_player_by_telegram_id") as find_p, \
             patch("services.telegram_bot.torneo_sync") as mock_sync:

            find_p.return_value = {"id": 1, "name": "Admin", "is_admin": True}
            mock_sync.sync_all.return_value = {"success": True, "message": "Sincronizado"}

            from services.telegram_bot import sincronizar_command
            await sincronizar_command(mock_update, mock_context)
            mock_update.message.reply_text.assert_awaited()
            texts = [c[0][0] for c in mock_update.message.reply_text.call_args_list]
            assert any("Sincronizando" in t for t in texts)

    @pytest.mark.asyncio
    async def test_cancelar(self, mock_update, mock_context):
        from services.telegram_bot import cancelar
        await cancelar(mock_update, mock_context)
        mock_update.message.reply_text.assert_awaited_once()
        text = mock_update.message.reply_text.call_args[0][0]
        assert "Cancelado" in text or "cancelada" in text or "opción" in text or "cancel" in text.lower()
