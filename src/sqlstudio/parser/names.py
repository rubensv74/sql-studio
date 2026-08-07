from __future__ import annotations


def split_qualified_parts(value: str) -> list[str]:
    """Split a multipart SQL identifier on dots outside bracket quoting."""

    parts: list[str] = []
    current: list[str] = []
    in_brackets = False
    index = 0

    while index < len(value):
        char = value[index]
        if char == "[":
            in_brackets = True
            current.append(char)
            index += 1
            continue
        if char == "]" and in_brackets:
            if index + 1 < len(value) and value[index + 1] == "]":
                current.extend(("]", "]"))
                index += 2
                continue
            in_brackets = False
            current.append(char)
            index += 1
            continue
        if char == "." and not in_brackets:
            part = "".join(current).strip()
            if part:
                parts.append(_unquote_bracket_identifier(part))
            current = []
            index += 1
            continue
        current.append(char)
        index += 1

    part = "".join(current).strip()
    if part:
        parts.append(_unquote_bracket_identifier(part))
    return parts


def split_qualified_name(value: str) -> tuple[str | None, str | None, str | None]:
    """Return name, schema and database from a supported multipart identifier."""

    parts = split_qualified_parts(value)
    if not parts:
        return None, None, None
    name = parts[-1]
    schema = parts[-2] if len(parts) > 1 else None
    database = parts[-3] if len(parts) > 2 else None
    return name, schema, database


def normalize_identifier(value: str) -> str:
    """Normalize one SQL identifier for case-insensitive alias/CTE matching."""

    parts = split_qualified_parts(value)
    return (parts[-1] if parts else value.strip()).casefold()


def _unquote_bracket_identifier(value: str) -> str:
    if len(value) >= 2 and value.startswith("[") and value.endswith("]"):
        return value[1:-1].replace("]]", "]")
    return value
