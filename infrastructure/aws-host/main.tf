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

variable "ami_id" {
  description = "Verified Amazon Linux 2023 x86-64 AMI in us-east-1, with SSM Agent."
  type        = string
  validation {
    condition     = can(regex("^ami-[0-9a-f]{17}$", var.ami_id))
    error_message = "Supply a verified AMI ID; no AMI is looked up automatically."
  }
}

variable "subnet_id" {
  description = "Subnet output from the separately applied aws-network root."
  type        = string
}

variable "security_group_id" {
  description = "No-ingress application security group from aws-network."
  type        = string
}

variable "availability_zone" {
  description = "The same us-east-1 availability zone used by the network subnet."
  type        = string
  validation {
    condition     = can(regex("^us-east-1[a-z]$", var.availability_zone))
    error_message = "Use the subnet's standard us-east-1 availability zone."
  }
}

variable "container_image" {
  description = "Verified public linux/amd64 GHCR image pinned by SHA-256 digest."
  type        = string
  validation {
    condition     = can(regex("^ghcr.io/ismet1292-wq/cloudops-observatory@sha256:[0-9a-f]{64}$", var.container_image))
    error_message = "Use this project's public image with an immutable sha256 digest."
  }
}

variable "initialize_empty_data_disk" {
  description = "Explicit permission to format a blank data disk; existing filesystems are never reformatted."
  type        = bool
  default     = false
}

resource "aws_iam_role" "host" {
  name_prefix = "observatory-host-"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = "sts:AssumeRole"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.host.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "host" {
  name_prefix = "observatory-host-"
  role        = aws_iam_role.host.name
}

resource "aws_ebs_volume" "data" {
  availability_zone = var.availability_zone
  type              = "gp3"
  size              = 8
  encrypted         = true
  tags              = { Name = "observatory-data" }
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_instance" "host" {
  ami                         = var.ami_id
  instance_type               = "t3.micro"
  subnet_id                   = var.subnet_id
  availability_zone           = var.availability_zone
  vpc_security_group_ids      = [var.security_group_id]
  associate_public_ip_address = true
  iam_instance_profile        = aws_iam_instance_profile.host.name
  user_data_replace_on_change = true
  user_data = templatefile("${path.module}/bootstrap.sh.tftpl", {
    volume_serial = replace(aws_ebs_volume.data.id, "-", "")
    image         = var.container_image
    initialize    = var.initialize_empty_data_disk ? "true" : "false"
  })
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }
  root_block_device {
    volume_type           = "gp3"
    volume_size           = 12
    encrypted             = true
    delete_on_termination = true
  }
  credit_specification {
    cpu_credits = "standard"
  }
  depends_on = [aws_iam_role_policy_attachment.ssm]
  tags       = { Name = "observatory-demo" }
}

resource "aws_volume_attachment" "data" {
  device_name = "/dev/sdf"
  volume_id   = aws_ebs_volume.data.id
  instance_id = aws_instance.host.id
}

output "instance_id" {
  value = aws_instance.host.id
}

output "data_volume_id" {
  value = aws_ebs_volume.data.id
}
