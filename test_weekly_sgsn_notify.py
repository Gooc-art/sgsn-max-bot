import datetime as dt
import csv
import tempfile
import unittest

import weekly_sgsn_notify as w


class WeeklySgsnNotifyTest(unittest.TestCase):
    def test_next_week(self):
        self.assertEqual(w.next_week(dt.date(2026, 8, 10)), (dt.date(2026, 8, 17), dt.date(2026, 8, 23)))
        self.assertEqual(w.next_week(dt.date(2026, 8, 16)), (dt.date(2026, 8, 17), dt.date(2026, 8, 23)))

    def test_sgsn_rows_reads_export_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = w.Path(tmp) / "report.csv"
            with path.open("w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Группа", "Кол-во", "Суд", "Дата", "Время", "Номер", "Категория", "Судья", "Стороны", "Представители", "Результат", "Ссылка", "Статус"])
                writer.writerow(["", "", "Суд", "2026-08-17", "10:00", "1", "", "", "Истец: Иванов", "", "", "", ""])
                writer.writerow(["", "", "Суд", "2026-08-17", "11:00", "2", "", "", "Ответчик: Служба государственного строительного надзора ЯНАО", "", "", "", ""])

            self.assertEqual(len(w.sgsn_rows(path)), 1)

    def test_weekly_chat_id_uses_file_when_env_is_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            old_file = w.CHAT_ID_FILE
            w.CHAT_ID_FILE = w.Path(tmp) / "weekly-chat-id"
            w.CHAT_ID_FILE.write_text("777\n", encoding="utf-8")
            try:
                self.assertEqual(w.weekly_chat_id(), "777")
            finally:
                w.CHAT_ID_FILE = old_file

    def test_weekly_target_supports_private_and_legacy_chat(self):
        self.assertEqual(w.weekly_target("user:42"), {"user_id": "42"})
        self.assertEqual(w.weekly_target("chat:777"), {"chat_id": "777"})
        self.assertEqual(w.weekly_target("777"), {"chat_id": "777"})


if __name__ == "__main__":
    unittest.main()
