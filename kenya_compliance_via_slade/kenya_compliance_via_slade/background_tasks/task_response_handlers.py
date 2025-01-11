import json

import frappe
import frappe.defaults
from frappe.model.document import Document

from ..doctype.doctype_names_mapping import (
    COUNTRIES_DOCTYPE_NAME,
    ITEM_CLASSIFICATIONS_DOCTYPE_NAME,
    PACKAGING_UNIT_DOCTYPE_NAME,
    PAYMENT_TYPE_DOCTYPE_NAME,
    TAXATION_TYPE_DOCTYPE_NAME,
    UNIT_OF_QUANTITY_DOCTYPE_NAME,
    UOM_CATEGORY_DOCTYPE_NAME,
    WORKSTATION_DOCTYPE_NAME,
)
from ..overrides.server.stock_ledger_entry import on_update
from ..utils import get_link_value


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

    doc_list = data if isinstance(data, list) else data.get("results", [data])

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


def update_unit_of_quantity(response: dict, **kwargs) -> None:
    field_mapping = {
        "slade_id": "id",
        "code": "code",
        "sort_order": "sort_order",
        "code_name": "name",
        "code_description": "description",
    }
    update_documents(response, UNIT_OF_QUANTITY_DOCTYPE_NAME, field_mapping)


def update_packaging_units(response: dict, **kwargs) -> None:
    field_mapping = {
        "slade_id": "id",
        "code": "code",
        "code_name": "name",
        "sort_order": "sort_order",
        "code_description": "description",
    }
    update_documents(response, PACKAGING_UNIT_DOCTYPE_NAME, field_mapping)


def update_payment_methods(response: dict, **kwargs) -> None:
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
    update_documents(
        response, PAYMENT_TYPE_DOCTYPE_NAME, field_mapping, filter_field="id"
    )


def update_currencies(response: dict, **kwargs) -> None:
    field_mapping = {
        "custom_slade_id": "id",
        "currency_name": "iso_code",
        "enabled": lambda x: 1 if x.get("active") else 0,
        "custom_conversion_rate": "conversion_rate",
    }
    update_documents(response, "Currency", field_mapping, filter_field="iso_code")


def update_item_classification_codes(response: dict | list, **kwargs) -> None:
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


def update_taxation_type(response: dict, **kwargs) -> None:
    doc: Document | None = None
    tax_list = response.get("results", [])

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


def update_countries(response: list, **kwargs) -> None:
    doc: Document | None = None
    for code, details in response.items():
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


def update_organisations(response: dict, **kwargs) -> None:
    if isinstance(response, str):
        try:
            response = json.loads(response)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON string: {response}")

    doc_list = (
        response
        if isinstance(response, list)
        else response.get("results", response)[:10]
    )

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

            doc.company_name = record.get("organisation_name", "")

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

        if record.get("default_currency"):
            doc.default_currency = (
                get_link_value(
                    "Currency", "custom_slade_id", record.get("default_currency")
                )
                or "KES"
            )
        if record.get("web_address"):
            doc.website = record.get("web_address", "")
        if record.get("phone_number"):
            doc.phone_no = record.get("phone_number", "")
        if record.get("description"):
            doc.company_description = record.get("description", "")
        if record.get("id"):
            doc.custom_slade_id = record.get("id", "")
        if record.get("email_address"):
            doc.email = record.get("email_address", "")
        if record.get("tax_payer_pin"):
            doc.tax_id = record.get("tax_payer_pin", "")
        doc.is_etims_verified = 1 if record.get("is_etims_verified") else 0

        doc.save()

    frappe.db.commit()


def update_branches(response: dict, **kwargs) -> None:
    field_mapping = {
        "slade_id": "id",
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
        "custom_company": {
            "doctype": "Company",
            "link_field": "organisation",
            "filter_field": "custom_slade_id",
            "extract_field": "name",
        },
        "custom_is_etims_branch": lambda x: 1 if x.get("branch_status") else 0,
        "custom_is_etims_verified": lambda x: 1 if x.get("is_etims_verified") else 0,
    }
    update_documents(response, "Branch", field_mapping, filter_field="name")


def update_departments(response: dict, **kwargs) -> None:
    if isinstance(response, str):
        try:
            response = json.loads(response)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON string: {response}")

    doc_list = (
        response if isinstance(response, list) else response.get("results", [response])
    )

    for record in doc_list:
        if isinstance(record, str):
            continue

        existing_department = frappe.db.get_value(
            "Department", {"custom_slade_id": record.get("id")}, "name"
        )
        if existing_department:
            doc = frappe.get_doc("Department", existing_department)
        else:
            department_name = record.get("name")
            matching_department = frappe.db.get_value(
                "Department", {"department_name": department_name}, "name"
            )
            if matching_department:
                branch_name = record.get("parent_name", "")
                department_name = (
                    f"{department_name} - {branch_name}"
                    if branch_name
                    else department_name
                )

            doc = frappe.new_doc("Department")
            doc.department_name = department_name

        if record.get("organisation"):
            doc.company = (
                get_link_value("Company", "custom_slade_id", record.get("organisation"))
                or frappe.defaults.get_user_default("Company")
                or frappe.get_value("Company", {}, "name")
            )
        if record.get("parent"):
            doc.custom_branch = get_link_value(
                "Branch", "slade_id", record.get("parent")
            )
        if record.get("id"):
            doc.custom_slade_id = record.get("id", "")
        doc.is_etims_verified = 1 if record.get("is_etims_verified") else 0

        doc.save()

    frappe.db.commit()


def update_workstations(response: dict, **kwargs) -> None:
    field_mapping = {
        "slade_id": "id",
        "active": lambda x: 1 if x.get("active") else 0,
        "workstation": "name",
        "workstation_type_display": "workstation_type_display",
        "workstation_type": "workstation_type",
        "is_billing_point": lambda x: 1 if x.get("is_billing_point") else 0,
        "company": {
            "doctype": "Company",
            "link_field": "organisation",
            "filter_field": "custom_slade_id",
            "extract_field": "name",
        },
        "department": {
            "doctype": "Department",
            "link_field": "org_unit",
            "filter_field": "custom_slade_id",
            "extract_field": "name",
        },
    }
    update_documents(
        response, WORKSTATION_DOCTYPE_NAME, field_mapping, filter_field="id"
    )


def uom_category_search_on_success(response: dict, **kwargs) -> None:
    field_mapping = {
        "slade_id": "id",
        "measure_type": "measure_type",
        "category_name": "name",
        "active": lambda x: 1 if x.get("active") else 0,
    }
    update_documents(
        response, UOM_CATEGORY_DOCTYPE_NAME, field_mapping, filter_field="name"
    )


def uom_search_on_success(response: dict, **kwargs) -> None:
    field_mapping = {
        "custom_slade_id": "id",
        "custom_uom_type": "uom_type",
        "custom_factor": "factor",
        "custom_category": {
            "doctype": UOM_CATEGORY_DOCTYPE_NAME,
            "link_field": "category",
            "filter_field": "slade_id",
            "extract_field": "name",
        },
        "uom_name": "name",
        "active": lambda x: 1 if x.get("active") else 0,
    }
    update_documents(response, "UOM", field_mapping, filter_field="name")


def warehouse_search_on_success(response: dict, **kwargs) -> None:
    handle_warehouse_search_on_success(response)


def location_search_on_success(response: dict, **kwargs) -> None:
    handle_warehouse_search_on_success(response, True)


def handle_warehouse_search_on_success(
    response: dict, is_location: bool = False
) -> None:
    if isinstance(response, str):
        try:
            response = json.loads(response)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON string: {response}")

    doc_list = (
        response if isinstance(response, list) else response.get("results", [response])
    )

    for record in doc_list:
        if isinstance(record, str):
            continue

        existing_warehouse = frappe.db.get_value(
            "Warehouse", {"warehouse_name": record.get("name")}, "name"
        )
        if existing_warehouse:
            doc = frappe.get_doc("Warehouse", existing_warehouse)
        else:
            warehouse_name = record.get("name")

            doc = frappe.new_doc("Warehouse")
            doc.warehouse_name = warehouse_name

        if record.get("organisation"):
            doc.company = (
                get_link_value("Company", "custom_slade_id", record.get("organisation"))
                or frappe.defaults.get_user_default("Company")
                or frappe.get_value("Company", {}, "name")
            )
        if is_location and record.get("branch"):
            doc.branch = get_link_value("Branch", "slade_id", record.get("branch"))
        if is_location and record.get("warehouse"):
            doc.parent_warehouse = get_link_value(
                "Warehouse", "custom_slade_id", record.get("warehouse")
            )
        if record.get("id"):
            doc.custom_slade_id = record.get("id", "")
        doc.disabled = 0 if record.get("active") else 1
        if not is_location:
            doc.is_group = 1

        try:
            doc.save()
        except frappe.DuplicateEntryError:
            continue

    frappe.db.commit()
