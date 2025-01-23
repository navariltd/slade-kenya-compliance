# Kenya Compliance via Slade360

<a id="more_details"></a>

This application integrates **ERPNext** with **Kenya Revenue Authority's (KRA) eTIMS** through the **Virtual Sales Control Unit (VSCU)**, facilitating seamless tax compliance and data synchronization. With this integration, businesses can:

- Automatically share sales and purchase transaction details with KRA.
- Update inventory records and manage customer information efficiently.
- Register items and synchronize product data with eTIMS servers.

### Why Compliance via Slade360?

While awaiting full approval by KRA, this integration provides a robust compliance solution through **Slade360**, offering businesses an efficient pathway to meet Kenyan tax regulations.

For more details about eTims and Slade360:

<a id="etims_official_documentation"></a>

- [VSCU Documentation](https://www.kra.go.ke/images/publications/VSCU_Specification_Document_v2.0.pdf)

- [Slade360 Documentation](https://developers.slade360.com/docs/getting-started)

## Architectural Overview

<a id="architectural_overview"></a>

An overview of ERPNext's Architecture
![ERPNext Architectural Overview](/kenya_compliance_via_slade/docs/images/erpnext_instance_architecture.PNG)

An overview of an ERPNext Instance's communication with the eTims servers
![Architectural Overview](/kenya_compliance_via_slade/docs/images/architectural_overview.jpg)

Once the application is [installed](#installation) and [configured](#environment-settings) in an ERPNext instance, communication to the ETims servers takes place through background jobs executed by [Redis Queue](https://redis.com/glossary/redis-queue/). The eTims response Information is stored in the relevant [customised DocType's](#customisations) tables in the [site's database](https://frappeframework.com/docs/user/en/basics/sites).

## Key Features

The following are the key features of the application:

1. [Application Workspace](#workspace)
2. [Error Logs](#error_logs)
3. [Bulk submission of information](#bulk_submissions)
4. [Flexible setup and configuration](#flexible_setup_and_configuration)

### App Workspace

<a id="workspace"></a>

![App Workspace](/kenya_compliance_via_slade/docs/images/workspace.png)

The workspace contains shortcuts to various documents of interest concerning eTims.

**NOTE**: The workspace may look different depending on when you install the app or due to future changes.

### Error Logs

<a id="error_logs"></a>

![Example Error Log](/kenya_compliance_via_slade/docs/images/error_log.PNG)

Each request is logged in the Integration Request DocType. Any response errors are logged in the Error Log doctype. Additionally, logs are written and can also be accessed through the logs folder of the bench harbouring the running instance if the records in the Error Logs/Integration Request DocTypes are cleared.

### Bulk Submission of Information

<a id="bulk_submissions"></a>

![Bulk Submission of Records](/kenya_compliance_via_slade/docs/images/bulk_submission.PNG)

Bulk submission of information is supported for relevant DocTypes.

### Setup and Configuration

<a id="flexible_setup_and_configuration"></a>

To set up the application, follow these steps:
![Refreshing data](/kenya_compliance_via_slade/docs/images/get-codes.png)

1. **Create the eTims Settings**:

   Navigate to the eTims Settings doctype and create a new record with the necessary details.

2. **Fetch All Codes**:

   In the eTims Settings doctype, click the _Get Codes_ button to fetch the latest codes from the eTims servers.

3. **Sync the Organisation Structures**:

   In the eTims Settings doctype, click the _Sync Organisation Units_ button to synchronize the organization structure, including branches, company departments, and workstations.

4. **Submit All Mode of Payments**:

   In the eTims Settings doctype, click the _Submit Mode of Payments_ button to set up the modes of payments.

5. **Submit All Warehouses**:

   Navigate to the Warehouse list view and click the _Submit Warehouses_ button to submit all warehouse details.

6. **Classify and Register All Items**:
   Navigate to the Item list view and classify each item according to the specifications provided by KRA and submit to eTims.

By following these steps, you will ensure that your application is properly set up and ready to communicate with the eTims servers.

## Key DocTypes

<a id="key_doctypes"></a>

The following are the key doctypes included:

1. [Current Environment Identifier](#current_env_id)
2. [Environment Settings for single and/or multiple companies](#environment_settings)
3. [Routes Reference](#routes_reference)

The app also creates a Workspace that collates important doctypes.

### Current Environment Identifier

<a id="current_env_id"></a>

This doctype is used to provide a global identifier for the current environment, which will in turn influence whether communication will happen with the Sandbox or Production eTims servers that KRA has provided.

This is a Single doctype with only two possible values: _Sandbox or Production_.

**NOTE**: The option is applied globally to all users of the current ERPNext instance.

![Current Environment Identifier](/kenya_compliance_via_slade/docs/images/current_environment_identifier.png)

### Environment Settings

<a id="environment_settings"></a>

This doctype aggregates all the settings, and credentials required for communication with the eTims Servers.

![Environment Settings](/kenya_compliance_via_slade/docs/images/environment_settings.png)

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

<a id="invoice_defaults"></a>

![Sales and Purchase Invoice Defaults](/kenya_compliance_via_slade/docs/images/invoice_defaults.png)

The Sales and Purchase Invoice Defaults tab allows users to set default values for sales and purchase invoices. This ensures consistency and reduces the need for manual entry.

1. **Payment Type**: The default payment type for sales invoices.
2. **Transaction Progress**: The default transaction progress for sales invoices.
3. **Purchase Type**: The default purchase type for purchase invoices.
4. **Purchase Status**: The default status for purchase invoices.
5. **Receipt Type**: The default receipt type for purchase invoices.

**NOTE**: These defaults can be overridden on individual invoices if necessary.

<a id="auth_details"></a>

![Authentication Details](/kenya_compliance_via_slade/docs/images/auth_details.png)

The Authentication Details tab includes fields for storing client secrets, keys, username, password, and token details. These fields are essential for secure communication with the eTims servers.

1. **Client Secret**: The secret key provided by Slade360.
2. **Client Key**: The client key issued by Slade360.
3. **Username**: The username for authentication.
4. **Password**: The password for authentication.
5. **Token**: The access token used for subsequent communication.

**NOTE**: If the token expires, it will be automatically regenerated upon a new eTims request.

### Routes Reference

<a id="routes_reference"></a>

![Routes Reference](/kenya_compliance_via_slade/docs/images/routes_reference.png)

This doctype holds references to the endpoints provided by KRA for the various activities. Each endpoint has an associated last request date that is updated after each eTims response. For a comprehensive documentation on the various endpoints, see the [More Details](#etims_official_documentation) section at the beginning.

**NOTE**: The _URL Path Function_ field is used as the search parameter whenever an endpoint is retrieved.

## Customisations

The following are the customisations done in order for the ERPNext instance to interface with the eTims servers.

1. [Item Doctype](#item_doctype_customisations)
2. [Sales Invoice Doctype](#sales_invoice_doctype_customisations)
3. [Customer Doctype](#customer_doctype_customisations)

### Item Doctype

<a id="item_doctype_customisations"></a>

![Item Doctype Customisations](/kenya_compliance_via_slade/docs/images/item_etims_tab.png)

The **eTims Details tab** will be present for each item during and after loading of each item. The tab holds fields to various doctypes that allow one to classify each item according to the specifications provided by KRA.

**NOTE**: The information captured here is mandatory when sending sales information to the eTims servers.

The doctypes linked include:

1. **Item Classifications**: Item classifications as specified by KRA
2. **Packaging Unit**: Packaging units as specified by KRA, e.g. Jars, wooden box, etc.
3. **Unit of Quantity**: Units of Quantity as specified by KRA, e.g. kilo-gramme, grammes, etc.
4. **Product Type**: Product type as specified by KRA, e.g. finished product, raw materials, etc.
5. **Item Type**: Product type as specified by KRA, e.g. sku, consu, service, etc.
6. **Country of Origin**: The country of origin declared for the item.

The _eTims Action_ button is also present for items that have not been registered in the etims server (for the lifetime of the current instance), which are denoted by the _Item Registered?_ check field not being ticked. This is a read-only field that is updated only after successful Item registration.

### Customer Doctype

<a id="customer_doctype_customisations"></a>

![Customer Doctype Customisations](/kenya_compliance_via_slade/docs/images/customer_doctype.png)

For customers, the customisations are domiciled in the Tax tab. Also present is the eTims Actions Button where one can perform a _Customer Search_ in the eTims Servers. Successful customer searches update read-only fields in the same record and check the _Is Validated field_.

**NOTE**: Supplying the customer's KRA PIN is a pre-requisite to making the search.

### Sales Invoice

<a id="sales_invoice_doctype_customisations"></a>

![Sales Invoice Customisations](/kenya_compliance_via_slade/docs/images/sales_invoice_details.png)

Customisations on the Sales Invoice are found under the eTims Details tab. The fields in the tab are:

1. **Payment Type**: A reference to the relevant payment type for the invoice record. This is a link field, with values fetched from KRA.
2. **Transaction Progress**: A reference to the relevant transaction progress for the invoice record. This is also a link field, with values also fetched from KRA.

Fields under the _eTims Response Details_ are values received as a response from eTims. These are read-only, and only updated after a successful response is received.

![Sales Invoice Items Customisations](/kenya_compliance_via_slade/docs/images/sales_invoice_item_details.PNG)

For each item, the above fields are required in order to submit sales information to eTims. These information is fetched from the item data by default, but it can be edited on the sales invoice before submitting information.

**NOTE**: Submission of the data happens whenever one submits a sales invoice as a background job.

### Stock Movements

<a id="stock_movements"></a>

Transactions that affect stock levels are automatically submitted to the eTims Servers.

Submission of Stock Movements is achieved by sending Stock Ledger Entry records. The process has been automated through [Background Jobs](#background_jobs) to relieve users from having to manually submit Stock Balance (inventory) information, as well as changes in stocks.

**NOTE**: Only Stockable Items are submitted to eTims Servers.

### Fetching Purchases

<a id="registered_purchases"></a>

Users are able to fetch Sales details registered by other Parties that form the basis for Purchase Documents.

![Registered Purchases](/kenya_compliance_via_slade/docs/images/registered_purchases.PNG)

Once the counter-party's sales information (your purchase) is successfully fetched, you can create Items, Suppliers, Purchase Invoices, and Purchase Receits from the details.

![Registered Purchases Actions](/kenya_compliance_via_slade/docs/images/registered_purchases_actions.PNG)

**NOTE**: This feature is highly experimental and may result in discrepancies between the information fetched and the generated records, e.g. Tax Details after creating a Purchase Invoice.

### Organisation Mapping

<a id="organisation_mapping"></a>

Managing the organisation structure is achieved via mapping Companies, Branches, and Departments to the relevant Slade360 organisation structures.

#### Company Mapping

Mapping the Companies ensures correct referencing of Company Ids when submitting information.

#### Branch Mapping

![branch mapping](/kenya_compliance_via_slade/docs/images/branch.png)

#### Department Mapping

![department mapping](/kenya_compliance_via_slade/docs/images/department.png)

Mapping the Departments ensures correct referencing of Department Ids (source_organisation_unit) when submitting invoices.

#### Warehouse Mapping

<a id="warehouse_mapping"></a>

![warehouse mapping](/kenya_compliance_via_slade/docs/images/warehouse.png)

Managing Warehouses is achieved via mapping Slade360 Warehouses and Locations to the ERPNEXT Warehouse doctype on a one-to-one basis. This ensures correct referencing of Warehouse Ids when submitting stock movement information.

### Imported Item Management

<a id="imported_item_management"></a>

![imported item management](/kenya_compliance_via_slade/docs/images/fetching%20imported%20items.PNG)

The **Registered Imported Item** doctype allows one to fetch imported items declared to belong to the user's company. These Items can be of existing Items (items already in ERPNext's database) or new Items.

![imported item record view](/kenya_compliance_via_slade/docs/images/imported_item_record_view.png)

To link an Imported Item to an existing Item, you reference the Item in the _Referenced Imported Item_ field of Item doctype under the _Purchasing_ tab.

![linking item with imported item](/kenya_compliance_via_slade/docs/images/linking-imported_item.png)

Once the records have been linked, the user can submit the _converted_ (specifying the item classification of the accepted imported item) back to eTims to register the item. This is done through the _eTims Action, Submit Imported Item_ action button. This action button is active if the Item is linked to an Imported Item and the Item has not been registered prior.

## How to Install

<a id="installation"></a>

### Manual Installation/Self Hosting

<a id="manual_installation"></a>

To install the app, [Setup, Initialise, and run a Frappe Bench instance](https://frappeframework.com/docs/user/en/installation).

Once the instance is up and running, add the application to the environment by running the command below in an active Bench terminal:

`bench get-app https://github.com/navariltd/kenya-compliance-via-slade.git`

followed by:

`bench --site <your.site.name.here> install-app kenya_compliance_via_slade`

To run tests, ensure Testing is enabled in the target site by executing:

`bench --site <your.site.name.here> set-config allow_tests true`

followed by

`bench --site <your.site.name.here> run-tests --app kenya_compliance_via_slade`

**NOTE**: Replace _<your.site.name.here>_ with the target site name.

### FrappeCloud Installation

<a id="frappecloud_installation"></a>

Installing on [FrappeCloud](https://frappecloud.com/docs/introduction) can be achieved after setting up a Bench instance, and a site. The app can then be added using the _Add App_ button in the _App_ tab of the bench and referencing this repository by using the _Install from GitHub_ option if you are not able to search for the app.
