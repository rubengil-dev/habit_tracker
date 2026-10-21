# Qué hay en este archivo y cómo usarlo
- **Contiene:** qué es el proyecto, por qué y para qué: la idea, el usuario, cómo debe ser la experiencia, cómo se va a construir a grandes rasgos y las restricciones.
- **No contiene:** nombres de carpetas, archivos ni variables, detalles técnicos, decisiones técnicas o metodológicas ni lo pendiente.
- **Se actualiza:** solo si yo lo pido, porque cambie la idea o el diseño del producto.

## Qué es
Un habit tracker personal donde los hábitos se convierten en medallas que suben de nivel. Cada hábito es un reto visto desde varios ángulos (volumen, velocidad, frecuencia...), y sus medallas reflejan el progreso en cada uno y a la vez se convierten en pequeños desafíos.

## Por qué existe
- Ya llevo mis hábitos en Notion, pero apuntarlos se ha convertido en un hábito más: cuesta y no da nada a cambio, sin gamificación ni respuesta inmediata al cumplir algo. Por eso lo he dejado y retomado varias veces.
- Esta app existe para que registrar sea gratificante: un minijuego en el que voy progresando. Tener todo en un sitio no es el objetivo (para eso ya está Notion). Las estadísticas suman, pero no mandan.
- Al principio también servía para aprender FastAPI. Ya no es un objetivo: lo que me interesa ahora es saber qué quiero y dirigir bien a la IA.
- Meta: empezar a usarla cuanto antes, y como muy tarde el 1 de enero de 2027.

## Para quién
- El MVP es solo para mí. No quiero tener ni gestionar datos de nadie más.
- Queda la puerta abierta a una fase 2 con más usuarios (primero familia y amigos cercanos), cada uno viendo solo lo suyo. Antes de abrirla a gente fuera de ese círculo hay que resolver las implicaciones legales de guardar datos de otros.
- Mientras tanto, a quien la quiera se le puede montar una copia propia que gestione esa persona. Que no reciba mis actualizaciones no es un problema.

## El producto

### Cómo se organiza lo que registro
- Un **hábito** tiene cero, una o varias **métricas** (p. ej. correr: distancia, tiempo y ritmo).
- Cada vez que hago un hábito registro una **sesión** con su fecha. Varias sesiones el mismo día cuentan por separado: dos carreras son dos sesiones.
- Dentro de la sesión relleno los **valores** de sus métricas, todos opcionales. Una sesión sin valores es un simple "lo he hecho": así funcionan los hábitos de sí/no (gimnasio, crochet).
- Las métricas son de **número** (km, páginas) o de **duración** (se introduce con un selector de minutos y segundos).
- Una métrica puede ser **calculada** a partir de otras dos del mismo hábito, según un tipo predefinido. De momento hay uno solo, el **ritmo** (A ÷ B: ritmo de carrera, velocidad lectora...). No se rellena a mano, queda vacía si falta alguno de los dos datos y, al crearla en un hábito con historia, se calcula para todas sus sesiones anteriores.
- Cada hábito define sus **etiquetas** (p. ej. lluvia, cansado, molestias) y cada sesión puede llevar varias. Se eligen de la lista, no se escriben, para poder usarlas después en estadísticas.
- Todo hábito tiene un **objetivo** de frecuencia desde que se crea (p. ej. 3 veces por semana, o como máximo 0 al día si es un hábito a evitar). De él sale la racha.
- Un hábito puede estar **activo** o no: así se oculta lo que ya no sigo sin borrar su historia.
- Todo es configurable por el usuario: no hay hábitos ni medallas prefijados en la app.

### Las medallas
Cada medalla pertenece a un hábito y tiene seis estados: bloqueada → desbloqueada → bronce → plata → oro → diamante. Hay cuatro tipos:
- **Histórica:** suma de una métrica ("has corrido 157 km") o número de sesiones ("100 días de gimnasio").
- **Récord:** la mejor marca de una métrica en una sola sesión ("tu mejor ritmo es 4'56''").
- **Objetivo:** cuántas sesiones han cumplido un listón de una métrica ("correr 10 km o más").
- **Constancia:** en cuántos periodos de calendario (día, semana, mes, trimestre, semestre o año) has cumplido un mínimo de sesiones ("leer cada día de la semana") o, en los hábitos a evitar, no has pasado de un máximo ("30 días limpio").

Cualquier medalla puede limitarse a las sesiones con una etiqueta (p. ej. récord de ritmo solo en sesiones de "correr").

En histórica y récord, lo mejor puede ser lo más alto (distancia) o lo más bajo (ritmo, tiempo en 100 m). En objetivo y constancia el nivel siempre sube con el número de veces o periodos cumplidos.

Al crear una medalla pongo el umbral de la primera y el de diamante, y la app propone los intermedios con una progresión exponencial redondeada (p. ej. 100, 500, 3.000, 20.000 y 100.000 km). Los reviso antes de guardar y siempre puedo editarlos a mano.

### Rachas
La **racha** de un hábito es cuántos periodos seguidos llevo cumpliendo su objetivo, contando hacia atrás desde el actual. No hay comodines: si un día no lo he hecho, no lo he hecho. Las medallas de constancia también muestran su progreso en el periodo en curso (p. ej. "3/7").

## Experiencia de usuario
- Registrar tiene que costar poco (pocos toques) y dar algo a cambio al momento: retroalimentación visual intensa, con animaciones al registrar y al cruzar umbrales y el progreso ganado a la vista. El detalle se define al diseñar el frontend.
- Inicio sesión una vez y la app me recuerda: pulso el icono del móvil y entro directo.
- Dos vistas:
  - **Registro diario:** lista todos los hábitos activos con su estado (hechos, pendientes y, en los de evitar, algo como "7 días limpios"), para que no se me olvide ninguno aunque lleve días sin registrarlo. No registrar también es registrar.
  - **Medallas:** filtrable, con las medallas como círculos con una barra de progreso animada que cambia de color al subir de nivel.
- Los días sin sesión se ven vacíos en el historial, como una casilla sin marcar.
- Borrar un hábito o una métrica arrastra todo lo que cuelga de él, así que el borrado pide confirmación proporcional a lo que se pierde: el hábito, escribiendo su nombre exacto; la métrica, con un aviso simple; la medalla, sin aviso.
- Puedo exportar todos mis datos a un archivo, como copia de seguridad.
- Se usa desde el móvil (sobre todo Android; en iPhone también funciona, instalándola desde Safari) y desde el portátil.

### Diseño visual
Por definir; el detalle de las dos vistas queda pendiente hasta hacer el frontend.

## Cómo se construye
1. **Backend:** una API propia que guarda los datos y calcula medallas y rachas. Hay una primera versión que sirve de punto de partida y se rediseña con lo decidido en la entrevista de diseño.
2. **Frontend:** una app web instalable que consume esa API. No sé frontend, así que lo construye Claude.
3. **Despliegue:** entra en el MVP, porque registrar desde el móvil es lo que hace que apuntar cueste poco.

## Visión futura
- Fase 2: abrir la app a más usuarios (ver "Para quién").
- Estadísticas avanzadas y detalladas, filtrables por etiquetas.
- Importar datos desde un archivo: para pasar de una copia propia a la app central y para traer el histórico de Notion (un día por página y un checkbox por hábito; cada casilla marcada sería una sesión sin valores). Opcional.
- Creación de hábitos asistida por IA. Es utópico y no debe condicionar el desarrollo actual.

## Restricciones
- Hosting gratuito.
- Mantenimiento mínimo: sin servidor que gestionar.
