#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import queue
import re
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path

from sud_export import COURTS


API_BASE = os.environ.get("MAX_API_BASE", "https://platform-api2.max.ru")
TOKEN = os.environ.get("MAX_TOKEN", "")
MAX_DAYS = int(os.environ.get("SUD_MAX_DAYS", "31"))


@dataclass
class Session:
    step: str = ""
    date_from: date | None = None
    date_to: date | None = None
    court: str | None = None
    last_job: str | None = None


@dataclass
class Job:
    id: str
    target: dict
    date_from: date
    date_to: date
    court: str | None
    outdir: Path
    status: str = "queued"
    rows: int = 0
    error: str = ""
    started_at: float = field(default_factory=time.time)


sessions: dict[str, Session] = {}
jobs: dict[str, Job] = {}
job_queue: queue.Queue[Job] = queue.Queue()


def request(method: str, path: str, params: dict | None = None, body: dict | None = None) -> dict:
    if not TOKEN:
        raise RuntimeError("MAX_TOKEN is not set")
    url = API_BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params, doseq=True)
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Authorization": TOKEN}
    if body is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=95) as resp:
        raw = resp.read()
    return json.loads(raw.decode() or "{}")


def multipart_upload(url: str, path: Path) -> dict:
    boundary = "----sud" + uuid.uuid4().hex
    ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    head = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="data"; filename="{path.name}"\r\n'
        f"Content-Type: {ctype}\r\n\r\n"
    ).encode()
    tail = f"\r\n--{boundary}--\r\n".encode()
    data = head + path.read_bytes() + tail
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}", "Content-Length": str(len(data))},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode() or "{}")


def target_params(target: dict) -> dict:
    if target.get("chat_id"):
        return {"chat_id": target["chat_id"]}
    return {"user_id": target["user_id"]}


def keyboard(rows: list[list[tuple[str, str]]]) -> dict:
    return {
        "type": "inline_keyboard",
        "payload": {
            "buttons": [[{"type": "callback", "text": text, "payload": payload} for text, payload in row] for row in rows]
        },
    }


def send_text(target: dict, text: str, buttons: list[list[tuple[str, str]]] | None = None) -> None:
    body = {"text": text[:4000]}
    if buttons:
        body["attachments"] = [keyboard(buttons)]
    request("POST", "/messages", target_params(target), body)
    time.sleep(0.55)


def answer_callback(callback_id: str, text: str = "") -> None:
    if callback_id:
        request("POST", "/answers", {"callback_id": callback_id}, {"message": {"text": text or "Принято"}})


def upload_and_send_file(target: dict, path: Path, caption: str) -> None:
    upload = request("POST", "/uploads", {"type": "file"})
    payload = multipart_upload(upload["url"], path)
    body = {"text": caption, "attachments": [{"type": "file", "payload": payload}]}
    for delay in (1, 2, 4):
        time.sleep(delay)
        try:
            request("POST", "/messages", target_params(target), body)
            time.sleep(0.55)
            return
        except Exception:
            if delay == 4:
                raise


def main_buttons() -> list[list[tuple[str, str]]]:
    return [[("За прошлую неделю", "week")], [("Выбрать период", "period"), ("Статус", "status")]]


def court_buttons(prefix: str) -> list[list[tuple[str, str]]]:
    rows = [[("Все суды", f"{prefix}:all")]]
    rows += [[(name.replace(" городской суд", ""), f"{prefix}:{host}")] for host, name in COURTS.items()]
    rows.append([("Отмена", "cancel")])
    return rows


def last_full_week(today: date | None = None) -> tuple[date, date]:
    today = today or date.today()
    this_monday = today - timedelta(days=today.weekday())
    start = this_monday - timedelta(days=7)
    return start, start + timedelta(days=6)


def parse_ru_date(text: str) -> date | None:
    text = text.strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    return None


def session_key(target: dict) -> str:
    return str(target.get("chat_id") or target["user_id"])


def rows_count(csv_path: Path) -> int:
    if not csv_path.exists():
        return 0
    with csv_path.open(encoding="utf-8-sig", errors="replace") as f:
        return max(0, sum(1 for _ in f) - 1)


def start_job(target: dict, start: date, end: date, court: str | None) -> Job:
    if (end - start).days + 1 > MAX_DAYS:
        raise ValueError(f"Период слишком большой. Максимум: {MAX_DAYS} дней.")
    job_id = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
    outdir = Path("output") / "bot" / job_id
    job = Job(job_id, target, start, end, court, outdir)
    jobs[job_id] = job
    sessions.setdefault(session_key(target), Session()).last_job = job_id
    job_queue.put(job)
    return job


def worker() -> None:
    while True:
        job = job_queue.get()
        job.status = "running"
        try:
            cmd = [
                sys.executable,
                "sud_export.py",
                "--from",
                job.date_from.isoformat(),
                "--to",
                job.date_to.isoformat(),
                "--outdir",
                str(job.outdir),
                "--timeout",
                "8",
            ]
            if job.court:
                cmd += ["--court", job.court]
            result = subprocess.run(cmd, text=True, capture_output=True, timeout=60 * 60)
            if result.returncode:
                raise RuntimeError((result.stderr or result.stdout).strip())
            match = re.search(r"rows=(\d+)", result.stdout)
            job.rows = int(match.group(1)) if match else rows_count(job.outdir / "report.csv")
            job.status = "done"
            send_text(job.target, f"Готово. Найдено записей: {job.rows}. Отправляю файлы.")
            for name, caption in (
                ("report.xlsx", "Excel-отчет"),
                ("report.pdf", "PDF-версия"),
                ("report.html", "HTML-отчет"),
                ("report.csv", "CSV-данные"),
            ):
                path = job.outdir / name
                if path.exists():
                    upload_and_send_file(job.target, path, caption)
            log = job.outdir / "run_log.csv"
            if log.exists() and log.stat().st_size > 64:
                upload_and_send_file(job.target, log, "Лог выполнения")
            send_text(job.target, "Можно запускать новую выгрузку.", main_buttons())
        except Exception as exc:
            job.status = "error"
            job.error = str(exc)
            send_text(job.target, f"Выгрузка не завершилась: {job.error[:1000]}")
            log = job.outdir / "run_log.csv"
            if log.exists():
                upload_and_send_file(job.target, log, "Лог выполнения")
        finally:
            job_queue.task_done()


def extract_event(update: dict) -> tuple[dict, str, str, str]:
    callback = update.get("callback") or update.get("message_callback") or {}
    message = update.get("message") or update.get("message_created", {}).get("message") or {}
    body = message.get("body") or {}
    text = body.get("text") or message.get("text") or ""
    payload = callback.get("payload") or ""
    callback_id = callback.get("callback_id") or ""
    chat = message.get("chat") or callback.get("chat") or {}
    user = message.get("sender") or message.get("user") or callback.get("user") or {}
    target = {}
    if chat.get("chat_id") or message.get("chat_id") or callback.get("chat_id"):
        target["chat_id"] = chat.get("chat_id") or message.get("chat_id") or callback.get("chat_id")
    target["user_id"] = user.get("user_id") or message.get("user_id") or callback.get("user_id")
    return target, text.strip(), payload.strip(), callback_id


def handle(target: dict, text: str, payload: str = "", callback_id: str = "") -> None:
    if not target.get("user_id") and not target.get("chat_id"):
        return
    key = session_key(target)
    sess = sessions.setdefault(key, Session())
    action = payload or text
    if callback_id:
        answer_callback(callback_id, "Принято")

    if action in {"/start", "start", "Старт"}:
        send_text(target, "Бот делает выгрузку судебных дел ЯНАО в Excel/PDF/CSV.", main_buttons())
    elif action in {"/week", "week"}:
        sess.date_from, sess.date_to = last_full_week()
        sess.step = "week_court"
        send_text(target, f"Период: {sess.date_from:%d.%m.%Y}-{sess.date_to:%d.%m.%Y}. Выберите суд.", court_buttons("run"))
    elif action in {"/period", "period"}:
        sess.step = "from"
        send_text(target, "Введите дату начала в формате ДД.ММ.ГГГГ.")
    elif action == "status" or action == "/status":
        job = jobs.get(sess.last_job or "")
        if not job:
            send_text(target, "Задач пока нет.", main_buttons())
        else:
            send_text(target, f"Последняя задача: {job.status}. Записей: {job.rows}. Ошибка: {job.error or '-'}", main_buttons())
    elif action in {"cancel", "/cancel"}:
        sess.step = ""
        send_text(target, "Отменено.", main_buttons())
    elif action.startswith("run:"):
        court = action.split(":", 1)[1]
        court = None if court == "all" else court
        try:
            job = start_job(target, sess.date_from or date.today(), sess.date_to or date.today(), court)
            send_text(target, f"Принял. Готовлю выгрузку {job.date_from:%d.%m.%Y}-{job.date_to:%d.%m.%Y}.")
        except ValueError as exc:
            send_text(target, str(exc), main_buttons())
    elif sess.step == "from":
        parsed = parse_ru_date(text)
        if not parsed:
            send_text(target, "Не понял дату. Введите в формате ДД.ММ.ГГГГ, например 29.07.2026.")
            return
        sess.date_from = parsed
        sess.step = "to"
        send_text(target, "Введите дату окончания в формате ДД.ММ.ГГГГ.")
    elif sess.step == "to":
        parsed = parse_ru_date(text)
        if not parsed:
            send_text(target, "Не понял дату. Введите в формате ДД.ММ.ГГГГ, например 29.07.2026.")
            return
        if sess.date_from and parsed < sess.date_from:
            send_text(target, "Дата окончания не может быть раньше даты начала.")
            return
        sess.date_to = parsed
        sess.step = "period_court"
        send_text(target, "Выберите суд.", court_buttons("run"))
    else:
        send_text(target, "Выберите действие.", main_buttons())


def poll() -> None:
    marker = None
    while True:
        params = {"limit": 20, "timeout": 30, "types": ["message_created", "message_callback"]}
        if marker is not None:
            params["marker"] = marker
        data = request("GET", "/updates", params)
        marker = data.get("marker", marker)
        for update in data.get("updates") or []:
            try:
                handle(*extract_event(update))
            except Exception as exc:
                print(f"update error: {exc}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--poll", action="store_true", help="run MAX long polling bot")
    args = parser.parse_args()
    if not args.poll:
        parser.error("use --poll")
    threading.Thread(target=worker, daemon=True).start()
    poll()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
