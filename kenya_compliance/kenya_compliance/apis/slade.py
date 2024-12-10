import json

import frappe

from ..background_tasks.tasks import (
    update_countries,
    update_item_classification_codes,
    update_packaging_units,
    update_taxation_type,
    update_unit_of_quantity,
)
from .remote_response_status_handlers import notices_search_on_success
from .apis import process_request


@frappe.whitelist()
def perform_notice_search(request_data: str) -> str:
    """Function to perform notice search."""
    message = process_request(
        request_data, "NoticeSearchReq", notices_search_on_success
    )
    return message


@frappe.whitelist()
def refresh_code_lists(request_data: str) -> str:
    """Refresh code lists based on request data."""
    tasks = [
        ("CurrencySearchReq", update_countries),
        ("PackagingUnitSearchReq", update_packaging_units),
        ("UOMSearchReq", update_unit_of_quantity),
        ("TaxSearchReq", update_taxation_type),
    ]

    messages = [process_request(request_data, task[0], task[1]) for task in tasks]

    return " ".join(messages)


@frappe.whitelist()
def get_item_classification_codes(request_data: str) -> str:
    """Function to get item classification codes."""
    message = process_request(
        request_data, "ItemClsSearchReq", update_item_classification_codes
    )
    return message
