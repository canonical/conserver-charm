# Terraform Module for Conserver

This is a Terraform module facilitating the deployment of the Conserver charm,
using the [Terraform Juju provider][juju-provider]. For more information, refer
to the provider [documentation][juju-provider-docs].

## Requirements

This module requires a `juju` model to be available. Refer to the
[usage section](#usage) below for more details

## API

### Inputs

| Name          | Type   | Description                                                                       | Default       |
| ------------- | ------ | --------------------------------------------------------------------------------- | ------------- |
| app_name      | string | Name to give the deployed application                                             | conserver     |
| charm_channel | string | Channel of the charm                                                              | latest/stable |
| config_file   | string | Base64 encoded contents of conserver.cf                                           |               |
| constraints   | string | String listing constraints for this application                                   | arch=amd64    |
| juju_model    | string | Reference to an existing model resource or data source for the model to deploy to |               |
| passwd_file   | string | Base64 encoded contents of conserver.passwd                                       |               |
| revision      | number | Revision number of the charm                                                      | null          |

### Outputs

| Name     | Type   | Description                      |
| -------- | ------ | -------------------------------- |
| app_name | string | Name of the deployed application |

## Usage

### Basic Usage

Users should ensure that Terraform is aware of the `juju_model` dependency of
the charm module.

To deploy this module, you can run

```shell
terraform apply -var="juju_model=<MODEL_NAME>" -auto-approve
```

[juju-provider]: https://github.com/juju/terraform-provider-juju/
[juju-provider-docs]: https://registry.terraform.io/providers/juju/juju/latest/docs
