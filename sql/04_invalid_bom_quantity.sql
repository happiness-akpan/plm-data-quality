-- Check: BOM lines with a missing, zero or negative quantity
-- Why it matters: impossible quantities break material planning,
-- causing the ERP to order the wrong number of parts

SELECT
    bom_line_id,
    parent_part_id,
    child_part_id,
    quantity
FROM read_csv_auto('data/sample/bom.csv')
WHERE quantity IS NULL
   OR quantity <= 0
ORDER BY bom_line_id;