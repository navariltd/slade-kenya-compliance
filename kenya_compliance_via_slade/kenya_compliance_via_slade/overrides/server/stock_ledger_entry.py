import uuid
from hashlib import sha256

import frappe
from frappe.model.document import Document

from ...apis.api_builder import EndpointsBuilder

# from ...apis.apis import save_operation_type
from ...apis.process_request import process_request
from ...doctype.doctype_names_mapping import (
    OPERATION_TYPE_DOCTYPE_NAME,
    SETTINGS_DOCTYPE_NAME,
)
from ...utils import extract_document_series_number, get_settings

endpoints_builder = EndpointsBuilder()


def on_update(doc: Document, method: str | None = None) -> None:
    if not frappe.db.exists(SETTINGS_DOCTYPE_NAME, {"is_active": 1}):
        return

    save_ledger_details(doc.name)


@frappe.whitelist()
def save_ledger_details(name: str) -> None:
    try:
        doc = frappe.get_doc("Stock Ledger Entry", name)
        if doc.custom_submitted_successfully:
            return

        elif not doc.custom_slade_id:
            record = frappe.get_doc(doc.voucher_type, doc.voucher_no)
            if (
                doc.voucher_type == "Stock Entry"
                and getattr(record, "stock_entry_type", "") == "Material Transfer"
            ):
                return
            else:
                payload = prepare_payload(doc, record)
                handle_operation_type(doc, record, payload)

        elif not doc.custom_inventory_submitted_successfully:
            stock_mvt_submission_on_success(
                response={"id": not doc.custom_slade_id}, document_name=name
            )

        else:
            stock_mvt_submit_items_on_success(response={}, document_name=name)

    except Exception as e:
        frappe.log_error(
            title=f"Error Fetching submitting ledger {name}",
            message=f"Error while submitting: {str(e)}",
        )


def prepare_payload(doc: dict, record: dict) -> dict:
    company_name = doc.company
    settings = get_settings(company_name=company_name)
    series_no = extract_document_series_number(record)

    payload = {
        "name": doc.name,
        "document_name": doc.name,
        "organisation": frappe.get_value("Company", company_name, "custom_slade_id"),
        "source_organisation_unit": frappe.get_value(
            "Department", settings.department, "custom_slade_id"
        ),
        "document_number": doc.name,
        "document_count": series_no,
    }

    payload["document_type"] = map_document_type(doc, record)

    if doc.voucher_type == "Stock Reconciliation" or (
        doc.voucher_type == "Stock Entry" and record.is_opening == "Yes"
    ):
        update_payload_for_stock_reconciliation(doc, payload)

    if doc.voucher_type in ("Purchase Receipt", "Purchase Invoice"):
        update_payload_for_purchase(doc, record, payload)

    if doc.voucher_type in ("Delivery Note", "Sales Invoice"):
        update_payload_for_sales(doc, record, payload)

    return payload


def map_document_type(doc: dict, record: dict) -> str:
    document_type_mapping = {
        "Stock Reconciliation": "stock_take",
        "Purchase Receipt": "grn",
        "Purchase Invoice": "purchases_invoice",
        "Delivery Note": "gdn",
        "Sales Invoice": "sales_invoice",
    }

    if doc.voucher_type in document_type_mapping:
        return document_type_mapping[doc.voucher_type]

    if doc.voucher_type == "Stock Entry":
        if record.is_opening == "Yes":
            return "stock_take"
        if doc.actual_qty > 0:
            return "warehouse_in"
        elif doc.actual_qty < 0:
            return "warehouse_out"

    return None


def update_payload_for_stock_reconciliation(doc: dict, payload: dict) -> None:
    settings = get_settings(company_name=doc.company)
    payload.update(
        {
            "inventory_reference": doc.name,
            "reason": "Stock Reconciliation",
            "location": frappe.get_value(
                "Warehouse", settings.warehouse, "custom_slade_id"
            ),
        }
    )


def update_payload_for_purchase(doc: dict, record: dict, payload: dict) -> None:
    if record.is_return:
        payload["document_type"] = "return_inwards"
    elif frappe.get_value("Item", doc.item_code, "is_imported_item"):
        payload["document_type"] = "purchases_invoice"


def update_payload_for_sales(doc: dict, record: dict, payload: dict) -> None:
    if (
        doc.voucher_type == "Sales Invoice"
        and record.custom_successfully_submitted != 1
    ):
        return

    if record.is_return:
        payload["document_type"] = (
            "return_inwards" if doc.actual_qty > 0 else "return_outwards"
        )


def handle_operation_type(doc: dict, record: dict, payload: dict) -> None:
    settings = get_settings(company_name=doc.company)
    warehouse = frappe.get_doc("Warehouse", settings.warehouse)
    if doc.voucher_type == "Stock Reconciliation" or (
        doc.voucher_type == "Stock Entry" and record.is_opening == "Yes"
    ):
        submit_stock_mvt(payload, "StockMasterSaveReq")

    else:
        operation_type = get_operation_type(doc, payload["document_type"])

        matching_operation = frappe.db.get_value(
            OPERATION_TYPE_DOCTYPE_NAME,
            {"operation_type": operation_type, "warehouse": settings.warehouse},
            ["name", "slade_id"],
        )

        if matching_operation:
            payload["operation_type"] = matching_operation[1]
            submit_stock_mvt(payload, "StockIOSaveReq")
        else:
            create_and_enqueue_operation(doc, operation_type, warehouse)


def get_operation_type(doc: dict, document_type: str) -> dict:
    document_to_operation_mapping = {
        "warehouse_in": "incoming",
        "warehouse_out": "outgoing",
        "stock_take": "internal",
        "inventory_operation": "internal",
        "grn": "incoming",
        "gdn": "outgoing",
        "purchases_invoice": "incoming",
        "sales_invoice": "outgoing",
        "return_inwards": "incoming",
        "return_outwards": "outgoing",
    }
    operation_type = document_to_operation_mapping.get(document_type)

    return operation_type


def create_and_enqueue_operation(
    doc: dict, operation_type: dict, warehouse: Document
) -> None:
    name_parts = [doc.company, warehouse.name, operation_type]
    new_operation_type = frappe.get_doc(
        {
            "doctype": OPERATION_TYPE_DOCTYPE_NAME,
            "operation_type": operation_type,
            "company": doc.company,
            "warehouse": warehouse.name,
            "source_location": (
                warehouse.custom_slade_supplier_warehouse
                if operation_type == "outgoing"
                else warehouse.custom_slade_id
            ),
            "destination_location": (
                warehouse.custom_slade_customer_warehouse
                if operation_type == "incoming"
                else warehouse.custom_slade_id
            ),
            "operation_name": " ".join(name_parts),
            "active": 1,
        }
    )
    new_operation_type.insert()


def get_default(field: str) -> str:
    return frappe.defaults.get_user_default(field) or frappe.get_value(
        field, {}, "name"
    )


def stock_operation_type_submit_on_success(
    response: dict, document_name: str, **kwargs
) -> None:
    frappe.db.set_value(
        OPERATION_TYPE_DOCTYPE_NAME, document_name, {"slade_id": response.get("id")}
    )
    save_ledger_details(kwargs.get("doc_name"))


def submit_stock_mvt(payload: dict, route_key: str, **kwargs) -> None:
    frappe.enqueue(
        process_request,
        queue="default",
        doctype="Stock Ledger Entry",
        request_data=payload,
        route_key=route_key,
        handler_function=stock_mvt_submission_on_success,
        request_method="POST",
    )


def is_valid_uuid(uuid_to_test: str, version: int = 4) -> bool:
    try:
        uuid_obj = uuid.UUID(uuid_to_test, version=version)
    except ValueError:
        return False
    return str(uuid_obj) == uuid_to_test


def stock_mvt_submission_on_success(
    response: dict, document_name: str, **kwargs
) -> None:
    id = response.get("id")
    if not id or id == "0" or not is_valid_uuid(id):
        frappe.log_error(
            title=f"Invalid ID for Stock Ledger Entry {document_name}",
            message="Received invalid ID from response",
        )
        return

    frappe.db.set_value("Stock Ledger Entry", document_name, {"custom_slade_id": id})
    doc = frappe.get_doc("Stock Ledger Entry", document_name)

    record = frappe.get_doc(doc.voucher_type, doc.voucher_no)
    item = frappe.get_doc("Item", doc.item_code)
    route_key = "StockIOLineReq"
    requset_data = {
        "document_name": document_name,
        "organisation": frappe.get_value("Company", record.company, "custom_slade_id"),
        "source_organisation_unit": frappe.get_value(
            "Department", record.department, "custom_slade_id"
        ),
        "product": item.custom_slade_id,
        "quantity": abs(doc.actual_qty),
        "quantity_confirmed": abs(doc.actual_qty),
    }
    if doc.voucher_type == "Stock Reconciliation" or (
        doc.voucher_type == "Stock Entry" and record.is_opening == "Yes"
    ):
        route_key = "StockMasterLineReq"
        requset_data["quantity"] = get_total_stock_balance(doc.item_code)

    if route_key == "StockIOLineReq":
        requset_data["inventory_operation"] = id
    else:
        requset_data["inventory_adjustment"] = id
    frappe.enqueue(
        process_request,
        queue="default",
        is_async=True,
        timeout=300,
        job_name=sha256(
            f"{doc.name}{doc.creation}{doc.modified}".encode(), usedforsecurity=False
        ).hexdigest(),
        doctype="Stock Ledger Entry",
        request_data=requset_data,
        route_key=route_key,
        handler_function=stock_mvt_submit_items_on_success,
        request_method="POST",
    )


def get_total_stock_balance(item_code: str) -> float:
    bins = frappe.get_all(
        "Bin", filters={"item_code": item_code}, fields=["warehouse", "actual_qty"]
    )

    total_qty = sum(float(bin["actual_qty"]) for bin in bins)

    return total_qty


def stock_mvt_submit_items_on_success(
    response: dict, document_name: str, **kwargs
) -> None:
    frappe.db.set_value(
        "Stock Ledger Entry",
        document_name,
        {"custom_inventory_submitted_successfully": 1},
    )
    doc = frappe.get_doc("Stock Ledger Entry", document_name)
    if doc.voucher_type == "Stock Reconciliation":
        route_key = "StockAdjustmentTransitionReq"
    else:
        route_key = "StockOperationTransitionReq"
    requset_data = {
        "document_name": document_name,
        "id": doc.custom_slade_id,
    }
    frappe.enqueue(
        process_request,
        queue="default",
        doctype="Stock Ledger Entry",
        request_data=requset_data,
        route_key=route_key,
        handler_function=process_stock_mvt_transition,
        request_method="PATCH",
        error_callback=stock_operation_on_error,
    )


def stock_operation_on_error(response_data: dict, document_name: str, **kwargs) -> None:
    from ...apis.apis import submit_inventory

    doc = frappe.get_doc("Stock Ledger Entry", document_name)

    submit_inventory(doc.item_code)


def process_stock_mvt_transition(response: dict, document_name: str, **kwargs) -> None:
    frappe.db.set_value(
        "Stock Ledger Entry", document_name, {"custom_submitted_successfully": 1}
    )
    doc = frappe.get_doc("Stock Ledger Entry", document_name)
    settings = get_settings(company_name=doc.company)
    requset_data = {
        "document_name": document_name,
        "location": frappe.get_value(
            "Warehouse", settings.warehouse, "custom_slade_id"
        ),
        "product": frappe.get_value("Item", doc.item_code, "custom_slade_id"),
    }
    frappe.enqueue(
        process_request,
        queue="default",
        doctype="Stock Ledger Entry",
        request_data=requset_data,
        route_key="GetStockBalanceReq",
        handler_function=stock_balance_on_success,
        request_method="GET",
    )


def stock_balance_on_success(response: dict, document_name: str, **kwargs) -> None:
    from ...apis.apis import submit_inventory, update_stock_quantity

    doc = frappe.get_doc("Stock Ledger Entry", document_name)

    results = (
        response.get("results", [])
        if isinstance(response, dict)
        else response if isinstance(response, list) else []
    )

    if not results:
        submit_inventory(doc.item_code)
        return

    slade_balance = float(results[0].get("quantity", 0)) if results else 0

    if slade_balance <= 0:

        frappe.enqueue(
            update_stock_quantity,
            queue="default",
            name=doc.item_code,
            id=results[0].get("id"),
        )
        return

    frappe.db.set_value(
        "Stock Ledger Entry", document_name, {"custom_new_total_qty": slade_balance}
    )
