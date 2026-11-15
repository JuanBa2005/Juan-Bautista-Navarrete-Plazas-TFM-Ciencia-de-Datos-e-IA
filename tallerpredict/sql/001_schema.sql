BEGIN;

CREATE TABLE IF NOT EXISTS vehicles (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    vehicle_key TEXT NOT NULL UNIQUE,
    brand TEXT NOT NULL,
    model TEXT NOT NULL,
    displacement_cc INTEGER CHECK (displacement_cc IS NULL OR displacement_cc > 0),
    fuel TEXT NOT NULL CHECK (fuel IN ('gasoil', 'gasolina', 'electrico', 'hibrido_gasolina', 'hibrido_gasoil')),
    manufacture_year INTEGER CHECK (manufacture_year BETWEEN 1950 AND 2100)
);

CREATE TABLE IF NOT EXISTS work_orders (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_key TEXT NOT NULL UNIQUE,
    vehicle_id BIGINT NOT NULL REFERENCES vehicles(id),
    entry_at TIMESTAMP NOT NULL,
    exit_at TIMESTAMP,
    CHECK (exit_at IS NULL OR exit_at >= entry_at)
);

CREATE TABLE IF NOT EXISTS repair_types (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS repair_events (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repair_key TEXT NOT NULL UNIQUE,
    order_id BIGINT NOT NULL REFERENCES work_orders(id),
    repair_type_id BIGINT NOT NULL REFERENCES repair_types(id),
    performed_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS parts (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    part_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    unit TEXT NOT NULL DEFAULT 'ud',
    unit_cost NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (unit_cost >= 0),
    supplier_lead_days INTEGER NOT NULL DEFAULT 2 CHECK (supplier_lead_days >= 0)
);

CREATE TABLE IF NOT EXISTS part_usage (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repair_event_id BIGINT NOT NULL REFERENCES repair_events(id),
    part_id BIGINT NOT NULL REFERENCES parts(id),
    quantity NUMERIC(12,2) NOT NULL CHECK (quantity > 0),
    UNIQUE (repair_event_id, part_id)
);

CREATE TABLE IF NOT EXISTS inventory_movements (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    movement_key TEXT NOT NULL UNIQUE,
    part_id BIGINT NOT NULL REFERENCES parts(id),
    movement_at TIMESTAMP NOT NULL,
    quantity_delta NUMERIC(12,2) NOT NULL CHECK (quantity_delta <> 0),
    movement_type TEXT NOT NULL CHECK (movement_type IN ('compra', 'consumo', 'devolucion', 'ajuste')),
    repair_event_id BIGINT REFERENCES repair_events(id),
    notes TEXT
);

CREATE INDEX IF NOT EXISTS ix_orders_entry ON work_orders(entry_at);
CREATE INDEX IF NOT EXISTS ix_repair_events_date ON repair_events(performed_at);
CREATE INDEX IF NOT EXISTS ix_movements_date_part ON inventory_movements(part_id, movement_at);

CREATE OR REPLACE VIEW current_stock AS
SELECT
    p.id AS part_id,
    p.part_code,
    p.name,
    COALESCE(SUM(m.quantity_delta), 0) AS units
FROM parts p
LEFT JOIN inventory_movements m ON m.part_id = p.id
GROUP BY p.id, p.part_code, p.name;

CREATE OR REPLACE VIEW monthly_consumption AS
SELECT
    p.part_code,
    p.name,
    DATE_TRUNC('month', e.performed_at)::date AS month,
    SUM(u.quantity) AS units
FROM part_usage u
JOIN parts p ON p.id = u.part_id
JOIN repair_events e ON e.id = u.repair_event_id
GROUP BY p.part_code, p.name, DATE_TRUNC('month', e.performed_at)::date;

COMMIT;
