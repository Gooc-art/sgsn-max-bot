import datetime as dt
import unittest

import sud_export as s


class SudExportTest(unittest.TestCase):
    def test_parse_schedule_and_case(self):
        schedule = """
        <table><tr><td>1</td><td><a href="/modules.php?name=sud_delo&name_op=case&case_id=1">2-1/2026</a></td>
        <td>09:30</td><td>1</td><td>КАТЕГОРИЯ: спор<br>ИСТЕЦ: Иванов</td><td>Петров П.П.</td><td>Отложено</td></tr></table>
        """
        rows = s.parse_schedule(schedule, "https://court.sudrf.ru/modules.php?name=sud_delo", "Суд", dt.date(2026, 7, 1))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].case_number, "2-1/2026")
        self.assertEqual(rows[0].url, "https://court.sudrf.ru/modules.php?name=sud_delo&name_op=case&case_id=1")
        parties, lawyers, check = s.parse_case("СТОРОНЫ ПО ДЕЛУ Истец Иванов Защитник (адвокат): Сидоров С.С. СУДЕБНЫЕ АКТЫ")
        self.assertIn("Истец Иванов", parties)
        self.assertIn("Сидоров", lawyers)
        self.assertEqual(check, "ok")


if __name__ == "__main__":
    unittest.main()
