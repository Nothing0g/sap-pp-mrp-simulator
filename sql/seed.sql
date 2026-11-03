INSERT INTO MARA (material_id, description, base_uom) VALUES
    ('FORK-100', 'Front suspension fork assembly', 'EA'),
    ('FORK-110', 'Fork lower-leg subassembly', 'EA'),
    ('FORK-120', 'Fork crown and steerer subassembly', 'EA'),
    ('LEG-L', 'Left lower leg', 'EA'),
    ('LEG-R', 'Right lower leg', 'EA'),
    ('CROWN-01', 'Fork crown', 'EA'),
    ('STEER-01', 'Steerer tube', 'EA'),
    ('SEAL-KIT', 'Fork seal kit', 'SET'),
    ('BOLT-M6', 'M6 mounting bolt', 'EA'),
    ('CAP-01', 'Top cap', 'EA');

INSERT INTO MARC (material_id, plant, procurement_type, planned_lead_time_days, lot_size, safety_stock) VALUES
    ('FORK-100', '1000', 'E', 2, 1, 0),
    ('FORK-110', '1000', 'E', 2, 1, 2),
    ('FORK-120', '1000', 'E', 1, 1, 0),
    ('LEG-L', '1000', 'F', 5, 10, 4),
    ('LEG-R', '1000', 'F', 5, 10, 4),
    ('CROWN-01', '1000', 'F', 4, 5, 1),
    ('STEER-01', '1000', 'F', 3, 5, 0),
    ('SEAL-KIT', '1000', 'F', 4, 20, 10),
    ('BOLT-M6', '1000', 'F', 2, 50, 20),
    ('CAP-01', '1000', 'F', 3, 10, 0);

INSERT INTO MARD (material_id, plant, storage_location, unrestricted_qty) VALUES
    ('FORK-100', '1000', '0001', 3),
    ('FORK-110', '1000', '0001', 1),
    ('FORK-120', '1000', '0001', 0),
    ('LEG-L', '1000', '0001', 18),
    ('LEG-R', '1000', '0001', 15),
    ('CROWN-01', '1000', '0001', 4),
    ('STEER-01', '1000', '0001', 5),
    ('SEAL-KIT', '1000', '0001', 25),
    ('BOLT-M6', '1000', '0001', 70),
    ('CAP-01', '1000', '0001', 6);

INSERT INTO STKO (bom_id, parent_material, alternative, valid_from, valid_to) VALUES
    ('BOM-FORK-100', 'FORK-100', 1, '2025-01-01', '9999-12-31'),
    ('BOM-FORK-110', 'FORK-110', 1, '2025-01-01', '9999-12-31'),
    ('BOM-FORK-120', 'FORK-120', 1, '2025-01-01', '9999-12-31');

INSERT INTO STPO (bom_id, item_no, component_material, qty_per, scrap_pct) VALUES
    ('BOM-FORK-100', 10, 'FORK-110', 1, 0),
    ('BOM-FORK-100', 20, 'FORK-120', 1, 0),
    ('BOM-FORK-100', 30, 'SEAL-KIT', 1, 2),
    ('BOM-FORK-100', 40, 'BOLT-M6', 4, 1),
    ('BOM-FORK-110', 10, 'LEG-L', 1, 0),
    ('BOM-FORK-110', 20, 'LEG-R', 1, 0),
    ('BOM-FORK-110', 30, 'BOLT-M6', 2, 1),
    ('BOM-FORK-120', 10, 'CROWN-01', 1, 0),
    ('BOM-FORK-120', 20, 'STEER-01', 1, 0),
    ('BOM-FORK-120', 30, 'CAP-01', 1, 0);

INSERT INTO CRHD (work_center, plant, description, available_minutes_per_day) VALUES
    ('WC-ASSEMBLY', '1000', 'Fork assembly bench', 420),
    ('WC-PREP', '1000', 'Subassembly preparation', 360);

INSERT INTO PLKO (routing_id, material_id, plant, valid_from, valid_to) VALUES
    ('ROUTE-FORK-100', 'FORK-100', '1000', '2025-01-01', '9999-12-31'),
    ('ROUTE-FORK-110', 'FORK-110', '1000', '2025-01-01', '9999-12-31'),
    ('ROUTE-FORK-120', 'FORK-120', '1000', '2025-01-01', '9999-12-31');

INSERT INTO PLPO (routing_id, operation_no, work_center, setup_minutes, run_minutes_per_unit) VALUES
    ('ROUTE-FORK-100', 10, 'WC-ASSEMBLY', 30, 18),
    ('ROUTE-FORK-110', 10, 'WC-PREP', 20, 12),
    ('ROUTE-FORK-120', 10, 'WC-PREP', 15, 8);

-- AFKO/AFPO stay empty: the exercise stops at simulated planned orders (PLAF).
