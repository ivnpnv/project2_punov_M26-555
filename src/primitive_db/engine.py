import shlex

import prompt
from prettytable import PrettyTable

from primitive_db.core import create_table, delete, drop_table, insert, select, update
from primitive_db.parser import parse_set, parse_values, parse_where
from primitive_db.utils import (
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
)


def print_help():
    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    print(
        "<command> create_table <имя_таблицы> <столбец1:тип> "
        "<столбец2:тип> .. - создать таблицу"
    )
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")
    print(
        "<command> insert into <имя_таблицы> values (<значение1>, ...) "
        "- добавить запись"
    )
    print(
        "<command> select from <имя_таблицы> "
        "[where <столбец> = <значение>] - прочитать"
    )
    print(
        "<command> update <имя_таблицы> set <столбец> = <значение> "
        "where <столбец> = <значение> - обновить"
    )
    print("<command> delete from <имя_таблицы> where <столбец> = <значение> - удалить")
    print("<command> info <имя_таблицы> - информация о таблице")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n")


def get_table_data(metadata, table_name):
    if table_name not in metadata:
        raise ValueError(f'Таблица "{table_name}" не существует.')
    return load_table_data(table_name)


def validate_clause(columns, clause):
    column_types = {}
    for column in columns:
        name, column_type = column.split(":")
        column_types[name] = column_type

    types = {"int": int, "str": str, "bool": bool}
    for name, value in clause.items():
        if name not in column_types:
            raise ValueError(f'Столбец "{name}" не существует.')
        column_type = column_types[name]
        if type(value) is not types[column_type]:
            raise ValueError(f'Столбец "{name}" должен иметь тип {column_type}.')


def print_rows(columns, rows):
    table = PrettyTable()
    table.field_names = [column.split(":")[0] for column in columns]
    for row in rows:
        table.add_row([row[name] for name in table.field_names])
    print(table)


def run():
    filepath = "db_meta.json"
    print_help()

    while True:
        metadata = load_metadata(filepath)
        user_input = prompt.string("Введите команду: ")

        try:
            lexer = shlex.shlex(user_input, posix=False, punctuation_chars="=,()")
            lexer.whitespace_split = True
            lexer.commenters = ""
            args = list(lexer)
            if not args:
                continue

            command = args[0]

            if command == "create_table":
                if len(args) < 3:
                    raise ValueError("Укажите имя таблицы и столбцы в формате имя:тип.")

                table_name = args[1]
                metadata = create_table(metadata, table_name, args[2:])
                if metadata is None:
                    continue
                save_table_data(table_name, [])
                save_metadata(filepath, metadata)
                columns = ", ".join(metadata[table_name])
                print(
                    f'Таблица "{table_name}" успешно создана '
                    f"со столбцами: {columns}"
                )

            elif command == "drop_table":
                if len(args) != 2:
                    raise ValueError("Укажите одно имя таблицы для удаления.")

                table_name = args[1]
                metadata = drop_table(metadata, table_name)
                if metadata is None:
                    continue
                save_metadata(filepath, metadata)
                print(f'Таблица "{table_name}" успешно удалена.')

            elif command == "insert":
                if (
                    len(args) < 6
                    or args[1] != "into"
                    or args[3] != "values"
                    or args[4] != "("
                    or args[-1] != ")"
                ):
                    raise ValueError(
                        "Формат: insert into <таблица> values (<значения>)."
                    )

                table_name = args[2]
                values = parse_values(" ".join(args[5:-1]))
                table_data = insert(metadata, table_name, values)
                if table_data is None:
                    continue
                save_table_data(table_name, table_data)
                record_id = table_data[-1]["ID"]
                print(
                    f'Запись с ID={record_id} успешно добавлена '
                    f'в таблицу "{table_name}".'
                )

            elif command == "select":
                if len(args) < 3 or args[1] != "from":
                    raise ValueError("Формат: select from <таблица> [where <условие>].")

                table_name = args[2]
                table_data = get_table_data(metadata, table_name)
                where_clause = None
                if len(args) > 3:
                    if args[3] != "where":
                        raise ValueError("После имени таблицы ожидается where.")
                    where_clause = parse_where(" ".join(args[4:]))
                    validate_clause(metadata[table_name], where_clause)
                rows = select(table_data, where_clause)
                if rows is None:
                    continue
                print_rows(metadata[table_name], rows)

            elif command == "update":
                if len(args) < 4 or args[2] != "set" or "where" not in args[3:]:
                    raise ValueError(
                        "Формат: update <таблица> set <поля> where <условие>."
                    )

                table_name = args[1]
                table_data = get_table_data(metadata, table_name)
                where_index = args.index("where", 3)
                set_clause = parse_set(" ".join(args[3:where_index]))
                where_clause = parse_where(" ".join(args[where_index + 1:]))
                validate_clause(metadata[table_name], set_clause)
                validate_clause(metadata[table_name], where_clause)
                if "ID" in set_clause:
                    raise ValueError("ID назначается автоматически и не изменяется.")
                matched_rows = select(table_data, where_clause)
                if matched_rows is None:
                    continue
                table_data = update(table_data, set_clause, where_clause)
                if table_data is None:
                    continue
                save_table_data(table_name, table_data)
                if not matched_rows:
                    print("Подходящих записей нет.")
                for row in matched_rows:
                    print(
                        f'Запись с ID={row["ID"]} в таблице '
                        f'"{table_name}" успешно обновлена.'
                    )

            elif command == "delete":
                if len(args) < 5 or args[1] != "from" or args[3] != "where":
                    raise ValueError("Формат: delete from <таблица> where <условие>.")

                table_name = args[2]
                table_data = get_table_data(metadata, table_name)
                where_clause = parse_where(" ".join(args[4:]))
                validate_clause(metadata[table_name], where_clause)
                matched_rows = select(table_data, where_clause)
                if matched_rows is None:
                    continue
                table_data = delete(table_data, where_clause)
                if table_data is None:
                    continue
                save_table_data(table_name, table_data)
                if not matched_rows:
                    print("Подходящих записей нет.")
                for row in matched_rows:
                    print(
                        f'Запись с ID={row["ID"]} успешно удалена '
                        f'из таблицы "{table_name}".'
                    )

            elif command == "info":
                if len(args) != 2:
                    raise ValueError("Формат: info <таблица>.")
                table_name = args[1]
                table_data = get_table_data(metadata, table_name)
                print(f"Таблица: {table_name}")
                print(f'Столбцы: {", ".join(metadata[table_name])}')
                print(f"Количество записей: {len(table_data)}")

            elif command in ("list_tables", "help", "exit"):
                if len(args) != 1:
                    raise ValueError(f"Команда {command} не принимает аргументы.")

                if command == "list_tables":
                    if not metadata:
                        print("Таблиц пока нет.")
                    for table_name in metadata:
                        print(f"- {table_name}")
                elif command == "help":
                    print_help()
                else:
                    break

            else:
                print(f"Функции {command} нет. Попробуйте снова.")

        except ValueError as error:
            print(f"Ошибка: {error}")
