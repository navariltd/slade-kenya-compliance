### Environment Settings

<a id="environment_settings"></a>

This doctype aggregates all the settings, and credentials required for communication with the eTims Servers.

![Environment Settings](../images/environment_settings.png)

The fields present include:

1. **Branch ID**: Provided by KRA during eTIMS VSCU registration.
2. **Device Serial Number**: Issued by KRA during eTIMS VSCU registration.
3. **Company**: Links to an existing company in the ERPNext instance.
4. **Department**: Departments are required to map requests to the Slade Server and are mapped to ERPNext.
5. **Workstation**: Workstations are required to map requests to the Slade Server and are mapped to ERPNext.
6. **Server URL**: Used for all requests to eTIMS.
7. **Auth Server URL**: Used to generate the access token.
8. **Sandbox Environment Check**: Indicates whether the settings are for the Sandbox (testing) or Production (real-world) eTIMS server. Ensure the correct environment is selected.
9. **Is Active Check**: Marks the settings record as active. Only one settings record can be active for each unique combination of environment, company (and company PIN), and branch ID.

<a id="auth_details"></a>

![Authentication Details](../images/auth_details.png)

The Authentication Details tab includes fields for storing client secrets, keys, username, password, and token details. These fields are essential for secure communication with the eTims servers.

1. **Client Secret**: The secret key provided by Slade360.
2. **Client Key**: The client key issued by Slade360.
3. **Username**: The username for authentication.
4. **Password**: The password for authentication.
5. **Token**: The access token used for subsequent communication.

**NOTE**: If the token expires, it will be automatically regenerated upon a new eTims request.

<a id="invoice_defaults"></a>

![Sales and Purchase Invoice Defaults](../images/invoice_defaults.png)

The Sales and Purchase Invoice Defaults tab allows users to set default values for sales and purchase invoices. This ensures consistency and reduces the need for manual entry.

1. **Payment Type**: The default payment type for sales invoices.
2. **Transaction Progress**: The default transaction progress for sales invoices.
3. **Purchase Type**: The default purchase type for purchase invoices.
4. **Purchase Status**: The default status for purchase invoices.
5. **Receipt Type**: The default receipt type for purchase invoices.

**NOTE**: These defaults can be overridden on individual invoices if necessary.
<a id="settings_freq"></a>

![Sales and Purchase Invoice Defaults](../images/settings_freq.png)

#### Frequency of Communication with eTims Servers

This section defines how often different types of information are refreshed or submitted to eTims.

1. **Notices Refresh Frequency**: Frequency at which system notices are refreshed (`notices_refresh_frequency`).
2. **Codes Refresh Frequency**: Frequency for refreshing system codes (`codes_refresh_frequency`).
3. **Sales Auto Submission Enabled**: Enables or disables automatic submission of sales data (`sales_auto_submission_enabled`).
4. **Sales Information Submission Frequency**: Defines how often sales data is sent (`sales_information_submission`).
5. **Purchase Auto Submission Enabled**: Enables or disables automatic submission of purchase data (`purchase_auto_submission_enabled`).
6. **Purchase Information Submission Frequency**: Defines how often purchase data is sent (`purchase_information_submission`).
7. **Stock Auto Submission Enabled**: Enables or disables automatic submission of stock data (`stock_auto_submission_enabled`).
8. **Stock Information Submission Frequency**: Defines how often stock data is sent (`stock_information_submission`).
9. **Stock Info. Cron Format**: Defines the cron format for stock information submission (`stock_info_cron_format`).
10. **Submission Timeframe**: Sets the allowed period for sending entries such as invoices and purchases to eTIMS. For example, if set to 4 days, entries can only be sent within the last 4 days.
    - **Sales Information Submission Timeframe**: Maximum period allowed for submitting sales information (`sales_information_submission_timeframe`).
    - **Max Sales Submission Attempts**: Maximum retries for failed sales invoice submissions before restrictions apply (`maximum_sales_information_submission_attempts`).
    - **Purchase Information Submission Timeframe**: Maximum period allowed for submitting purchase information (`purchase_information_submission_timeframe`).
    - **Max Purchase Submission Attempts**: Maximum retries for failed purchase invoice submissions before restrictions apply (`maximum_purchase_information_submission_attempts`).
    - **Stock Information Submission Timeframe**: Maximum period allowed for submitting stock information (`stock_information_submission_timeframe`).
    - **Max Stock Submission Attempts**: Maximum retries for failed stock submissions before restrictions apply (`maximum_stock_information_submission_attempts`).
