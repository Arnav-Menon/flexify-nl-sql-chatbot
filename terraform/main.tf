
provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location
}

resource "azurerm_virtual_network" "vnet" {
  name                = var.vnet_name
  address_space       = [var.subnet_prefix]
  location            = var.location
  resource_group_name = var.resource_group_name
}

resource "azurerm_subnet" "subnet" {
  name                 = var.subnet_name
  resource_group_name  = var.resource_group_name
  virtual_network_name = var.vnet_name
  address_prefixes     = [var.subnet_prefix]
  private_endpoint_network_policies_enabled = true
}

resource "azurerm_cognitive_account" "openai" {
  name                = var.cognitive_account_name
  location            = var.location
  resource_group_name = var.resource_group_name
  kind                = "OpenAI"
  sku_name            = var.sku_name

  network_acls {
    default_action = "Deny"
    virtual_network_subnet_ids = [azurerm_subnet.subnet.id]
    ip_rules = []
  }

  public_network_access = "Disabled"
  custom_subdomain_name = var.cognitive_account_name
}

resource "azurerm_private_dns_zone" "dns" {
  name                = var.private_dns_zone
  resource_group_name = var.resource_group_name
}

resource "azurerm_private_dns_zone_virtual_network_link" "dns_link" {
  name                  = "dns-link"
  resource_group_name   = var.resource_group_name
  private_dns_zone_name = azurerm_private_dns_zone.dns.name
  virtual_network_id    = azurerm_virtual_network.vnet.id
}
