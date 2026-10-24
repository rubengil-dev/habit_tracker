# Qué hay en este archivo y cómo usarlo
- **Contiene:** qué hacer al abrir un chat, el índice de archivos de `.claude/` y las reglas para mantenerlos.
- **No contiene:** nada del proyecto ni de cómo trabajar conmigo.
- **Se actualiza:** cuando se añade, se quita o se redefine un archivo de `.claude/`.

## Al abrir un chat
1. Lee enteros @PAUTAS.md, @CONTEXTO.md y @ESTADO.md.
2. Si el primer mensaje no pide nada concreto, empieza por la sección "Próxima sesión" de `ESTADO.md`.
3. Si pide otra cosa, recuérdame en una línea qué tocaba según `ESTADO.md` y sigue con mi petición. Pregunta antes de seguir solo si choca con algo: depende de algo aún pendiente, contradice una decisión de `DECISIONES.md` o cambia el plan de la próxima sesión.

## Archivos de `.claude/`

| Archivo           | Para qué                                                      | Cuándo leerlo                                                                 |
|-------------------|---------------------------------------------------------------|-------------------------------------------------------------------------------|
| `CLAUDE.md`       | Arranque, índice de archivos y reglas para mantenerlos        | Siempre (se carga solo)                                                       |
| `PAUTAS.md`       | Cómo trabajar conmigo                                         | Siempre, al abrir el chat                                                     |
| `CONTEXTO.md`     | Qué es el proyecto, por qué y para qué                        | Siempre, al abrir el chat                                                     |
| `ESTADO.md`       | Fases hechas y pendientes, próxima sesión y lo abierto        | Siempre, al abrir el chat                                                     |
| `ESTILO.md`       | Cómo me gusta el código                                       | Antes de escribir o modificar código por primera vez en la sesión             |
| `TECNICO.md`      | Cómo está hecho: repo, entorno, comandos, estructura, datos   | Antes de tocar código o datos                                                 |
| `DECISIONES.md`   | Decisiones técnicas y metodológicas tomadas, con su porqué    | Antes de trabajar en una fase, y siempre antes de cambiar algo ya decidido    |
| `HISTORICO.md`    | Qué se hizo en cada sesión, con sus commits                   | Solo si lo pido o hay que averiguar cuándo se rompió algo                     |

## Reglas para mantener los archivos
- Cada dato vive en un solo archivo. Si encaja en dos, va al más específico y el otro no lo repite.
- Cada archivo empieza con su bloque "Qué hay en este archivo y cómo usarlo". Lo que no cuadra con ese bloque no va en ese archivo.
- Fuera de `TECNICO.md`, no se guarda lo que se saca rápido del código o de git.
- Una decisión abierta vive en `ESTADO.md`. Cuando se cierra, sale de ahí y pasa a `DECISIONES.md`, o a `CONTEXTO.md` si cambia el qué o el porqué del proyecto.
