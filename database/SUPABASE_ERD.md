# Diagrama de Base de Datos (Supabase)

A continuación, puedes visualizar la estructura de la base de datos que vamos a crear en Supabase, junto con el propósito de cada tabla y la relación entre ellas.

## Entity-Relationship Diagram (ERD)

**Relaciones principales:**
- **PLAYERS** *asiste a* **ATTENDANCE**
- **MATCHES** *recibe* **ATTENDANCE**
- **PLAYERS** *adeuda* **DEBTS**

### Tablas

#### PLAYERS
| Columna | Tipo de dato | Propósito |
| :--- | :--- | :--- |
| `id` | uuid (**PK**) | Generado por defecto |
| `name` | string | Nombre completo |
| `nickname` | string | Apodo/Alias para reconocimiento de mensajes |
| `dni` | string | Documento único para sincronización |
| `email` | string | Correo electrónico |
| `goals` | integer | Goles totales en el torneo |
| `yellow_cards` | integer | Tarjetas amarillas acumuladas |
| `red_cards` | integer | Tarjetas rojas acumuladas |
| `is_suspended` | boolean | Si el jugador está sancionado actualmente |
| `suspension_reason` | string | Motivo de la sanción |
| `created_at` | timestamp | Fecha de registro |
| `auth_id` | uuid | **TODO: Añadir en Supabase.** Link con el `user_id` de Auth |
| `is_admin` | boolean | **TODO: Añadir en Supabase.** Permisos de administrador |

#### MATCHES
| Columna | Tipo de dato | Propósito |
| :--- | :--- | :--- |
| `id` | uuid (**PK**) | Generado por defecto |
| `match_date` | datetime | Fecha y hora del partido |
| `opponent` | string | Nombre del equipo rival |
| `field` | string | Cancha/Predio donde se juega |
| `category` | string | Categoría del torneo (Ej: Silver) |
| `created_at` | timestamp | Fecha de creación |

#### ATTENDANCE
| Columna | Tipo de dato | Propósito |
| :--- | :--- | :--- |
| `id` | uuid (**PK**) | Generado por defecto |
| `match_id` | uuid (**FK**) | Relación con MATCHES |
| `player_id` | uuid (**FK**) | Relación con PLAYERS |
| `status` | string | Ej: confirmado, baja, duda |
| `created_at` | timestamp | Fecha de confirmación |

#### DEBTS
| Columna | Tipo de dato | Propósito |
| :--- | :--- | :--- |
| `id` | uuid (**PK**) | Generado por defecto |
| `player_id` | uuid (**FK**) | Relación con PLAYERS |
| `amount` | numeric | Monto de la deuda (Ej: 1500) |
| `is_paid` | boolean | Por defecto 'false' |
| `created_at` | timestamp | Fecha de registro de la deuda |

## Explicación de las Relaciones

- `players` y `matches` son las tablas principales. Existen de forma independiente.
- `attendance` es una tabla intermedia (*Many-to-Many*). Un jugador (`player_id`) puede asistir a muchos partidos, y un partido (`match_id`) tiene muchos asistentes.
- `debts` es una relación de Uno a Muchos (*One-to-Many*). Un solo jugador (`player_id`) puede deber por diferentes razones (una deuda por la cancha, otra por las bebidas del tercer tiempo), pero cada deuda pertenece siempre a un único jugador.

> [!TIP]
> **En Supabase:** Al crear las columnas `match_id` y `player_id` en la sección "Table Editor", busca el botón que parece un "clip o eslabón de cadena" (Foreign Key). Esto te permitirá enlazar visualmente esas columnas con la columna `id` de las tablas correspondientes, obligando a que no haya asistencias de jugadores que no existen.
