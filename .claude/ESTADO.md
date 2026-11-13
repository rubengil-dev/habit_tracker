# Qué hay en este archivo y cómo usarlo
- **Contiene:** en qué punto estamos respecto a las fases del proyecto, por dónde empezar la próxima sesión y lo pendiente para más adelante.
- **No contiene:** cifras, nombres de archivos, detalles de lo hecho ni decisiones ya cerradas.
- **Se actualiza:** al cerrar cada sesión.

## Próxima sesión
**Probar contra la rama `dev` de Neon**: aplicar yo la migración nueva (sin negativos e histórica siempre ascendente) y ejecutar el script de datos de prueba (pide teclear `dev` y la contraseña del usuario `demo`); después, prueba de la API de punta a punta con esos datos y medición de las consultas (3.7 y 2.5).

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
- Todas las rutas bajo `/api`, y todos los errores con un código fijo para el front.
- Integración continua en cada push (linter, tests en SQLite y en Postgres), con tests de regresión sobre los datos de prueba y tests con datos aleatorios en periodos, rachas y umbrales.
- Sin valores negativos, histórica siempre ascendente y sin histórica sobre un ritmo.
- Migración inicial aplicada en la rama `dev` de Neon, con mi usuario creado (la segunda, pendiente).

## Plan de mejoras
Sale de la revisión del 12 nov 2026. Tres bloques, en este orden, cada uno en su rama. Cuando un punto se termina, se quita de aquí. Hechos: el bloque 1 (quick wins), el 2.6 y, del bloque 3, el 3.1, 3.2, 3.3 y 3.6.

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
- **2.7 Lógica fuera de los routers.** Junto a 2.1 y 2.2.
  - Por qué: los routers de sesiones y medallas llevan reglas de negocio, y 2.1 y 2.2 tocan justo esas funciones.
  - Cómo: moverlas a los servicios, como ya está hecho con las etiquetas.

### Bloque 3: quick fixes (aportan poco, pero hay que hacerlos y son rápidos)
- **3.4 Documentación de la API cerrada en producción.** Al desplegar.
  - Por qué: la documentación automática enseña toda la API sin iniciar sesión.
  - Cómo: una variable de entorno que la apague en Vercel.
- **3.5 Conexiones en serverless.** Al desplegar.
  - Por qué: el motor guarda conexiones abiertas en cada instancia, mala combinación con funciones serverless y el pooling de Neon.
  - Cómo: no guardar conexiones en producción y comprobar que el driver funciona con el pooling.
- **3.7 Prueba de punta a punta contra la rama `dev` de Neon.**
  - Por qué: quedó sin hacer en la revisión; los tests usan SQLite y un Postgres local, no Neon.
  - Cómo: con los datos del script de prueba, recorrer la API con el usuario `demo`, junto con la medición de 2.5.
- **3.8 README y etiqueta de versión.**
  - Por qué: el README hará falta para montar un clon a alguien; la etiqueta marca qué código está desplegado.
  - Cómo: un README corto con los pasos de instalación y una etiqueta de git en el primer despliegue.

## Pendiente para más adelante

### Tareas
- **Frontend**: confirmaciones de borrado (ver `CONTEXTO.md`).
- **Al desplegar**: crear mi usuario en la rama `production` de Neon; usar en Vercel la conexión con pooling de Neon; poner las funciones de Vercel en Frankfurt, junto a Neon; dejar los tests fuera de lo que se despliega; configurar las variables de entorno en Vercel. Además, los puntos del plan marcados "al desplegar".
- **Fase 2, prioridad**: el bloqueo del login es por usuario, así que quien conozca un nombre de usuario puede tenerlo bloqueado a base de fallos. Añadir otra defensa (p. ej. límite por IP) antes de abrir la app a más gente.

### Decisiones abiertas
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
- La migración nueva en la rama `dev` de Neon (`uv run alembic upgrade head`): falla si ya hay algún valor negativo o alguna histórica con "menor es mejor".
