module "cloud_storage" {
  source = "../../modules/storage"
  project_id = var.project_id
  project_region = var.project_region
  access_prevention_policy = var.access_prevention_policy
  archive_storage_age = var.archive_storage_age
  coldline_storage_age = var.coldline_storage_age
  delete_age = var.delete_age
  logging_bucket = var.logging_bucket
  nearline_storage_age = var.nearline_storage_age
  storage_bucket = var.storage_bucket
  dataflow_bucket = var.dataflow_bucket
  composer_bucket = var.composer_bucket
}

module "bigquery" {
  source = "../../modules/bigquery"
  dataset_name = var.dataset_name
  project_id = var.project_id
  project_region = var.project_region
  service_account_name = var.service_account_name
  table_name = var.table_name
  owner_email = var.owner_email
}

module "cloud_composer" {
  source = "../../modules/composer"
  project_id = var.project_id
  project_region = var.project_region
  composer_name = var.composer_name
  service_account_name = var.service_account_name
  composer_bucket_name = module.cloud_storage.composer_bucket_name
  dataset_bucket_name = module.cloud_storage.dataset_bucket_name
  artifactory_image_name = var.artifactory_image_name
  cluster_namespace = var.cluster_namespace
  cluster_service_account_name = var.cluster_service_account_name
}

module "artifactory" {
  source = "../../modules/artifactory"
  project_id = var.project_id
  project_region = var.project_region
  repository_name = var.repository_name
}

output "cluster_name" {
  value = module.cloud_composer.cluster_name
}
