# Copyright (c) 2025, Navari Ltd and contributors
# For license information, please see license.txt

from typing import Any, Dict, List, Optional, Tuple

from pypika.functions import Count, Sum
from pypika.terms import Case

import frappe
from frappe.query_builder import DocType


def execute(
    filters: Optional[Dict[str, Any]] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:

    columns = [
        {
            "fieldname": "integration_request_service",
            "label": "Service",
            "fieldtype": "Data",
            "width": 400,
        },
        {"fieldname": "queued", "label": "Queued", "fieldtype": "Int", "width": 150},
        {
            "fieldname": "completed",
            "label": "Completed",
            "fieldtype": "Int",
            "width": 150,
        },
        {
            "fieldname": "cancelled",
            "label": "Cancelled",
            "fieldtype": "Int",
            "width": 150,
        },
        {"fieldname": "failed", "label": "Failed", "fieldtype": "Int", "width": 150},
        {"fieldname": "total", "label": "Total", "fieldtype": "Int", "width": 150},
    ]

    IntegrationRequest = DocType("Integration Request")

    query = (
        frappe.qb.from_(IntegrationRequest)
        .select(
            IntegrationRequest.integration_request_service,
            Sum(Case().when(IntegrationRequest.status == "Queued", 1).else_(0)).as_(
                "queued"
            ),
            Sum(Case().when(IntegrationRequest.status == "Completed", 1).else_(0)).as_(
                "completed"
            ),
            Sum(Case().when(IntegrationRequest.status == "Cancelled", 1).else_(0)).as_(
                "cancelled"
            ),
            Sum(Case().when(IntegrationRequest.status == "Failed", 1).else_(0)).as_(
                "failed"
            ),
            Count("*").as_("total"),
        )
        .groupby(IntegrationRequest.integration_request_service)
        .orderby(IntegrationRequest.integration_request_service)
    )

    if filters.get("from_date"):
        query = query.where(IntegrationRequest.creation >= filters["from_date"])
    if filters.get("to_date"):
        query = query.where(IntegrationRequest.creation <= filters["to_date"])

    if filters.get("integration_request_service"):
        selected_services = filters["integration_request_service"]
        if isinstance(selected_services, str):
            selected_services = selected_services.split(",")
        query = query.where(
            IntegrationRequest.integration_request_service.isin(selected_services)
        )

    data = query.run(as_dict=True)

    return columns, data
