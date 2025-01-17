const doctypeName = "UOM";

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
        __("Fetch eTims UOM List"),
        function (listview) {
          frappe.call({
            method:
              "kenya_compliance_via_slade.kenya_compliance_via_slade.background_tasks.tasks.fetch_etims_uom_list",
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

      listview.page.add_inner_button(
        __("Submit all UOMs to eTims"),
        function (listview) {
          frappe.call({
            method:
              "kenya_compliance_via_slade.kenya_compliance_via_slade.apis.apis.submit_uom_list",
            args: {},
            callback: (response) => {},
            error: (error) => {
              // Error Handling is Defered to the Server
            },
          });
        },
        __("eTims Actions")
      );
    }
  },
};
