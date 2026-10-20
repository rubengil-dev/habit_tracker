# Qué hay en este archivo y cómo usarlo
- **Contiene:** qué es el proyecto, por qué y para qué: la idea, el usuario, cómo debe ser la experiencia, cómo se va a construir a grandes rasgos y las restricciones.
- **No contiene:** nombres de carpetas, archivos ni variables, detalles técnicos, decisiones técnicas o metodológicas ni lo pendiente.
- **Se actualiza:** solo si yo lo pido, porque cambie la idea o el diseño del producto.

## Qué es
Un habit tracker personal, para un solo usuario (yo), donde los hábitos se convierten en medallas que suben de nivel, al estilo de las medallas de Pokémon GO.

Por qué existe y qué quiero conseguir con él: por definir en la entrevista.

## El producto

### Cómo se organiza lo que registro
- Un **hábito** (p. ej. correr) tiene una o varias **métricas** (p. ej. kilómetros, ritmo).
- Cada día registro **valores** de una métrica con su fecha. Varios registros el mismo día cuentan por separado.
- Una métrica puede ser **calculada** a partir de otras del mismo hábito (p. ej. el ritmo a partir de tiempo y distancia), en vez de registrarse a mano.
- De cada métrica cuelgan una o varias **medallas**. Un hábito puede estar **activo** o no: así se oculta lo que ya no sigo sin borrar su historia.
- Todo es configurable por el usuario: no hay hábitos ni medallas prefijados en la app.

### Las medallas
Cada medalla tiene seis estados: bloqueada → desbloqueada → bronce → plata → oro → diamante. Los umbrales de cada nivel los pongo yo. Hay cuatro tipos:
- **Histórica:** suma de todo lo registrado ("has corrido 157 km").
- **Récord:** la mejor marca de un solo registro ("tu mejor ritmo es 4'56''").
- **Objetivo:** cuántas veces has cumplido un listón ("correr 10 km o más de una vez").
- **Constancia:** en cuántos periodos de calendario (día, semana, mes, trimestre, semestre o año) has cumplido un mínimo de veces ("leer cada día de la semana").

En las medallas de histórica y récord, lo mejor puede ser lo más alto (distancia) o lo más bajo (ritmo). En objetivo y constancia el nivel siempre sube con el número de veces o periodos cumplidos.

### Rachas
La **racha** de un hábito es cuántos periodos seguidos llevo cumpliendo su medalla de constancia, contando hacia atrás desde el actual. Las medallas de constancia también muestran su progreso en el periodo en curso (p. ej. "3/7").

## Experiencia de usuario
Dos vistas:
- **Registro diario:** donde anoto los valores del día.
- **Medallas:** filtrable, con las medallas como círculos con una barra de progreso animada que cambia de color al subir de nivel.

Borrar un hábito o una métrica arrastra todo lo que cuelga de él, así que el borrado pide confirmación proporcional a lo que se pierde: el hábito, escribiendo su nombre exacto; la métrica, con un aviso simple; la medalla, sin aviso.

Se usa desde el móvil y desde el portátil.

### Diseño visual
Por definir; el detalle de las dos vistas queda pendiente hasta hacer el frontend.

## Cómo se construye
1. **Backend:** una API REST propia que guarda los datos y calcula medallas y rachas. Ya construido (pendiente de pulir, ver `ESTADO.md`).
2. **Frontend:** una app aparte que consume esa API. No sé frontend, así que lo construye Claude.
3. **Despliegue:** accesible desde el móvil y el portátil, instalable si es posible como app web.

## Visión futura
- Creación de hábitos asistida por IA. Es utópico y no debe condicionar el desarrollo actual.
- Migrar a la app los datos de hábitos que hoy llevo en Notion. Detalles por definir.

## Restricciones
- Un solo usuario.
- Hosting gratuito.
- Mantenimiento mínimo: sin servidor que gestionar.
