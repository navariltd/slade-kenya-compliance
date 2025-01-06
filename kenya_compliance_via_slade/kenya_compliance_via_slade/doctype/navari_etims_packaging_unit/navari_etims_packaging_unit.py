# Copyright (c) 2024, Navari Ltd and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class NavarieTimsPackagingUnit(Document):
    def before_insert(self) -> None:
        if not self.code_description and self.code:
            self.code_description = self.code
        if not self.code_name and self.code:
            self.code_name = self.code
