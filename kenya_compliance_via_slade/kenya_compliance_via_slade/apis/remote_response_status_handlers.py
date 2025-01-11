from datetime import datetime
from io import BytesIO

import deprecation
import qrcode

import frappe

from ... import __version__
from ..doctype.doctype_names_mapping import (
    COUNTRIES_DOCTYPE_NAME,
    IMPORTED_ITEMS_STATUS_DOCTYPE_NAME,
    ITEM_CLASSIFICATIONS_DOCTYPE_NAME,
    ITEM_TYPE_DOCTYPE_NAME,
    NOTICES_DOCTYPE_NAME,
    PACKAGING_UNIT_DOCTYPE_NAME,
    PRODUCT_TYPE_DOCTYPE_NAME,
    REGISTERED_IMPORTED_ITEM_DOCTYPE_NAME,
    REGISTERED_PURCHASES_DOCTYPE_NAME,
    REGISTERED_PURCHASES_DOCTYPE_NAME_ITEM,
    REGISTERED_STOCK_MOVEMENTS_DOCTYPE_NAME,
    TAXATION_TYPE_DOCTYPE_NAME,
    UNIT_OF_QUANTITY_DOCTYPE_NAME,
    USER_DOCTYPE_NAME,
)
from ..handlers import handle_errors, handle_slade_errors
from ..utils import get_link_value, get_or_create_link


def on_error(
    response: dict | str,
    url: str | None = None,
    doctype: str | None = None,
    document_name: str | None = None,
) -> None:
    """Base "on-error" callback.

    Args:
        response (dict | str): The remote response
        url (str | None, optional): The remote address. Defaults to None.
        doctype (str | None, optional): The doctype calling the remote address. Defaults to None.
        document_name (str | None, optional): The document calling the remote address. Defaults to None.
        integration_reqeust_name (str | None, optional): The created Integration Request document name. Defaults to None.
    """
    handle_errors(
        response,
        route=url,
        doctype=doctype,
        document_name=document_name,
    )


def on_slade_error(
    response: dict | str,
    url: str | None = None,
    doctype: str | None = None,
    document_name: str | None = None,
) -> None:
    """Base "on-error" callback.

    Args:
        response (dict | str): The remote response
        url (str | None, optional): The remote address. Defaults to None.
        doctype (str | None, optional): The doctype calling the remote address. Defaults to None.
        document_name (str | None, optional): The document calling the remote address. Defaults to None.
        integration_reqeust_name (str | None, optional): The created Integration Request document name. Defaults to None.
    """
    handle_slade_errors(
        response,
        route=url,
        doctype=doctype,
        document_name=document_name,
    )


"""
These functions are required as serialising lambda expressions is a bit involving.
"""


def customer_search_on_success(
    response: dict,
    document_name: str,
) -> None:
    frappe.db.set_value(
        "Customer",
        document_name,
        {
            "custom_tax_payers_name": response["partner_name"],
            # "custom_tax_payers_status": response["taxprSttsCd"],
            "custom_county_name": response["town"],
            "custom_subcounty_name": response["town"],
            "custom_tax_locality_name": response["physical_address"],
            "custom_location_name": response["physical_address"],
            "custom_is_validated": 1,
        },
    )


def item_registration_on_success(response: dict, document_name: str, **kwargs) -> None:
    updates = {
        "custom_item_registered": 1 if response.get("sent_to_etims") else 0,
        "custom_slade_id": response.get("id"),
        "custom_sent_to_slade": 1,
    }
    frappe.db.set_value("Item", document_name, updates)


def customer_insurance_details_submission_on_success(
    response: dict, document_name: str
) -> None:
    frappe.db.set_value(
        "Customer",
        document_name,
        {"custom_insurance_details_submitted_successfully": 1},
    )


def customer_branch_details_submission_on_success(
    response: dict, document_name: str
) -> None:
    doctype = "Supplier" if response.get("is_supplier") else "Customer"
    frappe.db.set_value(
        doctype,
        document_name,
        {"custom_details_submitted_successfully": 1, "slade_id": response.get("id")},
    )


def user_details_submission_on_success(
    response: dict, document_name: str, **kwargs
) -> None:
    frappe.db.set_value(
        USER_DOCTYPE_NAME,
        document_name,
        {
            "submitted_successfully_to_etims": (
                1 if response.get("sent_to_etims") else 0
            ),
            "slade_id": response.get("id"),
            "sent_to_slade": 1,
        },
    )


def user_details_fetch_on_success(response: dict, document_name: str, **kwargs) -> None:
    result = response.get("results", [])[0] if response.get("results") else response
    email = result.get("email")

    existing_user = frappe.db.exists("User", {"email": email})
    if not existing_user:
        user = frappe.get_doc(
            {
                "doctype": "User",
                "email": email,
                "first_name": result.get("first_name"),
                "last_name": result.get("last_name"),
                "full_name": result.get("full_name"),
                "enabled": 1,
                "roles": [{"role": "System Manager"}],
            }
        )
        user.insert(ignore_permissions=True)
    else:
        user = frappe.get_doc("User", existing_user)

    workstation = (
        result.get("user_workstations")[0]["workstation"]
        if result.get("user_workstations") and len(result.get("user_workstations")) > 0
        else None
    )

    branch_id = (
        result.get("user_workstations")[0]["workstation__org_unit__parent"]
        if result.get("user_workstations") and len(result.get("user_workstations")) > 0
        else None
    )

    data = {
        "submitted_successfully_to_etims": 1 if response.get("sent_to_etims") else 0,
        "slade_id": result.get("id"),
        "sent_to_slade": 1,
        "first_name": result.get("first_name"),
        "last_name": result.get("last_name"),
        "users_full_names": result.get("full_name"),
        "email": email,
        "workstation": workstation,
        "company": get_link_value(
            "Company", "custom_slade_id", result.get("organisation_id")
        ),
        "branch": get_link_value("Branch", "slade_id", branch_id),
        "system_user": user.name,
    }

    existing_doc = frappe.db.exists("Navari eTims User", {"email": email})
    if not existing_doc:
        new_doc = frappe.get_doc({"doctype": "Navari eTims User", **data})
        new_doc.insert(ignore_permissions=True)
    else:
        frappe.db.set_value("Navari eTims User", existing_doc, data)


@deprecation.deprecated(
    deprecated_in="0.6.6",
    removed_in="1.0.0",
    current_version=__version__,
    details="Callback became redundant due to changes in the Item doctype rendering the field obsolete",
)
def inventory_submission_on_success(
    response: dict, document_name: str, **kwargs
) -> None:
    frappe.db.set_value("Item", document_name, {"custom_inventory_submitted": 1})


def imported_item_submission_on_success(
    response: dict, document_name: str, **kwargs
) -> None:
    frappe.db.set_value("Item", document_name, {"custom_imported_item_submitted": 1})


def submit_inventory_on_success(response: dict, document_name: str, **kwargs) -> None:
    frappe.db.set_value(
        "Stock Ledger Entry",
        document_name,
        {"custom_inventory_submitted_successfully": 1},
    )


def sales_information_submission_on_success(
    response: dict, document_name: str, doctype: str, **kwargs
) -> None:
    """
    Callback function executed after successfully processing an item.
    Updates the invoice with custom ID and submission status.
    """
    frappe.db.set_value(
        doctype,
        document_name,
        {
            "custom_slade_id": response.get("id"),
            "custom_successfully_submitted": 1,
        },
    )
    frappe.enqueue(
        "kenya_compliance_via_slade.kenya_compliance_via_slade.apis.remote_response_status_handlers.process_invoice_items",
        document_name=document_name,
        doctype=doctype,
        invoice_slade_id=response.get("id"),
        queue="long",
    )


@frappe.whitelist()
def process_invoice_items(
    document_name: str, doctype: str, invoice_slade_id: str, **kwargs
) -> None:
    """
    Retrieves the specific invoice, extracts all items, and sends each
    item separately.
    """
    from .apis import process_request

    invoice = frappe.get_doc(doctype, document_name)

    if not invoice:
        frappe.throw(f"{doctype} with name {document_name} not found.")

    items = invoice.get("items", [])
    items_table_doctype = frappe.get_meta(doctype).get_field("items").options
    if not items:
        frappe.throw(f"No items found for {doctype} {document_name}.")

    for item in items:
        payload = {
            "product": get_link_value(
                "Item", "name", item.get("item_code"), "custom_slade_id"
            ),
            "quantity": item.get("qty"),
            "new_price": item.get("rate"),
            "amount": item.get("amount"),
            "sales_invoice": invoice_slade_id,
            "document_name": item.get("name"),
        }
        process_request(
            payload,
            "SalesLineSaveReq",
            sales_item_submission_on_success,
            doctype=items_table_doctype,
            method="POST",
        )

    process_sales_transition(document_name, doctype, invoice_slade_id)


def process_sales_transition(
    document_name: str, doctype: str, invoice_slade_id: str
) -> None:
    from .apis import process_request

    def handle_transition_success(response: dict, document_name: str, **kwargs) -> None:
        # process_sales_sign(document_name, doctype, invoice_slade_id)
        frappe.enqueue(
            "kenya_compliance_via_slade.kenya_compliance_via_slade.apis.remote_response_status_handlers.process_sales_sign",
            document_name=document_name,
            doctype=doctype,
            invoice_slade_id=response.get("id"),
            queue="long",
        )

    payload = {"invoice_id": invoice_slade_id, "document_name": document_name}

    process_request(
        payload,
        "SalesTransitionReq",
        handle_transition_success,
        method="PATCH",
        doctype=doctype,
    )


def process_sales_sign(document_name: str, doctype: str, invoice_slade_id: str) -> None:
    from .apis import process_request

    def handle_invoice_sign_success(
        response: dict, document_name: str, **kwargs
    ) -> None:
        # process_sales_sign(document_name, doctype, invoice_slade_id)
        frappe.enqueue(
            "kenya_compliance_via_slade.kenya_compliance_via_slade.apis.apis.get_invoice_details",
            request_data={"id": invoice_slade_id, "document_name": document_name},
            invoice_type=doctype,
            queue="long",
        )

    payload = {"invoice_id": invoice_slade_id, "document_name": document_name}

    process_request(
        payload,
        "SalesSignInvReq",
        handle_invoice_sign_success,
        method="POST",
        doctype=doctype,
    )


def update_invoice_info(response: dict, **kwargs) -> None:
    doctype = kwargs.get("doctype")
    custom_slade_id = response.get("id")
    scu_data = response.get("scu_data")
    if not scu_data:
        return

    qr_code_url = scu_data.get("qr_code_url")
    updates = {
        "custom_slade_id": custom_slade_id,
        "custom_qr_code_url": qr_code_url,
        "custom_current_receipt_number": scu_data.get("scu_receipt_number"),
        "custom_control_unit_date_time": parse_datetime(
            scu_data.get("scu_receipt_timestamp")
        ),
        "custom_receipt_signature": scu_data.get("scu_receipt_signature"),
        "custom_internal_data": scu_data.get("scu_internal_data"),
        "custom_scu_id": scu_data.get("scu_id"),
        "custom_scu_mrc_no": scu_data.get("scu_mrc_number"),
        "custom_scu_invoice_number": scu_data.get("scu_invoice_number"),
    }

    # Generate QR Code image if qr_code_url is available
    if qr_code_url:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_code_url)
        qr.make(fit=True)

        # Save QR Code image as binary
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        # Attach the QR code image to the document and get the file URL
        file_doc = frappe.get_doc(
            {
                "doctype": "File",
                "file_name": f"QR-{custom_slade_id}.png",
                "is_private": 1,
                "content": buffer.read(),
                "attached_to_doctype": doctype,
                "attached_to_name": custom_slade_id,
            }
        )
        file_doc.save()
        updates["custom_qr_code"] = file_doc.file_url

    document_name = frappe.db.get_value(
        doctype, {"custom_slade_id": custom_slade_id}, "name"
    )
    if document_name:
        frappe.db.set_value(doctype, document_name, updates)


def sales_item_submission_on_success(
    response: dict, document_name: str, doctype: str, **kwargs
) -> None:
    updates = {
        "custom_slade_id": response.get("id"),
        "custom_sent_to_slade": 1,
    }
    frappe.db.set_value(doctype, document_name, updates)


def item_composition_submission_on_success(
    response: dict, document_name: str, **kwargs
) -> None:
    frappe.db.set_value(
        "BOM", document_name, {"custom_item_composition_submitted_successfully": 1}
    )


def purchase_invoice_submission_on_success(
    response: dict, document_name: str, **kwargs
) -> None:
    frappe.db.set_value(
        "Purchase Invoice",
        document_name,
        {
            "custom_slade_id": response.get("id"),
            "custom_submitted_successfully": 1,
        },
    )


def stock_mvt_submission_on_success(
    response: dict, document_name: str, **kwargs
) -> None:
    frappe.db.set_value(
        "Stock Ledger Entry", document_name, {"custom_submitted_successfully": 1}
    )


def purchase_search_on_success(response: dict, **kwargs) -> None:
    sales_list = (
        response.get("results", [])
        if isinstance(response, dict)
        else response if isinstance(response, list) else [response]
    )
    for sale in sales_list:
        registered_purchase = create_purchase_from_search_details(sale)
        frappe.enqueue(
            "kenya_compliance_via_slade.kenya_compliance_via_slade.apis.remote_response_status_handlers.fetch_purchase_items",
            registered_purchase=registered_purchase,
            queue="long",
        )


def fetch_purchase_items(registered_purchase: str) -> None:
    from .apis import process_request

    payload = {
        "purchase_invoice": registered_purchase,
        "document_name": registered_purchase,
    }

    process_request(
        payload,
        "TrnsPurchaseItemReq",
        create_and_link_purchase_item,
        method="GET",
        doctype=REGISTERED_PURCHASES_DOCTYPE_NAME,
    )


def parse_datetime(date_str: str, format: str = "%Y-%m-%dT%H:%M:%S%z") -> str:
    if not date_str:
        return
    try:
        if "T" in date_str:
            parsed_date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S%z")
        else:
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
        return parsed_date.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        frappe.log_error(
            f"Invalid datetime format: {date_str}", title="Datetime Parsing Error"
        )
        return None


def create_purchase_from_search_details(fetched_purchase: dict) -> str:
    """
    Create and submit a new registered purchase document using details from fetched_purchase.
    """
    existing_doc = frappe.get_value(
        REGISTERED_PURCHASES_DOCTYPE_NAME, {"slade_id": fetched_purchase["id"]}, "name"
    )

    if existing_doc:
        doc = frappe.get_doc(REGISTERED_PURCHASES_DOCTYPE_NAME, existing_doc)
    else:
        doc = frappe.new_doc(REGISTERED_PURCHASES_DOCTYPE_NAME)

    doc.flags.ignore_permissions = True
    doc.flags.ignore_validate_update_after_submit = True
    doc.slade_id = fetched_purchase["id"]

    doc.supplier_name = fetched_purchase["supplier_name"]
    doc.supplier_pin = fetched_purchase["supplier_pin"]
    doc.supplier_branch_id = fetched_purchase["supplier_branch_id"]
    doc.supplier_invoice_number = fetched_purchase["supplier_invoice_number"]

    doc.receipt_type_code = fetched_purchase["receipt_type_code"]
    if fetched_purchase.get("payment_type_code"):
        doc.payment_type_code = frappe.get_doc(
            "Navari KRA eTims Payment Type",
            {"code": fetched_purchase["payment_type_code"]},
            ["name"],
        ).name

    doc.validated_date = parse_datetime(fetched_purchase["validated_date"])
    doc.sales_date = parse_datetime(fetched_purchase["sale_date"])
    doc.stock_released_date = parse_datetime(fetched_purchase["stock_released_date"])
    doc.remarks = fetched_purchase["remark"]

    doc.total_item_count = fetched_purchase["total_item_count"]
    doc.total_taxable_amount = fetched_purchase["total_taxable_amount"]
    doc.total_tax_amount = fetched_purchase["total_tax_amount"]
    doc.total_amount = fetched_purchase["total_amount"]

    doc.taxable_amount_a = fetched_purchase.get("taxable_amount_A", 0.0)
    doc.taxable_amount_b = fetched_purchase.get("taxable_amount_B", 0.0)
    doc.taxable_amount_c = fetched_purchase.get("taxable_amount_C", 0.0)
    doc.taxable_amount_d = fetched_purchase.get("taxable_amount_D", 0.0)
    doc.taxable_amount_e = fetched_purchase.get("taxable_amount_E", 0.0)

    doc.tax_rate_a = fetched_purchase.get("tax_rate_A", 0.0)
    doc.tax_rate_b = fetched_purchase.get("tax_rate_B", 0.0)
    doc.tax_rate_c = fetched_purchase.get("tax_rate_C", 0.0)
    doc.tax_rate_d = fetched_purchase.get("tax_rate_D", 0.0)
    doc.tax_rate_e = fetched_purchase.get("tax_rate_E", 0.0)

    doc.tax_amount_a = fetched_purchase.get("tax_amount_A", 0.0)
    doc.tax_amount_b = fetched_purchase.get("tax_amount_B", 0.0)
    doc.tax_amount_c = fetched_purchase.get("tax_amount_C", 0.0)
    doc.tax_amount_d = fetched_purchase.get("tax_amount_D", 0.0)
    doc.tax_amount_e = fetched_purchase.get("tax_amount_E", 0.0)

    doc.workflow_state = fetched_purchase["workflow_state"]
    doc.branch = (get_link_value("Branch", "slade_id", fetched_purchase["branch"]),)
    doc.organisation = (
        get_link_value("Company", "custom_slade_id", fetched_purchase["organisation"]),
    )
    doc.can_send_to_etims = fetched_purchase["can_send_to_etims"]

    try:
        doc.submit()
    except frappe.exceptions.DuplicateEntryError:
        frappe.log_error(
            title="Duplicate entries", message=f"Duplicate for document: {doc.name}"
        )

    return doc.name


def create_and_link_purchase_item(response: dict, document_name: str, **kwargs) -> None:
    item_list = response if isinstance(response, list) else response.get("results")
    parent_record = frappe.get_doc(REGISTERED_PURCHASES_DOCTYPE_NAME, document_name)
    parent_record.flags.ignore_permissions = True
    parent_record.flags.ignore_validate_update_after_submit = True

    for item in item_list:
        existing_item = frappe.get_all(
            REGISTERED_PURCHASES_DOCTYPE_NAME_ITEM, filters={"slade_id": item["id"]}
        )

        if existing_item:
            registered_item = frappe.get_doc(
                REGISTERED_PURCHASES_DOCTYPE_NAME_ITEM, item["id"]
            )
            registered_item.flags.ignore_permissions = True
            registered_item.flags.ignore_validate_update_after_submit = True
        else:
            registered_item = frappe.new_doc(REGISTERED_PURCHASES_DOCTYPE_NAME_ITEM)
            registered_item.parent = parent_record.name
            registered_item.parentfield = "items"
            registered_item.parenttype = REGISTERED_PURCHASES_DOCTYPE_NAME

        registered_item.slade_id = item["id"]
        registered_item.item_name = item["item_name"]
        registered_item.purchase_invoice = item["purchase_invoice"]
        registered_item.is_mapped = 1 if item["is_mapped"] else 0
        registered_item.product_name = item["product_name"]
        registered_item.product_code = item["product_code"]
        registered_item.item_code = item["item_code"]
        registered_item.item_classification_code_data = item["item_classification_code"]
        registered_item.item_classification_code = get_or_create_link(
            ITEM_CLASSIFICATIONS_DOCTYPE_NAME,
            "itemclscd",
            item["item_classification_code"],
        )
        registered_item.item_sequence = item["item_sequence_number"]
        registered_item.barcode = item["barcode"]
        registered_item.package = item["package"]
        registered_item.packaging_unit_code = item["package_unit_code"]
        registered_item.quantity = item["quantity"]
        registered_item.quantity_unit_code = item["quantity_unit_code"]
        registered_item.unit_price = item["unit_price"]
        registered_item.supply_amount = item["supply_amount"]
        registered_item.discount_rate = item["discount_rate"]
        registered_item.discount_amount = item["discount_amount"]
        registered_item.taxation_type_code = item["taxation_type_code"]
        registered_item.taxable_amount = item["taxable_amount"]
        registered_item.tax_amount = item["tax_amount"]
        registered_item.total_amount = item["total_amount"]
        registered_item.save()

        parent_record.append("items", registered_item)

    parent_record.save()


def notices_search_on_success(response: dict | list, **kwargs) -> None:
    notices = response if isinstance(response, list) else response.get("results")
    if isinstance(notices, list):
        for notice in notices:
            create_notice_if_new(notice)
    else:
        frappe.log_error(
            title="Invalid Response Format",
            message="Expected a list or single notice in the response",
        )


def create_notice_if_new(notice: dict) -> None:
    exists = frappe.db.exists(
        NOTICES_DOCTYPE_NAME, {"notice_number": notice.get("notice_number")}
    )
    if exists:
        return

    doc = frappe.new_doc(NOTICES_DOCTYPE_NAME)
    doc.flags.ignore_permissions = True
    doc.flags.ignore_validate_update_after_submit = True
    doc.update(
        {
            "notice_number": notice.get("notice_number"),
            "title": notice.get("title"),
            "registration_name": notice.get("registration_name"),
            "details_url": notice.get("detail_url"),
            "registration_datetime": datetime.fromisoformat(
                notice.get("registration_date")
            ).strftime("%Y-%m-%d %H:%M:%S"),
            "contents": notice.get("content"),
        }
    )
    doc.save()

    try:
        doc.submit()
    except frappe.exceptions.DuplicateEntryError:
        frappe.log_error(
            title="Duplicate Entry Error",
            message=f"Duplicate notice detected: {notice.get('notice_number')}",
        )
    except Exception as e:
        frappe.log_error(
            title="Notice Creation Failed",
            message=f"Error creating notice {notice.get('notice_number')}: {str(e)}",
        )


def stock_mvt_search_on_success(response: dict, **kwargs) -> None:
    stock_list = response["data"]["stockList"]

    for stock in stock_list:
        doc = frappe.new_doc(REGISTERED_STOCK_MOVEMENTS_DOCTYPE_NAME)

        doc.customer_pin = stock["custTin"]
        doc.customer_branch_id = stock["custBhfId"]
        doc.stored_and_released_number = stock["sarNo"]
        doc.occurred_date = stock["ocrnDt"]
        doc.total_item_count = stock["totItemCnt"]
        doc.total_supply_price = stock["totTaxblAmt"]
        doc.total_vat = stock["totTaxAmt"]
        doc.total_amount = stock["totAmt"]
        doc.remark = stock["remark"]

        doc.set("items", [])

        for item in stock["itemList"]:
            doc.append(
                "items",
                {
                    "item_name": item["itemNm"],
                    "item_sequence": item["itemSeq"],
                    "item_code": item["itemCd"],
                    "barcode": item["bcd"],
                    "item_classification_code": item["itemClsCd"],
                    "packaging_unit_code": item["pkgUnitCd"],
                    "unit_of_quantity_code": item["qtyUnitCd"],
                    "package": item["pkg"],
                    "quantity": item["qty"],
                    "item_expiry_date": item["itemExprDt"],
                    "unit_price": item["prc"],
                    "supply_amount": item["splyAmt"],
                    "discount_rate": item["totDcAmt"],
                    "taxable_amount": item["taxblAmt"],
                    "tax_amount": item["taxAmt"],
                    "taxation_type_code": item["taxTyCd"],
                    "total_amount": item["totAmt"],
                },
            )

        doc.save()


def imported_items_search_on_success(response: dict, **kwargs) -> None:
    items = response.get("results", [])
    batch_size = 20
    counter = 0

    for item in items:
        try:
            item_id = item.get("id")
            existing_item = frappe.db.get_value(
                REGISTERED_IMPORTED_ITEM_DOCTYPE_NAME,
                {"slade_id": item_id},
                "name",
                order_by="creation desc",
            )

            request_data = {
                "item_name": item.get("item_name"),
                "product_name": item.get("product_name"),
                "product_code": item.get("product_code"),
                "task_code": item.get("task_code"),
                "declaration_date": parse_date(item.get("declaration_date")),
                "item_sequence": item.get("item_sequence"),
                "declaration_number": item.get("declaration_number"),
                "imported_item_status_code": item.get("import_item_status_code"),
                "imported_item_status": get_link_value(
                    IMPORTED_ITEMS_STATUS_DOCTYPE_NAME,
                    "code",
                    item.get("import_item_status_code"),
                ),
                "hs_code": item.get("hs_code"),
                "origin_nation_code": get_link_value(
                    COUNTRIES_DOCTYPE_NAME, "code", item.get("origin_nation_code")
                ),
                "export_nation_code": get_link_value(
                    COUNTRIES_DOCTYPE_NAME, "code", item.get("export_nation_code")
                ),
                "package": item.get("package"),
                "packaging_unit_code": get_or_create_link(
                    PACKAGING_UNIT_DOCTYPE_NAME, "code", item.get("packaging_unit_code")
                ),
                "quantity": item.get("quantity"),
                "quantity_unit_code": get_or_create_link(
                    UNIT_OF_QUANTITY_DOCTYPE_NAME,
                    "code",
                    item.get("quantity_unit_code"),
                ),
                "branch": get_or_create_link("Branch", "slade_id", item.get("branch")),
                # "organisation": get_or_create_link(
                #     ORGANISATION_UNIT_DOCTYPE_NAME, "slade_id", item.get("organisation")
                # ),
                "gross_weight": item.get("gross_weight"),
                "net_weight": item.get("net_weight"),
                "suppliers_name": item.get("supplier_name"),
                "agent_name": item.get("agent_name"),
                "invoice_foreign_currency_amount": item.get(
                    "invoice_foreign_currency_amount"
                ),
                "invoice_foreign_currency": item.get("invoice_foreign_currency_code"),
                "invoice_foreign_currency_rate": item.get(
                    "invoice_foreign_currency_exchange"
                ),
                "slade_id": item_id,
                "sent_to_etims": 1 if item.get("sent_to_etims") else 0,
            }

            if existing_item:
                item_doc = frappe.get_doc(
                    REGISTERED_IMPORTED_ITEM_DOCTYPE_NAME, existing_item
                )
                item_doc.update(request_data)
                item_doc.flags.ignore_mandatory = True
                item_doc.save(ignore_permissions=True)
            else:
                item_doc = frappe.get_doc(
                    {"doctype": REGISTERED_IMPORTED_ITEM_DOCTYPE_NAME, **request_data}
                )
                item_doc.insert(
                    ignore_permissions=True,
                    ignore_mandatory=True,
                    ignore_if_duplicate=True,
                )

            if item.get("product"):
                product_name = get_link_value(
                    "Item", "custom_slade_id", item.get("product")
                )
                product = frappe.get_doc("Item", product_name)
                product.custom_referenced_imported_item = item_doc.name
                product.custom_imported_item_task_code = item_doc.task_code
                product.custom_hs_code = item_doc.hs_code
                product.custom_branch = item_doc.branch
                product.custom_organisation = item_doc.organisation
                product.custom_imported_item_submitted = item_doc.sent_to_etims
                product.custom_imported_item_status = item_doc.imported_item_status
                product.custom_imported_item_status_code = (
                    item_doc.imported_item_status_code
                )
                product.flags.ignore_mandatory = True
                product.save()

            counter += 1
            if counter % batch_size == 0:
                frappe.db.commit()

        except Exception as e:
            frappe.log_error(
                title="Imported Item Sync Error",
                message=f"Error while processing item with ID {item.get('id')}: {str(e)}",
            )

    if counter % batch_size != 0:
        frappe.db.commit()

    frappe.msgprint(
        "Imported Items fetched successfully. Go to <b>Navari eTims Registered Imported Item</b> Doctype for more information."
    )


def parse_date(date_str: str) -> None:
    formats = [
        "%d%m%Y",
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%B %d, %Y",
        "%b %d, %Y",
        "%Y.%m.%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    if date_str.isdigit():
        try:
            return datetime.fromtimestamp(int(date_str))
        except ValueError:
            pass
    raise ValueError(f"Invalid date format: {date_str}")


def search_branch_request_on_success(response: dict, **kwargs) -> None:
    for branch in response.get("results", []):
        doc = None

        try:
            doc = frappe.get_doc(
                "Branch",
                {"slade_id": branch["id"]},
                for_update=True,
            )

        except frappe.exceptions.DoesNotExistError:
            doc = frappe.new_doc("Branch")

        finally:
            doc.branch = branch["name"]
            doc.slade_id = branch["id"]
            doc.custom_etims_device_serial_no = branch["etims_device_serial_no"]
            doc.custom_branch_code = branch["etims_branch_id"]
            doc.custom_pin = branch["organisation_tax_pin"]
            doc.custom_branch_name = branch["name"]
            doc.custom_branch_status_code = branch["branch_status"]
            doc.custom_county_name = branch["county_name"]
            doc.custom_sub_county_name = branch["sub_county_name"]
            doc.custom_tax_locality_name = branch["tax_locality_name"]
            doc.custom_location_description = branch["location_description"]
            doc.custom_manager_name = branch["manager_name"]
            doc.custom_manager_contact = branch["parent_phone_number"]
            doc.custom_manager_email = branch["email_address"]
            doc.custom_is_head_office = "Y" if branch["is_headquater"] else "N"
            doc.custom_is_etims_branch = 1 if branch["is_etims_verified"] else 0

            doc.save()


def item_search_on_success(response: dict, **kwargs) -> None:
    items = response.get("results", []) or [response]
    batch_size = 20
    counter = 0

    for item_data in items:
        try:
            slade_id = item_data.get("id")
            existing_item = frappe.db.get_value(
                "Item", {"custom_slade_id": slade_id}, "name", order_by="creation desc"
            )

            request_data = {
                "item_name": item_data.get("name"),
                "item_code": item_data.get("name"),
                "custom_item_registered": 1 if item_data.get("sent_to_etims") else 0,
                "custom_slade_id": item_data.get("id"),
                "custom_sent_to_slade": 1,
                "description": item_data.get("description"),
                "is_sales_item": item_data.get("can_be_sold", False),
                "is_purchase_item": item_data.get("can_be_purchased", False),
                "company_name": frappe.defaults.get_user_default("Company"),
                "code": item_data.get("code"),
                "custom_item_code_etims": item_data.get("scu_item_code"),
                "product_type": item_data.get("product_type"),
                "product_type_code": item_data.get("product_type"),
                "preferred_name": item_data.get("preferred_name"),
                "custom_etims_country_of_origin_code": item_data.get(
                    "country_of_origin"
                ),
                "valuation_rate": round(item_data.get("selling_price", 0.0), 2),
                "last_purchase_rate": round(item_data.get("purchasing_price", 0.0), 2),
                "custom_item_classification": get_link_value(
                    ITEM_CLASSIFICATIONS_DOCTYPE_NAME,
                    "slade_id",
                    item_data.get("scu_item_classification"),
                ),
                "custom_etims_country_of_origin": get_link_value(
                    COUNTRIES_DOCTYPE_NAME, "code", item_data.get("country_of_origin")
                ),
                "custom_packaging_unit": get_link_value(
                    PACKAGING_UNIT_DOCTYPE_NAME,
                    "slade_id",
                    item_data.get("packaging_unit"),
                ),
                "custom_unit_of_quantity": get_link_value(
                    UNIT_OF_QUANTITY_DOCTYPE_NAME,
                    "slade_id",
                    item_data.get("quantity_unit"),
                ),
                "custom_item_type": get_link_value(
                    ITEM_TYPE_DOCTYPE_NAME, "name", item_data.get("item_type")
                ),
                "custom_taxation_type": get_link_value(
                    TAXATION_TYPE_DOCTYPE_NAME,
                    "slade_id",
                    item_data.get("sale_taxes")[0],
                ),
                "custom_product_type": get_link_value(
                    PRODUCT_TYPE_DOCTYPE_NAME, "code", item_data.get("product_type")
                ),
            }

            if existing_item:
                item_doc = frappe.get_doc("Item", existing_item)
                item_doc.update(request_data)
                item_doc.flags.ignore_mandatory = True
                item_doc.save(ignore_permissions=True)
            else:
                request_data["item_group"] = "All Item Groups"
                new_item = frappe.get_doc({"doctype": "Item", **request_data})
                new_item.insert(
                    ignore_permissions=True,
                    ignore_mandatory=True,
                    ignore_if_duplicate=True,
                )

            counter += 1
            if counter % batch_size == 0:
                frappe.db.commit()

        except Exception as e:
            frappe.log_error(
                title="Item Sync Error",
                message=f"Error while processing item with ID {item_data.get('id')}: {str(e)}",
            )

    if counter % batch_size != 0:
        frappe.db.commit()


def initialize_device_submission_on_success(response: dict, **kwargs) -> None:
    pass


def customers_search_on_success(response: dict, **kwargs) -> None:
    data = response.get("results", []) if response.get("results") else response
    if isinstance(data, dict):
        data = [data]
    for customer in data:
        existing_customer = frappe.db.exists("Customer", {"slade_id": customer["id"]})
        data = {
            "slade_id": customer["id"],
            "customer_name": customer["partner_name"],
            "email_id": customer["email_address"],
            "mobile_no": customer["phone_number"],
            "tax_id": customer.get("customer_tax_pin"),
            "organisation": customer.get("organisation"),
            "currency": customer.get("currency"),
            "primary_address": customer.get("physical_address"),
            "active": 1 if customer.get("active") else 0,
            "custom_details_submitted_successfully": 1,
            "customer_type": (
                customer.get("customer_type").title()
                if customer.get("customer_type")
                in ["Company", "Individual", "Partnership"]
                else "Individual"
            ),
        }

        if existing_customer and customer.get("is_customer"):
            doc = frappe.get_doc("Customer", existing_customer)
            doc.update(data)
            doc.save(ignore_permissions=True)
        else:
            doc = frappe.new_doc("Customer")
            doc.update(data)
            doc.insert(ignore_permissions=True)
        frappe.db.commit()


def warehouse_update_on_success(response: dict, document_name: str, **kwargs) -> None:
    frappe.db.set_value(
        "Warehouse", document_name, {"custom_slade_id": response.get("id")}
    )


def pricelist_update_on_success(response: dict, document_name: str, **kwargs) -> None:
    frappe.db.set_value(
        "Price List", document_name, {"custom_slade_id": response.get("id")}
    )


def item_price_update_on_success(response: dict, document_name: str, **kwargs) -> None:
    frappe.db.set_value(
        "Item Price", document_name, {"custom_slade_id": response.get("id")}
    )
