import datetime as dt
import unittest
from unittest import mock

import max_bot as b


class MaxBotTest(unittest.TestCase):
    def test_last_full_week(self):
        self.assertEqual(b.last_full_week(dt.date(2026, 7, 29)), (dt.date(2026, 7, 20), dt.date(2026, 7, 26)))

    def test_current_week(self):
        self.assertEqual(b.current_week(dt.date(2026, 7, 29)), (dt.date(2026, 7, 27), dt.date(2026, 8, 2)))

    def test_parse_ru_date(self):
        self.assertEqual(b.parse_ru_date("29.07.2026"), dt.date(2026, 7, 29))
        self.assertEqual(b.parse_ru_date("2026-07-29"), dt.date(2026, 7, 29))
        self.assertIsNone(b.parse_ru_date("29/07/2026"))

    def test_message_id_shapes(self):
        self.assertEqual(b.message_id({"message": {"body": {"mid": "m1"}}}), "m1")
        self.assertEqual(b.message_id({"body": {"mid": "m2"}}), "m2")

    def test_extract_callback_target_from_recipient(self):
        target, text, payload, callback_id = b.extract_event(
            {
                "update_type": "message_callback",
                "callback": {"callback_id": "cb1", "payload": "week", "user": {"user_id": 42}},
                "message": {"recipient": {"chat_id": 7}, "body": {"text": "old"}},
            }
        )

        self.assertEqual(target, {"chat_id": 7, "user_id": 42})
        self.assertEqual(text, "old")
        self.assertEqual(payload, "week")
        self.assertEqual(callback_id, "cb1")

    def test_callback_action_survives_answer_failure(self):
        b.sessions.clear()
        shown = []
        with mock.patch.object(b, "answer_callback", side_effect=RuntimeError("answer failed")):
            with mock.patch.object(b, "show_menu", side_effect=lambda target, text, buttons: shown.append(text)):
                b.handle({"user_id": 42}, "", "week", "cb1")

        self.assertEqual(b.sessions["42"].step, "week_court")
        self.assertIn("Выберите суд", shown[-1])


if __name__ == "__main__":
    unittest.main()
