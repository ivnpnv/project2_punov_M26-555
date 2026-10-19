def create_table(metadata, table_name, columns):
    if table_name in metadata:
        raise ValueError(f'Таблица "{table_name}" уже существует.')

    if not table_name or not columns:
        raise ValueError("Укажите имя таблицы и хотя бы один столбец.")

    table_columns = ["ID:int"]
    column_names = set()

    for column in columns:
        parts = column.split(":")
        if len(parts) != 2:
            raise ValueError(f"Некорректное значение: {column}. Попробуйте снова.")

        column_name, column_type = parts
        if not column_name or column_type not in ("int", "str", "bool"):
            raise ValueError(f"Некорректное значение: {column}. Попробуйте снова.")

        if column_name in column_names:
            raise ValueError(f'Столбец "{column_name}" указан повторно.')
        column_names.add(column_name)

        if column_name == "ID":
            if column_type != "int":
                raise ValueError("Столбец ID должен иметь тип int.")
        else:
            table_columns.append(column)

    metadata[table_name] = table_columns
    return metadata


def drop_table(metadata, table_name):
    if table_name not in metadata:
        raise ValueError(f'Таблица "{table_name}" не существует.')

    del metadata[table_name]
    return metadata
