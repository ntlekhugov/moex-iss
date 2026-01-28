# -*- coding: utf-8 -*-
"""
MOEX ISS API — Пакет для работы с данными Московской Биржи
==========================================================

Этот пакет предоставляет простой интерфейс для загрузки данных
с информационно-статистического сервера (ISS) Московской Биржи.

Основные возможности:
- Загрузка исторических данных по индексам акций и облигаций
- Получение информации о доступных инструментах
- Инкрементальное обновление данных
- Экспорт в CSV формат

Быстрый старт:
-------------
    from moex_iss import MOEXClient

    client = MOEXClient()

    # Скачать данные по индексу IMOEX
    df = client.get_index_history('IMOEX', start_date='2024-01-01')
    print(df.head())

Автор: Создано на основе проекта russia_macro_analysis
Документация MOEX ISS: https://iss.moex.com/iss/reference/
"""

__version__ = "1.0.0"
__author__ = "Russia Macro Analysis Team"

from .client import MOEXClient
from .indices import (
    download_bond_indices,
    download_equity_indices,
    BOND_INDICES,
    EQUITY_INDICES,
)

__all__ = [
    "MOEXClient",
    "download_bond_indices",
    "download_equity_indices",
    "BOND_INDICES",
    "EQUITY_INDICES",
]
