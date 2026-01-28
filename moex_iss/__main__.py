#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Точка входа для запуска пакета как модуля.

Позволяет использовать:
    python -m moex_iss [команда]

Вместо:
    python -m moex_iss.cli [команда]
"""

from .cli import main

if __name__ == "__main__":
    main()
