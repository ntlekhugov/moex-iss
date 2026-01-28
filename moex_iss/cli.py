#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MOEX ISS CLI — Командный интерфейс для загрузки данных
======================================================

Позволяет скачивать данные с Московской Биржи из командной строки.

Использование:
-------------
    # Показать справку
    python -m moex_iss --help

    # Скачать данные по индексу IMOEX
    python -m moex_iss download IMOEX

    # Скачать несколько индексов за период
    python -m moex_iss download IMOEX MOEXOG RGBITR --start 2024-01-01

    # Скачать все индексы облигаций
    python -m moex_iss download-bonds

    # Скачать все индексы акций
    python -m moex_iss download-equity

    # Показать список доступных индексов
    python -m moex_iss list

    # Исследовать структуру API
    python -m moex_iss explore
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

from .client import MOEXClient
from .indices import (
    BOND_INDICES,
    EQUITY_INDICES,
    download_bond_indices,
    download_equity_indices,
    download_index,
    list_indices,
)


def cmd_download(args):
    """
    Команда: скачать данные по указанным индексам.

    Примеры:
        moex-iss download IMOEX MOEXOG --start 2024-01-01 --output ./data
    """
    print("=" * 60)
    print("MOEX ISS — Загрузка данных")
    print("=" * 60)

    indices = args.indices
    start_date = args.start
    end_date = args.end
    output_dir = Path(args.output)

    print(f"\nИндексы: {', '.join(indices)}")
    print(f"Период: {start_date or '2010-01-01'} — {end_date or 'сегодня'}")
    print(f"Директория: {output_dir.absolute()}")
    print("-" * 60)

    client = MOEXClient()
    success_count = 0

    for index_code in indices:
        df = download_index(
            index_code,
            output_dir=output_dir,
            start_date=start_date,
            end_date=end_date,
            client=client
        )
        if df is not None:
            success_count += 1
            print(f"✓ {index_code}: загружено {len(df)} записей")
        else:
            print(f"✗ {index_code}: ошибка загрузки")

    print("-" * 60)
    print(f"Итого: {success_count}/{len(indices)} индексов загружено успешно")

    return 0 if success_count == len(indices) else 1


def cmd_download_bonds(args):
    """
    Команда: скачать все индексы облигаций.
    """
    print("=" * 60)
    print("MOEX ISS — Загрузка индексов облигаций")
    print("=" * 60)

    print(f"\nВсего индексов: {len(BOND_INDICES)}")
    print(f"Директория: {args.output}")
    print("-" * 60)

    results = download_bond_indices(
        output_dir=args.output,
        start_date=args.start,
        end_date=args.end
    )

    success_count = sum(results.values())
    print("-" * 60)
    print(f"Итого: {success_count}/{len(results)} индексов загружено успешно")

    return 0 if success_count == len(results) else 1


def cmd_download_equity(args):
    """
    Команда: скачать все индексы акций.
    """
    print("=" * 60)
    print("MOEX ISS — Загрузка индексов акций")
    print("=" * 60)

    print(f"\nВсего индексов: {len(EQUITY_INDICES)}")
    print(f"Директория: {args.output}")
    print("-" * 60)

    results = download_equity_indices(
        output_dir=args.output,
        start_date=args.start,
        end_date=args.end
    )

    success_count = sum(results.values())
    print("-" * 60)
    print(f"Итого: {success_count}/{len(results)} индексов загружено успешно")

    return 0 if success_count == len(results) else 1


def cmd_list(args):
    """
    Команда: показать список доступных индексов.
    """
    print("=" * 60)
    print("MOEX ISS — Доступные индексы")
    print("=" * 60)

    index_type = args.type

    if index_type in ("all", "bonds"):
        print("\n📊 ИНДЕКСЫ ОБЛИГАЦИЙ")
        print("-" * 60)
        for code, info in BOND_INDICES.items():
            print(f"  {code:15} │ {info['name_ru']}")
            if args.verbose:
                print(f"  {' ':15} │   {info['description']}")
        print(f"\n  Всего: {len(BOND_INDICES)} индексов облигаций")

    if index_type in ("all", "equity"):
        print("\n📈 ИНДЕКСЫ АКЦИЙ")
        print("-" * 60)
        for code, info in EQUITY_INDICES.items():
            print(f"  {code:15} │ {info['name_ru']}")
            if args.verbose:
                print(f"  {' ':15} │   {info['description']}")
        print(f"\n  Всего: {len(EQUITY_INDICES)} индексов акций")

    return 0


def cmd_explore(args):
    """
    Команда: исследовать структуру MOEX ISS API.
    """
    print("=" * 60)
    print("MOEX ISS — Структура API")
    print("=" * 60)

    client = MOEXClient()

    # Движки
    print("\n🔧 ДВИЖКИ (engines)")
    print("-" * 40)
    engines = client.get_engines()
    for _, row in engines.iterrows():
        print(f"  {row['name']:15} │ {row.get('title', '')}")

    # Рынки
    print("\n📦 РЫНКИ фондового движка (stock)")
    print("-" * 40)
    markets = client.get_markets('stock')
    for _, row in markets.iterrows():
        market_name = row.get('market_name', row.get('NAME', ''))
        title = row.get('title', row.get('TITLE', ''))
        print(f"  {market_name:15} │ {title}")

    # Примеры индексов
    print("\n📊 ПРИМЕРЫ ИНДЕКСОВ (первые 10)")
    print("-" * 40)
    indices = client.get_available_indices()
    for _, row in indices.head(10).iterrows():
        print(f"  {row['SECID']:15} │ {row.get('SHORTNAME', '')}")

    print("\n💡 Подсказка: используйте 'list' для полного списка индексов")

    return 0


def cmd_info(args):
    """
    Команда: показать информацию об индексе.
    """
    index_code = args.index.upper()

    print("=" * 60)
    print(f"MOEX ISS — Информация об индексе {index_code}")
    print("=" * 60)

    # Ищем в словарях
    info = None
    category = None

    if index_code in BOND_INDICES:
        info = BOND_INDICES[index_code]
        category = "облигации"
    elif index_code in EQUITY_INDICES:
        info = EQUITY_INDICES[index_code]
        category = "акции"

    if info:
        print(f"\n  Код:         {index_code}")
        print(f"  Название:    {info['name_ru']}")
        print(f"  Категория:   {category}")
        print(f"  Тип:         {info['type']}")
        print(f"  Режим:       {info['board']}")
        print(f"  Описание:    {info['description']}")
    else:
        print(f"\n  Индекс {index_code} не найден в справочнике.")
        print("  Попробуйте команду 'list' для просмотра доступных индексов.")

    # Пробуем получить актуальные данные
    print("\n  Последние данные с биржи:")
    print("  " + "-" * 40)

    client = MOEXClient()
    df = client.get_index_history(index_code)

    if not df.empty:
        last_row = df.iloc[-1]
        print(f"  Дата:        {last_row.get('TRADEDATE', 'N/A')}")
        print(f"  Открытие:    {last_row.get('OPEN', 'N/A')}")
        print(f"  Закрытие:    {last_row.get('CLOSE', 'N/A')}")
        print(f"  Максимум:    {last_row.get('HIGH', 'N/A')}")
        print(f"  Минимум:     {last_row.get('LOW', 'N/A')}")
    else:
        print("  Данные недоступны")

    return 0


def main():
    """
    Главная функция CLI.
    """
    parser = argparse.ArgumentParser(
        prog="moex-iss",
        description="Командный интерфейс для загрузки данных с Московской Биржи",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  moex-iss download IMOEX                    Скачать индекс IMOEX
  moex-iss download IMOEX RGBITR -s 2024-01-01  Скачать два индекса с даты
  moex-iss download-bonds                    Скачать все индексы облигаций
  moex-iss download-equity                   Скачать все индексы акций
  moex-iss list                              Показать все доступные индексы
  moex-iss list -t bonds                     Показать только облигации
  moex-iss info IMOEX                        Информация об индексе
  moex-iss explore                           Исследовать структуру API

Документация: https://iss.moex.com/iss/reference/
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Доступные команды")

    # ---- download ----
    download_parser = subparsers.add_parser(
        "download",
        help="Скачать данные по указанным индексам"
    )
    download_parser.add_argument(
        "indices",
        nargs="+",
        help="Коды индексов (например: IMOEX MOEXOG RGBITR)"
    )
    download_parser.add_argument(
        "-s", "--start",
        help="Начальная дата (YYYY-MM-DD)"
    )
    download_parser.add_argument(
        "-e", "--end",
        help="Конечная дата (YYYY-MM-DD)"
    )
    download_parser.add_argument(
        "-o", "--output",
        default="./data",
        help="Директория для сохранения (по умолчанию: ./data)"
    )
    download_parser.set_defaults(func=cmd_download)

    # ---- download-bonds ----
    bonds_parser = subparsers.add_parser(
        "download-bonds",
        help="Скачать все индексы облигаций"
    )
    bonds_parser.add_argument(
        "-s", "--start",
        help="Начальная дата (YYYY-MM-DD)"
    )
    bonds_parser.add_argument(
        "-e", "--end",
        help="Конечная дата (YYYY-MM-DD)"
    )
    bonds_parser.add_argument(
        "-o", "--output",
        default="./data/bonds",
        help="Директория для сохранения"
    )
    bonds_parser.set_defaults(func=cmd_download_bonds)

    # ---- download-equity ----
    equity_parser = subparsers.add_parser(
        "download-equity",
        help="Скачать все индексы акций"
    )
    equity_parser.add_argument(
        "-s", "--start",
        help="Начальная дата (YYYY-MM-DD)"
    )
    equity_parser.add_argument(
        "-e", "--end",
        help="Конечная дата (YYYY-MM-DD)"
    )
    equity_parser.add_argument(
        "-o", "--output",
        default="./data/equity",
        help="Директория для сохранения"
    )
    equity_parser.set_defaults(func=cmd_download_equity)

    # ---- list ----
    list_parser = subparsers.add_parser(
        "list",
        help="Показать список доступных индексов"
    )
    list_parser.add_argument(
        "-t", "--type",
        choices=["all", "bonds", "equity"],
        default="all",
        help="Тип индексов (по умолчанию: all)"
    )
    list_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Показать описания"
    )
    list_parser.set_defaults(func=cmd_list)

    # ---- info ----
    info_parser = subparsers.add_parser(
        "info",
        help="Показать информацию об индексе"
    )
    info_parser.add_argument(
        "index",
        help="Код индекса (например: IMOEX)"
    )
    info_parser.set_defaults(func=cmd_info)

    # ---- explore ----
    explore_parser = subparsers.add_parser(
        "explore",
        help="Исследовать структуру MOEX ISS API"
    )
    explore_parser.set_defaults(func=cmd_explore)

    # Парсим аргументы
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    # Выполняем команду
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
