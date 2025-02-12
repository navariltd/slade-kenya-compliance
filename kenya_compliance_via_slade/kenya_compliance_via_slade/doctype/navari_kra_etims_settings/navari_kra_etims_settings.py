from typing import Optional

import frappe
import frappe.defaults
from frappe.model.document import Document

from ...background_tasks.tasks import (
    refresh_notices,
    search_organisations_request,
    send_purchase_information,
    send_sales_invoices_information,
    send_stock_information,
)
from ...utils import user_details_fetch


class NavariKRAeTimsSettings(Document):
    """ETims Integration Settings doctype"""

    def after_insert(self) -> None:
        if self.is_active == 1:
            request_data = {
                "branch_id": self.bhfid,
                "company_name": self.company,
                "document_name": self.name,
            }
            search_organisations_request(request_data)
            user_details_fetch(self.name)

    def validate(self) -> None:
        if self.is_active == 1:
            existing_doc: Optional[str] = frappe.db.exists(
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

    def on_update(self) -> None:
        def get_or_create_scheduled_job(
            method_name: str, frequency: str, cron_format: Optional[str] = None
        ) -> None:
            task: Optional[str] = frappe.db.exists(
                "Scheduled Job Type", {"method": ["like", f"%{method_name}%"]}
            )

            if task:
                task = frappe.get_doc("Scheduled Job Type", task)
            else:
                task = frappe.new_doc("Scheduled Job Type")
                task.method = method_name

            task.frequency = frequency

            if frequency == "Cron" and cron_format:
                task.cron_format = cron_format

            task.save(ignore_permissions=True)

        if self.sales_information_submission:
            get_or_create_scheduled_job(
                f"{send_sales_invoices_information.__module__}.{send_sales_invoices_information.__name__}",
                self.sales_information_submission,
                (
                    self.sales_info_cron_format
                    if self.sales_information_submission == "Cron"
                    else None
                ),
            )

        if self.stock_information_submission:
            get_or_create_scheduled_job(
                f"{send_stock_information.__module__}.{send_stock_information.__name__}",
                self.stock_information_submission,
                (
                    self.stock_info_cron_format
                    if self.stock_information_submission == "Cron"
                    else None
                ),
            )

        if self.purchase_information_submission:
            get_or_create_scheduled_job(
                f"{send_purchase_information.__module__}.{send_purchase_information.__name__}",
                self.purchase_information_submission,
                (
                    self.purchase_info_cron_format
                    if self.purchase_information_submission == "Cron"
                    else None
                ),
            )

        if self.notices_refresh_frequency:
            get_or_create_scheduled_job(
                f"{refresh_notices.__module__}.{refresh_notices.__name__}",
                self.notices_refresh_frequency,
                (
                    self.notices_refresh_freq_cron_format
                    if self.notices_refresh_frequency == "Cron"
                    else None
                ),
            )
