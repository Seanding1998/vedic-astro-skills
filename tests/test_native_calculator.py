"""Regression tests for the clean-room native Vedic calculator."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from vedic_native_calculator import (
    BAV_ROW_CONSTANTS,
    BirthInput,
    PLANET_ORDER,
    SIGNS,
    calculate_chart,
    format_south_indian_svg,
)


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

    def test_south_indian_svg_contains_twelve_signs_and_all_grahas(self) -> None:
        # 使用最小结构化样本，单独验证图形模板，不重复执行天文计算。
        chart = {
            "metadata": {
                "birth_date": "2002-12-11", "birth_time": "20:47",
                "place": "Quanzhou", "ayanamsa_mode": "TRUE_CITRA",
            },
            "ayanamsa": 23.9,
            "lagna": {"sign_idx": 0, "deg_str": "05deg12'"},
            "planets": {
                name: {"sign_idx": idx, "deg_str": "10deg20'", "retrograde": False}
                for idx, name in enumerate(PLANET_ORDER)
            },
        }
        svg = format_south_indian_svg(chart)
        self.assertEqual(svg.count("<rect x=\""), 13)
        self.assertIn("南印度式 D1 星盘", svg)
        self.assertIn("白羊（1）", svg)
        for body in ("日", "月", "火", "水", "木", "金", "土", "罗喉", "计都"):
            self.assertIn(body, svg)


if __name__ == "__main__":
    unittest.main()
