import shlex

import prompt

from primitive_db.core import create_table, drop_table
from primitive_db.utils import load_metadata, save_metadata


def print_help():
    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    print(
        "<command> create_table <имя_таблицы> <столбец1:тип> "
        "<столбец2:тип> .. - создать таблицу"
    )
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n")


def run():
    filepath = "db_meta.json"
    print_help()

    while True:
        metadata = load_metadata(filepath)
        user_input = prompt.string("Введите команду: ")

        try:
            args = shlex.split(user_input)
            if not args:
                continue

            command = args[0]

            if command == "create_table":
                if len(args) < 3:
                    raise ValueError("Укажите имя таблицы и столбцы в формате имя:тип.")

                table_name = args[1]
                metadata = create_table(metadata, table_name, args[2:])
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
                save_metadata(filepath, metadata)
                print(f'Таблица "{table_name}" успешно удалена.')

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
