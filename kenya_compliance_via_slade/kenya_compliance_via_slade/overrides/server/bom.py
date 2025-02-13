import frappe
import frappe.defaults
from frappe.model.document import Document

from ...apis.apis import submit_item_composition
from ...doctype.doctype_names_mapping import SETTINGS_DOCTYPE_NAME


def on_submit(doc: Document, method: str = None) -> None:
    """Item doctype before insertion hook"""

    if not frappe.db.exists(SETTINGS_DOCTYPE_NAME, {"is_active": 1}):
        return

    submit_item_composition(doc.name)
