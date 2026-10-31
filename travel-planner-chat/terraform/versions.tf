terraform {
  required_version = ">= 1.10"
  backend "s3" {}
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.region
  default_tags {
    tags = { Project = "travel-demo", Purpose = "temporary-teaching" }
  }
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "instance_type" {
  type    = string
  default = "t3.small"
  validation {
    condition     = contains(["t3.small", "t3a.small"], var.instance_type)
    error_message = "Use one small teaching instance."
  }
}

variable "backend_archive" {
  type        = string
  description = "Path to the backend tar.gz created by the build script."
}

data "aws_caller_identity" "current" {}
data "aws_availability_zones" "available" { state = "available" }
data "aws_ssm_parameter" "ami" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}
