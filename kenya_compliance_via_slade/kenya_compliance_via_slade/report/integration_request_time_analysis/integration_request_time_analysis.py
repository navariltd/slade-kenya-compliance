# Copyright (c) 2025, Navari Ltd and contributors
# For license information, please see license.txt

from typing import Any, Dict, List, Optional, Tuple

from pypika.functions import Avg, Max, Min

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
            "width": 450,
        },
        {
            "fieldname": "avg_time",
            "label": "Average Time (Seconds)",
            "fieldtype": "Float",
            "width": 250,
        },
        {
            "fieldname": "min_time",
            "label": "Min Time (Seconds)",
            "fieldtype": "Float",
            "width": 250,
        },
        {
            "fieldname": "max_time",
            "label": "Max Time (Seconds)",
            "fieldtype": "Float",
            "width": 250,
        },
    ]

    IntegrationRequest = DocType("Integration Request")
    Version = DocType("Version")

    # Subquery to get the first `modified` time when `status` changes
    first_status_change_query = (
        frappe.qb.from_(Version)
        .select(
            Version.ref_doctype,
            Version.docname,
            Min(Version.modified).as_("first_modified"),
        )
        .where(
            (Version.ref_doctype == "Integration Request")
            & (Version.data.like('%"status"%'))
        )
        .groupby(Version.ref_doctype, Version.docname)
    ).as_("status_change_times")

    # Main query to compute avg, min, and max times based on the first status change
    query = (
        frappe.qb.from_(IntegrationRequest)
        .join(first_status_change_query)
        .on(IntegrationRequest.name == first_status_change_query.docname)
        .select(
            IntegrationRequest.integration_request_service,
            Avg(
                first_status_change_query.first_modified - IntegrationRequest.creation
            ).as_("avg_time"),
            Min(
                first_status_change_query.first_modified - IntegrationRequest.creation
            ).as_("min_time"),
            Max(
                first_status_change_query.first_modified - IntegrationRequest.creation
            ).as_("max_time"),
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
