from .create_fields_from_json import create_fields_from_json


def execute() -> None:
    create_fields_from_json(
        "./custom_fields/stock_ledger_entry.json", "Stock Ledger Entry"
    )
