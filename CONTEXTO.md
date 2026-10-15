# CONTEXTO.MD — Habit Tracker

## 0. Cómo usar este documento
- Resume arquitectura y decisiones YA CERRADAS. No es histórico de pruebas ni de sintaxis literal de código.
- Léelo entero antes de proponer nada. Si falta contexto para actuar, pregunta — no asumas.
- Se complementa con ESTADO.MD (qué está hecho/pendiente ahora mismo, cambia cada sesión). Si ambos discrepan sobre qué está hecho, manda ESTADO.MD.

## 1. Cómo trabajar conmigo

### Proceso
- Revisa este documento antes de preguntar.
- Pide siempre archivos reales antes de asumir patrones de código a partir de prosa — este documento no describe sintaxis, solo decisiones; el código real manda.
- Testeo solo en la review periódica (ver 7), nunca tras cada implementación puntual.
- BBDD parte de 0 en cada testeo salvo indicación contraria.
- Para testear, da las peticiones CURL (evita la interfaz de Swagger).
- Evalúa si lo pedido es asumible o hay mejor opción; avisa si no. Sé crítico, lleva la contraria con razonamiento real — nada de advertencias débiles "por si acaso".
- Señala bugs reales al revisar código pegado, no solo valides.
- Si documento y usuario discrepan sobre qué está hecho/decidido: gana el usuario, pero se contrasta explícitamente citando el documento antes de asumir el cambio. Nunca sobreescribir en silencio. El usuario también puede cometer errores.
- Parafrasea o cita el documento al referenciarlo — evita alucinaciones.

### Estilo de respuesta
- Conciso, sin relleno. Ritmo lento, paso a paso: un concepto, confirmación, siguiente.
- Explica el porqué técnico, no solo código.
- Tono de colega: informal, directo, con sarcasmo/ironía, sin paños calientes.

## 2. Objetivo y entorno

### 2.1 Qué es la app
- Habit tracker personal (single-user) con medallas de 5 tiers (locked→unlocked→bronze→silver→gold→diamond) estilo Pokémon GO: medallas circulares con barra de progreso animada que cambia de color al subir de tier.
- Dos vistas: data entry diario y vista de medallas filtrable (diseño de detalle pendiente hasta hacer el frontend).
- Fase utópica futura: creación de hábitos asistida por IA — no condiciona el desarrollo actual (ver Pendientes P3 en ESTADO.MD).

### 2.2 Entorno técnico
- Windows, Git Bash. Ruta: `c:/Data/1_MisCosas/developer/habit_tracker`
- venv: `.venv` (activar con `source .venv/Scripts/activate`)
- GitHub: https://github.com/rubengil-dev/habit_tracker

### 2.3 Stack y despliegue
- Backend: Python + FastAPI + SQLAlchemy + SQLite (single-user, sin gestión de servidor).
- Frontend: pendiente por completo. A priori vía API REST hecho por Claude, ya que el usuario no sabe frontend. Modificable.
- Deploy futuro (gratis, móvil/laptop): backend en Render/Railway, frontend en Vercel como PWA. Modificable.
- Modelo de datos data-driven, NO hardcodeado por hábito.

## 3. Convenciones de código

### 3.1 Estructura de archivos
- ROOT: `models.py` (SQLAlchemy), `schemas.py` (Pydantic), `enums.py` (Enums, sin dependencias), `requirements.txt`.
- `routers/`: `__init__.py`, habits.py, metrics.py, badges.py, entries.py — CRUD completo por entidad.
- `services/`: `__init__.py` +
  - `utils.py` — funciones ciegas sin conocimiento de dominio: `check_tier`, `get_period`, `get_previous_period`, `get_period_bounds`, `count_entries_by_period`.
  - `badge_progress.py` — dispatcher de recálculo (`calculation_router`) + `recalculate_badges` (usada por entries.py y badges.py) + 4 `calculate_*`.
  - `calc_streaks.py` — lógica de rachas: `get_active_consistency_badge`, `current_badge_progress`, `calculate_habit_streak`.
- Criterio de ubicación: si la función conoce reglas de negocio, va en su archivo de dominio aunque no "calcule" en sentido estricto; si es herramienta ciega reutilizable, va en utils.py.

### 3.2 Decisiones de API (contrato, no sintaxis)
- Listados anidados (`GET /habits/{id}/metrics`, etc.): 404 si el padre no existe; `[]` con 200 si existe pero vacío.
- Creates/updates con FK validan siempre: (1) cada FK existe (404 si no), (2) coherencia entre FKs relacionadas cuando aplica (400 si no cuadra). En updates parciales: `update_data.get("campo", objeto.campo)` antes de validar.
- DELETE con body de respuesta (entries: `badges_update`+`streak_update`) → 200. DELETE sin body (habits, metrics, badges) → 204.
- POST es explícito campo a campo a propósito (legibilidad) — no cambiar sin motivo nuevo. PATCH usa bucle genérico sobre `exclude_unset`.
- Enums: doble capa intencionada (defense in depth) — Pydantic cubre la API, CheckConstraint (autogenerado en models.py desde el propio Enum) cubre cualquier escritura que la salte (ej. futura migración de Notion). models.py sigue en String puro. Valores en minúscula en BBDD, capitalización es cosa del frontend. Al añadir un valor a un Enum, el constraint se regenera solo, pero solo aplica a tabla nueva — recrear si ya existe `habits.db`.
- Cualquier `IntegrityError` (violación de CheckConstraint) se captura de forma global en main.py, no por endpoint.
- El orden "period más corto gana" depende del ORDEN DE DECLARACIÓN de `FrequencyPeriod` en enums.py, no de un valor numérico. No reordenar sin revisar `PERIOD_ORDER` en calc_streaks.py — si se hace mal, el desempate se rompe en silencio.
- Comentarios/formato de código: sigue el patrón de los archivos existentes (bloque corto en inglés antes de cada bloque lógico, cabeceras en MAYÚSCULA, docstring de qué-no-cómo). No lo redescribas de memoria — pide el archivo real.

## 4. Modelo de datos

### 4.1 Entidades
- **Habits**: id, habit (unique), active.
- **Metrics**: id, habit_id (FK CASCADE, indexado), metric, unit, calculated (bool), formula (nullable). CheckConstraint `calculated_requires_formula`.
- **Badges**: id, habit_id (FK CASCADE, denormalizado a propósito, indexado), metric_id (FK CASCADE, indexado), badge, metric_type, unlocked/bronze/silver/gold/diamond (Float), current_value/current_tier (cacheados, fijados solo por el servidor — ver 4.3), frequency_target (Integer, nullable) + frequency_period (String, nullable) — obligatorios juntos si consistency, higher_is_better (Boolean, default=True), threshold_value (Float, nullable) — objective y opcionalmente consistency. CheckConstraints: `tiers_check` (en consistency/objective siempre ascendentes, el value es un conteo, ver 4.3/5.1; en historic/top ascendentes si higher_is_better=true, descendentes si false), `objective_requires_threshold`, `consistency_requires_frequency`, `valid_metric_type`/`valid_current_tier`/`valid_frequency_period`.
- **Entries**: id, habit_id (FK CASCADE, indexado), metric_id (FK CASCADE, indexado), value (Float), date (Date).

### 4.2 Relaciones y cascada
Todas las FKs con `ondelete="CASCADE"`. `database.py` activa `PRAGMA foreign_keys=ON` por conexión (evento "connect", necesario en SQLite) y hace `db.rollback()` en `get_db()` ante cualquier excepción (necesario para que el exception handler de IntegrityError no deje la sesión en estado inconsistente). Borrar Habit arrastra Metrics+Badges+Entries; borrar Metric arrastra sus Entries y Badges; borrar Badge es aislado, sin cascada. Verificado en ejecución sin huérfanos.

### 4.3 Decisiones cerradas (no reabrir sin motivo nuevo)
- Una métrica puede alimentar varias badges — el recálculo busca TODAS las de su metric_id.
- Campos derivados (ritmo, etc.) son una Metric más con `calculated=True`. El motor que ejecute `formula` no existe aún (ver Pendientes P2 en ESTADO.MD).
- current_value/current_tier: recálculo SÍNCRONO en create/update/delete de Entry y en create/update de Badge (esto último recalcula tanto el metric_id viejo como el nuevo si cambió). Nunca cron. Streak igual: nunca se guarda en BBDD, se calcula al vuelo.
- current_value/current_tier fuera de BadgeCreate/BadgeUpdate — los fija el servidor vía `recalculate_badges`, un cliente no puede fijar un tier a mano sin cumplirlo.
- Todo Habit debería tener ≥1 badge consistency (regla de negocio, no CheckConstraint) — ver Pendientes P2 en ESTADO.MD.
- Tiers de consistency/objective siempre ascendentes: en ambos, `value` es un conteo (periodos cumplidos o entries que pasan el threshold), nunca el valor crudo — un conteo más alto siempre es mejor. `higher_is_better` en esos dos tipos solo controla la dirección del filtro contra `threshold_value` (`>=`/`<=`), nunca el orden de los tiers.

## 5. Lógica de negocio

### 5.1 Metric types (los 4)
- **historic**: SUM de todas las entries de la métrica, sin filtro de fecha. Tier según higher_is_better (value es el valor real acumulado).
- **top**: mejor marca de una entry (MAX o MIN según higher_is_better). Tier según higher_is_better (value es el valor real).
- **objective**: cuenta entries que cumplen threshold_value según higher_is_better (`>=`/`<=`). Tier siempre ascendente (value es un conteo).
- **consistency**: ver 5.2. Tier siempre ascendente (mismo motivo que objective).

### 5.2 Consistency
FrequencyPeriod (minúscula en BBDD): daily, weekly, monthly, quarterly, halfyearly, yearly — siempre periodos naturales de calendario (weekly=ISO lun-dom, quarterly=trimestres naturales...), nunca ventana deslizante.

`calculate_consistency`: (1) entries del metric_id, filtradas por threshold_value/higher_is_better si aplica, (2) agrupa por periodo, (3) cuenta entries por periodo — (1)-(3) delegados en `count_entries_by_period` (utils.py), compartida con `calculate_habit_streak` (5.3), (4) value = nº de periodos con count≥target (el periodo actual cuenta en cuanto cumple, aunque no haya cerrado), (5) tier = `check_tier`.

Contrato `services/utils.py`:
- `check_tier(badge, value)`: compara contra los 5 thresholds. Ascendente si higher_is_better=true, o si metric_type es consistency/objective. Descendente solo en historic/top con higher_is_better=false.
- `get_period(entry_date, frequency_period)`: fecha → clave de su periodo natural.
- `get_previous_period(cursor_date, frequency_period)`: fecha dentro del periodo inmediatamente anterior (va al primer día del actual y resta 1 día, nunca resta a lo bruto).
- `get_period_bounds(cursor_date, frequency_period)`: (start, end) del periodo que contiene cursor_date. Usada por `current_badge_progress` para filtrar en SQL en vez de cargar histórico completo a memoria.
- `count_entries_by_period(db, metric_id, frequency_period, threshold_value=None, higher_is_better=True) -> dict`: query filtrada por metric_id (+ threshold si aplica) trayendo solo `Entries.date`, agrupa con `get_period` y devuelve conteo por periodo.

Contrato `badge_progress.py`: `calculation_router(db, badge) -> (value, tier)`, dispatcher por metric_type. Nota de estilo (no bug): `value or 0` en historic/top no distingue None (sin entries) de 0.0 real.

### 5.3 Racha (streak)
Distinta del contador de badge: "cuántos periodos SEGUIDOS cumples, contando hacia atrás desde el actual hasta el primer fallo". No se guarda en BBDD.

Dos usos:
1. **Racha del hábito**: `calculate_habit_streak(habit_id, db) -> int`, usa la badge consistency "activa" (desempate abajo) y `count_entries_by_period`. Enganchada a create/update/delete de entries.
2. **Progreso de badge individual**: `current_badge_progress(badge, db) -> tuple[int,int]` (ej. "3/7"). Filtra en SQL (COUNT + rango vía get_period_bounds), no en memoria. Expuesta en API como `current_progress` en `BadgeResponse`, solo para metric_type consistency (null en el resto); calculada únicamente en get_badge/list_badges/list_badges_related, nunca en create/update (no se cachea, se recalcula al vuelo cada vez).

Fuera de alcance: récord histórico de racha (el más largo, no el actual) — ver Pendientes P2 en ESTADO.MD.

**Desempate de badge activa** (`get_active_consistency_badge`): gana frequency_period MÁS CORTO; en empate, gana frequency_target MÁS ALTO. Sin badges consistency → None.

**Regla del periodo actual en el streak** (distinta de la de consistency en 5.2):
- Periodo actual cumple (aunque no cerrado) → cuenta ya.
- Periodo actual no cumple todavía → ni suma ni rompe, se salta.
- Solo periodos YA CERRADOS que fallan rompen la racha.
- Se descartó (de momento) romper la racha por "imposibilidad matemática de cumplir el periodo actual" — complicación técnica innecesaria, y asumiría máx. 1 entry útil/día.

`streak_update` va DENTRO de la respuesta de POST/PATCH/DELETE de `/entries`, nunca en un GET aparte.

## 6. API — Routers (mapa + decisiones)
- **habits.py**: CRUD + `delete_habit` (204, cascada) + `GET /habits/{id}/badges` (anidado, todas las badges de todos los metrics del habit). `response_model` en los 4 endpoints con salida (`HabitResponse`/`list[...]`), reflejo directo del modelo.
- **metrics.py**: CRUD + `delete_metric` (204, cascada de sus Entries y Badges). `create_metric` acepta `calculated=true` con cualquier `formula` no-null, sin validar contenido (ver Pendientes P2 en ESTADO.MD). `response_model` en los 4 endpoints con salida.
- **badges.py**: CRUD + validación FK/coherencia estándar (3.2). `create_badge`/`update_badge` disparan `recalculate_badges` tras el commit (en update, recalcula metric_id viejo y nuevo si cambió), seguido de un `db.refresh()` adicional — necesario porque `recalculate_badges` hace su propio commit interno que expira el objeto (`expire_on_commit`); sin ese segundo refresh la respuesta salía vacía. Helper local `build_badge_response(badge, db, with_progress)` vive en badges.py, no en utils.py (conoce reglas de negocio) — calcula `current_progress` solo si `with_progress=True` y `metric_type==consistency`; True en gets, False en create/update.
- **entries.py**: CRUD + usa `recalculate_badges` (services/badge_progress.py, compartida con badges.py). Los 3 verbos de escritura devuelven `{entry, badges_update, streak_update}` (DELETE sin "entry"), tipado con `EntryWriteResponse`. Los 3 GET usan `EntryResponse`/`list[...]`.
- **database.py**: engine SQLite + `PRAGMA foreign_keys=ON` + rollback en `get_db()` ante cualquier excepción.
- **main.py**: `create_all` + `include_router` de los 4 + exception handler global `IntegrityError`→400 (rollback real ocurre en `get_db()`, el handler solo formatea). Sin `tags=[...]` → Swagger agrupa todo bajo "default" (cosmético, decidido no arreglar).

## 7. Rutina de cierre (al resetear el chat)
1. Actualizar ESTADO.MD comparándolo con lo hecho en la sesión (este documento, CONTEXTO.MD, solo se toca si cambió arquitectura/decisión). Formato según tamaño de cambio:
   - **Mínimo** (palabra/frase suelta): sección + lugar exacto (texto literal a buscar) + qué añadir/quitar. No reescribir la subsección entera.
   - **Reseñable** (subsección completa o varias líneas relacionadas): reescribir la subsección entera, en su propio bloque de código.
   - **Varios cambios en la sesión**: cada subsección afectada en su propio bloque de código independiente. Nunca mezclar mínimo y reescritura en la misma subsección.
   - **Reestructuración grande** (afecta a la organización del documento): se entrega completo.
   - Es manual de contexto+estado, nunca histórico de pruebas: no se apunta "probamos X, salió bien"; si algo pasa de pendiente a confirmado, se borra el pendiente y se ajusta a "confirmado" (o "implementado sin testear" si no se ha probado en ejecución real).
   - Prioridad 1: no perder información relevante. Prioridad 2 (subordinada): brevedad.
   - Nunca duplicar: un hallazgo se explica una vez, en la sección que toque.
   - Corregir algo ya escrito = sobreescribir esa línea directamente, no acumular versiones.
2. El usuario reenviará el docuemnto actualizado y Claude auditará la primera copia repitiendo estos mismos pasos y respondiendo: (a) qué huecos de código quedan, (b) qué sabe Claude de la sesión que el documento no refleja, (c) qué sobra o falta, (d) si los procedimientos quedan claros, (e) qué podría inventarse una sesión futura por un hueco de información. Todo lo encontrado se corrige antes de la versión final, mismo formato de entrega.
3. Todo lo entregado en 1 y 2 va siempre como bloque(s) de código plano en el chat, nunca como artifact.
4. Tras la versión final, dar un mensaje de COMMIT claro y breve para la sesión para hacer el commit a GitHub.

## 8. Review completa de código (periódica)
- Cada 2-3 resets (según cuánto código se añadió, ver contador en ESTADO.MD): revisión de errores + optimización, ventanas de 2-3 archivos según grafo de dependencias, sobre archivos reales. Único momento de testeo en ejecución completo (excepción de testeo dirigido, ver sección 1).
- Se hace al FINAL de la sesión que toque, obligatoria esa sesión, no se traslada ni se pospone.
- Al completarla: contador vuelve a 0, se anota métrica 1-10 de código añadido desde el último reset.