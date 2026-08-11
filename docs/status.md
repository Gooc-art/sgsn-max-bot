# Статус проекта sgsn-max-bot

Дата фиксации: 2026-08-11.

## Версия в проде

- GitHub: `https://github.com/Gooc-art/sgsn-max-bot`
- Последний функциональный commit: `b57e60c` (`Broaden SGSN party matching`)
- Последний deploy: `31463998259`, статус `success`
- MAX setup workflow: `31463399563`, статус `success`
- Сервер: `localadmin@10.10.68.10`
- Рабочая папка: `/home/localadmin/sgsn-max-bot`
- Runner: `BOTSGSN-sgsn-max-bot`
- Service: `sgsn-max-bot.service`
- Env: `/home/localadmin/.config/sgsn-max-bot/max-bot.env`

## Что делает бот

MAX-бот запускает выгрузку судебных заседаний ЯНАО с сайтов `sudrf.ru`.
Основная выгрузка идет по всем судам из `COURTS`, если пользователь не выбрал
конкретный суд.

Файлы результата:

- `report.xlsx`
- `report.pdf`
- `report.html`
- `report.csv`
- `run_log.csv`

В `report.xlsx` есть:

- `Report` — все найденные строки;
- `СГСН участвует` — только строки, где в сторонах найдена Служба государственного строительного надзора ЯНАО.

## Фильтр СГСН

Функция: `is_sgsn_party()` в `sud_export.py`.

Учитываются варианты:

- `СГСН`
- `С.Г.С.Н.`
- `ГСН`
- `Г.С.Н.`
- `служба ГСН`
- `Служба государственного строительного надзора ...`

Широкое совпадение вроде `Департамент строительного надзора` специально не
считается СГСН, чтобы не добавлять лишние строки во вкладку.

## Запуск вручную

```bash
cd ~/sgsn-max-bot
python3 sud_export.py \
  --from 2026-08-11 \
  --to 2026-08-11 \
  --outdir output/manual \
  --timeout 8 \
  --sort-by-lawyer
```

Smoke без обогащения карточек:

```bash
python3 sud_export.py \
  --from 2026-08-11 \
  --to 2026-08-11 \
  --outdir /tmp/sgsn-one-day-smoke \
  --timeout 8 \
  --max-cases 0 \
  --sort-by-lawyer
```

Последний локальный smoke:

- дата: `2026-08-11`
- суды: все
- режим: `--max-cases 0`
- строк: `218`
- `report.xlsx` создан
- вкладка `СГСН участвует` есть

## MAX-бот

Команды:

- `/start`
- `/month`
- `/week`
- `/period`
- `/status`
- `/weekly_here`
- `/cancel`

Перезапуск:

```bash
systemctl --user restart sgsn-max-bot.service
systemctl --user status sgsn-max-bot.service --no-pager
```

## GitHub Actions

- `.github/workflows/deploy.yml` — автодеплой при push в `main`.
- `.github/workflows/max-bot.yml` — ручная настройка env и рестарт MAX-бота.
- `.github/workflows/export.yml` — ручная выгрузка.
- `.github/workflows/weekly-sgsn.yml` — воскресная проверка СГСН.

Секреты GitHub:

- `MAX_TOKEN` — токен MAX-бота. В репозиторий не записывается.

## Проверки

```bash
python3 -m py_compile sud_export.py max_bot.py weekly_sgsn_notify.py
python3 -m unittest -q
```

Последняя проверка перед деплоем:

- compile: OK
- tests: OK, `30`
- deploy: OK

## Что не сделано

Отдельный источник данных СГСН не подключен. Сейчас проект ищет участие СГСН
в судебных карточках `sudrf.ru`. Новый источник добавлять только когда он
будет известен.
