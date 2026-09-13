# Terraform e provedores. O estado fica no S3, com trava nativa (use_lockfile),
# recurso do Terraform 1.10+ que dispensa a tabela no DynamoDB.
terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket       = "tfstate-481665095044-medassist-prod"
    key          = "medassist/infra.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}

provider "aws" {
  region = var.regiao

  default_tags {
    tags = {
      Projeto   = "MedAssistPro"
      Ambiente  = "prod"
      Terraform = "true"
    }
  }
}
