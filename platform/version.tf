terraform {
  required_providers {
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.140"
    }
  }
}

provider "databricks" {
  profile = "free"
}
