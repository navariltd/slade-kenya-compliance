# Copyright (c) 2025, Navari Ltd and contributors
# For license information, please see license.txt

from typing import Any, Dict, List, Optional, Tuple

from pypika.functions import Avg, Max, Min

import frappe
from frappe.query_builder import DocType


def execute(
    filters: Optional[Dict[str, Any]] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    if filters is None:
        filters = {}

    columns = [
        {
            "fieldname": "doctype",
            "label": "Document Type",
            "fieldtype": "Data",
            "width": 300,
        },
        {
            "fieldname": "avg_time",
            "label": "Average Time (Seconds)",
            "fieldtype": "Float",
            "width": 300,
        },
        {
            "fieldname": "min_time",
            "label": "Min Time (Seconds)",
            "fieldtype": "Float",
            "width": 300,
        },
        {
            "fieldname": "max_time",
            "label": "Max Time (Seconds)",
            "fieldtype": "Float",
            "width": 300,
        },
    ]

    tracked_docs = {
        "Item": DocType("Item"),
        "Invoice": DocType("Sales Invoice"),
        "Credit Note": DocType("Sales Invoice"),
        "Purchase Invoice": DocType("Purchase Invoice"),
        "Stock Ledger Entry": DocType("Stock Ledger Entry"),
    }

    from_date = filters.get("from_date")
    to_date = filters.get("to_date")

    data = []

    for doc_name, doctype in tracked_docs.items():
        meta = frappe.get_meta(
            "Sales Invoice" if doc_name in ["Invoice", "Credit Note"] else doc_name
        )
        has_fields = {
            "custom_slade_id": meta.has_field("custom_slade_id"),
            "custom_successfully_submitted": meta.has_field(
                "custom_successfully_submitted"
            ),
            "custom_submitted_successfully": meta.has_field(
                "custom_submitted_successfully"
            ),
            "custom_sent_to_slade": meta.has_field("custom_sent_to_slade"),
        }

        completion_conditions = []
        if has_fields["custom_sent_to_slade"]:
            completion_conditions.append(doctype.custom_sent_to_slade)
        if has_fields["custom_successfully_submitted"]:
            completion_conditions.append(doctype.custom_successfully_submitted)
        if has_fields["custom_submitted_successfully"]:
            completion_conditions.append(doctype.custom_submitted_successfully)

        completion_condition = None
        if completion_conditions:
            completion_condition = completion_conditions[0]
            for cond in completion_conditions[1:]:
                completion_condition |= cond

        query = (
            frappe.qb.from_(doctype).select(
                Avg(doctype.modified - doctype.creation).as_("avg_time"),
                Min(doctype.modified - doctype.creation).as_("min_time"),
                Max(doctype.modified - doctype.creation).as_("max_time"),
            )
            # Exclude records where submission takes longer than 300 seconds
            # to prevent skewed data due to retries or delayed background jobs
            .where((doctype.modified - doctype.creation) <= 300)
        )

        if from_date:
            query = query.where(doctype.creation >= from_date)
        if to_date:
            query = query.where(doctype.creation <= to_date)

        if doc_name == "Invoice":
            query = query.where(doctype.is_return == 0)
        elif doc_name == "Credit Note":
            query = query.where(doctype.is_return == 1)

        if completion_condition:
            query = query.where(completion_condition)

        try:
            row = query.run(as_dict=True)[0]
            row["doctype"] = doc_name
            data.append(row)
        except Exception as e:
            frappe.log_error(f"Error fetching data for {doc_name}: {str(e)}")

    return columns, data
