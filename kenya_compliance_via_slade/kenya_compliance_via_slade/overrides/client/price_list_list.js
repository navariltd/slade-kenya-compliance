const doctypeName = "Price List";
const settingsDoctypeName = "Navari KRA eTims Settings";

frappe.listview_settings[doctypeName] = {
  onload: async function (listview) {
    const companyName = frappe.boot.sysdefaults.company;
    const { message: activeSetting } = await frappe.db.get_value(
      settingsDoctypeName,
      { is_active: 1 },
      "name"
    );

    if (activeSetting?.name) {
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
    }
  },
};
