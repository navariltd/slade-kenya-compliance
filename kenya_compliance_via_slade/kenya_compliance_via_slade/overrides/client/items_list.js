const doctypeName = "Item";
const settingsDoctypeName = "Navari KRA eTims Settings";

frappe.listview_settings[doctypeName].onload = async function (listview) {
  const companyName = frappe.boot.sysdefaults.company;
  const { message: activeSetting } = await frappe.db.get_value(
    settingsDoctypeName,
    { is_active: 1 },
    "name"
  );

  if (activeSetting?.name) {
    listview.page.add_inner_button(
      __("Get Imported Items"),
      function (listview) {
        frappe.call({
          method:
            "kenya_compliance_via_slade.kenya_compliance_via_slade.apis.apis.perform_import_item_search",
          args: {
            request_data: {
              company_name: companyName,
            },
          },
          callback: (response) => {},
          error: (r) => {
            // Error Handling is Defered to the Server
          },
        });
      },
      __("eTims Actions")
    );

    listview.page.add_inner_button(
      __("Get Registered Items"),
      function (listview) {
        frappe.call({
          method:
            "kenya_compliance_via_slade.kenya_compliance_via_slade.apis.apis.perform_item_search",
          args: {
            request_data: {
              company_name: companyName,
              // sent_to_etims: true,
            },
          },
          callback: (response) => {},
          error: (r) => {
            // Error Handling is Defered to the Server
          },
        });
      },
      __("eTims Actions")
    );

    listview.page.add_inner_button(
      __("Submit Inventory"),
      function (listview) {
        frappe.call({
          method:
            "kenya_compliance_via_slade.kenya_compliance_via_slade.apis.apis.send_entire_stock_balance",
          args: {},
          callback: (response) => {},
          error: (r) => {
            // Error Handling is Defered to the Server
          },
        });
      },
      __("eTims Actions")
    );

    listview.page.add_inner_button(
      __("Register all Items"),
      function (listview) {
        frappe.call({
          method:
            "kenya_compliance_via_slade.kenya_compliance_via_slade.apis.apis.register_all_items",
          args: {},
          callback: (response) => {},
          error: (r) => {
            // Error Handling is Defered to the Server
          },
        });
      },
      __("eTims Actions")
    );

    listview.page.add_action_item(__("Bulk Register Items"), function () {
      const itemsToRegister = listview
        .get_checked_items()
        .map((item) => item.name);

      frappe.call({
        method:
          "kenya_compliance_via_slade.kenya_compliance_via_slade.apis.apis.bulk_register_item",
        args: {
          docs_list: itemsToRegister,
        },
        callback: (response) => {
          frappe.msgprint("Bulk submission queued.");
        },
        error: (r) => {
          // Error Handling is Defered to the Server
        },
      });
    });
  }
};
