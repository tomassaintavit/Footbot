# 📁 Project Structure

```text
project-root/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   ├── App.jsx
│   │   └── main.jsx
│   └── package.json
│
├── backend/
│   ├── routers/          (Módulos separados para players, matches, chat, etc)
│   ├── models/           (Modelos Pydantic / SQLAlchemy)
│   ├── schemas/          (Estructuras de datos enviadas o recibidas)
│   ├── main.py           (Entrada principal de FastAPI)
│   ├── database.py       (Configuración e instancia de conexión a Supabase)
│   ├── requirements.txt
│   └── .env
│
├── n8n/
│   ├── sync_sheets_debts.json  (Flujo: lee de Google Sheets del Tesorero y envía a Supabase)
│   └── reminders_workflow.json (Opcional: Flujo para envíos programados y recurrentes)
│
├── database/
│   ├── schema.sql
│   └── seed.sql
│
├── docs/
│   ├── architecture.md
│   ├── api.md
│   └── workflows.md
│
├── README.md
├── STEP_BY_STEP.md
└── PROJECT_STRUCTURE.md
```
