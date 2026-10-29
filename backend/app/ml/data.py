"""CDC BRFSS 2015 contract and train-only scaling; zeros are valid values."""
import csv
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, pstdev

CONTRACT_ID = "cdc-brfss2015-binary-v1"
CONTRACT_2021 = "cdc-brfss2021-binary-v1"
SUPPORTED_CONTRACTS = (CONTRACT_ID, CONTRACT_2021)
TARGET_2021 = "CDC BRFSS 2021 DIABETE4: 1=yes; 0=no, pregnancy-only or borderline/prediabetes"
TARGET = "Diabetes_binary"
TARGET_DESCRIPTION = "CDC BRFSS 2015 Diabetes_binary survey label (0 or 1)"


def binary(name, label):
    return {"name": name, "label": label, "min": 0, "max": 1,
            "options": [{"value": 0, "label": "No"}, {"value": 1, "label": "Yes"}]}


def coded(name, label, labels):
    return {"name": name, "label": label, "min": 1, "max": len(labels),
            "options": [{"value": i + 1, "label": text} for i, text in enumerate(labels)]}


FIELD_SPECS = [
    binary("HighBP", "High blood pressure indicator"),
    binary("HighChol", "High cholesterol indicator"),
    binary("CholCheck", "Cholesterol checked in past 5 years"),
    {"name": "BMI", "label": "BMI (dataset integer value)", "min": 12, "max": 98},
    binary("Smoker", "Smoked at least 100 cigarettes in lifetime"),
    binary("Stroke", "History of stroke"),
    binary("HeartDiseaseorAttack", "History of coronary heart disease or heart attack"),
    binary("PhysActivity", "Physical activity in past 30 days, outside work"),
    binary("Fruits", "Fruit at least once per day"),
    binary("Veggies", "Vegetables at least once per day"),
    binary("HvyAlcoholConsump", "Heavy alcohol consumption indicator"),
    binary("AnyHealthcare", "Any healthcare coverage"),
    binary("NoDocbcCost", "Could not see doctor because of cost in past 12 months"),
    coded("GenHlth", "General health", ["Excellent", "Very good", "Good", "Fair", "Poor"]),
    {"name": "MentHlth", "label": "Days mental health was not good (past 30 days)", "min": 0, "max": 30},
    {"name": "PhysHlth", "label": "Days physical health was not good (past 30 days)", "min": 0, "max": 30},
    binary("DiffWalk", "Serious difficulty walking or climbing stairs"),
    {"name": "Sex", "label": "Sex (source survey coding)", "min": 0, "max": 1,
     "options": [{"value": 0, "label": "Female"}, {"value": 1, "label": "Male"}]},
    coded("Age", "Age band", ["18-24", "25-29", "30-34", "35-39", "40-44", "45-49",
          "50-54", "55-59", "60-64", "65-69", "70-74", "75-79", "80 or older"]),
    coded("Education", "Education level", ["Never attended / kindergarten", "Grades 1-8",
          "Grades 9-11", "High school graduate / GED", "College 1-3 years", "College 4+ years"]),
    coded("Income", "Annual household income (2015 USD)", ["Under $10,000", "$10,000-$14,999",
          "$15,000-$19,999", "$20,000-$24,999", "$25,000-$34,999", "$35,000-$49,999",
          "$50,000-$74,999", "$75,000 or more"]),
]
FEATURES = tuple(field["name"] for field in FIELD_SPECS)


def validate_values(values):
    if len(values) != len(FEATURES):
        raise ValueError("Wrong feature count")
    for value, spec in zip(values, FIELD_SPECS):
        if not math.isfinite(value) or value != int(value) or not spec["min"] <= value <= spec["max"]:
            raise ValueError(f"{spec['name']} must be an integer in [{spec['min']}, {spec['max']}]")


def read_dataset(path: Path) -> tuple[list[list[float]], list[int]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        expected = {*FEATURES, TARGET}
        if not reader.fieldnames or len(reader.fieldnames) != len(expected) or set(reader.fieldnames) != expected:
            raise ValueError(f"CSV must contain exactly: {', '.join((*FEATURES, TARGET))}")
        rows, labels = [], []
        for number, row in enumerate(reader, 2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"Row {number}: wrong column count")
            try:
                values = tuple(float(row[name]) for name in FEATURES)
                label = float(row[TARGET])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Row {number}: all cells must be numeric") from exc
            try:
                validate_values(values)
            except ValueError as exc:
                raise ValueError(f"Row {number}: {exc}") from exc
            if label not in (0, 1):
                raise ValueError(f"Row {number}: {TARGET} must be 0 or 1")
            rows.append(list(values))
            labels.append(int(label))
    if len(rows) < 100 or min(labels.count(0), labels.count(1)) < 20:
        raise ValueError("Need at least 100 rows and at least 20 examples of each class")
    return rows, labels


def split_indices(rows, labels, seed=42):
    """Identical profiles stay together, even when their recorded labels differ."""
    import numpy as np
    from sklearn.model_selection import StratifiedGroupKFold

    mapping = {}
    groups = [mapping.setdefault(tuple(row), len(mapping)) for row in rows]
    folds = [test for _, test in StratifiedGroupKFold(
        n_splits=5, shuffle=True, random_state=seed
    ).split(rows, labels, groups)]
    train, validation, test = np.concatenate(folds[2:]), folds[1], folds[0]
    for indices in (train, validation, test):
        if len({labels[i] for i in indices}) != 2:
            raise ValueError("Each grouped split must contain both classes")
    return train, validation, test


@dataclass(frozen=True)
class Preprocessor:
    means: list[float]
    scales: list[float]

    @classmethod
    def fit(cls, rows: list[list[float]]) -> "Preprocessor":
        if not rows:
            raise ValueError("Training rows are empty")
        for row in rows:
            validate_values(row)
        columns = list(zip(*rows))
        return cls([mean(column) for column in columns], [pstdev(column) or 1.0 for column in columns])

    def transform(self, rows):
        for row in rows:
            validate_values(row)
        return [[(value - self.means[i]) / self.scales[i] for i, value in enumerate(row)] for row in rows]

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Preprocessor":
        values = [data[key] for key in ("means", "scales")]
        if any(len(column) != len(FEATURES) for column in values):
            raise ValueError("Invalid preprocessing dimensions")
        if any(not math.isfinite(v) for column in values for v in column):
            raise ValueError("Non-finite preprocessing value")
        if any(v <= 0 for v in data["scales"]):
            raise ValueError("Preprocessing scales must be positive")
        return cls(*values)
