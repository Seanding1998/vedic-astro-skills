"""Regression tests for the clean-room native Vedic calculator."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from vedic_native_calculator import BAV_ROW_CONSTANTS, BirthInput, PLANET_ORDER, SIGNS, calculate_chart


class NativeCalculatorRegressionTests(unittest.TestCase):
    # Reproducible birth input used for numerical SAV/BAV regression only.
    # Interpretive claims are deliberately outside the scope of this test.
    BIRTH = BirthInput(
        year=2002,
        month=12,
        day=11,
        hour=20,
        minute=47,
        lat=25.4333,
        lon=119.0,
        tz="Asia/Shanghai",
        place="Quanzhou",
    )

    @classmethod
    def setUpClass(cls) -> None:
        cls.chart = calculate_chart(cls.BIRTH, require_ashtakavarga=True)

    def test_d1_contains_all_nine_grahas(self) -> None:
        self.assertEqual(set(self.chart["planets"]), set(PLANET_ORDER))
        self.assertTrue(self.chart["validation"]["planet_count"]["ok"])
        self.assertTrue(self.chart["validation"]["rahu_ketu_180"]["ok"])

    def test_ashtakavarga_is_available_and_conserves_337_points(self) -> None:
        self.assertTrue(self.chart["ashtakavarga_status"]["ok"])
        self.assertEqual(self.chart["ashtakavarga_status"]["source"], "PyJHora")
        self.assertEqual(sum(self.chart["sav"].values()), 337)
        self.assertTrue(self.chart["validation"]["sav_total"]["ok"])

    def test_bav_rows_and_sav_columns_reconcile_exactly(self) -> None:
        for planet, expected in BAV_ROW_CONSTANTS.items():
            self.assertEqual(sum(self.chart["bav"][planet].values()), expected)
            self.assertTrue(self.chart["validation"]["bav_row_constants"][planet]["ok"])

        for sign in SIGNS:
            total = sum(self.chart["bav"][planet][sign] for planet in BAV_ROW_CONSTANTS)
            self.assertEqual(total, self.chart["sav"][sign])
            self.assertTrue(self.chart["validation"]["bav_to_sav_columns"][sign]["ok"])

    def test_nakshatra_fields_are_consumable_by_the_shared_validator(self) -> None:
        for planet in PLANET_ORDER:
            row = self.chart["planets"][planet]
            self.assertIsInstance(row["nakshatra"], str)
            self.assertIn(row["pada"], {1, 2, 3, 4})
            self.assertIsInstance(row["nakshatra_lord"], str)


if __name__ == "__main__":
    unittest.main()
