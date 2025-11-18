# Gemini Enterprise Demo #4 - Customer Data Platform
# Terraform Configuration for Infrastructure Deployment

terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Generate random password for AlloyDB
resource "random_password" "alloydb_password" {
  length  = 32
  special = true
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "aiplatform.googleapis.com",
    "discoveryengine.googleapis.com",
    "bigquery.googleapis.com",
    "alloydb.googleapis.com",
    "firestore.googleapis.com",
    "storage-api.googleapis.com",
    "compute.googleapis.com",
    "servicenetworking.googleapis.com",
  ])

  service            = each.key
  disable_on_destroy = false
}

# BigQuery dataset for customer analytics
resource "google_bigquery_dataset" "customer_analytics" {
  dataset_id                 = "customer_analytics"
  friendly_name              = "Customer Analytics"
  description                = "Customer analytics data warehouse for Demo #4"
  location                   = var.region
  default_table_expiration_ms = null

  labels = {
    demo = "gemini-enterprise-cdp"
    env  = var.environment
  }

  depends_on = [google_project_service.required_apis]
}

# BigQuery table: customers
resource "google_bigquery_table" "customers" {
  dataset_id = google_bigquery_dataset.customer_analytics.dataset_id
  table_id   = "customers"

  schema = jsonencode([
    { name = "customer_id", type = "STRING", mode = "REQUIRED" },
    { name = "company_name", type = "STRING", mode = "REQUIRED" },
    { name = "industry", type = "STRING", mode = "NULLABLE" },
    { name = "employee_count", type = "INTEGER", mode = "NULLABLE" },
    { name = "annual_revenue_usd", type = "FLOAT", mode = "NULLABLE" },
    { name = "account_tier", type = "STRING", mode = "NULLABLE" },
    { name = "customer_since", type = "DATE", mode = "NULLABLE" },
    { name = "lifetime_value_usd", type = "FLOAT", mode = "NULLABLE" },
    { name = "total_transactions", type = "INTEGER", mode = "NULLABLE" },
    { name = "last_transaction_date", type = "DATE", mode = "NULLABLE" },
    { name = "churn_risk_score", type = "FLOAT", mode = "NULLABLE" },
    { name = "health_score", type = "INTEGER", mode = "NULLABLE" },
    { name = "primary_contact_email", type = "STRING", mode = "NULLABLE" },
    { name = "geographic_region", type = "STRING", mode = "NULLABLE" },
  ])
}

# BigQuery table: transactions
resource "google_bigquery_table" "transactions" {
  dataset_id = google_bigquery_dataset.customer_analytics.dataset_id
  table_id   = "transactions"

  schema = jsonencode([
    { name = "transaction_id", type = "STRING", mode = "REQUIRED" },
    { name = "customer_id", type = "STRING", mode = "REQUIRED" },
    { name = "transaction_date", type = "TIMESTAMP", mode = "REQUIRED" },
    { name = "amount_usd", type = "FLOAT", mode = "REQUIRED" },
    { name = "product_id", type = "STRING", mode = "NULLABLE" },
    { name = "transaction_type", type = "STRING", mode = "NULLABLE" },
  ])

  # Partitioning for performance
  time_partitioning {
    type  = "DAY"
    field = "transaction_date"
  }
}

# Firestore database
resource "google_firestore_database" "customer_data" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"

  depends_on = [google_project_service.required_apis]
}

# Cloud Storage bucket: customer documents
resource "google_storage_bucket" "customer_docs" {
  name          = "${var.project_id}-customer-docs"
  location      = var.region
  force_destroy = var.environment == "dev" ? true : false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    demo = "gemini-enterprise-cdp"
    type = "customer-documents"
  }
}

# Cloud Storage bucket: support call recordings
resource "google_storage_bucket" "support_calls" {
  name          = "${var.project_id}-support-calls"
  location      = var.region
  force_destroy = var.environment == "dev" ? true : false

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    demo = "gemini-enterprise-cdp"
    type = "support-calls"
  }
}

# VPC network for AlloyDB
resource "google_compute_network" "alloydb_network" {
  name                    = "alloydb-network"
  auto_create_subnetworks = false

  depends_on = [google_project_service.required_apis]
}

# Subnet for AlloyDB
resource "google_compute_subnetwork" "alloydb_subnet" {
  name          = "alloydb-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.alloydb_network.id
}

# Allocate IP range for private service connection
resource "google_compute_global_address" "private_ip_alloc" {
  name          = "alloydb-ip-range"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.alloydb_network.id
}

# Private VPC connection for AlloyDB
resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.alloydb_network.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_alloc.name]

  depends_on = [google_project_service.required_apis]
}

# AlloyDB cluster
resource "google_alloydb_cluster" "customer_db" {
  cluster_id = "customer-db-cluster"
  location   = var.region
  network    = google_compute_network.alloydb_network.id

  initial_user {
    user     = "postgres"
    password = random_password.alloydb_password.result
  }

  labels = {
    demo = "gemini-enterprise-cdp"
  }

  depends_on = [google_service_networking_connection.private_vpc_connection]
}

# AlloyDB primary instance
resource "google_alloydb_instance" "customer_db_primary" {
  cluster       = google_alloydb_cluster.customer_db.name
  instance_id   = "customer-db-primary"
  instance_type = "PRIMARY"

  machine_config {
    cpu_count = var.alloydb_cpu_count
  }

  labels = {
    demo = "gemini-enterprise-cdp"
  }
}

# Service account for MCP server
resource "google_service_account" "mcp_server" {
  account_id   = "mcp-server"
  display_name = "MCP Multi-Database Server"
  description  = "Service account for Demo #4 MCP server"
}

# IAM bindings for MCP server
resource "google_project_iam_member" "mcp_bigquery_viewer" {
  project = var.project_id
  role    = "roles/bigquery.dataViewer"
  member  = "serviceAccount:${google_service_account.mcp_server.email}"
}

resource "google_project_iam_member" "mcp_firestore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.mcp_server.email}"
}

resource "google_project_iam_member" "mcp_storage_viewer" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.mcp_server.email}"
}

resource "google_project_iam_member" "mcp_alloydb_client" {
  project = var.project_id
  role    = "roles/alloydb.client"
  member  = "serviceAccount:${google_service_account.mcp_server.email}"
}

# Secret Manager for AlloyDB password
resource "google_secret_manager_secret" "alloydb_password" {
  secret_id = "alloydb-password"

  replication {
    auto {}
  }

  labels = {
    demo = "gemini-enterprise-cdp"
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "alloydb_password" {
  secret      = google_secret_manager_secret.alloydb_password.id
  secret_data = random_password.alloydb_password.result
}

# Grant MCP server access to secret
resource "google_secret_manager_secret_iam_member" "mcp_secret_accessor" {
  secret_id = google_secret_manager_secret.alloydb_password.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.mcp_server.email}"
}
