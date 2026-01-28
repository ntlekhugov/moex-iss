# -*- coding: utf-8 -*-
"""
MOEX ISS API Клиент
===================

Модуль предоставляет класс MOEXClient для работы с API Московской Биржи.

Документация MOEX ISS API:
- Официальная документация: https://iss.moex.com/iss/reference/
- Руководство разработчика: https://fs.moex.com/files/8888

Структура API:
-------------
MOEX ISS API организован иерархически:

    Движки (engines) → Рынки (markets) → Режимы торгов (boards) → Инструменты (securities)

Основные движки:
- stock    — Фондовый рынок (акции, облигации, индексы)
- currency — Валютный рынок
- futures  — Срочный рынок (фьючерсы, опционы)

Примеры использования:
---------------------
    from moex_iss import MOEXClient

    client = MOEXClient()

    # Получить список всех индексов
    indices = client.get_available_indices()

    # Скачать исторические данные
    df = client.get_index_history('IMOEX', start_date='2024-01-01')

    # Исследовать структуру API
    engines = client.get_engines()
    markets = client.get_markets('stock')
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

import pandas as pd
import requests

# ============================================================================
# Настройка логирования
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Константы MOEX ISS API
# ============================================================================

# Базовые URL-адреса API
BASE_URL = "http://iss.moex.com/iss"
HISTORY_URL = "http://iss.moex.com/iss/history"

# Движки (engines) — верхний уровень структуры API
ENGINE_STOCK = "stock"          # Фондовый рынок
ENGINE_CURRENCY = "currency"    # Валютный рынок
ENGINE_FUTURES = "futures"      # Срочный рынок
ENGINE_COMMODITY = "commodity"  # Товарный рынок

# Рынки (markets) в рамках фондового движка
MARKET_INDEX = "index"          # Индексы
MARKET_SHARES = "shares"        # Акции
MARKET_BONDS = "bonds"          # Облигации
MARKET_REPO = "repo"            # Репо

# Режимы торгов (boards) — определяют правила торговли
BOARD_SNDX = "SNDX"   # Основной режим для индексов
BOARD_RTSI = "RTSI"   # Режим для RTS индексов
BOARD_TQBR = "TQBR"   # Т+ режим для акций (основной)
BOARD_TQCB = "TQCB"   # Режим для корпоративных облигаций
BOARD_TQOB = "TQOB"   # Режим для государственных облигаций


class MOEXClient:
    """
    Клиент для работы с MOEX ISS API.

    Позволяет получать данные о торгах на Московской Бирже:
    - Индексы (IMOEX, RGBI, секторные индексы и др.)
    - Исторические котировки
    - Справочную информацию об инструментах

    Атрибуты:
    ---------
    BASE_URL : str
        Базовый URL для текущих данных
    HISTORY_URL : str
        URL для исторических данных

    Примеры:
    --------
    >>> client = MOEXClient()
    >>> df = client.get_index_history('IMOEX', start_date='2024-01-01')
    >>> print(df.head())
    """

    # URL-адреса API как атрибуты класса (для удобства наследования)
    BASE_URL = BASE_URL
    HISTORY_URL = HISTORY_URL

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Инициализация клиента MOEX ISS API.

        Параметры:
        ----------
        username : str, optional
            Имя пользователя для аутентификации (обычно не требуется)
        password : str, optional
            Пароль для аутентификации (обычно не требуется)
        timeout : int, default=30
            Таймаут запросов в секундах

        Примечание:
        ----------
        Большинство данных MOEX ISS доступны без аутентификации.
        Логин/пароль нужны только для специальных сервисов.
        """
        self.username = username
        self.password = password
        self.timeout = timeout

        # Создаём сессию для переиспользования соединений
        # (ускоряет множественные запросы)
        self.session = requests.Session()

        # Настраиваем аутентификацию, если указаны учётные данные
        if username and password:
            self.session.auth = (username, password)

    # ========================================================================
    # Приватные методы для работы с HTTP запросами
    # ========================================================================

    def _make_request(
        self,
        url: str,
        params: Optional[Dict] = None
    ) -> requests.Response:
        """
        Выполняет HTTP запрос к MOEX ISS API.

        Параметры:
        ----------
        url : str
            URL для запроса (без .json расширения)
        params : dict, optional
            Параметры запроса (будут добавлены в URL)

        Возвращает:
        -----------
        requests.Response
            Объект ответа сервера

        Исключения:
        -----------
        requests.RequestException
            При ошибке сети или сервера
        """
        if params is None:
            params = {}

        # По умолчанию запрашиваем английский язык
        # (можно изменить на 'ru' для русских названий)
        if 'lang' not in params:
            params['lang'] = 'ru'

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()  # Проверяем HTTP статус
            return response

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса к {url}: {str(e)}")
            raise

    def _get_json_data(
        self,
        url: str,
        params: Optional[Dict] = None
    ) -> Dict:
        """
        Получает JSON данные из MOEX ISS API.

        Параметры:
        ----------
        url : str
            URL для запроса (без .json расширения)
        params : dict, optional
            Параметры запроса

        Возвращает:
        -----------
        dict
            Словарь с данными ответа

        Примечание:
        ----------
        Автоматически добавляет .json к URL для получения JSON формата.
        По умолчанию MOEX возвращает XML.
        """
        response = self._make_request(url + '.json', params)
        return response.json()

    # ========================================================================
    # Методы для исследования структуры API
    # ========================================================================

    def get_engines(self) -> pd.DataFrame:
        """
        Получает список доступных движков (engines).

        Движок — это верхний уровень иерархии MOEX ISS API.
        Каждый движок соответствует определённому типу рынка.

        Возвращает:
        -----------
        pd.DataFrame
            Таблица с информацией о движках:
            - id: идентификатор движка
            - name: название (stock, currency, futures, etc.)
            - title: описание на русском

        Примеры:
        --------
        >>> client = MOEXClient()
        >>> engines = client.get_engines()
        >>> print(engines[['name', 'title']])
        """
        url = f"{self.BASE_URL}/engines"
        data = self._get_json_data(url)
        return pd.DataFrame(
            data['engines']['data'],
            columns=data['engines']['columns']
        )

    def get_markets(self, engine: str) -> pd.DataFrame:
        """
        Получает список рынков для указанного движка.

        Рынок — это второй уровень иерархии API.
        Например, в движке 'stock' есть рынки: shares, bonds, index.

        Параметры:
        ----------
        engine : str
            Название движка ('stock', 'currency', 'futures')

        Возвращает:
        -----------
        pd.DataFrame
            Таблица с информацией о рынках:
            - id: идентификатор рынка
            - market_name: название (shares, bonds, index)
            - title: описание на русском

        Примеры:
        --------
        >>> client = MOEXClient()
        >>> markets = client.get_markets('stock')
        >>> print(markets[['market_name', 'title']])
        """
        url = f"{self.BASE_URL}/engines/{engine}/markets"
        data = self._get_json_data(url)
        return pd.DataFrame(
            data['markets']['data'],
            columns=data['markets']['columns']
        )

    def get_boards(self, engine: str, market: str) -> pd.DataFrame:
        """
        Получает список режимов торгов (boards) для рынка.

        Режим торгов определяет правила совершения сделок:
        - тип расчётов (T+0, T+1, T+2)
        - валюту расчётов
        - тип котировок

        Параметры:
        ----------
        engine : str
            Название движка ('stock')
        market : str
            Название рынка ('index', 'shares', 'bonds')

        Возвращает:
        -----------
        pd.DataFrame
            Таблица с информацией о режимах торгов

        Примеры:
        --------
        >>> client = MOEXClient()
        >>> boards = client.get_boards('stock', 'index')
        >>> print(boards[['boardid', 'title']])
        """
        url = f"{self.BASE_URL}/engines/{engine}/markets/{market}/boards"
        data = self._get_json_data(url)
        return pd.DataFrame(
            data['boards']['data'],
            columns=data['boards']['columns']
        )

    def get_securities(
        self,
        engine: str,
        market: str,
        board: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Получает список инструментов (ценных бумаг).

        Параметры:
        ----------
        engine : str
            Название движка ('stock')
        market : str
            Название рынка ('index', 'shares', 'bonds')
        board : str, optional
            Режим торгов (если не указан, вернёт все инструменты рынка)

        Возвращает:
        -----------
        pd.DataFrame
            Таблица с информацией об инструментах:
            - SECID: тикер инструмента (IMOEX, SBER, etc.)
            - SHORTNAME: краткое название
            - BOARDID: режим торгов

        Примеры:
        --------
        >>> client = MOEXClient()
        >>> indices = client.get_securities('stock', 'index')
        >>> print(indices[['SECID', 'SHORTNAME']].head(10))
        """
        if board:
            url = f"{self.BASE_URL}/engines/{engine}/markets/{market}/boards/{board}/securities"
        else:
            url = f"{self.BASE_URL}/engines/{engine}/markets/{market}/securities"

        data = self._get_json_data(url)
        return pd.DataFrame(
            data['securities']['data'],
            columns=data['securities']['columns']
        )

    def get_available_indices(self) -> pd.DataFrame:
        """
        Получает список всех доступных индексов.

        Удобный метод-обёртка для get_securities('stock', 'index').

        Возвращает:
        -----------
        pd.DataFrame
            Таблица всех индексов MOEX

        Примеры:
        --------
        >>> client = MOEXClient()
        >>> indices = client.get_available_indices()
        >>> print(indices[['SECID', 'SHORTNAME']].head())
        """
        return self.get_securities('stock', 'index')

    # ========================================================================
    # Методы для получения исторических данных
    # ========================================================================

    def get_index_history(
        self,
        index_code: str,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
        board: str = "SNDX"
    ) -> pd.DataFrame:
        """
        Получает исторические данные по индексу.

        Параметры:
        ----------
        index_code : str
            Код индекса (IMOEX, RGBI, MOEXOG, etc.)
        start_date : str или datetime, optional
            Начальная дата (формат 'YYYY-MM-DD'). По умолчанию: 30 дней назад
        end_date : str или datetime, optional
            Конечная дата (формат 'YYYY-MM-DD'). По умолчанию: сегодня
        board : str, default='SNDX'
            Режим торгов. Для большинства индексов — 'SNDX',
            для RTS индексов — 'RTSI'

        Возвращает:
        -----------
        pd.DataFrame
            Таблица с историческими данными:
            - TRADEDATE: дата торгов
            - OPEN: цена открытия
            - HIGH: максимум дня
            - LOW: минимум дня
            - CLOSE: цена закрытия
            - VALUE: объём торгов в рублях

        Примеры:
        --------
        >>> client = MOEXClient()
        >>> df = client.get_index_history('IMOEX', start_date='2024-01-01')
        >>> print(df.head())
        """
        return self.get_historical_data(
            engine='stock',
            market='index',
            board=board,
            security=index_code,
            from_date=start_date,
            till_date=end_date
        )

    def get_historical_data(
        self,
        engine: str,
        market: str,
        board: str,
        security: str,
        from_date: Optional[Union[str, datetime]] = None,
        till_date: Optional[Union[str, datetime]] = None,
        interval: int = 24  # Дневные данные
    ) -> pd.DataFrame:
        """
        Получает исторические данные по инструменту.

        Универсальный метод для получения исторических котировок
        любого инструмента MOEX.

        Параметры:
        ----------
        engine : str
            Движок ('stock', 'currency', 'futures')
        market : str
            Рынок ('index', 'shares', 'bonds')
        board : str
            Режим торгов ('SNDX', 'TQBR', etc.)
        security : str
            Тикер инструмента (IMOEX, SBER, etc.)
        from_date : str или datetime, optional
            Начальная дата. По умолчанию: 30 дней назад
        till_date : str или datetime, optional
            Конечная дата. По умолчанию: сегодня
        interval : int, default=24
            Интервал в часах (24 = дневные данные)

        Возвращает:
        -----------
        pd.DataFrame
            Таблица с историческими данными.
            Колонки зависят от типа инструмента.

        Примечание:
        ----------
        Метод автоматически обрабатывает пагинацию — MOEX ISS
        возвращает не более 100 записей за один запрос.
        """
        # Устанавливаем даты по умолчанию
        if from_date is None:
            from_date = datetime.now() - timedelta(days=30)
        if till_date is None:
            till_date = datetime.now()

        # Приводим даты к строковому формату
        if isinstance(from_date, datetime):
            from_date = from_date.strftime('%Y-%m-%d')
        if isinstance(till_date, datetime):
            till_date = till_date.strftime('%Y-%m-%d')

        # Формируем URL запроса
        url = (
            f"{self.HISTORY_URL}/engines/{engine}/markets/{market}"
            f"/boards/{board}/securities/{security}"
        )

        # Параметры запроса
        params = {
            'from': from_date,
            'till': till_date,
            'interval': interval,
            'start': 0  # Начинаем с первой записи
        }

        # Получаем первую порцию данных
        data = self._get_json_data(url, params)

        # Проверяем наличие данных
        if 'history' not in data or not data['history']['data']:
            logger.warning(
                f"Нет данных для {security} за период {from_date} — {till_date}"
            )
            return pd.DataFrame()

        # Создаём DataFrame из первой порции
        df = pd.DataFrame(
            data['history']['data'],
            columns=data['history']['columns']
        )

        # Обрабатываем пагинацию (MOEX возвращает до 100 записей за раз)
        # Проверяем, есть ли ещё данные
        cursor_data = data.get('history.cursor', {}).get('data', [[0, 0, 0]])
        if cursor_data:
            total_records = cursor_data[0][1]  # Общее количество записей

            # Загружаем оставшиеся страницы
            while len(df) < total_records:
                params['start'] = len(df)
                more_data = self._get_json_data(url, params)

                if 'history' in more_data and more_data['history']['data']:
                    more_df = pd.DataFrame(
                        more_data['history']['data'],
                        columns=more_data['history']['columns']
                    )
                    df = pd.concat([df, more_df], ignore_index=True)
                else:
                    break  # Нет больше данных

        # Преобразуем колонку даты
        if 'TRADEDATE' in df.columns:
            df['TRADEDATE'] = pd.to_datetime(df['TRADEDATE'])
            df = df.sort_values('TRADEDATE')

        logger.info(
            f"Загружено {len(df)} записей для {security} "
            f"за период {from_date} — {till_date}"
        )

        return df

    # ========================================================================
    # Утилиты для сохранения данных
    # ========================================================================

    def download_to_csv(
        self,
        index_code: str,
        output_path: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        board: str = "SNDX"
    ) -> bool:
        """
        Скачивает данные индекса и сохраняет в CSV файл.

        Параметры:
        ----------
        index_code : str
            Код индекса (IMOEX, RGBI, etc.)
        output_path : str
            Путь для сохранения CSV файла
        start_date : str, optional
            Начальная дата ('YYYY-MM-DD')
        end_date : str, optional
            Конечная дата ('YYYY-MM-DD')
        board : str, default='SNDX'
            Режим торгов

        Возвращает:
        -----------
        bool
            True если данные успешно сохранены, False в случае ошибки

        Примеры:
        --------
        >>> client = MOEXClient()
        >>> client.download_to_csv('IMOEX', 'imoex_2024.csv', '2024-01-01')
        True
        """
        try:
            df = self.get_index_history(
                index_code,
                start_date=start_date,
                end_date=end_date,
                board=board
            )

            if df.empty:
                logger.warning(f"Нет данных для сохранения: {index_code}")
                return False

            # Преобразуем дату в строку для CSV
            if 'TRADEDATE' in df.columns:
                df['TRADEDATE'] = df['TRADEDATE'].dt.strftime('%Y-%m-%d')

            df.to_csv(output_path, index=False, encoding='utf-8')
            logger.info(f"Данные сохранены в {output_path}")
            return True

        except Exception as e:
            logger.error(f"Ошибка при сохранении {index_code}: {e}")
            return False


# ============================================================================
# Точка входа для тестирования модуля
# ============================================================================

if __name__ == "__main__":
    # Демонстрация работы клиента
    print("=" * 60)
    print("Демонстрация MOEX ISS API клиента")
    print("=" * 60)

    client = MOEXClient()

    # Показываем доступные движки
    print("\n1. Доступные движки (engines):")
    engines = client.get_engines()
    print(engines[['name', 'title']].to_string(index=False))

    # Показываем рынки фондового движка
    print("\n2. Рынки фондового движка (stock):")
    markets = client.get_markets('stock')
    if 'market_name' in markets.columns:
        print(markets[['market_name', 'title']].head(10).to_string(index=False))

    # Показываем несколько индексов
    print("\n3. Примеры индексов:")
    indices = client.get_available_indices()
    print(indices[['SECID', 'SHORTNAME']].head(10).to_string(index=False))

    # Скачиваем данные по IMOEX
    print("\n4. Данные по IMOEX за последние 10 дней:")
    df = client.get_index_history('IMOEX')
    if not df.empty:
        print(df[['TRADEDATE', 'OPEN', 'CLOSE', 'VALUE']].tail(10).to_string(index=False))
