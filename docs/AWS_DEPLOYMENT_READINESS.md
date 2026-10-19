# AWS deployment readiness

Checked October 18, 2026. Status: offline preparation complete for the current draft; live deployment is not authorized or verified.

## Verified evidence

- Application tests passed for e4c65f7: https://github.com/ismet1292-wq/cloudops-observatory/actions/runs/39185438591
- All three Terraform roots passed CI validation, including host mocked tests and bootstrap shell syntax: https://github.com/ismet1292-wq/cloudops-observatory/actions/runs/39185438527
- GHCR latest and the full source commit tag dd87b9caa69998c30adb9f24c8eb788a7f6ee37e resolved to the same digest:

```text
ghcr.io/ismet1292-wq/cloudops-observatory@sha256:6a0e30e4179b1f23eda23d52f73b57a0d61f4643510fa6ab6796bfabe8cbf417
```

- Docker manifest inspection reported linux/amd64 for that digest, compatible with the proposed x86-64 host.
- The publishing run for the source commit succeeded: https://github.com/ismet1292-wq/cloudops-observatory/actions/runs/37256820374

These checks verify registry identity/platform metadata and workflow results. They do not establish image vulnerability status, boot success, or live application behavior. The release predates the infrastructure draft; it remains the existing published application image, not an image rebuilt from the current documentation commit.

To repeat the registry metadata checks from PowerShell (does not deploy or start a container):

```powershell
docker buildx imagetools inspect ghcr.io/ismet1292-wq/cloudops-observatory:latest
docker manifest inspect --verbose ghcr.io/ismet1292-wq/cloudops-observatory@sha256:6a0e30e4179b1f23eda23d52f73b57a0d61f4643510fa6ab6796bfabe8cbf417
```

The local Docker Linux engine was not running during this check, so no new container execution or persistence test was performed. No AWS lookup, credentials, plan, apply, or cloud resource creation was performed. Mocked Terraform tests use synthetic provider responses.

## Inputs prepared

Both deployment roots have terraform.tfvars.example files. These are not loaded automatically and contain empty account-specific values deliberately. The host example includes only the verified public image digest and leaves disk initialization disabled. Real local .tfvars files and state are excluded from Git.

The current draft requires network deployment first and explicit transfer of verified subnet/security group outputs to the host root. It does not automatically orchestrate two applies or verify that supplied IDs match the intended account/network.

## Remaining decisions before AWS access

- Identify the intended AWS account and an authorized access method without creating long-lived access keys for this project.
- Agree on a maximum demonstration duration, spending limit, and cleanup owner.
- Estimate us-east-1 costs for t3.micro runtime, 12 GiB root plus 8 GiB data gp3 disks, one public IPv4, data transfer, and any backup storage. Check actual account credits/eligibility separately; do not assume zero cost.
- Verify a current official Amazon Linux 2023 x86-64 AMI, account availability zone support, CIDR suitability, and network outputs after access is authorized.
- Review operator Session Manager permissions, the instance managed policy, state storage/locking, and backup/retention policy.
- Decide whether to initialize the newly created blank data disk. A retained data disk costs money and is protected from Terraform deletion.

A spending limit has not been selected, and there is no cost approval or guaranteed automatic cutoff. Budget alerts alone do not enforce a hard cap. Keep all real AWS operations outside the current scope.

## Evidence required after any future authorized deployment

Record the reviewed plan, actual resources, image digest, successful cloud-init/systemd startup, a working SSM tunnel, health endpoint response, incident creation and recovery, history persistence after container restart and host reboot, and cleanup results. Until then, describe this work as an infrastructure draft with offline validation.

See [the deployment plan](AWS_DEPLOYMENT_PLAN.md) and [host draft instructions](../infrastructure/aws-host/README.md).
