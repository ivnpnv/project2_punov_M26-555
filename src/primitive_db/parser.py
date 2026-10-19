import json
import shlex


def parse_value(value):
    if value.startswith("'") and value.endswith("'"):
        return shlex.split(value)[0]

    try:
        result = json.loads(value)
    except json.JSONDecodeError:
        raise ValueError(
            f"Некорректное значение: {value}. Строки указывайте в кавычках."
        ) from None

    if type(result) not in (str, int, bool):
        raise ValueError("Допустимы только строки, целые числа и true/false.")

    return result


def parse_assignment(tokens):
    if len(tokens) != 3 or tokens[1] != "=":
        raise ValueError("Ожидается условие в формате столбец = значение.")

    column = tokens[0]
    if not column.isidentifier():
        raise ValueError(f"Некорректное имя столбца: {column}.")

    return {column: parse_value(tokens[2])}


def parse_where(clause):
    lexer = shlex.shlex(clause, posix=False, punctuation_chars="=")
    lexer.whitespace_split = True
    lexer.commenters = ""

    return parse_assignment(list(lexer))


def parse_set(clause):
    lexer = shlex.shlex(clause, posix=False, punctuation_chars="=,")
    lexer.whitespace_split = True
    lexer.commenters = ""
    tokens = list(lexer)
    result = {}
    assignment = []

    for token in tokens:
        if token == ",":
            result.update(parse_assignment(assignment))
            assignment = []
        else:
            assignment.append(token)

    result.update(parse_assignment(assignment))
    return result


def parse_values(clause):
    lexer = shlex.shlex(clause, posix=False, punctuation_chars=",")
    lexer.whitespace_split = True
    lexer.commenters = ""
    tokens = list(lexer)
    if not tokens:
        return []

    if len(tokens) % 2 == 0:
        raise ValueError("Значения должны быть разделены запятыми.")

    values = []
    for index, token in enumerate(tokens):
        if index % 2 == 0:
            values.append(parse_value(token))
        elif token != ",":
            raise ValueError("Значения должны быть разделены запятыми.")

    return values
