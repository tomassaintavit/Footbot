# Diagrama de Base de Datos (Supabase)

**Relaciones principales:**
- **PLAYERS** *asiste a* **ATTENDANCE**
- **MATCHES** *recibe* **ATTENDANCE**
- **PLAYERS** *tiene* **TRANSACTIONS** (cargos y pagos)
- **PLAYERS** *registra* **LOGS** (bitácora de acciones admin)

### Tablas

#### PLAYERS
| Columna | Tipo | Propósito |
| :--- | :--- | :--- |
| `id` | **bigint (PK)** | Generado por defecto |
| `name` | text | Nombre completo |
| `nickname` | text | Apodo |
| `dni` | text | Documento para vincular con Google Sheet |
| `email` | text | Correo electrónico |
| `goals` | integer | Goles totales en el torneo |
| `yellow_cards` | integer | Tarjetas amarillas acumuladas |
| `red_cards` | integer | Tarjetas rojas acumuladas |
| `is_suspended` | boolean | Si está sancionado |
| `suspension_reason` | text | Motivo de la sanción |
| `telegram_id` | text | ID de Telegram para comandos del bot |
| `auth_id` | uuid | ID de Supabase Auth para login web |
| `is_admin` | boolean | Permisos de administrador |
| `created_at` | timestamptz | Fecha de registro |

#### MATCHES
| Columna | Tipo | Propósito |
| :--- | :--- | :--- |
| `id` | **bigint (PK)** | Generado por defecto |
| `match_date` | timestamptz | Fecha y hora del partido |
| `opponent` | text | Equipo rival |
| `field` | text | Cancha |
| `category` | text | Categoría del torneo (Silver) |
| `created_at` | timestamptz | Fecha de creación |

#### ATTENDANCE
| Columna | Tipo | Propósito |
| :--- | :--- | :--- |
| `id` | **bigint (PK)** | Generado por defecto |
| `match_id` | **bigint (FK → matches)** | Partido |
| `player_id` | **bigint (FK → players)** | Jugador |
| `status` | text | confirmado, baja, duda |
| `created_at` | timestamptz | Fecha de confirmación |

#### TRANSACTIONS (ledger contable)
| Columna | Tipo | Propósito |
| :--- | :--- | :--- |
| `id` | **uuid (PK)** | Generado por defecto |
| `player_id` | **bigint (FK → players)** | Jugador |
| `amount` | numeric | **Positivo** = cargo (cuota, deuda). **Negativo** = pago |
| `description` | text | "Cuota mensual", "Pago", "Ajuste por conciliación", etc. |
| `year` | integer | Año (para agrupar históricamente) |
| `month` | integer | Mes |
| `created_at` | timestamptz | Fecha del movimiento |

> El saldo actual de un jugador se calcula como `SUM(amount)`. Si da positivo, debe; si da negativo o cero, está al día.

#### LOGS
| Columna | Tipo | Propósito |
| :--- | :--- | :--- |
| `id` | **bigint (PK)** | Generado por defecto |
| `player_id` | **bigint (FK → players)** | Admin que realizó la acción |
| `action` | text | Nombre de la acción (add_debt, payment, etc.) |
| `details` | text | Descripción legible de la operación |
| `created_at` | timestamptz | Fecha del registro |

#### POSITIONS
| Columna | Tipo | Propósito |
| :--- | :--- | :--- |
| `id` | **bigint (PK)** | Generado por defecto |
| `position` | integer | Puesto en la tabla |
| `team` | text | Nombre del equipo |
| `played` | integer | Partidos jugados |
| `won` | integer | Ganados |
| `drawn` | integer | Empatados |
| `lost` | integer | Perdidos |
| `goals_for` | integer | Goles a favor |
| `goals_against` | integer | Goles en contra |
| `points` | integer | Puntos |
| `created_at` | timestamptz | Fecha de sincronización |

## Relaciones

- `players` y `matches` son tablas principales independientes.
- `attendance` es **Muchos a Muchos** entre players y matches.
- `transactions` es **Uno a Muchos**: un jugador tiene muchos movimientos financieros.
- `logs` es **Uno a Muchos**: un admin genera muchos registros de auditoría.
- `positions` es independiente (datos del torneo, se reemplaza en cada sincronización).
