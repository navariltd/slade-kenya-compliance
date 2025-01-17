// Copyright (c) 2025, Navari Ltd and contributors
// For license information, please see license.txt

const doctypeName = "Warehouse";

frappe.ui.form.on(doctypeName, {
  refresh: async function (frm) {
    const companyName = frappe.boot.sysdefaults.company;
    const { message: activeSetting } = await frappe.db.get_value(
      settingsDoctypeName,
      { is_active: 1 },
      "name"
    );

    if (activeSetting?.name) {
      if (!frm.is_new()) {
        const submit_name = !frm.doc.custom_slade_id
          ? "Submit Warehouse"
          : "Update Warehouse";
        frm.add_custom_button(
          __(submit_name),
          function () {
            frappe.call({
              method:
                "kenya_compliance_via_slade.kenya_compliance_via_slade.apis.apis.save_warehouse_details",
              args: {
                name: frm.doc.name,
              },
              callback: (response) => {
                frappe.msgprint("Request queued. Please check in later.");
              },
              error: (r) => {
                // Error Handling is Defered to the Server
              },
            });
          },
          __("eTims Actions")
        );
        const type = frm.doc.is_group ? "warehouse" : "location";
        if (frm.doc.custom_slade_id) {
          frm.add_custom_button(
            __("Fetch Warehouse Details"),
            function () {
              frappe.call({
                method:
                  "kenya_compliance_via_slade.kenya_compliance_via_slade.apis.apis.sync_warehouse_details",
                args: {
                  request_data: {
                    document_name: frm.doc.name,
                    id: frm.doc.custom_slade_id,
                  },
                  type: type,
                },
                callback: (response) => {
                  frappe.msgprint("Request queued. Please check in later.");
                },
                error: (r) => {
                  // Error Handling is Defered to the Server
                },
              });
            },
            __("eTims Actions")
          );
        }
      }
    }
  },
});
