# Qué hay en este archivo y cómo usarlo
- **Contiene:** en qué punto estamos, por dónde empezar la próxima sesión, qué funciona y qué falla, y lo pendiente y abierto.
- **No contiene:** historial de lo que se probó por el camino ni decisiones ya cerradas.
- **Se actualiza:** al cerrar cada sesión.

## Próxima sesión
1. **Seguir la entrevista de diseño por el bloque 4.** Los bloques 1 (para qué y para quién), 2 (modelo de datos) y 3 (medallas) se hicieron el 21 oct 2026; lo decidido está en `CONTEXTO.md` y `DECISIONES.md`. Quedan:
   - **4. Rachas:** cómo se guarda el objetivo del hábito, la racha en modo evitar y el récord de racha.
   - **5. Vistas y diseño visual**, incluida la retroalimentación visual al registrar y al subir de nivel.
   - **6. Stack, hosting, login y base de datos:** qué se conserva del código y qué se rehace, presentado antes de tocar nada.
   - **7. Decisiones abiertas del backend** (abajo).

   Al terminar: lista del MVP (qué entra y qué va después) con una estimación, para tenerlo cuanto antes y como muy tarde el 1 ene 2027.
2. **Entorno.** Depende del bloque 6: si cambian la BBDD o el stack, el arreglo de `.venv` y de la ruta de la BBDD puede cambiar o sobrar.
3. **Bugs y mejoras menores.** Tras el bloque 6, ver cuáles siguen vivos con el rediseño.

## Fases
- [x] Backend v1: CRUD de las cuatro entidades, los cuatro tipos de medalla, recálculo síncrono, rachas y cascada.
- [ ] Entrevista de diseño (quedan los bloques 4 a 7).
- [ ] Rediseño del backend según la entrevista.
- [ ] Frontend.
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
Del backend v1, todos verificados en ejecución el 15 oct 2026.
1. **500 en todo POST/PATCH/DELETE de registros cuya métrica tenga medallas.** El schema de respuesta espera medallas completas, pero el recálculo devuelve diccionarios con otra forma. Arreglo: un schema propio para ese diccionario.
2. **El rango de un periodo semanal sale equivocado.** Para el jueves 15/10 devuelve del 9/10 al 11/10, la cola de la semana anterior, porque el cálculo del periodo anterior resta 7 días a lo bruto en vez de ir al lunes y restar 1. Rompe el progreso actual de las medallas semanales; la racha no se ve afectada.
3. **Medalla de récord o histórica con "mayor es mejor" falso y sin registros → diamante.** Un `or 0` mete un 0, que en orden descendente es mejor que diamante. El mismo patrón en histórica/récord no distingue "sin registros" de un 0 real.
4. **Se acepta una frecuencia objetivo ≤ 0.** Con 0, la racha nunca rompe: recorre periodos hacia atrás hasta un `OverflowError` y devuelve 500 en cada registro de ese hábito. Ojo: con el modo evitar, "como máximo 0" pasa a ser válido.
5. **PATCH con `null` explícito en los booleanos** (activo, calculada, mayor es mejor) se guarda, porque esas columnas admiten nulos y un CHECK con NULL pasa en SQLite. Después, los GET devuelven 500 para siempre. Ejemplo: `PATCH /habits/1 {"active": null}`.
6. **PATCH de una métrica acepta un hábito sin validarlo.** Si no existe, da un 400 genérico en vez de 404. Si existe, las medallas y registros de esa métrica se quedan con el hábito antiguo y los datos quedan incoherentes.
7. **Crear un hábito ignora el campo "activo":** siempre lo crea activo.

## Mejoras menores
- Pydantic: sustituir la clase `Config` por `model_config = ConfigDict(from_attributes=True)`; la forma actual está deprecada y saca 4 avisos.
- Mover un registro a otro hábito solo devuelve la racha del hábito nuevo.

## Entorno
- `.venv` está roto desde que se movió la carpeta: lo creó Python 3.14 y sus ejecutables apuntan a la ruta antigua `developer\habit_tracker`. Mientras tanto, `python -m uvicorn` funciona.
- La ruta de la BBDD es relativa a la carpeta desde la que se arranca: arrancar desde otra crea una BBDD vacía sin avisar. Hacerla relativa al proyecto y que se pueda cambiar para las pruebas.

## Pendiente para más adelante

### Tareas
- Probar explícitamente las medallas de "menos es mejor" (p. ej. los 100 m más rápidos): en la primera versión dieron muchos errores.
- CORS, cuando el frontend esté en otro origen.
- Frontend: confirmaciones de borrado (ver `CONTEXTO.md`).

### Decisiones abiertas
Rachas (bloque 4):
- Cómo se guarda el objetivo del hábito: como campo propio del hábito o como una medalla de constancia predeterminada que se crea con él.
- Racha en modo evitar: cómo cuenta el periodo en curso.
- Récord histórico de racha (la más larga, no la actual): no diseñado.

Vistas y diseño (bloque 5):
- Diseño visual, detalle de las dos vistas y retroalimentación visual.

Stack y despliegue (bloque 6):
- Stack del backend: seguir con FastAPI o cambiar; versión de Python y gestión de dependencias (el entorno roto usa la 3.14).
- Stack del frontend, dentro de una web instalable.
- Qué base de datos gestionada.
- Qué servicio de login.
- Hosting. A priori, backend en Render o Railway y frontend en Vercel; modificable.

Backend (bloque 7):
- Registros con fecha futura: ¿bloquearlos?
- Zona horaria del "hoy" al desplegar en un servidor en UTC.
- Mover una métrica a otro hábito: ¿prohibirlo, o arrastrar sus medallas y sesiones? (bug 6).

Fase 2:
- Implicaciones legales de guardar datos de otros, antes de abrir la app fuera de familia y amigos cercanos.

### Mejoras futuras
Nada por ahora (la visión futura está en `CONTEXTO.md`).

### Pendiente de probar yo
Nada.
