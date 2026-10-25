-- Check: parts that are the same part number written in different formats
-- Method: normalise each part number to a canonical key
--   (prefix letters in upper case + numeric part as an integer), then pair
--   parts that share a key
-- Why it matters: duplicates split a part's history, stock and cost, and
-- cause procurement to buy the same part under two numbers

WITH keyed AS (
    SELECT
        part_id,
        part_number,
        description,
        source_system,
        REGEXP_EXTRACT(UPPER(part_number), '^([A-Z]+)', 1)        AS prefix,
        CAST(REGEXP_EXTRACT(part_number, '([0-9]+)$', 1) AS BIGINT) AS num
    FROM read_csv_auto('data/sample/parts.csv')
)
SELECT
    a.part_id      AS part_id_1,
    a.part_number  AS part_number_1,
    a.source_system AS source_1,
    b.part_id      AS part_id_2,
    b.part_number  AS part_number_2,
    b.source_system AS source_2
FROM keyed AS a
JOIN keyed AS b
    ON  a.prefix = b.prefix
    AND a.num    = b.num
    AND a.part_id < b.part_id
ORDER BY part_id_1;