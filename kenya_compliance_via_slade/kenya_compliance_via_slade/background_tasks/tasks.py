import json

import frappe
import frappe.defaults
from frappe.model.document import Document

from ..apis.api_builder import EndpointsBuilder
from ..apis.apis import process_request
from ..apis.remote_response_status_handlers import notices_search_on_success
from ..doctype.doctype_names_mapping import (
    COUNTRIES_DOCTYPE_NAME,
    ITEM_CLASSIFICATIONS_DOCTYPE_NAME,
    PACKAGING_UNIT_DOCTYPE_NAME,
    PAYMENT_TYPE_DOCTYPE_NAME,
    TAXATION_TYPE_DOCTYPE_NAME,
    UNIT_OF_QUANTITY_DOCTYPE_NAME,
)
from ..overrides.server.stock_ledger_entry import on_update

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
        ("UOMSearchReq", update_unit_of_quantity),
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


def refresh_notices() -> None:
    from ..apis.apis import perform_notice_search

    company = frappe.defaults.get_user_default("Company")

    perform_notice_search(json.dumps({"company_name": company}))


def send_sales_invoices_information() -> None:
    from ..overrides.server.sales_invoice import on_submit

    all_submitted_unsent: list[Document] = frappe.get_all(
        "Sales Invoice", {"docstatus": 1, "custom_successfully_submitted": 0}, ["name"]
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


def send_pos_invoices_information() -> None:
    from ..overrides.server.sales_invoice import on_submit

    all_pending_pos_invoices: list[Document] = frappe.get_all(
        "POS Invoice", {"docstatus": 1, "custom_successfully_submitted": 0}, ["name"]
    )

    if all_pending_pos_invoices:
        for pos_invoice in all_pending_pos_invoices:
            doc = frappe.get_doc(
                "POS Invoice", pos_invoice.name, for_update=False
            )  # Refetch to get the document representation of the record

            try:
                on_submit(
                    doc, method=None
                )  # Delegate to the on_submit method for sales invoices

            except TypeError:
                continue


def send_stock_information() -> None:
    all_stock_ledger_entries: list[Document] = frappe.get_all(
        "Stock Ledger Entry",
        {"docstatus": 1, "custom_submitted_successfully": 0},
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

    all_submitted_purchase_invoices: list[Document] = frappe.get_all(
        "Purchase Invoice",
        {"docstatus": 1, "custom_submitted_successfully": 0},
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


def send_item_inventory_information() -> None:
    from ..apis.apis import submit_inventory

    query = """
        SELECT sle.name as name,
            sle.owner,
            sle.custom_submitted_successfully,
            sle.custom_inventory_submitted_successfully,
            qty_after_transaction as residual_qty,
            sle.warehouse,
            w.custom_branch as branch_id,
            i.item_code as item,
            custom_item_code_etims as item_code
        FROM `tabStock Ledger Entry` sle
            INNER JOIN tabItem i ON sle.item_code = i.item_code
            INNER JOIN tabWarehouse w ON sle.warehouse = w.name
        WHERE sle.custom_submitted_successfully = '1'
            AND sle.custom_inventory_submitted_successfully = '0'
        ORDER BY sle.creation DESC;
        """

    sles = frappe.db.sql(query, as_dict=True)

    for stock_ledger in sles:
        response = json.dumps(stock_ledger)

        try:
            submit_inventory(response)

        except Exception as error:
            # TODO: Suspicious looking type(error)
            frappe.throw("Error Encountered", type(error), title="Error")


def update_documents(
    data: dict | list,
    doctype_name: str,
    field_mapping: dict,
    filter_field: str = "code",
) -> None:
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON string: {data}")

    doc_list = data if isinstance(data, list) else data.get("results", data)

    for record in doc_list:
        if isinstance(record, str):
            continue

        filter_value = record.get(filter_field)
        try:
            doc = frappe.get_doc(doctype_name, filter_value)
        except frappe.DoesNotExistError:
            doc = frappe.new_doc(doctype_name)

        for field, value in field_mapping.items():
            if callable(value):
                setattr(doc, field, value(record))
            elif isinstance(value, dict):
                linked_doctype = value.get("doctype")
                link_field = value.get("link_field")
                link_filter_field = value.get("filter_field", "custom_slade_id")
                link_extract_field = value.get("extract_field", "name")
                link_filter_value = record.get(link_field)
                if linked_doctype and link_filter_value:
                    linked_value = frappe.db.get_value(
                        linked_doctype,
                        {link_filter_field: link_filter_value},
                        link_extract_field,
                    )
                    setattr(doc, field, linked_value or "")
            else:
                setattr(doc, field, record.get(value, ""))

        doc.save()

    frappe.db.commit()


def update_unit_of_quantity(data: dict, document_name: str) -> None:
    field_mapping = {
        "slade_id": "id",
        "code": "code",
        "sort_order": "sort_order",
        "code_name": "name",
        "code_description": "description",
    }
    update_documents(data, UNIT_OF_QUANTITY_DOCTYPE_NAME, field_mapping)


def update_packaging_units(data: dict, document_name: str) -> None:
    field_mapping = {
        "slade_id": "id",
        "code": "code",
        "code_name": "name",
        "sort_order": "sort_order",
        "code_description": "description",
    }
    update_documents(data, PACKAGING_UNIT_DOCTYPE_NAME, field_mapping)


def update_payment_methods(data: dict, document_name: str) -> None:
    field_mapping = {
        "slade_id": "id",
        "account_details": "account_details",
        "mobile_money_type": "mobile_money_type",
        "mobile_money_business_number": "mobile_money_business_number",
        "bank_name": "bank_name",
        "bank_branch": "bank_branch",
        "bank_account_number": "bank_account_number",
        "active": lambda x: 1 if x.get("active") else 0,
        "code_name": "name",
        "description": "description",
        "account": "account",
    }
    update_documents(data, PAYMENT_TYPE_DOCTYPE_NAME, field_mapping, filter_field="id")


def update_currencies(data: dict, document_name: str) -> None:
    field_mapping = {
        "slade_id": "id",
        "currency_name": "iso_code",
        "enabled": lambda x: 1 if x.get("active") else 0,
        "custom_conversion_rate": "conversion_rate",
    }
    update_documents(data, "Currency", field_mapping, filter_field="iso_code")


def update_item_classification_codes(response: dict | list, document_name: str) -> None:
    field_mapping = {
        "slade_id": "id",
        "itemclscd": "classification_code",
        "itemclslvl": "classification_level",
        "itemclsnm": "classification_name",
        "taxtycd": "tax_type_code",
        "useyn": lambda x: 1 if x.get("is_used") else 0,
        "mjrtgyn": lambda x: 1 if x.get("is_frequently_used") else 0,
    }
    update_documents(
        response,
        ITEM_CLASSIFICATIONS_DOCTYPE_NAME,
        field_mapping,
        filter_field="classification_code",
    )


def update_taxation_type(data: dict, document_name: str) -> None:
    doc: Document | None = None
    tax_list = data.get("results", [])

    for taxation_type in tax_list:
        code = (
            taxation_type["tax_code"]
            if taxation_type["tax_code"]
            else taxation_type["name"]
        )
        try:
            doc_name = frappe.db.get_value(
                TAXATION_TYPE_DOCTYPE_NAME, {"cd": code}, "name"
            )
            doc = frappe.get_doc(TAXATION_TYPE_DOCTYPE_NAME, doc_name)

        except Exception:
            doc = frappe.new_doc(TAXATION_TYPE_DOCTYPE_NAME)

        finally:
            doc.cd = code
            doc.cdnm = taxation_type["name"]
            doc.slade_id = taxation_type["id"]
            doc.cddesc = taxation_type["description"]
            doc.useyn = 1 if taxation_type["active"] else 0
            doc.srtord = taxation_type["percentage"]

            doc.save()

    frappe.db.commit()


def update_countries(data: list, document_name: str) -> None:
    doc: Document | None = None
    for code, details in data.items():
        country_name = details.get("name", "").strip().lower()
        existing_doc = frappe.get_value(
            COUNTRIES_DOCTYPE_NAME, {"name": ["like", country_name]}
        )

        if existing_doc:
            doc = frappe.get_doc(COUNTRIES_DOCTYPE_NAME, existing_doc)
        else:
            doc = frappe.new_doc(COUNTRIES_DOCTYPE_NAME)

        doc.code = code
        doc.code_name = details.get("name")
        doc.currency_code = details.get("currency_code")
        doc.sort_order = details.get("sort_order", 0)
        doc.code_description = details.get("description", "")

        doc.save()

    frappe.db.commit()


def update_organisations(data: dict, document_name: str) -> None:
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON string: {data}")

    # Limiting to first 5 records temporarily; remove slicing [:5] later
    doc_list = data if isinstance(data, list) else data.get("results", data)[:5]

    for record in doc_list:
        if isinstance(record, str):
            continue

        filter_value = record.get("organisation_name")
        company_name = frappe.db.get_value(
            "Company", {"company_name": filter_value}, "name"
        )

        if company_name:
            doc = frappe.get_doc("Company", company_name)
        else:
            doc = frappe.new_doc("Company")
            doc.default_currency = "KES"

            doc.company_name = record.get("organisation_name", "Default Company")
            doc.default_country = record.get("default_country", "Kenya")
            doc.company_description = record.get(
                "description", "No description provided."
            )
            doc.email = record.get("email_address", "no-email@default.com")
            doc.phone_no = record.get("phone_number", "000-000-0000")
            generated_abbr = "".join(
                [word[0] for word in doc.company_name.split()]
            ).upper()[:5]
            existing_abbr = frappe.db.exists("Company", {"abbr": generated_abbr})

            if existing_abbr:
                counter = 1
                unique_abbr = generated_abbr
                while frappe.db.exists("Company", {"abbr": unique_abbr}):
                    unique_abbr = f"{generated_abbr}{counter}"
                    counter += 1
                doc.abbr = unique_abbr
            else:
                doc.abbr = generated_abbr

        doc.custom_slade_id = record.get("id", "")
        doc.tax_id = record.get("organisation_tax_pin", "")
        doc.is_etims_verified = 1 if record.get("is_etims_verified") else 0

        doc.save()

    frappe.db.commit()


def update_branches(data: dict, document_name: str) -> None:
    field_mapping = {
        "custom_slade_id": "id",
        "tax_id": "organisation_tax_pin",
        "branch": "name",
        "custom_etims_device_serial_no": "etims_device_serial_no",
        "custom_branch_code": "etims_branch_id",
        "custom_pin": "organisation_tax_pin",
        "custom_branch_name": "name",
        "custom_county_name": "county_name",
        "custom_tax_locality_name": "tax_locality_name",
        "custom_sub_county_name": "sub_county_name",
        "custom_manager_name": "manager_name",
        "custom_location_description": "location_description",
        "custom_is_head_office": lambda x: 1 if x.get("is_headquater") else 0,
        "company": {
            "doctype": "Company",
            "link_field": "organisation",
            "filter_field": "custom_slade_id",
            "extract_field": "name",
        },
        "custom_is_etims_branch": lambda x: 1 if x.get("branch_status") else 0,
        "custom_is_etims_verified": lambda x: 1 if x.get("is_etims_verified") else 0,
    }
    update_documents(data, "Branch", field_mapping, filter_field="id")


def update_departments(data: dict, document_name: str) -> None:
    field_mapping = {
        "custom_slade_id": "id",
        "tax_id": "organisation_tax_pin",
        "department_name": "name",
        "company": {
            "doctype": "Company",
            "link_field": "organisation",
            "filter_field": "custom_slade_id",
            "extract_field": "name",
        },
        "is_etims_verified": lambda x: 1 if x.get("is_etims_verified") else 0,
    }
    update_documents(data, "Department", field_mapping, filter_field="id")
