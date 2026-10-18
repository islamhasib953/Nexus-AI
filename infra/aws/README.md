# AWS deployment plan

The initial target is one private-subnet EC2 instance running the production compose file, fronted by an HTTPS reverse proxy or ALB. PostgreSQL should be Amazon RDS PostgreSQL when the budget allows; Qdrant may remain local only for an early pilot, then move to a managed/private deployment. Redis is optional until asynchronous workers require it.

The EC2 instance uses an instance profile rather than static AWS keys. It may pull images from ECR and read only the named Secrets Manager secret. Security groups allow HTTPS from the load balancer and SSH only through a controlled admin path; no database port is internet-facing.

Single-instance limitation: this topology has a single point of failure and maintenance downtime. The upgrade path is ALB + two EC2 instances, RDS Multi-AZ, external Redis, managed vector storage, autoscaling, and blue/green deployment.

Required secret keys are documented in `.env.production.example`; values are injected at runtime and are never baked into images.
