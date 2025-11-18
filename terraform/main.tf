resource "juju_application" "conserver" {
  name  = var.app_name
  model = var.juju_model

  units = 1

  charm {
    name     = "conserver"
    base     = "ubuntu@22.04"
    channel  = var.charm_channel
    revision = var.revision
  }

  config = {
    config-file = var.config_file
    passwd-file = var.passwd_file
  }
}