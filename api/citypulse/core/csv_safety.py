"""Spreadsheet formula-injection defence. We never evaluate cells; on export, text that a
spreadsheet could interpret as a formula is prefixed with an apostrophe (OWASP CSV injection)."""
import re

_TRIGGER = re.compile(r"^[\s]*[=+\-@\t\r]")
_NUMBER = re.compile(r"^[\s]*[+-]?\d+([.,]\d+)?\s*$")


def is_formula_like(value: str) -> bool:
    """True for text starting with = + - @ (plain signed numbers are not formulas)."""
    return bool(value) and bool(_TRIGGER.match(value)) and not _NUMBER.match(value)


def neutralise_formula(value: str) -> str:
    return "'" + value if is_formula_like(value) else value
