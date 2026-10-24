# Qué hay en este archivo y cómo usarlo
- **Contiene:** en qué punto estamos respecto a las fases del proyecto, por dónde empezar la próxima sesión y lo pendiente para más adelante.
- **No contiene:** cifras, nombres de archivos, detalles de lo hecho ni decisiones ya cerradas.
- **Se actualiza:** al cerrar cada sesión.

## Próxima sesión
1. **Montar el entorno del rediseño:**
   - Elegir la versión de Python según lo que soporte Vercel (tengo instaladas la 3.11 y la 3.14; uv descarga la que haga falta).
   - Que Claude me enseñe uv con los comandos exactos, por si lo aplico en otros proyectos.
   - Verificar las condiciones de los planes gratuitos de Vercel y Neon. Las cuentas las creo yo; Claude no las crea.
2. **Rediseño del backend**, en rama aparte. Antes de ejecutarlo, Claude me lista punto a punto qué borra y qué crea, para tener el control y reflejarlo en `HISTORICO.md`. Con tests de pytest desde el principio (ver Tareas).

## Fases
- [x] Backend v1: CRUD de las cuatro entidades, los cuatro tipos de medalla, recálculo síncrono, rachas y cascada.
- [x] Entrevista de diseño, salvo el bloque 5.
- [ ] Rediseño del backend según la entrevista.
- [ ] Frontend, empezando por la entrevista de front (bloque 5).
- [ ] Despliegue (entra en el MVP).

## Qué funciona
Del backend v1. Verificado en ejecución el 23 jul 2026:
- Los cuatro tipos de medalla, con "mayor es mejor" verdadero y falso.
- Recálculo síncrono al crear, modificar (incluido el cambio de métrica) y borrar registros, y al crear o modificar medallas, sobre todas las medallas de la métrica afectada. Sin interferencias entre métricas.
- Orden de umbrales protegido en creación y en PATCH.
- Racha del hábito, sus dos desempates, y rotura correcta con un hueco.
- Cascada de borrado en tres niveles, sin huérfanos.
- Errores: 404 por clave ajena inexistente, 400 por descuadre o violación de restricción, 422 por validación.

Implementado sin testear:
- Valor y nivel actual fuera de los schemas de entrada.
- Índices en claves ajenas.
- Restricciones de enumerados en la BBDD.
- Progreso actual de la medalla de constancia, calculado por SQL y expuesto en la API.
- Schemas de respuesta aplicados a los cuatro routers.

## Bugs confirmados
Del backend v1, todos verificados en ejecución el 15 oct 2026. No se arreglan en el v1: el rediseño los resuelve o los absorbe (el 1 desaparece con los schemas nuevos; el 2, 3, 5 y 7 se corrigen al portar el código; el 4 lo cubren la fecha de inicio y la validación; el 6 desaparece al prohibir mover métricas). Sirven de lista de casos para los tests.
1. **500 en todo POST/PATCH/DELETE de registros cuya métrica tenga medallas.** El schema de respuesta espera medallas completas, pero el recálculo devuelve diccionarios con otra forma. Arreglo: un schema propio para ese diccionario.
2. **El rango de un periodo semanal sale equivocado.** Para el jueves 15/10 devuelve del 9/10 al 11/10, la cola de la semana anterior, porque el cálculo del periodo anterior resta 7 días a lo bruto en vez de ir al lunes y restar 1. Rompe el progreso actual de las medallas semanales; la racha no se ve afectada.
3. **Medalla de récord o histórica con "mayor es mejor" falso y sin registros → diamante.** Un `or 0` mete un 0, que en orden descendente es mejor que diamante. El mismo patrón en histórica/récord no distingue "sin registros" de un 0 real.
4. **Se acepta una frecuencia objetivo ≤ 0.** Con 0, la racha nunca rompe: recorre periodos hacia atrás hasta un `OverflowError` y devuelve 500 en cada registro de ese hábito. Ojo: con el modo evitar, "como máximo 0" pasa a ser válido; lo que no puede ser ≤ 0 es "al menos".
5. **PATCH con `null` explícito en los booleanos** (activo, calculada, mayor es mejor) se guarda, porque esas columnas admiten nulos y un CHECK con NULL pasa en SQLite. Después, los GET devuelven 500 para siempre. Ejemplo: `PATCH /habits/1 {"active": null}`.
6. **PATCH de una métrica acepta un hábito sin validarlo.** Si no existe, da un 400 genérico en vez de 404. Si existe, las medallas y registros de esa métrica se quedan con el hábito antiguo y los datos quedan incoherentes.
7. **Crear un hábito ignora el campo "activo":** siempre lo crea activo.

## Mejoras menores
- Pydantic: sustituir la clase `Config` por `model_config = ConfigDict(from_attributes=True)`; la forma actual está deprecada y saca 4 avisos.

## Entorno
Del v1. Los dos problemas desaparecen con el rediseño (uv y variables de entorno), así que no se arreglan antes.
- `.venv` está roto desde que se movió la carpeta: lo creó Python 3.14 y sus ejecutables apuntan a la ruta antigua `developer\habit_tracker`. Mientras tanto, `python -m uvicorn` funciona.
- La ruta de la BBDD es relativa a la carpeta desde la que se arranca: arrancar desde otra crea una BBDD vacía sin avisar.

## Pendiente para más adelante

### Tareas
- **Tests de pytest de los casos que ya fallaron o son delicados**: "menos es mejor" (p. ej. los 100 m más rápidos), periodos semanales, modo evitar (incluido el máximo 0), sesiones futuras, cambio de objetivo retroactivo, mejor racha, calculadas en hábitos con historia y borrado de etiquetas.
- **Frontend**: confirmaciones de borrado (ver `CONTEXTO.md`).
- **Entrevista de front** (bloque 5) cuando toque empezar el frontend.

### Decisiones abiertas
Frontend (bloque 5, al empezar el frontend):
- Pantallas, diseño visual y retroalimentación visual (animaciones; ¿vibración o sonido?). Hay un esqueleto propuesto por Claude: Hoy, Registrar, Medallas, Detalle del hábito y Configuración.
- Cómo se muestra la mejor racha.
- Framework del frontend.
- Fecha por defecto al registrar de madrugada: ¿que el día empiece a las 4:00, para que a la 1:00 aparezca ayer?

Backend:
- Versión de Python (ver Próxima sesión).
- Medalla de racha: ¿su valor es la mejor racha del hábito (el nivel conseguido no baja si se rompe la racha) o la racha actual (el nivel baja al romperse)? ¿Y las del modo evitar? Recomendación: la mejor racha, para que las medallas reflejen progreso conseguido.

Fase 2:
- Implicaciones legales de guardar datos de otros, antes de abrir la app fuera de familia y amigos cercanos.

## Pendiente de probar yo 
Nada.