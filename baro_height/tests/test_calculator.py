import unittest
from baro_height.src.height_calculator import BaroHeightCalculator
import math

class TestBaroHeightCalculator(unittest.TestCase):
    def test_initialization(self):
        calc = BaroHeightCalculator()
        self.assertEqual(calc.calculate_height(100000, 25), 0.0)

    def test_reset_zero(self):
        calc = BaroHeightCalculator()
        p0 = 101325.0
        t0 = 20.0
        calc.reset_zero(p0, t0)

        # At same pressure/temp, height should be 0
        self.assertAlmostEqual(calc.calculate_height(p0, t0), 0.0)

    def test_height_calculation(self):
        calc = BaroHeightCalculator()
        p0 = 101325.0
        t0 = 20.0 # 293.15 K
        calc.reset_zero(p0, t0)

        # Decrease pressure -> Increase height
        p1 = p0 - 12.0 # approx 1m
        h = calc.calculate_height(p1, t0)
        self.assertGreater(h, 0.0)

        # Check specific value
        # h = (R * T) / (M * g) * ln(p0 / p1)
        # R = 8.3144598, M = 0.0289644, g = 9.80665
        # T = 293.15
        # term = (8.3144598 * 293.15) / (0.0289644 * 9.80665) approx 8581
        # ln(101325 / 101313) approx ln(1.000118) approx 0.000118
        # h approx 8581 * 0.000118 approx 1.01m

        expected_h = (8.3144598 * 293.15) / (0.0289644 * 9.80665) * math.log(p0 / p1)
        self.assertAlmostEqual(h, expected_h, places=3)

    def test_calibration(self):
        calc = BaroHeightCalculator(scale=1.25)
        p0 = 101325.0
        t0 = 20.0
        calc.reset_zero(p0, t0)

        p1 = p0 - 12.0
        h_raw = (8.3144598 * 293.15) / (0.0289644 * 9.80665) * math.log(p0 / p1)
        h_cal = calc.calculate_height(p1, t0)

        self.assertAlmostEqual(h_cal, h_raw * 1.25, places=3)

    def test_reset_with_offset(self):
        calc = BaroHeightCalculator()
        p0 = 101325.0
        t0 = 20.0
        calc.reset_zero(p0, t0, current_height=5.0)

        self.assertAlmostEqual(calc.calculate_height(p0, t0), 5.0)

        p1 = p0 - 12.0
        h = calc.calculate_height(p1, t0)
        # approx 1.01 + 5.0 = 6.01
        expected_h = ((8.3144598 * 293.15) / (0.0289644 * 9.80665) * math.log(p0 / p1)) + 5.0
        self.assertAlmostEqual(h, expected_h, places=3)

if __name__ == '__main__':
    unittest.main()
