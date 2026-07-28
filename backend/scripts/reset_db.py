import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import supabase

MY_TELEGRAM_ID = "7959667351"
MY_PLAYER_ID = 16

TABLES_TO_CLEAR = ["matches", "positions", "debts"]

print("=" * 60)
print("⚠️  RESET DE BASE DE DATOS - Footbot")
print("=" * 60)

my_player = supabase.table("players").select("id,name,dni,telegram_id,is_admin").eq("id", MY_PLAYER_ID).execute()
if not my_player.data:
    print(f"\n❌ ERROR: No se encontró el jugador con id={MY_PLAYER_ID}")
    print("   Abortando por seguridad.")
    sys.exit(1)

p = my_player.data[0]
print(f"\n✅ Tu usuario está intacto:")
print(f"   ID: {p['id']} | {p['name']} | DNI: {p['dni']} | TG: {p['telegram_id']} | Admin: {p['is_admin']}")

for t in TABLES_TO_CLEAR:
    c = supabase.table(t).select("id", count="exact").execute()
    print(f"   {t}: {c.count} registros → se borrarán TODOS")

others = supabase.table("players").select("id", count="exact").neq("id", MY_PLAYER_ID).execute()
print(f"\n   players (otros): {others.count} registros → se borrarán")

print(f"\n{'=' * 60}")
print("¿Estás seguro? Escribí 'BORRAR' para confirmar:")
confirm = input("> ")

if confirm.strip() != "BORRAR":
    print("\n❌ Cancelado. No se borró nada.")
    sys.exit(0)

print("\n🔄 Ejecutando...")

for t in TABLES_TO_CLEAR:
    supabase.table(t).delete().not_.is_("id", "null").execute()
    print(f"   ✅ {t}: 0 registros")

supabase.table("players").delete().neq("id", MY_PLAYER_ID).execute()
print(f"   ✅ players: solo queda {p['name']} (id={MY_PLAYER_ID})")

print(f"\n{'=' * 60}")
print("✅ RESET COMPLETO")
print(f"   Queda tu usuario: {p['name']} (admin=True, telegram_id={p['telegram_id']})")
print("   Ejecutá /sincronizar desde el bot para poblar los datos nuevos.")
print(f"{'=' * 60}")
