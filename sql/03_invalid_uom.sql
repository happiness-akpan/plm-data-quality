-- Check: parts whose unit of measure is missing or not in the approved list
-- Approved units (from profiling 00_profile_uom.sql): EA, M, L, KG
-- Why it matters: target systems reject unknown units, and a wrong unit
-- corrupts quantities in BOMs, costing and inventory

SELECT
    part_id,
    part_number,
    name,
    unit_of_measure
FROM read_csv_auto('data/sample/parts.csv')
WHERE unit_of_measure IS NULL
   OR unit_of_measure NOT IN ('EA', 'M', 'L', 'KG')
ORDER BY part_id;