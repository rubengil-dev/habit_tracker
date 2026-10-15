# ESTADO.MD — Habit Tracker (última actualización: 15 oct 2026)

## PRÓXIMA SESIÓN — empezar por aquí, en este orden
1. **Entrevista de diseño + reescritura de CONTEXTO y ESTADO.** Hace meses que el usuario no toca la app y no recuerda bien qué decidió. Hay que repasar entero qué quiere la app, revisar las decisiones cerradas de CONTEXTO y proponer mejoras (la implementación ya no depende de la capacidad del usuario). Después, rehacer ambos archivos según su definición en `CLAUDE.md`. CONTEXTO cuenta exactamente qué construimos y por qué, y queda estable. ESTADO es una foto del punto actual, sin historial. Dentro de esa reescritura:
   - Pasar el proceso de `CLAUDE.md` a §1/§7/§8; quitar contador de review, bloques para copiar y curls para el usuario.
   - Corregir la ruta de §2.2: ahora es `C:\Data\1_MisCosas\Proyectos\HabitTracker`.
   - §6: `GET /habits/{id}/badges` vive en badges.py, no en habits.py.
   - §5.2: `get_previous_period` weekly sí resta a lo bruto (ver bug 2).
   - §5.2: `value or 0` sí es bug (ver bug 3).
   Temas ya respondidos (15 oct):
   - Varias entries el mismo día cuentan por separado (2 carreras hoy = 2 para un objetivo /semana). Es el comportamiento actual.
   - `Habits.active` sirve para filtrar en el panel visual y mostrar solo los activos sin borrar nada. Hoy no se usa en ningún sitio.
   Temas abiertos para la entrevista:
   - Entries con fecha futura: ¿bloquearlas?
   - Zona horaria de `date.today()` al desplegar en un servidor UTC.
   - Mover una métrica a otro hábito: ¿prohibir o arrastrar sus badges y entries? Ver bug 6.
2. **Entorno.**
   - Recrear `.venv`: está roto desde que se movió la carpeta, y `uvicorn.exe`/`pip.exe`/`activate` apuntan a `developer\habit_tracker`. Mientras tanto, `python -m uvicorn` funciona.
   - Ruta de la BBDD: `sqlite:///habits.db` en database.py es relativa a la carpeta desde la que se arranca, así que arrancar desde otra crea una BBDD vacía sin avisar. Hacerla relativa al proyecto.
3. **Git.**
   - Hay trabajo sin commitear desde el 24 jul (response schemas en los 4 routers + schemas.py). Commitear junto con el arreglo del bug 1.
   - `README.md` aparece como borrado, pero estaba vacío (0 bytes): confirmar el borrado en ese mismo commit.
4. **Corregir todos los "Bugs confirmados" y las "Mejoras menores"** (ver abajo), ya alineados con lo decidido en la entrevista.

## Confirmado funcionando (última verificación: 23 jul 2026)
- Arranque del servidor limpio.
- Los 4 metric_types (historic, top, objective, consistency), con higher_is_better=true y false — ambos casos confirmados en los 4.
- Recálculo síncrono en create/update(incl. cambio de metric_id)/delete de entry, y en create/update de badge, sobre TODAS las badges del metric_id afectado. Aislamiento entre metrics confirmado.
- `tiers_check` protegido en ambas direcciones: rechaza tiers mal ordenados en create y en PATCH.
- Racha del hábito y ambos criterios de desempate (por periodo, por target); racha con hueco rompe correctamente sin mirar más atrás del primer periodo cerrado que falla.
- Cascada de DELETE en 3 niveles (habit→metric→badge/entry), sin huérfanos.
- Errores: 404 en FK inexistente, 400 en descuadre de FK relacionadas o violación de CheckConstraint, 422 en validación Pydantic — todos correctos.
- `recalculate_badges` centralizada (services/badge_progress.py) funcionando desde badges.py y entries.py.
- Refactor de agrupación por periodo (`count_entries_by_period`): mergeado a main (rama `refactor/date-periods` borrada tras el merge).

## Implementado sin testear
- current_value/current_tier fuera de schemas (CONTEXTO.MD §4.3).
- Índices FK (CONTEXTO.MD §4.1).
- CheckConstraints de validez de enum a nivel BBDD: `valid_metric_type`/`valid_current_tier`/`valid_frequency_period`.
- `current_badge_progress` optimizada vía SQL y expuesta en API vía `current_progress`.
- Response schemas (`HabitResponse`, `MetricResponse`, `BadgeResponse`, `EntryResponse`, `EntryWriteResponse`) aplicados como `response_model` en los 4 routers.

## Bugs confirmados
Todos verificados en ejecución el 15 oct 2026.
1. **500 en todo POST/PATCH/DELETE de `/entries` cuya métrica tenga badges.** `EntryWriteResponse.badges_update` está tipado como `list[BadgeResponse]` (schemas.py), pero `recalculate_badges` devuelve dicts `{badge_id, current_value, old_tier, new_tier, tier_changed}`, así que la validación de respuesta falla. Arreglo: un schema propio para ese dict.
2. **`get_period_bounds` weekly devuelve un periodo equivocado.** Para el jueves 15/10 devuelve del 9/10 al 11/10, la cola de la semana anterior. Causa: `get_previous_period` weekly resta 7 días a lo bruto en vez de ir al lunes y restar 1. Rompe `current_progress` de las badges weekly. La racha no se ve afectada.
3. **Badge top/historic con `higher_is_better=false` y sin entries → DIAMOND.** `best or 0` / `total or 0` meten un 0, que en orden descendente es mejor que diamond.
4. **Se acepta `frequency_target` ≤ 0** (no hay validación en Pydantic ni en BBDD). Con 0, `calculate_habit_streak` nunca rompe: recorre periodos hacia atrás hasta `OverflowError` y devuelve 500 en cada entry de ese hábito.
5. **PATCH con `null` explícito en `active`/`calculated`/`higher_is_better`** se guarda porque esas columnas son nullable y un CHECK con NULL pasa en SQLite. Después de eso, los GET devuelven 500 para siempre, porque los Response schemas exigen bool. Ejemplo: `PATCH /habits/1 {"active": null}`.
6. **`PATCH /metrics` acepta `habit_id` sin validarlo.** Si no existe, da 400 genérico por FK en vez de 404 (contrato §3.2). Si existe, las badges y entries de esa métrica se quedan con el `habit_id` antiguo y los datos quedan incoherentes.
7. **`create_habit` ignora `data.active`**: siempre crea el hábito activo.

## Mejoras menores
- `class Config` → `model_config = ConfigDict(from_attributes=True)`. La forma actual está deprecada en Pydantic v2 y saca 4 warnings.
- entries.py: imports sin usar (`Badges`, `calculation_router`).
- models.py: el docstring empieza con 4 comillas.
- `update_entry` que mueve una entry a otro hábito solo devuelve el `streak_update` del hábito nuevo.

## Pendientes

### Prioridad 1 — arreglar
Ninguno actualmente.

### Prioridad 2 — diseñado, falta implementar
1. Confirmación de borrado en frontend (habit con texto exacto, metric con aviso simple, badge sin aviso) — 100% frontend, backend ya soporta la cascada.
2. CORSMiddleware en main.py, cuando exista frontend en otro origen.
3. Blindar "todo Habit debe tener ≥1 badge consistency" en el router.
4. Metrics calculated=true: bloquear POST/PATCH /entries manuales sobre ellas (evita duplicidad futura).
5. Motor de cálculo de métricas derivadas: leer formula, generar/actualizar la entry de la métrica calculada. Incluye validar que formula sea un texto usable (mínimo 2 métricas del mismo habit + un operador +-*/). Depende conceptualmente del punto 4, hacer ambos juntos.
6. Récord histórico de racha (el más largo, no el actual) — no diseñado.

### Prioridad 3 — ideas a futuro
1. Creación de hábitos asistida por IA — utópico, no debe condicionar el desarrollo actual.

## Review periódica
Eliminada (15 oct 2026). La revisión completa del 15 oct cuenta como la última. Desde ahora, al cerrar cada sesión solo se hace un test rápido de lo nuevo (ver CLAUDE.md).