# Qué hay en este archivo y cómo usarlo
- **Contiene:** una entrada por sesión, la más reciente arriba: fecha, qué se hizo en pocas líneas y los hashes de commit. El detalle de cada cambio está en git (`git show <hash>`).
- **No contiene:** cifras, decisiones con su porqué ni el estado actual.
- **Se actualiza:** al cerrar cada sesión, después del commit del trabajo.

## 2026-10-24: revisión de los archivos de la entrevista
- Revisados y retocados por mí los archivos de `.claude/` y `.gitignore` (`*.venv` y `*.env` en lugar de `*env`). `CONTEXTO.md`: medallas de racha añadidas a los tipos de medalla, visión futura reordenada por actualizaciones y la nota de la medalla creada sobre un hábito con historial. `PAUTAS.md`: nueva revisión completa del proyecto cada 2 o 3 sesiones. `ESTADO.md` reestructurado.
- Commits: `94af874`. El commit que guarda esta entrada no puede llevar su propio hash: es el último de `git log`.

## 2026-10-21: entrevista de diseño
- Entrevista de diseño completa salvo el bloque 5 (vistas y diseño visual), aplazado al inicio del frontend. Sin cambios de código.
- `CONTEXTO.md`: nuevo porqué del proyecto (registrar tiene que ser gratificante), MVP solo para mí con puerta abierta a más usuarios, modelo por sesiones con etiquetas y calculada de ritmo, medallas colgadas del hábito (con modo evitar y filtro por etiqueta), objetivo y fecha de inicio del hábito, mejor racha, y alcance del MVP.
- `DECISIONES.md`: despliegue en Vercel con Postgres en Neon, login propio, uv, Alembic y pytest, UUID, sesiones, calculadas guardadas, racha a partir del objetivo del hábito, fechas y zona horaria, no mover entre hábitos y borrado de etiquetas. Sustituyen a la fórmula de texto, a la medalla colgada de la métrica y a la regla de "medalla de constancia obligatoria".
- `ESTADO.md`: próxima sesión (entorno, rediseño del backend, entrevista de front), bugs de la v1 mapeados a lo que los resuelve y decisiones abiertas reordenadas. `PAUTAS.md`: en cambios grandes se lista punto a punto qué se borra y qué se crea.
- Commits: `2416be4` (bloques 1 a 3), `178bbfe` (bloque 4), `1be4ac7` (bloques 6 y 7, cierre de la entrevista y push). Los commits posteriores (esta entrada y un retoque de `ESTADO.md`) no pueden llevar su propio hash: son los últimos de `git log`.

## 2026-10-20: archivos de Claude en 8
- `CLAUDE.md`, `CONTEXTO.md` y `ESTADO.md` pasan a 8 archivos dentro de `.claude/` (CLAUDE, PAUTAS, CONTEXTO, ESTADO, ESTILO, TECNICO, DECISIONES, HISTORICO), con la estructura usada en el proyecto del TFM. Quedan huecos marcados para la entrevista de la próxima sesión.
- Comentarios, docstrings e imports de todo el código ajustados a `ESTILO.md`, sin cambios de lógica.
- Los schemas de respuesta, pendientes desde julio, entran en el mismo commit que el código, con el bug 1 aún sin arreglar.
- `README.md`, vacío, borrado.
- Commits: `cf4d93b` (archivos de Claude), `a3fb890` (código), `ad96b45` (histórico y estado). El commit de cierre, que borra el README y guarda esta entrada, no puede llevar su propio hash: es el último de `git log`.

## 2026-10-15: revisión integral y CLAUDE.md
- Revisión completa del código: bugs confirmados en ejecución y mejoras menores, anotados en ESTADO.
- `CLAUDE.md` con la forma de trabajar; `CONTEXTO` y `ESTADO` versionados como `.md`. Review periódica eliminada.
- Commits: `474013c`.

## Antes del 2026-10-15 (reconstruido de git)
- 2026-07-22: `count_entries_by_period` extraída a utilidades; arreglada la respuesta de medalla tras el recálculo; niveles de constancia y objetivo siempre ascendentes. Commit `530f657`.
- 2026-07-21: errores de integridad capturados globalmente, "mayor es mejor" soportado de verdad, recálculo síncrono al crear y modificar medallas, restricciones de enumerados y claves ajenas en la BBDD, índices y reorganización de funciones, progreso actual por SQL. Commit `db36eff`.
- 2026-07-18: rachas, reorganización de carpetas y progreso del periodo actual (`b549645`); comentarios completos, cascada de borrado, comprobaciones en routers y `badge_progress` terminado (`fab340b`); lógica de cálculo casi completa (`e5ba30b`); endpoints terminados y paso a servicios (`3c9127c`).
- 2026-07-16: primer commit y endpoints terminados. Commits `b7cade4`, `6df3300`.
