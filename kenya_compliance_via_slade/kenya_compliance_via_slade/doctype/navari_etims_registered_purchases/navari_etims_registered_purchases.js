// Copyright (c) 2024, Navari Ltd and contributors
// For license information, please see license.txt
const doctypeName = "Navari eTims Registered Purchases";

frappe.ui.form.on(doctypeName, {
  refresh: function (frm) {
    let companyName = frappe.boot.sysdefaults.company;

    if (!companyName) {
      frappe.call({
        method: "frappe.client.get_list",
        args: {
          doctype: "Company",
          fields: ["name"],
          limit_page_length: 1,
        },
        callback: function (response) {
          if (response.message && response.message.length > 0) {
            companyName = response.message[0].name;
          }
        },
      });
    }

    if (!frm.is_new()) {
      frm.add_custom_button(
        __("Create Supplier"),
        function () {
          frappe.call({
            method:
              "kenya_compliance_via_slade.kenya_compliance_via_slade.apis.apis.create_supplier_from_fetched_registered_purchases",
            args: {
              request_data: {
                name: frm.doc.name,
                company_name: companyName,
                supplier_name: frm.doc.supplier_name,
                supplier_pin: frm.doc.supplier_pin,
                supplier_branch_id: frm.doc.supplier_branch_id,
              },
            },
            callback: (response) => {},
            error: (error) => {
              // Error Handling is Defered to the Server
            },
          });
        },
        __("eTims Actions")
      );
      frm.add_custom_button(
        __("Create Items"),
        function () {
          frappe.call({
            method:
              "kenya_compliance_via_slade.kenya_compliance_via_slade.apis.apis.create_items_from_fetched_registered",
            args: {
              request_data: {
                name: frm.doc.name,
                company_name: companyName,
                items: frm.doc.items,
              },
            },
            callback: (response) => {},
            error: (error) => {
              // Error Handling is Defered to the Server
            },
          });
        },
        __("eTims Actions")
      );
      frm.add_custom_button(
        __("Create Purchase Invoice"),
        function () {
          frappe.call({
            method:
              "kenya_compliance_via_slade.kenya_compliance_via_slade.apis.apis.create_purchase_invoice_from_request",
            args: {
              request_data: {
                name: frm.doc.name,
                company_name: companyName,
                supplier_name: frm.doc.supplier_name,
                supplier_pin: frm.doc.supplier_pin,
                supplier_branch_id: frm.doc.supplier_branch_id,
                branch: frm.doc.branch,
                organisation: frm.doc.organisation,
                supplier_invoice_no: frm.doc.supplier_invoice_number,
                supplier_invoice_date: frm.doc.sales_date,
                items: frm.doc.items,
              },
            },
            callback: (response) => {},
            error: (error) => {
              // Error Handling is Defered to the Server
            },
          });
        },
        __("eTims Actions")
      );

      frm.add_custom_button(
        __("Fetch Registered Purchase Details"),
        function () {
          frappe.call({
            method:
              "kenya_compliance_via_slade.kenya_compliance_via_slade.apis.apis.perform_purchase_search",
            args: {
              request_data: {
                id: frm.doc.name,
                document_name: frm.doc.name,
                company_name: companyName,
              },
            },
            callback: (response) => {},
            error: (error) => {
              // Error Handling is Defered to the Server
            },
          });
        },
        __("eTims Actions")
      );
      // frm.add_custom_button(
      //   __("Create Purchase Receipt"),
      //   function () {
      //     frappe.call({
      //       method: null,
      //       args: {
      //         request_data: {
      //           name: frm.doc.name,
      //           company_name: companyName,
      //           supplier_name: frm.doc.supplier_name,
      //           supplier_pin: frm.doc.supplier_pin,
      //           items: frm.doc.items,
      //         },
      //       },
      //       callback: (response) => {},
      //       error: (error) => {
      //         // Error Handling is Defered to the Server
      //       },
      //     });
      //   },
      //   __("eTims Actions")
      // );
    }
  },
});
