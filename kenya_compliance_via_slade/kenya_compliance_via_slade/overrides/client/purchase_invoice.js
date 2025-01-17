const parentDoctype = "Purchase Invoice";
const settingsDoctypeName = "Navari KRA eTims Settings";

frappe.ui.form.on(parentDoctype, {
  refresh: async function (frm) {
    frm.set_value("update_stock", 1);
    if (frm.doc.update_stock === 1) {
      frm.toggle_reqd("set_warehouse", true);
    }
  },
});
