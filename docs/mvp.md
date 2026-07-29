# MVP выгрузки

## Команда

```text
sud export --month 2026-07 --out hearings.csv
```

## Колонки

- `дата`
- `время`
- `дело`
- `суд`
- `судья`
- `причина`
- `адвокат`
- `ссылка`

## Суды для первой версии

- Суд ЯНАО: `oblsud--ynao.sudrf.ru`
- Салехардский городской суд: `salehardsky--ynao.sudrf.ru`
- Ноябрьский городской суд: `noyabrsky--ynao.sudrf.ru`
- Надымский городской суд: `nadymsky--ynao.sudrf.ru`
- Новый Уренгойский городской суд: `novourengoysky--ynao.sudrf.ru`
- Муравленковский городской суд: `muravlenkovsky--ynao.sudrf.ru`
- Тазовский районный суд: `tazovsky--ynao.sudrf.ru`
- Ямальский районный суд: `yamalsky--ynao.sudrf.ru`
- Лабытнангский городской суд: `labytnangsky.ynao.sudrf.ru`

## Не делаем в первой версии

- личный кабинет
- платные тарифы
- сложную базу данных
- ML/LLM-разбор причин
- гарантии полноты данных

CSV за месяц достаточно для проверки пользы.
