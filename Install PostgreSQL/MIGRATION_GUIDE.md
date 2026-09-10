# Инструкция по загрузке данных из локальной папки Data в PostgreSQL

Данное руководство описывает процесс переноса данных из JSON-файлов локальной папки `Data` в базу данных PostgreSQL.

## Содержание

1. [Подготовка](#подготовка)
2. [Способ 1: Автоматическая миграция через скрипт](#способ-1-автоматическая-миграция-через-скрипт)
3. [Способ 2: Ручная загрузка через Python утилиту](#способ-2-ручная-загрузка-через-python-утилиту)
4. [Способ 3: Пошаговая загрузка через psql](#способ-3-пошаговая-загрузка-через-psql)
5. [Проверка результатов](#проверка-результатов)
6. [Устранение неполадок](#устранение-неполадок)

---

## Подготовка

### Требования

- Установленный PostgreSQL (версия 14 или выше)
- Python 3.8+ с установленными модулями `json` и `csv` (входят в стандартную библиотеку)
- Папка `Data` с JSON-файлами экспортированных данных
- Созданная база данных PostgreSQL с инициализированной схемой

### Шаг 1: Проверка структуры папки Data

Убедитесь, что папка `Data` содержит следующие JSON-файлы:

```
Data/
├── card_types.json      # Типы карт
├── owners.json          # Владельцы карт
├── applicants.json      # Заявители
├── organizations.json   # Организации
├── mfcs.json            # МФЦ
├── employees.json       # Сотрудники
├── cards.json           # Карты
├── documents.json       # Документы
├── action_log.json      # Журнал действий
├── constants.json       # Константы системы
└── counters.json        # Счетчики
```

### Шаг 2: Инициализация схемы БД

Перед загрузкой данных необходимо создать структуру таблиц:

```cmd
"C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d card_system -f "path\to\postgres\init.sql"
```

### Шаг 3: Настройка переменных окружения

Для удобства установите переменные окружения:

```cmd
setx PG_BIN "C:\Program Files\PostgreSQL\16\bin"
setx PG_USER "postgres"
setx PG_PASSWORD "your_password"
setx DB_NAME "card_system"
setx DATA_DIR "C:\path\to\your\project\data"
```

**Важно:** После установки переменных перезапустите командную строку.

---

## Способ 1: Автоматическая миграция через скрипт

### Использование готового BAT-скрипта

В папке `Install PostgreSQL` находится скрипт `migrate_from_json.bat`, который автоматизирует весь процесс миграции.

#### Быстрый старт

1. Откройте командную строку от имени администратора
2. Перейдите в папку со скриптом:
   ```cmd
   cd "C:\path\to\Install PostgreSQL"
   ```

3. Запустите скрипт с параметрами:
   ```cmd
   migrate_from_json.bat "C:\path\to\data" card_system postgres
   ```
   
   Или используйте значения по умолчанию (отредактируйте скрипт перед запуском):
   ```cmd
   migrate_from_json.bat
   ```

#### Параметры скрипта

| Параметр | Описание | Пример |
|----------|----------|--------|
| 1 | Путь к папке с JSON файлами | `C:\project\data` |
| 2 | Имя базы данных | `card_system` |
| 3 | Пользователь PostgreSQL | `postgres` |

#### Что делает скрипт

1. Преобразует все JSON файлы в CSV формат
2. Создает временные таблицы в PostgreSQL
3. Загружает данные из CSV во временные таблицы
4. Очищает временные файлы

#### Логирование

Скрипт выводит подробный лог в консоль. Для сохранения в файл:

```cmd
migrate_from_json.bat "C:\path\to\data" card_system postgres > migration_log.txt 2>&1
```

---

## Способ 2: Ручная загрузка через Python утилиту

### Шаг 1: Преобразование JSON в CSV

Используйте утилиту `json_to_csv.py` из папки `Install PostgreSQL`:

#### Обработка одного файла

```cmd
python "Install PostgreSQL\json_to_csv.py" data/cards.csv output/cards.csv
```

#### Обработка всей папки

```cmd
python "Install PostgreSQL\json_to_csv.py" --dir data --output csv_output
```

#### Параметры утилиты

```
Режимы работы:
  1. Одиночный файл:
     python json_to_csv.py <input.json> <output.csv>

  2. Обработка папки:
     python json_to_csv.py --dir <path_to_data_folder> [--output <output_folder>]
```

### Шаг 2: Загрузка CSV в PostgreSQL

#### Вариант A: Через psql \copy

```cmd
"C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d card_system -c "\copy card_types FROM 'csv_output/card_types.csv' WITH CSV HEADER ENCODING 'UTF8';"
```

#### Вариант B: Через SQL команду COPY

Создайте SQL скрипт `load_data.sql`:

```sql
-- Загрузка справочников
\COPY card_types(id, name, print_name, created_at, updated_at) 
FROM 'csv_output/card_types.csv' WITH CSV HEADER ENCODING 'UTF8';

\COPY owners(id, full_name, created_at, updated_at) 
FROM 'csv_output/owners.csv' WITH CSV HEADER ENCODING 'UTF8';

\COPY applicants(id, full_name, created_at, updated_at) 
FROM 'csv_output/applicants.csv' WITH CSV HEADER ENCODING 'UTF8';

-- Загрузка основных таблиц
\COPY cards(id, card_number, card_type_id, status, owner_id, applicant_id, created_at, updated_at) 
FROM 'csv_output/cards.csv' WITH CSV HEADER ENCODING 'UTF8';

\COPY documents(id, doc_type, doc_number, doc_date, organization_id, mfc_id, employee_id, lines, status, created_by, created_at, updated_at, posted_at, posted_by) 
FROM 'csv_output/documents.csv' WITH CSV HEADER ENCODING 'UTF8';
```

Выполните скрипт:

```cmd
"C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d card_system -f load_data.sql
```

---

## Способ 3: Пошаговая загрузка через psql

### Порядок загрузки таблиц

**Важно:** Соблюдайте порядок загрузки из-за внешних ключей!

1. **Справочники (без внешних ключей):**
   - `constants`
   - `counters`
   - `employees`
   - `organizations`
   - `mfcs`
   - `card_types`
   - `owners`
   - `applicants`

2. **Основные таблицы (с внешними ключами):**
   - `cards`
   - `documents`
   - `action_log`

### Пошаговая инструкция

#### Шаг 1: Подключение к базе данных

```cmd
"C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d card_system
```

#### Шаг 2: Отключение внешних ключей (опционально)

Если возникают ошибки из-за порядка загрузки, временно отключите проверку внешних ключей:

```sql
ALTER TABLE cards DISABLE TRIGGER ALL;
ALTER TABLE documents DISABLE TRIGGER ALL;
ALTER TABLE action_log DISABLE TRIGGER ALL;
```

#### Шаг 3: Загрузка каждой таблицы

Для каждой таблицы выполните:

```sql
-- Пример для card_types
\COPY card_types(id, name, print_name, created_at, updated_at) 
FROM 'C:/path/to/csv/card_types.csv' WITH CSV HEADER ENCODING 'UTF8';

-- Пример для cards
\COPY cards(id, card_number, card_type_id, status, owner_id, applicant_id, created_at, updated_at) 
FROM 'C:/path/to/csv/cards.csv' WITH CSV HEADER ENCODING 'UTF8';
```

**Важно:** Используйте прямые слеши `/` в путях даже в Windows!

#### Шаг 4: Включение внешних ключей

```sql
ALTER TABLE cards ENABLE TRIGGER ALL;
ALTER TABLE documents ENABLE TRIGGER ALL;
ALTER TABLE action_log ENABLE TRIGGER ALL;
```

#### Шаг 5: Обновление последовательностей

После загрузки данных обновите счетчики:

```sql
-- Для таблиц с SERIAL полями
SELECT setval('action_log_id_seq', (SELECT MAX(id) FROM action_log));
```

---

## Проверка результатов

### Быстрая проверка количества записей

```cmd
"C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d card_system -c "
SELECT 
    (SELECT COUNT(*) FROM card_types) as card_types,
    (SELECT COUNT(*) FROM owners) as owners,
    (SELECT COUNT(*) FROM applicants) as applicants,
    (SELECT COUNT(*) FROM cards) as cards,
    (SELECT COUNT(*) FROM documents) as documents,
    (SELECT COUNT(*) FROM action_log) as action_log;
"
```

### Детальная проверка

Подключитесь к базе данных и выполните запросы:

```sql
-- Проверка типов карт
SELECT * FROM card_types LIMIT 10;

-- Проверка карт
SELECT c.card_number, ct.name as type_name, o.full_name as owner_name
FROM cards c
LEFT JOIN card_types ct ON c.card_type_id = ct.id
LEFT JOIN owners o ON c.owner_id = o.id
LIMIT 10;

-- Проверка документов
SELECT d.doc_type, d.doc_number, d.doc_date, d.status
FROM documents d
ORDER BY d.created_at DESC
LIMIT 10;
```

### Сверка с исходными данными

Сравните количество записей в JSON и PostgreSQL:

```cmd
REM Для Windows (PowerShell)
powershell -c "(Get-Content data/cards.json | Measure-Object -Line).Lines / 2"

REM Для Linux/Mac
wc -l data/cards.json
```

---

## Устранение неполадок

### Ошибка: "duplicate key value violates unique constraint"

**Причина:** В таблице уже есть данные с такими же ID.

**Решение:**
```sql
-- Очистка таблиц перед загрузкой
TRUNCATE TABLE cards, documents, action_log RESTART IDENTITY CASCADE;
TRUNCATE TABLE card_types, owners, applicants, organizations, mfcs, employees RESTART IDENTITY CASCADE;
```

### Ошибка: "column does not exist"

**Причина:** Названия колонок в CSV не совпадают со структурой БД.

**Решение:**
1. Проверьте заголовки CSV файла
2. Укажите явный список колонок в команде `\COPY`
3. При необходимости переименуйте колонки в CSV

### Ошибка: "invalid input syntax for type uuid"

**Причина:** UUID в JSON формате отличается от формата PostgreSQL.

**Решение:**
```sql
-- Временное изменение типа колонки
ALTER TABLE cards ALTER COLUMN card_type_id TYPE VARCHAR(50);
-- Загрузка данных
-- Возврат типа UUID
ALTER TABLE cards ALTER COLUMN card_type_id TYPE UUID USING card_type_id::UUID;
```

### Ошибка: "date/time field value out of range"

**Причина:** Формат даты в JSON не соответствует формату PostgreSQL.

**Решение:**
1. Преобразуйте даты в формат `YYYY-MM-DD HH:MM:SS` перед загрузкой
2. Используйте команду TO_DATE в PostgreSQL:
   ```sql
   UPDATE documents SET doc_date = TO_DATE(doc_date, 'DD.MM.YYYY');
   ```

### Ошибка: "permission denied for table"

**Причина:** У пользователя нет прав на запись.

**Решение:**
```sql
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO app_user;
```

### Данные загружены, но связи не работают

**Причина:** UUID записаны как строки.

**Решение:**
```sql
-- Проверка типов данных
\d cards

-- Исправление (если нужно)
ALTER TABLE cards ALTER COLUMN card_type_id TYPE UUID USING card_type_id::UUID;
```

---

## Дополнительные материалы

### Полезные команды psql

```cmd
-- Показать все таблицы
\dt

-- Показать структуру таблицы
\d cards

-- Показать содержимое таблицы
SELECT * FROM cards LIMIT 10;

-- Выйти из psql
\q
```

### Скрипты в папке Install PostgreSQL

| Файл | Описание |
|------|----------|
| `migrate_from_json.bat` | Автоматический скрипт миграции |
| `json_to_csv.py` | Утилита преобразования JSON в CSV |
| `backup_daily.bat` | Резервное копирование |
| `restore_backup.bat` | Восстановление из резервной копии |

### Контакты поддержки

При возникновении проблем обратитесь к:
- Документации PostgreSQL: https://www.postgresql.org/docs/
- Логи PostgreSQL: `C:\Program Files\PostgreSQL\16\data\log\`

---

**Дата обновления инструкции:** 2024  
**Версия PostgreSQL:** 16.x (адаптируется под вашу версию)
