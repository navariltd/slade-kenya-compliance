const doctypeName = "Navari Slade360 Organisation";

frappe.listview_settings[doctypeName] = {
  onload: function (listview) {
    const companyName = frappe.boot.sysdefaults.company;

    listview.page.add_inner_button(
      __("Get Organisations"),
      function (listview) {
        frappe.call({
          method:
            "kenya_compliance_via_slade.kenya_compliance_via_slade.apis.apis.search_organisations_request",
          args: {
            request_data: {
              company_name: companyName,
            },
          },
          callback: (response) => {
            console.log("Request queued. Please check in later");
          },
          error: (error) => {
            // Error Handling is Defered to the Server
          },
        });
      }
    );
  },
};
