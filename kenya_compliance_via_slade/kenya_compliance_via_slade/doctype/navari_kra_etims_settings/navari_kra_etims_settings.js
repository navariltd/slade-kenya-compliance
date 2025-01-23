// Copyright (c) 2024, Navari Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on("Navari KRA eTims Settings", {
  refresh: function (frm) {
    const companyName = frm.doc.company;

    if (!frm.is_new() && frm.doc.is_active) {
      frm.add_custom_button(
        __("Get Notices"),
        function () {
          frappe.call({
            method:
              "kenya_compliance_via_slade.kenya_compliance_via_slade.background_tasks.tasks.perform_notice_search",
            args: {
              request_data: {
                document_name: frm.doc.name,
                company_name: companyName,
                branch_id: frm.doc.bhfid,
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
        __("Get Codes"),
        function () {
          frappe.call({
            method:
              "kenya_compliance_via_slade.kenya_compliance_via_slade.background_tasks.tasks.refresh_code_lists",
            args: {
              request_data: {
                document_name: frm.doc.name,
                company_name: companyName,
                branch_id: frm.doc.bhfid,
              },
            },
            callback: (response) => {
              frappe.call({
                method:
                  "kenya_compliance_via_slade.kenya_compliance_via_slade.background_tasks.tasks.get_item_classification_codes",
                args: {
                  request_data: {
                    document_name: frm.doc.name,
                    company_name: companyName,
                    branch_id: frm.doc.bhfid,
                  },
                },
                callback: (response) => {},
                error: (error) => {
                  // Error Handling is Defered to the Server
                },
              });
            },
            error: (error) => {
              // Error Handling is Defered to the Server
            },
          });
        },
        __("eTims Actions")
      );
      frm.add_custom_button(
        __("Sync Organisation Units"),
        function () {
          frappe.call({
            method:
              "kenya_compliance_via_slade.kenya_compliance_via_slade.background_tasks.tasks.search_organisations_request",
            args: {
              request_data: {
                document_name: frm.doc.name,
                company_name: companyName,
                branch_id: frm.doc.bhfid,
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
        __("Submit Mode of Payments"),
        function () {
          frappe.call({
            method:
              "kenya_compliance_via_slade.kenya_compliance_via_slade.apis.apis.send_all_mode_of_payments",
            args: {},

            callback: (response) => {},
            error: (error) => {
              // Error Handling is Defered to the Server
            },
          });
        },
        __("eTims Actions")
      );

      frm.add_custom_button(
        __("Submit Warehouses"),
        function () {
          frappe.call({
            method:
              "kenya_compliance_via_slade.kenya_compliance_via_slade.apis.apis.submit_warehouse_list",
            args: {},

            callback: (response) => {},
            error: (error) => {
              // Error Handling is Defered to the Server
            },
          });
        },
        __("eTims Actions")
      );

      // frm.add_custom_button(
      //   __("Initialize device"),
      //   function () {
      //     frappe.call({
      //       method: "frappe.client.get_value",
      //       args: {
      //         doctype: "Branch",
      //         fieldname: "custom_branch_code",
      //         filters: { name: frm.doc.bhfid },
      //       },
      //       callback: function (res) {
      //         if (res.message) {
      //           const custom_branch_code = res.message.custom_branch_code;

      //           frappe.call({
      //             method:
      //               "kenya_compliance_via_slade.kenya_compliance_via_slade.apis.apis.initialize_device",
      //             args: {
      //               request_data: {
      //                 document_name: frm.doc.name,
      //                 etims_branch_id: custom_branch_code,
      //                 username: frm.doc.auth_username,
      //                 password: frm.doc.auth_password,
      //                 vscu_url: frm.doc.server_url,
      //                 etims_web_address:
      //                   "https://etims-api-sbx.kra.go.ke/etims-api",
      //                 organisation_tax_pin: frm.doc.tin,
      //                 etims_device_serial_no: frm.doc.dvcsrlno,
      //                 company_name: companyName,
      //                 branch_id: frm.doc.bhfid,
      //               },
      //             },
      //             callback: (response) => {
      //               // console.log(response);
      //             },
      //             error: (error) => {
      //               // Error handling
      //             },
      //           });
      //         } else {
      //           frappe.msgprint(__("Failed to fetch slade_id for the branch."));
      //         }
      //       },
      //     });
      //   },
      //   __("eTims Actions")
      // );
    }

    frm.add_custom_button(
      __("Get Auth Token"),
      function () {
        frappe.call({
          method:
            "kenya_compliance_via_slade.kenya_compliance_via_slade.utils.update_navari_settings_with_token",
          args: {
            docname: frm.doc.name,
          },
        });
      },
      __("eTims Actions")
    );

    frm.add_custom_button(
      __("Ping Server"),
      function () {
        frappe.call({
          method:
            "kenya_compliance_via_slade.kenya_compliance_via_slade.apis.apis.ping_server",
          args: {
            request_data: {
              server_url: frm.doc.server_url + "/alive",
              auth_url: frm.doc.auth_server_url,
            },
          },
        });
      },
      __("eTims Actions")
    );

    frm.set_query("bhfid", function () {
      return {
        filters: [["Branch", "custom_is_etims_branch", "=", 1]],
      };
    });
  },
  sandbox: function (frm) {
    const sandboxFieldValue = parseInt(frm.doc.sandbox);
    const sandboxServerUrl = "https://etims-api-sbx.kra.go.ke/etims-api";
    const productionServerUrl = "https://etims-api.kra.go.ke/etims-api";

    if (sandboxFieldValue === 1) {
      frm.set_value("env", "Sandbox");
      frm.set_value("server_url", sandboxServerUrl);
    } else {
      frm.set_value("env", "Production");
      frm.set_value("server_url", productionServerUrl);
    }
  },
});
