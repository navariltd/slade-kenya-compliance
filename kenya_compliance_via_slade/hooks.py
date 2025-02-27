from .kenya_compliance_via_slade.doctype.doctype_names_mapping import (
    IMPORTED_ITEMS_STATUS_DOCTYPE_NAME,
    ITEM_TYPE_DOCTYPE_NAME,
    PRODUCT_TYPE_DOCTYPE_NAME,
    PURCHASE_RECEIPT_DOCTYPE_NAME,
    ROUTES_TABLE_DOCTYPE_NAME,
    TRANSACTION_PROGRESS_DOCTYPE_NAME,
    TRANSACTION_TYPE_DOCTYPE_NAME,
)

app_name = "kenya_compliance_via_slade"
app_title = "Kenya Compliance (KRA eTIMS)"
app_publisher = "Navari Ltd"
app_description = "This app works to integrate ERPNext with KRA's eTIMS via Slade360 Advantage to allow for the sharing of information with the revenue authority."
app_email = "solutions@navari.co.ke"
app_license = "GNU Affero General Public License v3.0"
required_apps = ["frappe/erpnext"]


# Fixtures
# --------
fixtures = [
    {"dt": TRANSACTION_TYPE_DOCTYPE_NAME},
    {"dt": PURCHASE_RECEIPT_DOCTYPE_NAME},
    {"dt": IMPORTED_ITEMS_STATUS_DOCTYPE_NAME},
    {"dt": ROUTES_TABLE_DOCTYPE_NAME},
    {"dt": ITEM_TYPE_DOCTYPE_NAME},
    {
        "dt": PRODUCT_TYPE_DOCTYPE_NAME,
    },
    {
        "dt": TRANSACTION_PROGRESS_DOCTYPE_NAME,
        "filters": [
            [
                "name",
                "in",
                (
                    "Wait for Approval",
                    "Approved",
                    "Cancel Requested",
                    "Canceled",
                    "Credit Note Generated",
                    "Transferred",
                ),
            ]
        ],
    },
]
# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/kenya_compliance_via_slade/css/kenya_compliance_via_slade.css"
# app_include_js = "/assets/kenya_compliance_via_slade/js/kenya_compliance_via_slade.js"

# include js, css files in header of web template
# web_include_css = "/assets/kenya_compliance_via_slade/css/kenya_compliance_via_slade.css"
# web_include_js = "/assets/kenya_compliance_via_slade/js/kenya_compliance_via_slade.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "kenya_compliance_via_slade/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Sales Invoice": "kenya_compliance_via_slade/overrides/client/sales_invoice.js",
    "Purchase Invoice": "kenya_compliance_via_slade/overrides/client/purchase_invoice.js",
    "Customer": "kenya_compliance_via_slade/overrides/client/customer.js",
    "Supplier": "kenya_compliance_via_slade/overrides/client/supplier.js",
    "Item": "kenya_compliance_via_slade/overrides/client/items.js",
    "BOM": "kenya_compliance_via_slade/overrides/client/bom.js",
    "Branch": "kenya_compliance_via_slade/overrides/client/branch.js",
    "UOM": "kenya_compliance_via_slade/overrides/client/uom.js",
    # "Warehouse": "kenya_compliance_via_slade/overrides/client/warehouse.js",
    "Mode of Payment": "kenya_compliance_via_slade/overrides/client/mode_of_payment.js",
    # "Price List": "kenya_compliance_via_slade/overrides/client/price_list.js",
    # "Item Price": "kenya_compliance_via_slade/overrides/client/item_price.js",
}

doctype_list_js = {
    "Item": "kenya_compliance_via_slade/overrides/client/items_list.js",
    "Sales Invoice": "kenya_compliance_via_slade/overrides/client/sales_invoice_list.js",
    "Branch": "kenya_compliance_via_slade/overrides/client/branch_list.js",
    "Customer": "kenya_compliance_via_slade/overrides/client/customer_list.js",
    "UOM": "kenya_compliance_via_slade/overrides/client/uom_list.js",
    # "Warehouse": "kenya_compliance_via_slade/overrides/client/warehouse_list.js",
    "Mode of Payment": "kenya_compliance_via_slade/overrides/client/mode_of_payment_list.js",
    "Supplier": "kenya_compliance_via_slade/overrides/client/supplier_list.js",
    # "Price List": "kenya_compliance_via_slade/overrides/client/price_list_list.js",
    # "Item Price": "kenya_compliance_via_slade/overrides/client/item_price_list.js",
}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "kenya_compliance_via_slade/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "kenya_compliance_via_slade.utils.jinja_methods",
# 	"filters": "kenya_compliance_via_slade.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "kenya_compliance_via_slade.install.before_install"
# after_install = "kenya_compliance_via_slade.kenya_compliance_via_slade.setup.after_install.after_install"

# Uninstallation
# ------------

# before_uninstall = "kenya_compliance_via_slade.uninstall.before_uninstall"
# after_uninstall = (
#     "kenya_compliance_via_slade.kenya_compliance_via_slade.setup.after_uninstall.after_uninstall"
# )

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "kenya_compliance_via_slade.utils.before_app_install"
# after_app_install = "kenya_compliance_via_slade.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "kenya_compliance_via_slade.utils.before_app_uninstall"
# after_app_uninstall = "kenya_compliance_via_slade.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "kenya_compliance_via_slade.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    # 	"*": {
    # 		"on_update": "method",
    # 		"on_cancel": "method",
    # 		"on_trash": "method"
    # 	}
    "Sales Invoice": {
        "before_save": [
            "kenya_compliance_via_slade.kenya_compliance_via_slade.utils.before_save_"
        ],
        "on_submit": [
            "kenya_compliance_via_slade.kenya_compliance_via_slade.overrides.server.sales_invoice.on_submit"
        ],
        "validate": [
            "kenya_compliance_via_slade.kenya_compliance_via_slade.overrides.server.shared_overrides.validate"
        ],
        "before_cancel": [
            "kenya_compliance_via_slade.kenya_compliance_via_slade.overrides.server.sales_invoice.before_cancel"
        ],
    },
    "Purchase Invoice": {
        "before_save": [
            "kenya_compliance_via_slade.kenya_compliance_via_slade.utils.before_save_"
        ],
        "on_submit": [
            "kenya_compliance_via_slade.kenya_compliance_via_slade.overrides.server.purchase_invoice.on_submit"
        ],
        "validate": [
            "kenya_compliance_via_slade.kenya_compliance_via_slade.overrides.server.purchase_invoice.validate"
        ],
        "before_cancel": [
            "kenya_compliance_via_slade.kenya_compliance_via_slade.overrides.server.sales_invoice.before_cancel"
        ],
    },
    "Item": {
        "validate": [
            "kenya_compliance_via_slade.kenya_compliance_via_slade.overrides.server.item.validate"
        ],
        "on_update": [
            "kenya_compliance_via_slade.kenya_compliance_via_slade.overrides.server.item.on_update"
        ],
        "on_trash": "kenya_compliance_via_slade.kenya_compliance_via_slade.overrides.server.item.prevent_item_deletion",
    },
    "BOM": {
        "on_submit": [
            "kenya_compliance_via_slade.kenya_compliance_via_slade.overrides.server.bom.on_submit"
        ]
    },
    "Supplier": {
        "on_update": [
            "kenya_compliance_via_slade.kenya_compliance_via_slade.overrides.server.supplier.on_update"
        ],
    },
    "Customer": {
        "on_update": [
            "kenya_compliance_via_slade.kenya_compliance_via_slade.overrides.server.customer.on_update"
        ],
    },
}

# Scheduled Tasks
# ---------------

scheduler_events = {
    "daily": [
        "kenya_compliance_via_slade.kenya_compliance_via_slade.background_tasks.tasks.refresh_notices",
    ],
    "hourly": [
        # "kenya_compliance_via_slade.kenya_compliance_via_slade.background_tasks.tasks.send_sales_invoices_information",
        # "kenya_compliance_via_slade.kenya_compliance_via_slade.background_tasks.tasks.send_purchase_information",
        # "kenya_compliance_via_slade.kenya_compliance_via_slade.background_tasks.tasks.send_stock_information",
    ],
    "monthly": [
        "kenya_compliance_via_slade.kenya_compliance_via_slade.background_tasks.tasks.refresh_code_lists",
        # "kenya_compliance_via_slade.kenya_compliance_via_slade.background_tasks.tasks.search_organisations_request",
        "kenya_compliance_via_slade.kenya_compliance_via_slade.background_tasks.tasks.get_item_classification_codes",
    ],
}

# Testing
# -------

# before_tests = "kenya_compliance_via_slade.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "kenya_compliance_via_slade.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "kenya_compliance_via_slade.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["kenya_compliance_via_slade.utils.before_request"]
# after_request = ["kenya_compliance_via_slade.utils.after_request"]

# Job Events
# ----------
# before_job = ["kenya_compliance_via_slade.utils.before_job"]
# after_job = ["kenya_compliance_via_slade.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"kenya_compliance_via_slade.auth.validate"
# ]
