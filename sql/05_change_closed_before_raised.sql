-- Check: change records whose closed date is earlier than their raised date
-- Why it matters: impossible dates indicate entry or conversion errors
-- and produce negative cycle times in change reporting
-- Note: an empty closed_date is valid (the change is still open)

SELECT
    change_id,
    part_id,
    change_type,
    status,
    raised_date,
    closed_date
FROM read_csv_auto('data/sample/changes.csv')
WHERE closed_date < raised_date
ORDER BY change_id;