# 📁 Project Structure

```text
project-root/
│
├── .agents/              (Configuraciones y skills de IA)
├── frontend/
│   ├── src/
│   │   ├── assets/       (Imágenes, fuentes, etc.)
│   │   ├── components/   (Componentes reutilizables)
│   │   ├── pages/        (Vistas principales de la app)
│   │   ├── services/     (Lógica de comunicación con el backend)
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
│
├── backend/
│   ├── routers/          (Endpoints de FastAPI: players, matches, chat, etc.)
│   ├── services/         (Lógica de negocio modularizada: Intelligence, Attendance, etc.)
│   ├── database.py       (Conexión a Supabase)
│   ├── main.py           (Entrada principal)
│   ├── schemas.py        (Modelos Pydantic para validación)
│   ├── .env.example      (Plantilla de variables de entorno)
│   └── requirements.txt
│
├── n8n/
│   └── asistencia_workflow.json (Flujo de automatización para asistencias)
│
├── database/
│   └── SUPABASE_ERD.md   (Documentación del esquema de base de datos)
│
├── docs/                 (Documentación adicional del proyecto)
│
├── README.md
├── PROJECT_STRUCTURE.md
└── skills-lock.json      (Versiones de los skills instalados)
```

