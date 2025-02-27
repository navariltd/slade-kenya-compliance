# Kenya Compliance via Slade 360 Advantage 🚀

This application integrates **ERPNext** with **Kenya Revenue Authority's (KRA) eTIMS** through the **Virtual Sales Control Unit (VSCU)**, facilitating seamless tax compliance and data synchronization. With this integration, businesses can:

- 📊 Automatically share sales and purchase transaction details with KRA.
- 📦 Update inventory records and manage customer information efficiently.
- 🛒 Register items and synchronize product data with eTIMS servers.

## Why Compliance via Slade 360 Advantage? 🤔

This integration leverages **Slade 360 Advantage**, a trusted third-party solution, to provide businesses with a seamless and robust compliance pathway for Kenyan tax regulations. With a highly reliable middleware to VSCU, it ensures efficiency and accuracy in tax compliance.

For more details about eTims and Slade 360 Advantage:

- 📄 [VSCU Documentation](https://www.kra.go.ke/images/publications/VSCU_Specification_Document_v2.0.pdf)
- 📘 [Slade 360 Advantage Documentation](https://developers.slade360.com/docs/getting-started)

## Key Sections 📚

- #### [Architectural Overview](kenya_compliance_via_slade/docs/architecture.md)

- #### [Setup & Configuration](kenya_compliance_via_slade/docs/setup_configuration.md)

- #### [Key Features](kenya_compliance_via_slade/docs/features.md)

- #### [Key DocTypes](kenya_compliance_via_slade/docs/doctypes.md)

- #### [Customisations](kenya_compliance_via_slade/docs/customisations.md)

- #### [Dashboard & Reports](kenya_compliance_via_slade/docs/dashboard_reports.md)

For a more comprehensive guide and details on the integration, visit our [Complete Guide](https://github.com/navariltd/kenya-compliance-via-slade/wiki).

## How to Install 🛠️

### Manual Installation/Self Hosting

To install the app, [Setup, Initialise, and run a Frappe Bench instance](https://frappeframework.com/docs/user/en/installation).

Once the instance is up and running, add the application to the environment by running the command below in an active Bench terminal:

```sh
bench get-app https://github.com/navariltd/kenya-compliance-via-slade.git
```

followed by:

```sh
bench --site <your.site.name.here> install-app kenya_compliance_via_slade
```

To run tests, ensure Testing is enabled in the target site by executing:

```sh
bench --site <your.site.name.here> set-config allow_tests true
```

followed by:

```sh
bench --site <your.site.name.here> run-tests --app kenya_compliance_via_slade
```

**NOTE**: Replace _<your.site.name.here>_ with the target site name.

### FrappeCloud Installation ☁️

Installing on [FrappeCloud](https://frappecloud.com/docs/introduction) can be achieved after setting up a Bench instance and a site. The app can then be added using the _Add App_ button in the _App_ tab of the bench and referencing this repository by using the _Install from GitHub_ option if you are not able to search for the app.

### Important Note ⚠️

This integration goes through an approved third party. Please contact them for registration with KRA and VSCU setup at: [etims@savannahinformatics.com](mailto:etims@savannahinformatics.com).

For support, contact us at: [support@navari.co.ke](mailto:support@navari.co.ke) or visit [Navari](https://navari.co.ke/).
