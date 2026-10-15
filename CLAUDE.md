# Habit Tracker

Al empezar cada sesión, lee enteros `CONTEXTO.md` y `ESTADO.md`. Si ESTADO tiene una sección "PRÓXIMA SESIÓN", se empieza por ahí.

## Los dos archivos
- `CONTEXTO.md`: qué estamos construyendo y por qué. Incluye la visión, las decisiones y sus motivos, lo necesario para entender la app. Es estable: no se toca salvo que yo lo pida.
- `ESTADO.md`: foto del punto actual, con lo hecho, lo que falla y lo que queda. No es un historial: si algo se prueba, falla y se arregla, solo queda el resultado final. Única excepción: un intento fallido que no hay que repetir se apunta, con su motivo.

## Forma de trabajar
Esta sección manda sobre CONTEXTO §1, §7 y §8 mientras CONTEXTO no se reescriba.
- Primero hablamos el tema hasta estar de acuerdo. Después lo implementas entero del tirón y al final resumes en pocas líneas qué has hecho, como un dev junior a su jefe de proyecto.
- Los tests los ejecutas tú (servidor + curl) contra una BBDD de prueba, nunca contra `habits.db`.
- Cierre de sesión: cuando diga "cerramos", "actualiza", "hemos terminado por hoy" o algo similar:
  1. Haz un test rápido solo de lo nuevo, no de toda la app, siguiendo el punto anterior.
  2. Actualiza `ESTADO.md` y dime resumidamente qué has cambiado, para que dé el OK.
  3. Si todo lo anterior ha ido bien, propón el commit (y el merge, si hay rama) y espera mi OK.

## Git
- Cambios sencillos sin riesgo de romper nada: en la rama actual.
- Features nuevas, corrección de bugs o cualquier cosa con riesgo: en una rama nueva, que se fusiona a `main` al cerrar la sesión si todo va bien.
- Commits y merges solo con mi OK.
