# AWS host draft (not deployed)

This independent Terraform root prepares one Amazon Linux 2023 x86-64 t3.micro host for the proposed demonstration in us-east-1. It is local code, not a verified cloud deployment. Do not run a real plan or apply under the current no-AWS-access/no-charges scope.

## Defined configuration

- Explicit, verified AMI, subnet, availability zone, security group, and public image digest inputs. There is no AWS data lookup or automatic latest-image selection.
- One EC2 instance with an auto-assigned public IPv4 for outbound access, an encrypted 12 GiB gp3 root disk, IMDSv2, and standard CPU credits.
- An instance role with AWS's AmazonSSMManagedInstanceCore policy. This supports more Systems Manager capabilities than port forwarding alone; review it and operator permissions before deployment. No IAM users, access keys, SSH key pairs, or registry credentials are defined.
- An encrypted 8 GiB gp3 data volume with prevent_destroy and a separate attachment. It survives instance replacement but continues to incur storage costs while retained.
- A bootstrap template that installs Docker, starts SSM Agent, waits up to ten minutes for the exact data volume serial, and mounts ext4 storage by UUID.
- Explicit opt-in before formatting a blank disk. Existing filesystems and disks with signatures or partitions are not reformatted. The data volume is initially blank, so first deployment needs an intentional initialize_empty_data_disk=true decision. This flag does not authorize a deployment by itself.
- A systemd service that waits for the data mount, runs the digest-pinned container with limited privileges and bounded Docker logs, and publishes only 127.0.0.1:8080.

The selected security group must be the no-ingress group from aws-network. This root cannot verify supplied IDs belong to the correct network without live AWS access. The AMI must have working SSM Agent and the required Amazon Linux tools; AMI authenticity, image digest/platform, package installation, boot behavior, SSM connectivity, and application recovery remain unverified.

## Offline validation

From the repository root in PowerShell:

```powershell
terraform -chdir=infrastructure/aws-host init -backend=false -input=false
terraform -chdir=infrastructure/aws-host fmt -check -recursive
terraform -chdir=infrastructure/aws-host validate -no-color
terraform -chdir=infrastructure/aws-host test -no-color
```

Tests use a mocked AWS provider and synthetic IDs/digest. They check IMDSv2, disk encryption, CPU credit settings, loopback publication in the rendered template, and rejection of a mutable image tag. No live AWS plan, apply, credentials, or lookup is used. CI additionally runs bash -n against the bootstrap template. These tests do not boot Linux or execute the bootstrap script.

## Future deployment inputs and ordering

After account/cost authorization, review and apply the network root first, then supply its subnet_id and security_group_id outputs here. Use the same availability zone for the data volume and subnet. Verify the official Amazon Linux 2023 x86-64 AMI and the public GHCR linux/amd64 digest independently. Do not use the tests' synthetic values. Keep local tfvars and state out of Git; ignored local state still needs secure backup and appropriate locking before collaborative use.

Review estimated EC2 runtime, both disks, public IPv4, transfer, and any backups. This is a billable design, not a free-tier guarantee. No public dashboard or inbound SSH rule is needed. Operator authorization to start SSM port-forwarding sessions is separate from the instance role and is not provisioned here. The local Session Manager plugin is also required.

After an explicitly authorized deployment, inspect cloud-init logs and systemctl status observatory, establish the port-forwarding session, check /healthz, and demonstrate incident creation/recovery. Verify container restart and host reboot preserve history before claiming success. The default targets remain internal demonstration endpoints.

If bootstrap fails, diagnose before rerunning its script: it installs packages, mounts storage, and can initialize a blank disk only when explicitly enabled. User-data changes replace the host. Before host replacement, stop the container and unmount the data filesystem, then stop the instance so the old attachment can detach safely. Never force-detach a mounted database volume. The disk stays in its original availability zone; do not change zones as a migration mechanism.

## Cleanup and retention

The data disk's prevent_destroy intentionally blocks a normal destroy plan. Agree on retention, take a consistent backup, and review the deletion plan before removing that protection. Do not remove protection merely to make a command succeed. Retention costs continue even after the host stops. Review any remaining volumes, snapshots, and public addresses after a future cleanup. No cleanup action is needed now because nothing was deployed.

References: [instance profile permissions](https://docs.aws.amazon.com/systems-manager/latest/userguide/setup-instance-permissions.html), [NVMe volume identification](https://docs.aws.amazon.com/ebs/latest/userguide/identify-nvme-ebs-device.html), and [the project deployment plan](../../docs/AWS_DEPLOYMENT_PLAN.md).
