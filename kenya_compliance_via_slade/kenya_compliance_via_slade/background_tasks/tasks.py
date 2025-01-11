import frappe
import frappe.defaults

from ..apis.api_builder import EndpointsBuilder
from ..apis.apis import process_request
from ..apis.remote_response_status_handlers import notices_search_on_success
from ..doctype.doctype_names_mapping import UOM_CATEGORY_DOCTYPE_NAME
from .task_response_handlers import (
    location_search_on_success,
    uom_category_search_on_success,
    uom_search_on_success,
    update_branches,
    update_countries,
    update_currencies,
    update_departments,
    update_item_classification_codes,
    update_organisations,
    update_packaging_units,
    update_payment_methods,
    update_taxation_type,
    update_unit_of_quantity,
    update_workstations,
    warehouse_search_on_success,
)

endpoints_builder = EndpointsBuilder()


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
        ("CurrencyCountrySearchReq", update_countries),
        ("CurrencySearchReq", update_currencies),
        ("PackagingUnitSearchReq", update_packaging_units),
        ("QuantityUnitsSearchReq", update_unit_of_quantity),
        ("TaxSearchReq", update_taxation_type),
        ("PaymentMtdSearchReq", update_payment_methods),
    ]

    messages = [process_request(request_data, task[0], task[1]) for task in tasks]

    return " ".join(messages)


@frappe.whitelist()
def search_organisations_request(request_data: str) -> str:
    """Refresh code lists based on request data."""
    tasks = [
        ("OrgSearchReq", update_organisations),
        ("BhfSearchReq", update_branches),
        ("DeptSearchReq", update_departments),
        ("WorkstationSearchReq", update_workstations),
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


@frappe.whitelist()
def fetch_etims_uom_categories(request_data: str) -> None:
    message = process_request(
        request_data,
        "UOMCategoriesSearchReq",
        uom_category_search_on_success,
        doctype=UOM_CATEGORY_DOCTYPE_NAME,
    )
    return message


@frappe.whitelist()
def fetch_etims_uom_list(request_data: str) -> None:
    message = process_request(
        request_data,
        "UOMListSearchReq",
        uom_search_on_success,
        doctype="UOM",
    )
    return message


@frappe.whitelist()
def fetch_etims_warehouse_list(request_data: str) -> None:
    warehouses = process_request(
        request_data,
        "WarehousesSearchReq",
        warehouse_search_on_success,
        doctype="Warehouse",
    )
    locations = process_request(
        request_data,
        "LocationsSearchReq",
        location_search_on_success,
        doctype="Warehouse",
    )
    return warehouses, locations
