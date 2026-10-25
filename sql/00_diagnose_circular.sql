-- Diagnostic: which circular pairs were planted, and which appeared by accident?

WITH bom AS (
    SELECT * FROM read_csv_auto('data/sample/bom.csv')
),
planted AS (
    SELECT LEAST(pair[1], pair[2])    AS part_a,
           GREATEST(pair[1], pair[2]) AS part_b
    FROM (SELECT UNNEST(circular_pairs) AS pair
          FROM read_json_auto('data/sample/defect_manifest.json'))
),
found AS (
    SELECT b1.parent_part_id AS part_a,
           b1.child_part_id  AS part_b,
           b1.bom_line_id    AS line_a_to_b,
           b2.bom_line_id    AS line_b_to_a
    FROM bom AS b1
    JOIN bom AS b2
        ON  b1.parent_part_id = b2.child_part_id
        AND b1.child_part_id  = b2.parent_part_id
    WHERE b1.parent_part_id < b1.child_part_id
)
SELECT
    f.*,
    CASE WHEN pl.part_a IS NOT NULL THEN 'planted' ELSE 'accidental' END AS origin
FROM found AS f
LEFT JOIN planted AS pl
    ON f.part_a = pl.part_a AND f.part_b = pl.part_b
ORDER BY origin, f.part_a;