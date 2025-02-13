import frappe
from frappe.model.document import Document

from erpnext.controllers.taxes_and_totals import get_itemised_tax_breakup_data

from ...apis.api_builder import EndpointsBuilder
from ...apis.process_request import process_request
from ...apis.remote_response_status_handlers import (
    purchase_invoice_submission_on_success,
)
from ...doctype.doctype_names_mapping import SETTINGS_DOCTYPE_NAME
from ...utils import get_taxation_types

endpoints_builder = EndpointsBuilder()


def validate(doc: Document, method: str = None) -> None:
    if not frappe.db.exists(SETTINGS_DOCTYPE_NAME, {"is_active": 1}):
        return
    get_itemised_tax_breakup_data(doc)
    if not doc.taxes:
        vat_acct = frappe.get_value(
            "Account", {"account_type": "Tax", "tax_rate": "16"}, ["name"], as_dict=True
        )
        doc.set(
            "taxes",
            [
                {
                    "account_head": vat_acct.name,
                    "included_in_print_rate": 1,
                    "description": vat_acct.name.split("-", 1)[0].strip(),
                    "category": "Total",
                    "add_deduct_tax": "Add",
                    "charge_type": "On Net Total",
                }
            ],
        )


def on_submit(doc: Document, method: str = None) -> None:
    submit_purchase_invoice(doc)


def submit_purchase_invoice(doc: Document) -> None:
    if doc.is_return == 0 and doc.update_stock == 1:
        # TODO: Handle cases when item tax templates have not been picked

        if not frappe.db.exists(SETTINGS_DOCTYPE_NAME, {"is_active": 1}):
            return

        company_name = (
            doc.company
            or frappe.defaults.get_user_default("Company")
            or frappe.get_value("Company", {}, "name")
        )
        payload = build_purchase_invoice_payload(doc, company_name)
        process_request(
            payload,
            "TrnsPurchaseSaveReq",
            purchase_invoice_submission_on_success,
            request_method="POST",
            doctype="Purchase Invoice",
        )


@frappe.whitelist()
def send_purchase_details(name: str) -> None:
    doc = frappe.get_doc("Purchase Invoice", name)
    submit_purchase_invoice(doc)


def build_purchase_invoice_payload(doc: Document, company_name: str) -> dict:
    taxation_type = get_taxation_types(doc)
    payload = {
        "document_name": doc.name,
        "company_name": company_name,
        "can_send_to_etims": True,
        "paid_invoice_amount": round(doc.grand_total - doc.outstanding_amount, 2),
        "total_amount": round(doc.grand_total, 2),
        "taxable_rate_A": taxation_type.get("A", {}).get("tax_rate", 0),
        "taxable_rate_B": taxation_type.get("B", {}).get("tax_rate", 0),
        "taxable_rate_C": taxation_type.get("C", {}).get("tax_rate", 0),
        "taxable_rate_D": taxation_type.get("D", {}).get("tax_rate", 0),
        "total_taxable_amount": round(doc.base_total, 2),
        "total_tax_amount": round(doc.total_taxes_and_charges, 2),
        "supplier_name": doc.supplier_name,
    }

    return payload
