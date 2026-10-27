# Qué hay en este archivo y cómo usarlo
- **Contiene:** las decisiones técnicas y metodológicas ya tomadas, agrupadas por área. Cada una es una pregunta con la decisión y su porqué.
- **No contiene:** decisiones abiertas ni decisiones de producto.
- **Se actualiza:** cuando se cierra una decisión abierta o se cambia una ya tomada. Para cambiar una, antes hay que hablarlo.

Donde el porqué dice "por recuperar", la decisión consta pero su motivo no se apuntó: se completa en la entrevista.

## Stack

### ¿Se conserva el código actual?
- **Decisión:** es el punto de partida, no una obligación. Se reutiliza lo que sirve, para no gastar tokens en rehacerlo; lo demás (cálculos, manejador de errores, códigos de respuesta, funciones heredadas que no entiendo) se puede cambiar, simplificar u optimizar. Los cambios grandes van en rama aparte y, antes de ejecutarlos, se lista punto a punto qué se borra y qué se crea.
- **Por qué:** los límites venían de lo que yo sabía hacer; ahora lo programa Claude. Parte del código lo escribió una IA gratuita y ya no lo entiendo. La lista punto a punto me da el control y, si algo se rompe, permite volver a ver qué se tocó (`HISTORICO.md`). La lógica de medallas y rachas era lo más probado, buen candidato a portar.

### ¿Qué base de datos?
- **Decisión:** Postgres gestionado en Neon, no un archivo SQLite en el servidor.
- **Por qué:** los hostings gratuitos no conservan el disco, así que un archivo SQLite perdería los datos al desplegar. Neon es gratuito y de sobra para un usuario, se duerme solo sin uso y despierta al conectarse, sin las pausas manuales de Supabase.

### ¿Contra qué base de datos se desarrolla y se prueba?
- **Decisión:** los tests, en SQLite en memoria (una base de datos nueva por test) y, cuando se quiera, contra un Postgres de usar y tirar. El servidor local, contra la rama `dev` de Neon; la app desplegada, contra la rama `production`.
- **Por qué:** SQLite en memoria es rápido, no necesita red y no toca datos reales. Postgres instalado en local obligaría a instalarlo o a usar Docker. Una rama de Neon es una copia aparte que se puede romper sin tocar la de producción.

### ¿App nativa o web instalable?
- **Decisión:** web instalable. Se prueba sobre Android.
- **Por qué:** una sola app para móvil y portátil, que funciona también en iPhone, sin pasar por tiendas de apps.

### ¿Dónde se despliega?
- **Decisión:** el backend FastAPI como funciones serverless en Vercel y el frontend en el mismo proyecto de Vercel, con la base de datos en Neon. Sin CORS, porque front y API comparten dirección.
- **Por qué:** coste 0 y sin servidor que gestionar. El arranque en frío (alrededor de un segundo) es asumible, y las animaciones no esperan al servidor: el front celebra al instante y confirma por detrás. Descartados: Render en gratuito (se duerme a los 15 minutos y tarda alrededor de un minuto en despertar), Supabase como backend completo (obligaría a reescribir la lógica de medallas en SQL y pausa el proyecto tras una semana sin uso) y todo en JavaScript (se perdería la lógica en Python). Condiciones verificadas el 26 oct 2026: Vercel Hobby es solo para uso personal no comercial y, si se pasa de sus límites, se para sin cobrar; Neon Free solo guarda unas horas de historial para restaurar, así que exportar es la copia de seguridad.

### ¿Con qué herramientas se gestiona el backend?
- **Decisión:** Python 3.14, con uv para Python y dependencias, Alembic para las migraciones de la BBDD y pytest para los tests. La configuración (dirección de la BBDD) va en variables de entorno, nunca en el código: un `.env` local ignorado por git y la configuración de Vercel en producción.
- **Por qué:** 3.14 es la más nueva que soporta Vercel, ya estaba instalada y es la que más soporte tiene por delante; un año después de salir, todas las librerías la soportan. uv recrea el entorno con un comando y fija versiones exactas, lo que evita casos como el `.venv` roto del v1. Alembic permite cambiar tablas sin borrar datos reales. pytest evita probar a mano con `curl`.

### ¿Hábitos y medallas fijos en el código o configurables?
- **Decisión:** el modelo de datos es data-driven: ningún hábito, métrica ni medalla está prefijado.
- **Por qué:** cualquier hábito se crea sin tocar código, y cada usuario crea los suyos si la app se abre a más gente.

## Usuarios e identificadores

### ¿Hay login y usuarios?
- **Decisión:** el MVP tiene un login propio, dentro de FastAPI, que admite varios usuarios pero con el registro cerrado: los usuarios se crean con un script, no desde la app. Contraseña cifrada con Argon2. Sesión de tres meses que se renueva sola cada día que uso la app; tras tres meses sin entrar, hay que volver a hacer login. Cinco fallos seguidos bloquean el usuario quince minutos. Cada hábito guarda su dueño desde el principio. El login con Google se añade en una iteración posterior.
- **Por qué:** una API desplegada es pública y necesita login igualmente. Hacerlo multiusuario desde el principio cuesta casi lo mismo y deja abierta la fase 2 sin migraciones con datos reales. Con el registro cerrado, nadie puede crearse una cuenta desde fuera. Si dejo de usar la app, el acceso se cierra solo, por si acaso. Un proveedor externo (Clerk, Google) aporta recuperación de contraseña y login social, que el MVP no necesita.

### ¿Cómo funciona la sesión de login?
- **Decisión:** la cookie lleva un código aleatorio y la BBDD guarda solo su huella (SHA-256), no una cookie firmada con una clave secreta. Cambiar la contraseña cierra todas las sesiones.
- **Por qué:** cerrar sesión o cambiar la contraseña anula la sesión al momento, cosa que una cookie firmada no permite. Sin firma no hay clave secreta que guardar. Si alguien robara una copia de la BBDD, las huellas no le darían sesiones válidas.

### ¿Cómo se identifica cada fila?
- **Decisión:** con UUID, no con números correlativos.
- **Por qué:** permite fusionar bases de datos distintas sin choques, p. ej. pasar de una copia propia (clon) a la app central con exportar e importar.

## Modelo de datos

### ¿Cómo se registra un hábito?
- **Decisión:** por sesiones (ver `CONTEXTO.md`), no con un registro suelto por métrica. Varias sesiones el mismo día son independientes.
- **Por qué:** con registros sueltos, el tiempo y la distancia de una misma actividad no quedan unidos, y con dos actividades el mismo día es imposible calcular bien el ritmo. Dos carreras son dos actividades distintas. Además, la sesión sin valores cubre los hábitos de sí/no sin un tipo de métrica aparte.

### ¿Qué tipos de métrica hay y cómo se guarda la duración?
- **Decisión:** número, duración y ritmo. El ritmo es la calculada (A ÷ B): un tipo más, no una métrica con un campo de cálculo aparte. La duración se guarda en segundos; el front la introduce y la muestra como minutos y segundos.
- **Por qué:** un tipo de métrica en vez de "calculada sí/no + tipo de cálculo" es lo mismo con un campo menos. Los segundos van en una sola columna, fácil de sumar y comparar.

### ¿Cómo funcionan las métricas calculadas?
- **Decisión:** se calculan al guardar la sesión y se guardan con ella; quedan vacías si falta A o B, o si B es 0. A y B no pueden ser calculadas. El valor se guarda en las unidades crudas (p. ej. segundos por km) y el front lo convierte al mostrarlo, igual que los segundos. De momento solo existe el tipo ritmo (A ÷ B).
- **Por qué:** guardarlas permite verlas en cada sesión y usarlas en medallas; con sesiones, calcularlas al guardar es trivial, sin motor aparte. Se descartaron la fórmula de texto libre (difícil de interpretar con seguridad, validar y mostrar con unidades) y poder rellenarlas a mano a veces, que era lo que la complicaba. Que una calculada no use otra evita bucles. Los tipos porcentaje y producto se propusieron y no convencieron.

### ¿Qué pasa al borrar un hábito, una métrica o una medalla?
- **Decisión:** todo borra en cascada: borrar un hábito arrastra todo lo suyo (métricas, etiquetas, medallas y sesiones); borrar una métrica arrastra sus valores, los ritmos que la usan (con sus valores) y las medallas de todas ellas; borrar una medalla no arrastra nada. Borrar una métrica que usa un ritmo avisa de cuáles se borran con ella, con un simple aceptar o cancelar.
- **Por qué:** no pueden quedar datos huérfanos, y un ritmo sin uno de sus operandos ya no se puede calcular.

### ¿De qué cuelga una medalla?
- **Decisión:** siempre del hábito. La métrica es opcional y depende del tipo (ver `CONTEXTO.md`).
- **Por qué:** los hábitos sin métricas (gimnasio) también necesitan medallas, y una histórica de sesiones tiene sentido aunque el hábito tenga métricas. Se descartaron una métrica ficticia en todos los hábitos (mete ruido) y partir la histórica en dos tipos (duplica lógica).

### ¿Qué medallas se recalculan?
- **Decisión:** todas las del hábito afectado. Una métrica puede alimentar varias medallas.
- **Por qué:** cada hábito es un reto visto desde varios ángulos; la misma métrica da medallas distintas (p. ej. distancia: histórica y objetivo). Una sesión toca todas las métricas del hábito y cuenta para las medallas de número de sesiones, así que en la práctica todas quedan afectadas; con un usuario, recalcularlas todas no es más lento.

### ¿Dónde viven el valor y el nivel actual de una medalla?
- **Decisión:** se guardan en la propia medalla y solo los fija el servidor; no existen en los schemas de entrada. Se recalculan de forma síncrona al crear, modificar o borrar una sesión, al crear o modificar una medalla, al cambiar la fecha de inicio del hábito o borrar una etiqueta, y también al leer las medallas o la vista del día. Nunca con un proceso programado.
- **Por qué:** que un cliente no pueda fijar un nivel sin cumplirlo. Al leer, porque las medallas del modo evitar suben solas con los días sin que se registre nada. El recálculo síncrono al escribir: por recuperar.

### ¿Dónde se hacen los cálculos de medallas y rachas?
- **Decisión:** en Python, sobre las sesiones del hábito cargadas una sola vez, no en SQL.
- **Por qué:** con los filtros de etiquetas, el SQL se complicaría mucho. Con un usuario hay pocos datos, y el resultado es el mismo en SQLite (tests) y en Postgres.

### ¿Se guarda la racha?
- **Decisión:** no. La racha, la mejor racha y el progreso actual de una medalla ("3/7") se calculan al vuelo cada vez que se piden.
- **Por qué:** por recuperar.

### ¿Cómo se validan los valores de los enumerados?
- **Decisión:** doble capa: Pydantic en la API y `CheckConstraint` en la BBDD, generado automáticamente desde el propio enumerado. Los valores se guardan en minúscula; la capitalización es cosa del frontend. Las columnas siguen siendo texto plano.
- **Por qué:** defensa en profundidad: la restricción de la BBDD cubre cualquier escritura que se salte la API (p. ej. una futura importación).

### ¿Cómo se ordenan los niveles de una medalla?
- **Decisión:** en objetivo, constancia y racha, siempre ascendentes: el valor es un conteo (sesiones que superan el listón, periodos cumplidos o periodos seguidos), no el valor crudo. En ellas, "mayor es mejor" solo decide el sentido del filtro contra el listón (`>=` / `<=`). En histórica y récord, ascendentes o descendentes según "mayor es mejor". "Mayor es mejor" va en cada medalla, no en la métrica.
- **Por qué:** un conteo más alto siempre es mejor. La misma métrica puede ser buena alta en una medalla (la sesión más larga) y baja en otra (el sprint más rápido).

### ¿Para qué sirve que un hábito esté activo?
- **Decisión:** para filtrar en el panel visual y mostrar solo los activos sin borrar nada.
- **Por qué:** conservar el historial de lo que ya no sigo haciendo.

### ¿Qué fecha tiene una sesión y cuándo puede registrarse?
- **Decisión:** la fecha es un día de calendario, sin hora, que elige el usuario (por defecto hoy). Puede ser pasada, pero no futura ni anterior a la fecha de inicio del hábito: la app la rechaza y, si quiero apuntarla, muevo antes la fecha de inicio a mano. Por lo mismo, la fecha de inicio no puede ser futura ni quedar por detrás de sesiones que ya existen. "Hoy" y el cierre de cada periodo se calculan con la zona horaria del usuario, un ajuste suyo (columna en la tabla de usuarios) con Europe/Madrid por defecto.
- **Por qué:** una sesión futura contaría para medallas y rachas antes de tiempo. Que la app moviera sola la fecha de inicio podría esconder un error al teclear la fecha de una sesión. El servidor de Vercel trabaja en UTC y, sin zona horaria, entre las 00:00 y las 02:00 en España creería que sigue siendo el día anterior. Apuntar de madrugada lo de ayer no rompe rachas porque se calculan al vuelo.

### ¿Qué se puede editar de una métrica, una sesión o una medalla?
- **Decisión:** nada cambia de hábito: se borra y se crea de nuevo. De una métrica, solo el nombre y la unidad. De una medalla, todo menos el tipo y la métrica, y la edición se valida como medalla completa. De una sesión, la fecha, los valores y las etiquetas; los valores y las etiquetas que se envían reemplazan a los anteriores.
- **Por qué:** una sesión lleva valores de las métricas de su hábito, que no tienen equivalente en otro. Cambiar el tipo de una métrica reinterpretaría su historia (10 km pasarían a 10 segundos) y cambiaría sus medallas en silencio. Borrar y crear de nuevo una medalla no pierde nada, porque se recalcula al momento sobre el historial. Reemplazar valores y etiquetas permite quitar uno con solo no enviarlo.

### ¿Qué pasa al borrar una etiqueta?
- **Decisión:** se quita de todas las sesiones. Si la usan medallas (como obligatoria o como excluida), borrarla también borra esas medallas, y el borrado exige antes mostrar cuáles son y confirmar escribiendo el nombre exacto de la etiqueta. Las demás medallas del hábito se recalculan.
- **Por qué:** una medalla con su filtro roto cambiaría de significado en silencio. Es la misma confirmación proporcional que en el resto de borrados. Se recalculan porque las de "solo sesiones sin etiquetas" pueden ganar sesiones.

## Medallas y rachas

### ¿De dónde sale la racha?
- **Decisión:** del objetivo de frecuencia, que es una propiedad del propio hábito, obligatoria desde que se crea. Sustituye a la regla anterior: todo hábito debía tener una medalla de constancia y, si tenía varias, mandaba la de periodo más corto. Cambiar el objetivo es retroactivo: el nuevo juzga todo el historial.
- **Por qué:** garantiza que todo hábito tenga racha y elimina el desempate entre medallas de constancia. Se descartó que el objetivo fuera una medalla especial (reglas propias: única, no borrable y con umbrales obligatorios al crear el hábito). Se descartó guardar un historial de objetivos: si quiero conservar el anterior, creo otro hábito.

### ¿Desde cuándo cuenta la racha?
- **Decisión:** nunca antes de la fecha de inicio del hábito.
- **Por qué:** en un hábito a evitar, un día sin sesiones es un éxito; sin ese límite, la racha recorrería el pasado sin fin (origen del bug 4 del v1).

### ¿Qué valor tiene una medalla de racha?
- **Decisión:** la mejor racha conseguida con su criterio, también en modo evitar. La racha actual se muestra aparte, como su progreso.
- **Por qué:** las medallas reflejan progreso conseguido, que no se pierde al romper la racha, y así se ven las dos cifras.

### ¿Qué es un periodo en las medallas de constancia?
- **Decisión:** siempre periodos naturales de calendario (semana ISO de lunes a domingo, trimestres naturales…), nunca ventanas deslizantes.
- **Por qué:** por recuperar.

### ¿Cuenta el periodo en curso?
- **Decisión:** en la medalla de constancia, el periodo en curso cuenta en cuanto cumple, aunque no haya cerrado. En la racha, si cumple suma ya; si todavía no cumple, ni suma ni rompe; solo rompen los periodos ya cerrados que fallan.
  En modo evitar es al revés: el periodo en curso no suma hasta que se cierra, y si ya se ha pasado del máximo, rompe al momento.
- **Por qué:** no castigar un periodo que aún se puede cumplir. Se descartó romper la racha por "imposibilidad matemática de cumplir el periodo actual": complica la técnica sin necesidad y asumiría como máximo un registro útil al día. En modo evitar, un periodo abierto aún se puede fallar (sumarlo a medianoche sería premiar sin haber hecho nada), y uno que ya ha pasado del máximo no tiene arreglo.

### ¿Dónde se calculan los umbrales sugeridos?
- **Decisión:** en el backend, con un endpoint. Progresión exponencial entre el primer umbral y el de diamante, redondeada a números redondos (1, 2, 3 o 5 por una potencia de 10) mientras sigan en orden; si se repetirían, redondea menos.
- **Por qué:** es Python, se prueba con pytest y lo puedo leer.

## API

### ¿Cómo son las rutas?
- **Decisión:** crear y listar cuelgan del hábito (`/habits/{id}/metrics`); leer, editar y borrar un elemento van directos (`/metrics/{id}`). La vista del día va en `/today`.
- **Por qué:** al crear, el hábito sale de la ruta y ya no se puede cambiar; para un elemento basta su id. `/habits/today` se confundiría con `/habits/{id}`.

### ¿Qué ve cada usuario?
- **Decisión:** solo lo suyo. Lo de otro usuario responde 404, como si no existiera.
- **Por qué:** no revela qué existe, y es la base de la fase 2.

### ¿Qué campos acepta la API?
- **Decisión:** solo los de cada formato: un campo desconocido da 422. En las ediciones, cualquier campo se puede omitir, pero `null` solo se acepta donde tiene sentido (p. ej. quitar la unidad).
- **Por qué:** que un cliente no pueda colar valores que fija el servidor (el nivel de una medalla) ni guardar un `null` que rompa las lecturas (bug 5 del v1).

### ¿Cómo responden los listados anidados?
- **Decisión:** 404 si el padre no existe; lista vacía con 200 si existe pero no tiene hijos.
- **Por qué:** por recuperar.

### ¿Cómo se validan las claves ajenas al crear o modificar?
- **Decisión:** siempre: (1) que cada una exista (404 si no) y (2) que sean coherentes entre sí cuando aplique (400 si no cuadran). En modificaciones parciales se toma el valor nuevo y, si no viene, el actual.
- **Por qué:** por recuperar.

### ¿Qué código devuelve un DELETE?
- **Decisión:** 200 con cuerpo en las sesiones (medallas y racha actualizadas); 204 sin cuerpo en el resto.
- **Por qué:** el frontend necesita saber qué cambió al borrar una sesión.

### ¿Cómo se escriben los POST y los PATCH?
- **Decisión:** el POST asigna campo a campo de forma explícita; el PATCH recorre genéricamente los campos enviados. No cambiar sin motivo nuevo.
- **Por qué:** legibilidad.

### ¿Dónde se capturan los errores?
- **Decisión:** de forma global, no por endpoint: los de integridad de la BBDD devuelven 400, y los de validación, 422 con dónde y por qué, sin repetir el valor enviado.
- **Por qué:** los de integridad, por recuperar. El valor enviado no se repite porque un `NaN` no se puede escribir en JSON y convertía el 422 en un 500.

### ¿Cómo recibe el frontend el efecto de una sesión sobre las medallas y la racha?
- **Decisión:** dentro de la respuesta del POST, el PATCH y el DELETE de sesiones: la sesión, solo las medallas que han cambiado (con su valor y nivel anteriores) y la racha y la mejor racha. Las que suben solas con los días (modo evitar) llegan en la vista del día.
- **Por qué:** el front celebra al instante con una sola respuesta, animando la barra desde donde estaba.

### ¿Cuándo se calcula el progreso de una medalla ("3/7")?
- **Decisión:** en las de constancia y racha (estas, con la racha actual), cada vez que se devuelve una medalla: al leerla, al crearla y al editarla. Nunca se guarda.
- **Por qué:** no se guarda, así que se calcula al pedirlo; al crear o editar, el front recibe la medalla completa sin pedirla otra vez.

### ¿Se agrupan los endpoints en Swagger?
- **Decisión:** no. Todo aparece bajo "default".
- **Por qué:** es cosmético; se decidió no arreglarlo.

## Código

### ¿Dónde va cada función?
- **Decisión:** si conoce reglas de negocio, va en el archivo de su dominio aunque no "calcule" en sentido estricto; si es una herramienta ciega y reutilizable, va en las utilidades.
- **Por qué:** por recuperar.

### ¿Cómo se llama una sesión en el código?
- **Decisión:** `Entry` (tablas `entries`, `entry_values` y `entry_tags`). En la API y en el front se sigue llamando sesión.
- **Por qué:** en el código, "session" ya significa dos cosas: la conexión a la BBDD (SQLAlchemy) y la sesión de login.
