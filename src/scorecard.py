"""
Run every data quality check, compare its findings with the defect manifest,
and report precision and recall per check.
"""
import json
from pathlib import Path

import duckdb
import pandas as pd

MANIFEST = Path("data/sample/defect_manifest.json")
OUTPUT = Path("outputs/scorecard.csv")

# Each check: (SQL file, manifest key, result columns that identify a defect)
# Two columns = the defect is a pair of parts (order does not matter)
CHECKS = [
    ("sql/01_orphaned_bom_lines.sql",          "orphaned_child_ids",        ["child_part_id"]),
    ("sql/02_released_missing_material.sql",   "released_missing_material", ["part_id"]),
    ("sql/03_invalid_uom.sql",                 "invalid_uom",               ["part_id"]),
    ("sql/04_invalid_bom_quantity.sql",        "invalid_quantity_lines",    ["bom_line_id"]),
    ("sql/05_change_closed_before_raised.sql", "closed_before_raised",      ["change_id"]),
    ("sql/06_obsolete_in_active_bom.sql",      "obsolete_in_active_bom",    ["child_part_id"]),
    ("sql/07_circular_bom_references.sql",     "circular_pairs",            ["part_a", "part_b"]),
    ("sql/08_near_duplicate_parts.sql",        "near_duplicate_pairs",      ["part_id_1", "part_id_2"]),
]


def to_keys(rows, is_pair):
    """Turn IDs (or pairs of IDs) into a set we can compare."""
    if is_pair:
        return {tuple(sorted(map(str, r))) for r in rows}
    return {str(r) for r in rows}


manifest = json.loads(MANIFEST.read_text())
results = []

for sql_file, key, cols in CHECKS:
    is_pair = len(cols) == 2
    df = duckdb.sql(Path(sql_file).read_text()).df()

    rows = df[cols].itertuples(index=False) if is_pair else df[cols[0]]
    found = to_keys(rows, is_pair)
    planted = to_keys(manifest[key], is_pair)

    caught = len(found & planted)          # in both = correctly found
    precision = caught / len(found) if found else 1.0
    recall = caught / len(planted) if planted else 1.0

    results.append({
        "check": Path(sql_file).stem,
        "planted": len(planted),
        "found": len(found),
        "caught": caught,
        "precision": f"{precision:.0%}",
        "recall": f"{recall:.0%}",
        "result": "PASS" if precision == 1 and recall == 1 else "FAIL",
    })

scorecard = pd.DataFrame(results)
print(scorecard.to_string(index=False))

OUTPUT.parent.mkdir(exist_ok=True)
scorecard.to_csv(OUTPUT, index=False)
print(f"\nSaved to {OUTPUT}")