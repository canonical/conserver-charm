variable "app_name" {
  description = "Name to give the deployed application"
  type        = string
  default     = "conserver"
}

variable "charm_channel" {
  description = "Channel of the charm"
  type        = string
  default     = "latest/stable"
}

variable "config_file" {
  description = "Base64 encoded content for the conserver.cf configuration file"
  type        = string
}

variable "constraints" {
  description = "String listing constraints for this application"
  type        = string
  default     = "arch=amd64"
}

variable "juju_model" {
  description = "Reference to an existing model resource or data source for the model to deploy to"
  type        = string
}

variable "passwd_file" {
  description = "Base64 encoded content for the conserver.passwd file"
  type        = string
  sensitive   = true
}

variable "revision" {
  description = "Revision number of the charm"
  type        = number
  nullable    = true
  default     = null
}
