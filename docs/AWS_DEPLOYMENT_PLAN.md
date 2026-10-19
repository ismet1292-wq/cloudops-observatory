# AWS deployment plan

Status: network foundation deployed and verified October 19, 2026. The EC2 host, storage, and application deployment remain drafts.
Region: us-east-1.

## Completed foundation

- The Terraform root contains only the AWS provider, an availability zone data source, and its output.
- Local formatting and validation passed; no AWS data lookup was executed.
- GitHub Actions application tests passed at commit 3ade71b.
- Terraform checks passed at commit c8b9d43.
- The latest manual container publishing run succeeded on October 4, 2026.

## Proposed first deployment

Use one Linux x86-64 EC2 instance running the existing Docker container. This matches the application's single-process SQLite design. It is a demonstration with downtime during host replacement, not a highly available production service.

Proposed components:

- Dedicated VPC and one public subnet in us-east-1, with an internet gateway and route for outbound connectivity.
- One small EC2 instance with an encrypted gp3 root disk, IMDSv2 required, and a narrowly scoped Systems Manager instance role.
- A public IPv4 address for outbound package downloads, GHCR pulls, and Systems Manager connectivity. Public IPv4 has a cost even though inbound access is blocked.
- A security group with no inbound rules. Outbound rules must cover HTTPS and any explicitly approved monitoring targets.
- Systems Manager Session Manager port forwarding for dashboard access. This requires SSM Agent, endpoint connectivity, authorized operator access, and the local Session Manager plugin.
- Publish container port 8080 only on host loopback (127.0.0.1). Access the dashboard through the tunnel. Do not expose the application's HTTP server to the internet.
- An encrypted data disk mounted on the host and bind-mounted to /data. Set ownership for container UID/GID 10001 before startup.
- A restart policy or host service that starts the container after reboot and waits for the data mount.

Pin the deployed public GHCR image to a verified digest. The existing workflow publishes latest and full commit-SHA tags, but a newly pushed documentation commit does not automatically publish an image. Record the digest and source commit before deployment. Do not assume an ARM image is available.

The current services.json monitors the container's own health endpoint and an intentional failure endpoint. Keep these for the first demonstration; they are not evidence of monitoring external production services.

## Persistence and recovery

Container replacement must retain incident history on the mounted data disk. Host replacement requires explicit reattachment of that disk in the same availability zone. Do not automatically format a disk containing data.

Define disk retention and backup policy before implementation. Retained disks and snapshots can continue to cost money after an instance is terminated. A retained disk is not a backup. Stop writes or use SQLite's backup API for a consistent database backup.

## Cost and access decisions before implementation

The original local-only scope was subsequently expanded by the user to authorize temporary non-root CLI access, the reviewed deployment policy, and the saved network plan. The network apply completed. EC2, storage, and application deployment require a separately reviewed plan and authorization.

Before a later live deployment, agree on the instance size, runtime window, spending limit, account access method, data retention, and cleanup owner. Estimate EC2 runtime, EBS storage, public IPv4, transfer, snapshots, and optional logging in us-east-1. Do not assume free-tier eligibility. Budget alerts are notifications, not a guaranteed spending cap.

Do not add NAT gateways, paid interface endpoints, load balancers, managed Kubernetes, or a managed database to this first design without revisiting scope and cost. The selected public-subnet design needs no inbound SSH or dashboard rule.

## Implementation sequence for a later authorized phase

1. Confirm account access and cost decisions without committing secrets.
2. Implement deployment infrastructure in a separate Terraform root so the current validation-only example stays clear.
3. Review least-privilege IAM, network rules, encrypted storage, image digest, bootstrap, and Terraform state handling.
4. Run formatting and validation locally and in CI.
5. With explicit authorization for AWS access, generate and review a plan. A plan can read AWS and requires credentials.
6. Obtain authorization for the concrete resources and costs before applying.
7. Verify startup, tunnel access, health, outage/recovery transitions, persistence after container restart, and recovery after host reboot.
8. Record evidence and limitations; do not claim deployment before those checks pass.
9. At the end of the demo window, remove the approved resources and check for retained disks, snapshots, addresses, and other billable leftovers.

## Sources

- [Session Manager overview](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html)
- [Starting sessions and port forwarding](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-sessions-start.html)
- [EC2 pricing](https://aws.amazon.com/ec2/pricing/on-demand/)
- [EBS pricing](https://aws.amazon.com/ebs/pricing/)
- [VPC and public IPv4 pricing](https://aws.amazon.com/vpc/pricing/)

These references support the design; actual account access, costs, and deployment behavior remain unverified.

### Network implementation prepared locally

The separate `infrastructure/aws-network/` root now defines the proposed VPC, subnet, internet route, and security group. It contains no compute, IAM, storage, or application bootstrap. The security group has no inbound rules and permits HTTPS egress. The subnet does not automatically assign public IP addresses.

Formatting and provider-schema validation are the only intended execution steps in the current scope. They cannot verify live connectivity or account availability zone support. The remaining work is host IAM, EC2 and persistent storage, bootstrap, image selection, cost review, and authorized deployment verification.

### Host and storage implementation prepared locally

The separate `infrastructure/aws-host/` root now defines an EC2 host, Systems Manager instance profile, encrypted root and data disks, volume attachment, and a Docker/systemd bootstrap template. It requires verified network outputs, AMI, and image digest inputs. Its data volume has deletion protection and initialization requires explicit opt-in. Dashboard publication is loopback-only. The role uses the AWS-managed AmazonSSMManagedInstanceCore policy, whose scope must be reviewed before deployment.

Local provider-schema validation, mocked tests, and shell syntax checks are preparation evidence only. The bootstrap has not been executed on EC2. Account access, AMI/image selection, cost approval, deployment, connectivity, recovery, and cleanup remain unfinished. See `infrastructure/aws-host/README.md` for ordering and retention details.
