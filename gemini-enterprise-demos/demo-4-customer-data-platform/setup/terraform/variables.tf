# Terraform Variables for Demo #4

variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "Google Cloud region for resources"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "alloydb_cpu_count" {
  description = "Number of vCPUs for AlloyDB instance"
  type        = number
  default     = 2

  validation {
    condition     = var.alloydb_cpu_count >= 2 && var.alloydb_cpu_count <= 64
    error_message = "AlloyDB CPU count must be between 2 and 64."
  }
}

variable "enable_deletion_protection" {
  description = "Enable deletion protection for AlloyDB"
  type        = bool
  default     = false
}

variable "bigquery_location" {
  description = "Location for BigQuery dataset (can differ from region)"
  type        = string
  default     = "US"
}
