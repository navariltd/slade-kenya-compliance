"""Utility functions"""

import re
from base64 import b64encode
from datetime import datetime, timedelta
from decimal import ROUND_DOWN, Decimal
from io import BytesIO
from typing import Literal
from urllib.parse import urlencode

import aiohttp
import qrcode
import requests
from aiohttp import ClientTimeout

import frappe
from frappe.model.document import Document

from .doctype.doctype_names_mapping import (
    ENVIRONMENT_SPECIFICATION_DOCTYPE_NAME,
    PAYMENT_TYPE_DOCTYPE_NAME,
    ROUTES_TABLE_CHILD_DOCTYPE_NAME,
    ROUTES_TABLE_DOCTYPE_NAME,
    SETTINGS_DOCTYPE_NAME,
)
from .logger import etims_logger


def is_valid_kra_pin(pin: str) -> bool:
    """Checks if the string provided conforms to the pattern of a KRA PIN.
    This function does not validate if the PIN actually exists, only that
    it resembles a valid KRA PIN.

    Args:
        pin (str): The KRA PIN to test

    Returns:
        bool: True if input is a valid KRA PIN, False otherwise
    """
    pattern = r"^[a-zA-Z]{1}[0-9]{9}[a-zA-Z]{1}$"
    return bool(re.match(pattern, pin))


async def make_get_request(url: str) -> dict[str, str] | str:
    """Make an Asynchronous GET Request to specified URL

    Args:
        url (str): The URL

    Returns:
        dict: The Response
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.content_type.startswith("text"):
                return await response.text()

            return await response.json()


async def make_post_request(
    url: str,
    data: dict[str, str] | None = None,
    headers: dict[str, str | int] | None = None,
) -> dict[str, str | dict]:
    """Make an Asynchronous POST Request to specified URL

    Args:
        url (str): The URL
        data (dict[str, str] | None, optional): Data to send to server. Defaults to None.
        headers (dict[str, str | int] | None, optional): Headers to set. Defaults to None.

    Returns:
        dict: The Server Response
    """
    # TODO: Refactor to a more efficient handling of creation of the session object
    # as described in documentation
    async with aiohttp.ClientSession(timeout=ClientTimeout(1800)) as session:
        # Timeout of 1800 or 30 mins, especially for fetching Item classification
        async with session.post(url, json=data, headers=headers) as response:
            return await response.json()


def build_datetime_from_string(
    date_string: str, format: str = "%Y-%m-%d %H:%M:%S"
) -> datetime:
    """Builds a Datetime object from string, and format provided

    Args:
        date_string (str): The string to build object from
        format (str, optional): The format of the date_string string. Defaults to "%Y-%m-%d".

    Returns:
        datetime: The datetime object
    """
    date_object = datetime.strptime(date_string, format)

    return date_object


def is_valid_url(url: str) -> bool:
    """Validates input is a valid URL

    Args:
        input (str): The input to validate

    Returns:
        bool: Validation result
    """
    pattern = r"^(https?|ftp):\/\/[^\s/$.?#].[^\s]*"
    return bool(re.match(pattern, url))


# def get_route_path(
#     search_field: str,
#     vendor: str,
#     routes_table_doctype: str = ROUTES_TABLE_CHILD_DOCTYPE_NAME,
# ) -> tuple[str, str] | None:

#     query = f"""
#     SELECT
#         url_path,
#         last_request_date
#     FROM `tab{routes_table_doctype}`
#     WHERE url_path_function LIKE '{search_field}'
#     AND parent LIKE '{ROUTES_TABLE_DOCTYPE_NAME}'
#     LIMIT 1
#     """

#     results = frappe.db.sql(query, as_dict=True)


#     if results:
#         return (results[0].url_path, results[0].last_request_date)
def get_route_path(
    search_field: str,
    vendor: str = "OSCU KRA",
    routes_table_doctype: str = ROUTES_TABLE_CHILD_DOCTYPE_NAME,
    parent_doctype: str = ROUTES_TABLE_DOCTYPE_NAME,
) -> tuple[str, str] | None:

    query = f"""
    SELECT
        child.url_path,
        child.last_request_date
    FROM `tab{routes_table_doctype}` AS child
    JOIN `tab{parent_doctype}` AS parent
    ON child.parent = parent.name
    WHERE child.url_path_function LIKE '{search_field}'
    AND parent.vendor LIKE '{vendor}'
    LIMIT 1
    """

    results = frappe.db.sql(query, as_dict=True)

    if results:
        return (results[0]["url_path"], results[0]["last_request_date"])

    return None


def get_environment_settings(
    company_name: str,
    vendor: str,
    doctype: str = SETTINGS_DOCTYPE_NAME,
    environment: str = "Sandbox",
    branch_id: str = "00",
) -> Document | None:
    error_message = None
    query = f"""
    SELECT server_url,
        name,
        vendor,
        tin,
        dvcsrlno,
        bhfid,
        company,
        communication_key,
        sales_control_unit_id as scu_id
    FROM `tab{doctype}`
    WHERE company = '{company_name}'
        AND env = '{environment}'
        AND vendor = '{vendor}'
        AND name IN (
            SELECT name
            FROM `tab{doctype}`
            WHERE is_active = 1
        )
    """

    if branch_id:
        query += f"AND bhfid = '{branch_id}';"
    setting_doctype = frappe.db.sql(query, as_dict=True)
    if setting_doctype:
        return setting_doctype[0]

    error_message = f"""
        There is no valid environment setting for these credentials:
            <ul>
                <li>Company: <b>{company_name}</b></li>
                <li>Branch ID: <b>{branch_id}</b></li>
                <li>Environment: <b>{environment}</b></li>
            </ul>
        Please ensure a valid <a href="/app/navari-kra-etims-settings">eTims Integration Setting</a> record exists
    """

    etims_logger.error(error_message)
    frappe.log_error(
        title="Incorrect Setup", message=error_message, reference_doctype=doctype
    )
    frappe.throw(error_message, title="Incorrect Setup")


def get_current_environment_state(
    environment_identifier_doctype: str = ENVIRONMENT_SPECIFICATION_DOCTYPE_NAME,
) -> str:
    """Fetches the Environment Identifier from the relevant doctype.

    Args:
        environment_identifier_doctype (str, optional): The doctype containing environment information. Defaults to ENVIRONMENT_SPECIFICATION_DOCTYPE_NAME.

    Returns:
        str: The environment identifier. Either "Sandbox", or "Production"
    """
    environment = frappe.db.get_single_value(
        environment_identifier_doctype, "environment"
    )

    return environment


def get_server_url(company_name: str, branch_id: str = "00") -> str | None:
    settings = frappe.db.get_value(
        SETTINGS_DOCTYPE_NAME,
        {"bhfid": branch_id, "company": company_name, "is_active": 1},
        ["server_url"],
        as_dict=True,
    ) or frappe.db.get_value(
        SETTINGS_DOCTYPE_NAME,
        {"company": company_name, "is_active": 1},
        ["server_url"],
        as_dict=True,
    )

    if settings:
        server_url = settings.get("server_url")

        return server_url

    return


def build_headers(company_name: str, branch_id: str = "00") -> dict[str, str] | None:
    """
    Build headers for Slade360 API requests.
    Checks for token validity and refreshes the token if expired.

    Args:
        company_name (str): The name of the company.
        branch_id (str, optional): The branch ID. Defaults to "00".

    Returns:
        dict[str, str] | None: The headers including the refreshed token or None if failed.
    """
    settings = frappe.db.get_value(
        SETTINGS_DOCTYPE_NAME,
        {"bhfid": branch_id, "company": company_name, "is_active": 1},
        ["access_token", "token_expiry", "name"],
        as_dict=True,
    ) or frappe.db.get_value(
        SETTINGS_DOCTYPE_NAME,
        {"company": company_name, "is_active": 1},
        ["access_token", "token_expiry", "name"],
        as_dict=True,
    )

    if settings:
        access_token = settings.get("access_token")
        token_expiry = settings.get("token_expiry")

        if not access_token or not token_expiry:
            return None

        if (
            datetime.strptime(str(token_expiry).split(".")[0], "%Y-%m-%d %H:%M:%S")
            < datetime.now()
        ):
            new_settings = update_navari_settings_with_token(settings.get("name"))

            if not new_settings:
                frappe.throw(
                    "Failed to refresh token. Please check your Slade360 integration settings.",
                    frappe.AuthenticationError,
                )

            access_token = new_settings.access_token

        logged_user = frappe.session.user
        user_data = frappe.db.get_value(
            "Navari eTims User",
            {"system_user": logged_user},
            ["workstation"],
            as_dict=True,
        )

        workstation = user_data.get("workstation") if user_data else None

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        if workstation:
            headers["X-Workstation"] = workstation
        else:
            headers["X-Workstation"] = "731ddef2-9011-4fbe-8f15-af86a81e9bd7"

        return headers

    return None


def get_branch_id(company_name: str, vendor: str) -> str | None:
    settings = get_curr_env_etims_settings(company_name, vendor)

    if settings:
        return settings.bhfid

    return None


def extract_document_series_number(document: Document) -> int | None:
    split_invoice_name = document.name.split("-")

    if len(split_invoice_name) == 4:
        return int(split_invoice_name[-1])

    if len(split_invoice_name) == 5:
        return int(split_invoice_name[-2])


def build_invoice_payload(
    invoice: Document, invoice_type_identifier: Literal["S", "C"], company_name: str
) -> dict[str, str | int | float]:
    # Retrieve taxation data for the invoice
    get_taxation_types(invoice)
    # frappe.throw(str(taxation_type))
    """Converts relevant invoice data to a JSON payload

    Args:
        invoice (Document): The Invoice record to generate data from
        invoice_type_identifier (Literal["S", "C"]): The
        Invoice type identifier. S for Sales Invoice, C for Credit Notes
        company_name (str): The company name used to fetch the valid settings doctype record

    Returns:
        dict[str, str | int | float]: The payload
    """
    invoice_name = invoice.name
    if invoice.amended_from:
        invoice_name = clean_invc_no(invoice_name)

    payload = {
        # "made_by": invoice.owner,
        "document_name": invoice.name,
        "branch_id": invoice.branch,
        "company_name": company_name,
        "description": invoice.remarks or "New",
        "payment_method": frappe.get_value(
            PAYMENT_TYPE_DOCTYPE_NAME, invoice.custom_payment_type, "slade_id"
        ),
        "customer": frappe.get_value("Customer", invoice.customer, "slade_id"),
        "invoice_date": str(invoice.posting_date),
        "currency": frappe.get_value("Currency", invoice.currency, "custom_slade_id"),
        "source_organisation_unit": frappe.get_value(
            "Department", invoice.department, "custom_slade_id"
        )
        or "4f2ede94-cb03-4532-9c38-a455470cfe0e",
        "branch": frappe.get_value("Branch", invoice.branch, "slade_id"),
        "organisation": frappe.get_value("Company", invoice.company, "custom_slade_id"),
        "sales_type": "cash",
    }

    return payload


def get_invoice_items_list(invoice: Document) -> list[dict[str, str | int | None]]:
    """Iterates over the invoice items and extracts relevant data

    Args:
        invoice (Document): The invoice

    Returns:
        list[dict[str, str | int | None]]: The parsed data as a list of dictionaries
    """
    # FIXME: Handle cases where same item can appear on different lines with different rates etc.
    # item_taxes = get_itemised_tax_breakup_data(invoice)
    items_list = []

    for index, item in enumerate(invoice.items):
        # taxable_amount = round(int(item_taxes[index]["taxable_amount"]), 2)
        # actual_tax_amount = 0
        # tax_head = invoice.taxes[0].description  # Fetch tax head from taxes table

        # actual_tax_amount = item_taxes[index][tax_head]["tax_amount"]

        # tax_amount = round(actual_tax_amount, 2)

        items_list.append(
            {
                "product": item.item_code,
                "quantity": abs(item.qty),
            }
        )

    return items_list


def update_last_request_date(
    response_datetime: str,
    route: str,
    routes_table: str = ROUTES_TABLE_CHILD_DOCTYPE_NAME,
) -> None:
    doc = frappe.get_doc(
        routes_table,
        {"url_path": route},
        ["*"],
    )

    doc.last_request_date = build_datetime_from_string(
        response_datetime, "%Y%m%d%H%M%S"
    )

    doc.save()
    frappe.db.commit()


def get_curr_env_etims_settings(
    company_name: str, vendor: str, branch_id: str = "00"
) -> Document | None:
    current_environment = get_current_environment_state(
        ENVIRONMENT_SPECIFICATION_DOCTYPE_NAME
    )
    settings = get_environment_settings(
        company_name, vendor, environment=current_environment, branch_id=branch_id
    )

    if settings:
        return settings


def get_most_recent_sales_number(
    company_name: str, vendor: str = "OSCU KRA"
) -> int | None:
    settings = get_curr_env_etims_settings(company_name, vendor)

    if settings:
        return settings.most_recent_sales_number

    return


def get_qr_code(data: str) -> str:
    """Generate QR Code data

    Args:
        data (str): The information used to generate the QR Code

    Returns:
        str: The QR Code.
    """
    qr_code_bytes = get_qr_code_bytes(data, format="PNG")
    base_64_string = bytes_to_base64_string(qr_code_bytes)

    return add_file_info(base_64_string)


def add_file_info(data: str) -> str:
    """Add info about the file type and encoding.

    This is required so the browser can make sense of the data."""
    return f"data:image/png;base64, {data}"


def get_qr_code_bytes(data: bytes | str, format: str = "PNG") -> bytes:
    """Create a QR code and return the bytes."""
    img = qrcode.make(data)

    buffered = BytesIO()
    img.save(buffered, format=format)

    return buffered.getvalue()


def bytes_to_base64_string(data: bytes) -> str:
    """Convert bytes to a base64 encoded string."""
    return b64encode(data).decode("utf-8")


def quantize_number(number: str | int | float) -> str:
    """Return number value to two decimal points"""
    return Decimal(number).quantize(Decimal(".01"), rounding=ROUND_DOWN).to_eng_string()


def split_user_email(email_string: str) -> str:
    """Retrieve portion before @ from an email string"""
    return email_string.split("@")[0]


def calculate_tax(doc: "Document") -> None:
    """Calculate tax for each item in the document based on item-level or document-level tax template."""
    for item in doc.items:
        tax: float = 0
        tax_rate: float | None = None

        # Check if the item has its own Item Tax Template
        if item.item_tax_template:
            tax_rate = get_item_tax_rate(item.item_tax_template)
        else:
            continue

        # Calculate tax if we have a valid tax rate
        if tax_rate is not None:
            tax = item.net_amount * tax_rate / 100

        # Set the custom tax fields in the item
        item.custom_tax_amount = tax
        item.custom_tax_rate = tax_rate if tax_rate else 0


def get_item_tax_rate(item_tax_template: str) -> float | None:
    """Fetch the tax rate from the Item Tax Template."""
    tax_template = frappe.get_doc("Item Tax Template", item_tax_template)
    if tax_template.taxes:
        return tax_template.taxes[0].tax_rate
    return None


"""Uncomment this function if you need document-level tax rate calculation in the future
A classic example usecase is Apex tevin typecase where the tax rate is fetched from the document's Sales Taxes and Charges Template
"""
# def get_doc_tax_rate(doc_tax_template: str) -> float | None:
#     """Fetch the tax rate from the document's Sales Taxes and Charges Template."""
#     tax_template = frappe.get_doc("Sales Taxes and Charges Template", doc_tax_template)
#     if tax_template.taxes:
#         return tax_template.taxes[0].rate
#     return None


def before_save_(doc: "Document", method: str | None = None) -> None:
    calculate_tax(doc)


def get_invoice_number(invoice_name: str) -> int:
    """
    Extracts the numeric portion from the invoice naming series.

    Args:
        invoice_name (str): The name of the Sales Invoice document (e.g., 'eTIMS-INV-00-00001').

    Returns:
        int: The extracted invoice number.
    """
    parts = invoice_name.split("-")
    if len(parts) >= 3:
        return int(parts[-1])
    else:
        raise ValueError("Invoice name format is incorrect")


"""For cancelled and amended invoices"""


def clean_invc_no(invoice_name: str) -> str:
    if "-" in invoice_name:
        invoice_name = "-".join(invoice_name.split("-")[:-1])
    return invoice_name


def get_taxation_types(doc: dict) -> dict:
    taxation_totals = {}

    # Loop through each item in the Sales Invoice
    for item in doc.items:
        taxation_type = item.custom_taxation_type
        taxable_amount = item.net_amount
        tax_amount = item.custom_tax_amount

        # Fetch the tax rate for the current taxation type from the specified doctype
        tax_rate = frappe.db.get_value(
            "Navari KRA eTims Taxation Type", taxation_type, "userdfncd1"
        )
        # If the taxation type already exists in the dictionary, update the totals
        if taxation_type in taxation_totals:
            taxation_totals[taxation_type]["taxable_amount"] += taxable_amount
            taxation_totals[taxation_type]["tax_amount"] += tax_amount

        else:
            taxation_totals[taxation_type] = {
                "tax_rate": tax_rate,
                "tax_amount": tax_amount,
                "taxable_amount": taxable_amount,
            }

    return taxation_totals


def authenticate_and_get_token(
    auth_server_url: str,
    username: str,
    password: str,
    client_id: str,
    client_secret: str,
) -> dict:
    payload = {
        "username": username,
        "password": password,
        "grant_type": "password",
        "client_id": client_id,
        "client_secret": client_secret,
    }
    print(payload)
    encoded_payload = urlencode(payload)

    headers = {
        "accept": "application/json",
        "content-type": "application/x-www-form-urlencoded",
    }

    response = requests.post(
        f"{auth_server_url}/oauth2/token/", headers=headers, data=encoded_payload
    )

    if response.status_code == 200:
        data = response.json()
        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")
        expires_in = data.get("expires_in")
        token_type = data.get("token_type")
        scope = data.get("scope")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": expires_in,
            "token_type": token_type,
            "scope": scope,
        }
    else:
        raise Exception(
            f"Authentication failed: {response.status_code} - {response.text}"
        )


@frappe.whitelist()
def update_navari_settings_with_token(docname: str) -> str:
    settings_doc = frappe.get_doc(SETTINGS_DOCTYPE_NAME, docname)
    auth_server_url = settings_doc.auth_server_url
    username = settings_doc.auth_username
    client_id = settings_doc.client_id
    password = settings_doc.get_password("auth_password")
    client_secret = settings_doc.get_password("client_secret")

    token_details = authenticate_and_get_token(
        auth_server_url, username, password, client_id, client_secret
    )

    if not token_details:
        return None

    settings_doc.access_token = token_details["access_token"]
    settings_doc.refresh_token = token_details["refresh_token"]
    settings_doc.token_expiry = datetime.now() + timedelta(
        seconds=token_details["expires_in"]
    )

    settings_doc.save()

    return settings_doc


def get_link_value(
    doctype: str, field_name: str, value: str, return_field: str = "name"
) -> str:
    try:
        return frappe.db.get_value(doctype, {field_name: value}, return_field)
    except Exception as e:
        frappe.log_error(
            title=f"Error Fetching Link for {doctype}",
            message=f"Error while fetching link for {doctype} with {field_name}={value}: {str(e)}",
        )
        return None


def get_or_create_link(doctype: str, field_name: str, value: str) -> str:
    if not value:
        return None

    try:
        link_name = frappe.db.get_value(doctype, {field_name: value}, "name")
        if not link_name:
            link_name = (
                frappe.get_doc(
                    {
                        "doctype": doctype,
                        field_name: value,
                        "code": value,
                    }
                )
                .insert(ignore_permissions=True, ignore_mandatory=True)
                .name
            )
            frappe.db.commit()
        return link_name
    except Exception as e:
        frappe.log_error(
            title=f"Error in get_or_create_link for {doctype}",
            message=f"Error in {doctype} - {value}: {str(e)}",
        )
        return None


def process_dynamic_url(route_path: str, request_data: dict | str) -> str:
    import json
    import re

    if isinstance(request_data, str):
        try:
            request_data = json.loads(request_data)
        except json.JSONDecodeError as e:
            raise ValueError("Invalid JSON string in request_data.") from e

    placeholders = re.findall(r"\{(.*?)\}", route_path)
    for placeholder in placeholders:
        if placeholder in request_data:
            route_path = route_path.replace(
                f"{{{placeholder}}}", str(request_data[placeholder])
            )
        else:
            raise ValueError(
                f"Missing required placeholder: '{placeholder}' in request_data."
            )

    return route_path
