resource "juju_application" "conserver" {
  name  = "conserver"
  model = var.juju_model

  units = 1

  charm {
    name    = "conserver"
    base    = "ubuntu@22.04"
    channel = var.charm_channel
  }

  config = {
    config-file = var.config_file
    passwd-file = var.passwd_file
  }
}