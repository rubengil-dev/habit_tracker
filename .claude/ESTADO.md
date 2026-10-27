# Qué hay en este archivo y cómo usarlo
- **Contiene:** en qué punto estamos respecto a las fases del proyecto, por dónde empezar la próxima sesión y lo pendiente para más adelante.
- **No contiene:** cifras, nombres de archivos, detalles de lo hecho ni decisiones ya cerradas.
- **Se actualiza:** al cerrar cada sesión.

## Próxima sesión
**Revisión completa del proyecto**: toca según `PAUTAS.md` (la última fue el 15 oct) y el backend es nuevo entero. Incluye probar la API de punta a punta contra la rama `dev` de Neon. Lo que salga se arregla en la misma sesión; si no sale nada, la sesión es breve y se cierra ahí.

## Sesión siguiente
**Entrevista de front** (bloque 5): diseño del frontend en conjunto y arranque.

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

## Pendiente para más adelante

### Tareas
- **Frontend**: confirmaciones de borrado (ver `CONTEXTO.md`).
- **Al desplegar**: crear mi usuario en la rama `production` de Neon; usar en Vercel la conexión con pooling de Neon; poner las funciones de Vercel en Frankfurt, junto a Neon; dejar los tests fuera de lo que se despliega; configurar las variables de entorno en Vercel.
- **Fase 2, prioridad**: el bloqueo del login es por usuario, así que quien conozca un nombre de usuario puede tenerlo bloqueado a base de fallos. Añadir otra defensa (p. ej. límite por IP) antes de abrir la app a más gente.

### Decisiones abiertas
Frontend (bloque 5, al empezar el frontend):
- Pantallas, diseño visual y retroalimentación visual (animaciones; ¿vibración o sonido?). Hay un esqueleto propuesto por Claude: Hoy, Registrar, Medallas, Detalle del hábito y Configuración.
- Cómo se muestra la mejor racha.
- Framework del frontend.
- Fecha por defecto al registrar de madrugada: ¿que el día empiece a las 4:00, para que a la 1:00 aparezca ayer?
- Celebración de las medallas que suben solas (modo evitar): hoy las avisa la vista del día al abrirla; si se abriera antes la de medallas, el aviso se perdería.
- Cómo se eligen los filtros de etiquetas al crear una medalla. Idea: "¿qué sesiones cuentan? Todas / con estas etiquetas / sin estas / sin ninguna".

Fase 2:
- Implicaciones legales de guardar datos de otros, antes de abrir la app fuera de familia y amigos cercanos.

## Pendiente de probar yo
Nada.
