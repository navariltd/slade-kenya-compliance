import json
from typing import Callable

import frappe
import frappe.defaults

from ..doctype.doctype_names_mapping import SETTINGS_DOCTYPE_NAME
from ..utils import (
    build_headers,
    get_link_value,
    get_route_path,
    get_server_url,
    get_settings,
    process_dynamic_url,
)
from .api_builder import EndpointsBuilder

endpoints_builder = EndpointsBuilder()
from .remote_response_status_handlers import on_slade_error


def process_request(
    request_data: str | dict,
    route_key: str,
    handler_function: Callable,
    request_method: str = "GET",
    doctype: str = SETTINGS_DOCTYPE_NAME,
) -> str:
    """Reusable function to process requests with common logic."""
    if not frappe.db.exists(SETTINGS_DOCTYPE_NAME, {"is_active": 1}):
        return

    data = parse_request_data(request_data)
    company_name, branch_id, document_name = extract_metadata(data)

    headers = build_headers(company_name, branch_id)
    server_url = get_server_url(company_name, branch_id)
    route_path, _ = get_route_path(route_key, "VSCU Slade 360")
    route_path = process_dynamic_url(route_path, request_data)
    if request_method != "GET":
        settings = get_settings(company_name, branch_id)
        updates = add_organisation_branch_department(settings)
        # data.update(updates)

    if headers and server_url and route_path:
        return execute_request(
            headers,
            server_url,
            route_path,
            data,
            route_key,
            handler_function,
            request_method,
            doctype,
            document_name,
        )
    else:
        return f"Failed to process {route_key}. Missing required configuration."


def add_organisation_branch_department(settings: dict) -> dict:
    organisation = settings.get("company")
    branch = settings.get("bhfid")
    source_organisation = settings.get("department")

    result = {}

    if organisation:
        result["organisation"] = get_link_value(
            "Company", "name", organisation, "custom_slade_id"
        )
    if branch:
        result["branch"] = get_link_value("Branch", "name", branch, "slade_id")
    if source_organisation:
        result["source_organisation_unit"] = get_link_value(
            "Department", "name", source_organisation, "custom_slade_id"
        )

    return result


def parse_request_data(request_data: str | dict) -> dict:
    if isinstance(request_data, str):
        return json.loads(request_data)
    elif isinstance(request_data, (dict, list)):
        return request_data
    return {}


def extract_metadata(data: dict) -> tuple:
    if isinstance(data, list) and data:
        first_entry = data[0]
        company_name = (
            first_entry.get("company_name", None)
            or frappe.defaults.get_user_default("Company")
            or frappe.get_value("Company", {}, "name")
        )
        branch_id = (
            first_entry.get("branch_id", None)
            or frappe.defaults.get_user_default("Branch")
            or frappe.get_value("Branch", "name")
        )
        document_name = first_entry.get("document_name", None)
    else:
        company_name = (
            data.get("company_name", None)
            or frappe.defaults.get_user_default("Company")
            or frappe.get_value("Company", {}, "name")
        )
        branch_id = (
            data.get("branch_id", None)
            or frappe.defaults.get_user_default("Branch")
            or frappe.get_value("Branch", "name")
        )
        document_name = data.get("document_name", None)
    return company_name, branch_id, document_name


def clean_data_for_get_request(data: dict) -> None:
    if "document_name" in data and data["document_name"]:
        data.pop("document_name")
    if "company_name" in data and data["company_name"]:
        data.pop("company_name")


def execute_request(
    headers: dict,
    server_url: str,
    route_path: str,
    data: dict,
    route_key: str,
    handler_function: Callable,
    request_method: str,
    doctype: str,
    document_name: str,
) -> str:
    url = f"{server_url}{route_path}"

    while url:
        endpoints_builder.headers = headers
        endpoints_builder.url = url
        endpoints_builder.payload = data
        endpoints_builder.request_description = route_key
        endpoints_builder.method = request_method
        endpoints_builder.success_callback = handler_function
        endpoints_builder.error_callback = on_slade_error

        response = endpoints_builder.make_remote_call(
            doctype=doctype,
            document_name=document_name,
        )

        if isinstance(response, dict) and "next" in response:
            url = response["next"]
        else:
            url = None

    return f"{route_key} completed successfully."
