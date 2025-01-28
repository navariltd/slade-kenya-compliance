import deprecation

import frappe
import frappe.defaults
from frappe import _
from frappe.model.document import Document

from .... import __version__
from ...apis.apis import perform_item_registration
from ...doctype.doctype_names_mapping import SETTINGS_DOCTYPE_NAME


@deprecation.deprecated(
    deprecated_in="0.6.2",
    removed_in="1.0.0",
    current_version=__version__,
    details="Use the Register Item button in Item record",
)
def after_insert(doc: Document, method: str) -> None:
    """Item doctype before insertion hook"""

    if not frappe.db.exists(SETTINGS_DOCTYPE_NAME, {"is_active": 1}):
        return

    perform_item_registration(doc.name)


def validate(doc: Document, method: str) -> None:
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

    new_prefix = f"{doc.custom_etims_country_of_origin_code}{doc.custom_product_type}{doc.custom_packaging_unit_code}{doc.custom_unit_of_quantity_code}"

    # Check if custom_item_code_etims exists and extract its suffix if so
    if doc.custom_item_code_etims:
        # Extract the last 7 digits as the suffix
        existing_suffix = doc.custom_item_code_etims[-7:]
    else:
        # If there is no existing code, generate a new suffix
        last_code = frappe.db.sql(
            """
            SELECT custom_item_code_etims
            FROM `tabItem`
            WHERE custom_item_classification = %s
            ORDER BY CAST(SUBSTRING(custom_item_code_etims, -7) AS UNSIGNED) DESC
            LIMIT 1
            """,
            (doc.custom_item_classification,),
        )
        last_code = last_code[0][0] if last_code else None
        if last_code:
            last_suffix = int(last_code[-7:])
            existing_suffix = str(last_suffix + 1).zfill(7)
        else:
            # Start from '0000001' if no matching classification item exists
            existing_suffix = "0000001"

    # Combine the new prefix with the existing or new suffix
    doc.custom_item_code_etims = f"{new_prefix}{existing_suffix}"
    if not doc.custom_sent_to_slade:
        perform_item_registration(doc.name)


@frappe.whitelist()
def prevent_item_deletion(doc: dict) -> None:
    if not frappe.db.exists(SETTINGS_DOCTYPE_NAME, {"is_active": 1}):
        return
    if doc.custom_item_registered == 1:  # Assuming 1 means registered, adjust as needed
        frappe.throw(_("Cannot delete registered items"))
    pass
