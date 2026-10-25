-- Check: BOM lines whose child part does not exist in the part master
-- Why it matters: these lines would fail to load, or create broken assemblies

SELECT
    b.bom_line_id,
    b.parent_part_id,
    b.child_part_id
FROM read_csv_auto('data/sample/bom.csv')   AS b
LEFT JOIN read_csv_auto('data/sample/parts.csv') AS p
    ON b.child_part_id = p.part_id
WHERE p.part_id IS NULL
ORDER BY b.bom_line_id;