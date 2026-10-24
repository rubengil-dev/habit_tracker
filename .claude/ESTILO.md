# Qué hay en este archivo y cómo usarlo
- **Contiene:** cómo me gusta el código a nivel general
- **No contiene:** cómo trabajamos ni la estructura concreta del proyecto.
- **Se actualiza:** cuando cambio una preferencia de estilo.

## Idioma
- Código, variables, docstrings y comentarios en inglés.

## Docstrings
- Siempre al principio de cada archivo y de cada función.
- Docstring del archivo: las comillas `"""` siempre en su propia línea.
- Docstring de función: si cabe en una línea, comillas y texto en la misma línea; si necesita más, las comillas en su propia línea y el texto entre ellas.
- Una frase corta de título; si hace falta detalle, termina en dos puntos y debajo van líneas sangradas, con guiones si hay varias cosas.
- Nada de párrafos ni explicaciones largas: qué hace, no cómo ni por qué.
- Para indicar transformaciones o flujos, flechas: `→`. Solo en docstrings y comentarios: en los `print`, la consola de Windows no la muestra.

```python
"""
Helpers to download files:
    - Retries
    - No half-written files
"""

def cycle_label(year):
    """
    Cycle name creator:
        Example: 1999 → '1999_2000'
    """


def run():
    """Bronze step, called from main."""
```

## Comentarios
- Títulos de bloque de una o pocas palabras: `# Imports`, `# Root`, `# Data layers`.
- Sin comentarios al final de la línea, salvo para aclarar algo no evidente: unidades (`# seconds`), ejemplos o el significado de cada fila de una tabla de configuración.
- Si el código necesita un comentario largo para entenderse, mejor un nombre de función más claro.

## Imports
- Bajo un único título `# Imports`, sin subclasificar.
- Una línea en blanco entre librerías externas e imports del propio proyecto.
- Cada archivo importa solo lo que usa. Nada de archivos comunes de imports.

## Funciones y archivos
- Cada archivo hace una sola cosa y su docstring lo dice.
- La función principal del archivo va arriba del todo y se lee como un índice: pocas líneas, solo llamadas a funciones con nombre claro.
- Las funciones de apoyo van debajo, en el orden en que se llaman. Se crean aunque se usen una sola vez, para darle nombre a cada paso.
- Nombres descriptivos en `snake_case`.

Ejemplo (paso de descarga de este proyecto; los cuerpos de las funciones de apoyo, docstrings incluidos, se omiten con `...`):

```python
def run():
    """Bronze step, called from main."""
    BRONZE.mkdir(parents=True, exist_ok=True)
    jobs = build_jobs()
    failed = download_all(jobs)
    write_manifest(jobs)
    print_summary(jobs, failed)


def build_jobs():
    ...


def download_all(jobs):
    ...


def write_manifest(jobs):
    ...


def print_summary(jobs, failed):
    ...
```

## Organización
- Configuración separada de la lógica: rutas internas en un archivo, fuentes externas (URLs, listas de ficheros, ajustes) en otro.
- Funciones compartidas en una carpeta de utilidades, un archivo por tema. Una función sale ahí cuando no es específica del archivo que la usa.
- Un único punto de entrada por programa (un `main`), y es el único con `if __name__ == "__main__":`. El resto de archivos solo definen funciones.
- Carpetas de etapas numeradas para que el orden alfabético sea el del proceso: `01_bronze`, `02_silver`…
- Las tablas de configuración escritas a mano se alinean en columnas para que se lean como una tabla.

## Simplicidad
- Cada complicación tiene que responder a un problema real. Si no, fuera.