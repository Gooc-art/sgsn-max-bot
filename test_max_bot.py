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

    def test_extract_nested_message_callback(self):
        target, text, payload, callback_id = b.extract_event(
            {
                "update_type": "message_callback",
                "message_callback": {
                    "callback": {"callback_id": "cb1", "payload": "week", "user": {"user_id": 42}},
                    "message": {"recipient": {"chat_id": 7}, "body": {"text": "old"}},
                },
            }
        )

        self.assertEqual(target, {"chat_id": 7, "user_id": 42})
        self.assertEqual(text, "old")
        self.assertEqual(payload, "week")
        self.assertEqual(callback_id, "cb1")

    def test_callback_action_survives_answer_failure(self):
        b.sessions.clear()
        shown = []
        with mock.patch.object(b, "ack_callback", side_effect=RuntimeError("answer failed")):
            with mock.patch.object(b, "show_menu", side_effect=lambda target, text, buttons: shown.append(text)):
                b.handle({"user_id": 42}, "", "week", "cb1")

        self.assertEqual(b.sessions["42"].step, "week_court")
        self.assertIn("Выберите суд", shown[-1])

    def test_callback_ack_happens_after_action(self):
        b.sessions.clear()
        calls = []
        with mock.patch.object(b, "show_menu", side_effect=lambda *args: calls.append("show")):
            with mock.patch.object(b, "ack_callback", side_effect=lambda callback_id: calls.append("ack")):
                b.handle({"user_id": 42}, "", "week", "cb1")

        self.assertEqual(calls, ["show", "ack"])

    def test_answer_callback_uses_notification(self):
        with mock.patch.object(b, "request") as req:
            b.answer_callback("cb1", "OK")

        req.assert_called_once_with("POST", "/answers", {"callback_id": "cb1"}, {"notification": "OK"})

    def test_all_button_payloads_route_to_non_fallback(self):
        b.sessions.clear()
        target = {"user_id": 42}
        b.sessions["42"] = b.Session(date_from=dt.date(2026, 7, 20), date_to=dt.date(2026, 7, 26))
        payloads = {
            payload
            for keyboard_rows in (b.main_buttons(), b.period_buttons(), b.court_buttons("court"), b.confirm_buttons())
            for row in keyboard_rows
            for _, payload in row
        }
        shown = []

        def show_menu(_target, text, _buttons):
            shown.append(text)

        with mock.patch.object(b, "show_menu", side_effect=show_menu):
            with mock.patch.object(b, "ack_callback"):
                with mock.patch.object(b, "start_job", side_effect=lambda *args: b.Job("j1", target, args[1], args[2], args[3], b.Path("out"))):
                    for payload in sorted(payloads):
                        shown.clear()
                        b.handle(target, "", payload, "cb1")
                        self.assertTrue(shown, payload)
                        self.assertNotEqual(shown[-1], "Выберите действие.", payload)

    def test_stale_court_button_without_period_asks_for_period(self):
        b.sessions.clear()
        shown = []
        with mock.patch.object(b, "show_menu", side_effect=lambda _target, text, _buttons: shown.append(text)):
            with mock.patch.object(b, "ack_callback") as ack:
                b.handle({"user_id": 42}, "", "court:all", "cb1")

        ack.assert_called_once_with("cb1")
        self.assertEqual(b.sessions["42"].step, "period")
        self.assertEqual(shown[-1], "Сначала выберите период выгрузки.")

    def test_stale_confirm_button_without_period_does_not_start_job(self):
        b.sessions.clear()
        shown = []
        with mock.patch.object(b, "show_menu", side_effect=lambda _target, text, _buttons: shown.append(text)):
            with mock.patch.object(b, "ack_callback") as ack:
                with mock.patch.object(b, "start_job") as start_job:
                    b.handle({"user_id": 42}, "", "run_confirm", "cb1")

        ack.assert_called_once_with("cb1")
        start_job.assert_not_called()
        self.assertEqual(b.sessions["42"].step, "period")
        self.assertEqual(shown[-1], "Сначала выберите период выгрузки.")


if __name__ == "__main__":
    unittest.main()
