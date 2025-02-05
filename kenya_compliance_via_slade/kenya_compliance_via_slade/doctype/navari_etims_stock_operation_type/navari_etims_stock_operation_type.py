# Copyright (c) 2025, Navari Ltd and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

from ...apis.apis import save_operation_type


class NavarieTimsStockOperationType(Document):
    def on_update(self) -> None:
        if not self.slade_id:
            save_operation_type(self.name)
