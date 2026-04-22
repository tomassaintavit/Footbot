# 🗺️ Roadmap de Footbot: Próximos Pasos

Este documento sirve como guía para las futuras fases de desarrollo tras haber completado la modularización y la extracción de intenciones inteligente.

---

## 🟢 Fase 10: Gestión de Jugadores (CRUD Inteligente)
Ahora que el bot gestiona deudas, el siguiente nivel es la gestión de la "plantilla".
- **Comandos sugeridos:**
    - "Agrega a Juan Pérez como nuevo jugador."
    - "Borra a Pedro de la base de datos."
    - "Suspende a Marcos por mala conducta."
- **Nivel técnico:** Crear un nuevo servicio `backend/services/players.py`.

## 🟡 Fase 11: Interfaz Web (React + Vite)
El backend ya es muy potente; ahora necesitamos que sea fácil de usar.
- **Login:** Usar @supabase/auth-ui-react para que los jugadores se logueen.
- **Chat UI:** Una interfaz limpia (estilo WhatsApp Web) para hablar con el bot.
- **Dashboard Admin:** Una tabla para que el admin vea todas las deudas de un vistazo (opcional).

## 🟡 Fase 12: Refactorización de Asistencia
Mudar la lógica de `attendance.py` al nuevo sistema de servicios.
- **Objetivo:** Que el bot pueda entender cambios sobre la marcha. 
- *Ejemplo:* "Anota a Pablo, pero saca a Juan que se lesionó".

---

## 🛠️ Archivos Clave del Proyecto
- `backend/services/`: El "cerebro" y las "manos" del bot.
- `backend/routers/`: Los "mozos" que reciben los pedidos de la web.
- `database/SUPABASE_ERD.md`: El mapa de tu base de datos.
- `STEP_BY_STEP.md`: El historial de tu progreso.

---
**¿Con cuál fase quieres seguir?**
- Escribe **"Fase 10"** para seguir dándole poder al bot en el backend.
- Escribe **"Fase 11"** para empezar con el diseño y la web.
