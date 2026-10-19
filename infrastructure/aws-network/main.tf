terraform {
  required_version = ">= 1.15.0, < 2.0.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
  default_tags {
    tags = {
      Project   = "cloudops-observatory"
      ManagedBy = "Terraform"
      Purpose   = "demonstration"
    }
  }
}

variable "availability_zone" {
  description = "An account-verified standard availability zone in us-east-1. No default is selected offline."
  type        = string
  validation {
    condition     = can(regex("^us-east-1[a-z]$", var.availability_zone))
    error_message = "Use a standard us-east-1 availability zone, such as us-east-1a, after verifying it in the target account."
  }
}

resource "aws_vpc" "observatory" {
  cidr_block           = "10.42.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = { Name = "observatory-demo" }
}

resource "aws_subnet" "observatory" {
  vpc_id                  = aws_vpc.observatory.id
  cidr_block              = "10.42.1.0/24"
  availability_zone       = var.availability_zone
  map_public_ip_on_launch = false
  tags                    = { Name = "observatory-demo-public" }
}

resource "aws_internet_gateway" "observatory" {
  vpc_id = aws_vpc.observatory.id
  tags   = { Name = "observatory-demo" }
}

resource "aws_route_table" "observatory" {
  vpc_id = aws_vpc.observatory.id
  tags   = { Name = "observatory-demo-public" }
}

resource "aws_route" "internet" {
  route_table_id         = aws_route_table.observatory.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.observatory.id
}

resource "aws_route_table_association" "observatory" {
  subnet_id      = aws_subnet.observatory.id
  route_table_id = aws_route_table.observatory.id
}

resource "aws_security_group" "observatory" {
  name_prefix = "observatory-demo-"
  description = "No inbound access; HTTPS egress for SSM and image downloads"
  vpc_id      = aws_vpc.observatory.id
  ingress     = []
  tags        = { Name = "observatory-demo" }
}

resource "aws_vpc_security_group_egress_rule" "https" {
  security_group_id = aws_security_group.observatory.id
  description       = "HTTPS to public SSM, package, and container endpoints"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
}

output "vpc_id" {
  value = aws_vpc.observatory.id
}

output "subnet_id" {
  value = aws_subnet.observatory.id
}

output "security_group_id" {
  value = aws_security_group.observatory.id
}
