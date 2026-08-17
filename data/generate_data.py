"""
Synthetic PLM dataset generator.

Produces three CSV extracts that mimic the shape of a Teamcenter-style export:

    parts.csv    - part master, sourced from two systems that do not agree
    bom.csv      - single-level BOM lines (parent -> child)
    changes.csv  - engineering change records against parts

Defects are injected deliberately and recorded in data/sample/defect_manifest.json
so the detection SQL can be tested against a known ground truth.

Usage:
    python generate_data.py --parts 5000 --seed 42 --out data/sample
"""

from __future__ import annotations

import argparse
import json
import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

# ----------------------------------------------------------------------------
# Reference vocabulary
# ----------------------------------------------------------------------------

PREFIXES = ["BRKT", "HSG", "SHFT", "SEAL", "BRG", "GSKT", "VLV", "PMP",
            "FLNG", "BOLT", "PLT", "DUCT", "CVR", "RTR", "STTR"]

NOUNS = {
    "BRKT": ["Bracket", "Mounting Bracket", "Support Bracket"],
    "HSG": ["Housing", "Casing", "Enclosure"],
    "SHFT": ["Shaft", "Drive Shaft", "Main Shaft"],
    "SEAL": ["Seal", "Oil Seal", "Lip Seal"],
    "BRG": ["Bearing", "Roller Bearing", "Ball Bearing"],
    "GSKT": ["Gasket", "Flange Gasket"],
    "VLV": ["Valve", "Control Valve", "Relief Valve"],
    "PMP": ["Pump", "Fuel Pump", "Scavenge Pump"],
    "FLNG": ["Flange", "Blind Flange"],
    "BOLT": ["Bolt", "Hex Bolt", "Stud Bolt"],
    "PLT": ["Plate", "Cover Plate", "Base Plate"],
    "DUCT": ["Duct", "Air Duct", "Bleed Duct"],
    "CVR": ["Cover", "Access Cover"],
    "RTR": ["Rotor", "Rotor Assembly"],
    "STTR": ["Stator", "Stator Vane"],
}

MODIFIERS = ["Upper", "Lower", "Front", "Rear", "Inboard", "Outboard",
             "LH", "RH", "Primary", "Secondary"]

MATERIALS = ["Ti-6Al-4V", "Inconel 718", "AL 7075-T6", "SS 316L",
             "Nitrile Rubber", "PTFE", "Carbon Steel", "Nickel Alloy C263"]

UOM = ["EA", "EA", "EA", "EA", "KG", "M", "L"]           # weighted toward EA
STATUS = ["In Work", "Released", "Released", "Released", "Obsolete"]
GROUPS = ["Mechanical Design", "Systems", "Structures", "Propulsion",
          "Aftermarket", "Tooling", "Supplier Managed"]
SOURCES = ["TC_PROD", "LEGACY_ERP"]

CHANGE_TYPES = ["ECR", "ECN", "Deviation", "Concession"]
CHANGE_STATUS = ["Draft", "In Review", "Approved", "Implemented", "Rejected"]


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

def rand_date(rng: random.Random, start: date, end: date) -> date:
    return start + timedelta(days=rng.randint(0, (end - start).days))


def build_name(rng: random.Random, prefix: str) -> str:
    noun = rng.choice(NOUNS[prefix])
    if rng.random() < 0.45:
        return f"{rng.choice(MODIFIERS)} {noun}"
    return noun


def mangle_part_number(rng: random.Random, pn: str) -> str:
    """Return a visually different but logically identical part number."""
    style = rng.choice(["underscore", "nosep", "lower", "space", "zeropad", "dotted"])
    prefix, num = pn.split("-", 1)
    if style == "underscore":
        return f"{prefix}_{num}"
    if style == "nosep":
        return f"{prefix}{num}"
    if style == "lower":
        return pn.lower()
    if style == "space":
        return f"{prefix} {num}"
    if style == "zeropad":
        return f"{prefix}-{num.lstrip('0').zfill(8)}"
    return f"{prefix}.{num}"


def mangle_description(rng: random.Random, desc: str) -> str:
    """Same part, described the way a different system or engineer would."""
    swaps = {
        "Bracket": "BRACKET", "Housing": "Hsg", "Shaft": "SHAFT",
        "Upper": "UPR", "Lower": "LWR", "Front": "FRT", "Rear": "RR",
        "Inboard": "INBD", "Outboard": "OUTBD", "Assembly": "ASSY",
        "Primary": "PRI", "Secondary": "SEC",
    }
    out = desc
    for k, v in swaps.items():
        if k in out and rng.random() < 0.6:
            out = out.replace(k, v)
    if rng.random() < 0.3:
        out = out.upper()
    if rng.random() < 0.25:
        out = f"  {out} "          # stray whitespace
    return out


# ----------------------------------------------------------------------------
# Generation
# ----------------------------------------------------------------------------

def generate(n_parts: int, seed: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    rng = random.Random(seed)
    manifest: dict[str, list | int] = {}

    today = date.today()
    start = today - timedelta(days=365 * 6)

    parts: list[dict] = []
    used_numbers: set[str] = set()

    # --- clean baseline -----------------------------------------------------
    for i in range(n_parts):
        prefix = rng.choice(PREFIXES)
        num = f"{rng.randint(1, 999999):06d}"
        pn = f"{prefix}-{num}"
        while pn in used_numbers:
            num = f"{rng.randint(1, 999999):06d}"
            pn = f"{prefix}-{num}"
        used_numbers.add(pn)

        name = build_name(rng, prefix)
        created = rand_date(rng, start, today)

        parts.append({
            "part_id": f"P{i + 1:07d}",
            "part_number": pn,
            "revision": rng.choice(["A", "A", "B", "B", "C", "D"]),
            "name": name,
            "description": f"{name}, {rng.choice(MATERIALS).split()[0]}",
            "material": rng.choice(MATERIALS),
            "unit_of_measure": rng.choice(UOM),
            "status": rng.choice(STATUS),
            "owning_group": rng.choice(GROUPS),
            "created_date": created.isoformat(),
            "source_system": rng.choices(SOURCES, weights=[0.75, 0.25])[0],
        })

    next_id = n_parts + 1

    # --- DEFECT 1: near-duplicate part numbers ------------------------------
    n_dupes = max(1, int(n_parts * 0.04))
    dupe_pairs = []
    for src in rng.sample(parts[:n_parts], n_dupes):
        dup = dict(src)
        dup["part_id"] = f"P{next_id:07d}"
        next_id += 1
        dup["part_number"] = mangle_part_number(rng, src["part_number"])
        dup["description"] = mangle_description(rng, src["description"])
        dup["source_system"] = "LEGACY_ERP" if src["source_system"] == "TC_PROD" else "TC_PROD"
        dup["created_date"] = rand_date(rng, start, today).isoformat()
        parts.append(dup)
        dupe_pairs.append([src["part_id"], dup["part_id"]])
    manifest["near_duplicate_pairs"] = dupe_pairs

    # --- DEFECT 2: released parts with no material --------------------------
    released = [p for p in parts if p["status"] == "Released"]
    missing_material = rng.sample(released, max(1, int(len(released) * 0.03)))
    for p in missing_material:
        p["material"] = ""
    manifest["released_missing_material"] = [p["part_id"] for p in missing_material]

    # --- DEFECT 3: missing / invalid UOM ------------------------------------
    bad_uom = rng.sample(parts, max(1, int(len(parts) * 0.02)))
    for p in bad_uom:
        p["unit_of_measure"] = rng.choice(["", "N/A", "???"])
    manifest["invalid_uom"] = [p["part_id"] for p in bad_uom]

    # --- BOM ----------------------------------------------------------------
    part_ids = [p["part_id"] for p in parts]
    assemblies = rng.sample(part_ids, int(len(part_ids) * 0.18))
    bom: list[dict] = []
    seen_edges: set[tuple[str, str]] = set()

    for parent in assemblies:
        for fn, child in enumerate(rng.sample(part_ids, rng.randint(2, 9)), start=1):
            if child == parent or (parent, child) in seen_edges:
                continue
            seen_edges.add((parent, child))
            bom.append({
                "bom_line_id": f"L{len(bom) + 1:07d}",
                "parent_part_id": parent,
                "child_part_id": child,
                "quantity": rng.choice([1, 1, 1, 2, 2, 4, 6, 8, 12]),
                "find_number": fn * 10,
                "effectivity_date": rand_date(rng, start, today).isoformat(),
            })

    # --- DEFECT 4: orphaned children (child not in part master) -------------
    orphans = []
    for _ in range(max(1, int(len(bom) * 0.01))):
        line = rng.choice(bom)
        ghost = f"P9{rng.randint(100000, 999999)}"
        bom.append({
            "bom_line_id": f"L{len(bom) + 1:07d}",
            "parent_part_id": line["parent_part_id"],
            "child_part_id": ghost,
            "quantity": 1,
            "find_number": 999,
            "effectivity_date": rand_date(rng, start, today).isoformat(),
        })
        orphans.append(ghost)
    manifest["orphaned_child_ids"] = orphans

    # --- DEFECT 5: zero / null / negative quantities ------------------------
    bad_qty = rng.sample(bom, max(1, int(len(bom) * 0.015)))
    for line in bad_qty:
        line["quantity"] = rng.choice([0, None, -1])
    manifest["invalid_quantity_lines"] = [l["bom_line_id"] for l in bad_qty]

    # --- DEFECT 6: circular references ---------------------------------------
    cycles = []
    for _ in range(6):
        a, b = rng.sample(part_ids, 2)
        bom.append({"bom_line_id": f"L{len(bom) + 1:07d}", "parent_part_id": a,
                    "child_part_id": b, "quantity": 1, "find_number": 500,
                    "effectivity_date": today.isoformat()})
        bom.append({"bom_line_id": f"L{len(bom) + 1:07d}", "parent_part_id": b,
                    "child_part_id": a, "quantity": 1, "find_number": 500,
                    "effectivity_date": today.isoformat()})
        cycles.append([a, b])
    manifest["circular_pairs"] = cycles

    # --- DEFECT 7: obsolete parts still used in active assemblies -----------
    obsolete_ids = [p["part_id"] for p in parts if p["status"] == "Obsolete"]
    obsolete_in_use = []
    for child in rng.sample(obsolete_ids, min(40, len(obsolete_ids))):
        parent = rng.choice([p["part_id"] for p in parts if p["status"] == "Released"])
        bom.append({
            "bom_line_id": f"L{len(bom) + 1:07d}",
            "parent_part_id": parent,
            "child_part_id": child,
            "quantity": rng.choice([1, 2, 4]),
            "find_number": 600,
            "effectivity_date": rand_date(rng, start, today).isoformat(),
        })
        obsolete_in_use.append(child)
    manifest["obsolete_in_active_bom"] = obsolete_in_use

    # --- Change records ------------------------------------------------------
    changes: list[dict] = []
    for i in range(int(n_parts * 0.35)):
        raised = rand_date(rng, start, today)
        status = rng.choice(CHANGE_STATUS)
        closed = ""
        if status in ("Implemented", "Rejected"):
            closed = (raised + timedelta(days=rng.randint(3, 180))).isoformat()
        changes.append({
            "change_id": f"CH{i + 1:06d}",
            "part_id": rng.choice(part_ids),
            "change_type": rng.choice(CHANGE_TYPES),
            "requested_by": rng.choice(GROUPS),
            "status": status,
            "raised_date": raised.isoformat(),
            "closed_date": closed,
        })

    # --- DEFECT 8: changes closed before they were raised -------------------
    backwards = rng.sample([c for c in changes if c["closed_date"]], 25)
    for c in backwards:
        raised = date.fromisoformat(c["raised_date"])
        c["closed_date"] = (raised - timedelta(days=rng.randint(1, 60))).isoformat()
    manifest["closed_before_raised"] = [c["change_id"] for c in backwards]

    manifest["counts"] = {
        "parts": len(parts),
        "bom_lines": len(bom),
        "changes": len(changes),
    }

    return pd.DataFrame(parts), pd.DataFrame(bom), pd.DataFrame(changes), manifest


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate synthetic PLM data with known defects.")
    ap.add_argument("--parts", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", type=str, default="data/sample")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    parts, bom, changes, manifest = generate(args.parts, args.seed)

    parts.to_csv(out / "parts.csv", index=False)
    bom.to_csv(out / "bom.csv", index=False)
    changes.to_csv(out / "changes.csv", index=False)
    (out / "defect_manifest.json").write_text(json.dumps(manifest, indent=2))

    print(f"Wrote {len(parts):,} parts, {len(bom):,} BOM lines, {len(changes):,} changes to {out}/")
    print("Injected defects:")
    for k, v in manifest.items():
        if k == "counts":
            continue
        print(f"  {k:<32} {len(v):>6}")


if __name__ == "__main__":
    main()
