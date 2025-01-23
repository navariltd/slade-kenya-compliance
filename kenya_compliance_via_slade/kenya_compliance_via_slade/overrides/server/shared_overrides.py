from typing import Literal

import frappe
from frappe.model.document import Document

from ...apis.api_builder import EndpointsBuilder
from ...apis.process_request import process_request
from ...apis.remote_response_status_handlers import (
    sales_information_submission_on_success,
)
from ...doctype.doctype_names_mapping import SETTINGS_DOCTYPE_NAME
from ...utils import build_invoice_payload

endpoints_builder = EndpointsBuilder()


def generic_invoices_on_submit_override(
    doc: Document, invoice_type: Literal["Sales Invoice", "POS Invoice"]
) -> None:
    """Defines a function to handle sending of Sales information from relevant invoice documents

    Args:
        doc (Document): The doctype object or record
        invoice_type (Literal[&quot;Sales Invoice&quot;, &quot;POS Invoice&quot;]):
        The Type of the invoice. Either Sales, or POS
    """

    if not frappe.db.exists(SETTINGS_DOCTYPE_NAME, {"is_active": 1}):
        return

    company_name = (
        doc.company
        or frappe.defaults.get_user_default("Company")
        or frappe.get_value("Company", {}, "name")
    )

    invoice_identifier = "C" if doc.is_return else "S"
    payload = build_invoice_payload(doc, invoice_identifier, company_name)
    additional_context = {
        "invoice_type": invoice_type,
    }
    process_request(
        payload,
        "TrnsSalesSaveWrReq",
        lambda response, **kwargs: sales_information_submission_on_success(
            response=response,
            **additional_context,
            **kwargs,
        ),
        request_method="POST",
        doctype=invoice_type,
    )


def validate(doc: Document, method: str) -> None:
    pass
    # vendor = ""
    # doc.custom_scu_id = get_curr_env_etims_settings(
    #     frappe.defaults.get_user_default("Company"), vendor, doc.branch
    # ).scu_id

    # item_taxes = get_itemised_tax_breakup_data(doc)

    # taxes_breakdown = defaultdict(list)
    # taxable_breakdown = defaultdict(list)
    # tax_head = doc.taxes[0].description

    # for index, item in enumerate(doc.items):
    #     taxes_breakdown[item.custom_taxation_type_code].append(
    #         item_taxes[index][tax_head]["tax_amount"]
    #     )
    #     taxable_breakdown[item.custom_taxation_type_code].append(
    #         item_taxes[index]["taxable_amount"]
    #     )

    # update_tax_breakdowns(doc, (taxes_breakdown, taxable_breakdown))


# def update_tax_breakdowns(invoice: Document, mapping: tuple) -> None:
#     invoice.custom_tax_a = round(sum(mapping[0]["A"]), 2)
#     invoice.custom_tax_b = round(sum(mapping[0]["B"]), 2)
#     invoice.custom_tax_c = round(sum(mapping[0]["C"]), 2)
#     invoice.custom_tax_d = round(sum(mapping[0]["D"]), 2)
#     invoice.custom_tax_e = round(sum(mapping[0]["E"]), 2)

#     invoice.custom_taxbl_amount_a = round(sum(mapping[1]["A"]), 2)
#     invoice.custom_taxbl_amount_b = round(sum(mapping[1]["B"]), 2)
#     invoice.custom_taxbl_amount_c = round(sum(mapping[1]["C"]), 2)
#     invoice.custom_taxbl_amount_d = round(sum(mapping[1]["D"]), 2)
#     invoice.custom_taxbl_amount_e = round(sum(mapping[1]["E"]), 2)
