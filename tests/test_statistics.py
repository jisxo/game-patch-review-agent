import unittest

from app.services.statistics import calculate_window_stats, wilson_interval


class StatisticsTests(unittest.TestCase):
    def test_empty_window(self) -> None:
        result = calculate_window_stats([])
        self.assertEqual(result.count, 0)
        self.assertIsNone(result.positive_ratio)

    def test_window_counts_and_interval(self) -> None:
        result = calculate_window_stats(
            [{"voted_up": True}, {"voted_up": True}, {"voted_up": False}]
        )
        self.assertEqual(result.positive_count, 2)
        self.assertEqual(result.negative_count, 1)
        self.assertAlmostEqual(result.positive_ratio or 0, 2 / 3)
        self.assertLess(result.positive_ratio_ci_low or 0, 2 / 3)
        self.assertGreater(result.positive_ratio_ci_high or 0, 2 / 3)

    def test_wilson_bounds(self) -> None:
        interval = wilson_interval(10, 10)
        self.assertIsNotNone(interval)
        assert interval is not None
        self.assertGreaterEqual(interval[0], 0)
        self.assertLessEqual(interval[1], 1)


if __name__ == "__main__":
    unittest.main()
