const itemDoctypName = "Item";

frappe.ui.form.on(itemDoctypName, {
  refresh: function (frm) {
    const companyName = frappe.boot.sysdefaults.company;
    const branchName = frappe.boot.sysdefaults.branch;

    let organisation = "";
    let branch = "";
    frappe.call({
      method: "frappe.client.get",
      args: {
      doctype: "Company",
      name: companyName,
      },
      callback: function (response) {
      if (response && response.message) {
        organisation = response.message.custom_slade_id
      }
      },
    });

    frappe.call({
      method: "frappe.client.get",
      args: {
      doctype: "Branch",
      name: branchName,
      },
      callback: function (response) {
      if (response && response.message) {
        branch = response.message.slade_id
      }
      },
    });

    if (frm.doc.custom_item_registered) {
      frm.toggle_enable("custom_item_classification", false);
      frm.toggle_enable("custom_etims_country_of_origin", false);
      frm.toggle_enable("custom_taxation_type", false);
      frm.toggle_enable("custom_packaging_unit", false);
      frm.toggle_enable("custom_unit_of_quantity", false);
      frm.toggle_enable("custom_product_type", false);
    }

    if (frm.doc.custom_imported_item_submitted) {
      frm.toggle_enable("custom_referenced_imported_item", false);
      frm.toggle_enable("custom_imported_item_status", false);
    }

    if (!frm.is_new()) {
      if (
        !frm.doc.custom_item_registered &&
        frm.doc.custom_item_classification &&
        frm.doc.custom_taxation_type
      ) {
        frm.add_custom_button(
          __("Register Item"),
          function () {
            // call with all options
            frappe.call({
              method:
                "kenya_compliance_via_slade.kenya_compliance_via_slade.apis.apis.perform_item_registration",
              args: {
                item_name: frm.doc.name,
              },
              callback: (response) => {
                frappe.msgprint(
                  "Item Registration Queued. Please check in later."
                );
              },
              error: (error) => {
                // Error Handling is Defered to the Server
              },
            });
          },
          __("eTims Actions")
        );
      }
      // if (frm.doc.is_stock_item) {
      //   frm.add_custom_button(
      //     __('Submit Item Inventory'),
      //     function () {
      //       frappe.call({
      //         method:
      //           'kenya_compliance_via_slade.kenya_compliance_via_slade.apis.apis.submit_inventory',
      //         args: {
      //           request_data: {
      //             company_name: companyName,
      //             name: frm.doc.name,
      //             itemName: frm.doc.item_code,
      //             itemCd: frm.doc.custom_item_code_etims,
      //             registered_by: frm.doc.owner,
      //             modified_by: frm.doc.modified_by,
      //             // TODO: Fix the branch id below
      //             branch_id: '00',
      //           },
      //         },
      //         callback: (response) => {
      //           frappe.msgprint('Inventory submission queued.');
      //         },
      //         error: (error) => {
      //           // Error Handling is Defered to the Server
      //         },
      //       });
      //     },
      //     __('eTims Actions'),
      //   );
      // }

      //  TODO: Fix later. Need more clarification on this
      // if (
      //   frm.doc.custom_referenced_imported_item &&
      //   frm.doc.custom_item_classification &&
      //   frm.doc.custom_taxation_type
      // ) {

      //   if (
      //     !frm.doc.custom_imported_item_submitted ) {
      //       frm.add_custom_button(
      //         __("Submit Imported Item"),
      //         function () {
      //           frappe.call({
      //             method: "frappe.client.get",
      //             args: {
      //               doctype: "Navari eTims Registered Imported Item",
      //               name: frm.doc.custom_referenced_imported_item,
      //             },
      //             callback: function (response) {
      //               if (response && response.message) {
      //                 const referenced_item = response.message;

      //                 frappe.call({
      //                   method:
      //                     "kenya_compliance_via_slade.kenya_compliance_via_slade.apis.apis.send_imported_item_request",
      //                   args: {
      //                     request_data: {
      //                       company_name: companyName,
      //                       document_name: frm.doc.name,
      //                       item_name: frm.doc.item_name,
      //                       package: referenced_item.package,
      //                       quantity: referenced_item.quantity,
      //                       declaration_date: referenced_item.declaration_date,
      //                       organisation: organisation,
      //                       branch: branch,
      //                       product: frm.doc.custom_slade_id,
      //                     },
      //                   },
      //                   callback: function (apiResponse) {
      //                     if (apiResponse && apiResponse.message) {
      //                       frappe.msgprint("Request queued. Check later.");
      //                     }
      //                   },
      //                 });
      //               } else {
      //                 frappe.msgprint("Unable to fetch referenced item details.");
      //               }
      //             },
      //           });
      //         },
      //         __("eTims Actions")
      //       );

      //   } else {
      //     frm.add_custom_button(
      //       __("Update Imported Item"),
      //       function () {
      //         frappe.call({
      //           method: "frappe.client.get",
      //           args: {
      //             doctype: "Navari eTims Registered Imported Item",
      //             name: frm.doc.custom_referenced_imported_item,
      //           },
      //           callback: function (response) {
      //             if (response && response.message) {
      //               const referenced_item = response.message;

      //               frappe.call({
      //                 method:
      //                   "kenya_compliance_via_slade.kenya_compliance_via_slade.apis.apis.update_imported_item_request",
      //                 args: {
      //                   request_data: {
      //                     company_name: companyName,
      //                     document_name: frm.doc.name,
      //                     item_name: frm.doc.item_name,
      //                     package: referenced_item.package,
      //                     quantity: referenced_item.quantity,
      //                     id: referenced_item.name,
      //                     declaration_date: referenced_item.declaration_date,
      //                     organisation: organisation,
      //                     branch: branch,
      //                     product: frm.doc.custom_slade_id,
      //                   },
      //                 },
      //                 callback: function (apiResponse) {
      //                   if (apiResponse && apiResponse.message) {
      //                     frappe.msgprint("Request queued. Check later.");
      //                   }
      //                 },
      //               });
      //             } else {
      //               frappe.msgprint("Unable to fetch referenced item details.");
      //             }
      //           },
      //         });
      //       },
      //       __("eTims Actions")
      //     );
      //   }


      // }
    }
  },
  custom_product_type_name: function (frm) {
    if (frm.doc.custom_product_type_name === "Service") {
      frm.set_value("is_stock_item", 0);
    } else {
      frm.set_value("is_stock_item", 1);
    }
  },
});
