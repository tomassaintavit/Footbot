from database import supabase
from datetime import datetime

def create_log(player_id: str, action: str, details: str):
    """
    Registra una acción administrativa en la tabla de audit_logs para auditoría.
    """
    try:
        supabase.table("audit_logs").insert({
            "player_id": player_id,
            "action": action,
            "details": details,
            "created_at": datetime.now().isoformat()
        }).execute()
        return True
    except Exception as e:
        print(f"⚠️ Error al guardar log de auditoría: {str(e)}")
        return False
