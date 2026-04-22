# 🚀 Step-by-Step Guide - Football Team Assistant Chatbot

Este documento te guía paso a paso para construir el proyecto basándonos en la arquitectura híbrida (FastAPI centralizado + n8n para utilidades).

---

## 🥇 Fase 1: Setup inicial

### 1. Crear el proyecto
```bash
mkdir Footbot
cd Footbot
```

### 2. Crear estructura base
```bash
mkdir frontend backend n8n database docs
```

---

## 🥈 Fase 2: Backend (FastAPI)

### 3. Crear entorno virtual
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Mac/Linux
```

### 4. Instalar dependencias
```bash
pip install fastapi uvicorn requests
```

### 5. Crear archivo principal
Crear `main.py`:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "API running"}
```

---

## 🥉 Fase 3: LLM local (Ollama)

### 6. Instalar Ollama
https://ollama.com/

### 7. Ejecutar modelo
```bash
ollama run llama3
```

---

## 🧠 Fase 4: Chat endpoint

### 8. Crear endpoint `/chat`
- Recibir mensaje.
- Enviarlo a Ollama (o LLM preferido) para obtener la intención.
- Si el usuario es administrador, permitir mutaciones. Si no, retornar información solo de lectura.

---

## 🗄️ Fase 5: Base de datos en Supabase

### 9. Esquema inicial de tablas
Crear las siguientes tablas relacionales que centralizan todo el conocimiento del proyecto:
- `players` (poblada desde API Torneo Golden)
- `matches` (poblada desde API Torneo Golden)
- `attendance` 
- `debts` (poblada desde automatización n8n asíncrona)

---

## 🌐 Fase 6: Fuente de Datos del Torneo (API)

### 10. Scraping vs APi Oficial (FastAPI)
- En lugar de raspar web con Node, utilizamos `requests` o `httpx` directamente en los routers (ej. `matches.py` y `players.py` de FastAPI).
- Extraemos jugadores sancionados, estadística y fechas de partidos del API endpoint oculto de **Torneo Golden**.
- Convertimos los resultados en un formato amigable para el modelo de datos e insertamos usando clientes de Supabase.

---

## 🔄 Fase 7: Integración con Tesorería (n8n)

### 11. ¿Por qué n8n?
- El rol n8n será de intermediario **únicamente** para aquellas integraciones de terceros donde no queremos reinventar la rueda por cuenta de tokens Oauth2 engorrosos.

### 12. Flujo Tesorero-Google Sheets
- Un trigger de _"Schedule Timer"_ o un trigger asociado al cambio del Excel dispara la lectura del Google Sheet del Tesorero.
- n8n recupera esas filas y, empleando su Nodo de Postgres/Supabase, envía la transacción `Update/Insert` a la tabla respectiva `debts`.

---

## 📋 Fase 8: Seguridad y Roles (Supabase Auth)

### 13. Endpoints Seguros
- Modificar los esquemas para recibir `auth_id`.
- Crear un decorador o dependencia en FastAPI para verificar si el usuario es `is_admin`.
- Bloquear operaciones como `/upload-attendance` o `/sync` a usuarios no autorizados.

---

## 🧠 Fase 9: Chatbot Inteligente (Intents CRUD)

### 14. Extracción de Intenciones
- Modificar el router `chat.py` para que Ollama devuelva un JSON con la acción deseada (create, read, update, delete).
- Implementar un "Router de Acciones" que ejecute el cambio en Supabase basado en la intención detectada.
- Ejemplo: "Cancela la deuda de Pablo" -> Detectar `Update Debts`.

---

## 🌐 Fase 9: Frontend (React)

### 14. Crear app base
```bash
cd frontend
npm create vite@latest
npm install
```

### 15. Crear chat UI
- Contenedores interactivos estilo ChatGPT.
- Envío y recepción asíncrona.

---

## 🚀 Fase 10: Integración final

### 16. Conexión End-To-End
- Frontend (React) consulta al 👉 Backend (FastAPI).
- El Backend pregunta la intención de frase al 👉 LLM (Ollama).
- LLM traduce "quién nos juega hoy" a un query en formato JSON.
- Backend hace una query SQL de datos frescos de ligas a 👉 BD (Supabase).
- Paralelamente, n8n actualiza silenciosamente los deudores en Supabase en el background, sin tocar al Backend.

---

## 🏁 Siguiente paso
- Desarrollar la lógica en los routers de FastAPI para la API de Torneos.
- Configurar el workflow de lectura de Google Sheets en local de n8n.
