# -*- coding: utf-8 -*-
"""
Модуль для загрузки индексов MOEX
=================================

Содержит:
- Полные списки индексов акций и облигаций
- Функции для пакетной загрузки данных
- Утилиты для работы с файлами

Использование:
-------------
    from moex_iss import download_bond_indices, download_equity_indices

    # Скачать все индексы облигаций
    download_bond_indices(output_dir='./data')

    # Скачать определённые индексы акций
    download_equity_indices(['IMOEX', 'MOEXOG'], output_dir='./data')
"""

import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union

import pandas as pd

from .client import MOEXClient

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# СПИСКИ ИНДЕКСОВ ОБЛИГАЦИЙ
# ============================================================================

BOND_INDICES: Dict[str, Dict] = {
    # ========== ГОСУДАРСТВЕННЫЕ ОБЛИГАЦИИ (ОФЗ) ==========
    # Основные индексы
    "RGBI": {
        "name_ru": "Индекс государственных облигаций",
        "name_en": "Government Bond Index",
        "type": "government",
        "board": "SNDX",
        "description": "Ценовой индекс ОФЗ (без учёта купонов)"
    },
    "RGBITR": {
        "name_ru": "Индекс гособлигаций полной доходности",
        "name_en": "Government Bond Total Return Index",
        "type": "government",
        "board": "SNDX",
        "description": "Индекс ОФЗ с учётом реинвестирования купонов"
    },

    # По дюрации (срокам погашения)
    "RUGBITR1Y": {
        "name_ru": "ОФЗ до 1 года (полная доходность)",
        "name_en": "Government Bonds <1Y Total Return",
        "type": "government",
        "board": "SNDX",
        "description": "Краткосрочные ОФЗ — низкая чувствительность к ставке"
    },
    "RUGBITR3Y": {
        "name_ru": "ОФЗ 1-3 года (полная доходность)",
        "name_en": "Government Bonds 1-3Y Total Return",
        "type": "government",
        "board": "SNDX",
        "description": "Среднесрочные ОФЗ"
    },
    "RUGBITR5Y": {
        "name_ru": "ОФЗ 3-5 лет (полная доходность)",
        "name_en": "Government Bonds 3-5Y Total Return",
        "type": "government",
        "board": "SNDX",
        "description": "Среднесрочные ОФЗ"
    },
    "RUGBITR7Y+": {
        "name_ru": "ОФЗ более 7 лет (полная доходность)",
        "name_en": "Government Bonds 7Y+ Total Return",
        "type": "government",
        "board": "SNDX",
        "description": "Долгосрочные ОФЗ — высокая чувствительность к ставке"
    },

    # Инфляционные ОФЗ (ОФЗ-ИН)
    "RUGBINFTR": {
        "name_ru": "ОФЗ с защитой от инфляции",
        "name_en": "Inflation-Linked Government Bonds TR",
        "type": "government",
        "board": "SNDX",
        "description": "Индекс ОФЗ-ИН (номинал индексируется на инфляцию)"
    },

    # ========== КОРПОРАТИВНЫЕ ОБЛИГАЦИИ ==========
    # Широкие индексы
    "RUCBITR": {
        "name_ru": "Индекс корпоративных облигаций",
        "name_en": "Corporate Bond Total Return Index",
        "type": "corporate",
        "board": "SNDX",
        "description": "Широкий индекс корпоративных облигаций (legacy)"
    },
    "RUCBTRNS": {
        "name_ru": "Корпоративные облигации (новая серия)",
        "name_en": "Corporate Bonds New Series TR",
        "type": "corporate",
        "board": "SNDX",
        "description": "Новая серия корпоративного индекса (с 2020)"
    },

    # Высокодоходные (ВДО)
    "RUCBHYTR": {
        "name_ru": "Высокодоходные облигации",
        "name_en": "High Yield Corporate Bonds TR",
        "type": "corporate",
        "board": "SNDX",
        "description": "Облигации с рейтингом ниже BBB (повышенный риск/доходность)"
    },

    # По кредитному рейтингу
    "RUCBTRAAANS": {
        "name_ru": "Корпоративные AAA",
        "name_en": "Corporate Bonds AAA TR",
        "type": "corporate",
        "board": "SNDX",
        "description": "Облигации эмитентов с наивысшим рейтингом"
    },
    "RUCBTRAANS": {
        "name_ru": "Корпоративные AA",
        "name_en": "Corporate Bonds AA TR",
        "type": "corporate",
        "board": "SNDX",
        "description": "Облигации эмитентов с рейтингом AA"
    },
    "RUCBTRANS": {
        "name_ru": "Корпоративные A",
        "name_en": "Corporate Bonds A TR",
        "type": "corporate",
        "board": "SNDX",
        "description": "Облигации эмитентов с рейтингом A"
    },
    "RUCBTRBBBNS": {
        "name_ru": "Корпоративные BBB",
        "name_en": "Corporate Bonds BBB TR",
        "type": "corporate",
        "board": "SNDX",
        "description": "Облигации инвестиционного уровня (нижняя граница)"
    },

    # ========== МУНИЦИПАЛЬНЫЕ ОБЛИГАЦИИ ==========
    "RUMBTRNS": {
        "name_ru": "Муниципальные облигации",
        "name_en": "Municipal Bonds TR",
        "type": "municipal",
        "board": "SNDX",
        "description": "Облигации регионов и муниципалитетов"
    },

    # ========== ИПОТЕЧНЫЕ ОБЛИГАЦИИ ==========
    "DOMMBSTR": {
        "name_ru": "Ипотечные облигации",
        "name_en": "Mortgage-Backed Securities TR",
        "type": "mortgage",
        "board": "SNDX",
        "description": "Облигации, обеспеченные пулом ипотечных кредитов"
    },

    # ========== ВАЛЮТНЫЕ ОБЛИГАЦИИ ==========
    "RUCNYTR": {
        "name_ru": "Облигации в юанях",
        "name_en": "CNY Bonds TR",
        "type": "fx",
        "board": "SNDX",
        "description": "Рублёвые облигации с привязкой к юаню"
    },
    "RUEUTR": {
        "name_ru": "Еврооблигации",
        "name_en": "Eurobonds TR",
        "type": "fx",
        "board": "SNDX",
        "description": "Российские еврооблигации"
    },

    # ========== АГРЕГИРОВАННЫЕ ИНДЕКСЫ ==========
    "RUABITR": {
        "name_ru": "Агрегированный индекс облигаций",
        "name_en": "Aggregate Bond Index TR",
        "type": "aggregate",
        "board": "SNDX",
        "description": "Широкий индекс всех типов облигаций"
    },

    # ========== ESG И ТЕМАТИЧЕСКИЕ ==========
    "RUESGTR": {
        "name_ru": "ESG облигации",
        "name_en": "ESG Bonds TR",
        "type": "thematic",
        "board": "SNDX",
        "description": "Облигации эмитентов с высоким ESG-рейтингом"
    },
    "RUGROWTR": {
        "name_ru": "Сектор роста",
        "name_en": "Growth Sector Bonds TR",
        "type": "thematic",
        "board": "SNDX",
        "description": "Облигации компаний сектора роста"
    },
}


# ============================================================================
# СПИСКИ ИНДЕКСОВ АКЦИЙ
# ============================================================================

EQUITY_INDICES: Dict[str, Dict] = {
    # ========== ШИРОКИЕ РЫНОЧНЫЕ ИНДЕКСЫ ==========
    "IMOEX": {
        "name_ru": "Индекс МосБиржи",
        "name_en": "MOEX Russia Index",
        "type": "broad_market",
        "board": "SNDX",
        "description": "Основной рублёвый индекс (~50 наиболее ликвидных акций)"
    },
    "RTSI": {
        "name_ru": "Индекс RTS",
        "name_en": "RTS Index",
        "type": "broad_market",
        "board": "RTSI",
        "description": "Долларовый эквивалент IMOEX"
    },
    "MOEX10": {
        "name_ru": "MOEX 10",
        "name_en": "MOEX 10 Index",
        "type": "broad_market",
        "board": "SNDX",
        "description": "Топ-10 наиболее ликвидных акций"
    },
    "MOEXBC": {
        "name_ru": "Голубые фишки",
        "name_en": "Blue Chip Index",
        "type": "broad_market",
        "board": "SNDX",
        "description": "15 крупнейших и наиболее ликвидных компаний"
    },
    "MOEXBMI": {
        "name_ru": "Широкий рынок",
        "name_en": "Broad Market Index",
        "type": "broad_market",
        "board": "SNDX",
        "description": "~100 акций — полное покрытие рынка"
    },
    "MCXSM": {
        "name_ru": "Малая и средняя капитализация",
        "name_en": "Small & Mid Cap Index",
        "type": "broad_market",
        "board": "SNDX",
        "description": "Акции компаний средней и малой капитализации"
    },

    # ========== СЕКТОРНЫЕ ИНДЕКСЫ ==========
    "MOEXOG": {
        "name_ru": "Нефть и газ",
        "name_en": "Oil & Gas Index",
        "type": "sector",
        "board": "SNDX",
        "description": "Газпром, Роснефть, Лукойл, Новатэк и др."
    },
    "MOEXFN": {
        "name_ru": "Финансы",
        "name_en": "Financials Index",
        "type": "sector",
        "board": "SNDX",
        "description": "Сбербанк, ВТБ, Тинькофф, Московская биржа"
    },
    "MOEXMM": {
        "name_ru": "Металлы и добыча",
        "name_en": "Metals & Mining Index",
        "type": "sector",
        "board": "SNDX",
        "description": "Норникель, Северсталь, НЛМК, Русал"
    },
    "MOEXEU": {
        "name_ru": "Электроэнергетика",
        "name_en": "Electric Utilities Index",
        "type": "sector",
        "board": "SNDX",
        "description": "Интер РАО, Русгидро, ФСК ЕЭС"
    },
    "MOEXTL": {
        "name_ru": "Телекоммуникации",
        "name_en": "Telecom Index",
        "type": "sector",
        "board": "SNDX",
        "description": "МТС, Ростелеком"
    },
    "MOEXTN": {
        "name_ru": "Транспорт",
        "name_en": "Transportation Index",
        "type": "sector",
        "board": "SNDX",
        "description": "Аэрофлот, НМТП, Globaltrans"
    },
    "MOEXCH": {
        "name_ru": "Химия и нефтехимия",
        "name_en": "Chemicals Index",
        "type": "sector",
        "board": "SNDX",
        "description": "ФосАгро, Акрон, Казаньоргсинтез"
    },
    "MOEXCN": {
        "name_ru": "Потребительский сектор",
        "name_en": "Consumer Index",
        "type": "sector",
        "board": "SNDX",
        "description": "Магнит, X5, Детский мир"
    },
    "MOEXRE": {
        "name_ru": "Недвижимость",
        "name_en": "Real Estate Index",
        "type": "sector",
        "board": "SNDX",
        "description": "ПИК, Самолёт, Эталон"
    },
    "MOEXIT": {
        "name_ru": "Информационные технологии",
        "name_en": "IT Index",
        "type": "sector",
        "board": "SNDX",
        "description": "Яндекс, VK, Positive Technologies, HeadHunter"
    },

    # ========== ESG И УСТОЙЧИВОЕ РАЗВИТИЕ ==========
    "MESG": {
        "name_ru": "MOEX-RAEX ESG",
        "name_en": "MOEX-RAEX ESG Index",
        "type": "esg",
        "board": "SNDX",
        "description": "Компании с высоким ESG-рейтингом"
    },
    "MRRT": {
        "name_ru": "Ответственность и открытость",
        "name_en": "Responsibility & Transparency Index",
        "type": "esg",
        "board": "SNDX",
        "description": "Индекс качества корпоративного управления"
    },
    "RUCGI": {
        "name_ru": "Корпоративное управление",
        "name_en": "Corporate Governance Index",
        "type": "esg",
        "board": "SNDX",
        "description": "Компании с лучшими практиками управления"
    },

    # ========== ИННОВАЦИОННЫЕ И СПЕЦИАЛЬНЫЕ ==========
    "MOEXINN": {
        "name_ru": "Инновации",
        "name_en": "Innovation Index",
        "type": "thematic",
        "board": "SNDX",
        "description": "Высокотехнологичные и инновационные компании"
    },
    "MIPO": {
        "name_ru": "IPO индекс",
        "name_en": "IPO Index",
        "type": "thematic",
        "board": "SNDX",
        "description": "Недавно размещённые компании"
    },
}


# ============================================================================
# ФУНКЦИИ ЗАГРУЗКИ ДАННЫХ
# ============================================================================

def download_index(
    index_code: str,
    output_dir: Union[str, Path],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    client: Optional[MOEXClient] = None
) -> Optional[pd.DataFrame]:
    """
    Скачивает данные одного индекса и сохраняет в CSV.

    Параметры:
    ----------
    index_code : str
        Код индекса (IMOEX, RGBITR, etc.)
    output_dir : str или Path
        Директория для сохранения файла
    start_date : str, optional
        Начальная дата ('YYYY-MM-DD'). По умолчанию: 2010-01-01
    end_date : str, optional
        Конечная дата. По умолчанию: сегодня
    client : MOEXClient, optional
        Клиент API. Если не указан, создаётся новый

    Возвращает:
    -----------
    pd.DataFrame или None
        Загруженные данные или None при ошибке
    """
    if client is None:
        client = MOEXClient()

    if start_date is None:
        start_date = "2010-01-01"

    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')

    # Определяем режим торгов
    board = "SNDX"
    if index_code in EQUITY_INDICES:
        board = EQUITY_INDICES[index_code].get("board", "SNDX")
    elif index_code in BOND_INDICES:
        board = BOND_INDICES[index_code].get("board", "SNDX")

    logger.info(f"Загрузка {index_code} за период {start_date} — {end_date}...")

    try:
        df = client.get_index_history(
            index_code,
            start_date=start_date,
            end_date=end_date,
            board=board
        )

        if df.empty:
            logger.warning(f"Нет данных для {index_code}")
            return None

        # Создаём директорию если нужно
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Формируем имя файла
        date_suffix = datetime.now().strftime('%Y%m%d')
        filename = f"{index_code}_{date_suffix}.csv"
        filepath = output_path / filename

        # Сохраняем
        if 'TRADEDATE' in df.columns:
            df['TRADEDATE'] = pd.to_datetime(df['TRADEDATE']).dt.strftime('%Y-%m-%d')

        df.to_csv(filepath, index=False, encoding='utf-8')
        logger.info(f"Сохранено {len(df)} записей в {filepath}")

        return df

    except Exception as e:
        logger.error(f"Ошибка при загрузке {index_code}: {e}")
        return None


def download_bond_indices(
    indices: Optional[List[str]] = None,
    output_dir: Union[str, Path] = "./data/bonds",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, bool]:
    """
    Скачивает данные по индексам облигаций.

    Параметры:
    ----------
    indices : list, optional
        Список кодов индексов. Если не указан, скачиваются все
    output_dir : str или Path
        Директория для сохранения
    start_date : str, optional
        Начальная дата ('YYYY-MM-DD')
    end_date : str, optional
        Конечная дата

    Возвращает:
    -----------
    dict
        Словарь {код_индекса: успешно_загружен}

    Примеры:
    --------
    >>> # Скачать все индексы облигаций
    >>> results = download_bond_indices()

    >>> # Скачать только ОФЗ
    >>> results = download_bond_indices(['RGBITR', 'RUGBITR1Y', 'RUGBITR7Y+'])
    """
    if indices is None:
        indices = list(BOND_INDICES.keys())

    client = MOEXClient()
    results = {}

    logger.info(f"Начинаем загрузку {len(indices)} индексов облигаций...")

    for index_code in indices:
        df = download_index(
            index_code,
            output_dir=output_dir,
            start_date=start_date,
            end_date=end_date,
            client=client
        )
        results[index_code] = df is not None

    # Статистика
    successful = sum(results.values())
    logger.info(f"Загрузка завершена: {successful}/{len(indices)} успешно")

    return results


def download_equity_indices(
    indices: Optional[List[str]] = None,
    output_dir: Union[str, Path] = "./data/equity",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, bool]:
    """
    Скачивает данные по индексам акций.

    Параметры:
    ----------
    indices : list, optional
        Список кодов индексов. Если не указан, скачиваются все
    output_dir : str или Path
        Директория для сохранения
    start_date : str, optional
        Начальная дата ('YYYY-MM-DD')
    end_date : str, optional
        Конечная дата

    Возвращает:
    -----------
    dict
        Словарь {код_индекса: успешно_загружен}

    Примеры:
    --------
    >>> # Скачать все секторные индексы
    >>> sectors = ['MOEXOG', 'MOEXFN', 'MOEXMM', 'MOEXIT']
    >>> results = download_equity_indices(sectors)

    >>> # Скачать все индексы акций
    >>> results = download_equity_indices()
    """
    if indices is None:
        indices = list(EQUITY_INDICES.keys())

    client = MOEXClient()
    results = {}

    logger.info(f"Начинаем загрузку {len(indices)} индексов акций...")

    for index_code in indices:
        df = download_index(
            index_code,
            output_dir=output_dir,
            start_date=start_date,
            end_date=end_date,
            client=client
        )
        results[index_code] = df is not None

    # Статистика
    successful = sum(results.values())
    logger.info(f"Загрузка завершена: {successful}/{len(indices)} успешно")

    return results


def list_indices(index_type: str = "all") -> pd.DataFrame:
    """
    Возвращает таблицу доступных индексов с описаниями.

    Параметры:
    ----------
    index_type : str
        Тип индексов: 'bonds', 'equity', 'all'

    Возвращает:
    -----------
    pd.DataFrame
        Таблица с колонками: code, name_ru, type, description
    """
    data = []

    if index_type in ("all", "bonds"):
        for code, info in BOND_INDICES.items():
            data.append({
                "code": code,
                "name_ru": info["name_ru"],
                "category": "облигации",
                "type": info["type"],
                "description": info["description"]
            })

    if index_type in ("all", "equity"):
        for code, info in EQUITY_INDICES.items():
            data.append({
                "code": code,
                "name_ru": info["name_ru"],
                "category": "акции",
                "type": info["type"],
                "description": info["description"]
            })

    return pd.DataFrame(data)


# ============================================================================
# Точка входа для тестирования
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Доступные индексы MOEX")
    print("=" * 60)

    # Показываем индексы облигаций
    print("\nИндексы облигаций:")
    print("-" * 40)
    for code, info in list(BOND_INDICES.items())[:5]:
        print(f"  {code:15} — {info['name_ru']}")
    print(f"  ... и ещё {len(BOND_INDICES) - 5} индексов")

    # Показываем индексы акций
    print("\nИндексы акций:")
    print("-" * 40)
    for code, info in list(EQUITY_INDICES.items())[:5]:
        print(f"  {code:15} — {info['name_ru']}")
    print(f"  ... и ещё {len(EQUITY_INDICES) - 5} индексов")

    # Пример загрузки
    print("\n" + "=" * 60)
    print("Пример: загрузка данных IMOEX")
    print("=" * 60)

    df = download_index('IMOEX', output_dir='./demo_data', start_date='2024-01-01')
    if df is not None:
        print(f"\nЗагружено {len(df)} записей:")
        print(df[['TRADEDATE', 'OPEN', 'CLOSE']].tail())
