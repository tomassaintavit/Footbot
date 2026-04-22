# ⚽ Football Team Assistant Chatbot

Chatbot inteligente para gestionar un equipo de fútbol. Permite registrar asistencia, consultar jugadores, deudas y obtener información de partidos coordinando múltiples orígenes de datos.

---

## 🚀 Features

- 💬 **Chatbot Autonómo:** Interfaz principal basada en chat.
- 🧠 **IA Local (Ollama):** Interpretación de lenguaje normal e intenciones de usuario.
- 📋 **Asistencia:** Toma de asistencia y disponibilidad mediante texto.
- 🧮 **Sincronización de Pagos:** Integración con Google Sheets del Tesorero usando **n8n** para volcar datos a DB automáticamente.
- ⚽ **Torneo Golden API:** Conexión directa en FastAPI para extraer fechas, fixture y estadísticas de jugadores.
- 🔐 **Acceso Seguro:** Sistema de login integrado mediante **Supabase Auth**.
- 🛡️ **Modo Admin:** Permisos exclusivos basados en el usuario logueado para realizar acciones críticas (ej. forzar un pago, modificar asistencias).
- 💬 **Chatbot Web:** Interfaz de chat moderna construida en **React**.

---

## 🏗️ Arquitectura

La arquitectura híbrida facilita la labor de todos los miembros del equipo. El backend de Python (FastAPI) asume la lógica del negocio principal y usa n8n estrictamente para integraciones de terceros (como que el Tesorero pueda seguir usando exclusivamente sus hojas de cálculo de Google).

```text
                               API Torneo Golden (Jugadores/Fechas)
                                      ^
                                      |
Frontend (React) <──> Backend (FastAPI) <──> LLM (Ollama)
                            |         ^
                            v         |
                      DB (Supabase)   |
                            ^         |
                            |         | (Actualiza Deudas usando API standard)
                       n8n ---------/                   
                            ^
                            | (Lectura de pagos y finanzas)
                      Google Sheets (Manejado por el Tesorero)
```

---

## 🧰 Tech Stack

- **Frontend:** React + Vite (Desplegado en Vercel).
- **Backend:** FastAPI (Python).
- **Autenticación y DB:** Supabase (Auth + PostgreSQL).
- **Integraciones:** n8n (flujo: Google Sheets -> Supabase).
- **IA:** Ollama (Llama 3 / Mistral) en entorno local.

---

## ⚙️ Setup

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # o `venv\Scripts\activate` en Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

### LLM
```bash
ollama run llama3
```

### n8n
```bash
npm install n8n -g
n8n
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 🧠 Uso

Ejemplos:
- “Me anoto para el sábado” (Usuario normal, comando de lectura/auto-agregar)
- “¿Cuántos somos?” (Usuario normal, comando de lectura)
- “¿Cuánto debo del mes?” (Usuario normal, consulta a BD poblada por n8n)
- "Anotar a Tomás para el sábado" o "Crear un nuevo evento" (**ADMIN ONLY**)
- "Actualizar la tabla de posciones" (**ADMIN ONLY**, dispara sincronización con Torneo Golden)

---

## 📊 Base de datos

Principales entidades en formato relacional (Supabase):
- `players`
- `matches`
- `attendance`
- `debts`
