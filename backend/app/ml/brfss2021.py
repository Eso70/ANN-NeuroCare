"""Explicit CDC BRFSS 2021 XPORT conversion; raw survey files remain untouched.

Definitions: CDC codebook21_llcp-v2-508.pdf, pages 21-25, 31, 40, 132-148,
155 and 161-162. Output is complete-case, unweighted survey classification data.
"""
import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

from app.ml.data import CONTRACT_2021, FEATURES, FIELD_SPECS, TARGET, TARGET_2021

SOURCE_URL = "https://www.cdc.gov/brfss/annual_data/annual_2021.html"
CODEBOOK_URL = "https://www.cdc.gov/brfss/annual_data/2021/pdf/codebook21_llcp-v2-508.pdf"
MAPPING_VERSION = "brfss2021-complete-case-integer-v1"

# Raw values not listed here stay missing and cause complete-case exclusion.
RECODE = {
    TARGET: ("DIABETE4", {1: 1, 2: 0, 3: 0, 4: 0}),
    "HighBP": ("_RFHYPE6", {1: 0, 2: 1}),
    "HighChol": ("TOLDHI3", {1: 1, 2: 0}),
    "CholCheck": ("_CHOLCH3", {1: 1, 2: 0, 3: 0}),
    "Smoker": ("SMOKE100", {1: 1, 2: 0}),
    "Stroke": ("CVDSTRK3", {1: 1, 2: 0}),
    "HeartDiseaseorAttack": ("_MICHD", {1: 1, 2: 0}),
    "PhysActivity": ("_TOTINDA", {1: 1, 2: 0}),
    "Fruits": ("_FRTLT1A", {1: 1, 2: 0}),
    "Veggies": ("_VEGLT1A", {1: 1, 2: 0}),
    "HvyAlcoholConsump": ("_RFDRHV7", {1: 0, 2: 1}),
    "AnyHealthcare": ("_HLTHPLN", {1: 1, 2: 0}),
    "NoDocbcCost": ("MEDCOST1", {1: 1, 2: 0}),
    "GenHlth": ("GENHLTH", {i: i for i in range(1, 6)}),
    "MentHlth": ("MENTHLTH", {**{i: i for i in range(1, 31)}, 88: 0}),
    "PhysHlth": ("PHYSHLTH", {**{i: i for i in range(1, 31)}, 88: 0}),
    "DiffWalk": ("DIFFWALK", {1: 1, 2: 0}),
    "Sex": ("SEXVAR", {1: 1, 2: 0}),
    "Age": ("_AGEG5YR", {i: i for i in range(1, 14)}),
    "Education": ("EDUCA", {i: i for i in range(1, 7)}),
    "Income": ("INCOME3", {i: min(i, 8) for i in range(1, 12)}),
}
REQUIRED_COLUMNS = {source for source, _ in RECODE.values()} | {"_BMI5", "IYEAR"}


def convert_frame(frame):
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"Missing 2021 columns: {sorted(missing)}")
    years = frame["IYEAR"].map(lambda value: value.decode().strip() if isinstance(value, bytes) else str(value).strip())
    if not years.isin(["2021", "2021.0", "2022", "2022.0"]).all():
        # Some interviews for the annual wave finish in the following calendar year.
        raise ValueError("Unexpected interview year in 2021 survey file")
    result = pd.DataFrame({name: frame[source].map(mapping) for name, (source, mapping) in RECODE.items()}, index=frame.index)
    # Source has two implied decimals; use integer rounding (ties to even), not clipping.
    result["BMI"] = (pd.to_numeric(frame["_BMI5"], errors="coerce") / 100).round()
    for spec in FIELD_SPECS:
        result[spec["name"]] = result[spec["name"]].where(result[spec["name"]].between(spec["min"], spec["max"]))
    invalid = result.isna().sum().astype(int).to_dict()
    return result.loc[:, [*FEATURES, TARGET]].dropna().astype("int16"), invalid


def prepare(source: Path, output: Path):
    manifest = output.with_suffix(".json")
    if output.exists() or manifest.exists():
        raise FileExistsError("Derived output already exists; choose another output path")
    output.parent.mkdir(parents=True, exist_ok=True)
    raw_rows, kept_rows, counts = 0, 0, {"0": 0, "1": 0}
    exclusions = {}
    try:
        with pd.read_sas(source, format="xport", iterator=True, chunksize=20000) as reader:
            for index, frame in enumerate(reader):
                cleaned, invalid = convert_frame(frame)
                raw_rows += len(frame)
                kept_rows += len(cleaned)
                for name, count in invalid.items():
                    exclusions[name] = exclusions.get(name, 0) + count
                for label in (0, 1):
                    counts[str(label)] += int((cleaned[TARGET] == label).sum())
                cleaned.to_csv(output, index=False, mode="w" if index == 0 else "a", header=index == 0)
                print(f"Converted {raw_rows} raw rows; retained {kept_rows} complete cases", flush=True)
        if raw_rows != 438693:
            raise ValueError(f"Expected official 2021 wave row count 438693; got {raw_rows}")
        if min(counts.values()) < 20:
            raise ValueError("Insufficient examples of both target classes")
        with source.open("rb") as stream:
            raw_digest = hashlib.file_digest(stream, "sha256").hexdigest()
        with output.open("rb") as stream:
            csv_digest = hashlib.file_digest(stream, "sha256").hexdigest()
        report = {
            "contract_id": CONTRACT_2021, "mapping_version": MAPPING_VERSION,
            "source_file": source.name, "source_sha256": raw_digest, "csv_sha256": csv_digest,
            "source_url": SOURCE_URL, "codebook_url": CODEBOOK_URL,
            "raw_rows": raw_rows, "retained_rows": kept_rows, "excluded_rows": raw_rows - kept_rows,
            "invalid_by_field_overlapping": exclusions, "class_counts": counts,
            "target": TARGET_2021, "income": "2021 nominal USD; raw categories 8-11 combined into $75,000 or more; no inflation adjustment",
            "bmi": "_BMI5 / 100, rounded to integer (ties to even); only 12 through 98 retained",
            "missing_values": "Unknown/refused/missing excluded, never converted to No. Raw 88 becomes zero ONLY for health-day counts.",
            "limitations": "Complete-case selection; self-report; no survey weights; changed survey questions. Not asserted interchangeable with the 2015 target.",
            "mapping": {name: {"source": column, "values": mapping} for name, (column, mapping) in RECODE.items()},
        }
        manifest.write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
        print(json.dumps({key: report[key] for key in ("raw_rows", "retained_rows", "excluded_rows", "class_counts")}), flush=True)
        return report
    except Exception:
        # Leave incomplete derived data distinguishable; never remove the raw file.
        if output.exists():
            output.rename(output.with_suffix(".incomplete.csv"))
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xpt", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    prepare(args.xpt.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
