# Qué hay en este archivo y cómo usarlo
- **Contiene:** las decisiones técnicas y metodológicas ya tomadas, agrupadas por área. Cada una es una pregunta con la decisión y su porqué.
- **No contiene:** decisiones abiertas ni decisiones de producto.
- **Se actualiza:** cuando se cierra una decisión abierta o se cambia una ya tomada. Para cambiar una, antes hay que hablarlo.

Donde el porqué dice "por recuperar", la decisión consta pero su motivo no se apuntó: se completa en la entrevista.

Varias decisiones de la entrevista de diseño (21 oct 2026) cambian el modelo y aún no están implementadas: el código actual sigue con registros sueltos por métrica, medallas colgadas de métricas y fórmulas de texto.

## Stack

### ¿Se conserva el código actual?
- **Decisión:** es el punto de partida, pero se puede reestructurar entero. Se conserva el diseño de la lógica de medallas y rachas. Cualquier reestructuración se presenta antes de hacerla, explicando qué cambia respecto a lo que hay.
- **Por qué:** sus límites venían de lo que yo sabía hacer cuando empecé; ahora lo programa Claude. La lógica de medallas y rachas es lo más valioso y ya está probada.

### ¿Qué base de datos?
- **Decisión:** una base de datos gestionada en la nube, no un archivo SQLite en el servidor. Cuál, abierto en `ESTADO.md`. La BBDD actual es de prueba y se puede borrar: no hay nada que migrar.
- **Por qué:** los hostings gratuitos no conservan el disco, así que un archivo SQLite perdería los datos al desplegar.

### ¿App nativa o web instalable?
- **Decisión:** web instalable. Se prueba sobre Android.
- **Por qué:** una sola app para móvil y portátil, que funciona también en iPhone, sin pasar por tiendas de apps.

### ¿Hábitos y medallas fijos en el código o configurables?
- **Decisión:** el modelo de datos es data-driven: ningún hábito, métrica ni medalla está prefijado.
- **Por qué:** cualquier hábito se crea sin tocar código, y cada usuario crea los suyos si la app se abre a más gente.

## Usuarios e identificadores

### ¿Hay login y usuarios?
- **Decisión:** el MVP tiene login con un sistema que admite varios usuarios, pero con el registro cerrado y solo mi cuenta. Cada hábito guarda su dueño desde el principio.
- **Por qué:** una API desplegada es pública y necesita login igualmente. Hacerlo multiusuario desde el principio cuesta casi lo mismo y deja abierta la fase 2 sin migraciones con datos reales.

### ¿Cómo se identifica cada fila?
- **Decisión:** con UUID, no con números correlativos.
- **Por qué:** permite fusionar bases de datos distintas sin choques, p. ej. pasar de una copia propia a la app central con exportar e importar.

## Modelo de datos

### ¿Cómo se registra un hábito?
- **Decisión:** por sesiones (ver `CONTEXTO.md`), no con un registro suelto por métrica. Varias sesiones el mismo día son independientes.
- **Por qué:** con registros sueltos, el tiempo y la distancia de una misma actividad no quedaban unidos, y con dos actividades el mismo día era imposible calcular bien el ritmo. Dos carreras son dos actividades distintas. Además, la sesión sin valores cubre los hábitos de sí/no sin un tipo de métrica aparte.

### ¿Qué tipos de métrica hay y cómo se guarda la duración?
- **Decisión:** número y duración. La duración se guarda en segundos; el front la introduce y la muestra como minutos y segundos.
- **Por qué:** una sola columna, fácil de sumar y comparar.

### ¿Cómo funcionan las métricas calculadas?
- **Decisión:** se calculan al guardar la sesión y se guardan con ella. A y B no pueden ser calculadas. El valor se guarda en las unidades crudas (p. ej. km por segundo) y el front lo convierte al mostrarlo, igual que los segundos. De momento solo existe el tipo ritmo (A ÷ B).
- **Por qué:** guardarlas permite verlas en cada sesión y usarlas en medallas; con sesiones, calcularlas al guardar es trivial, sin motor aparte. Se descartaron la fórmula de texto libre (difícil de interpretar con seguridad, validar y mostrar con unidades) y poder rellenarlas a mano a veces, que era lo que la complicaba. Que una calculada no use otra evita bucles. Los tipos porcentaje y producto se propusieron y no convencieron.

### ¿Qué pasa al borrar un hábito, una métrica o una medalla?
- **Decisión:** todo borra en cascada: borrar un hábito arrastra todo lo suyo (métricas, medallas y sesiones); borrar una métrica arrastra sus valores y las medallas que la usan; borrar una medalla no arrastra nada.
- **Por qué:** no pueden quedar datos huérfanos.

### ¿De qué cuelga una medalla?
- **Decisión:** siempre del hábito. La métrica es opcional y depende del tipo (ver `CONTEXTO.md`).
- **Por qué:** los hábitos sin métricas (gimnasio) también necesitan medallas, y una histórica de sesiones tiene sentido aunque el hábito tenga métricas. Se descartaron una métrica ficticia en todos los hábitos (mete ruido) y partir la histórica en dos tipos (duplica lógica).

### ¿Una métrica alimenta una medalla o varias?
- **Decisión:** varias. El recálculo busca todas las medallas afectadas.
- **Por qué:** cada hábito es un reto visto desde varios ángulos; la misma métrica da medallas distintas (p. ej. distancia: histórica y objetivo).

### ¿Dónde viven el valor y el nivel actual de una medalla?
- **Decisión:** se guardan en la propia medalla y solo los fija el servidor; no existen en los schemas de entrada. Se recalculan de forma síncrona al crear, modificar o borrar una sesión y al crear o modificar una medalla. Nunca con un proceso programado.
- **Por qué:** que un cliente no pueda fijar un nivel sin cumplirlo. El recálculo síncrono: por recuperar.

### ¿Se guarda la racha?
- **Decisión:** no. La racha, la mejor racha y el progreso actual de una medalla ("3/7") se calculan al vuelo cada vez que se piden.
- **Por qué:** por recuperar.

### ¿Cómo se validan los valores de los enumerados?
- **Decisión:** doble capa: Pydantic en la API y `CheckConstraint` en la BBDD, generado automáticamente desde el propio enumerado. Los valores se guardan en minúscula; la capitalización es cosa del frontend. Las columnas siguen siendo texto plano.
- **Por qué:** defensa en profundidad: la restricción de la BBDD cubre cualquier escritura que se salte la API (p. ej. una futura importación).

### ¿Cómo se ordenan los niveles de una medalla?
- **Decisión:** en constancia y objetivo, siempre ascendentes: el valor es un conteo (periodos cumplidos o sesiones que superan el listón), no el valor crudo. En ellas, "mayor es mejor" solo decide el sentido del filtro contra el listón (`>=` / `<=`). En histórica y récord, ascendentes o descendentes según "mayor es mejor". "Mayor es mejor" va en cada medalla, no en la métrica.
- **Por qué:** un conteo más alto siempre es mejor. La misma métrica puede ser buena alta en una medalla (la sesión más larga) y baja en otra (el sprint más rápido).

### ¿Para qué sirve que un hábito esté activo?
- **Decisión:** para filtrar en el panel visual y mostrar solo los activos sin borrar nada.
- **Por qué:** conservar el historial de lo que ya no sigo.

## Medallas y rachas

### ¿De dónde sale la racha?
- **Decisión:** del objetivo de frecuencia, que es una propiedad del propio hábito, obligatoria desde que se crea. Sustituye a la regla anterior: todo hábito debía tener una medalla de constancia y, si tenía varias, mandaba la de periodo más corto. Cambiar el objetivo es retroactivo: el nuevo juzga todo el historial.
- **Por qué:** garantiza que todo hábito tenga racha y elimina el desempate entre medallas de constancia. Se descartó que el objetivo fuera una medalla especial (reglas propias: única, no borrable y con umbrales obligatorios al crear el hábito). Se descartó guardar un historial de objetivos: si quiero conservar el anterior, creo otro hábito.

### ¿Desde cuándo cuenta la racha?
- **Decisión:** nunca antes de la fecha de inicio del hábito.
- **Por qué:** en un hábito a evitar, un día sin sesiones es un éxito; sin ese límite, la racha recorrería el pasado sin fin (origen del bug 4 de `ESTADO.md`).

### ¿Qué es un periodo en las medallas de constancia?
- **Decisión:** siempre periodos naturales de calendario (semana ISO de lunes a domingo, trimestres naturales…), nunca ventanas deslizantes.
- **Por qué:** por recuperar.

### ¿Cuenta el periodo en curso?
- **Decisión:** en la medalla de constancia, el periodo en curso cuenta en cuanto cumple, aunque no haya cerrado. En la racha, si cumple suma ya; si todavía no cumple, ni suma ni rompe; solo rompen los periodos ya cerrados que fallan.
  En modo evitar es al revés: el periodo en curso no suma hasta que se cierra, y si ya se ha pasado del máximo, rompe al momento.
- **Por qué:** no castigar un periodo que aún se puede cumplir. Se descartó romper la racha por "imposibilidad matemática de cumplir el periodo actual": complica la técnica sin necesidad y asumiría como máximo un registro útil al día. En modo evitar, un periodo abierto aún se puede fallar (sumarlo a medianoche sería premiar sin haber hecho nada), y uno que ya ha pasado del máximo no tiene arreglo.

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
