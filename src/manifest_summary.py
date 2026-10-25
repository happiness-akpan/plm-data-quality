"""Print how many defects of each type the generator planted."""
import json

with open("data/sample/defect_manifest.json") as f:
    manifest = json.load(f)

print("Planted defects:")
for defect_type, items in manifest.items():
    count = len(items) if isinstance(items, (list, dict)) else items
    print(f"  {defect_type:<30} {count}")