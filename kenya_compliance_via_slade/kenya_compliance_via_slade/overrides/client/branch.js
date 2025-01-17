const doctype = "Branch";

frappe.ui.form.on(doctype, {
  refresh: async function (frm) {
    const companyName = frappe.boot.sysdefaults.company;
    const { message: activeSetting } = await frappe.db.get_value(
      settingsDoctypeName,
      { is_active: 1 },
      "name"
    );

    if (activeSetting?.name) {
      frm.add_custom_button(
        __("Get Imported Items"),
        function () {
          frappe.call({
            method:
              "kenya_compliance_via_slade.kenya_compliance_via_slade.apis.apis.perform_import_item_search",
            args: {
              request_data: {
                company_name: companyName,
                branch_code: frm.doc.custom_branch_code,
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
    }
  },
});
