# Qué hay en este archivo y cómo usarlo
- **Contiene:** una entrada por sesión, la más reciente arriba: fecha, qué se hizo en pocas líneas y los hashes de commit. El detalle de cada cambio está en git (`git show <hash>`).
- **No contiene:** cifras, decisiones con su porqué ni el estado actual.
- **Se actualiza:** al cerrar cada sesión, después del commit del trabajo.

## 2026-10-20: archivos de Claude en 8
- `CLAUDE.md`, `CONTEXTO.md` y `ESTADO.md` pasan a 8 archivos dentro de `.claude/` (CLAUDE, PAUTAS, CONTEXTO, ESTADO, ESTILO, TECNICO, DECISIONES, HISTORICO), con la estructura usada en el proyecto del TFM. Quedan huecos marcados para la entrevista de la próxima sesión.
- Comentarios, docstrings e imports de todo el código ajustados a `ESTILO.md`, sin cambios de lógica.
- Commits: pendiente.

## 2026-10-15: revisión integral y CLAUDE.md
- Revisión completa del código: bugs confirmados en ejecución y mejoras menores, anotados en ESTADO.
- `CLAUDE.md` con la forma de trabajar; `CONTEXTO` y `ESTADO` versionados como `.md`. Review periódica eliminada.
- Commits: `474013c`.

## Antes del 2026-10-15 (reconstruido de git)
- 2026-07-22: `count_entries_by_period` extraída a utilidades; arreglada la respuesta de medalla tras el recálculo; niveles de constancia y objetivo siempre ascendentes. Commit `530f657`.
- 2026-07-21: errores de integridad capturados globalmente, "mayor es mejor" soportado de verdad, recálculo síncrono al crear y modificar medallas, restricciones de enumerados y claves ajenas en la BBDD, índices y reorganización de funciones, progreso actual por SQL. Commit `db36eff`.
- 2026-07-18: rachas, reorganización de carpetas y progreso del periodo actual (`b549645`); comentarios completos, cascada de borrado, comprobaciones en routers y `badge_progress` terminado (`fab340b`); lógica de cálculo casi completa (`e5ba30b`); endpoints terminados y paso a servicios (`3c9127c`).
- 2026-07-16: primer commit y endpoints terminados. Commits `b7cade4`, `6df3300`.
