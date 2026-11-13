# Qué hay en este archivo y cómo usarlo
- **Contiene:** en qué punto estamos respecto a las fases del proyecto, por dónde empezar la próxima sesión y lo pendiente para más adelante.
- **No contiene:** cifras, nombres de archivos, detalles de lo hecho ni decisiones ya cerradas.
- **Se actualiza:** al cerrar cada sesión.

## Próxima sesión
**Bloque 1 del plan de mejoras** (quick wins), en su rama. Antes de empezar, cerrar las dos decisiones de "Revisión" de más abajo. La revisión completa del proyecto se hizo el 12 nov 2026 y de ella sale el plan; quedaron sin hacer la prueba de la API de punta a punta contra la rama `dev` de Neon y el linter (plan, 3.7).

## Sesión siguiente
**Entrevista de front** (bloque 5): diseño del frontend en conjunto y arranque. En ella se cierran los puntos 2.1 y 2.2 del plan, que cambian lo que la API le devuelve al front.

## Fases
- [x] Backend v1: CRUD de las cuatro entidades, los cuatro tipos de medalla, recálculo síncrono, rachas y cascada.
- [x] Entrevista de diseño, salvo el bloque 5.
- [x] Rediseño del backend según la entrevista.
- [ ] Frontend, empezando por la entrevista de front (bloque 5).
- [ ] Despliegue (entra en el MVP).

## Qué funciona
Backend rediseñado, con sus casos cubiertos por los tests y probado también contra Postgres (27 oct 2026):
- Login con sesión que se renueva sola mientras uso la app, bloqueo tras fallos seguidos y cada usuario viendo solo lo suyo.
- Hábitos, métricas (número, duración y ritmo), etiquetas, sesiones y los cinco tipos de medalla, con modo evitar y filtros de etiquetas.
- Recálculo de medallas al escribir y al leer, racha y mejor racha, progreso del periodo en curso y umbrales sugeridos.
- Vista del día y exportar.
- Migración aplicada en la rama `dev` de Neon, con mi usuario creado.

## Plan de mejoras
Sale de la revisión del 12 nov 2026. Tres bloques, en este orden, cada uno en su rama. Cuando un punto se termina, se quita de aquí.

### Bloque 1: quick wins (fáciles y aportan)
- **1.1 Integración continua.**
  - Por qué: los tests solo se pasan a mano y el de migraciones se salta siempre en local. Lo que venga después queda protegido.
  - Cómo: un workflow de GitHub Actions que pase los tests en cada push, en SQLite y contra un Postgres de usar y tirar, con un mínimo de cobertura.
- **1.2 Suma con decimales.**
  - Por qué: una suma con decimales puede quedarse una milésima por debajo del umbral y dejar la medalla sin subir. Es el único fallo que da un resultado incorrecto en el uso normal. Los ritmos tienen el mismo problema.
  - Cómo: redondear la suma de las históricas y el valor de los ritmos con el limpiador de decimales que ya usan los umbrales sugeridos, y un test del caso.
- **1.3 Prefijo `/api` en todas las rutas.**
  - Por qué: front y API compartirán dirección, y la vista del día sería a la vez pantalla y endpoint. Ahora es una línea por router; con el front escrito, más caro.
  - Cómo: registrar los routers con el prefijo y usar la misma base en el cliente de los tests.
- **1.4 Errores legibles.**
  - Por qué: algunas respuestas devuelven el texto crudo de la BBDD, que el front no puede mostrar ni interpretar.
  - Cómo: validar el hábito editado entero, como ya se hace con las medallas, y traducir cada restricción de la BBDD a un mensaje con código estable, con un código de respuesta propio para los nombres repetidos.
- **1.5 Umbrales enteros en las medallas de conteo.**
  - Por qué: en rangos estrechos, los umbrales sugeridos salen con decimales para cosas que se cuentan en sesiones o periodos.
  - Cómo: una opción en los umbrales sugeridos que redondee a enteros y rechace el rango si no caben cinco distintos, y exigir enteros al crear o editar medallas de conteo.
- **1.6 Datos de prueba.**
  - Por qué: el front necesita hábitos con meses de historial para verse con datos reales, y el test de regresión (2.6) usa el mismo dato.
  - Cómo: un script que cree en la rama `dev` un par de hábitos con métricas, etiquetas, medallas y sesiones.

### Bloque 2: hard wins (difíciles pero aportan mucho)
- **2.1 Celebración que no se pierde.** Se cierra en la entrevista de front.
  - Por qué: si se abre la vista de medallas antes que la del día, o la respuesta no llega al móvil, la subida de una medalla no se celebra nunca.
  - Cómo: guardar en cada medalla el último nivel celebrado (con migración) y un endpoint con el que el front confirma que la ha mostrado; hasta entonces, la subida queda pendiente.
- **2.2 Registrar sin duplicados.** Se cierra en la entrevista de front.
  - Por qué: con mala cobertura, un reintento crea dos sesiones, y el servidor no lo distingue de dos sesiones de verdad.
  - Cómo: que el front genere el identificador de la sesión y lo envíe; si ya existe, la API devuelve la sesión existente.
- **2.3 Copia de seguridad automática.** Al desplegar.
  - Por qué: Neon gratis guarda solo unas horas de historial y exportar es manual: un borrado por error no tendría vuelta atrás.
  - Cómo: un workflow semanal que vuelque la BBDD de producción, cifrada, y probar una restauración una vez en una rama de Neon.
- **2.4 Migraciones de producción.** Al desplegar.
  - Por qué: no está definido quién aplica las migraciones en producción; el día que se olvide, la app desplegada falla.
  - Cómo: un paso en el workflow de `main`, tras los tests, con la conexión guardada como secreto de GitHub.
- **2.5 Consultas en una pasada.**
  - Por qué: la vista del día y la de medallas hacen varias consultas por cada hábito, y son las que se abren a diario.
  - Cómo: primero medirlo contra la rama `dev` de Neon; si pesa, cargar el historial y las medallas de todos los hábitos de una vez.
- **2.6 Tests de regresión y con datos aleatorios.**
  - Por qué: un cambio en las reglas de medallas o rachas puede alterar resultados sin que ningún test lo note.
  - Cómo: un export fijo con las medallas que debe dar, y tests con datos aleatorios en periodos, rachas y umbrales.
- **2.7 Lógica fuera de los routers.** Junto a 2.1 y 2.2.
  - Por qué: los routers de sesiones y medallas llevan reglas de negocio, y 2.1 y 2.2 tocan justo esas funciones.
  - Cómo: moverlas a los servicios, como ya está hecho con las etiquetas.

### Bloque 3: quick fixes (aportan poco, pero hay que hacerlos y son rápidos)
- **3.1 Error del servidor en los umbrales sugeridos.**
  - Por qué: un valor infinito provoca un error interno en vez de un rechazo.
  - Cómo: rechazar infinitos y no-números en los parámetros de entrada.
- **3.2 Valores negativos.**
  - Por qué: una duración negativa se acepta y resta en las medallas.
  - Cómo: no admitir duraciones negativas (las métricas de número, según la decisión abierta).
- **3.3 Histórica sobre un ritmo.**
  - Por qué: se puede crear una medalla que suma ritmos, que no significa nada.
  - Cómo: rechazarla al crear la medalla.
- **3.4 Documentación de la API cerrada en producción.** Al desplegar.
  - Por qué: la documentación automática enseña toda la API sin iniciar sesión.
  - Cómo: una variable de entorno que la apague en Vercel.
- **3.5 Conexiones en serverless.** Al desplegar.
  - Por qué: el motor guarda conexiones abiertas en cada instancia, mala combinación con funciones serverless y el pooling de Neon.
  - Cómo: no guardar conexiones en producción y comprobar que el driver funciona con el pooling.
- **3.6 Limpieza.**
  - Por qué: código que no se usa o está duplicado.
  - Cómo: quitar una relación entre tablas que no se usa, que los tests usen la sesión de BBDD real de la app en vez de una copia, y separar las reglas de las medallas de los formatos de la API.
- **3.7 Lo que quedó sin verificar en la revisión.**
  - Por qué: no se pudo pasar el linter ni probar contra la rama `dev` de Neon.
  - Cómo: añadir el linter a las dependencias de desarrollo y a la integración continua, y hacer la prueba de punta a punta junto con la medición de 2.5.
- **3.8 README y etiqueta de versión.**
  - Por qué: el README hará falta para montar un clon a alguien; la etiqueta marca qué código está desplegado.
  - Cómo: un README corto con los pasos de instalación y una etiqueta de git en el primer despliegue.

## Pendiente para más adelante

### Tareas
- **Frontend**: confirmaciones de borrado (ver `CONTEXTO.md`).
- **Al desplegar**: crear mi usuario en la rama `production` de Neon; usar en Vercel la conexión con pooling de Neon; poner las funciones de Vercel en Frankfurt, junto a Neon; dejar los tests fuera de lo que se despliega; configurar las variables de entorno en Vercel. Además, los puntos del plan marcados "al desplegar".
- **Fase 2, prioridad**: el bloqueo del login es por usuario, así que quien conozca un nombre de usuario puede tenerlo bloqueado a base de fallos. Añadir otra defensa (p. ej. límite por IP) antes de abrir la app a más gente.

### Decisiones abiertas
Revisión (antes de empezar el plan):
- Histórica con "menor es mejor": al ser una suma, empieza en diamante y solo puede bajar. ¿Se queda así o se prohíbe?
- ¿Puede ser negativa una métrica de número? (plan, 3.2)

Frontend (bloque 5, al empezar el frontend):
- Pantallas, diseño visual y retroalimentación visual (animaciones; ¿vibración o sonido?). Hay un esqueleto propuesto por Claude: Hoy, Registrar, Medallas, Detalle del hábito y Configuración.
- Cómo se muestra la mejor racha.
- Framework del frontend.
- Fecha por defecto al registrar de madrugada: ¿que el día empiece a las 4:00, para que a la 1:00 aparezca ayer?
- Celebración de las medallas que suben solas (modo evitar): hoy las avisa la vista del día al abrirla; si se abriera antes la de medallas, el aviso se perdería. Propuesta en el plan, 2.1.
- Reintentos al registrar con mala cobertura: hoy duplican la sesión. Propuesta en el plan, 2.2.
- Cómo se eligen los filtros de etiquetas al crear una medalla. Idea: "¿qué sesiones cuentan? Todas / con estas etiquetas / sin estas / sin ninguna".

Fase 2:
- Implicaciones legales de guardar datos de otros, antes de abrir la app fuera de familia y amigos cercanos.

## Pendiente de probar yo
Nada.
