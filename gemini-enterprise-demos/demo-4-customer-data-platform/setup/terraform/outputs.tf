# Terraform Outputs for Demo #4

output "project_id" {
  description = "Google Cloud Project ID"
  value       = var.project_id
}

output "region" {
  description = "Google Cloud region"
  value       = var.region
}

output "bigquery_dataset" {
  description = "BigQuery dataset name"
  value       = google_bigquery_dataset.customer_analytics.dataset_id
}

output "bigquery_dataset_full" {
  description = "Full BigQuery dataset path"
  value       = "${var.project_id}.${google_bigquery_dataset.customer_analytics.dataset_id}"
}

output "customer_docs_bucket" {
  description = "Customer documents bucket name"
  value       = google_storage_bucket.customer_docs.name
}

output "support_calls_bucket" {
  description = "Support calls bucket name"
  value       = google_storage_bucket.support_calls.name
}

output "alloydb_cluster_name" {
  description = "AlloyDB cluster name"
  value       = google_alloydb_cluster.customer_db.name
}

output "alloydb_instance_name" {
  description = "AlloyDB instance name"
  value       = google_alloydb_instance.customer_db_primary.name
}

output "alloydb_ip_address" {
  description = "AlloyDB instance IP address"
  value       = google_alloydb_instance.customer_db_primary.ip_address
  sensitive   = false
}

output "alloydb_password_secret" {
  description = "Secret Manager secret name for AlloyDB password"
  value       = google_secret_manager_secret.alloydb_password.secret_id
}

output "alloydb_connection_string" {
  description = "PostgreSQL connection string for AlloyDB (without password)"
  value       = "host=${google_alloydb_instance.customer_db_primary.ip_address} port=5432 user=postgres dbname=postgres"
}

output "mcp_server_service_account" {
  description = "Service account email for MCP server"
  value       = google_service_account.mcp_server.email
}

output "vpc_network" {
  description = "VPC network name"
  value       = google_compute_network.alloydb_network.name
}

output "firestore_database" {
  description = "Firestore database name"
  value       = google_firestore_database.customer_data.name
}

# Summary output for easy reference
output "setup_summary" {
  description = "Summary of deployed resources"
  value = {
    bigquery = {
      dataset = "${var.project_id}.${google_bigquery_dataset.customer_analytics.dataset_id}"
      tables  = ["customers", "transactions"]
    }
    alloydb = {
      cluster     = google_alloydb_cluster.customer_db.name
      instance    = google_alloydb_instance.customer_db_primary.name
      ip_address  = google_alloydb_instance.customer_db_primary.ip_address
      secret_name = google_secret_manager_secret.alloydb_password.secret_id
    }
    storage = {
      customer_docs  = google_storage_bucket.customer_docs.name
      support_calls  = google_storage_bucket.support_calls.name
    }
    network = {
      vpc    = google_compute_network.alloydb_network.name
      subnet = google_compute_subnetwork.alloydb_subnet.name
    }
    service_account = google_service_account.mcp_server.email
  }
}

# Instructions for next steps
output "next_steps" {
  description = "Next steps after Terraform deployment"
  value = <<-EOT

  ✅ Infrastructure deployed successfully!

  Next steps:

  1. Retrieve AlloyDB password:
     gcloud secrets versions access latest --secret=${google_secret_manager_secret.alloydb_password.secret_id}

  2. Configure MCP server:
     cd ../mcp-server
     cat > .env << EOF
     PROJECT_ID=${var.project_id}
     ALLOYDB_HOST=${google_alloydb_instance.customer_db_primary.ip_address}
     ALLOYDB_PASSWORD=$(gcloud secrets versions access latest --secret=${google_secret_manager_secret.alloydb_password.secret_id})
     EOF

  3. Load mock data:
     bq load --source_format=NEWLINE_DELIMITED_JSON \
       ${var.project_id}:${google_bigquery_dataset.customer_analytics.dataset_id}.customers \
       ../../mock-data/bigquery_customers.json

  4. Start MCP server:
     npm install && npm start

  5. Create Gemini Enterprise data stores (via Console):
     https://console.cloud.google.com/gen-app-builder/engines

  For full documentation, see: ../01-PREREQUISITES.md

  EOT
}
