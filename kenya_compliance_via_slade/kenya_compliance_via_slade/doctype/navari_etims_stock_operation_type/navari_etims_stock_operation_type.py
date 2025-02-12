# Copyright (c) 2025, Navari Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from ...apis.apis import save_operation_type


class NavarieTimsStockOperationType(Document):
    def on_update(self) -> None:
        if not self.slade_id:
            save_operation_type(self.name)

    def validate(self) -> None:
        if not self.slade_id and self.warehouse:
            warehouse = frappe.get_doc("Warehouse", self.warehouse)
            if self.operation_type == "incoming":
                self.source_location = warehouse.custom_slade_supplier_warehouse
                self.destination_location = warehouse.custom_slade_id
            elif self.operation_type == "outgoing":
                self.source_location = warehouse.custom_slade_id
                self.destination_location = warehouse.custom_slade_customer_warehouse
