# AWS network foundation (not deployed)

This independent Terraform root implements the network portion of the proposed AWS design. It is not a complete application deployment. The original terraform/ root remains a read-only availability zone example.

Resources defined: a VPC, public subnet, internet gateway, route table, default internet route, subnet association, and an application security group with no inbound rules and TCP 443 outbound only. Public IP assignment is disabled by default; a later host configuration must explicitly request an address for direct internet egress. No NAT gateway is defined.

There is no instance, IAM role, application bootstrap, data disk, or dashboard here yet. No AWS plan or apply has been run. Account availability zone support, CIDR suitability, quotas, connectivity, and deployed security behavior remain unverified. The availability_zone variable is intentionally required and must be verified in the target account before a future plan.

Offline checks (PowerShell, from the repository root):

```powershell
terraform -chdir=infrastructure/aws-network fmt -check -recursive
terraform -chdir=infrastructure/aws-network init -backend=false -input=false
terraform -chdir=infrastructure/aws-network validate -no-color
```

These checks download providers and validate syntax/provider schemas; they do not contact AWS or require AWS credentials. CI performs the same checks. Provider packages have separate checksums for Windows and Linux in the committed lock file.

Do not run plan or apply under the current preparation-only scope. Even this network root creates real AWS infrastructure if applied. Review the deployment plan, account access, costs, state storage, and cleanup first. Existing monitoring targets use loopback; external HTTP targets would require a separately reviewed outbound rule.

See ../../docs/AWS_DEPLOYMENT_PLAN.md for the full proposal and remaining deployment work.
