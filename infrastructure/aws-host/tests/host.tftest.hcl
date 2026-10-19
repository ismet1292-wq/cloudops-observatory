mock_provider "aws" {}

variables {
  ami_id                     = "ami-00000000000000000"
  subnet_id                  = "subnet-00000000000000000"
  security_group_id          = "sg-00000000000000000"
  availability_zone          = "us-east-1a"
  container_image            = "ghcr.io/ismet1292-wq/cloudops-observatory@sha256:0000000000000000000000000000000000000000000000000000000000000000"
  initialize_empty_data_disk = false
}

run "host_security_and_storage" {
  command = plan

  assert {
    condition     = aws_instance.host.metadata_options[0].http_tokens == "required" && aws_instance.host.metadata_options[0].http_put_response_hop_limit == 1
    error_message = "Require IMDSv2 and prevent container metadata access across a second hop."
  }
  assert {
    condition     = aws_instance.host.root_block_device[0].encrypted && aws_ebs_volume.data.encrypted
    error_message = "Both the root disk and incident-history disk must be encrypted."
  }
  assert {
    condition     = aws_instance.host.credit_specification[0].cpu_credits == "standard"
    error_message = "Do not enable surplus CPU-credit charges."
  }
  assert {
    condition = strcontains(templatefile("${path.module}/bootstrap.sh.tftpl", {
      volume_serial = "vol00000000000000000"
      image         = var.container_image
      initialize    = "false"
    }), "127.0.0.1:8080:8080")
    error_message = "Publish the dashboard on host loopback only."
  }
}

run "reject_mutable_image" {
  command = plan
  variables {
    container_image = "ghcr.io/ismet1292-wq/cloudops-observatory:latest"
  }
  expect_failures = [var.container_image]
}
