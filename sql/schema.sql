PRAGMA foreign_keys = ON;

-- Learning simulation schema. Names echo selected SAP PP objects; this is not an SAP database replica.
CREATE TABLE IF NOT EXISTS MARA (
    material_id TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    base_uom TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS MARC (
    material_id TEXT NOT NULL REFERENCES MARA(material_id),
    plant TEXT NOT NULL,
    procurement_type TEXT NOT NULL CHECK (procurement_type IN ('E', 'F')),
    planned_lead_time_days INTEGER NOT NULL CHECK (planned_lead_time_days >= 0),
    lot_size INTEGER NOT NULL CHECK (lot_size > 0),
    safety_stock REAL NOT NULL DEFAULT 0 CHECK (safety_stock >= 0),
    PRIMARY KEY (material_id, plant)
);

CREATE TABLE IF NOT EXISTS MARD (
    material_id TEXT NOT NULL,
    plant TEXT NOT NULL,
    storage_location TEXT NOT NULL,
    unrestricted_qty REAL NOT NULL CHECK (unrestricted_qty >= 0),
    PRIMARY KEY (material_id, plant, storage_location),
    FOREIGN KEY (material_id, plant) REFERENCES MARC(material_id, plant)
);

CREATE TABLE IF NOT EXISTS STKO (
    bom_id TEXT PRIMARY KEY,
    parent_material TEXT NOT NULL REFERENCES MARA(material_id),
    alternative INTEGER NOT NULL DEFAULT 1,
    valid_from TEXT NOT NULL,
    valid_to TEXT NOT NULL,
    UNIQUE (parent_material, alternative, valid_from)
);

CREATE TABLE IF NOT EXISTS STPO (
    bom_id TEXT NOT NULL REFERENCES STKO(bom_id),
    item_no INTEGER NOT NULL,
    component_material TEXT NOT NULL REFERENCES MARA(material_id),
    qty_per REAL NOT NULL CHECK (qty_per > 0),
    scrap_pct REAL NOT NULL DEFAULT 0 CHECK (scrap_pct >= 0),
    PRIMARY KEY (bom_id, item_no)
);

CREATE TABLE IF NOT EXISTS CRHD (
    work_center TEXT PRIMARY KEY,
    plant TEXT NOT NULL,
    description TEXT NOT NULL,
    available_minutes_per_day INTEGER NOT NULL CHECK (available_minutes_per_day > 0)
);

CREATE TABLE IF NOT EXISTS PLKO (
    routing_id TEXT PRIMARY KEY,
    material_id TEXT NOT NULL REFERENCES MARA(material_id),
    plant TEXT NOT NULL,
    valid_from TEXT NOT NULL,
    valid_to TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS PLPO (
    routing_id TEXT NOT NULL REFERENCES PLKO(routing_id),
    operation_no INTEGER NOT NULL,
    work_center TEXT NOT NULL REFERENCES CRHD(work_center),
    setup_minutes REAL NOT NULL DEFAULT 0 CHECK (setup_minutes >= 0),
    run_minutes_per_unit REAL NOT NULL DEFAULT 0 CHECK (run_minutes_per_unit >= 0),
    PRIMARY KEY (routing_id, operation_no)
);

-- PLAF represents simulated planned orders. AFKO/AFPO are included only to show
-- the downstream production-order concept; this planner deliberately does not create them.
CREATE TABLE IF NOT EXISTS PLAF (
    planned_order_id TEXT PRIMARY KEY,
    material_id TEXT NOT NULL,
    plant TEXT NOT NULL,
    order_category TEXT NOT NULL CHECK (order_category IN ('IN_HOUSE', 'PURCHASE')),
    planned_qty REAL NOT NULL CHECK (planned_qty > 0),
    start_date TEXT NOT NULL,
    finish_date TEXT NOT NULL,
    lead_time_days INTEGER NOT NULL,
    FOREIGN KEY (material_id, plant) REFERENCES MARC(material_id, plant)
);

CREATE TABLE IF NOT EXISTS AFKO (
    production_order_id TEXT PRIMARY KEY,
    order_type TEXT NOT NULL,
    basic_start_date TEXT NOT NULL,
    basic_finish_date TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS AFPO (
    production_order_id TEXT NOT NULL REFERENCES AFKO(production_order_id),
    item_no INTEGER NOT NULL,
    material_id TEXT NOT NULL REFERENCES MARA(material_id),
    order_qty REAL NOT NULL CHECK (order_qty > 0),
    plant TEXT NOT NULL,
    PRIMARY KEY (production_order_id, item_no)
);

CREATE INDEX IF NOT EXISTS idx_stko_parent_validity ON STKO(parent_material, valid_from, valid_to);
CREATE INDEX IF NOT EXISTS idx_stpo_component ON STPO(component_material);
CREATE INDEX IF NOT EXISTS idx_plko_material_validity ON PLKO(material_id, plant, valid_from, valid_to);
CREATE INDEX IF NOT EXISTS idx_mard_material_plant ON MARD(material_id, plant);
