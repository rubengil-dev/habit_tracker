# Qué hay en este archivo y cómo usarlo
- **Contiene:** cómo está hecho el proyecto: repo, entorno, comandos, estructura, datos y sus limitaciones conocidas. Es un resumen para no tener que buscarlo en el código.
- **No contiene:** el porqué de cada elección ni lo pendiente.
- **Se actualiza:** cuando cambia algo de lo que describe.

## Repo
- GitHub: https://github.com/rubengil-dev/habit_tracker. Rama principal: `main`.
- Ruta local: `C:\Data\1_MisCosas\Proyectos\HabitTracker`. Windows, con Git Bash y PowerShell.
- Ignorados en git: `__pycache*`, `*.venv`, `*.env` (el `.env`, con la dirección y la contraseña de la BBDD), `*.ipynb` y las bases de datos (`*.db`, `*.sqlite`, `*.sqlite3`).

## Entorno
- Python 3.14 y dependencias con uv: `pyproject.toml` (qué hace falta), `uv.lock` (versiones exactas) y `.python-version`. El entorno vive en `.venv` y `uv sync` lo recrea.
- Al añadir una librería: `uv add <librería>`, o `uv add --dev <librería>` si solo sirve para desarrollar.
- Librerías clave: FastAPI, SQLAlchemy 2.1, Pydantic 2, psycopg 3 (driver de Postgres), Alembic, pydantic-settings (lee el `.env`), pwdlib con Argon2 (contraseñas) y tzdata (zonas horarias, que Windows no trae). Solo para desarrollar: pytest, pytest-cov (cobertura), ruff (linter), httpx2 (cliente de pruebas de FastAPI) y uvicorn.
- Ruff, configurado en `pyproject.toml`, solo busca fallos reales (errores, nombres sin definir o sin usar, bugs probables), no estilo: el estilo lo marca `ESTILO.md`.
- Docker Desktop (para un Postgres de usar y tirar): no arranca solo con Windows. En Git Bash, los comandos `docker` con rutas Linux necesitan `MSYS_NO_PATHCONV=1` delante: si no, Git Bash convierte `/var/...` en una ruta de Windows.
- Configuración: la variable `DATABASE_URL`, en el `.env` de la raíz (plantilla sin secretos en `.env.example`). La cadena de Neon se pega tal cual: el código le añade el driver.
- BBDD: Postgres en Neon, región Frankfurt. Ramas: `production` (la app desplegada) y `dev` (desarrollo local). El `.env` apunta a `dev`, sin pooling.

## Comandos
Todos desde la raíz del proyecto:
- Servidor: `uv run uvicorn app.main:app --reload`. API en `http://localhost:8000/api/...`; Swagger en `http://localhost:8000/docs`.
- Tests: `uv run pytest` (con cobertura: `--cov=app`). Para pasarlos contra Postgres, la variable `TEST_DATABASE_URL` con una BBDD de usar y tirar: los tests borran todas sus tablas, y se niegan a arrancar si es la del `.env`.
- Postgres de usar y tirar (con Docker Desktop abierto): `MSYS_NO_PATHCONV=1 docker run -d --rm --name habit-test-pg -e POSTGRES_PASSWORD=test -e POSTGRES_DB=habit_test -p 55432:5432 --tmpfs /var/lib/postgresql/data postgres:17-alpine`, y `TEST_DATABASE_URL=postgresql://postgres:test@localhost:55432/habit_test`. `docker stop habit-test-pg` lo borra.
- Linter: `uv run ruff check app tests scripts migrations`.
- Integración continua: `.github/workflows/tests.yml` pasa en cada push el linter, los tests en SQLite (mínimo 95 % de cobertura de `app/`) y los tests contra un Postgres de GitHub.
- Migraciones: `uv run alembic upgrade head` (aplicar las pendientes), `uv run alembic revision --autogenerate -m "<qué cambia>"` (crear una tras tocar `models.py`; leerla antes de aplicarla), `uv run alembic current` (en cuál está la BBDD) y `uv run alembic check` (si el código y la BBDD coinciden).
- Usuarios: `uv run python -m scripts.create_user <usuario>` crea el usuario o, si existe, le cambia la contraseña (y lo desbloquea y cierra sus sesiones).
- Datos de prueba: `uv run python -m scripts.seed_dev` rehace desde cero el usuario `demo` con 5 hábitos y meses de historial, siempre los mismos. Pide escribir el nombre de la rama de Neon (`dev`) para confirmar y la contraseña del usuario `demo`. No toca a ningún otro usuario.

## Estructura
- `app/`: la API.
  - `main.py`: crea la app, registra los routers bajo `/api` y los manejadores globales de errores (HTTP, integridad y validación), todos con la forma de "Errores".
  - `errors.py`: `ApiError` (error con código) y los códigos de los errores que no lanza la app (framework, validación y reglas de la BBDD).
  - `config.py`: variables de entorno, leídas del `.env` de la raíz la primera vez que se usan.
  - `database.py`: clase base de las tablas (con nombres fijos para las restricciones, que necesita Alembic), motor de Postgres y sesión por petición con `rollback` ante cualquier excepción.
  - `enums.py`, `models.py` (tablas) y `schemas.py` (formatos de entrada y salida de la API, reglas de las medallas y la validación de una edición como elemento completo).
  - `dependencies.py`: lo que comparten los endpoints: el usuario de la cookie (401 si no hay), su "hoy", las filas de la ruta que son suyas (404 si no) y las filas que menciona un cuerpo (404 si no existen, 400 si son de otro hábito).
  - `routers/`: un archivo por entidad (`auth`, `habits`, `metrics`, `tags`, `entries`, `badges`), más `today` (vista del día) y `export`.
  - `services/`: lógica de negocio: `periods` (periodos naturales y el "hoy" del usuario), `tiers` (nivel de un valor, umbrales sugeridos y qué medallas cuentan), `history` (carga las sesiones de un hábito), `ratios`, `streaks` (periodos cumplidos, rachas y objetivo en curso), `badges` (valor, progreso y recálculo), `tags` (borrado) y `auth` (contraseñas, sesiones y bloqueo).
  - `utils/`: herramientas sin reglas de negocio, un archivo por tema: `numbers` (quitar el ruido de los decimales).
- `migrations/`: Alembic. `env.py` conecta con la BBDD del `.env` y compara con `models.py`; `versions/` guarda un archivo por cambio, con fecha y descripción en el nombre; `script.py.mako` es la plantilla de esos archivos.
- `tests/`: pytest. `conftest.py` (BBDD vacía por test, hábito de prueba, clientes de la API con el "hoy" fijo y rutas relativas a `/api`, y la protección contra la BBDD del `.env`), `helpers.py` y un `test_<tema>.py` por servicio, por router, por script y para los errores.
- `scripts/`: `create_user.py` (crear usuarios o cambiar contraseñas) y `seed_dev.py` (usuario `demo` con datos de prueba).
- `.github/workflows/tests.yml`: integración continua.

## Datos
Diez tablas, con UUID. Todas las claves ajenas tienen `ON DELETE CASCADE` e índice. Las principales llevan `created_at`, que ordena los listados (los UUID no tienen orden).
- **users:** usuario (único), huella Argon2 de la contraseña, zona horaria (Europe/Madrid), fallos de login seguidos y bloqueado hasta.
- **auth_sessions:** usuario, huella SHA-256 del token de la cookie y caducidad.
- **habits:** dueño, nombre (único por usuario), activo, fecha de inicio y objetivo: número, periodo y modo (mínimo o máximo). "Al menos 0" no se acepta.
- **metrics:** hábito, nombre (único por hábito), unidad (opcional) y tipo: número, duración (segundos) o ritmo, con sus operandos A y B, distintos.
- **tags:** hábito y nombre (único por hábito).
- **entries** (sesiones): hábito y fecha.
- **entry_values:** sesión, métrica y valor. Una fila por métrica rellenada, ritmos incluidos.
- **entry_tags:** sesión y etiqueta.
- **badges:** hábito, métrica (opcional según el tipo), nombre, tipo, mayor es mejor, listón, periodo, objetivo y modo (constancia y racha), solo sesiones sin etiquetas, los cinco umbrales (desbloqueada a diamante) y el valor y nivel actuales. Restricciones: campos que necesita cada tipo y orden de los umbrales.
- **badge_tags:** medalla, etiqueta y regla (obligatoria o excluida). Una regla por etiqueta y medalla.

## Endpoints
Todos cuelgan de `/api` (se omite abajo). Crear y listar cuelgan del hábito (`/habits/{id}/metrics`, `/tags`, `/entries`, `/badges`); leer, editar y borrar un elemento van directos (`/metrics/{id}`…). Además:
- `POST /auth/login`, `POST /auth/logout`, `GET` y `PATCH /auth/me` (zona horaria).
- `GET /habits/{id}`: el hábito con su racha y su mejor racha.
- `GET /tags/{id}/badges`: las medallas que se borrarían con la etiqueta.
- `GET /habits/{id}/entries?start=&end=`: sesiones de la más nueva a la más antigua, opcionalmente entre dos fechas.
- `POST`, `PATCH` y `DELETE` de sesiones: la sesión (salvo al borrar), las medallas que cambiaron (valor y nivel antes y después) y las rachas.
- `GET /badges`: todas las medallas del usuario. `GET /badges/suggest-tiers?first=&diamond=&whole=`: umbrales sugeridos; con `whole=true`, solo enteros (medallas que cuentan sesiones o periodos). Las medallas de constancia y racha llevan su progreso.
- `GET /today`: hábitos activos con las sesiones de hoy, el objetivo del periodo en curso, las rachas y las medallas que han subido solas.
- `GET /export`: todo lo del usuario en un JSON descargable, con versión de formato.

## Errores
Toda respuesta de error es `{"detail": texto, "code": código}`. El front elige su mensaje por el código; `detail` es para quien lee la API (en la 422, la lista de dónde y por qué). Códigos:
| Código                  | Estado | Cuándo                                                        |
|-------------------------|--------|---------------------------------------------------------------|
| `not_logged_in`         | 401    | Sin sesión o caducada                                         |
| `wrong_credentials`     | 401    | Usuario o contraseña incorrectos                              |
| `login_locked`          | 429    | Bloqueado tras fallos seguidos (con cabecera `Retry-After`)   |
| `not_found`             | 404    | Elemento que no existe o es de otro usuario, o ruta que no existe |
| `method_not_allowed`    | 405    | Método que la ruta no admite                                  |
| `other_habit`           | 400    | Métrica o etiqueta de otro hábito                             |
| `future_date`           | 400    | Sesión o fecha de inicio en el futuro                         |
| `before_start_date`     | 400    | Sesión anterior a la fecha de inicio del hábito               |
| `sessions_before_start` | 400    | Fecha de inicio que dejaría sesiones antes                    |
| `calculated_metric`     | 400    | Valor escrito a mano en un ritmo                              |
| `ratio_of_ratio`        | 400    | Ritmo que usa otro ritmo                                      |
| `duplicate_name`        | 409    | Nombre repetido                                               |
| `integrity_error`       | 400    | Cualquier otra regla de la BBDD (no debería llegar: la API valida antes) |
| `invalid_range`         | 422    | Extremos de los umbrales sugeridos que no sirven              |
| `validation_error`      | 422    | Cuerpo o parámetro que rompe una regla del formato            |
| `http_error`            | otros  | Cualquier otro error del framework                            |

## Contratos de las funciones
- `period_start(day, period)`, `next_period_start(start, period)`, `period_end(day, period)` y `period_starts(first, last, period)`: periodos naturales, identificados por su primer día. `local_today(timezone, now)`: el "hoy" del usuario.
- `tier_for(badge, value)`: nivel de un valor; sin valor, bloqueada. `suggest_tiers(first, diamond, whole=False)`: los cinco umbrales. `is_count(badge)`: si su valor cuenta sesiones o periodos (umbrales enteros).
- `drop_float_noise(value)`: redondea a 12 cifras significativas (0,1 + 0,7 → 0,8). Lo usan la suma de las históricas, los ritmos y los umbrales sugeridos.
- `check_as_whole(schema, row, changes, extra)`: valida una edición parcial como si fuera un elemento nuevo (422 si rompe una regla).
- `seed(db, password, today)`: rehace el usuario `demo` con sus datos de prueba.
- `load_history(db, habit_id)` → lista de `EntryFacts` (fecha, valores por métrica y etiquetas): lo único que leen rachas y medallas.
- `ratio_value(values, metric)`, `refresh_ratios(entry, ratios)` y `backfill_ratio(db, metric)`.
- `period_outcomes(dates, period, target, mode, start, today)` → cumplido, fallado o abierto en cada periodo desde la fecha de inicio; `streaks(outcomes)` → (actual, mejor); `habit_streaks(habit, history, today)` y `goal_so_far(habit, history, today)`.
- `badge_value(badge, history, start, today)`, `badge_progress(...)` y `recalculate_badges(db, habit, today, history=None)` → solo las medallas que cambiaron.
- `login`, `find_session`, `renew_if_due`, `close_session` y `hash_password`.

## Trampas conocidas
- Los enumerados se guardan como texto con un CHECK generado desde el enumerado. Añadir un valor exige escribir la migración a mano: autogenerate no detecta cambios en los CHECK.
- El recálculo de medallas no hace commit: lo hace el endpoint al final, para guardar todo de una vez.
- Un UUID nuevo no existe hasta el `flush`: hay que hacerlo antes de usar el id de una fila recién creada (p. ej. `backfill_ratio`).
- SQLAlchemy cambia un `None` por el valor por defecto de la columna sin avisar; por eso la API rechaza los `null` ya en el schema.
- SQLite (tests) devuelve las fechas con hora sin zona horaria: `UTCDateTime` les vuelve a poner UTC. También necesita `PRAGMA foreign_keys=ON` en cada conexión para borrar en cascada (solo en `conftest.py`).
- Una migración autogenerada copiaría `UTCDateTime`, que solo existe en la app: `render_item` en `env.py` lo cambia por el tipo estándar.
- En `routers/badges.py`, `/badges/suggest-tiers` va antes que `/badges/{badge_id}`: al revés, "suggest-tiers" se leería como un id.
- En los tests, `client` y `anon_client` son el mismo cliente (el primero es el segundo con la cookie puesta): no se pueden usar los dos en un mismo test.
- `seed_dev.py` escribe directamente en la BBDD, sin pasar por la API: `test_seed.py` comprueba que todo lo que crea cumple las reglas de la API.
