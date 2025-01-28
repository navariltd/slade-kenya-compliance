const doctype = "BOM";
const settingsDoctypeName = "Navari KRA eTims Settings";

frappe.ui.form.on(doctype, {
  refresh: async function (frm) {
    const companyName = frappe.boot.sysdefaults.company;
    const { message: activeSetting } = await frappe.db.get_value(
      settingsDoctypeName,
      { is_active: 1 },
      "name"
    );

    if (activeSetting?.name) {
      let itemCode;

      frappe.db.get_value("Item", { name: frm.doc.item }, ["*"], (response) => {
        itemCode = response.custom_item_code_etims;
      });

      if (
        !frm.is_new() &&
        frm.doc.docstatus === 1 &&
        frm.doc.custom_item_composition_submitted_successfully != 1
      ) {
        frm.add_custom_button(
          __("Submit Item Composition"),
          function () {
            frappe.call({
              method:
                "kenya_compliance_via_slade.kenya_compliance_via_slade.apis.apis.submit_item_composition",
              args: {
                name: frm.doc.name,
              },
              callback: (response) => {},
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
