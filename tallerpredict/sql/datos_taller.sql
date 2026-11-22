-- Carga de datos del taller desde archivos CSV.
-- Ejecutar con psql desde la raíz del proyecto tallerpredict/ (carpeta datos/).
-- Ejemplo: psql -X -v ON_ERROR_STOP=1 -U postgres -d taller_predict -f datos_taller.sql
-- Requiere haber ejecutado esquema_taller_postgresql.sql y disponer de tablas vacías.
-- Los CSV originales contienen la columna id. COPY admite sus valores explícitos incluso con IDENTITY ALWAYS.
-- Las rutas de \copy son relativas al directorio de trabajo de psql, NO a la ubicación del script.
-- No ejecutar este archivo en pgAdmin Query Tool: \copy es una instrucción del cliente psql.
\set ON_ERROR_STOP on
BEGIN;
SET LOCAL client_encoding = 'UTF8';

-- vehicles (150 registros)
\copy public.vehicles ("id", "vehicle_key", "brand", "model", "displacement_cc", "fuel", "manufacture_year") FROM 'datos/vehicles.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', NULL '', ENCODING 'UTF8');
SELECT setval(pg_get_serial_sequence('public.vehicles', 'id'), (SELECT MAX(id) FROM public.vehicles), true);

-- repair_types (25 registros)
\copy public.repair_types ("id", "name") FROM 'datos/repair_types.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', NULL '', ENCODING 'UTF8');
SELECT setval(pg_get_serial_sequence('public.repair_types', 'id'), (SELECT MAX(id) FROM public.repair_types), true);

-- parts (80 registros)
\copy public.parts ("id", "part_code", "name", "unit", "unit_cost", "supplier_lead_days") FROM 'datos/parts.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', NULL '', ENCODING 'UTF8');
SELECT setval(pg_get_serial_sequence('public.parts', 'id'), (SELECT MAX(id) FROM public.parts), true);

-- work_orders (1160 registros)
\copy public.work_orders ("id", "order_key", "vehicle_id", "entry_at", "exit_at") FROM 'datos/work_orders.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', NULL '', ENCODING 'UTF8');
SELECT setval(pg_get_serial_sequence('public.work_orders', 'id'), (SELECT MAX(id) FROM public.work_orders), true);

-- repair_events (1617 registros)
\copy public.repair_events ("id", "repair_key", "order_id", "repair_type_id", "performed_at") FROM 'datos/repair_events.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', NULL '', ENCODING 'UTF8');
SELECT setval(pg_get_serial_sequence('public.repair_events', 'id'), (SELECT MAX(id) FROM public.repair_events), true);

-- part_usage (2344 registros)
\copy public.part_usage ("id", "repair_event_id", "part_id", "quantity") FROM 'datos/part_usage.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', NULL '', ENCODING 'UTF8');
SELECT setval(pg_get_serial_sequence('public.part_usage', 'id'), (SELECT MAX(id) FROM public.part_usage), true);

-- inventory_movements (3206 registros)
\copy public.inventory_movements ("id", "movement_key", "part_id", "movement_at", "quantity_delta", "movement_type", "repair_event_id", "notes") FROM 'datos/inventory_movements.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', NULL '', ENCODING 'UTF8');
SELECT setval(pg_get_serial_sequence('public.inventory_movements', 'id'), (SELECT MAX(id) FROM public.inventory_movements), true);

-- Validar las cantidades antes de confirmar la transacción.
DO $validacion$
BEGIN
  IF (SELECT COUNT(*) FROM public.vehicles) <> 150 THEN
    RAISE EXCEPTION 'Número inesperado de filas en vehicles';
  END IF;
  IF (SELECT COUNT(*) FROM public.repair_types) <> 25 THEN
    RAISE EXCEPTION 'Número inesperado de filas en repair_types';
  END IF;
  IF (SELECT COUNT(*) FROM public.parts) <> 80 THEN
    RAISE EXCEPTION 'Número inesperado de filas en parts';
  END IF;
  IF (SELECT COUNT(*) FROM public.work_orders) <> 1160 THEN
    RAISE EXCEPTION 'Número inesperado de filas en work_orders';
  END IF;
  IF (SELECT COUNT(*) FROM public.repair_events) <> 1617 THEN
    RAISE EXCEPTION 'Número inesperado de filas en repair_events';
  END IF;
  IF (SELECT COUNT(*) FROM public.part_usage) <> 2344 THEN
    RAISE EXCEPTION 'Número inesperado de filas en part_usage';
  END IF;
  IF (SELECT COUNT(*) FROM public.inventory_movements) <> 3206 THEN
    RAISE EXCEPTION 'Número inesperado de filas en inventory_movements';
  END IF;
END;
$validacion$;
COMMIT;

-- Resumen de registros importados:
SELECT 'vehicles' AS tabla, COUNT(*) AS registros FROM public.vehicles
UNION ALL SELECT 'repair_types', COUNT(*) FROM public.repair_types
UNION ALL SELECT 'parts', COUNT(*) FROM public.parts
UNION ALL SELECT 'work_orders', COUNT(*) FROM public.work_orders
UNION ALL SELECT 'repair_events', COUNT(*) FROM public.repair_events
UNION ALL SELECT 'part_usage', COUNT(*) FROM public.part_usage
UNION ALL SELECT 'inventory_movements', COUNT(*) FROM public.inventory_movements;
