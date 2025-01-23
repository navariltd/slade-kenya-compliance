// Copyright (c) 2025, Navari Ltd and contributors
// For license information, please see license.txt

const doctypeName = "Price List";
const settingsDoctypeName = "Navari KRA eTims Settings";

frappe.ui.form.on(doctypeName, {
  refresh: async function (frm) {
    const companyName = frappe.boot.sysdefaults.company;
    const { message: activeSetting } = await frappe.db.get_value(
      settingsDoctypeName,
      { is_active: 1 },
      "name"
    );

    if (activeSetting?.name) {
      frm.set_query("custom_warehouse", function () {
        return {
          filters: {
            is_group: 0,
          },
        };
      });

      if (!frm.is_new()) {
        const submit_name = !frm.doc.custom_slade_id
          ? "Submit Price List"
          : "Update Price List";
        frm.add_custom_button(
          __(submit_name),
          function () {
            frappe.call({
              method:
                "kenya_compliance_via_slade.kenya_compliance_via_slade.apis.apis.submit_pricelist",
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
        if (frm.doc.custom_slade_id) {
          frm.add_custom_button(
            __("Fetch Price List Details"),
            function () {
              frappe.call({
                method:
                  "kenya_compliance_via_slade.kenya_compliance_via_slade.apis.apis.sync_pricelist",
                args: {
                  request_data: {
                    document_name: frm.doc.name,
                    id: frm.doc.custom_slade_id,
                    company_name: companyName,
                  },
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
