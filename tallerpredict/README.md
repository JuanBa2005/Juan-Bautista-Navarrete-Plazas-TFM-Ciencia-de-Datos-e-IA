# Taller Predict

Este paquete contiene los datos ya preparados, en siete CSV, y dos scripts SQL: uno crea el esquema y otro importa los CSV.

## Estructura

- `sql/`: `esquema_taller_postgresql.sql`, `datos_taller.sql`.
- `datos/`: `vehicles.csv`, `repair_types.csv`, `parts.csv`, `work_orders.csv`, `repair_events.csv`, `part_usage.csv` e `inventory_movements.csv`.
- `validacion_datos_taller.json`: resumen de validación original, sin modificaciones.

## Importación (PostgreSQL, con `psql`)

1. Abre una terminal **en la carpeta `tallerpredict`** (la que contiene `sql/`, `datos/` y `validacion_datos_taller.json`).
2. Crea la base de datos si no existe (por ejemplo, `createdb -U postgres taller_predict`).
3. Ejecuta:

```bash
psql -X -v ON_ERROR_STOP=1 -U postgres -d taller_predict -f sql/esquema_taller_postgresql.sql
psql -X -v ON_ERROR_STOP=1 -U postgres -d taller_predict -f sql/datos_taller.sql
```

**Importante:** `\copy` es una orden del cliente `psql`, no una sentencia SQL estándar; no funcionará pegándola en el editor de consultas de pgAdmin. Las rutas `datos/*.csv` se resuelven respecto del directorio desde el que ejecutas `psql`. `\copy` lee los archivos desde tu ordenador y no requiere privilegios de superusuario ni acceso del servidor a la carpeta. Se ejecuta sobre **tablas vacías**: repetir la importación sobre las mismas tablas dará errores de claves únicas/primarias.

Los CSV incluyen `id` y el mecanismo `COPY FROM` de PostgreSQL acepta los valores explícitos de una columna `GENERATED ALWAYS AS IDENTITY`; el script sincroniza después las secuencias para futuras inserciones. Todas las cargas y las verificaciones de cantidad se ejecutan dentro de una sola transacción.

Si la base de datos usa otro esquema en vez de `public`, adapta los prefijos `public.` del SQL de carga.
