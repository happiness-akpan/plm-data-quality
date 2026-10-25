# PLM Data Quality Framework

Pre-migration data quality checks for PLM part, BOM and engineering change data,
validated against synthetic test data with known, planted defects.

**Result: 8 of 8 checks detect their defects with 100% precision and 100% recall.**

## The business problem

When engineering data moves between systems (a PLM upgrade, a PLM-to-ERP
integration, or two companies merging their part masters), bad data travels with
it. Duplicate parts split stock and cost history. BOM lines pointing at missing
parts fail to load. Obsolete parts in live assemblies get ordered.

Finding these issues before migration is far cheaper than fixing them after.
This project builds a set of automated checks that do exactly that, and proves
they work.

## Approach

1. **Synthetic data.** Real client data cannot be published, so
   `data/generate_data.py` creates a realistic PLM extract (parts, single-level
   BOMs, engineering changes) from two source systems that do not fully agree.
2. **Planted defects with an answer key.** The generator injects eight types of
   real-world defects and records every one in `defect_manifest.json`.
3. **Profile first, then write rules.** Each column is profiled before a rule is
   written, so rules are based on the data, not assumptions.
4. **One SQL check per defect type**, run with DuckDB directly on the CSV files.
5. **Automated scoring.** `src/scorecard.py` compares each check's findings with
   the answer key by ID, not just by count, and reports precision and recall.

## Results

| Check | Business risk | Technique | Planted | Found | Precision | Recall |
|---|---|---|---|---|---|---|
| Orphaned BOM lines | Lines fail to load or break assemblies | LEFT JOIN anti-match | 51 | 51 | 100% | 100% |
| Released, missing material | Released parts cannot be built or bought | Filtered NULL/blank test | 94 | 94 | 100% | 100% |
| Invalid unit of measure | Corrupts quantities and costing | Profiling + approved list | 104 | 104 | 100% | 100% |
| Invalid BOM quantity | Breaks material planning | Range validation | 78 | 78 | 100% | 100% |
| Change closed before raised | Negative cycle times in reporting | Cross-column date logic | 25 | 25 | 100% | 100% |
| Obsolete part in active BOM | Retired parts ordered or fitted | Double join on status | 40 | 40 | 100% | 100% |
| Circular BOM reference | BOM explosion fails or loops | Self-join, de-duplicated pairs | 6 | 6 | 100% | 100% |
| Near-duplicate part numbers | Split history, duplicate procurement | Canonical key normalisation | 200 | 200 | 100% | 100% |

## What validation uncovered

Testing the checks against the answer key exposed two flaws in the test data
itself, not in the checks:

- **Background noise.** The obsolete-part check first flagged 856 BOM lines
  against 40 planted. Diagnosis showed 654 distinct obsolete parts in BOMs, so
  random generation had placed obsolete parts in normal assemblies, making the
  planted defects indistinguishable. The generator was changed to build baseline
  BOMs from active parts only.
- **Unrecorded real defects.** The circular-reference check found 8 loops
  against 6 planted. A diagnostic query labelling each loop as planted or
  accidental showed 2 genuine loops created by chance. The generator was changed
  to prevent reverse links in baseline BOMs.

A fixed reference date was also introduced so that the same seed always produces
identical data.

The lesson carried into real projects: question the test data and the answer
key, not only the results.

## Repository layout

```
data/
  generate_data.py       synthetic data generator with planted defects
  sample/                generated CSVs and defect_manifest.json (seed 42)
sql/
  00_*.sql               profiling and diagnostic queries
  01_*.sql - 08_*.sql    one data quality check per defect type
src/
  run_check.py           runs a single check and prints its findings
  scorecard.py           runs all checks and scores them against the manifest
  manifest_summary.py    counts planted defects by type
outputs/
  scorecard.csv          latest scorecard
```

## Run it yourself

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python data/generate_data.py --parts 5000 --seed 42 --out data/sample
python src/scorecard.py
```

## Known limits and next steps

- Circular references are detected for direct two-part loops; longer loops
  (A to B to C to A) need a recursive query.
- Near-duplicates are matched on part number format; adding description
  similarity scoring would catch duplicates with genuinely different numbers.
- A dashboard view of the scorecard and defect trends.

## Tools

Python, pandas, DuckDB, SQL, Git/GitHub