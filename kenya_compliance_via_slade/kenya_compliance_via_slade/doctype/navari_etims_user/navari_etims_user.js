// Copyright (c) 2024, Navari Ltd and contributors
// For license information, please see license.txt

const doctypeName = "Navari eTims User";

frappe.ui.form.on(doctypeName, {
  refresh: async function (frm) {
    const companyName = frappe.boot.sysdefaults.company;

    if (!frm.is_new()) {
      if (!frm.doc.slade_id) {
        frm.add_custom_button(
          __("Submit Branch User Details"),
          function () {
            frappe.call({
              method:
                "kenya_compliance_via_slade.kenya_compliance_via_slade.apis.apis.save_branch_user_details",
              args: {
                request_data: {
                  document_name: frm.doc.name,
                  company_name: companyName,
                  user_id: frm.doc.system_user,
                  first_name: frm.doc.first_name,
                  last_name: frm.doc.last_name,
                  email: frm.doc.email,
                  description: frm.doc.description,
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
      } else {
        frm.add_custom_button(
          __("Get Branch User Details"),
          function () {
            frappe.call({
              method:
                "kenya_compliance_via_slade.kenya_compliance_via_slade.apis.apis.get_branch_user_details",
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
