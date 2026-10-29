import csv
import tempfile
import unittest
from pathlib import Path

from app.ml.data import FEATURES, TARGET, Preprocessor, read_dataset, split_indices
from tests.fixtures import PAYLOAD


class DataContractTests(unittest.TestCase):
    def write_csv(self, rows, headers=(*FEATURES, TARGET)):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "fixture.csv"
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(headers)
            writer.writerows(rows)
        return path

    def rows(self):
        rows = []
        for i in range(100):
            values = {**PAYLOAD, "MentHlth": i % 31, "PhysHlth": i // 31}
            rows.append([values[name] for name in FEATURES] + [i % 2])
        return rows

    def test_valid_dataset(self):
        rows, labels = read_dataset(self.write_csv(self.rows()))
        self.assertEqual(len(rows), 100)
        self.assertEqual(labels.count(1), 50)

    def test_duplicates_preserved_and_grouped_across_conflicting_labels(self):
        source = self.rows()
        source += [source[0], source[0][:-1] + [1]]
        rows, labels = read_dataset(self.write_csv(source))
        self.assertEqual(len(rows), 102)
        indices = split_indices(rows, labels)
        profiles = [{tuple(rows[i]) for i in split} for split in indices]
        self.assertFalse(profiles[0] & profiles[1] or profiles[0] & profiles[2] or profiles[1] & profiles[2])
        self.assertEqual(set().union(*(set(split) for split in indices)), set(range(102)))

    def test_invalid_codes_rejected(self):
        for name, bad in (("BMI", "NaN"), ("HighBP", 2), ("Age", 40), ("Income", 0), ("MentHlth", 31), ("Sex", 0.5)):
            rows = self.rows()
            rows[0][FEATURES.index(name)] = bad
            with self.assertRaisesRegex(ValueError, name):
                read_dataset(self.write_csv(rows))

    def test_wrong_label_rejected(self):
        rows = self.rows()
        rows[0][-1] = 2
        with self.assertRaisesRegex(ValueError, TARGET):
            read_dataset(self.write_csv(rows))

    def test_extra_column_rejected(self):
        with self.assertRaisesRegex(ValueError, "exactly"):
            read_dataset(self.write_csv([], (*FEATURES, TARGET, "PatientName")))

    def test_small_dataset_rejected(self):
        with self.assertRaisesRegex(ValueError, "at least 100"):
            read_dataset(self.write_csv(self.rows()[:10]))

    def test_scaling_preserves_zeros_and_cannot_fit_heldout_data(self):
        first = [PAYLOAD[name] for name in FEATURES]
        second = first.copy()
        second[0] = 1
        processor = Preprocessor.fit([first, second])
        self.assertEqual(processor.transform([first])[0][0], -1)
        self.assertEqual(processor.means[0], 0.5)
        processor.transform([second])
        self.assertEqual(processor.means[0], 0.5)
        self.assertEqual(Preprocessor.from_dict(processor.to_dict()), processor)

    def test_empty_training_rejected(self):
        with self.assertRaisesRegex(ValueError, "empty"):
            Preprocessor.fit([])

    def test_corrupt_preprocessor_rejected(self):
        with self.assertRaisesRegex(ValueError, "dimensions"):
            Preprocessor.from_dict({"means": [], "scales": []})
        with self.assertRaisesRegex(ValueError, "positive"):
            Preprocessor.from_dict({"means": [1] * 21, "scales": [0] * 21})


if __name__ == "__main__":
    unittest.main()
