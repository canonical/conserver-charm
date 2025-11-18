# Terraform Module for Conserver

This is a Terraform module facilitating the deployment of the Conserver charm,
using the [Terraform Juju provider][juju-provider]. For more information, refer
to the provider [documentation][juju-provider-docs].

## Requirements

This module requires a `juju` model to be available. Refer to the
[usage section](#usage) below for more details

## API

### Inputs

| Name          | Type   | Description                                 | Default       |
| ------------- | ------ | ------------------------------------------- | ------------- |
| app_name      | string | Name of the Juju application                | conserver     |
| juju_model    | string | Name of the Juju model to deploy into       |               |
| charm_channel | string | Channel to use for the charm                | latest/stable |
| revision      | number | Revision to use for the charm               | null          |
| config_file   | string | Base64 encoded contents of conserver.cf     |               |
| passwd_file   | string | Base64 encoded contents of conserver.passwd |               |

### Outputs

| Name     | Type   | Description                  |
| -------- | ------ | ---------------------------- |
| app_name | string | Name of the Juju application |

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
