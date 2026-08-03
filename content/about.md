---
title: "About Me"
date: 2026-08-03
draft: false
---

# Rohit Gudi

## Professional Summary

Security-focused software engineer with 10+ years building the systems that protect high-value assets in regulated, multi-cloud environments. Depth in software supply chain integrity (Sigstore signing, SBOMs, build attestations, SLSA), workload identity and machine authentication (SPIFFE/SPIRE, mTLS), and Kubernetes security primitives (RBAC, service accounts, namespace isolation, network policy, pod security, admission control). Builds security frameworks and libraries that engineering organizations adopt by default — shifting security left so product teams ship safely without becoming security experts. Strong Python, Go, and Rust; deep Kubernetes, AWS/Azure/GCP, and Infrastructure-as-Code background. Comfortable owning ambiguous, greenfield security problems end to end and driving them across organizational boundaries.

[Download Resume (PDF)](/Rohit%20Gudi.pdf)

## Professional Experience

### Capital One | Principal Software Engineer / Infrastructure | McLean, VA | 07/2022 – Present

- Architected and secured the software supply chain for commercialized products — OCI artifact distribution, Sigstore-based signing, SBOM generation, and build attestations — delivering verifiable provenance as a contractual security artifact to financial-services customers.
- Deployed and operated a SPIRE/SPIFFE ecosystem providing workload identity, authentication, and authorization for cloud-native applications on Kubernetes, with short-lived, automatically rotated credentials issued per attested workload.
- Built Helm library charts adopted as the default deployment path across the organization, enforcing pod security contexts, RBAC and service-account scoping, and ingress/Gateway API standards — a reusable security framework that eliminated entire classes of misconfiguration without requiring product teams to become security experts.
- Integrated policy-as-code (OPA/Gatekeeper) as a Kubernetes admission controller, automating compliance enforcement against organizational and regulatory standards at deploy time rather than in audit after the fact.
- Developed automated tooling in Python and Go to continuously scan Kubernetes environments for vulnerabilities, misconfigurations, and policy violations, surfacing posture findings for remediation across the fleet.
- Architected a self-service deployment pipeline (Helm + Terraform) and reusable AWS CDK scaffolding for hybrid-SaaS, air-gapped, and customer on-prem installations of the Databolt tokenization products, integrating container vulnerability scanning and hardened default configurations — reducing customer onboarding time by 30%.
- Built and operated an internal platform for hosting and distributing open-source artifacts, defining the SDLC controls governing dependency ingestion and developer access.
- Designed multi-account AWS network security: VPC architecture, Transit Gateways, security groups, Kubernetes network policies, Istio service mesh for east-west mTLS, and DNS.
- Delivered a self-service Internal Developer Platform with security guardrails baked in, enabling new product streams to onboard rapidly; championed SRE practices org-wide, improving golden-signal reliability metrics (latency, error rate, throughput, saturation) by 15%.
- Partnered with product management and customers to define deployment architectures and operational requirements; mentored engineers on secure-by-default platform patterns and authored the architecture documentation behind them.

### Slalom | Cloud Engineering / Enablement Consultant | Philadelphia, PA | 09/2020 – 07/2022

- **Salesforce:** Architected YubiKey FIDO-compliant authentication using Go microservices and designed secure cloud/hybrid identity-management solutions. Integrated Mulesoft services into EKS via Spinnaker CI/CD; built reusable Grafana/Prometheus dashboards reducing MTTR by 20%.
- **Capital One (via AWS Professional Services):** Secured EKS deployment and automation with SAST/SCA scanning in CI. Modularized Terraform achieving 95% deployment consistency. Hardened API Gateway, CloudFront, AWS WAF, and cloud networking (VPCs, routing, load balancing). Implemented gRPC and REST services on multi-region ECS clusters.
- Standardized DevOps practice across client engagements through architecture diagrams, operational documentation, automated alerting, and refined on-call rotations.

### Cadent TV | Senior DevOps Engineer | Philadelphia, PA | 05/2019 – 09/2020

- Led Cadent's initial AWS environment build with segmented network design, and standardized secure infrastructure deployment through reusable Terraform modules.
- Architected the AWS microservices strategy on Kubernetes (EKS), Lambda, Kinesis, Fargate, and AppSync; standardized Helm chart templates, improving deployment reliability by 40%.
- Drove adoption of Datadog (60% monitoring improvement) and Docker (75% reduction in setup time); automated critical production operations with Ansible, saving 15 hours weekly.

### iCIMS | Systems Engineer III | Holmdel, NJ | 03/2016 – 05/2019

- Re-architected communication systems into secure microservices (Java, React) and led the migration of 4,000+ customers to a new email service provider at 98% delivery success.
- Owned platform email security and deliverability as postmaster, reducing spam complaints from 15% to under 2%.
- Led configuration management with CloudFormation and Ansible (50% reduction in server setup time); scaled monitoring infrastructure for 11,000+ career web portals.

## Technical Skills

### Security & Supply Chain
Sigstore/cosign, SLSA, SBOMs (Syft), build attestations, Trivy, Snyk, SAST/SCA, SPIFFE/SPIRE, mTLS, OPA/Gatekeeper, admission controllers, Kubernetes RBAC & Pod Security, network policy, container security

### Languages
Go, Python, Rust, Bash/Shell, JavaScript/Node.js

### Kubernetes & Containers
EKS, GKE, AKS, Rancher, Docker, ECS/Fargate, Helm (library charts), Istio service mesh, Gateway API

### Cloud
AWS, Azure, GCP — multi-account IAM, VPC architecture, Transit Gateways, network segmentation, encryption, DNS, load balancing

### IaC & CI/CD
Terraform, AWS CDK, CloudFormation, Ansible, Jenkins, GitHub Actions, ArgoCD, Spinnaker

### Observability
Prometheus, Grafana, Datadog, Sysdig, OpenTelemetry, ELK/Elasticsearch, Splunk

## Education

B.S. Information Technology — New Jersey Institute of Technology, Newark, NJ | 2016
