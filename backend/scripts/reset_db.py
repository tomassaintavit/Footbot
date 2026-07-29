import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import supabase

MY_TELEGRAM_ID = "7959667351"
MY_PLAYER_ID = 16

TABLES_TO_CLEAR = ["matches", "positions", "transactions"]

print("=" * 60)
print("\u26a0\ufe0f  RESET DE BASE DE DATOS - Footbot")
print("=" * 60)

my_player = supabase.table("players").select("id,name,dni,telegram_id,is_admin").eq("id", MY_PLAYER_ID).execute()
if not my_player.data:
    print(f"\n\u274c ERROR: No se encontr\u00f3 el jugador con id={MY_PLAYER_ID}")
    print("   Abortando por seguridad.")
    sys.exit(1)

p = my_player.data[0]
print(f"\n\u2705 Tu usuario est\u00e1 intacto:")
print(f"   ID: {p['id']} | {p['name']} | DNI: {p['dni']} | TG: {p['telegram_id']} | Admin: {p['is_admin']}")

for t in TABLES_TO_CLEAR:
    c = supabase.table(t).select("id", count="exact").execute()
    print(f"   {t}: {c.count} registros \u2192 se borrar\u00e1n TODOS")

others = supabase.table("players").select("id", count="exact").neq("id", MY_PLAYER_ID).execute()
print(f"\n   players (otros): {others.count} registros \u2192 se borrar\u00e1n")

print(f"\n{'=' * 60}")
print("\u00bfEst\u00e1s seguro? Escrib\u00ed 'BORRAR' para confirmar:")
confirm = input("> ")

if confirm.strip() != "BORRAR":
    print("\n\u274c Cancelado. No se borr\u00f3 nada.")
    sys.exit(0)

print("\n\U0001f504 Ejecutando...")

for t in TABLES_TO_CLEAR:
    supabase.table(t).delete().not_.is_("id", "null").execute()
    print(f"   \u2705 {t}: 0 registros")

supabase.table("players").delete().neq("id", MY_PLAYER_ID).execute()
print(f"   \u2705 players: solo queda {p['name']} (id={MY_PLAYER_ID})")

print(f"\n{'=' * 60}")
print("\u2705 RESET COMPLETO")
print(f"   Queda tu usuario: {p['name']} (admin=True, telegram_id={p['telegram_id']})")
print("   Ejecut\u00e1 /sincronizar desde el bot para poblar los datos nuevos.")
print(f"{'=' * 60}")
