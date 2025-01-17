const doctype = "Customer";

frappe.ui.form.on(doctype, {
  refresh: async function (frm) {
    const companyName = frappe.boot.sysdefaults.company;
    let currency = frm.doc.default_currency || "KES";

    frappe.call({
      method: "frappe.client.get_value",
      args: {
        doctype: "Currency",
        fieldname: "name",
        filters: { name: currency },
      },
      callback: function (r) {
        if (r.message) {
          currency = r.message.name;
        }
      },
    });

    if (!frm.is_new()) {
      if (frm.doc.tax_id) {
        frm.add_custom_button(
          __("Perform Customer Search"),
          function () {
            frappe.call({
              method:
                "kenya_compliance_via_slade.kenya_compliance_via_slade.apis.apis.perform_customer_search",
              args: {
                request_data: {
                  doc_name: frm.doc.name,
                  customer_pin: frm.doc.tax_id,
                  company_name: companyName,
                },
              },
              callback: (response) => {
                frappe.msgprint("Search queued. Please check in later.");
              },
              error: (r) => {
                // Error Handling is Defered to the Server
              },
            });
          },
          __("eTims Actions")
        );
      }
      if (!frm.doc.slade_id) {
        frm.add_custom_button(
          __("Send Customer Details"),
          function () {
            frappe.call({
              method:
                "kenya_compliance_via_slade.kenya_compliance_via_slade.apis.apis.send_branch_customer_details",
              args: {
                request_data: {
                  document_name: frm.doc.name,
                  customer_tax_pin: frm.doc.tax_id,
                  partner_name: frm.doc.customer_name,
                  phone_number: frm.doc.mobile_no,
                  currency: currency,
                  is_customer: true,
                  country: "KEN",
                  customer_type: "INDIVIDUAL",
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
      } else {
        frm.add_custom_button(
          __("Get Customer Detals"),
          function () {
            frappe.call({
              method:
                "kenya_compliance_via_slade.kenya_compliance_via_slade.apis.apis.get_customer_details",
              args: {
                request_data: {
                  doc_name: frm.doc.name,
                  id: frm.doc.slade_id,
                  company_name: companyName,
                },
              },
              callback: (response) => {
                frappe.msgprint("Search queued. Please check in later.");
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
  customer_group: function (frm) {
    frappe.db.get_value(
      "Customer Group",
      {
        name: frm.doc.customer_group,
      },
      ["custom_insurance_applicable"],
      (response) => {
        const customerGroupInsuranceApplicable =
          response.custom_insurance_applicable;

        if (customerGroupInsuranceApplicable) {
          frappe.msgprint(
            `The Customer Group ${frm.doc.customer_group} has Insurance Applicable on. Please fill the relevant insurance fields under Tax tab`
          );
          frm.toggle_reqd("custom_insurance_code", true);
          frm.toggle_reqd("custom_insurance_name", true);
          frm.toggle_reqd("custom_premium_rate", true);

          frm.set_value("custom_insurance_applicable", 1);
        } else {
          frm.toggle_reqd("custom_insurance_code", false);
          frm.toggle_reqd("custom_insurance_name", false);
          frm.toggle_reqd("custom_premium_rate", false);

          frm.set_value("custom_insurance_applicable", 0);
        }
      }
    );
  },
});
