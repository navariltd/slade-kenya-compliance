const parentDoctype = "Sales Invoice";
const childDoctype = `${parentDoctype} Item`;
const packagingUnitDoctypeName = "Navari eTims Packaging Unit";
const unitOfQuantityDoctypeName = "Navari eTims Unit of Quantity";
const taxationTypeDoctypeName = "Navari KRA eTims Taxation Type";
const settingsDoctypeName = "Navari KRA eTims Settings";

frappe.ui.form.on(parentDoctype, {
  refresh: function (frm) {
    frm.set_value("update_stock", 1);
    if (frm.doc.update_stock === 1) {
      frm.toggle_reqd("set_warehouse", true);
    }

    if (!frm.doc.custom_successfully_submitted) {
      frm.add_custom_button(
        __("Send Invoice"),
        function () {
          frappe.call({
            method:
              "kenya_compliance_via_slade.kenya_compliance_via_slade.overrides.server.sales_invoice.send_invoice_details",
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

  },
  validate: function (frm) {
    frappe.db.get_value(
      settingsDoctypeName,
      {
        is_active: 1,
        bhfid: frm.doc.branch,
        company: frappe.defaults.get_user_default("Company"),
      },
      [
        "name",
        "company",
        "bhfid",
        "sales_payment_type",
        "sales_transaction_progress",
      ],
      (response) => {
        if (!frm.doc.custom_payment_type) {
          frm.set_value("custom_payment_type", response.sales_payment_type);
        }
        if (!frm.doc.custom_transaction_progres) {
          frm.set_value(
            "custom_transaction_progres",
            response.sales_transaction_progress
          );
        }
      }
    );
  },
});

frappe.ui.form.on(childDoctype, {
  item_code: function (frm, cdt, cdn) {
    const item = locals[cdt][cdn].item_code;
    const taxationType = locals[cdt][cdn].custom_taxation_type;

    if (!taxationType) {
      frappe.db.get_value(
        "Item",
        { item_code: item },
        ["custom_taxation_type"],
        (response) => {
          locals[cdt][cdn].custom_taxation_type = response.custom_taxation_type;
          locals[cdt][cdn].custom_taxation_type_code =
            response.custom_taxation_type;
        }
      );
    }
  },
  custom_packaging_unit: async function (frm, cdt, cdn) {
    const packagingUnit = locals[cdt][cdn].custom_packaging_unit;

    if (packagingUnit) {
      frappe.db.get_value(
        packagingUnitDoctypeName,
        {
          name: packagingUnit,
        },
        ["code"],
        (response) => {
          const code = response.code;
          locals[cdt][cdn].custom_packaging_unit_code = code;
          frm.refresh_field("custom_packaging_unit_code");
        }
      );
    }
  },
  custom_unit_of_quantity: function (frm, cdt, cdn) {
    const unitOfQuantity = locals[cdt][cdn].custom_unit_of_quantity;

    if (unitOfQuantity) {
      frappe.db.get_value(
        unitOfQuantityDoctypeName,
        {
          name: unitOfQuantity,
        },
        ["code"],
        (response) => {
          const code = response.code;
          locals[cdt][cdn].custom_unit_of_quantity_code = code;
          frm.refresh_field("custom_unit_of_quantity_code");
        }
      );
    }
  },
});
