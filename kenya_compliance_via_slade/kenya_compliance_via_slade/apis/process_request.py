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
    parse_request_data,
    process_dynamic_url,
)
from .api_builder import EndpointsBuilder

endpoints_builder = EndpointsBuilder()


def process_request(
    request_data: str | dict,
    route_key: str,
    handler_function: Callable,
    request_method: str = "GET",
    doctype: str = SETTINGS_DOCTYPE_NAME,
    error_callback: Callable = None,
) -> str:
    """Reusable function to process requests with common logic."""
    if not frappe.db.exists(SETTINGS_DOCTYPE_NAME, {"is_active": 1}):
        return

    data = parse_request_data(request_data)
    company_name, branch_id, document_name = extract_metadata(data)

    headers = build_headers(company_name, branch_id)

    server_url = get_server_url(company_name, branch_id)
    route_path, _ = get_route_path(route_key, "VSCU Slade 360")
    dynamic_route_path = process_dynamic_url(route_path, request_data)
    url = f"{server_url}{dynamic_route_path}"
    if request_method != "GET":
        settings = get_settings(company_name, branch_id)
        updates = add_organisation_branch_department(settings)
        # data.update(updates)

    if headers and server_url and route_path:
        return execute_request(
            headers,
            url,
            route_path,
            data,
            route_key,
            handler_function,
            request_method,
            doctype,
            document_name,
            error_callback,
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
            data.pop("company_name", None)
            or frappe.defaults.get_user_default("Company")
            or frappe.get_value("Company", {}, "name")
        )
        branch_id = (
            data.pop("branch_id", None)
            or frappe.defaults.get_user_default("Branch")
            or frappe.get_value("Branch", "name")
        )
        document_name = data.pop("document_name", None)
    return company_name, branch_id, document_name


def clean_data_for_get_request(data: dict) -> None:
    if "document_name" in data and data["document_name"]:
        data.pop("document_name")
    if "company_name" in data and data["company_name"]:
        data.pop("company_name")


def execute_request(
    headers: dict,
    url: str,
    route_path: str,
    data: dict,
    route_key: str,
    handler_function: Callable,
    request_method: str,
    doctype: str,
    document_name: str,
    error_callback: Callable = None,
) -> str:

    # Clean data for GET request
    if request_method == "GET":
        clean_data_for_get_request(data)

    while url:
        endpoints_builder.headers = headers
        endpoints_builder.url = url
        endpoints_builder.route_path = route_path
        endpoints_builder.payload = data
        endpoints_builder.request_description = route_key
        endpoints_builder.method = request_method
        endpoints_builder.success_callback = handler_function
        endpoints_builder.error_callback = error_callback

        response = endpoints_builder.make_remote_call(
            doctype=doctype,
            document_name=document_name,
        )

        if isinstance(response, dict) and "next" in response:
            url = response["next"]
        else:
            url = None

    return f"{route_key} completed successfully."
