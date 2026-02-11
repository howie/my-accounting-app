"""Bank statement parser registry and base class.

Provides a registry pattern for extensible bank-specific parsers.
New banks can be added by creating a parser class with @register_parser decorator.
"""

from src.services.bank_parsers.base import BankStatementParser, ParsedStatementTransaction

# Registry of all bank parsers: bank_code -> parser class
PARSER_REGISTRY: dict[str, type[BankStatementParser]] = {}


def register_parser(cls: type[BankStatementParser]) -> type[BankStatementParser]:
    """Decorator to auto-register bank parsers.

    Usage:
        @register_parser
        class CtbcParser(BankStatementParser):
            bank_code = "CTBC"
            ...
    """
    if not hasattr(cls, "bank_code") or not cls.bank_code:
        raise ValueError(f"Parser class {cls.__name__} must define bank_code attribute")

    PARSER_REGISTRY[cls.bank_code] = cls
    return cls


def get_parser(bank_code: str) -> BankStatementParser:
    """Get a parser instance by bank code.

    Args:
        bank_code: The bank identifier (e.g., "CTBC", "CATHAY")

    Returns:
        An instance of the parser for the specified bank.

    Raises:
        KeyError: If no parser is registered for the bank code.
    """
    if bank_code not in PARSER_REGISTRY:
        raise KeyError(f"No parser registered for bank code: {bank_code}")
    return PARSER_REGISTRY[bank_code]()


def get_all_parsers() -> list[BankStatementParser]:
    """Get instances of all registered parsers.

    Returns:
        List of parser instances for all registered banks.
    """
    return [cls() for cls in PARSER_REGISTRY.values()]


def get_all_bank_codes() -> list[str]:
    """Get all registered bank codes.

    Returns:
        List of bank codes for all registered parsers.
    """
    return list(PARSER_REGISTRY.keys())


def get_bank_info() -> list[dict]:
    """Get info for all registered banks.

    Returns:
        List of dicts with bank_code, bank_name, email_query, password_hint.
    """
    return [
        {
            "code": parser.bank_code,
            "name": parser.bank_name,
            "email_query": parser.email_query,
            "password_hint": parser.password_hint,
        }
        for parser in get_all_parsers()
    ]


__all__ = [
    "BankStatementParser",
    "ParsedStatementTransaction",
    "register_parser",
    "get_parser",
    "get_all_parsers",
    "get_all_bank_codes",
    "get_bank_info",
    "PARSER_REGISTRY",
]
