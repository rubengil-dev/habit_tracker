# Qué hay en este archivo y cómo usarlo
- **Contiene:** las decisiones técnicas y metodológicas ya tomadas, agrupadas por área. Cada una es una pregunta con la decisión y su porqué.
- **No contiene:** decisiones abiertas ni decisiones de producto.
- **Se actualiza:** cuando se cierra una decisión abierta o se cambia una ya tomada. Para cambiar una, antes hay que hablarlo.

Donde el porqué dice "por recuperar", la decisión consta pero su motivo no se apuntó: se completa en la entrevista.

## Stack

### ¿Qué backend y qué base de datos?
- **Decisión:** Python + FastAPI + SQLAlchemy + SQLite.
- **Por qué:** es un solo usuario y SQLite no requiere gestionar un servidor de base de datos.

### ¿Hábitos y medallas fijos en el código o configurables?
- **Decisión:** el modelo de datos es data-driven: ningún hábito, métrica ni medalla está prefijado.
- **Por qué:** cualquier hábito se crea sin tocar código.

## Modelo de datos

### ¿Qué pasa al borrar un hábito, una métrica o una medalla?
- **Decisión:** todas las claves ajenas borran en cascada: borrar un hábito arrastra sus métricas, medallas y registros; borrar una métrica arrastra sus registros y medallas; borrar una medalla no arrastra nada.
- **Por qué:** no pueden quedar datos huérfanos.

### ¿Una métrica alimenta una medalla o varias?
- **Decisión:** varias. El recálculo busca todas las medallas de la métrica afectada.
- **Por qué:** por recuperar.

### ¿Cómo se representan los campos derivados (ritmo, etc.)?
- **Decisión:** como una métrica más, marcada como calculada y con su fórmula. Sus registros los genera el sistema, no el usuario: se bloquearán el POST y el PATCH manuales de registros sobre ellas. La fórmula tendrá que ser un texto usable: mínimo dos métricas del mismo hábito y un operador (`+ - * /`).
- **Por qué:** evita duplicar el registro (manual y calculado). Falta implementar el motor y los bloqueos (ver `ESTADO.md`).

### ¿Dónde viven el valor y el nivel actual de una medalla?
- **Decisión:** se guardan en la propia medalla y solo los fija el servidor; no existen en los schemas de entrada. Se recalculan de forma síncrona al crear, modificar o borrar un registro y al crear o modificar una medalla (en este último caso, tanto la métrica antigua como la nueva si cambia). Nunca con un proceso programado.
- **Por qué:** que un cliente no pueda fijar un nivel sin cumplirlo. El recálculo síncrono: por recuperar.

### ¿Se guarda la racha?
- **Decisión:** no. La racha y el progreso actual de una medalla ("3/7") se calculan al vuelo cada vez que se piden.
- **Por qué:** por recuperar.

### ¿La medalla guarda también el hábito, si ya cuelga de una métrica?
- **Decisión:** sí, a propósito (denormalizado) y con índice.
- **Por qué:** por recuperar.

### ¿Cómo se validan los valores de los enumerados?
- **Decisión:** doble capa: Pydantic en la API y `CheckConstraint` en la BBDD, generado automáticamente desde el propio enumerado. Los valores se guardan en minúscula; la capitalización es cosa del frontend. Las columnas siguen siendo texto plano.
- **Por qué:** defensa en profundidad: la restricción de la BBDD cubre cualquier escritura que se salte la API (p. ej. una futura migración desde Notion).

### ¿Todo hábito tiene medalla de constancia?
- **Decisión:** debería tener al menos una. Es regla de negocio, no restricción de BBDD. Falta blindarla en el router (ver `ESTADO.md`).
- **Por qué:** la racha del hábito se calcula sobre su medalla de constancia; sin ella no hay racha.

### ¿Cómo se ordenan los niveles de una medalla?
- **Decisión:** en constancia y objetivo, siempre ascendentes: el valor es un conteo (periodos cumplidos o registros que superan el listón), no el valor crudo. En ellas, "mayor es mejor" solo decide el sentido del filtro contra el listón (`>=` / `<=`). En histórica y récord, ascendentes o descendentes según "mayor es mejor".
- **Por qué:** un conteo más alto siempre es mejor.

### ¿Para qué sirve que un hábito esté activo?
- **Decisión:** para filtrar en el panel visual y mostrar solo los activos sin borrar nada.
- **Por qué:** conservar el historial de lo que ya no sigo.

### ¿Cuentan por separado varios registros el mismo día?
- **Decisión:** sí. Dos carreras hoy son dos para un objetivo semanal.
- **Por qué:** por recuperar.

## Medallas y rachas

### ¿Qué es un periodo en las medallas de constancia?
- **Decisión:** siempre periodos naturales de calendario (semana ISO de lunes a domingo, trimestres naturales…), nunca ventanas deslizantes.
- **Por qué:** por recuperar.

### ¿Cuenta el periodo en curso?
- **Decisión:** en la medalla de constancia, el periodo en curso cuenta en cuanto cumple, aunque no haya cerrado. En la racha, si cumple suma ya; si todavía no cumple, ni suma ni rompe; solo rompen los periodos ya cerrados que fallan.
- **Por qué:** no castigar un periodo que aún se puede cumplir. Se descartó romper la racha por "imposibilidad matemática de cumplir el periodo actual": complica la técnica sin necesidad y asumiría como máximo un registro útil al día.

### ¿Qué medalla de constancia manda en la racha del hábito?
- **Decisión:** la de periodo más corto; si empatan, la de mayor objetivo de frecuencia. Sin medallas de constancia, no hay racha.
- **Por qué:** por recuperar. El orden "más corto" sale del orden de declaración del enumerado de periodos, no de un valor numérico.

## API

### ¿Cómo responden los listados anidados?
- **Decisión:** 404 si el padre no existe; lista vacía con 200 si existe pero no tiene hijos.
- **Por qué:** por recuperar.

### ¿Cómo se validan las claves ajenas al crear o modificar?
- **Decisión:** siempre: (1) que cada una exista (404 si no) y (2) que sean coherentes entre sí cuando aplique (400 si no cuadran). En modificaciones parciales se toma el valor nuevo y, si no viene, el actual.
- **Por qué:** por recuperar.

### ¿Qué código devuelve un DELETE?
- **Decisión:** 200 con cuerpo si hay algo que contar (registros: medallas y racha actualizadas); 204 sin cuerpo en hábitos, métricas y medallas.
- **Por qué:** el frontend necesita saber qué cambió al borrar un registro.

### ¿Cómo se escriben los POST y los PATCH?
- **Decisión:** el POST asigna campo a campo de forma explícita; el PATCH recorre genéricamente los campos enviados. No cambiar sin motivo nuevo.
- **Por qué:** legibilidad.

### ¿Dónde se captura un error de integridad de la BBDD?
- **Decisión:** de forma global, en un único manejador que devuelve 400, no por endpoint.
- **Por qué:** por recuperar.

### ¿Cómo recibe el frontend el efecto de un registro sobre las medallas y la racha?
- **Decisión:** dentro de la respuesta del POST, el PATCH y el DELETE de registros, nunca en un GET aparte.
- **Por qué:** por recuperar.

### ¿Cuándo se calcula el progreso de una medalla ("3/7")?
- **Decisión:** solo en las de constancia y solo en las consultas (GET), nunca al crear ni modificar.
- **Por qué:** no se guarda, así que se calcula al pedirlo.

### ¿Se agrupan los endpoints en Swagger?
- **Decisión:** no. Todo aparece bajo "default".
- **Por qué:** es cosmético; se decidió no arreglarlo.

## Código

### ¿Dónde va cada función?
- **Decisión:** si conoce reglas de negocio, va en el archivo de su dominio aunque no "calcule" en sentido estricto; si es una herramienta ciega y reutilizable, va en las utilidades.
- **Por qué:** por recuperar.

## Metodología

### ¿Hay revisión periódica completa del código?
- **Decisión:** no. La del 15 oct 2026 fue la última. Al cerrar cada sesión solo se hace un test rápido de lo nuevo.
- **Por qué:** por recuperar.
