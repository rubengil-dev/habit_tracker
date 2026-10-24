# Qué hay en este archivo y cómo usarlo
- **Contiene:** cómo está hecho el proyecto: repo, entorno, comandos, estructura, datos y sus limitaciones conocidas. Es un resumen para no tener que buscarlo en el código.
- **No contiene:** el porqué de cada elección ni lo pendiente.
- **Se actualiza:** cuando cambia algo de lo que describe.

## Repo
- GitHub: https://github.com/rubengil-dev/habit_tracker. Rama principal: `main`.
- Ruta local: `C:\Data\1_MisCosas\Proyectos\HabitTracker`. Windows, con Git Bash y PowerShell.
- Ignorados en git: `__pycache*`, `.venv`, `*env`, `*.ipynb` y las bases de datos (`*.db`, `*.sqlite`, `*.sqlite3`), así que `habits.db` no se versiona.

## Entorno
- Entorno virtual en `.venv`, dependencias en `requirements.txt`. Al añadir una librería: instalarla en `.venv` y regenerar con `pip freeze > requirements.txt`.
- Librerías clave: FastAPI, SQLAlchemy 2, Pydantic 2 y Uvicorn.

## Comandos
- Servidor, desde la raíz del proyecto: `python -m uvicorn main:app --reload`. Swagger en `/docs`.
- Pruebas: arrancar el servidor contra una BBDD de prueba y lanzar peticiones con `curl`. Nunca contra `habits.db`. Hoy la BBDD está fija en `database.py` (ver `ESTADO.md`).

## Estructura
Todo en la raíz salvo los dos paquetes:
- `main.py`: crea la app, crea las tablas si no existen, registra los routers y captura globalmente los errores de integridad (→ 400).
- `database.py`: motor SQLite (`habits.db`), activación de claves ajenas en cada conexión y la sesión por petición, con `rollback` ante cualquier excepción.
- `models.py`: tablas SQLAlchemy.
- `schemas.py`: schemas Pydantic de entrada y de respuesta.
- `enums.py`: tipo de medalla, nivel y periodo de frecuencia. Sin dependencias.
- `routers/`: un archivo por entidad (`habits`, `metrics`, `badges`, `entries`) con su CRUD.
- `services/`: lógica de negocio.
  - `utils.py`: herramientas sin conocimiento del dominio.
  - `badge_progress.py`: recálculo de medallas.
  - `calc_streaks.py`: rachas y progreso actual.

## Datos
Cuatro tablas. Todas las claves ajenas tienen `ON DELETE CASCADE` e índice.
- **Habits:** id, nombre (único), activo.
- **Metrics:** id, hábito, nombre, unidad, calculada, fórmula (opcional). Una calculada exige fórmula.
- **Badges:** id, hábito, métrica, nombre, tipo, los cinco umbrales (desbloqueada, bronce, plata, oro, diamante), valor y nivel actual (cacheados), frecuencia objetivo y periodo (opcionales; obligatorios juntos en constancia), mayor es mejor (por defecto verdadero) y valor listón (opcional; obligatorio en objetivo). Restricciones: orden de umbrales, listón en objetivo, frecuencia en constancia, y validez de tipo, nivel y periodo.
- **Entries:** id, hábito, métrica, valor, fecha.

## Endpoints
Cada entidad: `GET` lista, `GET` uno, `POST`, `PATCH` y `DELETE`. Además, los anidados `GET /habits/{id}/metrics`, `/habits/{id}/entries` y `/habits/{id}/badges` (este último vive en `badges.py`).
- `POST/PATCH/DELETE /entries` devuelven el registro, las medallas actualizadas y la racha.
- Las medallas devuelven su progreso actual solo en los GET y solo las de constancia.

## Contratos de las funciones
- `check_tier(badge, value)`: nivel que corresponde a un valor. Ascendente si mayor es mejor o si el tipo es constancia/objetivo; descendente solo en histórica/récord con mayor es mejor falso.
- `get_period(date, period)`: fecha → clave de su periodo natural.
- `get_previous_period(date, period)`: fecha dentro del periodo inmediatamente anterior.
- `get_period_bounds(date, period)`: (inicio, fin) del periodo que contiene la fecha.
- `count_entries_by_period(db, metric_id, period, threshold, higher_is_better)`: registros por periodo, con filtro de listón si lo hay. La usan la medalla de constancia y la racha.
- `calculation_router(db, badge)` → (valor, nivel): reparte según el tipo de medalla a `calculate_historic`, `calculate_top`, `calculate_objective` o `calculate_consistency`.
- `recalculate_badges(db, metric_id)`: recalcula todas las medallas de la métrica y devuelve una lista de cambios. La usan `entries.py` y `badges.py`.
- `get_active_consistency_badge(habit_id, db)`, `calculate_habit_streak(habit_id, db)` → int y `current_badge_progress(badge, db)` → (cumplidos, objetivo).
- `build_badge_response(badge, db, with_progress)`: vive en `badges.py` y arma la respuesta de una medalla.

## Trampas conocidas
- Añadir un valor a un enumerado regenera su restricción, pero solo en tablas nuevas: hay que recrear `habits.db`. No hay migraciones.
- El desempate "periodo más corto" usa el orden de declaración de `FrequencyPeriod` (`PERIOD_ORDER` en `calc_streaks.py`). Reordenar el enumerado rompe el desempate sin avisar.
- `recalculate_badges` hace su propio `commit`, que expira los objetos de la sesión. Por eso `create_badge` y `update_badge` hacen un `refresh` después; sin él, la respuesta sale vacía.
- SQLite exige activar `PRAGMA foreign_keys=ON` en cada conexión, y `get_db` tiene que hacer `rollback` para que el manejador de errores de integridad no deje la sesión inconsistente.
- En SQLite, un CHECK con NULL pasa (origen del bug 5 de `ESTADO.md`).