# Qué hay en este archivo y cómo usarlo
- **Contiene:** cómo trabajar conmigo en cualquier proyecto: qué sé, cómo hablarme, cómo avanzar, pruebas, cierre de sesión y git.
- **No contiene:** nada específico de un proyecto ni el estilo de código.
- **Se actualiza:** cuando cambio o añado una forma de trabajar.

## Qué sé
- **Lo manejo bien:** Python, pandas/numpy, Jupyter y SQL.
- **Me defiendo:** estadística clásica, R, Git/GitHub, terminal, entornos virtuales, cómo funciona una web (petición → backend/API → respuesta → front) y machine learning a nivel conceptual.
- **Me suena:** deep learning (conceptos), FastAPI (lo usé hace meses y lo tengo olvidado), Streamlit, despliegue en Vercel, VBA y DAX/M.
- **Nada:** análisis de supervivencia, Java, JavaScript/HTML/CSS, React, Flask, Docker, Render, y escribir código de machine learning o deep learning.
- En Git, terminal y entornos virtuales sé qué se puede hacer pero no me sé los comandos: cuando tenga que ejecutar algo, dame el comando exacto.

## Cómo hablarme
- Hablamos en español.
- Lo técnico nuevo: primero una analogía o un ejemplo para situarme, después la explicación técnica. En lo que manejo bien, ve directo.
- Cuando haya que elegir, dame opciones y una recomendación.
- Si algo no es obvio (por qué se hace de una forma y no de otra), explícamelo sin que te lo pida.
- Soy maniático con cómo quiero las cosas. Si algo que te pido choca con lo óptimo (para ti como LLM o para el proyecto), dímelo antes de hacerlo y explica por qué. Puedo aceptarlo igualmente, pero que sea una decisión consciente.

## Cómo avanzamos
- Quiero ir rápido: entender qué hace el código a grandes rasgos, no aprender a escribirlo. Lo que sí quiero aprender es a dirigir a la IA y a ver qué necesita un proyecto. Si quiero entender algo más a fondo, te lo pregunto.
- Primero hablamos el tema hasta estar de acuerdo. Después lo implementas entero del tirón.
- En cambios grandes (reestructuraciones, rediseños), antes de ejecutarlos lista punto a punto qué borras y qué creas, para tener el control y reflejarlo en `HISTORICO.md`. Del código existente conserva lo que sirva para no gastar tokens, pero cambia sin miedo lo que no sirva o se pueda hacer mejor.
- Al terminar, resume como un dev junior a su jefe de proyecto: por cada archivo nuevo o cambiado, 2-4 líneas de qué hace y cómo se combinan sus funciones principales para dar el resultado. Sin código ni explicación línea a línea. Los docstrings, claros, para que también sirvan de resumen.
- Cuando cambies archivos de `.claude/`, no me los copies en el chat: los reviso yo en el editor, que marca lo cambiado desde el último commit. Dime solo qué archivos has tocado y qué has cambiado, en pocas líneas. Cuando dé el OK a una revisión, commit, para que la siguiente ronda de cambios se vea limpia en el editor.
- Si hay notebooks y código, los notebooks son independientes: no importan nada del código. Las funciones que comparten se duplican y, si cambian, se actualizan en los dos sitios.

## Pruebas
- Las ejecutas tú (tests, scripts, servidor local + peticiones).
- Lo visual no lo puedes juzgar bien: pídeme que lo pruebe en ese momento. Solo si te digo que ahora no, lo apuntas en `ESTADO.md` como "Pendiente de probar yo".

## Cierre de sesión
Cuando diga "cerramos", "actualiza", "hemos terminado por hoy" o similar:
1. Test rápido solo de lo nuevo.
2. Actualiza los archivos de `.claude/` que toquen (como mínimo `ESTADO.md`) y enséñame los cambios para que dé el OK.
3. Con mi OK: commit del trabajo, merge si aplica y push a GitHub.
4. Escribe la entrada de la sesión en `HISTORICO.md` con los hashes del paso 3, y commitéala y súbela con el mismo OK. Va en un commit aparte porque un commit no puede llevar dentro su propio hash.

## Git
- Cambios sencillos sin riesgo: en la rama actual. Features, bugs o cualquier cosa con riesgo: rama nueva, que se fusiona a `main` al cerrar la sesión si todo va bien.
- Commits y merges solo con mi OK. Mensajes breves.
