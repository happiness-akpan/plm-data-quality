-- Check: Released parts with no material recorded
-- Why it matters: released parts must be buildable; a missing material
-- blocks purchasing/manufacturing and often fails target-system validation

SELECT
    part_id,
    part_number,
    name,
    status,
    material
FROM read_csv_auto('data/sample/parts.csv')
WHERE status = 'Released'
  AND (material IS NULL OR TRIM(material) = '')
ORDER BY part_id;