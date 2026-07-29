# ⚽ Footbot

Bot de Telegram + Web App para administrar Buen Palo Fútbol Club. Manejo de jugadores, deudas, pagos, partidos, asistencia y posiciones sincronizados con Torneo Golden y Google Sheets.

---

## Stack

| Capa | Tecnología |
|------|-----------|
| **Bot** | python-telegram-bot |
| **Backend** | FastAPI (Python) |
| **Frontend** | React 19 + Vite 8 + Tailwind CSS |
| **DB** | Supabase (PostgreSQL) |
| **Sincronización Golden** | httpx |
| **Sincronización Sheets** | gspread + google-auth |
| **Gráficos** | Recharts |
| **NLP** | Ollama (llama3) — *inactivo* |

---

## Arquitectura

```
Torneo Golden API ─────┐
                        v
Google Sheets ─────────> Backend (FastAPI + Bot Telegram) ───> DB (Supabase) ───> Frontend (React)
                        ^
                        |
                   Telegram (usuario/admin)
```

- El Sheet de Google es la fuente de verdad para deudas. Cada operación de pago/cuota escribe al Sheet y luego sincroniza a Supabase.
- Las operaciones de agenda (jugadores, partidos, posiciones) se sincronizan desde Torneo Golden.
- El frontend tiene tres vistas: **pública** (estadísticas del equipo), **login** (email/contraseña Supabase), **admin** (dashboard económico).

---

## Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Variables de entorno (`.env`)

```env
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu-service-key

TELEGRAM_BOT_TOKEN=token-de-botfather

GOLDEN_API_BASE=https://torneo-golden-backend-production.up.railway.app
GOLDEN_TORNEO_ID=id-del-torneo
GOLDEN_EQUIPO_ID=id-de-buen-palo

GOOGLE_SHEETS_CREDS_PATH=google-creds.json
GOOGLE_SHEET_ID=id-del-sheet

OLLAMA_URL=http://localhost:11434
```

### Frontend

```bash
cd frontend
npm install
```

Variables (`frontend/.env.local`):

```env
VITE_SUPABASE_URL=https://tu-proyecto.supabase.co
VITE_SUPABASE_ANON_KEY=tu-anon-key
```

---

## Ejecutar

```bash
# Backend + bot (dev)
cd backend && uvicorn main:app --reload

# Solo bot (standalone)
cd backend && python run_telegram.py

# Frontend (dev, con proxy a backend)
cd frontend && npm run dev
```

El frontend en dev escucha en `:5173` y redirige `/api/*` a `localhost:8000`.

---

## Bot — Comandos

### Información (admin)

| Comando | Descripción |
|---------|------------|
| `/jugadores` | Lista de jugadores |
| `/deudas` | Deudas pendientes |
| `/partidos` | Próximos partidos |
| `/asistencia` | Confirmados al próximo partido |
| `/posiciones` | Tabla de posiciones |

### Administración (admin)

| Comando | Descripción |
|---------|------------|
| `/sincronizar` | Sincroniza jugadores, posiciones y partidos desde Torneo Golden |
| `/sincronizar_deudas` | Sincroniza deudas desde Google Sheets |
| `/nuevo_jugador` | Agrega un jugador (conversación) |
| `/borrar_jugador` | Elimina un jugador (conversación con desambiguación) |
| `/actualizar_jugador` | Modifica datos de un jugador (conversación) |
| `/nueva_deuda` | Carga una deuda a un jugador (conversación) |
| `/borrar_deuda` | Elimina deudas de un jugador (conversación) |
| `/agregar_deuda_mes` | Suma cuota mensual a todos los jugadores (conversación) |
| `/pagar` | Registrar pago de un jugador (conversación con selección) |
| `/pagar_lote MONTO` | Pagos múltiples por selección numérica (grilla 2 columnas) |

### Vinculación

| Comando | Descripción |
|---------|------------|
| `/link` | Vincula un jugador a un ID de Telegram |

### Generales

| Comando | Descripción |
|---------|------------|
| `/start` | Bienvenida |
| `/help` | Lista de comandos |
| `/cancelar` | Cancela cualquier conversación activa |

---

## Frontend — Vistas

### Pública (`/`)

Landing page con:
- Escudo de Buen Palo (SVG, dorado #C6970C sobre fondo oscuro)
- Top 3 goleadores, tarjetas amarillas y rojas
- Último partido (resultado)
- Próximos 3 partidos (fecha, hora, rival)
- Tabla de posiciones (con scroll horizontal en mobile)

### Login

- Formulario email/contraseña contra Supabase
- Verifica que el usuario tenga `is_admin = true` en la tabla `players`
- Redirige al dashboard o muestra error

### Admin Dashboard

- Resumen de deuda total
- Gráfico de torta (rojo = impago, blanco = pagado)
- Barras horizontales por jugador
- Tabla de jugadores con indicador verde/rojo de estado de pago

---

## API — Endpoints públicos

| Ruta | Descripción |
|------|------------|
| `GET /api/public/players/top-scorers` | Top 3 goleadores |
| `GET /api/public/players/top-yellow` | Top 3 amarillas |
| `GET /api/public/players/top-red` | Top 3 rojas |
| `GET /api/public/matches/last` | Último partido |
| `GET /api/public/matches/upcoming` | Próximos 3 partidos |
| `GET /api/public/positions` | Tabla de posiciones |

## API — Endpoints admin (requieren JWT + is_admin)

| Ruta | Descripción |
|------|------------|
| `GET /api/admin/me` | Perfil del admin autenticado |
| `GET /api/admin/debts` | Deudas impagas |
| `GET /api/admin/debts/summary` | Resumen agregado (total + por jugador) |

---

## Base de datos

Tablas principales en Supabase:

- `players` — Jugadores (con `is_admin`, `telegram_id`, `auth_id`, `dni`)
- `matches` — Partidos del fixture
- `attendance` — Asistencia
- `debts` — Deudas
- `positions` — Posiciones del torneo
- `logs` — Bitácora de acciones admin

---

## Notas

- Los comandos de administración verifican `is_admin` antes de ejecutarse.
- El NLP con Ollama está implementado en `services/intelligence.py` pero actualmente no se usa en el flujo del bot (todo es por comandos directos).
- `is_admin`, `telegram_id` y `auth_id` nunca se sobrescriben en las sincronizaciones desde Torneo Golden.
