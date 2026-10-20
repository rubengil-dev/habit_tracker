# Qué hay en este archivo y cómo usarlo
- **Contiene:** en qué punto estamos, por dónde empezar la próxima sesión, qué funciona y qué falla, y lo pendiente y abierto.
- **No contiene:** historial de lo que se probó por el camino ni decisiones ya cerradas.
- **Se actualiza:** al cerrar cada sesión.

## Próxima sesión
1. **Entrevista de diseño.** Hace meses que no toco la app y no recuerdo bien qué decidí. Recorrer qué quiero que sea la app y rellenar los huecos de los archivos de `.claude/` (marcados como "por definir" y "por recuperar"). Revisar las decisiones de `DECISIONES.md` y proponer mejoras: la implementación ya no depende de mi capacidad.
2. **Entorno.** Recrear `.venv`, que está roto, y hacer la ruta de la BBDD independiente de la carpeta de arranque (detalle en "Entorno").
3. **Git.** Hacer push y confirmar el borrado de `README.md` (ver "Git").
4. **Corregir los bugs confirmados y las mejoras menores**, ya alineados con lo decidido en la entrevista.

## Fases
- [x] Backend: CRUD de las cuatro entidades, los cuatro tipos de medalla, recálculo síncrono, rachas y cascada.
- [ ] Pulido del backend: bugs y pendientes de abajo.
- [ ] Frontend.
- [ ] Despliegue.

## Qué funciona
Verificado en ejecución el 23 jul 2026:
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
Todos verificados en ejecución el 15 oct 2026.
1. **500 en todo POST/PATCH/DELETE de registros cuya métrica tenga medallas.** El schema de respuesta espera medallas completas, pero el recálculo devuelve diccionarios con otra forma. Arreglo: un schema propio para ese diccionario.
2. **El rango de un periodo semanal sale equivocado.** Para el jueves 15/10 devuelve del 9/10 al 11/10, la cola de la semana anterior, porque el cálculo del periodo anterior resta 7 días a lo bruto en vez de ir al lunes y restar 1. Rompe el progreso actual de las medallas semanales; la racha no se ve afectada.
3. **Medalla de récord o histórica con "mayor es mejor" falso y sin registros → diamante.** Un `or 0` mete un 0, que en orden descendente es mejor que diamante. El mismo patrón en histórica/récord no distingue "sin registros" de un 0 real.
4. **Se acepta una frecuencia objetivo ≤ 0.** Con 0, la racha nunca rompe: recorre periodos hacia atrás hasta un `OverflowError` y devuelve 500 en cada registro de ese hábito.
5. **PATCH con `null` explícito en los booleanos** (activo, calculada, mayor es mejor) se guarda, porque esas columnas admiten nulos y un CHECK con NULL pasa en SQLite. Después, los GET devuelven 500 para siempre. Ejemplo: `PATCH /habits/1 {"active": null}`.
6. **PATCH de una métrica acepta un hábito sin validarlo.** Si no existe, da un 400 genérico en vez de 404. Si existe, las medallas y registros de esa métrica se quedan con el hábito antiguo y los datos quedan incoherentes.
7. **Crear un hábito ignora el campo "activo":** siempre lo crea activo.

## Mejoras menores
- Pydantic: sustituir la clase `Config` por `model_config = ConfigDict(from_attributes=True)`; la forma actual está deprecada y saca 4 avisos.
- Mover un registro a otro hábito solo devuelve la racha del hábito nuevo.

## Entorno
- `.venv` está roto desde que se movió la carpeta: lo creó Python 3.14 y sus ejecutables apuntan a la ruta antigua `developer\habit_tracker`. Mientras tanto, `python -m uvicorn` funciona.
- La ruta de la BBDD es relativa a la carpeta desde la que se arranca: arrancar desde otra crea una BBDD vacía sin avisar. Hacerla relativa al proyecto y que se pueda cambiar para las pruebas.

## Git
- Commiteado en local, sin push: todo lo anterior a esta sesión.
- `README.md` aparece como borrado, pero estaba vacío: confirmar el borrado en el siguiente commit.

## Pendiente para más adelante

### Tareas
- Blindar en el router que todo hábito tenga al menos una medalla de constancia.
- Bloquear los registros manuales sobre métricas calculadas.
- Motor de cálculo de métricas derivadas: leer la fórmula y generar o actualizar el registro de la métrica calculada. Depende del punto anterior; hacerlos juntos.
- Validar el contenido de la fórmula (hoy se acepta cualquier texto).
- CORS, cuando el frontend esté en otro origen.
- Frontend: confirmaciones de borrado (ver `CONTEXTO.md`).

### Decisiones abiertas
Backend:
- Registros con fecha futura: ¿bloquearlos?
- Zona horaria del "hoy" al desplegar en un servidor en UTC.
- Mover una métrica a otro hábito: ¿prohibirlo, o arrastrar sus medallas y registros? (bug 6).
- Versión de Python y gestión de dependencias (el entorno roto usa la 3.14).
- Récord histórico de racha (la más larga, no la actual): no diseñado.

Frontend y despliegue:
- Stack del frontend. A priori, una API REST y una app web instalable; modificable.
- Hosting. A priori, backend en Render o Railway y frontend en Vercel; modificable.
- Diseño visual y detalle de las dos vistas.
- Seguridad: es un solo usuario, pero una API desplegada es pública. ¿Hace falta autenticación?
- Si SQLite aguanta en un hosting gratuito sin disco persistente.

### Mejoras futuras
Nada por ahora (la visión futura está en `CONTEXTO.md`).

### Pendiente de probar yo
Nada.
