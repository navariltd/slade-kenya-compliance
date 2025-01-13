from hashlib import sha256

import frappe
from frappe.model.document import Document

from ...apis.api_builder import EndpointsBuilder
from ...apis.apis import process_request
from ...doctype.doctype_names_mapping import OPERATION_TYPE_DOCTYPE_NAME
from ...utils import extract_document_series_number

endpoints_builder = EndpointsBuilder()


def on_update(doc: Document, method: str | None = None) -> None:
    save_ledger_details(doc.name)


@frappe.whitelist()
def save_ledger_details(name: str) -> None:
    try:
        doc = frappe.get_doc("Stock Ledger Entry", name)
        company_name = doc.company
        slade_id = doc.custom_slade_id
        if slade_id:
            return
        record = frappe.get_doc(doc.voucher_type, doc.voucher_no)
        item = frappe.get_doc("Item", doc.item_code)
        series_no = extract_document_series_number(record)
        route_key = "StockIOSaveReq"
        if record.branch:
            branch_name = record.branch
        elif record.custom_branch:
            branch_name = record.custom_branch
        else:
            branch_name = frappe.defaults.get_user_default(
                "Branch"
            ) or frappe.get_value("Branch", {}, "name")

        department_name = frappe.defaults.get_user_default(
            "Department"
        ) or frappe.get_value("Department", {}, "name")
        payload = {
            "name": doc.name,
            "document_name": doc.name,
            "branch": frappe.get_value("Branch", branch_name, "slade_id"),
            "organisation": frappe.get_value(
                "Company", company_name, "custom_slade_id"
            ),
            "source_organisation_unit": frappe.get_value(
                "Department", department_name, "custom_slade_id"
            ),
            "document_number": record.name,
            "document_count": series_no,
        }

        document_type_mapping = {
            "Stock Reconciliation": "stock_take",
            "Stock Entry": {
                "Material Receipt": "warehouse_in",
                "Material Transfer": "inventory_operation",
                "Manufacture": "inventory_operation",
                "Send to Subcontractor": "inventory_operation",
                "Material Issue": "inventory_operation",
                "Repack": "inventory_operation",
            },
            "Purchase Receipt": "grn",
            "Purchase Invoice": "purchases_invoice",
            "Delivery Note": "gdn",
            "Sales Invoice": "sales_invoice",
        }

        if doc.voucher_type in document_type_mapping:
            if isinstance(document_type_mapping[doc.voucher_type], dict):
                payload["document_type"] = document_type_mapping[doc.voucher_type].get(
                    record.stock_entry_type, "inventory_operation"
                )
            else:
                payload["document_type"] = document_type_mapping[doc.voucher_type]

        # solve the issue of stock transer later
        if (
            doc.voucher_type == "Stock Entry"
            and record.stock_entry_type == "Material Transfer"
        ):
            route_key = "StockMoveReq"
            return

        if doc.voucher_type == "Stock Reconciliation":
            route_key = "StockMasterSaveReq"
            qty_diff = doc.actual_qty
            if record.purpose == "Opening Stock":
                payload["document_type"] = "warehouse_in"
            elif qty_diff < 0:
                payload["document_type"] = "warehouse_out"
            else:
                payload["document_type"] = "warehouse_in"

        if doc.voucher_type in ("Purchase Receipt", "Purchase Invoice"):
            if record.is_return:
                payload["document_type"] = "return_inwards"
            elif item.get("is_imported_item"):
                payload["document_type"] = "purchases_invoice"

        if doc.voucher_type in ("Delivery Note", "Sales Invoice"):
            if (
                doc.voucher_type == "Sales Invoice"
                and record.custom_successfully_submitted != 1
            ):
                return
            if record.is_return:
                if doc.actual_qty > 0:
                    payload["document_type"] = "return_inwards"
                else:
                    payload["document_type"] = "return_outwards"
            else:
                payload["document_type"] = "sales_invoice"

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
        operation_type = document_to_operation_mapping.get(payload["document_type"])
        operation_type_fields = {
            "operation_type": operation_type,
            "company": doc.company,
        }

        operation_type_fields["source_location"] = (
            doc.custom_source_warehouse or doc.warehouse
        )
        operation_type_fields["destination_location"] = (
            doc.custom_target_warehouse or doc.warehouse
        )
        operation_type_fields["transit_location"] = (
            frappe.get_value(
                "Warehouse",
                {"warehouse_type": "Transit", "company": doc.company},
                "name",
            )
            or doc.warehouse
        )

        matching_operation_type = frappe.db.get_value(
            OPERATION_TYPE_DOCTYPE_NAME, operation_type_fields, ["name", "slade_id"]
        )

        if matching_operation_type:
            matching_operation_name, matching_operation_slade_id = (
                matching_operation_type
            )
        else:
            matching_operation_name, matching_operation_slade_id = None, None

        if not matching_operation_name:
            name_parts = [doc.company]
            if operation_type_fields.get("source_location"):
                name_parts.append(operation_type_fields["source_location"])
            if operation_type_fields.get("destination_location"):
                name_parts.append(operation_type_fields["destination_location"])
            new_operation_type = frappe.get_doc(
                {
                    "doctype": OPERATION_TYPE_DOCTYPE_NAME,
                    "operation_type": operation_type,
                    "company": doc.company,
                    "source_location": operation_type_fields.get("source_location"),
                    "transit_location": operation_type_fields.get("transit_location"),
                    "destination_location": operation_type_fields.get(
                        "destination_location"
                    ),
                    "operation_name": " ".join(name_parts),
                    "active": 1,
                }
            )
            new_operation_type.insert()
            matching_operation_name = new_operation_type.name

        if not matching_operation_slade_id:
            frappe.enqueue(
                "kenya_compliance_via_slade.kenya_compliance_via_slade.apis.apis.save_operation_type",
                name=matching_operation_name,
                on_success=lambda response, **kwargs: stock_operation_type_submit_on_success(
                    response, doc_name=doc.name, **kwargs
                ),
                queue="long",
            )

        else:
            payload["operation_type"] = matching_operation_slade_id
            submit_stock_mvt(payload, route_key)
    except Exception as e:
        frappe.log_error(
            title=f"Error Fetching submitting ledger {name}",
            message=f"Error while submitting: {str(e)}",
        )


def stock_operation_type_submit_on_success(
    response: dict, document_name: str, **kwargs
) -> None:
    frappe.db.set_value(
        OPERATION_TYPE_DOCTYPE_NAME, document_name, {"slade_id": response.get("id")}
    )
    save_ledger_details(kwargs.get("doc_name"))


def submit_stock_mvt(payload: dict, route_key: str, **kwargs) -> None:

    # job_name = sha256(
    #     f"{doc.name}{doc.creation}{doc.modified}".encode(), usedforsecurity=False
    # ).hexdigest()

    frappe.enqueue(
        process_request,
        queue="default",
        doctype="Stock Ledger Entry",
        request_data=payload,
        route_key=route_key,
        handler_function=stock_mvt_submission_on_success,
        request_method="POST",
    )


def stock_mvt_submission_on_success(
    response: dict, document_name: str, **kwargs
) -> None:
    id = response.get("id")
    frappe.db.set_value("Stock Ledger Entry", document_name, {"custom_slade_id": id})
    doc = frappe.get_doc("Stock Ledger Entry", document_name)
    record = frappe.get_doc(doc.voucher_type, doc.voucher_no)
    item = frappe.get_doc("Item", doc.item_code)
    route_key = "StockIOLineReq"
    requset_data = {
        "document_name": document_name,
        "branch": frappe.get_value("Branch", record.branch, "slade_id"),
        "organisation": frappe.get_value("Company", record.company, "custom_slade_id"),
        "source_organisation_unit": frappe.get_value(
            "Department", record.department, "custom_slade_id"
        ),
        "product": item.custom_slade_id,
        "quantity": abs(doc.actual_qty),
        "quantity_confirmed": abs(doc.actual_qty),
        "new_price": (round(int(doc.valuation_rate), 2) if doc.valuation_rate else 0),
    }
    if doc.voucher_type == "Stock Reconciliation":
        route_key = "StockMasterLineReq"

    if (
        doc.voucher_type == "Stock Entry"
        and record.stock_entry_type == "Material Transfer"
    ):
        return

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


def stock_mvt_submit_items_on_success(
    response: dict, document_name: str, **kwargs
) -> None:
    pass
    frappe.db.set_value(
        "Stock Ledger Entry", document_name, {"custom_submitted_successfully": 1}
    )
