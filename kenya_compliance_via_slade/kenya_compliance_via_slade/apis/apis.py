import asyncio
import json

import aiohttp

import frappe
import frappe.defaults
from frappe.model.document import Document

from ..doctype.doctype_names_mapping import (
    COUNTRIES_DOCTYPE_NAME,
    ITEM_CLASSIFICATIONS_DOCTYPE_NAME,
    OPERATION_TYPE_DOCTYPE_NAME,
    PACKAGING_UNIT_DOCTYPE_NAME,
    REGISTERED_PURCHASES_DOCTYPE_NAME,
    SETTINGS_DOCTYPE_NAME,
    TAXATION_TYPE_DOCTYPE_NAME,
    UNIT_OF_QUANTITY_DOCTYPE_NAME,
    UOM_CATEGORY_DOCTYPE_NAME,
    USER_DOCTYPE_NAME,
)
from ..utils import (
    generate_custom_item_code_etims,
    get_link_value,
    get_settings,
    make_get_request,
)
from .api_builder import EndpointsBuilder
from .process_request import process_request
from .remote_response_status_handlers import (
    customer_branch_details_submission_on_success,
    customer_search_on_success,
    customers_search_on_success,
    imported_item_submission_on_success,
    imported_items_search_on_success,
    initialize_device_submission_on_success,
    item_composition_submission_on_success,
    item_price_update_on_success,
    item_registration_on_success,
    item_search_on_success,
    mode_of_payment_on_success,
    pricelist_update_on_success,
    purchase_search_on_success,
    search_branch_request_on_success,
    submit_inventory_on_success,
    update_invoice_info,
    user_details_fetch_on_success,
    user_details_submission_on_success,
)

endpoints_builder = EndpointsBuilder()
from ..background_tasks.task_response_handlers import (
    operation_types_search_on_success,
    uom_category_search_on_success,
    uom_search_on_success,
)


@frappe.whitelist()
def bulk_submit_sales_invoices(docs_list: str) -> None:
    from ..overrides.server.sales_invoice import on_submit

    data = json.loads(docs_list)
    all_sales_invoices = frappe.db.get_all(
        "Sales Invoice", {"docstatus": 1, "custom_successfully_submitted": 0}, ["name"]
    )

    for record in data:
        for invoice in all_sales_invoices:
            if record == invoice.name:
                doc = frappe.get_doc("Sales Invoice", record, for_update=False)
                frappe.enqueue(on_submit, doc=doc)


@frappe.whitelist()
def bulk_register_item(docs_list: str) -> None:
    data = json.loads(docs_list)

    for record in data:
        is_registered = frappe.db.get_value("Item", record, "custom_sent_to_slade")
        if is_registered == 0:
            item_name = frappe.db.get_value("Item", record, "name")
            frappe.enqueue(perform_item_registration, item_name=str(item_name))


@frappe.whitelist()
def register_all_items() -> None:
    data = frappe.db.get_all(
        "Item", filters={"custom_sent_to_slade": 0}, fields=["name"]
    )

    for record in data:
        item_name = frappe.db.get_value("Item", record, "name")
        frappe.enqueue(perform_item_registration, item_name=str(item_name))


@frappe.whitelist()
def perform_customer_search(request_data: str) -> None:
    """Search customer details in the eTims Server

    Args:
        request_data (str): Data received from the client
    """
    return process_request(
        request_data,
        "CustSearchReq",
        customer_search_on_success,
        request_method="POST",
        doctype="Customer",
    )


@frappe.whitelist()
def perform_item_registration(item_name: str) -> dict | None:
    item = frappe.get_doc("Item", item_name)
    missing_fields = []

    required_fields = [
        # "custom_item_code_etims",
        "custom_item_classification",
        "custom_product_type",
        "custom_item_type",
        "custom_etims_country_of_origin_code",
        "custom_packaging_unit",
        "custom_unit_of_quantity",
        "custom_taxation_type",
    ]

    for field in required_fields:
        if not item.get(field):
            missing_fields.append(field)

    if missing_fields:
        return
    if not item.custom_item_code_etims:
        item.custom_item_code_etims = generate_custom_item_code_etims(item)
        frappe.db.set_value(
            "Item", item.name, "custom_item_code_etims", item.custom_item_code_etims
        )

    tax = get_link_value(
        TAXATION_TYPE_DOCTYPE_NAME, "cd", item.get("custom_taxation_type"), "slade_id"
    )
    sent_to_slade = item.get("custom_sent_to_slade", False)
    custom_slade_id = item.get("custom_slade_id", None)

    request_data = {
        "name": item.get("item_name"),
        "document_name": item.get("name"),
        "description": item.get("description"),
        "can_be_sold": True if item.get("is_sales_item") == 1 else False,
        "can_be_purchased": True if item.get("is_purchase_item") == 1 else False,
        "company_name": frappe.defaults.get_user_default("Company"),
        "code": item.get("item_code"),
        "scu_item_code": item.get("custom_item_code_etims"),
        "scu_item_classification": get_link_value(
            ITEM_CLASSIFICATIONS_DOCTYPE_NAME,
            "itemclscd",
            item.get("custom_item_classification"),
            "slade_id",
        ),
        "product_type": item.get("custom_product_type"),
        "item_type": item.get("custom_item_type"),
        "preferred_name": item.get("item_name"),
        "country_of_origin": item.get("custom_etims_country_of_origin_code"),
        "packaging_unit": get_link_value(
            PACKAGING_UNIT_DOCTYPE_NAME,
            "code",
            item.get("custom_packaging_unit"),
            "slade_id",
        ),
        "quantity_unit": get_link_value(
            UNIT_OF_QUANTITY_DOCTYPE_NAME,
            "code",
            item.get("custom_unit_of_quantity"),
            "slade_id",
        ),
        "sale_taxes": [tax],
        "selling_price": round(item.get("valuation_rate", 1), 2),
        "purchasing_price": round(item.get("last_purchase_rate", 1), 2),
        "categories": [],
        "purchase_taxes": [],
    }

    if sent_to_slade and custom_slade_id:
        request_data["id"] = custom_slade_id
        process_request(
            request_data,
            "ItemsSearchReq",
            item_registration_on_success,
            request_method="PATCH",
            doctype="Item",
        )
    else:
        process_request(
            request_data,
            "ItemsSearchReq",
            item_registration_on_success,
            request_method="POST",
            doctype="Item",
        )


@frappe.whitelist()
def fetch_item_details(request_data: str) -> None:
    process_request(
        request_data, "ItemSearchReq", item_search_on_success, doctype="Item"
    )


@frappe.whitelist()
def submit_all_suppliers() -> None:
    suppliers: list[Document] = frappe.get_all(
        "Supplier",
        {
            "custom_details_submitted_successfully": 0,
        },
        ["name"],
    )
    for supplier in suppliers:
        frappe.enqueue(
            send_branch_customer_details, name=supplier.name, is_customer=False
        )


@frappe.whitelist()
def submit_all_customers() -> None:
    customers: list[Document] = frappe.get_all(
        "Customer",
        {
            "custom_details_submitted_successfully": 0,
        },
        ["name"],
    )
    for customer in customers:
        frappe.enqueue(send_branch_customer_details, name=customer.name)


@frappe.whitelist()
def send_branch_customer_details(name: str, is_customer: bool = True) -> None:
    doctype = "Customer" if is_customer else "Supplier"
    data = frappe.get_doc(doctype, name)

    payload = {
        "document_name": name,
        "currency": data.get("default_currency") or "KES",
        "country": "KEN",
    }

    if is_customer:
        payload.update(
            {
                "is_customer": True,
                "customer_tax_pin": data.get("customer_tax_pin"),
                "partner_name": data.get("customer_name"),
                "phone_number": data.get("mobile_no"),
                "customer_type": "INDIVIDUAL",
            }
        )
    else:
        payload.update(
            {
                "customer_tax_pin": data.get("tax_id"),
                "partner_name": data.get("supplier_name"),
                "is_supplier": True,
                "supplier_type": "INDIVIDUAL",
            }
        )

    phone_number = (data.get("phone_number") or "").replace(" ", "").strip()
    payload["phone_number"] = (
        "+254" + phone_number[-9:] if len(phone_number) >= 9 else None
    )

    currency_name = payload.get("currency")

    if currency_name:
        payload["currency"] = frappe.get_value(
            "Currency", currency_name, "custom_slade_id"
        )

    process_request(
        json.dumps(payload),
        "BhfCustSaveReq",
        customer_branch_details_submission_on_success,
        request_method="POST",
        doctype=doctype,
    )


@frappe.whitelist()
def search_customers_request(request_data: str) -> None:
    return process_request(
        request_data, "CustomersSearchReq", customers_search_on_success
    )


@frappe.whitelist()
def get_customer_details(request_data: str) -> None:
    return process_request(
        request_data, "CustomerSearchReq", customers_search_on_success
    )


@frappe.whitelist()
def get_my_user_details(request_data: str) -> None:
    return process_request(
        request_data,
        "BhfUserSearchReq",
        user_details_fetch_on_success,
        request_method="GET",
        doctype=USER_DOCTYPE_NAME,
    )


@frappe.whitelist()
def get_branch_user_details(request_data: str) -> None:
    return process_request(
        request_data,
        "BhfUserSaveReq",
        user_details_fetch_on_success,
        request_method="GET",
        doctype=USER_DOCTYPE_NAME,
    )


@frappe.whitelist()
def save_branch_user_details(request_data: str) -> None:
    return process_request(
        request_data,
        "BhfUserSaveReq",
        user_details_submission_on_success,
        request_method="POST",
        doctype=USER_DOCTYPE_NAME,
    )


@frappe.whitelist()
def create_branch_user() -> None:
    # TODO: Implement auto-creation through background tasks
    present_users = frappe.db.get_all(
        "User", {"name": ["not in", ["Administrator", "Guest"]]}, ["name", "email"]
    )

    for user in present_users:
        if not frappe.db.exists(USER_DOCTYPE_NAME, {"email": user.email}):
            doc = frappe.new_doc(USER_DOCTYPE_NAME)

            doc.system_user = user.email
            doc.branch_id = frappe.get_value(
                "Branch",
                {"custom_branch_code": frappe.get_value("Branch", "name")},
                ["name"],
            )  # Created users are assigned to Branch 00

            doc.save(ignore_permissions=True)

    frappe.msgprint("Inspect the Branches to make sure they are mapped correctly")


@frappe.whitelist()
def perform_item_search(request_data: str) -> None:
    data: dict = json.loads(request_data)

    process_request(
        request_data, "ItemsSearchReq", item_search_on_success, doctype="Item"
    )


@frappe.whitelist()
def perform_import_item_search(request_data: str) -> None:
    process_request(
        request_data,
        "ImportItemSearchReq",
        imported_items_search_on_success,
        doctype="Item",
    )


@frappe.whitelist()
def perform_import_item_search_all_branches() -> None:
    all_credentials = frappe.get_all(
        SETTINGS_DOCTYPE_NAME,
        ["name", "bhfid", "company"],
    )

    for credential in all_credentials:
        request_data = json.dumps(
            {"company_name": credential.company, "branch_code": credential.bhfid}
        )

        perform_import_item_search(request_data)


@frappe.whitelist()
def perform_purchases_search(request_data: str) -> None:
    process_request(
        request_data,
        "TrnsPurchaseSalesReq",
        purchase_search_on_success,
        doctype=REGISTERED_PURCHASES_DOCTYPE_NAME,
    )


@frappe.whitelist()
def perform_purchase_search(request_data: str) -> None:
    process_request(
        request_data,
        "TrnsPurchaseSearchReq",
        purchase_search_on_success,
        doctype=REGISTERED_PURCHASES_DOCTYPE_NAME,
    )


@frappe.whitelist()
def send_entire_stock_balance() -> None:
    all_items = frappe.get_all(
        "Item",
        filters={"is_stock_item": 1, "custom_sent_to_slade": 1},
        fields=["name", "item_code", "item_name"],
    )

    for item in all_items:
        frappe.enqueue(submit_inventory, name=item.name)


@frappe.whitelist()
def submit_inventory(name: str) -> None:
    # TODO: Redesign this function to work with the new structure for Stock Submission
    # pass
    if not name:
        frappe.throw("Item name is required.")

    settings = get_settings()
    stock_levels = frappe.db.get_all(
        "Bin",
        filters={"item_code": name},
        fields=["warehouse", "actual_qty", "reserved_qty", "projected_qty", "name"],
    )

    if not stock_levels:
        frappe.msgprint(f"No stock levels found for item {name}.")
    else:
        request_data = {
            "document_name": name,
            "inventory_reference": name,
            "description": f"{name} Stock Adjustment for {name}",
            "reason": "Opening Stock",
            "source_organisation_unit": get_link_value(
                "Department",
                "name",
                settings.department,
                "custom_slade_id",
            ),
            "location": get_link_value(
                "Warehouse",
                "name",
                settings.get("warehouse"),
                "custom_slade_id",
            ),
        }
        process_request(
            request_data,
            route_key="StockMasterSaveReq",
            handler_function=submit_inventory_on_success,
            request_method="POST",
            doctype="Item",
        )


@frappe.whitelist()
def search_branch_request(request_data: str) -> None:
    return process_request(
        request_data, "BhfSearchReq", search_branch_request_on_success, doctype="Branch"
    )


@frappe.whitelist()
def send_imported_item_request(request_data: str) -> None:
    process_request(
        request_data,
        "ImportItemSearchReq",
        imported_item_submission_on_success,
        request_method="POST",
        doctype="Item",
    )


@frappe.whitelist()
def update_imported_item_request(request_data: str) -> None:
    process_request(
        request_data,
        "ImportItemUpdateReq",
        imported_item_submission_on_success,
        method="PUT",
        doctype="Item",
    )


@frappe.whitelist()
def submit_item_composition(name: str) -> None:
    item = frappe.get_doc("BOM", name)
    request_data = {
        "final_product": get_link_value("Item", "name", item.item, "custom_slade_id"),
        "document_name": name,
    }
    process_request(
        request_data,
        "BOMReq",
        item_composition_submission_on_success,
        request_method="POST",
        doctype="BOM",
    )


@frappe.whitelist()
def create_supplier_from_fetched_registered_purchases(request_data: str) -> None:
    data: dict = json.loads(request_data)

    new_supplier = create_supplier(data)

    frappe.msgprint(f"Supplier: {new_supplier.name} created")


def create_supplier(supplier_details: dict) -> Document:
    new_supplier = frappe.new_doc("Supplier")

    new_supplier.supplier_name = supplier_details["supplier_name"]
    new_supplier.tax_id = supplier_details["supplier_pin"]
    new_supplier.custom_supplier_branch = supplier_details["supplier_branch_id"]

    if "supplier_currency" in supplier_details:
        new_supplier.default_currency = supplier_details["supplier_currency"]

    if "supplier_nation" in supplier_details:
        new_supplier.country = supplier_details["supplier_nation"].capitalize()

    new_supplier.insert(ignore_if_duplicate=True)

    return new_supplier


@frappe.whitelist()
def create_items_from_fetched_registered(request_data: str) -> None:
    data = json.loads(request_data)

    if data["items"]:
        items = data["items"]
        for item in items:
            create_item(item)


def create_item(item: dict | frappe._dict) -> Document:
    item_code = item.get("item_code", None)

    new_item = frappe.new_doc("Item")
    new_item.is_stock_item = 0  # Default to 0
    new_item.item_code = item["product_code"]
    new_item.item_name = item["item_name"]
    new_item.item_group = "All Item Groups"
    if "item_classification_code" in item:
        new_item.custom_item_classification = item["item_classification_code"]
    new_item.custom_packaging_unit = item["packaging_unit_code"]
    new_item.custom_unit_of_quantity = (
        item.get("quantity_unit_code", None) or item["unit_of_quantity_code"]
    )
    new_item.custom_taxation_type = item["taxation_type_code"]
    new_item.custom_etims_country_of_origin = (
        frappe.get_doc(
            COUNTRIES_DOCTYPE_NAME,
            {"code": item_code[:2]},
            for_update=False,
        ).name
        if item_code
        else None
    )
    new_item.custom_product_type = item_code[2:3] if item_code else None

    if item_code and int(item_code[2:3]) != 3:
        new_item.is_stock_item = 1
    else:
        new_item.is_stock_item = 0

    new_item.custom_item_code_etims = item["item_code"]
    new_item.valuation_rate = item["unit_price"]

    if "imported_item" in item:
        new_item.is_stock_item = 1
        new_item.custom_referenced_imported_item = item["imported_item"]

    new_item.insert(ignore_mandatory=True, ignore_if_duplicate=True)

    return new_item


@frappe.whitelist()
def create_purchase_invoice_from_request(request_data: str) -> None:
    data = json.loads(request_data)

    if not data.get("company_name"):
        data["company_name"] = frappe.defaults.get_user_default(
            "Company"
        ) or frappe.get_value("Company", {}, "name")

    # Check if supplier exists
    supplier = None
    if not frappe.db.exists("Supplier", data["supplier_name"], cache=False):
        supplier = create_supplier(data).name

    all_items = []
    all_existing_items = {
        item["name"]: item for item in frappe.db.get_all("Item", ["*"])
    }

    for received_item in data["items"]:
        # Check if item exists
        if received_item["item_name"] not in all_existing_items:
            created_item = create_item(received_item)
            all_items.append(created_item)

    set_warehouse = frappe.get_value(
        "Warehouse",
        {"custom_branch": data["branch"]},
        ["name"],
        as_dict=True,
    )

    if not set_warehouse:
        set_warehouse = frappe.get_value(
            "Warehouse", {"is_group": 0, "company": data["company_name"]}, "name"
        )  # use first warehouse match if not available for the branch

    # Create the Purchase Invoice
    purchase_invoice = frappe.new_doc("Purchase Invoice")
    purchase_invoice.supplier = supplier or data["supplier_name"]
    purchase_invoice.supplier = supplier or data["supplier_name"]
    purchase_invoice.update_stock = 1
    purchase_invoice.set_warehouse = set_warehouse
    purchase_invoice.branch = data["branch"]
    purchase_invoice.company = data["company_name"]
    purchase_invoice.custom_slade_organisation = data["organisation"]
    purchase_invoice.bill_no = data["supplier_invoice_no"]
    purchase_invoice.bill_date = data["supplier_invoice_date"]
    purchase_invoice.bill_date = data["supplier_invoice_date"]

    if "currency" in data:
        # The "currency" key is only available when creating from Imported Item
        purchase_invoice.currency = data["currency"]
        purchase_invoice.custom_source_registered_imported_item = data["name"]
    else:
        purchase_invoice.custom_source_registered_purchase = data["name"]

    if "exchange_rate" in data:
        purchase_invoice.conversion_rate = data["exchange_rate"]

    purchase_invoice.set("items", [])

    # TODO: Remove Hard-coded values
    purchase_invoice.custom_purchase_type = "Copy"
    purchase_invoice.custom_receipt_type = "Purchase"
    purchase_invoice.custom_payment_type = "CASH"
    purchase_invoice.custom_purchase_status = "Approved"

    company_abbr = frappe.get_value(
        "Company", {"name": frappe.defaults.get_user_default("Company")}, ["abbr"]
    )
    expense_account = frappe.db.get_value(
        "Account",
        {
            "name": [
                "like",
                f"%Cost of Goods Sold%{company_abbr}",
            ]
        },
        ["name"],
    )

    for item in data["items"]:
        matching_item = frappe.get_all(
            "Item",
            filters={
                "item_name": item["item_name"],
                "custom_item_classification": item["item_classification_code"],
            },
            fields=["name"],
        )
        item_code = matching_item[0]["name"]
        purchase_invoice.append(
            "items",
            {
                "item_name": item["item_name"],
                "item_code": item_code,
                "qty": item["quantity"],
                "rate": item["unit_price"],
                "expense_account": expense_account,
                "custom_item_classification": item["item_classification_code"],
                "custom_packaging_unit": item["packaging_unit_code"],
                "custom_unit_of_quantity": item["quantity_unit_code"],
                "custom_taxation_type": item["taxation_type_code"],
            },
        )

    purchase_invoice.insert(ignore_mandatory=True)

    frappe.msgprint("Purchase Invoices have been created")


@frappe.whitelist()
def ping_server(request_data: str) -> None:
    data = json.loads(request_data)
    server_url = data.get("server_url")
    auth_url = data.get("auth_url")

    async def check_server(url: str) -> tuple:
        try:
            response = await make_get_request(url)
            return "Online", response
        except aiohttp.client_exceptions.ClientConnectorError:
            return "Offline", None

    async def main() -> None:
        server_status, server_response = await check_server(server_url)
        auth_status, auth_response = await check_server(auth_url)

        if server_response:
            frappe.msgprint(f"Server Status: {server_status}\n{server_response}")
        else:
            frappe.msgprint(f"Server Status: {server_status}")

        frappe.msgprint(f"Auth Server Status: {auth_status}")

    asyncio.run(main())


@frappe.whitelist()
def create_stock_entry_from_stock_movement(request_data: str) -> None:
    data = json.loads(request_data)

    for item in data["items"]:
        if not frappe.db.exists("Item", item["item_name"], cache=False):
            # Create item if item doesn't exist
            create_item(item)

    # Create stock entry
    stock_entry = frappe.new_doc("Stock Entry")
    stock_entry.stock_entry_type = "Material Transfer"

    stock_entry.set("items", [])

    source_warehouse = frappe.get_value(
        "Warehouse",
        {"custom_branch": data["branch_id"]},
        ["name"],
        as_dict=True,
    )

    target_warehouse = frappe.get_value(
        "Warehouse",
        {"custom_branch": "01"},  # TODO: Fix hardcode from 01 to a general solution
        ["name"],
        as_dict=True,
    )

    for item in data["items"]:
        stock_entry.append(
            "items",
            {
                "s_warehouse": source_warehouse.name,
                "t_warehouse": target_warehouse.name,
                "item_code": item["item_name"],
                "qty": item["quantity"],
            },
        )

    stock_entry.save(ignore_permissions=True)

    frappe.msgprint(f"Stock Entry {stock_entry.name} created successfully")


@frappe.whitelist()
def initialize_device(request_data: str) -> None:
    return process_request(
        request_data,
        "DeviceVerificationReq",
        initialize_device_submission_on_success,
        request_method="POST",
        doctype=SETTINGS_DOCTYPE_NAME,
    )


@frappe.whitelist()
def get_invoice_details(
    id: str, document_name: str, invoice_type: str = "Sales Invoice"
) -> None:
    request_data = {"id": id, "document_name": document_name}
    invoice = frappe.get_doc(invoice_type, document_name)
    route_key = "TrnsSalesSearchReq"
    if invoice.is_return:
        route_key = "SalesCreditNoteSaveReq"
    process_request(
        request_data,
        route_key,
        update_invoice_info,
        doctype=invoice_type,
    )


@frappe.whitelist()
def save_uom_category_details(name: str) -> dict | None:
    item = frappe.get_doc(UOM_CATEGORY_DOCTYPE_NAME, name)

    slade_id = item.get("slade_id", None)

    request_data = {
        "name": item.get("category_name"),
        "document_name": item.get("name"),
        "measure_type": item.get("measure_type"),
        "active": True if item.get("active") == 1 else False,
    }

    if slade_id:
        request_data["id"] = slade_id
        process_request(
            request_data,
            "UOMCategoriesSearchReq",
            uom_category_search_on_success,
            request_method="PATCH",
            doctype=UOM_CATEGORY_DOCTYPE_NAME,
        )
    else:
        process_request(
            request_data,
            "UOMCategoriesSearchReq",
            uom_category_search_on_success,
            request_method="POST",
            doctype=UOM_CATEGORY_DOCTYPE_NAME,
        )


@frappe.whitelist()
def sync_uom_category_details(request_data: str) -> None:
    process_request(
        request_data,
        "UOMCategorySearchReq",
        uom_category_search_on_success,
        doctype=UOM_CATEGORY_DOCTYPE_NAME,
    )


@frappe.whitelist()
def save_uom_details(name: str) -> dict | None:
    item = frappe.get_doc("UOM", name)

    slade_id = item.get("slade_id", None)

    request_data = {
        "name": item.get("uom_name"),
        "document_name": item.get("name"),
        "factor": item.get("custom_factor"),
        "uom_type": item.get("custom_uom_type"),
        "category": get_link_value(
            UOM_CATEGORY_DOCTYPE_NAME,
            "name",
            item.get("custom_category"),
            "slade_id",
        ),
        "active": True if item.get("active") == 1 else False,
    }

    if slade_id:
        request_data["id"] = slade_id
        process_request(
            request_data,
            "UOMListSearchReq",
            uom_search_on_success,
            request_method="PATCH",
            doctype="UOM",
        )
    else:
        process_request(
            request_data,
            "UOMListSearchReq",
            uom_search_on_success,
            request_method="POST",
            doctype="UOM",
        )


@frappe.whitelist()
def sync_uom_details(request_data: str) -> None:
    process_request(
        request_data,
        "UOMDetailSearchReq",
        uom_search_on_success,
        doctype="UOM",
    )


@frappe.whitelist()
def submit_uom_list() -> dict | None:
    uoms = frappe.get_all(
        "UOM", filters={"custom_slade_id": ["is", "not set"]}, fields=["name"]
    )
    request_data = []
    for uom in uoms:
        item = frappe.get_doc("UOM", uom.name)
        category = item.get("custom_category") or "Unit"
        item_data = {
            "name": item.get("uom_name"),
            "factor": item.get("custom_factor"),
            "uom_type": item.get("custom_uom_type") or "reference",
            "category": get_link_value(
                UOM_CATEGORY_DOCTYPE_NAME,
                "name",
                category,
                "slade_id",
            ),
            "active": True if item.get("active") == 1 else False,
        }
        request_data.append(item_data)

    process_request(
        request_data,
        "UOMListSearchReq",
        uom_search_on_success,
        request_method="POST",
        doctype="UOM",
    )


@frappe.whitelist()
def submit_pricelist(name: str) -> dict | None:
    item = frappe.get_doc("Price List", name)
    slade_id = item.get("custom_slade_id", None)

    route_key = "PriceListsSearchReq"
    on_success = pricelist_update_on_success

    # pricelist_type is mandatory for the request and cannot accept both selling and buying
    pricelist_type = (
        "selling"
        if item.get("selling") == 1
        else "purchases" if item.get("buying") == 1 else "selling"
    )
    request_data = {
        "name": item.get("price_list_name"),
        "document_name": item.get("name"),
        "pricelist_status": item.get("custom_pricelist_status"),
        "pricelist_type": pricelist_type,
        "organisation": get_link_value(
            "Company",
            "name",
            item.get("custom_company"),
            "custom_slade_id",
        ),
        "active": False if item.get("enabled") == 0 else True,
    }

    if item.get("custom_warehouse"):
        request_data["location"] = get_link_value(
            "Warehouse",
            "name",
            item.get("custom_warehouse"),
            "custom_slade_id",
        )

    if item.get("custom_effective_from"):
        request_data["effective_from"] = item.get("custom_effective_from").strftime(
            "%Y-%m-%d"
        )

    if item.get("custom_effective_to"):
        request_data["effective_to"] = item.get("custom_effective_to").strftime(
            "%Y-%m-%d"
        )

    if slade_id:
        request_data["id"] = slade_id
        method = "PATCH"
    else:
        method = "POST"

    process_request(
        request_data,
        route_key=route_key,
        handler_function=on_success,
        request_method=method,
        doctype="Price List",
    )


@frappe.whitelist()
def sync_pricelist(request_data: str) -> None:
    process_request(
        request_data,
        "PriceListSearchReq",
        pricelist_update_on_success,
        doctype="Price List",
    )


@frappe.whitelist()
def submit_item_price(name: str) -> dict | None:
    item = frappe.get_doc("Item Price", name)
    slade_id = item.get("custom_slade_id", None)
    item_code = item.get("item_code", None)
    item_name = item.get("name", None)

    route_key = "ItemPricesSearchReq"
    on_success = item_price_update_on_success

    request_data = {
        "name": f"{item_code} - {item_name}",
        "document_name": item_name,
        "price_inclusive_tax": item.get("price_list_rate"),
        "organisation": get_link_value(
            "Company",
            "name",
            item.get("custom_company"),
            "custom_slade_id",
        ),
        "product": get_link_value(
            "Item",
            "name",
            item_code,
            "custom_slade_id",
        ),
        "currency": get_link_value(
            "Currency",
            "name",
            item.get("currency"),
            "custom_slade_id",
        ),
        "pricelist": get_link_value(
            "Price List",
            "name",
            item.get("price_list"),
            "custom_slade_id",
        ),
        "active": False if item.get("enabled") == 0 else True,
    }

    if slade_id:
        request_data["id"] = slade_id
        method = "PATCH"
    else:
        method = "POST"

    process_request(
        request_data,
        route_key=route_key,
        handler_function=on_success,
        request_method=method,
        doctype="Item Price",
    )


@frappe.whitelist()
def sync_item_price(request_data: str) -> None:
    process_request(
        request_data,
        "ItemPriceSearchReq",
        item_price_update_on_success,
        doctype="Item Price",
    )


@frappe.whitelist()
def save_operation_type(name: str) -> dict | None:
    item = frappe.get_doc(OPERATION_TYPE_DOCTYPE_NAME, name)
    slade_id = item.get("slade_id", None)

    route_key = "OperationTypesReq"
    if item.get("destination_location") and item.get("source_location"):
        request_data = {
            "operation_name": item.get("operation_name"),
            "document_name": item.get("name"),
            "operation_type": item.get("operation_type"),
            "organisation": get_link_value(
                "Company",
                "name",
                item.get("company"),
                "custom_slade_id",
            ),
            "destination_location": item.get("destination_location"),
            "source_location": item.get("source_location"),
            "active": False if item.get("active") == 0 else True,
        }

        if slade_id:
            request_data["id"] = slade_id
            method = "PATCH"
        else:
            method = "POST"

        process_request(
            request_data,
            route_key=route_key,
            handler_function=operation_types_search_on_success,
            request_method=method,
            doctype=OPERATION_TYPE_DOCTYPE_NAME,
        )
    return None


@frappe.whitelist()
def sync_operation_type(request_data: str) -> None:
    process_request(
        request_data,
        "OperationTypeReq",
        operation_types_search_on_success,
        doctype=OPERATION_TYPE_DOCTYPE_NAME,
    )


@frappe.whitelist()
def send_all_mode_of_payments() -> None:
    mode_of_payments = frappe.get_all(
        "Mode of Payment",
        filters={"custom_slade_id": ["is", "not set"]},
        fields=["name"],
    )
    for mop in mode_of_payments:
        frappe.enqueue(send_mode_of_payment_details, name=mop.name)


@frappe.whitelist()
def send_mode_of_payment_details(name: str) -> dict | None:
    route_key = "AccountsSearchReq"
    on_success = reaceavable_accouct_search_on_success
    # fetch the reaceavable account to link to the mode of payment
    request_data = {
        "number": "1000-0001",
        "document_name": name,
    }

    process_request(
        request_data,
        route_key=route_key,
        handler_function=on_success,
        request_method="GET",
        doctype="Mode of Payment",
    )


def reaceavable_accouct_search_on_success(
    response: dict, document_name: str, **kwargs
) -> None:
    if isinstance(response, str):
        try:
            response = json.loads(response)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON string: {response}")

    account = (
        response if isinstance(response, list) else response.get("results", [response])
    )[0]

    mode_of_payment = frappe.get_doc("Mode of Payment", document_name)

    request_data = {
        "account": account.get("id"),
        "name": mode_of_payment.get("mode_of_payment"),
        "organisation": account.get("organisation"),
        "document_name": document_name,
    }

    process_request(
        request_data,
        route_key="PaymentMtdSearchReq",
        handler_function=mode_of_payment_on_success,
        request_method="POST",
        doctype="Mode of Payment",
    )
