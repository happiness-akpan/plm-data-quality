-- Profiling: every distinct unit of measure and how often it appears
-- Purpose: understand the data before deciding which values are valid

SELECT
    unit_of_measure,
    COUNT(*) AS how_many
FROM read_csv_auto('data/sample/parts.csv')
GROUP BY unit_of_measure
ORDER BY how_many DESC;