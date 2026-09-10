@echo off
REM migrate_from_json.bat - Скрипт миграции данных из JSON файлов в PostgreSQL
REM Использование: migrate_from_json.bat [путь_к_папке_data] [имя_БД] [пользователь]

SETLOCAL EnableDelayedExpansion

REM ============================================
REM НАСТРОЙКИ (измените под вашу систему)
REM ============================================
set PG_BIN=C:\Program Files\PostgreSQL\16\bin
set PG_USER=postgres
set PG_PASSWORD=your_postgres_password
set DB_NAME=card_system
set DATA_DIR=C:\path\to\your\project\data

REM Переопределение параметров из командной строки (если переданы)
if not "%~1"=="" set DATA_DIR=%~1
if not "%~2"=="" set DB_NAME=%~2
if not "%~3"=="" set PG_USER=%~3

REM Установка переменной окружения для пароля
set PGPASSWORD=%PG_PASSWORD%

echo ====================================================
echo Миграция данных из JSON в PostgreSQL
echo ====================================================
echo Параметры:
echo   - База данных: %DB_NAME%
echo   - Пользователь: %PG_USER%
echo   - Папка с данными: %DATA_DIR%
echo ====================================================
echo.

REM Проверка существования папки с данными
if not exist "%DATA_DIR%" (
    echo ОШИБКА: Папка с данными не найдена: %DATA_DIR%
    exit /b 1
)

REM Проверка существования утилит PostgreSQL
if not exist "%PG_BIN%\psql.exe" (
    echo ОШИБКА: psql.exe не найден. Проверьте путь к PostgreSQL: %PG_BIN%
    exit /b 1
)

if not exist "%PG_BIN%\pg_restore.exe" (
    echo ОШИБКА: pg_restore.exe не найден. Проверьте путь к PostgreSQL: %PG_BIN%
    exit /b 1
)

REM Создание временной папки для CSV файлов
set TEMP_CSV_DIR=%TEMP%\pg_migration_%RANDOM%
mkdir "%TEMP_CSV_DIR%"

echo Шаг 1: Преобразование JSON файлов в CSV...
echo.

REM ============================================
REM Функция преобразования JSON в CSV (Python)
REM ============================================
if not exist "json_to_csv.py" (
    echo Создание скрипта json_to_csv.py...
    (
        echo import json
        echo import csv
        echo import sys
        echo import os
        echo.
        echo def json_to_csv(json_file, csv_file):
        echo     with open^(json_file, 'r', encoding='utf-8'^) as f:
        echo         data = json.load^(f^)
        echo.
        echo     if not data:
        echo         print^(f"Файл {json_file} пустой"^)
        echo         return False
        echo.
        echo     # Если данные в виде словаря ^{...^}, преобразуем в список
        echo     if isinstance^(data, dict^):
        echo         data = [data]
        echo.
        echo     if not isinstance^(data, list^):
        echo         print^f"Неподдерживаемый формат данных в {json_file}"^)
        echo         return False
        echo.
        echo     # Получаем заголовки из первого элемента
        echo     fieldnames = list^(data[0].keys^(^^)
        echo.
        echo     with open^(csv_file, 'w', encoding='utf-8', newline=''^) as f:
        echo         writer = csv.DictWriter^(f, fieldnames=fieldnames^)
        echo         writer.writeheader^(^)
        echo         for row in data:
        echo             # Преобразуем сложные типы данных в строки
        echo             for key in fieldnames:
        echo                 if isinstance^(row.get^(key^), ^(list, dict^)^):
        echo                     row[key] = json.dumps^(row[key], ensure_ascii=False^)
        echo                 elif row.get^(key^) is None:
        echo                     row[key] = ''
        echo             writer.writerow^(row^)
        echo.
        echo     return True
        echo.
        echo if __name__ == "__main__":
        echo     if len^(sys.argv^) != 3:
        echo         print^("Использование: python json_to_csv.py ^<json_file^> ^<csv_file^>"^)
        echo         sys.exit^(1^)
        echo.
        echo     json_file = sys.argv[1]
        echo     csv_file = sys.argv[2]
        echo.
        echo     if json_to_csv^(json_file, csv_file^):
        echo         print^f"Успешно: {json_file} -^> {csv_file}"^)
        echo         sys.exit^(0^)
        echo     else:
        echo         sys.exit^(1^)
    ) > "json_to_csv.py"
)

REM Обработка каждого JSON файла
set FILES_PROCESSED=0
set FILES_FAILED=0

for %%F in ("%DATA_DIR%\*.json") do (
    set JSON_FILE=%%F
    set FILENAME=%%~nF
    set CSV_FILE=%TEMP_CSV_DIR%\!FILENAME!.csv
    
    echo Обработка: !FILENAME!.json
    python json_to_csv.py "!JSON_FILE!" "!CSV_FILE!"
    
    if !ERRORLEVEL! EQU 0 (
        set /a FILES_PROCESSED+=1
    ) else (
        set /a FILES_FAILED+=1
        echo ОШИБКА при обработке !FILENAME!.json
    )
)

echo.
echo Преобразование завершено: %FILES_PROCESSED% файлов успешно, %FILES_FAILED% с ошибками
echo.

REM ============================================
REM Шаг 2: Загрузка данных в PostgreSQL
REM ============================================
echo Шаг 2: Загрузка данных в PostgreSQL...
echo.

REM Функция загрузки CSV в таблицу
:LOAD_TABLE
set TABLE_NAME=%1
set CSV_FILE=%2

if exist "%CSV_FILE%" (
    echo Загрузка таблицы %TABLE_NAME%...
    
    REM Получаем заголовки из первой строки CSV
    set /p HEADERS=<"%CSV_FILE%"
    
    REM Создаем временную таблицу и загружаем данные
    "%PG_BIN%\psql.exe" -U %PG_USER% -d %DB_NAME% -c "DROP TABLE IF EXISTS temp_%TABLE_NAME% CASCADE;"
    "%PG_BIN%\psql.exe" -U %PG_USER% -d %DB_NAME% -c "CREATE TABLE temp_%TABLE_NAME% AS SELECT * FROM %TABLE_NAME% WITH NO DATA;"
    
    REM Используем COPY для загрузки данных
    "%PG_BIN%\psql.exe" -U %PG_USER% -d %DB_NAME% -c "\copy temp_%TABLE_NAME% FROM '%CSV_FILE%' WITH CSV HEADER ENCODING 'UTF8';"
    
    if !ERRORLEVEL! EQU 0 (
        echo Успешно загружено в temp_%TABLE_NAME%
        REM Здесь можно добавить логику объединения с основной таблицей
    ) else (
        echo ОШИБКА загрузки %TABLE_NAME%
    )
) else (
    echo Файл %CSV_FILE% не найден, пропускаем %TABLE_NAME%
)
goto :EOF

REM Загрузка основных таблиц (порядок важен из-за внешних ключей)
call :LOAD_TABLE "constants" "%TEMP_CSV_DIR%\constants.csv"
call :LOAD_TABLE "counters" "%TEMP_CSV_DIR%\counters.csv"
call :LOAD_TABLE "employees" "%TEMP_CSV_DIR%\employees.csv"
call :LOAD_TABLE "organizations" "%TEMP_CSV_DIR%\organizations.csv"
call :LOAD_TABLE "mfcs" "%TEMP_CSV_DIR%\mfcs.csv"
call :LOAD_TABLE "card_types" "%TEMP_CSV_DIR%\card_types.csv"
call :LOAD_TABLE "owners" "%TEMP_CSV_DIR%\owners.csv"
call :LOAD_TABLE "applicants" "%TEMP_CSV_DIR%\applicants.csv"
call :LOAD_TABLE "cards" "%TEMP_CSV_DIR%\cards.csv"
call :LOAD_TABLE "documents" "%TEMP_CSV_DIR%\documents.csv"
call :LOAD_TABLE "action_log" "%TEMP_CSV_DIR%\action_log.csv"

echo.
echo ====================================================
echo Миграция завершена!
echo ====================================================
echo.
echo Важно: После миграции проверьте данные в базе:
echo   "%PG_BIN%\psql.exe" -U %PG_USER% -d %DB_NAME% -c "SELECT COUNT(*) FROM cards;"
echo.

REM Очистка временных файлов
echo Очистка временных файлов...
rmdir /s /q "%TEMP_CSV_DIR%"
del /q "json_to_csv.py"

echo Готово!
pause
