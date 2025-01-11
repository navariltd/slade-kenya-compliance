const doctypeName = "Price List";

frappe.listview_settings[doctypeName] = {
  onload: function (listview) {
    const companyName = frappe.boot.sysdefaults.company;

    listview.page.add_inner_button(
      __("Fetch eTims Price List List"),
      function (listview) {
        frappe.call({
          method:
            "kenya_compliance_via_slade.kenya_compliance_via_slade.background_tasks.tasks.fetch_etims_pricelists",
          args: {
            request_data: {
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

    // listview.page.add_inner_button(
    //   __("Submit all Price Lists to eTims"),
    //   function (listview) {
    //     frappe.call({
    //       method:
    //         "kenya_compliance_via_slade.kenya_compliance_via_slade.apis.apis.submit_pricelists",
    //       args: {},
    //       callback: (response) => {},
    //       error: (error) => {
    //         // Error Handling is Defered to the Server
    //       },
    //     });
    //   },
    //   __("eTims Actions")
    // );
  },
};
