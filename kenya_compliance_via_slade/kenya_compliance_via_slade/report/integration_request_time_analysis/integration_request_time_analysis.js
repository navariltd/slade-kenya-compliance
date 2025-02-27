// Copyright (c) 2025, Navari Ltd and contributors
// For license information, please see license.txt

frappe.query_reports["Integration Request Time Analysis"] = {
  filters: [
    {
      fieldname: "from_date",
      label: "From Date",
      fieldtype: "Date",
      reqd: 0,
    },
    {
      fieldname: "to_date",
      label: "To Date",
      fieldtype: "Date",
      reqd: 0,
    },
    {
      fieldname: "integration_request_service",
      label: "Service",
      fieldtype: "MultiSelectList",
      reqd: 0,
      get_data: function (txt) {
        return new Promise((resolve) => {
          frappe.call({
            method: "frappe.client.get_list",
            args: {
              doctype: "Integration Request",
              fields: ["integration_request_service", "name"],
              distinct: true,
              group_by: "integration_request_service",
              ignore_permissions: 1,
              limit_page_length: 0,
            },
            callback: function (response) {
              if (response.message) {
                let services = response.message
                  .map((item) => item.integration_request_service)
                  .filter(Boolean); // Ensure only valid values

                resolve(services); // Pass array of strings
              } else {
                resolve([]); // Return empty array if no data
              }
            },
          });
        });
      },
    },
  ],

  onload: function (report) {
    report.page.add_inner_button("Clear Filters", function () {
      report.filters.forEach((filter) => {
        filter.set_input(filter.df.default || "");
      });
      report.refresh();
    });
  },
};
