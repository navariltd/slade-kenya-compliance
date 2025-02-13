import frappe
import frappe.defaults
from frappe import _
from frappe.model.document import Document

from ...apis.apis import perform_item_registration
from ...doctype.doctype_names_mapping import SETTINGS_DOCTYPE_NAME
from ...utils import generate_custom_item_code_etims


def on_update(doc: Document, method: str = None) -> None:
    """Item doctype before insertion hook"""

    if not frappe.db.exists(SETTINGS_DOCTYPE_NAME, {"is_active": 1}):
        return

    if not doc.custom_sent_to_slade:
        perform_item_registration(doc.name)


def validate(doc: Document, method: str = None) -> None:
    # Check if the tax type field has changed
    if not frappe.db.exists(SETTINGS_DOCTYPE_NAME, {"is_active": 1}):
        return
    is_tax_type_changed = doc.has_value_changed("custom_taxation_type")
    if doc.custom_taxation_type and is_tax_type_changed:
        relevant_tax_templates = frappe.get_all(
            "Item Tax Template",
            ["*"],
            {"custom_etims_taxation_type": doc.custom_taxation_type},
        )

        if relevant_tax_templates:
            doc.set("taxes", [])
            for template in relevant_tax_templates:
                doc.append("taxes", {"item_tax_template": template.name})

    required_fields = [
        doc.custom_etims_country_of_origin_code,
        doc.custom_product_type,
        doc.custom_packaging_unit_code,
        doc.custom_unit_of_quantity_code,
        doc.custom_item_classification,
    ]

    if any(not field for field in required_fields):
        return

    if not doc.custom_item_code_etims:
        doc.custom_item_code_etims = generate_custom_item_code_etims(doc)


@frappe.whitelist()
def prevent_item_deletion(doc: dict) -> None:
    if not frappe.db.exists(SETTINGS_DOCTYPE_NAME, {"is_active": 1}):
        return
    if doc.custom_item_registered == 1:  # Assuming 1 means registered, adjust as needed
        frappe.throw(_("Cannot delete registered items"))
    pass
