import json
from datetime import datetime, timedelta

import frappe
import frappe.defaults
from frappe.model.document import Document

from ..apis.api_builder import EndpointsBuilder
from ..apis.apis import process_request
from ..apis.remote_response_status_handlers import notices_search_on_success
from ..doctype.doctype_names_mapping import (
    OPERATION_TYPE_DOCTYPE_NAME,
    UOM_CATEGORY_DOCTYPE_NAME,
)
from ..overrides.server.stock_ledger_entry import on_update
from .task_response_handlers import (
    itemprice_search_on_success,
    location_search_on_success,
    operation_types_search_on_success,
    pricelist_search_on_success,
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


def refresh_notices() -> None:
    company = frappe.defaults.get_user_default("Company")

    perform_notice_search(json.dumps({"company_name": company}))


def send_sales_invoices_information() -> None:
    from ..overrides.server.sales_invoice import on_submit

    # Limit to only sales invoices that were created in the last 12 hours
    twelve_hours_ago = datetime.now() - timedelta(hours=12)
    all_submitted_unsent: list[Document] = frappe.get_all(
        "Sales Invoice",
        {
            "docstatus": 1,
            "custom_successfully_submitted": 0,
            "creation": [">=", twelve_hours_ago],
        },
        ["name"],
    )  # Fetch all Sales Invoice records according to filter

    if all_submitted_unsent:
        for sales_invoice in all_submitted_unsent:
            doc = frappe.get_doc(
                "Sales Invoice", sales_invoice.name, for_update=False
            )  # Refetch to get the document representation of the record

            try:
                on_submit(
                    doc, method=None
                )  # Delegate to the on_submit method for sales invoices

            except TypeError:
                continue


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


@frappe.whitelist()
def fetch_etims_pricelists(request_data: str) -> None:
    pricelists = process_request(
        request_data,
        "PriceListsSearchReq",
        pricelist_search_on_success,
        doctype="Price List",
    )
    return pricelists


@frappe.whitelist()
def fetch_etims_item_prices(request_data: str) -> None:
    itemprices = process_request(
        request_data,
        "ItemPricesSearchReq",
        itemprice_search_on_success,
        doctype="Item Price",
    )
    return itemprices


@frappe.whitelist()
def fetch_etims_operation_types(request_data: str) -> None:
    operation_types = process_request(
        request_data,
        "OperationTypesReq",
        operation_types_search_on_success,
        doctype=OPERATION_TYPE_DOCTYPE_NAME,
    )
    return operation_types


def send_stock_information() -> None:
    # Limit to only ledgers that were created in the last 12 hours
    twelve_hours_ago = datetime.now() - timedelta(hours=12)
    all_stock_ledger_entries: list[Document] = frappe.get_all(
        "Stock Ledger Entry",
        {
            "docstatus": 1,
            "custom_submitted_successfully": 0,
            "creation": [">=", twelve_hours_ago],
        },
        ["name"],
    )
    for entry in all_stock_ledger_entries:
        doc = frappe.get_doc(
            "Stock Ledger Entry", entry.name, for_update=False
        )  # Refetch to get the document representation of the record

        try:
            on_update(
                doc, method=None
            )  # Delegate to the on_update method for Stock Ledger Entry override

        except TypeError:
            continue


def send_purchase_information() -> None:
    from ..overrides.server.purchase_invoice import on_submit

    # Limit to only purchase invoices that were created in the last 12 hours
    twelve_hours_ago = datetime.now() - timedelta(hours=12)
    all_submitted_purchase_invoices: list[Document] = frappe.get_all(
        "Purchase Invoice",
        {
            "docstatus": 1,
            "custom_submitted_successfully": 0,
            "creation": [">=", twelve_hours_ago],
        },
        ["name"],
    )

    for invoice in all_submitted_purchase_invoices:
        doc = frappe.get_doc(
            "Purchase Invoice", invoice.name, for_update=False
        )  # Refetch to get the document representation of the record

        try:
            on_submit(doc, method=None)

        except TypeError:
            continue
