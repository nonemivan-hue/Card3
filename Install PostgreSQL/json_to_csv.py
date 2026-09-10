#!/usr/bin/env python3
"""
json_to_csv.py - Утилита для преобразования JSON файлов в CSV формат для импорта в PostgreSQL

Использование:
    python json_to_csv.py <input_json_file> <output_csv_file>
    
Пример:
    python json_to_csv.py data/cards.json output/cards.csv
"""

import json
import csv
import sys
import os
from datetime import datetime


def convert_value(value):
    """Преобразует значение в строковый формат, подходящий для CSV"""
    if value is None:
        return ''
    elif isinstance(value, bool):
        return str(value).lower()
    elif isinstance(value, (list, dict)):
        # Сложные типы данных сериализуем в JSON
        return json.dumps(value, ensure_ascii=False)
    elif isinstance(value, str):
        # Проверяем, не является ли строка датой/временем
        if len(value) == 19 and value[4] == '-' and value[7] == '-':
            try:
                # Попытка распознать дату
                datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
                return value.replace('T', ' ')
            except ValueError:
                pass
        return value
    else:
        return str(value)


def json_to_csv(json_file, csv_file):
    """
    Преобразует JSON файл в CSV формат
    
    Args:
        json_file: Путь к входному JSON файлу
        csv_file: Путь к выходному CSV файлу
        
    Returns:
        bool: True если успешно, False иначе
    """
    print(f"Обработка файла: {json_file}")
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Ошибка чтения JSON: {e}")
        return False
    except FileNotFoundError:
        print(f"Файл не найден: {json_file}")
        return False
    
    if not data:
        print(f"Файл {json_file} пустой")
        return False
    
    # Если данные в виде словаря {...}, преобразуем в список
    if isinstance(data, dict):
        data = [data]
    
    if not isinstance(data, list):
        print(f"Неподдерживаемый формат данных в {json_file}. Ожидается список объектов.")
        return False
    
    # Получаем заголовки из всех элементов (объединяем ключи)
    all_keys = set()
    for item in data:
        if isinstance(item, dict):
            all_keys.update(item.keys())
    
    # Сортируем ключи для консистентности
    fieldnames = sorted(list(all_keys))
    
    if not fieldnames:
        print(f"Нет данных для экспорта в {json_file}")
        return False
    
    print(f"Найдено полей: {len(fieldnames)}")
    print(f"Найдено записей: {len(data)}")
    
    try:
        with open(csv_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            
            for row in data:
                if not isinstance(row, dict):
                    continue
                    
                # Преобразуем все значения в строковый формат
                csv_row = {}
                for key in fieldnames:
                    csv_row[key] = convert_value(row.get(key))
                
                writer.writerow(csv_row)
        
        print(f"Успешно: {json_file} -> {csv_file}")
        return True
        
    except Exception as e:
        print(f"Ошибка записи CSV: {e}")
        return False


def process_directory(data_dir, output_dir=None):
    """
    Обрабатывает все JSON файлы в директории
    
    Args:
        data_dir: Путь к папке с JSON файлами
        output_dir: Путь к папке для CSV файлов (по умолчанию создается подпапка 'csv')
    """
    if output_dir is None:
        output_dir = os.path.join(data_dir, 'csv')
    
    os.makedirs(output_dir, exist_ok=True)
    
    json_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
    
    if not json_files:
        print(f"В папке {data_dir} не найдено JSON файлов")
        return 0, 0
    
    success_count = 0
    failed_count = 0
    
    print(f"Найдено JSON файлов: {len(json_files)}")
    print("=" * 60)
    
    for json_file in sorted(json_files):
        json_path = os.path.join(data_dir, json_file)
        csv_filename = os.path.splitext(json_file)[0] + '.csv'
        csv_path = os.path.join(output_dir, csv_filename)
        
        if json_to_csv(json_path, csv_path):
            success_count += 1
        else:
            failed_count += 1
        
        print("-" * 60)
    
    return success_count, failed_count


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nРежимы работы:")
        print("  1. Одиночный файл:")
        print("     python json_to_csv.py <input.json> <output.csv>")
        print("\n  2. Обработка папки:")
        print("     python json_to_csv.py --dir <path_to_data_folder> [--output <output_folder>]")
        sys.exit(1)
    
    if sys.argv[1] == '--dir':
        if len(sys.argv) < 3:
            print("Ошибка: укажите путь к папке с данными")
            sys.exit(1)
        
        data_dir = sys.argv[2]
        output_dir = None
        
        if len(sys.argv) >= 5 and sys.argv[3] == '--output':
            output_dir = sys.argv[4]
        
        success, failed = process_directory(data_dir, output_dir)
        
        print("\n" + "=" * 60)
        print(f"Итого: обработано успешно - {success}, с ошибками - {failed}")
        
        sys.exit(0 if failed == 0 else 1)
    else:
        if len(sys.argv) != 3:
            print("Ошибка: укажите входной и выходной файлы")
            print(__doc__)
            sys.exit(1)
        
        json_file = sys.argv[1]
        csv_file = sys.argv[2]
        
        if json_to_csv(json_file, csv_file):
            sys.exit(0)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
