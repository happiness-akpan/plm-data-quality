-- Check: obsolete child parts used in assemblies that are not obsolete
-- Why it matters: live assemblies must not reference retired parts;
-- manufacturing may try to buy or fit a part that no longer exists

SELECT
    b.bom_line_id,
    b.parent_part_id,
    pa.status AS parent_status,
    b.child_part_id,
    c.status  AS child_status
FROM read_csv_auto('data/sample/bom.csv')   AS b
JOIN read_csv_auto('data/sample/parts.csv') AS c
    ON b.child_part_id  = c.part_id
JOIN read_csv_auto('data/sample/parts.csv') AS pa
    ON b.parent_part_id = pa.part_id
WHERE c.status  = 'Obsolete'
  AND pa.status <> 'Obsolete'
ORDER BY b.bom_line_id;