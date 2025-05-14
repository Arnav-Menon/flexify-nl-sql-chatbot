
variable "location" {
  type    = string
  default = "eastus"
}

variable "resource_group_name" {
  type    = string
  default = "flexify-evals-fs"
}

variable "vnet_name" {
  type    = string
  default = "vnet01"
}

variable "subnet_name" {
  type    = string
  default = "subnet-1"
}

variable "subnet_prefix" {
  type    = string
  default = "172.16.0.0/26"
}

variable "cognitive_account_name" {
  type    = string
  default = "nl-sql-chatbot"
}

variable "sku_name" {
  type    = string
  default = "S0"
}

variable "private_dns_zone" {
  type    = string
  default = "privatelink.openai.azure.com"
}
