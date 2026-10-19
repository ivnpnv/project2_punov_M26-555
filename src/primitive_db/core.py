from primitive_db.utils import load_table_data


def create_table(metadata, table_name, columns):
    if not table_name.isidentifier():
        raise ValueError(f"Некорректное имя таблицы: {table_name}.")

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


def insert(metadata, table_name, values):
    if table_name not in metadata:
        raise ValueError(f'Таблица "{table_name}" не существует.')

    columns = metadata[table_name][1:]
    if len(values) != len(columns):
        raise ValueError("Количество значений не соответствует количеству столбцов.")

    types = {"int": int, "str": str, "bool": bool}
    record = {}

    for column, value in zip(columns, values):
        column_name, column_type = column.split(":")
        if type(value) is not types[column_type]:
            raise ValueError(
                f'Столбец "{column_name}" должен иметь тип {column_type}.'
            )
        record[column_name] = value

    table_data = load_table_data(table_name)
    max_id = 0
    for row in table_data:
        if row["ID"] > max_id:
            max_id = row["ID"]

    new_record = {"ID": max_id + 1}
    new_record.update(record)
    table_data.append(new_record)
    return table_data


def matches_where(record, where_clause):
    for column, value in where_clause.items():
        if record[column] != value:
            return False
    return True


def select(table_data, where_clause=None):
    if where_clause is None:
        return table_data

    selected_rows = []
    for row in table_data:
        if matches_where(row, where_clause):
            selected_rows.append(row)

    return selected_rows


def update(table_data, set_clause, where_clause):
    for row in select(table_data, where_clause):
        row.update(set_clause)

    return table_data


def delete(table_data, where_clause):
    remaining_rows = []
    for row in table_data:
        if not matches_where(row, where_clause):
            remaining_rows.append(row)

    return remaining_rows
