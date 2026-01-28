# MOEX ISS API — Справочник

Краткий справочник по работе с API информационно-статистического сервера Московской Биржи.

## Официальные ресурсы

| Ресурс | Ссылка |
|--------|--------|
| **Интерактивный справочник API** | https://iss.moex.com/iss/reference/ |
| **Руководство разработчика (PDF)** | https://fs.moex.com/files/8888 |
| **Общая информация об индексах** | https://www.moex.com/ru/indices |
| **Методология расчёта индексов** | https://www.moex.com/s2532 |

## Базовая структура API

### URL-адреса

```
Текущие данные:    http://iss.moex.com/iss/
Исторические:      http://iss.moex.com/iss/history/
```

### Иерархия данных

```
Движки (engines)
└── Рынки (markets)
    └── Режимы торгов (boards)
        └── Инструменты (securities)
```

## Основные движки

| Движок | Код | Описание |
|--------|-----|----------|
| Фондовый рынок | `stock` | Акции, облигации, индексы |
| Валютный рынок | `currency` | Валютные пары |
| Срочный рынок | `futures` | Фьючерсы, опционы |
| Товарный рынок | `commodity` | Товарные контракты |

## Рынки фондового движка

| Рынок | Код | Описание |
|-------|-----|----------|
| Индексы | `index` | Биржевые индексы |
| Акции | `shares` | Обыкновенные и привилегированные акции |
| Облигации | `bonds` | Корпоративные и государственные |
| РЕПО | `repo` | Операции РЕПО |

## Режимы торгов (boards)

| Режим | Описание | Используется для |
|-------|----------|------------------|
| `SNDX` | Основной режим индексов | Большинство индексов |
| `RTSI` | Режим RTS | Индекс RTS |
| `TQBR` | Т+ режим (основной для акций) | Акции |
| `TQCB` | Корпоративные облигации | Корп. облигации |
| `TQOB` | Государственные облигации | ОФЗ |

## Примеры API запросов

### Получить список движков

```bash
curl "http://iss.moex.com/iss/engines.json"
```

**Ответ:**
```json
{
  "engines": {
    "columns": ["id", "name", "title"],
    "data": [
      [1, "stock", "Фондовый рынок и рынок депозитов"],
      [2, "state", "Рынок ГЦБ"],
      ...
    ]
  }
}
```

### Получить рынки движка

```bash
curl "http://iss.moex.com/iss/engines/stock/markets.json"
```

### Получить список индексов

```bash
curl "http://iss.moex.com/iss/engines/stock/markets/index/securities.json"
```

### Получить исторические данные

```bash
# Данные по IMOEX за январь 2024
curl "http://iss.moex.com/iss/history/engines/stock/markets/index/boards/SNDX/securities/IMOEX.json?from=2024-01-01&till=2024-01-31"
```

### Параметры запроса исторических данных

| Параметр | Описание | Пример |
|----------|----------|--------|
| `from` | Начальная дата | `2024-01-01` |
| `till` | Конечная дата | `2024-12-31` |
| `start` | Смещение для пагинации | `0`, `100`, `200` |
| `lang` | Язык ответа | `ru`, `en` |

## Пагинация

MOEX ISS возвращает максимум **100 записей** за один запрос.

Для получения всех данных используйте параметр `start`:

```bash
# Первые 100 записей
curl "...?from=2024-01-01&start=0"

# Следующие 100 записей
curl "...?from=2024-01-01&start=100"

# И так далее
curl "...?from=2024-01-01&start=200"
```

## Формат ответа

### JSON структура

```json
{
  "history": {
    "columns": ["BOARDID", "TRADEDATE", "SECID", "OPEN", "HIGH", "LOW", "CLOSE", "VALUE"],
    "data": [
      ["SNDX", "2024-01-09", "IMOEX", 3099.15, 3120.45, 3095.20, 3115.30, 12345678],
      ...
    ]
  },
  "history.cursor": {
    "columns": ["INDEX", "TOTAL", "PAGESIZE"],
    "data": [[0, 250, 100]]
  }
}
```

### Основные колонки исторических данных

| Колонка | Описание |
|---------|----------|
| `TRADEDATE` | Дата торгов |
| `SECID` | Код инструмента |
| `OPEN` | Цена открытия |
| `HIGH` | Максимум |
| `LOW` | Минимум |
| `CLOSE` | Цена закрытия |
| `VALUE` | Объём торгов (руб.) |
| `VOLUME` | Объём торгов (шт.) |

## Работа с Python

### Базовый пример

```python
import requests
import pandas as pd

def get_index_data(index_code, start_date, end_date):
    """Получить данные индекса с MOEX ISS API."""
    url = f"http://iss.moex.com/iss/history/engines/stock/markets/index/boards/SNDX/securities/{index_code}.json"

    params = {
        'from': start_date,
        'till': end_date,
        'start': 0
    }

    all_data = []

    while True:
        response = requests.get(url, params=params)
        data = response.json()

        rows = data['history']['data']
        if not rows:
            break

        all_data.extend(rows)
        params['start'] += 100

    columns = data['history']['columns']
    return pd.DataFrame(all_data, columns=columns)

# Использование
df = get_index_data('IMOEX', '2024-01-01', '2024-12-31')
print(df.head())
```

## Ограничения и рекомендации

1. **Нет официальных лимитов** на количество запросов, но рекомендуется делать паузы 0.5-1 сек между запросами

2. **Максимум 100 записей** за один запрос — используйте пагинацию

3. **Данные задерживаются** на 15 минут для бесплатного доступа

4. **Нет данных** за выходные и праздничные дни

5. **Исторические данные** доступны с 2006 года для большинства индексов

## Полезные эндпоинты

| Что получить | URL |
|--------------|-----|
| Все движки | `/iss/engines.json` |
| Рынки движка | `/iss/engines/{engine}/markets.json` |
| Режимы рынка | `/iss/engines/{engine}/markets/{market}/boards.json` |
| Инструменты | `/iss/engines/{engine}/markets/{market}/securities.json` |
| История | `/iss/history/engines/{engine}/markets/{market}/boards/{board}/securities/{secid}.json` |
| Справка об инструменте | `/iss/securities/{secid}.json` |

## Обработка ошибок

| HTTP код | Описание |
|----------|----------|
| 200 | Успех |
| 400 | Неверный запрос |
| 404 | Инструмент не найден |
| 500 | Ошибка сервера |

При ошибке API возвращает пустой массив `data: []`.
