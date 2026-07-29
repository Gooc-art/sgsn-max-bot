import datetime as dt
import unittest

import max_bot as b


class MaxBotTest(unittest.TestCase):
    def test_last_full_week(self):
        self.assertEqual(b.last_full_week(dt.date(2026, 7, 29)), (dt.date(2026, 7, 20), dt.date(2026, 7, 26)))

    def test_parse_ru_date(self):
        self.assertEqual(b.parse_ru_date("29.07.2026"), dt.date(2026, 7, 29))
        self.assertEqual(b.parse_ru_date("2026-07-29"), dt.date(2026, 7, 29))
        self.assertIsNone(b.parse_ru_date("29/07/2026"))


if __name__ == "__main__":
    unittest.main()
