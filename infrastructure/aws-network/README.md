# AWS network foundation (deployed October 19, 2026)

This independent Terraform root implements the network portion of the proposed AWS design. It is not a complete application deployment. The original terraform/ root remains a read-only availability zone example.

Resources defined: a VPC, public subnet, internet gateway, route table, default internet route, subnet association, and an application security group with no inbound rules and TCP 443 outbound only. Public IP assignment is disabled by default; a later host configuration must explicitly request an address for direct internet egress. No NAT gateway is defined.

There is no instance, IAM role, application bootstrap, data disk, or dashboard here yet. A saved Terraform plan was applied with explicit user approval on October 19, 2026: 8 resources added, 0 changed, 0 destroyed. AWS confirmed the subnet in us-east-1a, its active internet route, and the application security group with no inbound rules and only TCP 443 outbound. End-to-end host connectivity remains unverified because no host has been deployed. The availability_zone variable is intentionally required and must be verified in the target account before a future plan.

Offline checks (PowerShell, from the repository root):

```powershell
terraform -chdir=infrastructure/aws-network fmt -check -recursive
terraform -chdir=infrastructure/aws-network init -backend=false -input=false
terraform -chdir=infrastructure/aws-network validate -no-color
```

These checks download providers and validate syntax/provider schemas; they do not contact AWS or require AWS credentials. CI performs the same checks. Provider packages have separate checksums for Windows and Linux in the committed lock file.

Any further apply or destroy must match the scope authorized by the user. Even this network root creates real AWS infrastructure if applied. Review the deployment plan, account access, costs, state storage, and cleanup first. Existing monitoring targets use loopback; external HTTP targets would require a separately reviewed outbound rule.

See ../../docs/AWS_DEPLOYMENT_PLAN.md for the full proposal and remaining deployment work.
