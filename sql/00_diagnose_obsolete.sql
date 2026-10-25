-- Diagnostic: how do the 40 planted obsolete parts appear in the data,
-- and how many distinct obsolete child parts does the data contain overall?

WITH planted AS (
    SELECT UNNEST(obsolete_in_active_bom) AS part_id
    FROM read_json_auto('data/sample/defect_manifest.json')
),
bom   AS (SELECT * FROM read_csv_auto('data/sample/bom.csv')),
parts AS (SELECT * FROM read_csv_auto('data/sample/parts.csv'))

SELECT
    (SELECT COUNT(*) FROM planted)                                   AS planted_parts,
    (SELECT COUNT(DISTINCT b.child_part_id)
       FROM bom b JOIN parts c ON b.child_part_id = c.part_id
      WHERE c.status = 'Obsolete')                                   AS distinct_obsolete_children,
    (SELECT COUNT(*) FROM bom b JOIN planted pl
        ON b.child_part_id = pl.part_id)                             AS bom_lines_using_planted;