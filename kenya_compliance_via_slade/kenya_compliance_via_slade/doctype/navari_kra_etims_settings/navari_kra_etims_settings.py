# Copyright (c) 2024, Navari Ltd and contributors
# For license information, please see license.txt

import frappe
import frappe.defaults
from frappe.model.document import Document


class NavariKRAeTimsSettings(Document):
    """ETims Integration Settings doctype"""
    def validate(self):
        if self.is_active == 1:
            print(self)
            existing_doc = frappe.db.exists(
                "Navari Slade360 eTims Settings",
                {
                    "bhfid": self.bhfid,
                    "company": self.company,
                    "is_active": 1,
                    "name": ("!=", self.name),
                },
            )

            if existing_doc:
                frappe.throw(
                    f"Only one active setting is allowed for bhfid '{self.bhfid}' and company '{self.company}'."
                )

