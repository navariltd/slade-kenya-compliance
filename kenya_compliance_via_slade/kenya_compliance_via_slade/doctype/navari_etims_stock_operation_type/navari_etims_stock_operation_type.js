// Copyright (c) 2025, Navari Ltd and contributors
// For license information, please see license.txt

const doctypeName = "Navari eTims Stock Operation Type";

frappe.ui.form.on(doctypeName, {
  refresh: async function (frm) {
    const companyName = frappe.boot.sysdefaults.company;

    if (!frm.is_new()) {
      const submit_name = !frm.doc.slade_id
        ? "Submit Stock Operation Type"
        : "Update Stock Operation Type";
      frm.add_custom_button(
        __(submit_name),
        function () {
          frappe.call({
            method:
              "kenya_compliance_via_slade.kenya_compliance_via_slade.apis.apis.save_operation_type",
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
      if (frm.doc.slade_id) {
        frm.add_custom_button(
          __("Fetch Stock Operation Type"),
          function () {
            frappe.call({
              method:
                "kenya_compliance_via_slade.kenya_compliance_via_slade.apis.apis.sync_operation_type",
              args: {
                request_data: {
                  document_name: frm.doc.name,
                  id: frm.doc.slade_id,
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
  },
});
