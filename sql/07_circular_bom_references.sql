-- Check: pairs of parts that list each other as children (A -> B and B -> A)
-- Why it matters: BOMs must be one-directional; loops make BOM explosion
-- run forever or fail, and migrations often reject the whole structure
-- Scope: detects direct two-part loops; longer loops (A -> B -> C -> A)
-- need a recursive query (possible future extension)

WITH bom AS (
    SELECT * FROM read_csv_auto('data/sample/bom.csv')
)
SELECT
    b1.parent_part_id AS part_a,
    b1.child_part_id  AS part_b,
    b1.bom_line_id    AS line_a_to_b,
    b2.bom_line_id    AS line_b_to_a
FROM bom AS b1
JOIN bom AS b2
    ON  b1.parent_part_id = b2.child_part_id
    AND b1.child_part_id  = b2.parent_part_id
WHERE b1.parent_part_id < b1.child_part_id
ORDER BY part_a;