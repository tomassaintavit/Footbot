import logging
from datetime import datetime, timedelta, timezone
from dateutil import parser
from telegram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from database import supabase

logger = logging.getLogger(__name__)

ADMIN_TELEGRAM_ID = "7959667351"

_scheduler: AsyncIOScheduler | None = None


def get_saturday_match():
    now = datetime.now(timezone.utc)
    result = (
        supabase.table("matches")
        .select("*")
        .gte("match_date", now.isoformat())
        .order("match_date")
        .limit(1)
        .execute()
    )
    if not result.data:
        return None

    match = result.data[0]
    try:
        md = parser.parse(match["match_date"])
    except Exception:
        return None

    art = timezone(timedelta(hours=-3))
    md_local = md.astimezone(art) if md.tzinfo else md.replace(tzinfo=art)

    # if md_local.weekday() != 5:
    #     return None

    return md_local, match


def build_message(md_local, match) -> str:
    opponent = match.get("opponent", "?")
    match_time = md_local.strftime("%H:%M")
    field = match.get("field", "")
    field_text = f" en {field}" if field else ""

    txs = supabase.table("transactions").select("amount, player_id, players!inner(name)").execute()
    balances: dict[int, float] = {}
    names: dict[int, str] = {}
    for t in txs.data:
        pid = t["player_id"]
        balances[pid] = balances.get(pid, 0) + t["amount"]
        names[pid] = t["players"]["name"]

    debtors = [names[pid] for pid, bal in balances.items() if bal > 0]

    lines = [
        "📅 <b>Recordatorio semanal</b>\n",
        f"⚽ <b>Mañana</b> vs {opponent} — {match_time}hs{field_text}",
    ]

    if debtors:
        lines.append(f"\n💰 <b>{len(debtors)} jugadores con deuda:</b>")
        lines.append(", ".join(debtors[:10]))
        if len(debtors) > 10:
            lines.append(f" y {len(debtors) - 10} más")
    else:
        lines.append("\n💰 Sin deudas pendientes ✅")

    return "\n".join(lines)


async def weekly_reminder_job(bot: Bot):
    result = get_saturday_match()
    if not result is None:
        md_local, match = result
        msg = build_message(md_local, match)
        await bot.send_message(chat_id=ADMIN_TELEGRAM_ID, text=msg, parse_mode="HTML")


def start_scheduler(bot: Bot):
    global _scheduler
    if _scheduler is not None:
        return

    _scheduler = AsyncIOScheduler(timezone="America/Argentina/Buenos_Aires")
    trigger = CronTrigger(day_of_week="wed", hour=18, minute=0)
    _scheduler.add_job(weekly_reminder_job, trigger, args=[bot])
    _scheduler.start()
    logger.info("Scheduler iniciado — recordatorio prueba mié 18:00 ART")


def stop_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Scheduler detenido")
