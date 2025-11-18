variable "app_name" {
  description = "Name to give the deployed application"
  type        = string
  default     = "conserver"
}

variable "juju_model" {
  description = "Name of the Juju model to deploy into"
  type        = string
}

variable "charm_channel" {
  description = "Channel to use for the charm (e.g., 'latest/stable')"
  type        = string
  default     = "latest/stable"
}

variable "revision" {
  description = "Revision number of the charm to use"
  type        = number
  nullable    = true
  default     = null
}

variable "config_file" {
  description = "Base64 encoded content for the conserver.cf configuration file"
  type        = string
}

variable "passwd_file" {
  description = "Base64 encoded content for the conserver.passwd file"
  type        = string
}