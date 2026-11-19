# CATALOGS

# created in UI with free tier limitation

resource "databricks_catalog" "tfLayerBronze" {
  name    = "bronze"
  comment = "@terraform"

  lifecycle {
    ignore_changes = [storage_root]
  }
}

import {
  to = databricks_catalog.tfLayerBronze
  id = "bronze"
}



resource "databricks_catalog" "tfLayerSilver" {
  name    = "silver"
  comment = "@terraform"

  lifecycle {
    ignore_changes = [storage_root]
  }
}

import {
  to = databricks_catalog.tfLayerSilver
  id = "silver"
}



resource "databricks_catalog" "tfLayerGold" {
  name    = "gold"
  comment = "@terraform"

  lifecycle {
    ignore_changes = [storage_root]
  }
}

import {
  to = databricks_catalog.tfLayerGold
  id = "gold"
}

# SCHEMAS

resource "databricks_schema" "tfSchemaBronzeFlights" {
  catalog_name = databricks_catalog.tfLayerBronze.name
  name         = "flights"
  comment      = "@terraform"
}

resource "databricks_schema" "tfSchemaSilverFlights" {
  catalog_name = databricks_catalog.tfLayerSilver.name
  name         = "flights"
  comment      = "@terraform"
}

resource "databricks_schema" "tfSchemaGoldFlights" {
  catalog_name = databricks_catalog.tfLayerGold.name
  name         = "flights"
  comment      = "@terraform"
}


# SECRETS

resource "databricks_secret_scope" "tfSecretScopeOpensky" {
  name = "opensky"
}


# VOLUMES

resource "databricks_volume" "tfVolumeBronzeFlightsRaw" {
  catalog_name = databricks_catalog.tfLayerBronze.name
  schema_name  = databricks_schema.tfSchemaBronzeFlights.name
  name         = "raw"
  volume_type  = "MANAGED"
  comment      = "@terraform"
}
